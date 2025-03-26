# app/api/v1/applications/xhs_copy/xhs_copy.py
from flask import Blueprint, request, g
from app.core.responses import success_response
from app.core.exceptions import ValidationException
from app.domains.applications.services.xhs_copy_service import (
    XhsCopyGenerationService,
)
from app.infrastructure.database.repositories.user_app_repository import (
    UserAppRepository,
)
from app.infrastructure.database.repositories.xhs_copy_repository import (
    XhsCopyGenerationRepository,
)
from app.infrastructure.database.repositories.llm_repository import (
    LLMProviderRepository,
    LLMModelRepository,
)
from app.infrastructure.database.repositories.user_llm_config_repository import (
    UserLLMConfigRepository,
)
from app.api.middleware.auth import auth_required
import logging
import traceback

logger = logging.getLogger(__name__)

xhs_copy_bp = Blueprint("xhs_copy", __name__)


# 文案生成接口
@xhs_copy_bp.route("/generate", methods=["POST"])
@auth_required
def generate_content():
    """生成小红书文案（用户接口）"""
    try:
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
 

        # 验证图片URL格式
        if image_urls:
            for url in image_urls:
                if not url.startswith(("http://", "https://")):
                    raise ValidationException(f"无效的图片URL: {url}")

        # 获取IP和用户代理
        ip_address = request.remote_addr
        user_agent = request.headers.get("User-Agent")

        # 初始化存储库和服务
        db_session = g.db_session
        generation_repo = XhsCopyGenerationRepository(db_session)

        provider_repo = LLMProviderRepository(db_session)
        model_repo = LLMModelRepository(db_session)
        user_llm_config_repo = UserLLMConfigRepository(db_session)

        generation_service = XhsCopyGenerationService(
            generation_repo,
            provider_repo,
            model_repo,
            user_llm_config_repo,
        )

        # 生成文案
        generation = generation_service.create_generation(
            prompt=prompt,
            image_urls=image_urls,
   
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return success_response(generation, "生成小红书文案成功")
    except Exception as e:
        # 记录未知错误
        if not isinstance(e, ValidationException):
            logger.error(
                f"Error generating content: {str(e)}\n{traceback.format_exc()}"
            )
        raise


@xhs_copy_bp.route("/generations", methods=["GET"])
@auth_required
def list_generations():
    """获取小红书文案生成历史记录"""
    try:
        user_id = g.user_id

        # 获取分页和过滤参数
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))

        # 过滤条件
        filters = {}
        if "status" in request.args:
            filters["status"] = request.args.get("status")

        if "config_id" in request.args:
            filters["config_id"] = int(request.args.get("config_id"))

        if "app_id" in request.args:
            filters["app_id"] = int(request.args.get("app_id"))

        if "start_date" in request.args and "end_date" in request.args:
            filters["start_date"] = request.args.get("start_date")
            filters["end_date"] = request.args.get("end_date")

        # 初始化存储库和服务
        db_session = g.db_session
        generation_repo = XhsCopyGenerationRepository(db_session)
        user_app_repo = UserAppRepository(db_session)
        provider_repo = LLMProviderRepository(db_session)
        model_repo = LLMModelRepository(db_session)
        user_llm_config_repo = UserLLMConfigRepository(db_session)

        generation_service = XhsCopyGenerationService(
            generation_repo,
            user_app_repo,
            provider_repo,
            model_repo,
            user_llm_config_repo,
        )

        # 获取生成记录
        generations, total = generation_service.get_all_generations(
            user_id=user_id, page=page, per_page=per_page, **filters
        )

        return success_response(
            {"items": generations, "total": total, "page": page, "per_page": per_page},
            "获取小红书文案生成历史记录成功",
        )
    except Exception as e:
        # 记录未知错误
        if not isinstance(e, ValidationException):
            logger.error(
                f"Error listing generations: {str(e)}\n{traceback.format_exc()}"
            )
        raise


