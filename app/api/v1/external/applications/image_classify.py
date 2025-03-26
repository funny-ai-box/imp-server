# app/api/v1/external/applications/image_classify.py
import time
import logging
import traceback
import json
import re
from flask import Blueprint, request, g
from app.core.responses import success_response
from app.core.exceptions import APIException, ValidationException
from app.core.status_codes import CLASSIFICATION_FAILED, PARAMETER_ERROR, INVALID_IMAGE_URL, INVALID_CATEGORIES
from app.infrastructure.database.repositories.user_app_repository import (
    UserAppRepository,
)
from app.infrastructure.database.repositories.llm_repository import (
    LLMProviderConfigRepository,
)
from app.infrastructure.database.repositories.image_classify_repository import (
    ImageClassifyRepository,
)
from app.infrastructure.llm_providers.factory import LLMProviderFactory
from app.api.middleware.app_key_auth import app_key_required

logger = logging.getLogger(__name__)

external_image_classify_bp = Blueprint("external_image_classify", __name__, url_prefix="/image_classify")


# 辅助函数
def _validate_and_extract_params(request):
    """验证和提取请求参数"""
    data = request.get_json()
    if not data:
        raise ValidationException("请求数据不能为空", PARAMETER_ERROR)

    # 提取图片URL
    image_url = data.get("image_url")
    if not image_url:
        raise ValidationException("图片URL不能为空", INVALID_IMAGE_URL)

    # 验证图片URL格式
    if not isinstance(image_url, str) or not image_url.startswith(("http://", "https://")):
        raise ValidationException(f"无效的图片URL: {image_url}", INVALID_IMAGE_URL)

    # 验证分类列表
    categories = data.get("categories")
    if not categories or not isinstance(categories, list) or len(categories) < 2:
        raise ValidationException("分类列表必须至少包含两个选项", INVALID_CATEGORIES)

    for category in categories:
        if not isinstance(category, dict) or "id" not in category or "text" not in category:
            raise ValidationException("分类列表格式错误，每项必须包含id和text字段", INVALID_CATEGORIES)

    return data


def _create_llm_provider(llm_provider_config):
    """创建LLM提供商实例"""
    provider_type = llm_provider_config.provider_type
    
    try:
        if provider_type == "Volcano":
            # 检查API密钥是否有效
            if not llm_provider_config.api_key:
                raise APIException("您尚未配置火山引擎API密钥", CLASSIFICATION_FAILED)
                
            # 记录连接尝试（用于调试）
            logger.info(f"正在尝试连接到火山引擎，基础URL为: {llm_provider_config.api_base_url}")
            
            # 火山引擎可能需要额外的配置项
            config = {
                "timeout": llm_provider_config.request_timeout or 60,
                "max_retries": llm_provider_config.max_retries or 3,
                "api_base_url": llm_provider_config.api_base_url,
                "api_version": llm_provider_config.api_version
            }

            # 添加应用ID和密钥（如果有）
            if llm_provider_config.app_id:
                config["app_id"] = llm_provider_config.app_id
            if llm_provider_config.app_secret:
                config["app_secret"] = llm_provider_config.app_secret

            return LLMProviderFactory.create_provider(
                "volcano", llm_provider_config.api_key, **config
            )
        else:
            raise APIException(f"图片分类仅支持Volcano提供商，当前配置: {provider_type}", CLASSIFICATION_FAILED)
    except Exception as e:
        logger.error(f"创建LLM提供商失败: {str(e)}")
        logger.error(f"详细错误: {traceback.format_exc()}")
        raise APIException(f"创建LLM提供商失败: {str(e)}", CLASSIFICATION_FAILED)


def _get_model_name(config=None):
    """获取模型名称，优先使用用户配置的模型"""
    # 如果配置中指定了视觉模型，使用配置的模型
    if config and "vision_model_name" in config:
        return config["vision_model_name"]
    
    # 如果配置中指定了模型，使用配置的模型
    if config and "model_name" in config:
        return config["model_name"]
        
    # 否则使用默认模型
    return "doubao-1.5-vision-pro-32k-250115"  # 火山引擎视觉模型


