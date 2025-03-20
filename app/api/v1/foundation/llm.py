from flask import Blueprint, request, g
from app.core.responses import success_response
from app.core.exceptions import ValidationException
from app.domains.model_management.services.ai_model_service import AIModelService
from app.infrastructure.database.repositories.ai_model_repository import AIModelRepository
from app.infrastructure.database.repositories.ai_provider_repository import AIProviderRepository
from app.api.middleware.auth import auth_required

ai_models_bp = Blueprint("ai_models", __name__)


from flask import Blueprint, request, g
from app.core.responses import success_response
from app.core.exceptions import ValidationException
from app.domains.model_management.services.ai_provider_service import AIProviderService
from app.infrastructure.database.repositories.ai_provider_repository import AIProviderRepository
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.api.middleware.auth import auth_required

ai_providers_bp = Blueprint("ai_providers", __name__)


@ai_providers_bp.route("/list_providers", methods=["GET"])
@auth_required
def list_providers():
    """获取大模型平台列表"""
    # 获取当前用户ID
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    provider_repo = AIProviderRepository(db_session)
    user_repo = UserRepository(db_session)
    provider_service = AIProviderService(provider_repo, user_repo)
    
    # 获取提供商列表
    providers = provider_service.get_all_providers(user_id)
    
    return success_response(providers, "获取大模型平台列表成功")


@ai_providers_bp.route("/get_provider", methods=["POST"])
@auth_required
def get_provider():
    """获取特定大模型平台信息"""
    # 验证请求数据
    data = request.get_json()
    if not data or "provider_id" not in data:
        raise ValidationException("缺少必填参数: provider_id")
    
    provider_id = data["provider_id"]
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    provider_repo = AIProviderRepository(db_session)
    user_repo = UserRepository(db_session)
    provider_service = AIProviderService(provider_repo, user_repo)
    
    # 获取提供商信息
    provider = provider_service.get_provider(provider_id, user_id)
    
    return success_response(provider, "获取大模型平台信息成功")


@ai_providers_bp.route("/create_provider", methods=["POST"])
@auth_required
def create_provider():
    """创建新的大模型平台(用户自己配置)"""
    # 验证请求数据
    data = request.get_json()
    if not data:
        raise ValidationException("请求数据不能为空")
    
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    provider_repo = AIProviderRepository(db_session)
    user_repo = UserRepository(db_session)
    provider_service = AIProviderService(provider_repo, user_repo)
    
    # 创建提供商(用户自己配置的API密钥等信息)
    provider = provider_service.create_provider(data, user_id)
    
    return success_response(provider, "成功创建大模型平台配置")


@ai_providers_bp.route("/update_provider", methods=["POST"])
@auth_required
def update_provider():
    """更新大模型平台信息"""
    # 验证请求数据
    data = request.get_json()
    if not data or "provider_id" not in data:
        raise ValidationException("缺少必填参数: provider_id")
    
    provider_id = data.pop("provider_id")
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    provider_repo = AIProviderRepository(db_session)
    user_repo = UserRepository(db_session)
    provider_service = AIProviderService(provider_repo, user_repo)
    
    # 更新提供商
    provider = provider_service.update_provider(provider_id, data, user_id)
    
    return success_response(provider, "更新大模型平台信息成功")


@ai_providers_bp.route("/delete_provider", methods=["POST"])
@auth_required
def delete_provider():
    """删除大模型平台"""
    # 验证请求数据
    data = request.get_json()
    if not data or "provider_id" not in data:
        raise ValidationException("缺少必填参数: provider_id")
    
    provider_id = data["provider_id"]
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    provider_repo = AIProviderRepository(db_session)
    user_repo = UserRepository(db_session)
    provider_service = AIProviderService(provider_repo, user_repo)
    
    # 删除提供商
    provider_service.delete_provider(provider_id, user_id)
    
    return success_response(None, "删除大模型平台成功")

