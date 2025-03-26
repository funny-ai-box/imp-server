"""LLM 相关服务"""
from typing import List, Dict, Any, Optional, Tuple
from app.infrastructure.database.repositories.llm_repository import LLMProviderRepository, LLMModelRepository

from app.infrastructure.database.repositories.user_repository import UserRepository
from app.core.exceptions import ValidationException, ConflictException, NotFoundException
from app.core.status_codes import PROVIDER_VALIDATION_ERROR, PROVIDER_ALREADY_EXISTS, MODEL_VALIDATION_ERROR


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