# app/api/v1/external/applications/xhs_copy.py
import time
import logging
import traceback
from flask import Blueprint, request, g
from app.core.responses import success_response
from app.core.exceptions import APIException, ValidationException
from app.core.status_codes import GENERATION_FAILED, PARAMETER_ERROR
from app.infrastructure.database.repositories.user_app_repository import (
    UserAppRepository,
)
from app.infrastructure.database.repositories.user_llm_config_repository import (
    UserLLMConfigRepository,
)
from app.infrastructure.database.repositories.xhs_copy_repository import (
    XhsCopyGenerationRepository,
)
from app.domains.foundation.services.forbidden_words_service import ForbiddenWordsService
from app.infrastructure.database.repositories.forbidden_words_repository import ForbiddenWordsRepository


from app.infrastructure.llm_providers.factory import LLMProviderFactory
from app.api.middleware.app_key_auth import app_key_required

logger = logging.getLogger(__name__)

external_xhs_copy_bp = Blueprint("external_xhs_copy", __name__, url_prefix="/xhs_copy")


# 辅助函数
def _validate_and_extract_params(request):
    """验证和提取请求参数"""
    data = request.get_json()
    if not data:
        raise ValidationException("请求数据不能为空", PARAMETER_ERROR)

    # 提取提示词
    prompt = data.get("prompt")
    if not prompt:
        raise ValidationException("提示词不能为空", PARAMETER_ERROR)

    # 验证图片URL
    image_urls = data.get("image_urls", [])
    if image_urls:
        for url in image_urls:
            if not isinstance(url, str) or not url.startswith(("http://", "https://")):
                raise ValidationException(f"无效的图片URL: {url}", PARAMETER_ERROR)

    custom_forbidden_words = data.get("forbidden_words", [])
    if custom_forbidden_words and not isinstance(custom_forbidden_words, list):
        raise ValidationException("自定义禁用词必须是数组格式", PARAMETER_ERROR)
    
    # 确保所有禁用词是字符串
    if custom_forbidden_words:
        for word in custom_forbidden_words:
            if not isinstance(word, str):
                raise ValidationException("禁用词必须是字符串", PARAMETER_ERROR)

    return data


def _create_llm_provider(user_llm_config):
    """创建LLM提供商实例"""
    provider_type = user_llm_config.provider_type
    
    try:
        if provider_type == "OpenAI":
            # 检查API密钥是否有效
            if not user_llm_config.api_key:
                raise APIException("您尚未配置OpenAI API密钥", GENERATION_FAILED)
                
            # 记录连接尝试（用于调试）
            print(f"正在尝试连接到OpenAI，基础URL为: {user_llm_config.api_base_url}")
            
            return LLMProviderFactory.create_provider(
                "openai",
                user_llm_config.api_key,
                api_base_url=user_llm_config.api_base_url,
                api_version=user_llm_config.api_version,
                timeout=user_llm_config.request_timeout,
                max_retries=user_llm_config.max_retries,
            )
        elif provider_type == "Claude":
            if not user_llm_config.api_key:
                raise APIException("您尚未配置Claude API密钥", GENERATION_FAILED)
            
            print(f"正在尝试连接到Claude，基础URL为: {user_llm_config.api_base_url}")
            
            return LLMProviderFactory.create_provider(
                "anthropic",
                user_llm_config.api_key,
                api_base_url=user_llm_config.api_base_url,
                timeout=user_llm_config.request_timeout,
                max_retries=user_llm_config.max_retries,
            )
        elif provider_type == "Volcano":
            if not user_llm_config.api_key:
                raise APIException("您尚未配置火山引擎API密钥", GENERATION_FAILED)
            
            print(f"正在尝试连接到火山引擎")
            
            # 火山引擎可能需要额外的配置项
            config = {
                "timeout": user_llm_config.request_timeout,
                "max_retries": user_llm_config.max_retries,
            }

            # 添加应用ID和密钥（如果有）
            if user_llm_config.app_id:
                config["app_id"] = user_llm_config.app_id
            if user_llm_config.app_secret:
                config["app_secret"] = user_llm_config.app_secret

            return LLMProviderFactory.create_provider(
                "volcano", user_llm_config.api_key, **config
            )
        else:
            raise APIException(f"不支持的LLM提供商类型: {provider_type}", GENERATION_FAILED)
    except Exception as e:
        print(f"创建LLM提供商失败: {str(e)}")
        print(f"详细错误: {traceback.format_exc()}")
        raise APIException(f"创建LLM提供商失败: {str(e)}", GENERATION_FAILED)