@ai_providers_bp.route("/provider_types", methods=["GET"])
@auth_required
def list_provider_types():
    """获取支持的大模型平台类型列表"""
    provider_types = [
        {
            "type": "OpenAI",
            "name": "OpenAI",
            "description": "OpenAI提供的大模型服务，包括GPT-3.5、GPT-4等模型",
            "config_fields": [
                {"name": "api_key", "description": "OpenAI API密钥", "required": True},
                {"name": "api_base_url", "description": "API基础URL(可选)", "required": False},
                {"name": "api_version", "description": "API版本(可选)", "required": False}
            ],
            "website": "https://openai.com"
        },
        {
            "type": "Claude",
            "name": "Anthropic Claude",
            "description": "Anthropic公司提供的Claude系列大语言模型",
            "config_fields": [
                {"name": "api_key", "description": "Anthropic API密钥", "required": True},
                {"name": "api_base_url", "description": "API基础URL(可选)", "required": False}
            ],
            "website": "https://anthropic.com"
        },
        {
            "type": "Volcano",
            "name": "火山引擎",
            "description": "字节跳动旗下的火山引擎AI服务",
            "config_fields": [
                {"name": "api_key", "description": "火山引擎API密钥", "required": True},
                {"name": "api_base_url", "description": "API基础URL(必填)", "required": True},
                {"name": "api_version", "description": "API版本(可选)", "required": False}
            ],
            "website": "https://www.volcengine.com/"
        }
    ]
    
    return success_response(provider_types, "获取支持的大模型平台类型列表成功")

@ai_models_bp.route("/list_models", methods=["POST"])
@auth_required
def list_models():
    """获取模型列表"""
    # 验证请求数据
    data = request.get_json()
    if not data or "provider_id" not in data:
        raise ValidationException("缺少必填参数: provider_id")
    
    provider_id = data["provider_id"]
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    model_repo = AIModelRepository(db_session)
    provider_repo = AIProviderRepository(db_session)
    model_service = AIModelService(model_repo, provider_repo)
    
    # 获取模型列表
    models = model_service.get_all_models(provider_id, user_id)
    
    return success_response(models, "获取模型列表成功")


@ai_models_bp.route("/get_model", methods=["POST"])
@auth_required
def get_model():
    """获取特定模型信息"""
    # 验证请求数据
    data = request.get_json()
    if not data or "model_id" not in data or "provider_id" not in data:
        raise ValidationException("缺少必填参数: model_id, provider_id")
    
    model_id = data["model_id"]
    provider_id = data["provider_id"]
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    model_repo = AIModelRepository(db_session)
    provider_repo = AIProviderRepository(db_session)
    model_service = AIModelService(model_repo, provider_repo)
    
    # 获取模型信息
    model = model_service.get_model(model_id, provider_id, user_id)
    
    return success_response(model, "获取模型信息成功")


@ai_models_bp.route("/create_model", methods=["POST"])
@auth_required
def create_model():
    """创建新的模型"""
    # 验证请求数据
    data = request.get_json()
    if not data or "provider_id" not in data:
        raise ValidationException("缺少必填参数: provider_id")
    
    provider_id = data.pop("provider_id")
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    model_repo = AIModelRepository(db_session)
    provider_repo = AIProviderRepository(db_session)
    model_service = AIModelService(model_repo, provider_repo)
    
    # 创建模型
    model = model_service.create_model(data, provider_id, user_id)
    
    return success_response(model, "创建模型成功")


@ai_models_bp.route("/update_model", methods=["POST"])
@auth_required
def update_model():
    """更新模型信息"""
    # 验证请求数据
    data = request.get_json()
    if not data or "model_id" not in data or "provider_id" not in data:
        raise ValidationException("缺少必填参数: model_id, provider_id")
    
    model_id = data.pop("model_id")
    provider_id = data.pop("provider_id")
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    model_repo = AIModelRepository(db_session)
    provider_repo = AIProviderRepository(db_session)
    model_service = AIModelService(model_repo, provider_repo)
    
    # 更新模型
    model = model_service.update_model(model_id, data, provider_id, user_id)
    
    return success_response(model, "更新模型信息成功")


@ai_models_bp.route("/delete_model", methods=["POST"])
@auth_required
def delete_model():
    """删除模型"""
    # 验证请求数据
    data = request.get_json()
    if not data or "model_id" not in data or "provider_id" not in data:
        raise ValidationException("缺少必填参数: model_id, provider_id")
    
    model_id = data["model_id"]
    provider_id = data["provider_id"]
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    model_repo = AIModelRepository(db_session)
    provider_repo = AIProviderRepository(db_session)
    model_service = AIModelService(model_repo, provider_repo)
    
    # 删除模型
    model_service.delete_model(model_id, provider_id, user_id)
    
    return success_response(None, "删除模型成功")