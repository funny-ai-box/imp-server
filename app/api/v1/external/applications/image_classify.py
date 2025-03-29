# app/api/v1/external/applications/image_classify.py
import logging
import traceback
from flask import Blueprint, request, g
from app.core.responses import success_response
from app.core.exceptions import ValidationException, NotFoundException, APIException
from app.core.status_codes import PARAMETER_ERROR, APPLICATION_NOT_FOUND
from app.domains.applications.services.image_classify_service import ImageClassifyService
from app.infrastructure.database.repositories.user_app_repository import UserAppRepository
from app.infrastructure.database.repositories.image_classify_repository import ImageClassifyRepository
from app.infrastructure.database.repositories.llm_repository import (
    LLMProviderRepository,
    LLMModelRepository,
    LLMProviderConfigRepository
)
from app.api.middleware.app_key_auth import app_key_required

logger = logging.getLogger(__name__)

external_image_classify_bp = Blueprint("external_image_classify", __name__, url_prefix="/image_classify")

@external_image_classify_bp.route("/classify", methods=["POST"])
@app_key_required
def external_classify():
    """图片分类API（外部接口）"""
    try:
        # 获取app_key_auth中间件已验证的应用和用户信息
        app_key = g.app_key
        user_id = g.user_id
        app = g.app

        # 验证应用类型和发布状态
        if app.app_type != "image_classify":
            raise ValidationException("该应用密钥不属于图片分类应用", PARAMETER_ERROR)

        if not app.published or not app.published_config:
            raise ValidationException("该应用未发布配置", PARAMETER_ERROR)

        # 验证请求数据
        data = request.get_json()
        if not data:
            raise ValidationException("请求数据不能为空", PARAMETER_ERROR)

        # 提取关键参数
        image_url = data.get("image_url")
        if not image_url:
            raise ValidationException("图片URL不能为空", PARAMETER_ERROR)

        categories = data.get("categories", [])
        if not categories or not isinstance(categories, list) or len(categories) < 2:
            raise ValidationException("分类列表必须至少包含两个选项", PARAMETER_ERROR)

        # 获取IP和用户代理
        ip_address = request.remote_addr
        user_agent = request.headers.get("User-Agent")

        # 初始化存储库和服务
        db_session = g.db_session
        classify_repo = ImageClassifyRepository(db_session)
        user_app_repo = UserAppRepository(db_session)
        provider_repo = LLMProviderRepository(db_session)
        model_repo = LLMModelRepository(db_session)
        llm_provider_config_repo = LLMProviderConfigRepository(db_session)

        # 初始化服务
        classify_service = ImageClassifyService(
            classify_repo,
            user_app_repo,
            provider_repo,
            model_repo,
            llm_provider_config_repo
        )

        # 调用分类服务
        classification = classify_service.create_classification(
            image_url=image_url,
            categories=categories,
            app_id=app.id,  # 使用应用ID
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            use_published_config=True
        )

        # 创建调试信息对象
        debug_info = {
            "provider_type": classification.get("provider_type"),
            "model": classification.get("model_id"),
            "tokens": classification.get("tokens_used"),
            "duration_ms": classification.get("duration_ms"),
            "app_id": app.id
        }

        # 格式化结果
        result = {
            "id": classification.get("id"),
            "category_id": classification.get("category_id"),
            "category_name": classification.get("category_name"),
            "confidence": classification.get("confidence"),
            "reasoning": classification.get("reasoning"),
            "status": classification.get("status"),
            "tokens_used": classification.get("tokens_used"),
            "duration_ms": classification.get("duration_ms"),
            "debug": debug_info
        }

        return success_response(result, "图片分类成功")

    except ValidationException as e:
        logger.warning(f"Validation error: {str(e)}")
        raise
    except NotFoundException as e:
        logger.error(f"Not found error: {str(e)}")
        raise
    except APIException as e:
        logger.error(f"API error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
        raise APIException("服务器内部错误", PARAMETER_ERROR)