# app/api/v1/external/applications/xhs_copy.py
import time
import logging
import traceback
from app.core.responses import success_response
from app.core.status_codes import GENERATION_FAILED, PARAMETER_ERROR
from app.infrastructure.database.repositories.user_app_repository import UserAppRepository
from app.infrastructure.database.repositories.user_llm_config_repository import UserLLMConfigRepository
from app.infrastructure.database.repositories.xhs_copy_repository import (
    XhsCopyConfigRepository,
    XhsCopyGenerationRepository
)
from app.infrastructure.database.repositories.llm_repository import LLMModelRepository, LLMProviderRepository
from app.domains.applications.services.xhs_copy_service import XhsCopyGenerationService
from flask import Blueprint, request, g
from app.api.middleware.app_key_auth import app_key_required
from app.core.exceptions import APIException, ValidationException

logger = logging.getLogger(__name__)

external_xhs_copy_bp = Blueprint("external_xhs_copy", __name__, url_prefix="/xhs_copy")

@external_xhs_copy_bp.route("/generate", methods=["POST"])
@app_key_required
def external_generate():
    """生成小红书文案（外部应用调用）"""
    try:
        # 获取app_key_auth中间件已验证的应用和用户信息
        app_key = g.app_key
        user_id = g.user_id
        app = g.app
        
        # 验证请求数据
        data = _validate_and_extract_params(request)
        
        # 验证应用类型和发布状态
        if app.app_type != "xhs_copy":
            raise ValidationException("该应用密钥不属于小红书文案生成应用", PARAMETER_ERROR)
        
        if not app.published or not app.published_config:
            raise ValidationException("该应用未发布配置", PARAMETER_ERROR)
        
        # 获取IP和用户代理
        ip_address = request.remote_addr
        user_agent = request.headers.get("User-Agent")
        
        # 初始化服务和仓库
        db_session = g.db_session
        generation_service = _initialize_generation_service(db_session)
        
        # 提取数据
        prompt = data["prompt"]
        image_urls = data.get("image_urls", [])
        config_id = app.published_config.get("config_id")
        
        # 调用服务生成文案
        generation = generation_service.create_generation(
            prompt=prompt,
            image_urls=image_urls,
            config_id=config_id,
            app_id=app.id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # 格式化结果
        result = {
            "title": generation["title"],
            "content": generation["content"],
            "tags": generation["tags"],
            "tokens_used": generation["tokens_used"],
            "duration_ms": generation["duration_ms"],
            "status": generation["status"],
            "generation_id": generation["id"]
        }
        
        return success_response(result, "生成小红书文案成功")
    
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
        logger.error(f"Unexpected error in external generate: {str(e)}\n{traceback.format_exc()}")
        raise APIException(f"生成文案失败: {str(e)}", GENERATION_FAILED)

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
            if not isinstance(url, str) or not url.startswith(('http://', 'https://')):
                raise ValidationException(f"无效的图片URL: {url}", PARAMETER_ERROR)
    
    return data

def _initialize_generation_service(db_session):
    """初始化生成服务"""
    generation_repo = XhsCopyGenerationRepository(db_session)
    config_repo = XhsCopyConfigRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    user_llm_config_repo = UserLLMConfigRepository(db_session)
    
    return XhsCopyGenerationService(
        generation_repo, config_repo, provider_repo, model_repo, user_llm_config_repo
    )

@external_xhs_copy_bp.route("/rate", methods=["POST"])
@app_key_required
def rate_generation():
    """评价生成结果（外部应用调用）"""
    try:
        # app_key_auth中间件已验证密钥，并将应用和用户信息存储在g中
        user_id = g.user_id
        
        # 验证请求数据
        data = request.get_json()
        if not data:
            raise ValidationException("请求数据不能为空", PARAMETER_ERROR)
        
        # 提取评分参数
        generation_id = data.get("generation_id")
        if not generation_id:
            raise ValidationException("缺少必填参数: generation_id", PARAMETER_ERROR)
        
        rating = data.get("rating")
        if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
            raise ValidationException("评分必须是1-5之间的整数", PARAMETER_ERROR)
        
        feedback = data.get("feedback")
        
        # 初始化服务
        db_session = g.db_session
        generation_service = _initialize_generation_service(db_session)
        
        # 提交评分
        generation = generation_service.rate_generation(
            generation_id=generation_id,
            user_id=user_id,
            rating=rating,
            feedback=feedback
        )
        
        return success_response({"success": True}, "评分提交成功")
        
    except ValidationException as e:
        raise
    except APIException as e:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in rate generation: {str(e)}\n{traceback.format_exc()}")
        raise APIException(f"评分提交失败: {str(e)}", GENERATION_FAILED)