def _prepare_prompts(config, prompt, image_urls, custom_forbidden_words=None):
    """准备提示词"""
    system_prompt = config.get(
        "system_prompt", "你是一位专业的小红书博主，擅长编写吸引人的小红书文案。"
    )

    # 使用用户提示词模板
    user_prompt_template = config.get(
        "user_prompt_template", "请根据以下内容，创作一篇吸引人的小红书文案：\n{prompt}"
    )

    # 替换模板中的变量
    user_prompt = user_prompt_template
    if "{prompt}" in user_prompt:
        user_prompt = user_prompt.replace("{prompt}", prompt)
    else:
        user_prompt = f"{user_prompt}\n\n{prompt}"

    # 添加图片描述
    if image_urls:
        image_descriptions = "\n\n参考以下图片URL："
        for i, url in enumerate(image_urls, 1):
            image_descriptions += f"\n图片{i}：{url}"
        user_prompt += image_descriptions

    # 添加配置要求
    requirements = "\n\n请按以下要求生成文案："
    # requirements += f"\n1. 标题长度不超过{config.get('title_length', 50)}个字"
    # requirements += f"\n2. 正文内容{config.get('content_length', 300)}字左右"
    requirements += f"\n3. 生成{config.get('tags_count', 5)}个适合的标签"
    # if config.get("include_emojis", True):
    #     requirements += "\n4. 适当地使用表情符号增加趣味性"
    
    # 添加禁用词要求
    if custom_forbidden_words and len(custom_forbidden_words) > 0:
        forbidden_words_str = "、".join(custom_forbidden_words)
        requirements += f"\n5. 严禁在文案中使用以下词语: {forbidden_words_str}"
    
    requirements += (
        "\n\n请按照以下格式输出：\n【标题】\n【正文】\n【标签】标签1 标签2 标签3..."
    )

    user_prompt += requirements

    if image_urls and len(image_urls) > 0:
        # 如果有图片，使用支持图片的格式
        content = [{"type": "text", "text": user_prompt}]
        
        # 最多添加4张图片（避免超出模型限制）
        for i, url in enumerate(image_urls[:4]):
            content.append({"type": "image_url", "image_url": {"url": url}})
            
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
    else:
        # 如果没有图片，使用普通文本格式
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

    return messages


def _parse_generation_result(content, config):
    """解析生成结果"""
    title = ""
    body = ""
    tags = []

    # 尝试解析标题、正文和标签
    if "【标题】" in content:
        title_parts = content.split("【标题】")
        if len(title_parts) > 1:
            title_content = (
                title_parts[1].split("【正文】")[0]
                if "【正文】" in title_parts[1]
                else title_parts[1]
            )
            title = title_content.strip()

    if "【正文】" in content:
        body_parts = content.split("【正文】")
        if len(body_parts) > 1:
            body_content = (
                body_parts[1].split("【标签】")[0]
                if "【标签】" in body_parts[1]
                else body_parts[1]
            )
            body = body_content.strip()

    if "【标签】" in content:
        tags_part = (
            content.split("【标签】")[1] if len(content.split("【标签】")) > 1 else ""
        )
        # 提取标签
        tag_candidates = [tag.strip() for tag in tags_part.split() if tag.strip()]
        # 过滤非空标签
        tags = [tag for tag in tag_candidates if tag]

    # 如果没有按格式输出，尝试更灵活地解析
    if not title and not body:
        # 可能是自由格式输出，尝试智能提取
        lines = content.split("\n")
        if lines:
            # 第一行可能是标题
            title = lines[0].strip()
            # 剩余内容作为正文
            body = "\n".join(lines[1:]).strip()

    return {"title": title, "body": body, "tags": tags}

def _get_model_name(app, user_llm_config, has_images=False):
    """
    获取模型名称，优先使用用户配置的模型
    
    Args:
        app: 应用对象，包含配置信息
        user_llm_config: 用户LLM配置
        has_images: 是否有图片输入
        
    Returns:
        模型名称
    """
    # 获取提供商类型
    provider_type = user_llm_config.provider_type
    
    # 从应用配置中获取模型名称
    config = app.published_config.get("config", {})
    model_name = config.get("model_name")
    
    # 如果有图片且使用火山引擎，检查是否有专门的视觉模型配置
    if has_images and provider_type == "Volcano":
        vision_model_name = config.get("vision_model_name")
        if vision_model_name:
            return vision_model_name
    
    # 如果用户指定了模型，使用用户指定的
    if model_name:
        return model_name
    
    # 否则使用默认模型
    if provider_type == "OpenAI":
        return "gpt-4o"
    elif provider_type == "Claude":
        return "claude-3-opus-20240229"
    elif provider_type == "Volcano":
        if has_images:
            return "doubao-1.5-vision-pro-32k-250115"
        else:
            return "deepseek-r1-250120"
    else:
        return None

