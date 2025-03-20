# app/api/v1/foundation/user_llm_config.py
from flask import Blueprint, request, g
from app.core.responses import success_response
from app.core.exceptions import ValidationException
from app.domains.foundation.services.user_llm_config_service import UserLLMConfigService
from app.infrastructure.database.repositories.user_llm_config_repository import (
    UserLLMConfigRepository,
)
from app.api.middleware.auth import auth_required

user_llm_config_bp = Blueprint("user_llm_config", __name__)


@user_llm_config_bp.route("/list", methods=["GET"])
@auth_required
def list_configs():
    """获取用户LLM配置列表"""
    user_id = g.user_id

    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = UserLLMConfigRepository(db_session)
    config_service = UserLLMConfigService(config_repo)

    # 获取配置列表
    configs = config_service.get_all_configs(user_id)

    return success_response(configs, "获取用户LLM配置列表成功")


@user_llm_config_bp.route("/get", methods=["POST"])
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
    config_repo = UserLLMConfigRepository(db_session)
    config_service = UserLLMConfigService(config_repo)

    # 获取配置
    config = config_service.get_config(config_id, user_id)

    return success_response(config, "获取用户LLM配置成功")


@user_llm_config_bp.route("/default", methods=["GET"])
@auth_required
def get_default_config():
    """获取默认LLM配置"""
    user_id = g.user_id
    provider_type = request.args.get("provider_type")

    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = UserLLMConfigRepository(db_session)
    config_service = UserLLMConfigService(config_repo)

    # 获取默认配置
    config = config_service.get_default_config(user_id, provider_type)

    if not config:
        return success_response(None, "未找到默认配置")

    return success_response(config, "获取默认用户LLM配置成功")


@user_llm_config_bp.route("/create", methods=["POST"])
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
    config_repo = UserLLMConfigRepository(db_session)
    config_service = UserLLMConfigService(config_repo)

    # 创建配置
    config = config_service.create_config(data, user_id)

    return success_response(config, "创建用户LLM配置成功")


@user_llm_config_bp.route("/update", methods=["POST"])
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
    config_repo = UserLLMConfigRepository(db_session)
    config_service = UserLLMConfigService(config_repo)

    # 更新配置
    config = config_service.update_config(config_id, data, user_id)

    return success_response(config, "更新用户LLM配置成功")


@user_llm_config_bp.route("/delete", methods=["POST"])
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
    config_repo = UserLLMConfigRepository(db_session)
    config_service = UserLLMConfigService(config_repo)

    # 删除配置
    config_service.delete_config(config_id, user_id)

    return success_response(None, "删除用户LLM配置成功")


@user_llm_config_bp.route("/set_default", methods=["POST"])
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
    config_repo = UserLLMConfigRepository(db_session)
    config_service = UserLLMConfigService(config_repo)

    # 设置默认配置
    config = config_service.set_default_config(config_id, user_id)

    return success_response(config, "设置默认用户LLM配置成功")


@user_llm_config_bp.route("/auth_requirements", methods=["GET"])
@auth_required
def get_auth_requirements():
    """获取不同提供商的鉴权要求"""
    auth_requirements = {
        "OpenAI": {
            "auth_type": "api_key",
            "required_fields": ["api_key"],
            "optional_fields": ["api_base_url", "api_version"],
            "description": "OpenAI API仅需要API密钥",
        },
        "Claude": {
            "auth_type": "api_key",
            "required_fields": ["api_key"],
            "optional_fields": ["api_base_url"],
            "description": "Anthropic Claude API仅需要API密钥",
        },
        "Volcano": {
            "auth_type": "id_key_secret",
            "required_fields": ["app_id", "app_key", "app_secret"],
            "optional_fields": ["api_base_url", "region"],
            "description": "火山引擎需要应用ID、应用Key和应用密钥",
        },
        "Baidu": {
            "auth_type": "key_secret",
            "required_fields": ["app_key", "app_secret"],
            "optional_fields": ["api_base_url"],
            "description": "百度AI需要应用Key和应用密钥",
        },
        "Aliyun": {
            "auth_type": "key_secret",
            "required_fields": ["app_key", "app_secret"],
            "optional_fields": ["region", "api_version"],
            "description": "阿里云需要应用Key和应用密钥",
        },
        "Tencent": {
            "auth_type": "id_key_secret",
            "required_fields": ["app_id", "app_key", "app_secret"],
            "optional_fields": ["region"],
            "description": "腾讯云需要应用ID、应用Key和应用密钥",
        },
        "Gemini": {
            "auth_type": "api_key",
            "required_fields": ["api_key"],
            "optional_fields": ["api_base_url"],
            "description": "Google Gemini API仅需要API密钥",
        },
    }

    provider_type = request.args.get("provider_type")
    if provider_type:
        if provider_type in auth_requirements:
            return success_response(
                auth_requirements[provider_type], f"获取{provider_type}鉴权要求成功"
            )
        else:
            return success_response(None, "未找到指定提供商的鉴权要求")

    return success_response(auth_requirements, "获取所有提供商鉴权要求成功")
