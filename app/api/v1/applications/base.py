from flask import Blueprint, request, g
from app.core.responses import success_response
from app.core.exceptions import ValidationException, NotFoundException
from app.domains.applications.services.base_service import ApplicationService
from app.infrastructure.database.repositories.application_repository import ApplicationRepository
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.infrastructure.database.repositories.llm_repository import AIProviderRepository
from app.api.middleware.auth import auth_required

applications_bp = Blueprint("applications", __name__)


@applications_bp.route("/list_applications", methods=["GET"])
@auth_required
def list_applications():
    """获取应用列表"""
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    app_repo = ApplicationRepository(db_session)
    user_repo = UserRepository(db_session)
    app_service = ApplicationService(app_repo, user_repo)
    
    # 获取应用列表
    applications = app_service.get_all_applications(user_id)
    
    return success_response(applications, "获取应用列表成功")


@applications_bp.route("/get_application", methods=["POST"])
@auth_required
def get_application():
    """获取特定应用信息"""
    # 验证请求数据
    data = request.get_json()
    if not data or "app_id" not in data:
        raise ValidationException("缺少必填参数: app_id")
    
    app_id = data["app_id"]
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    app_repo = ApplicationRepository(db_session)
    user_repo = UserRepository(db_session)
    app_service = ApplicationService(app_repo, user_repo)
    
    # 获取应用信息
    application = app_service.get_application(app_id, user_id)
    
    return success_response(application, "获取应用信息成功")


@applications_bp.route("/create_application", methods=["POST"])
@auth_required
def create_application():
    """创建新的应用"""
    # 验证请求数据
    data = request.get_json()
    if not data:
        raise ValidationException("请求数据不能为空")
    
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    app_repo = ApplicationRepository(db_session)
    user_repo = UserRepository(db_session)
    app_service = ApplicationService(app_repo, user_repo)
    
    # 创建应用
    application = app_service.create_application(data, user_id)
    
    return success_response(application, "创建应用成功")


@applications_bp.route("/update_application", methods=["POST"])
@auth_required
def update_application():
    """更新应用信息"""
    # 验证请求数据
    data = request.get_json()
    if not data or "app_id" not in data:
        raise ValidationException("缺少必填参数: app_id")
    
    app_id = data.pop("app_id")
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    app_repo = ApplicationRepository(db_session)
    user_repo = UserRepository(db_session)
    app_service = ApplicationService(app_repo, user_repo)
    
    # 更新应用
    application = app_service.update_application(app_id, data, user_id)
    
    return success_response(application, "更新应用信息成功")


@applications_bp.route("/delete_application", methods=["POST"])
@auth_required
def delete_application():
    """删除应用"""
    # 验证请求数据
    data = request.get_json()
    if not data or "app_id" not in data:
        raise ValidationException("缺少必填参数: app_id")
    
    app_id = data["app_id"]
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    app_repo = ApplicationRepository(db_session)
    user_repo = UserRepository(db_session)
    app_service = ApplicationService(app_repo, user_repo)
    
    # 删除应用
    app_service.delete_application(app_id, user_id)
    
    return success_response(None, "删除应用成功")