from flask import Blueprint, request, g
from app.core.responses import success_response
from app.core.exceptions import ValidationException
from app.domains.foundation.services.llm_service import LLMModelService, LLMProviderConfigService, LLMProviderService
from app.infrastructure.database.repositories.llm_repository import LLMModelRepository, LLMProviderConfigRepository, LLMProviderRepository,LLMProviderRepository

from app.api.middleware.auth import auth_required




from app.infrastructure.database.repositories.user_repository import UserRepository
from app.api.middleware.auth import auth_required

llm_provider_bp = Blueprint("llm_provider", __name__)


@llm_provider_bp.route("/provider_list", methods=["GET"])
@auth_required
def list_providers():
    """获取大模型平台列表"""
    # 初始化存储库和服务
    db_session = g.db_session
    provider_repo = LLMProviderRepository(db_session)
    provider_service = LLMProviderService(provider_repo)
    
    # 获取提供商列表
    providers = provider_service.get_all_providers()
    
    return success_response(providers, "获取大模型平台列表成功")


@llm_provider_bp.route("/provider_detail", methods=["GET"])
@auth_required
def get_provider():
    """获取特定大模型平台信息"""
    # 验证请求数据
    data = request.args
    if not data or "provider_id" not in data:
        raise ValidationException("缺少必填参数: provider_id")
    
    provider_id = data["provider_id"]
    
    # 初始化存储库和服务
    db_session = g.db_session
    provider_repo = LLMProviderRepository(db_session)
    provider_service = LLMProviderService(provider_repo)
    
    # 获取提供商信息
    provider = provider_service.get_provider(provider_id)
    
    return success_response(provider, "获取大模型平台信息成功")

@llm_provider_bp.route("/model_list", methods=["GET"])
@auth_required
def list_models():
    """获取模型列表"""
    # 验证请求数据

    data = request.args
    print(data)
    if not data or "provider_id" not in data:
        raise ValidationException("缺少必填参数: provider_id")
    
    provider_id = data["provider_id"]
    
    # 初始化存储库和服务
    db_session = g.db_session
    model_repo = LLMModelRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_service = LLMModelService(model_repo, provider_repo)
    
    # 获取模型列表
    models = model_service.get_all_models(provider_id)
    
    return success_response(models, "获取模型列表成功")


@llm_provider_bp.route("/model_detail", methods=["GET"])
@auth_required
def get_model():
    """获取特定模型信息"""
    # 验证请求数据
    data = request.args()
    if not data or "model_id" not in data or "provider_id" not in data:
        raise ValidationException("缺少必填参数: model_id, provider_id")
    
    model_id = data["model_id"]
    provider_id = data["provider_id"]
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    model_repo = LLMModelRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_service = LLMModelService(model_repo, provider_repo)
    
    # 获取模型信息
    model = model_service.get_model(model_id, provider_id, user_id)
    
    return success_response(model, "获取模型信息成功")



llm_provider_config_bp = Blueprint("llm_provider_config", __name__)


@llm_provider_config_bp.route("/list", methods=["GET"])
@auth_required
def list_configs():
    """获取用户LLM配置列表"""
    user_id = g.user_id

    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = LLMProviderConfigRepository(db_session)
    config_service = LLMProviderConfigService(config_repo)

    # 获取配置列表
    configs = config_service.get_all_configs(user_id)

    return success_response(configs, "获取用户LLM配置列表成功")


@llm_provider_config_bp.route("/get", methods=["POST"])
@auth_required
def get_config():
    """获取特定LLM配置"""
    # 验证请求数据
    data = request.get_json()
    if not data or "config_id" not in data:
        raise ValidationException("缺少必填参数: config_id")

    config_id = data["config_id"]
    user_id = g.user_id

    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = LLMProviderConfigRepository(db_session)
    config_service = LLMProviderConfigService(config_repo)

    # 获取配置
    config = config_service.get_config(config_id, user_id)

    return success_response(config, "获取用户LLM配置成功")


@llm_provider_config_bp.route("/default", methods=["GET"])
@auth_required
def get_default_config():
    """获取默认LLM配置"""
    user_id = g.user_id
    provider_type = request.args.get("provider_type")

    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = LLMProviderConfigRepository(db_session)
    config_service = LLMProviderConfigService(config_repo)

    # 获取默认配置
    config = config_service.get_default_config(user_id, provider_type)

    if not config:
        return success_response(None, "未找到默认配置")

    return success_response(config, "获取默认用户LLM配置成功")


@llm_provider_config_bp.route("/create", methods=["POST"])
@auth_required
def create_config():
    """创建用户LLM配置"""
    # 验证请求数据
    data = request.get_json()
    if not data:
        raise ValidationException("请求数据不能为空")

    user_id = g.user_id

    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = LLMProviderConfigRepository(db_session)
    config_service = LLMProviderConfigService(config_repo)

    # 创建配置
    config = config_service.create_config(data, user_id)

    return success_response(config, "创建用户LLM配置成功")


@llm_provider_config_bp.route("/update", methods=["POST"])
@auth_required
def update_config():
    """更新用户LLM配置"""
    # 验证请求数据
    data = request.get_json()
    if not data or "config_id" not in data:
        raise ValidationException("缺少必填参数: config_id")

    config_id = data.pop("config_id")
    user_id = g.user_id

    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = LLMProviderConfigRepository(db_session)
    config_service = LLMProviderConfigService(config_repo)

    # 更新配置
    config = config_service.update_config(config_id, data, user_id)

    return success_response(config, "更新用户LLM配置成功")


@llm_provider_config_bp.route("/delete", methods=["POST"])
@auth_required
def delete_config():
    """删除用户LLM配置"""
    # 验证请求数据
    data = request.get_json()
    if not data or "config_id" not in data:
        raise ValidationException("缺少必填参数: config_id")

    config_id = data["config_id"]
    user_id = g.user_id

    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = LLMProviderConfigRepository(db_session)
    config_service = LLMProviderConfigService(config_repo)

    # 删除配置
    config_service.delete_config(config_id, user_id)

    return success_response(None, "删除用户LLM配置成功")


@llm_provider_config_bp.route("/set_default", methods=["POST"])
@auth_required
def set_default_config():
    """设置默认用户LLM配置"""
    # 验证请求数据
    data = request.get_json()
    if not data or "config_id" not in data:
        raise ValidationException("缺少必填参数: config_id")

    config_id = data["config_id"]
    user_id = g.user_id

    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = LLMProviderConfigRepository(db_session)
    config_service = LLMProviderConfigService(config_repo)

    # 设置默认配置
    config = config_service.set_default_config(config_id, user_id)

    return success_response(config, "设置默认用户LLM配置成功")