def _create_generation_record(
    generation_repo, prompt, image_urls, app_id, user_id, ip_address, user_agent
):
    """创建生成记录"""
    generation_data = {
        "prompt": prompt,
        "image_urls": image_urls,
        "app_id": app_id,
        "user_id": user_id,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "status": "processing",
    }
    return generation_repo.create(generation_data)


def _update_generation_success(
    generation_repo,
    generation_id,
    user_id,
    title,
    content,
    tags,
    tokens_used,
    tokens_prompt,
    tokens_completion,
    duration_ms,
    provider_type,
    model_name,
    temperature,
    max_tokens,
    user_llm_config_id,
    contains_forbidden_words=False,
    detected_forbidden_words=None,
    estimated_cost=0.0,
    raw_request=None,
    raw_response=None
):
    """更新生成成功状态"""
    update_data = {
        "status": "completed",
        "title": title,
        "content": content,
        "tags": tags,
        "tokens_used": tokens_used,
        "tokens_prompt": tokens_prompt,
        "tokens_completion": tokens_completion,
        "duration_ms": duration_ms,
        "provider_type": provider_type,
        "model_name": model_name,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "user_llm_config_id": user_llm_config_id,
        "contains_forbidden_words": contains_forbidden_words,
        "detected_forbidden_words": detected_forbidden_words or [],
        "estimated_cost": estimated_cost,
        "raw_request": raw_request,
        "raw_response": raw_response
    }

    return generation_repo.update(generation_id, user_id, update_data)


def _update_generation_failure(
    generation_repo, generation_id, user_id, error_message, duration_ms
):
    """更新生成失败状态"""
    update_data = {
        "status": "failed",
        "error_message": error_message,
        "duration_ms": duration_ms,
    }

    return generation_repo.update(generation_id, user_id, update_data)


