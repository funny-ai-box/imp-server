# app/api/v1/applications/user_app.py
from app.infrastructure.database.repositories.app_template_repository import AppTemplateRepository
from flask import Blueprint, request, g
from app.core.responses import success_response
from app.core.exceptions import ValidationException
from app.domains.applications.services.user_app_service import UserAppService
from app.infrastructure.database.repositories.user_app_repository import UserAppRepository
from app.infrastructure.database.repositories.llm_repository import LLMProviderConfigRepository
from app.api.middleware.auth import auth_required

user_app_bp = Blueprint("user_app", __name__, url_prefix="/user_app")

@user_app_bp.route("/list", methods=["GET"])
@auth_required
def list_user_apps():
    """获取用户的所有应用"""
    user_id = g.user_id
    app_type = request.args.get("app_type")  # 可选按类型过滤
    
    # 初始化存储库和服务
    db_session = g.db_session
    user_app_repo = UserAppRepository(db_session)
    llm_provider_config_repo = LLMProviderConfigRepository(db_session)
    user_app_service = UserAppService(user_app_repo, llm_provider_config_repo)
    
    # 获取应用列表
    apps = user_app_service.get_all_apps(user_id)
    
    # 按类型过滤
    if app_type:
        apps = [app for app in apps if app["app_type"] == app_type]
    
    return success_response(apps, "获取用户应用列表成功")

@user_app_bp.route("/detail", methods=["GET"])
@auth_required
def get_user_app():
    """获取特定应用"""
    # 验证请求数据
    data = request.args
    if not data or "app_id" not in data:
        raise ValidationException("缺少必填参数: app_id")
    
    app_id = data["app_id"]
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    user_app_repo = UserAppRepository(db_session)
    llm_provider_config_repo = LLMProviderConfigRepository(db_session)
    user_app_service = UserAppService(user_app_repo, llm_provider_config_repo)
    
    # 获取应用
    app = user_app_service.get_app(app_id, user_id)
    
    return success_response(app, "获取应用成功")


@user_app_bp.route("/update", methods=["POST"])
@auth_required
def update_user_app():
    """更新用户应用配置"""
    # 验证请求数据
    data = request.get_json()
    if not data or "app_id" not in data:
        raise ValidationException("缺少必填参数: app_id")
    
    app_id = data.pop("app_id")
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    user_app_repo = UserAppRepository(db_session)
    llm_provider_config_repo = LLMProviderConfigRepository(db_session)
    user_app_service = UserAppService(user_app_repo, llm_provider_config_repo)
    
    # 更新应用
    app = user_app_service.update_app(app_id, data, user_id)
    
    return success_response(app, "应用更新成功")

@user_app_bp.route("/publish", methods=["POST"])
@auth_required
def publish_user_app():
    """发布应用配置"""
    # 验证请求数据
    data = request.get_json()
    if not data or "app_id" not in data:
        raise ValidationException("缺少必填参数: app_id")
    
    app_id = data["app_id"]
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    user_app_repo = UserAppRepository(db_session)
    app_template_repo = AppTemplateRepository(db_session)
    llm_provider_config_repo = LLMProviderConfigRepository(db_session)
    user_app_service = UserAppService(user_app_repo,app_template_repo, llm_provider_config_repo)
    
    # 发布应用
    app = user_app_service.publish_app(app_id, user_id)
   
    return success_response(app, "应用配置发布成功")

@user_app_bp.route("/unpublish", methods=["POST"])
@auth_required
def unpublish_user_app():
   """取消发布应用"""
   # 验证请求数据
   data = request.get_json()
   if not data or "app_id" not in data:
       raise ValidationException("缺少必填参数: app_id")
   
   app_id = data["app_id"]
   user_id = g.user_id
   
   # 初始化存储库和服务
   db_session = g.db_session
   user_app_repo = UserAppRepository(db_session)
   llm_provider_config_repo = LLMProviderConfigRepository(db_session)
   user_app_service = UserAppService(user_app_repo, llm_provider_config_repo)
   
   # 取消发布应用
   app = user_app_service.unpublish_app(app_id, user_id)
   
   return success_response(app, "应用已取消发布")

@user_app_bp.route("/delete", methods=["POST"])
@auth_required
def delete_user_app():
   """删除用户应用"""
   # 验证请求数据
   data = request.get_json()
   if not data or "app_id" not in data:
       raise ValidationException("缺少必填参数: app_id")
   
   app_id = data["app_id"]
   user_id = g.user_id
   
   # 初始化存储库和服务
   db_session = g.db_session
   user_app_repo = UserAppRepository(db_session)
   llm_provider_config_repo = LLMProviderConfigRepository(db_session)
   user_app_service = UserAppService(user_app_repo, llm_provider_config_repo)
   
   # 删除应用
   user_app_service.delete_app(app_id, user_id)
   
   return success_response(None, "应用删除成功")

@user_app_bp.route("/regenerate_key", methods=["POST"])
@auth_required
def regenerate_app_key():
   """重新生成应用密钥"""
   # 验证请求数据
   data = request.get_json()
   if not data or "app_id" not in data:
       raise ValidationException("缺少必填参数: app_id")
   
   app_id = data["app_id"]
   user_id = g.user_id
   
   # 初始化存储库和服务
   db_session = g.db_session
   user_app_repo = UserAppRepository(db_session)
   llm_provider_config_repo = LLMProviderConfigRepository(db_session)
   user_app_service = UserAppService(user_app_repo, llm_provider_config_repo)
   
   # 重新生成密钥
   app = user_app_service.regenerate_app_key(app_id, user_id)
   
   return success_response(app, "应用密钥已重新生成")