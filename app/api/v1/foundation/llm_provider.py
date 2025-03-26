from flask import Blueprint, request, g
from app.core.responses import success_response
from app.core.exceptions import ValidationException
from app.domains.foundation.services.llm_service import LLMModelService, LLMProviderService
from app.infrastructure.database.repositories.llm_repository import LLMModelRepository, LLMProviderRepository,LLMProviderRepository

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