@external_xhs_copy_bp.route("/generate", methods=["POST"])
@app_key_required
def external_generate():
    try:
        # 获取app_key_auth中间件已验证的应用和用户信息
        app_key = g.app_key
        user_id = g.user_id
        app = g.app

        # 验证请求数据
        data = _validate_and_extract_params(request)

        # 验证应用类型和发布状态
        if app.app_type != "xhs_copy":
            raise ValidationException(
                "该应用密钥不属于小红书文案生成应用", PARAMETER_ERROR
            )

        if not app.published or not app.published_config:
            raise ValidationException("该应用未发布配置", PARAMETER_ERROR)

        # 获取IP和用户代理
        ip_address = request.remote_addr
        user_agent = request.headers.get("User-Agent")

        # 初始化服务和仓库
        db_session = g.db_session
        user_app_repo = UserAppRepository(db_session)
        user_llm_config_repo = UserLLMConfigRepository(db_session)
        generation_repo = XhsCopyGenerationRepository(db_session)
        
        # 获取系统预置禁用词（如果需要）

        
        forbidden_words_repo = ForbiddenWordsRepository(db_session)
        forbidden_words_service = ForbiddenWordsService(forbidden_words_repo)
        
        # 获取应用场景的系统预置禁用词列表
        try:
            system_forbidden_words = [word["word"] for word in 
                                    forbidden_words_service.get_all_words("xhs_copy")]
        except Exception as e:
            logger.warning(f"无法获取系统预置禁用词: {str(e)}")
            system_forbidden_words = []

        # 提取数据
        prompt = data["prompt"]
        image_urls = data.get("image_urls", [])
        custom_forbidden_words = data.get("forbidden_words", [])
        
        # 合并系统预置禁用词和自定义禁用词
        all_forbidden_words = list(set(system_forbidden_words + custom_forbidden_words))

        # 从应用中获取配置和关联的LLM配置
        config = app.published_config.get("config", {})
        user_llm_config_id = app.user_llm_config_id

        # 创建生成记录
        start_time = time.time()
        generation = _create_generation_record(
            generation_repo,
            prompt=prompt,
            image_urls=image_urls,
            app_id=app.id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        try:
            # 获取用户LLM配置
            user_llm_config = user_llm_config_repo.get_by_id(
                user_llm_config_id, user_id
            )

            # 创建LLM提供商实例
            ai_provider = _create_llm_provider(user_llm_config)

            # 准备提示词，包含禁用词
            messages = _prepare_prompts(config, prompt, image_urls, all_forbidden_words)

            # 确定是否有图片
            has_images = bool(image_urls) and len(image_urls) > 0
            
            # 获取模型名称
            model_name = _get_model_name(app, user_llm_config, has_images)

            # 生成文案参数
            max_tokens = config.get("max_tokens", 800)
            temperature = config.get("temperature", 0.7)
            
            # 保存请求参数用于调试
            request_params = {
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "model": model_name,
                "has_images": has_images,
                "config": config,
            }

            # 调用LLM服务
            response = ai_provider.generate_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                model=model_name,
            )

            # 解析生成结果
            content = response["message"]["content"]
            parsed_result = _parse_generation_result(content, config)

            # 获取tokens使用量
            tokens_used = response.get("usage", {}).get("total_tokens", 0)
            
            # 获取实际使用的模型（可能与请求的不同）
            used_model = response.get("model", model_name)

            # 计算处理时间
            duration_ms = int((time.time() - start_time) * 1000)
            
            # 检查生成内容是否包含禁用词
            contains_forbidden = False
            detected_words = []
            
            if all_forbidden_words:
                generated_text = parsed_result["title"] + " " + parsed_result["body"]
                generated_text_lower = generated_text.lower()
                
                for word in all_forbidden_words:
                    if word.lower() in generated_text_lower:
                        contains_forbidden = True
                        detected_words.append(word)
            
            # 更新生成记录
            
            generation = _update_generation_success(
    generation_repo,
    generation_id=generation.id,
    user_id=user_id,
    title=parsed_result["title"],
    content=parsed_result["body"],
    tags=parsed_result["tags"],
    tokens_used=tokens_used,
    tokens_prompt=response.get("usage", {}).get("prompt_tokens", 0),
    tokens_completion=response.get("usage", {}).get("completion_tokens", 0),
    duration_ms=duration_ms,
    provider_type=user_llm_config.provider_type,
    model_name=used_model,
    temperature=temperature,
    max_tokens=max_tokens,
    user_llm_config_id=user_llm_config_id,
    contains_forbidden_words=contains_forbidden,
    detected_forbidden_words=detected_words,

    raw_request={
        "prompt": prompt,
        "image_urls": image_urls,
        "custom_forbidden_words": custom_forbidden_words,
        "config": config,
        "messages": messages
    },
    raw_response=response
)

            # 创建调试信息对象
            debug_info = {
                "provider_type": user_llm_config.provider_type,
                "requested_model": model_name,
                "actual_model": used_model,
                "request_params": request_params,
                "config_used": config,
                "tokens": {
                    "total": tokens_used,
                    "prompt": response.get("usage", {}).get("prompt_tokens", 0),
                    "completion": response.get("usage", {}).get("completion_tokens", 0),
                },
                "duration_ms": duration_ms,
                "app_id": app.id,
                "user_llm_config_id": user_llm_config_id,
                "forbidden_words_used": detected_words if contains_forbidden else []
            }

            # 格式化结果
            result = {
                "id": generation.id,
                "title": generation.title,
                "content": generation.content,
                "tags": generation.tags,
                "tokens_used": tokens_used,
                "duration_ms": duration_ms,
                "status": generation.status,
                "model": used_model,
                "provider_type": user_llm_config.provider_type,
                "contains_forbidden_words": contains_forbidden,
                "detected_forbidden_words": detected_words,
                "debug": debug_info  # 添加调试信息
            }

            return success_response(result, "生成小红书文案成功")

        except Exception as e:
            logger.error(f"Generation error: {str(e)}\n{traceback.format_exc()}")
            # 更新失败状态
            _update_generation_failure(
                generation_repo,
                generation_id=generation.id,
                user_id=user_id,
                error_message=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )

            # 重新抛出异常
            if isinstance(e, APIException):
                raise
            raise APIException(f"生成文案失败: {str(e)}", GENERATION_FAILED)

    except ValidationException as e:
        # 参数验证失败
        logger.warning(f"Validation error: {str(e)}")
        raise
    except APIException as e:
        # 业务异常
        logger.error(f"API error: {str(e)}")
        raise
    except Exception as e:
        # 未预期的异常
        logger.error(
            f"Unexpected error in external generate: {str(e)}\n{traceback.format_exc()}"
        )
        raise APIException(f"生成文案失败: {str(e)}", GENERATION_FAILED)

