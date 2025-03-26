"""LLM 相关服务"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from app.infrastructure.database.repositories.llm_repository import LLMProviderConfigRepository, LLMProviderRepository, LLMModelRepository

from app.infrastructure.database.repositories.user_repository import UserRepository
from app.core.exceptions import ValidationException, ConflictException, NotFoundException
from app.core.status_codes import PROVIDER_VALIDATION_ERROR, PROVIDER_ALREADY_EXISTS, MODEL_VALIDATION_ERROR

logger = logging.getLogger(__name__)
class LLMProviderService:
    """AI提供商服务"""
    
    def __init__(self, provider_repository: LLMProviderRepository):
        """
        初始化服务
        
        参数:
            provider_repository: AI提供商存储库
        """
        self.provider_repo = provider_repository
  
    
    def get_all_providers(self) -> List[Dict[str, Any]]:
        """
        获取所有AI提供商
            
        返回:
            提供商列表
        """
        providers = self.provider_repo.get_all_providers()
        return [self._format_provider(provider) for provider in providers]
    
    def get_provider(self, provider_id: int) -> Dict[str, Any]:
        """
        获取特定的AI提供商
        
        参数:
            provider_id: 提供商ID
            
        返回:
            提供商信息
        """
        provider = self.provider_repo.get_by_id(provider_id)
        return self._format_provider(provider)
    
    def get_provider_by_type(self, provider_type: str) -> Dict[str, Any]:
        """
        根据类型获取AI提供商
        
        参数:
            provider_type: 提供商类型
            
        返回:
            提供商信息
        """
        provider = self.provider_repo.get_by_type(provider_type)
        return self._format_provider(provider)
    
    def get_auth_requirements(self, provider_type: Optional[str] = None) -> Dict[str, Any]:
        """
        获取提供商的鉴权需求
        
        参数:
            provider_type: 提供商类型，如果为None则返回所有提供商的鉴权需求
            
        返回:
            鉴权需求信息
        """
        if provider_type:
            provider = self.provider_repo.get_by_type(provider_type)
            if not provider:
                return None
            return {
                provider.provider_type: {
                    "auth_type": provider.auth_type,
                    "required_fields": provider.required_fields,
                    "optional_fields": provider.optional_fields,
                    "description": provider.auth_description
                }
            }
        else:
            providers = self.provider_repo.get_all_providers()
            auth_requirements = {}
            for provider in providers:
                auth_requirements[provider.provider_type] = {
                    "auth_type": provider.auth_type,
                    "required_fields": provider.required_fields,
                    "optional_fields": provider.optional_fields,
                    "description": provider.auth_description
                }
            return auth_requirements
    
    def create_provider(self, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建新的AI提供商
        
        参数:
            provider_data: 提供商数据
            
        返回:
            创建的提供商信息
            
        异常:
            ValidationException: 验证失败
            ConflictException: 提供商已存在
        """
        # 验证数据
        self._validate_provider_data(provider_data)
        
        # 创建提供商
        try:
            provider = self.provider_repo.create(provider_data)
            return self._format_provider(provider)
        except Exception as e:
            raise ConflictException(
                f"创建AI提供商失败: {str(e)}", 
                PROVIDER_ALREADY_EXISTS
            )
    
    def update_provider(self, provider_id: int, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新AI提供商
        
        参数:
            provider_id: 提供商ID
            provider_data: 要更新的数据
            
        返回:
            更新后的提供商信息
        """
        # 验证数据
        if provider_data:
            self._validate_provider_data(provider_data, is_update=True)
        
        # 更新提供商
        provider = self.provider_repo.update(provider_id, provider_data)
        return self._format_provider(provider)
    
    def delete_provider(self, provider_id: int) -> bool:
        """
        删除AI提供商
        
        参数:
            provider_id: 提供商ID
            
        返回:
            操作是否成功
        """
        return self.provider_repo.delete(provider_id)
    
    def _validate_provider_data(self, data: Dict[str, Any], is_update: bool = False) -> None:
        """
        验证提供商数据
        
        参数:
            data: 要验证的数据
            is_update: 是否为更新操作
            
        异常:
            ValidationException: 验证失败
        """
        if not is_update:
            # 必填字段验证
            required_fields = ["name", "provider_type", "auth_type", "required_fields"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                raise ValidationException(
                    f"缺少必填字段: {', '.join(missing_fields)}", 
                    PROVIDER_VALIDATION_ERROR
                )
        
        # 提供商类型验证
        if "provider_type" in data:
            valid_types = ["OpenAI", "Claude", "Volcano", "Baidu", "Aliyun", "Tencent", "Gemini"]
            if data["provider_type"] not in valid_types:
                raise ValidationException(
                    f"无效的提供商类型: {data['provider_type']}，有效类型: {', '.join(valid_types)}", 
                    PROVIDER_VALIDATION_ERROR
                )
            
        # 鉴权类型验证
        if "auth_type" in data:
            valid_auth_types = ["api_key", "key_secret", "id_key_secret"]
            if data["auth_type"] not in valid_auth_types:
                raise ValidationException(
                    f"无效的鉴权类型: {data['auth_type']}，有效类型: {', '.join(valid_auth_types)}", 
                    PROVIDER_VALIDATION_ERROR
                )
            
        # 必填字段和可选字段验证
        if "required_fields" in data and not isinstance(data["required_fields"], list):
            raise ValidationException(
                "required_fields必须是一个列表", 
                PROVIDER_VALIDATION_ERROR
            )
            
        if "optional_fields" in data and not isinstance(data["optional_fields"], list):
            raise ValidationException(
                "optional_fields必须是一个列表", 
                PROVIDER_VALIDATION_ERROR
            )
    
    def _format_provider(self, provider) -> Dict[str, Any]:
        """
        格式化提供商数据
        
        参数:
            provider: 提供商实例
            
        返回:
            格式化后的提供商数据
        """
        # 适应新的数据模型结构
        return {
            "id": provider.id,
            "name": provider.name,
            "provider_type": provider.provider_type,
            "description": provider.description,
            "auth_type": provider.auth_type,
            "required_fields": provider.required_fields,
            "optional_fields": provider.optional_fields,
            "auth_description": provider.auth_description,
            "is_active": provider.is_active,
            "created_at": provider.created_at.isoformat() if provider.created_at else None,
            "updated_at": provider.updated_at.isoformat() if provider.updated_at else None
        }


class LLMModelService:
    """AI模型服务"""
    
    def __init__(self, model_repository: LLMModelRepository, provider_repository: LLMProviderRepository):
        """
        初始化服务
        
        参数:
            model_repository: AI模型存储库
            provider_repository: AI提供商存储库
        """
        self.model_repo = model_repository
        self.provider_repo = provider_repository
    
    def get_all_models(self, provider_id: Optional[int] = None, model_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取模型列表
        
        参数:
            provider_id: 提供商ID，如果指定则只返回该提供商的模型
            model_type: 模型类型，如果指定则只返回该类型的模型
            
        返回:
            模型列表
        """
        if provider_id:
            # 验证提供商存在
            self.provider_repo.get_by_id(provider_id)
            models = self.model_repo.get_all_by_provider(provider_id)
        elif model_type:
            models = self.model_repo.get_all_by_type(model_type)
        else:
            models = self.model_repo.get_all_models()
            
        return [self._format_model(model) for model in models]
    
    def get_model(self, model_id: int) -> Dict[str, Any]:
        """
        获取特定的AI模型
        
        参数:
            model_id: 模型ID
            
        返回:
            模型信息
        """
        model = self.model_repo.get_by_id(model_id)
        return self._format_model(model)
    
    def get_model_by_model_id(self, model_id_str: str) -> Dict[str, Any]:
        """
        根据模型标识符获取模型
        
        参数:
            model_id_str: 模型标识符，如gpt-4-turbo
            
        返回:
            模型信息
        """
        model = self.model_repo.get_by_model_id(model_id_str)
        return self._format_model(model)
    
    def create_model(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建新的AI模型
        
        参数:
            model_data: 模型数据
            
        返回:
            创建的模型信息
            
        异常:
            ValidationException: 验证失败
            NotFoundException: 提供商不存在
        """
        # 验证数据
        self._validate_model_data(model_data)
        
        # 验证提供商存在
        if "provider_id" in model_data:
            provider_id = model_data["provider_id"]
            provider = self.provider_repo.get_by_id(provider_id)
            if not provider:
                raise NotFoundException(f"提供商(ID:{provider_id})不存在")
        
        # 创建模型
        model = self.model_repo.create(model_data)
        return self._format_model(model)
    
    def update_model(self, model_id: int, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新AI模型
        
        参数:
            model_id: 模型ID
            model_data: 要更新的数据
            
        返回:
            更新后的模型信息
        """
        # 验证数据
        if model_data:
            self._validate_model_data(model_data, is_update=True)
        
        # 更新模型
        model = self.model_repo.update(model_id, model_data)
        return self._format_model(model)
    
    def delete_model(self, model_id: int) -> bool:
        """
        删除AI模型
        
        参数:
            model_id: 模型ID
            
        返回:
            操作是否成功
        """
        return self.model_repo.delete(model_id)
    
    def _validate_model_data(self, data: Dict[str, Any], is_update: bool = False) -> None:
        """
        验证模型数据
        
        参数:
            data: 要验证的数据
            is_update: 是否为更新操作
            
        异常:
            ValidationException: 验证失败
        """
        if not is_update:
            # 必填字段验证
            required_fields = ["name", "model_id", "model_type", "provider_id"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                raise ValidationException(
                    f"缺少必填字段: {', '.join(missing_fields)}", 
                    MODEL_VALIDATION_ERROR
                )
                
        # 验证模型类型
        if "model_type" in data:
            valid_types = [
                "chat", "completion", "embedding", "multimodal", 
                "code", "vision", "fine_tuned", "instruction_tuned", 
                "rag", "reasoning"
            ]
            if data["model_type"] not in valid_types:
                raise ValidationException(
                    f"无效的模型类型: {data['model_type']}，有效类型: {', '.join(valid_types)}", 
                    MODEL_VALIDATION_ERROR
                )
    
    def _format_model(self, model) -> Dict[str, Any]:
        """
        格式化模型数据
        
        参数:
            model: 模型实例
            
        返回:
            格式化后的模型数据
        """
        return {
            "id": model.id,
            "name": model.name,
            "model_id": model.model_id,
            "model_type": model.model_type,
            "description": model.description,
            "capabilities": model.capabilities,
            "context_window": model.context_window,
            "max_tokens": model.max_tokens,
            "token_price_input": model.token_price_input,
            "token_price_output": model.token_price_output,
            "supported_features": model.supported_features,
            "language_support": model.language_support,
            "training_data_cutoff": model.training_data_cutoff.isoformat() if model.training_data_cutoff else None,
            "version": model.version,
            "is_available": model.is_available,
            "provider_id": model.provider_id,
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None
        }
    
class LLMProviderConfigService:
    """用户LLM配置服务"""

    def __init__(self, config_repository: LLMProviderConfigRepository):
        """初始化服务"""
        self.config_repo = config_repository

    def get_all_configs(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户所有LLM配置"""
        configs = self.config_repo.get_all_by_user(user_id)
        return [self._format_config(config) for config in configs]

    def get_config(self, config_id: int, user_id: str) -> Dict[str, Any]:
        """获取特定LLM配置"""
        config = self.config_repo.get_by_id(config_id, user_id)
        return self._format_config(config)

    def get_default_config(
        self, user_id: str, provider_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """获取默认LLM配置"""
        config = self.config_repo.get_default(user_id, provider_type)
        if not config:
            return None
        return self._format_config(config)

    def create_config(
        self, config_data: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """创建新的LLM配置"""
        # 验证数据
        self._validate_config_data(config_data)

        # 设置用户ID
        config_data["user_id"] = user_id
        
        # 如果设置为默认配置或该类型没有其他配置，则设为默认
        is_default = config_data.get("is_default", False)
        if "provider_type" in config_data:
            # 检查是否已有同类型的配置
            existing_default = self.config_repo.get_default(user_id, config_data["provider_type"])
            if not existing_default or is_default:
                config_data["is_default"] = True
                
                # 如果要设为默认，先取消其他同类型配置的默认状态
                if is_default and existing_default:
                    try:
                        self.config_repo.update(existing_default.id, user_id, {"is_default": False})
                    except Exception as e:
                        logger.error(f"Failed to reset default status: {str(e)}")

        # 创建配置
        config = self.config_repo.create(config_data)
        return self._format_config(config)

    def update_config(
        self, config_id: int, config_data: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """更新LLM配置"""
        # 获取当前配置
        current_config = self.config_repo.get_by_id(config_id, user_id)
        
        # 验证数据
        if config_data:
            self._validate_config_data(config_data, is_update=True)

        # 如果要设置为默认且当前未设为默认
        if config_data.get("is_default", False) and not current_config.is_default:
            # 取消其他同类型配置的默认状态
            provider_type = config_data.get("provider_type", current_config.provider_type)
            try:
                existing_configs = self.config_repo.get_all_by_user(user_id)
                for config in existing_configs:
                    if (config.id != config_id and 
                        config.provider_type == provider_type and 
                        config.is_default):
                        self.config_repo.update(config.id, user_id, {"is_default": False})
            except Exception as e:
                logger.error(f"Failed to reset default status: {str(e)}")

        # 更新配置
        config = self.config_repo.update(config_id, user_id, config_data)
        return self._format_config(config)

    def delete_config(self, config_id: int, user_id: str) -> bool:
        """删除LLM配置"""
        # 获取当前配置
        config = self.config_repo.get_by_id(config_id, user_id)
        
        # 检查是否为默认配置
        if config.is_default:
            # 尝试将同类型的另一个配置设为默认
            try:
                other_configs = self.config_repo.get_all_by_user(user_id)
                alternatives = [c for c in other_configs 
                               if c.id != config_id and c.provider_type == config.provider_type]
                
                if alternatives:
                    # 选择第一个替代配置设为默认
                    self.config_repo.update(alternatives[0].id, user_id, {"is_default": True})
            except Exception as e:
                logger.error(f"Failed to set alternative default config: {str(e)}")
        
        return self.config_repo.delete(config_id, user_id)

    def set_default_config(self, config_id: int, user_id: str) -> Dict[str, Any]:
        """设置默认LLM配置"""
        # 获取当前配置
        config = self.config_repo.get_by_id(config_id, user_id)
        
        try:
            # 取消同类型其他配置的默认状态
            other_configs = self.config_repo.get_all_by_user(user_id)
            for other_config in other_configs:
                if (other_config.id != config_id and 
                    other_config.provider_type == config.provider_type and 
                    other_config.is_default):
                    self.config_repo.update(other_config.id, user_id, {"is_default": False})
            
            # 设置当前配置为默认
            config = self.config_repo.set_as_default(config_id, user_id)
            return self._format_config(config)
        except Exception as e:
            logger.error(f"Failed to set default config: {str(e)}")
            raise

    def _format_config(self, config) -> Dict[str, Any]:
        """格式化配置数据，保护敏感信息"""
        # 安全屏蔽敏感信息
        def mask_sensitive(value: Optional[str]) -> Optional[str]:
            if not value or len(value) < 8:
                return None
            return f"***{value[-4:]}"
        
        result = {
            "id": config.id,
            "name": config.name,
            "provider_type": config.provider_type,
            "api_key": mask_sensitive(config.api_key),
            "api_secret": mask_sensitive(config.api_secret),
            "app_id": config.app_id,
            "app_key": mask_sensitive(config.app_key),
            "app_secret": mask_sensitive(config.app_secret),
            "api_base_url": config.api_base_url,
            "api_version": config.api_version,
            "region": config.region,
            "is_default": config.is_default,
            "is_active": config.is_active,
            "request_timeout": config.request_timeout,
            "max_retries": config.max_retries,
            "remark": config.remark,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None,
        }

        # 对不同提供商返回不同的鉴权信息
        if config.provider_type in ["OpenAI", "Claude", "Gemini"]:
            # OpenAI和Claude使用api_key
            result["auth_type"] = "api_key"
        elif config.provider_type in ["Baidu", "Aliyun"]:
            # 百度和阿里云使用app_key和app_secret
            result["auth_type"] = "key_secret"
        elif config.provider_type in ["Volcano", "Tencent"]:
            # 火山引擎和腾讯云使用app_id、app_key和app_secret
            result["auth_type"] = "id_key_secret"

        return result

    def _validate_config_data(
        self, data: Dict[str, Any], is_update: bool = False
    ) -> None:
        """验证配置数据"""
        if not is_update:
            # 必填字段验证
            required_fields = ["name", "provider_type"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                raise ValidationException(
                    f"缺少必填字段: {', '.join(missing_fields)}"
                )

        # 提供商类型验证
        if "provider_type" in data:
            valid_types = [
                "OpenAI",
                "Claude",
                "Volcano",
                "Gemini",
                "Baidu",
                "Aliyun",
                "Tencent",
            ]
            if data["provider_type"] not in valid_types:
                raise ValidationException(
                    f"无效的提供商类型: {data['provider_type']}，有效类型: {', '.join(valid_types)}",
                
                )

            # 根据提供商类型验证必要的鉴权字段
            provider_type = data["provider_type"]
            if not is_update and provider_type in ["OpenAI", "Claude", "Gemini"]:
                if "api_key" not in data or not data["api_key"]:
                    raise ValidationException(
                        f"{provider_type}配置必须提供api_key"
                    )
            elif not is_update and provider_type in ["Baidu", "Aliyun"]:
                if "app_key" not in data or not data["app_key"] or "app_secret" not in data or not data["app_secret"]:
                    raise ValidationException(
                        f"{provider_type}配置必须提供app_key和app_secret"
                    )
            elif not is_update and provider_type in ["Volcano", "Tencent"]:
                if ("app_id" not in data or not data["app_id"] or
                    "app_key" not in data or not data["app_key"] or
                    "app_secret" not in data or not data["app_secret"]):
                    raise ValidationException(
                        f"{provider_type}配置必须提供app_id、app_key和app_secret"
                    )

        # 超时时间验证
        if "request_timeout" in data:
            timeout = data["request_timeout"]
            if not isinstance(timeout, int) or timeout < 1 or timeout > 300:
                raise ValidationException(
                    "请求超时时间必须在1-300秒之间"
                )

        # 重试次数验证
        if "max_retries" in data:
            retries = data["max_retries"]
            if not isinstance(retries, int) or retries < 0 or retries > 10:
                raise ValidationException("最大重试次数必须在0-10之间")