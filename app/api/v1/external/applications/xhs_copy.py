
import time
from app.core.responses import success_response
from app.core.status_codes import GENERATION_FAILED
from app.infrastructure.database.repositories.user_app_repository import UserAppRepository
from app.infrastructure.llm_providers.factory import LLMProviderFactory
from flask import Blueprint, request, g
from app.api.middleware.app_key_auth import app_key_required
from app.core.exceptions import APIException, ValidationException
from app.domains.applications.services.xhs_copy_service import XhsCopyGenerationService
from app.infrastructure.database.repositories.llm_repository import LLMModelRepository, LLMProviderRepository
from app.infrastructure.database.repositories.user_llm_config_repository import UserLLMConfigRepository


external_xhs_copy_bp = Blueprint("external_xhs_copy", __name__,url_prefix="/xhs_copy")


@external_xhs_copy_bp.route("/generate", methods=["POST"])
@app_key_required
def external_generate():
    """生成小红书文案（外部应用调用）"""
    # app_key_auth中间件已验证密钥，并将应用和用户信息存储在g中
    app_key = g.app_key
    user_id = g.user_id
    
    # 验证请求数据
    data = request.get_json()
    if not data:
        raise ValidationException("请求数据不能为空")
    
    # 提取数据
    prompt = data.get("prompt")
    if not prompt:
        raise ValidationException("提示词不能为空")
    
    image_urls = data.get("image_urls", [])
    
    # 获取IP和用户代理
    ip_address = request.remote_addr
    user_agent = request.headers.get("User-Agent")
    
    # 初始化存储库
    db_session = g.db_session
    user_app_repo = UserAppRepository(db_session)
    user_llm_config_repo = UserLLMConfigRepository(db_session)
    
    # 获取应用信息
    app = user_app_repo.get_by_app_key(app_key)
    
    # 验证应用类型
    if app.app_type != "xhs_copy":
        raise ValidationException("该应用密钥不属于小红书文案生成应用")
    
    # 验证应用是否已发布
    if not app.published or not app.published_config:
        raise ValidationException("该应用未发布配置")
    
    # 获取用户LLM配置
    user_llm_config = None
    if "user_llm_config_id" in app.published_config and app.published_config["user_llm_config_id"]:
        user_llm_config_id = app.published_config["user_llm_config_id"]
        try:
            user_llm_config = user_llm_config_repo.get_by_id(user_llm_config_id, user_id)
        except Exception as e:
            raise APIException(f"无法获取LLM配置: {str(e)}", GENERATION_FAILED)
    
    if not user_llm_config:
        raise APIException("未配置LLM服务", GENERATION_FAILED)
    
    # 开始计时
    start_time = time.time()
    
    try:
        # 创建AI提供商实例
        ai_provider = None
        
        if user_llm_config.provider_type == "OpenAI":
            if not user_llm_config.api_key:
                raise APIException("未配置OpenAI API密钥", GENERATION_FAILED)
                
            ai_provider = LLMProviderFactory.create_provider(
                "openai",
                user_llm_config.api_key,
                api_base_url=user_llm_config.api_base_url,
                api_version=user_llm_config.api_version,
                timeout=user_llm_config.request_timeout,
                max_retries=user_llm_config.max_retries
            )
        elif user_llm_config.provider_type == "Claude":
            if not user_llm_config.api_key:
                raise APIException("未配置Claude API密钥", GENERATION_FAILED)
                
            ai_provider = LLMProviderFactory.create_provider(
                "anthropic",
                user_llm_config.api_key,
                api_base_url=user_llm_config.api_base_url,
                timeout=user_llm_config.request_timeout,
                max_retries=user_llm_config.max_retries
            )
        elif user_llm_config.provider_type in ["Volcano", "Baidu", "Aliyun", "Tencent", "Gemini"]:
            # 实现其他平台的提供商初始化
            pass
        else:
            raise APIException(f"不支持的LLM提供商类型: {user_llm_config.provider_type}", GENERATION_FAILED)
        
        if not ai_provider:
            raise APIException("初始化LLM提供商失败", GENERATION_FAILED)
        
        # 获取配置
        config = app.published_config.get("config", {})
        
        # 准备提示词
        system_prompt = config.get("system_prompt") or "你是一位专业的小红书博主，擅长编写吸引人的小红书文案。"
        
        # 获取用户提示词模板
        user_prompt_template = config.get("user_prompt_template") or "请根据以下内容，创作一篇吸引人的小红书文案：\n{prompt}"
        
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
        title_length = config.get("title_length", 50)
        content_length = config.get("content_length", 1000)
        tags_count = config.get("tags_count", 5)
        include_emojis = config.get("include_emojis", True)
        
        requirements = "\n\n请按以下要求生成文案："
        requirements += f"\n1. 标题长度不超过{title_length}个字"
        requirements += f"\n2. 正文内容{content_length}字左右"
        requirements += f"\n3. 生成{tags_count}个适合的标签"
        if include_emojis:
            requirements += "\n4. 适当地使用表情符号增加趣味性"
        requirements += "\n\n请按照以下格式输出：\n【标题】\n【正文】\n【标签】标签1 标签2 标签3..."
        
        user_prompt += requirements
        
        # 生成文案
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # 获取模型名称
        model_name = "gpt-4" # 默认模型
        
        if user_llm_config.provider_type == "OpenAI":
            model_name = config.get("model_id") or "gpt-4" 
        elif user_llm_config.provider_type == "Claude":
            model_name = config.get("model_id") or "claude-3-opus-20240229"
        
        # 设置参数
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 2000)
        
        response = ai_provider.generate_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            model=model_name
        )
        
        # 解析生成结果
        content = response["message"]["content"]
        
        # 提取标题、正文和标签
        title = ""
        body = ""
        tags = []
        
        # 简单解析结果（可根据实际输出调整）
        if "【标题】" in content:
            title_parts = content.split("【标题】")
            if len(title_parts) > 1:
                title_content = title_parts[1].split("【正文】")[0] if "【正文】" in title_parts[1] else title_parts[1]
                title = title_content.strip()
        
        if "【正文】" in content:
            body_parts = content.split("【正文】")
            if len(body_parts) > 1:
                body_content = body_parts[1].split("【标签】")[0] if "【标签】" in body_parts[1] else body_parts[1]
                body = body_content.strip()
        
        if "【标签】" in content:
            tags_part = content.split("【标签】")[1] if len(content.split("【标签】")) > 1 else ""
            # 提取标签
            tag_candidates = [tag.strip() for tag in tags_part.split() if tag.strip()]
            # 过滤非空标签
            tags = [tag for tag in tag_candidates if tag]
        
        # 如果没有按格式输出，尝试更灵活地解析
        if not title and not body:
            # 可能是自由格式输出，尝试智能提取
            lines = content.split('\n')
            if lines:
                # 第一行可能是标题
                title = lines[0].strip()
                # 剩余内容作为正文
                body = '\n'.join(lines[1:]).strip()
        
        # 计算tokens使用量
        tokens_used = response["usage"]["total_tokens"] if "usage" in response else 0
        
        # 计算处理时间
        duration_ms = int((time.time() - start_time) * 1000)
        
        # 构建结果
        result = {
            "title": title,
            "content": body,
            "tags": tags,
            "tokens_used": tokens_used,
            "duration_ms": duration_ms,
            "status": "success"
        }
        
        # 记录生成日志 (可选)
        # ...
        
        return success_response(result, "生成小红书文案成功")
        
    except Exception as e:
        # 计算处理时间
        duration_ms = int((time.time() - start_time) * 1000)
        
        # 构建错误结果
        error_result = {
            "error_message": str(e),
            "duration_ms": duration_ms,
            "status": "failed"
        }
        
        # 记录错误日志 (可选)
        # ...
        
        # 返回错误信息
        return success_response(error_result, "生成小红书文案失败", http_status_code=500)