def _prepare_prompts(config, image_url, categories):
    """准备提示词"""
    # 系统提示词
    system_prompt = config.get(
        "system_prompt", 
        "你是一位专业的图像分类助手，你的任务是判断图片属于哪个预定义分类。请仔细分析图片内容，如果图片不属于任何分类或信息值太低，请明确表示无法分类。"
    )

    # 构建分类选项文本
    categories_text = "\n".join([f"ID: {cat['id']}, 分类: {cat['text']}" for cat in categories])
    
    # 用户提示词
    user_prompt = f"""请分析下面这张图片，并判断它应该属于以下哪个分类：

{categories_text}

请仔细分析图片内容，并给出你的分类结果和推理过程。
你的回答必须是以下JSON格式：
{{
  "category_id": "分类ID",
  "category_name": "分类名称",
  "confidence": 0.95,
  "reasoning": "这里是你对分类的推理过程"
}}

只能选择一个最匹配的分类。如果图片内容不清晰、信息值低或不属于任何一个给定分类，请返回以下JSON格式：
{{
  "category_id": null,
  "category_name": null,
  "confidence": 0,
  "reasoning": "这里说明为什么无法对图片进行分类的原因"
}}

置信度为0-1之间的小数，推理过程需要详细说明为什么图片属于该分类或无法分类的原因。"""

    # 构建消息
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        }
    ]

    return messages


def _extract_json(text):
    """从文本中提取JSON格式的内容"""
    # 尝试正则提取JSON格式内容
    json_pattern = r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}))*\}'
    matches = re.findall(json_pattern, text)
    
    if matches:
        # 尝试解析找到的每个JSON块
        for match in matches:
            try:
                json.loads(match)
                return match
            except:
                continue
    
    return None


def _parse_classification_result(content, categories):
    """解析分类结果
    
    尝试从LLM响应中提取JSON格式的分类结果，包含category_id、category_name、confidence和reasoning
    支持无法分类的情况，返回null值
    """
    try:
        # 尝试获取JSON格式的响应
        json_content = _extract_json(content)
        if json_content:
            result = json.loads(json_content)
            
            # 检查是否为无法分类的情况（空分类）
            if result.get("category_id") is None and result.get("category_name") is None:
                return {
                    "category_id": None,
                    "category_name": None,
                    "confidence": 0,
                    "reasoning": result.get("reasoning", "无法对图片进行分类，信息值太低或不符合任何给定分类")
                }
            
            # 验证结果中包含必需的字段
            if "category_id" not in result or "category_name" not in result:
                logger.warning(f"分类结果缺少必要字段: {result}")
                # 尝试推断分类或返回无法分类
                if "无法分类" in content or "不属于任何分类" in content:
                    return {
                        "category_id": None,
                        "category_name": None,
                        "confidence": 0,
                        "reasoning": "根据LLM响应，图片无法分类"
                    }
                return _guess_classification(content, categories)
            
            # 确保所有必要字段都存在
            if "confidence" not in result:
                result["confidence"] = 0.8  # 默认置信度
            if "reasoning" not in result:
                result["reasoning"] = "未提供推理过程"
            
            # 验证category_id是否在提供的分类列表中
            valid_ids = [cat["id"] for cat in categories]
            if result["category_id"] not in valid_ids:
                logger.warning(f"分类ID不在提供的列表中: {result['category_id']}")
                # 尝试匹配最接近的ID
                for cat in categories:
                    if cat["text"].lower() == result["category_name"].lower():
                        result["category_id"] = cat["id"]
                        break
            
            return result
        else:
            # 检查是否有明确表示无法分类的内容
            if "无法分类" in content or "不属于任何分类" in content:
                return {
                    "category_id": None,
                    "category_name": None,
                    "confidence": 0,
                    "reasoning": "LLM表示无法分类，但未返回标准JSON格式"
                }
            
            # 无法解析JSON，尝试推断分类
            return _guess_classification(content, categories)
    except Exception as e:
        logger.error(f"解析分类结果失败: {str(e)}\n{traceback.format_exc()}")
        # 尝试推断分类
        return _guess_classification(content, categories)


def _guess_classification(content, categories):
    """从文本响应中推断分类结果"""
    content_lower = content.lower()
    best_match = None
    highest_score = 0
    reasoning = "通过文本分析推断的分类结果"
    
    # 简单的文本匹配算法
    for category in categories:
        category_name = category["text"].lower()
        score = content_lower.count(category_name)
        
        # 增加对ID的检测
        id_match = re.search(r'id[:\s]*["\']?' + re.escape(category["id"]) + r'["\']?', content_lower)
        if id_match:
            score += 5
        
        if score > highest_score:
            highest_score = score
            best_match = category
    
    # 如果没有找到匹配项，选择第一个分类
    if not best_match and categories:
        best_match = categories[0]
        reasoning = "无法确定明确分类，默认选择第一个分类"
    
    return {
        "category_id": best_match["id"],
        "category_name": best_match["text"],
        "confidence": min(highest_score * 0.1, 0.95) if highest_score > 0 else 0.5,
        "reasoning": reasoning
    }


