# app/api/v1/applications/app_key.py
from flask import Blueprint, request, g
from app.core.responses import success_response
from app.core.exceptions import ValidationException
from app.domains.applications.services.base_service import ApplicationService
from app.infrastructure.database.repositories.application_repository import ApplicationRepository
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.api.middleware.auth import auth_required
import uuid

app_key_bp = Blueprint("app_key", __name__, url_prefix="/app_key")

@app_key_bp.route("/list", methods=["GET"])
@auth_required
def list_app_keys():
    """获取用户的所有应用API密钥"""
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    app_repo = ApplicationRepository(db_session)
    user_repo = UserRepository(db_session)
    app_service = ApplicationService(app_repo, user_repo)
    
    # 获取应用列表
    applications = app_service.get_all_applications(user_id)
    
    return success_response(applications, "获取应用API密钥列表成功")

@app_key_bp.route("/create", methods=["POST"])
@auth_required
def create_app_key():
    """创建新的应用API密钥"""
    # 验证请求数据
    data = request.get_json()
    if not data:
        raise ValidationException("请求数据不能为空")
    
    # 确保必须字段存在
    if "name" not in data:
        raise ValidationException("缺少必填字段: name")
    
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    app_repo = ApplicationRepository(db_session)
    user_repo = UserRepository(db_session)
    app_service = ApplicationService(app_repo, user_repo)
    
    # 创建应用
    application = app_service.create_application(data, user_id)
    
    return success_response(application, "创建应用API密钥成功")

@app_key_bp.route("/get", methods=["POST"])
@auth_required
def get_app_key():
    """获取特定应用API密钥"""
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
    
    return success_response(application, "获取应用API密钥成功")

@app_key_bp.route("/update", methods=["POST"])
@auth_required
def update_app_key():
    """更新应用API密钥信息"""
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
    
    return success_response(application, "更新应用API密钥信息成功")

@app_key_bp.route("/regenerate", methods=["POST"])
@auth_required
def regenerate_app_key():
    """重新生成应用API密钥"""
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
    
    # 更新应用密钥
    new_app_key = str(uuid.uuid4()).replace("-", "")
    application = app_service.update_application(app_id, {"app_key": new_app_key}, user_id)
    
    return success_response(application, "重新生成应用API密钥成功")

@app_key_bp.route("/delete", methods=["POST"])
@auth_required
def delete_app_key():
    """删除应用API密钥"""
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
    
    return success_response(None, "删除应用API密钥成功")