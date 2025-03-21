
from flask import Blueprint, request, g
from app.core.responses import success_response
from app.core.exceptions import ValidationException
from app.domains.applications.services.xhs_copy_service import XhsCopyConfigService
from app.infrastructure.database.repositories.xhs_copy_repository import XhsCopyConfigRepository
from app.infrastructure.database.repositories.llm_repository import LLMProviderRepository, LLMModelRepository
from app.infrastructure.database.repositories.user_llm_config_repository import UserLLMConfigRepository
from app.api.middleware.auth import auth_required

xhs_copy_config_bp = Blueprint("xhs_copy_config", __name__, url_prefix="/configs")

@xhs_copy_config_bp.route("/list", methods=["GET"])
@auth_required
def list_configs():
    """获取用户的小红书文案生成配置列表"""
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = XhsCopyConfigRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    user_llm_config_repo = UserLLMConfigRepository(db_session)
    config_service = XhsCopyConfigService(config_repo, provider_repo, model_repo, user_llm_config_repo)
    
    # 获取配置列表
    configs = config_service.get_all_configs(user_id)
    
    return success_response(configs, "获取小红书配置列表成功")

@xhs_copy_config_bp.route("/get", methods=["POST"])
@auth_required
def get_config():
    """获取特定小红书应用配置"""
    # 验证请求数据
    data = request.get_json()
    if not data or "config_id" not in data:
        raise ValidationException("缺少必填参数: config_id")
    
    config_id = data["config_id"]
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = XhsCopyConfigRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    user_llm_config_repo = UserLLMConfigRepository(db_session)
    config_service = XhsCopyConfigService(config_repo, provider_repo, model_repo, user_llm_config_repo)
    
    # 获取配置
    config = config_service.get_config(config_id, user_id)
    
    return success_response(config, "获取小红书配置成功")

@xhs_copy_config_bp.route("/default", methods=["GET"])
@auth_required
def get_default_config():
    """获取默认小红书应用配置"""
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = XhsCopyConfigRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    user_llm_config_repo = UserLLMConfigRepository(db_session)
    config_service = XhsCopyConfigService(config_repo, provider_repo, model_repo, user_llm_config_repo)
    
    # 获取默认配置
    config = config_service.get_default_config(user_id)
    
    if not config:
        return success_response(None, "未找到默认配置")
    
    return success_response(config, "获取默认小红书配置成功")

@xhs_copy_config_bp.route("/create", methods=["POST"])
@auth_required
def create_config():
    """创建小红书应用配置"""
    # 验证请求数据
    data = request.get_json()
    if not data:
        raise ValidationException("请求数据不能为空")
    
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = XhsCopyConfigRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    user_llm_config_repo = UserLLMConfigRepository(db_session)
    config_service = XhsCopyConfigService(config_repo, provider_repo, model_repo, user_llm_config_repo)
    
    # 创建配置
    config = config_service.create_config(data, user_id)
    
    return success_response(config, "创建小红书配置成功")

@xhs_copy_config_bp.route("/update", methods=["POST"])
@auth_required
def update_config():
    """更新小红书应用配置"""
    # 验证请求数据
    data = request.get_json()
    if not data or "config_id" not in data:
        raise ValidationException("缺少必填参数: config_id")
    
    config_id = data.pop("config_id")
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = XhsCopyConfigRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    user_llm_config_repo = UserLLMConfigRepository(db_session)
    config_service = XhsCopyConfigService(config_repo, provider_repo, model_repo, user_llm_config_repo)
    
    # 更新配置
    config = config_service.update_config(config_id, data, user_id)
    
    return success_response(config, "更新小红书配置成功")

@xhs_copy_config_bp.route("/delete", methods=["POST"])
@auth_required
def delete_config():
    """删除小红书应用配置"""
    # 验证请求数据
    data = request.get_json()
    if not data or "config_id" not in data:
        raise ValidationException("缺少必填参数: config_id")
    
    config_id = data["config_id"]
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = XhsCopyConfigRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    user_llm_config_repo = UserLLMConfigRepository(db_session)
    config_service = XhsCopyConfigService(config_repo, provider_repo, model_repo, user_llm_config_repo)
    
    # 删除配置
    config_service.delete_config(config_id, user_id)
    
    return success_response(None, "删除小红书配置成功")

@xhs_copy_config_bp.route("/set_default", methods=["POST"])
@auth_required
def set_default_config():
    """设置默认小红书应用配置"""
    # 验证请求数据
    data = request.get_json()
    if not data or "config_id" not in data:
        raise ValidationException("缺少必填参数: config_id")
    
    config_id = data["config_id"]
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = XhsCopyConfigRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    user_llm_config_repo = UserLLMConfigRepository(db_session)
    config_service = XhsCopyConfigService(config_repo, provider_repo, model_repo, user_llm_config_repo)
    
    # 设置默认配置
    config = config_service.set_default_config(config_id, user_id)
    
    return success_response(config, "设置默认小红书配置成功")

@xhs_copy_config_bp.route("/available_llm_configs", methods=["GET"])
@auth_required
def get_available_llm_configs():
    """获取用户可用的LLM配置"""
    user_id = g.user_id
    
    # 初始化存储库
    db_session = g.db_session
    user_llm_config_repo = UserLLMConfigRepository(db_session)
    
    # 获取用户的所有LLM配置
    configs = user_llm_config_repo.get_all_by_user(user_id)
    
    # 格式化配置列表，只返回必要信息
    formatted_configs = [
        {
            "id": config.id,
            "name": config.name,
            "provider_type": config.provider_type,
            "is_default": config.is_default,
            "is_active": config.is_active,
        }
        for config in configs if config.is_active
    ]
    
    return success_response(formatted_configs, "获取可用LLM配置成功")