def _create_classification_record(
    classify_repo, image_url, categories, app_id, user_id, ip_address, user_agent
):
    """创建分类记录"""
    record_data = {
        "image_url": image_url,
        "categories": categories,
        "app_id": app_id,
        "user_id": user_id,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "status": "processing",
    }
    return classify_repo.create(record_data)


def _update_classification_success(
    classify_repo,
    classification_id,
    user_id,
    category_id,
    category_name,
    confidence,
    reasoning,
    tokens_used,
    duration_ms,
    provider_type=None,
    model_name=None,
    raw_request=None,
    raw_response=None
):
    """更新分类成功状态，支持无法分类的情况"""
    status = "completed" if category_id is not None else "unclassified"
    
    update_data = {
        "status": status,
        "category_id": category_id,
        "category_name": category_name,
        "confidence": confidence,
        "reasoning": reasoning,
        "tokens_used": tokens_used,
        "duration_ms": duration_ms,
    }
    
    # 添加模型信息（如果提供）
    if provider_type:
        update_data["provider_type"] = provider_type
    if model_name:
        update_data["model_name"] = model_name
    
    # 添加原始请求/响应数据（如果提供）
    if raw_request:
        update_data["raw_request"] = raw_request
    if raw_response:
        update_data["raw_response"] = raw_response

    return classify_repo.update(classification_id, user_id, update_data)


def _update_classification_failure(
    classify_repo, classification_id, user_id, error_message, duration_ms, raw_request=None
):
    """更新分类失败状态"""
    update_data = {
        "status": "failed",
        "error_message": error_message,
        "duration_ms": duration_ms,
    }
    
    # 添加原始请求数据（如果提供）
    if raw_request:
        update_data["raw_request"] = raw_request

    return classify_repo.update(classification_id, user_id, update_data)


