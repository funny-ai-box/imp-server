# app/api/v1/applications/app_store.py (修改)
from flask import Blueprint, request, g
from app.core.responses import success_response
from app.core.exceptions import ValidationException
from app.domains.applications.services.app_store_service import AppStoreService
from app.domains.applications.services.user_app_service import UserAppService
from app.infrastructure.database.repositories.app_template_repository import (
    AppTemplateRepository,
)
from app.infrastructure.database.repositories.user_app_repository import (
    UserAppRepository,
)
from app.infrastructure.database.repositories.user_llm_config_repository import (
    UserLLMConfigRepository,
)
from app.api.middleware.auth import auth_required

app_store_bp = Blueprint("app_store", __name__, url_prefix="/store")


@app_store_bp.route("/list", methods=["GET"])
@auth_required
def list_available_apps():
    """获取应用商店中可用的应用列表"""
    # 初始化存储库和服务
    db_session = g.db_session
    template_repo = AppTemplateRepository(db_session)
    app_store_service = AppStoreService(template_repo)

    # 获取应用模板列表
    templates = app_store_service.get_all_templates()

    return success_response(templates, "获取可用应用列表成功")


@app_store_bp.route("/detail", methods=["GET"])
@auth_required
def get_app_details():
    """获取特定应用的详细信息"""
    # 验证请求数据
    data = request.args
    if not data:
        raise ValidationException("请求数据不能为空")
    app_id = data.get("id")
    if not app_id :
        raise ValidationException("请提供app_id")
    # 初始化存储库和服务
    db_session = g.db_session
    template_repo = AppTemplateRepository(db_session)
    app_store_service = AppStoreService(template_repo)
    template = app_store_service.get_template_by_id(app_id)
    return success_response(template, "获取应用详情成功")


@app_store_bp.route("/instantiate", methods=["POST"])
@auth_required
def instantiate_app():
    """从模板实例化应用"""
    # 验证请求数据
    data = request.get_json()
    if not data or "template_id" not in data:
        raise ValidationException("缺少必填参数: template_id")

    template_id = data["template_id"]
    custom_config = data.get("config")
    custom_name = data.get("name")
    user_id = g.user_id

    # 初始化存储库和服务
    db_session = g.db_session
    template_repo = AppTemplateRepository(db_session)
    user_app_repo = UserAppRepository(db_session)
    user_llm_config_repo = UserLLMConfigRepository(db_session)

    user_app_service = UserAppService(
        user_app_repo, template_repo, user_llm_config_repo
    )

    # 实例化应用
    app = user_app_service.instantiate_from_template(
        template_id=template_id, user_id=user_id, custom_config=custom_config
    )

    # 如果提供了自定义名称，更新应用名称
    if custom_name:
        app = user_app_service.update_app(
            app_id=app["id"], app_data={"name": custom_name}, user_id=user_id
        )

    return success_response(app, "应用实例化成功")
