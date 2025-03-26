# app/api/v1/applications/image_classify.py
from flask import Blueprint, request, g
from app.core.responses import success_response
from app.core.exceptions import ValidationException
from app.domains.applications.services.image_classify_service import (
    ImageClassifyService
)
from app.infrastructure.database.repositories.user_app_repository import (
    UserAppRepository,
)
from app.infrastructure.database.repositories.image_classify_repository import (
    ImageClassifyRepository,
)
from app.infrastructure.database.repositories.llm_repository import (
    LLMProviderRepository,
    LLMModelRepository,LLMProviderConfigRepository
)

from app.api.middleware.auth import auth_required
import logging
import traceback

logger = logging.getLogger(__name__)

image_classify_bp = Blueprint("image_classify", __name__)


# 图片分类接口
@image_classify_bp.route("/classify", methods=["POST"])
@auth_required
def classify_image():
    """生成图片分类（用户接口）"""
    try:
        user_id = g.user_id

        # 验证请求数据
        data = request.get_json()
        if not data:
            raise ValidationException("请求数据不能为空")

        # 提取数据
        image_url = data.get("image_url")
        if not image_url:
            raise ValidationException("图片URL不能为空")

        categories = data.get("categories", [])
        if not categories or not isinstance(categories, list) or len(categories) < 2:
            raise ValidationException("分类列表必须至少包含两个选项")

        app_id = data.get("app_id")  # 可选参数

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

        classify_service = ImageClassifyService(
            classify_repo,
            user_app_repo,
            provider_repo,
            model_repo,
            llm_provider_config_repo,
        )

        # 执行图片分类
        classification = classify_service.create_classification(
            image_url=image_url,
            categories=categories,
            app_id=app_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return success_response(classification, "图片分类成功")
    except Exception as e:
        # 记录未知错误
        if not isinstance(e, ValidationException):
            logger.error(
                f"Error classifying image: {str(e)}\n{traceback.format_exc()}"
            )
        raise


@image_classify_bp.route("/classifications", methods=["GET"])
@auth_required
def list_classifications():
    """获取图片分类历史记录"""
    try:
        user_id = g.user_id

        # 获取分页和过滤参数
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))

        # 过滤条件
        filters = {}
        if "status" in request.args:
            filters["status"] = request.args.get("status")

        if "app_id" in request.args:
            filters["app_id"] = int(request.args.get("app_id"))

        if "start_date" in request.args and "end_date" in request.args:
            filters["start_date"] = request.args.get("start_date")
            filters["end_date"] = request.args.get("end_date")

        # 初始化存储库和服务
        db_session = g.db_session
        classify_repo = ImageClassifyRepository(db_session)
        user_app_repo = UserAppRepository(db_session)
        provider_repo = LLMProviderRepository(db_session)
        model_repo = LLMModelRepository(db_session)
        llm_provider_config_repo = LLMProviderConfigRepository(db_session)

        classify_service = ImageClassifyService(
            classify_repo,
            user_app_repo,
            provider_repo,
            model_repo,
            llm_provider_config_repo,
        )

        # 获取分类记录
        classifications, total = classify_service.get_all_classifications(
            user_id=user_id, page=page, per_page=per_page, **filters
        )

        return success_response(
            {"items": classifications, "total": total, "page": page, "per_page": per_page},
            "获取图片分类历史记录成功",
        )
    except Exception as e:
        # 记录未知错误
        if not isinstance(e, ValidationException):
            logger.error(
                f"Error listing classifications: {str(e)}\n{traceback.format_exc()}"
            )
        raise