@external_image_classify_bp.route("/classify", methods=["POST"])
@app_key_required
def external_classify():
    """图片分类API（外部接口）"""
    try:
        # 获取app_key_auth中间件已验证的应用和用户信息
        app_key = g.app_key
        user_id = g.user_id
        app = g.app

        # 验证请求数据
        data = _validate_and_extract_params(request)

        # 验证应用类型和发布状态
        if app.app_type != "image_classify":
            raise ValidationException(
                "该应用密钥不属于图片分类应用", PARAMETER_ERROR
            )

        if not app.published or not app.published_config:
            raise ValidationException("该应用未发布配置", PARAMETER_ERROR)

        # 获取IP和用户代理
        ip_address = request.remote_addr
        user_agent = request.headers.get("User-Agent")

        # 初始化服务和仓库
        db_session = g.db_session
        user_app_repo = UserAppRepository(db_session)
        llm_provider_config_repo = LLMProviderConfigRepository(db_session)
        classify_repo = ImageClassifyRepository(db_session)

        # 提取数据
        image_url = data["image_url"]
        categories = data["categories"]

        # 从应用中获取配置
        config = app.published_config.get("config", {})
        
        # 检查config中是否包含provider_type
        provider_type = config.get("provider_type")
        if not provider_type:
            raise ValidationException("应用配置中未指定provider_type", PARAMETER_ERROR)
            
        # 目前图片分类仅支持Volcano
        if provider_type != "Volcano":
            raise ValidationException("图片分类目前仅支持Volcano提供商", PARAMETER_ERROR)

        # 创建分类记录
        start_time = time.time()
        classification = _create_classification_record(
            classify_repo,
            image_url=image_url,
            categories=categories,
            app_id=app.id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        # 保存原始请求以便调试
        raw_request = {
            "image_url": image_url,
            "categories": categories,
            "app_id": app.id,
            "user_id": user_id,
            "config": config
        }

        try:
            # 获取用户LLM配置
            llm_provider_config = llm_provider_config_repo.get_default(user_id, provider_type)
            if not llm_provider_config:
                raise APIException(f"未找到{provider_type}的LLM配置，请先在LLM设置中配置", CLASSIFICATION_FAILED)

            # 创建LLM提供商实例
            ai_provider = _create_llm_provider(llm_provider_config)

            # 准备提示词
            messages = _prepare_prompts(config, image_url, categories)

            # 确定模型名称
            model_name = _get_model_name(config)

            # 分类参数
            max_tokens = config.get("max_tokens", 800)
            temperature = config.get("temperature", 0.2)  # 降低温度增加确定性
            
            # 更新原始请求信息
            raw_request.update({
                "messages": messages,
                "model_name": model_name,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "provider_type": provider_type
            })

            # 调用LLM服务
            logger.info(f"开始调用图片分类服务: 模型={model_name}, 图片URL={image_url}")
            response = ai_provider.generate_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                model=model_name,
            )
            logger.info(f"图片分类调用完成，获取到响应，用时{int((time.time() - start_time) * 1000)}ms")

            # 解析分类结果
            content = response["message"]["content"]
            parsed_result = _parse_classification_result(content, categories)

            # 获取tokens使用量
            tokens_used = response.get("usage", {}).get("total_tokens", 0)
            tokens_prompt = response.get("usage", {}).get("prompt_tokens", 0)
            tokens_completion = response.get("usage", {}).get("completion_tokens", 0)

            # 计算处理时间
            duration_ms = int((time.time() - start_time) * 1000)

            # 获取实际使用的模型（可能与请求的不同）
            used_model = response.get("model", model_name)

            # 更新分类记录
            classification = _update_classification_success(
                classify_repo,
                classification_id=classification.id,
                user_id=user_id,
                category_id=parsed_result["category_id"],
                category_name=parsed_result["category_name"],
                confidence=parsed_result.get("confidence", 0.0),
                reasoning=parsed_result.get("reasoning", ""),
                tokens_used=tokens_used,
                duration_ms=duration_ms,
                provider_type=provider_type,
                model_name=used_model,
                raw_request=raw_request,
                raw_response=response
            )

            # 创建调试信息对象
            debug_info = {
                "provider_type": provider_type,
                "requested_model": model_name,
                "actual_model": used_model,
                "config_used": config,
                "tokens": {
                    "total": tokens_used,
                    "prompt": tokens_prompt,
                    "completion": tokens_completion,
                },
                "duration_ms": duration_ms,
                "app_id": app.id
            }

            # 格式化结果
            result = {
                "id": classification.id,
                "category_id": classification.category_id,
                "category_name": classification.category_name,
                "confidence": classification.confidence,
                "reasoning": classification.reasoning,
                "tokens_used": classification.tokens_used,
                "duration_ms": classification.duration_ms,
                "status": classification.status,
                "model": used_model,
                "provider_type": provider_type,
                "debug": debug_info  # 添加调试信息
            }

            return success_response(result, "图片分类成功")

        except Exception as e:
            logger.error(f"Classification error: {str(e)}\n{traceback.format_exc()}")
            
            # 提取有用的错误信息
            error_message = str(e)
            
            # 尝试从错误消息中提取有用信息
            if "url=" in error_message and "Timeout" in error_message:
                error_message = "下载图片超时，请检查图片URL是否可访问"
            elif "InvalidParameter" in error_message:
                error_message = "图片参数无效，请检查图片URL是否可访问或格式是否支持"
            
            # 更新失败状态
            _update_classification_failure(
                classify_repo,
                classification_id=classification.id,
                user_id=user_id,
                error_message=error_message,
                duration_ms=int((time.time() - start_time) * 1000),
                raw_request=raw_request
            )

            # 返回详细的错误信息
            error_result = {
                "id": classification.id,
                "status": "failed",
                "error_message": error_message,
                "duration_ms": int((time.time() - start_time) * 1000),
                "raw_error": str(e)
            }
            
            return success_response(error_result, "图片分类失败")

    except ValidationException as e:
        # 参数验证失败
        logger.warning(f"Validation error: {str(e)}")
        raise ValidationException(str(e))
    except APIException as e:
        # 业务异常
        logger.error(f"API error: {str(e)}")
        raise ValidationException(str(e))
    except Exception as e:
        # 未预期的异常
        logger.error(
            f"Unexpected error in external classify: {str(e)}\n{traceback.format_exc()}"
        )
        raise ValidationException("服务器内部错误")