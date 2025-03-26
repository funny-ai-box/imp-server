"""LLM 相关服务"""
from typing import List, Dict, Any, Optional, Tuple
from app.infrastructure.database.repositories.llm_repository import  LLMProviderRepository,LLMModelRepository

from app.infrastructure.database.repositories.user_repository import UserRepository
from app.core.exceptions import ValidationException, ConflictException
from app.core.status_codes import PROVIDER_VALIDATION_ERROR, PROVIDER_ALREADY_EXISTS, MODEL_VALIDATION_ERROR

class LLMProviderService:
    """AI提供商服务"""
    
    def __init__(self, provider_repository: LLMProviderRepository):
        """
        初始化服务
        
        参数:
            provider_repository: AI提供商存储库
            user_repository: 用户存储库
        """
        self.provider_repo = provider_repository
  
    
    def get_all_providers(self) -> List[Dict[str, Any]]:
        """
        获取用户的所有AI提供商
        
        参数:
            user_id: 用户ID
            
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
    
    def create_provider(self, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建新的AI提供商
        
        参数:
            provider_data: 提供商数据
            user_id: 用户ID
            
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
            user_id: 用户ID
            
        返回:
            更新后的提供商信息
        """
        # 验证数据
        if provider_data:
            self._validate_provider_data(provider_data, is_update=True)

        
        # 更新提供商
        provider = self.provider_repo.update(provider_id,  provider_data)
        return self._format_provider(provider)
    
    def delete_provider(self, provider_id: int) -> bool:
        """
        删除AI提供商
        
        参数:
            provider_id: 提供商ID
            user_id: 用户ID
            
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
            required_fields = ["name", "provider_type", "api_key"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                raise ValidationException(
                    f"缺少必填字段: {', '.join(missing_fields)}", 
                    PROVIDER_VALIDATION_ERROR
                )
        
        # 提供商类型验证
        if "provider_type" in data:
            valid_types = ["OpenAI", "Claude", "Volcano"]
            if data["provider_type"] not in valid_types:
                raise ValidationException(
                    f"无效的提供商类型: {data['provider_type']}，有效类型: {', '.join(valid_types)}", 
                    PROVIDER_VALIDATION_ERROR
                )
            
            # 基于提供商类型验证必要的字段
            if data["provider_type"] == "OpenAI" and "api_key" in data:
                if not data["api_key"]:
                    raise ValidationException("OpenAI平台需要提供有效的API密钥", PROVIDER_VALIDATION_ERROR)
            
            elif data["provider_type"] == "Claude" and "api_key" in data:
                if not data["api_key"]:
                    raise ValidationException("Claude平台需要提供有效的API密钥", PROVIDER_VALIDATION_ERROR)
            
            elif data["provider_type"] == "Volcano" and "api_key" in data:
                # 火山引擎可能需要更多配置
                if not data["api_key"]:
                    raise ValidationException("火山引擎平台需要提供有效的API密钥", PROVIDER_VALIDATION_ERROR)
    
    def _format_provider(self, provider) -> Dict[str, Any]:
        """
        格式化提供商数据
        
        参数:
            provider: 提供商实例
            
        返回:
            格式化后的提供商数据
        """

        return {
            "id": provider.id,
            "name": provider.name,
            "provider_type": provider.provider_type,
            "api_key": "***" + provider.api_key[-4:] if provider.api_key else None,  # 隐藏API密钥
            "api_base_url": provider.api_base_url,
            "api_version": provider.api_version,
            "is_active": provider.is_active,
            "created_at": provider.created_at.isoformat() if provider.created_at else None,
            "updated_at": provider.updated_at.isoformat() if provider.updated_at else None,

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
    
    def get_all_models(self, provider_id: int) -> List[Dict[str, Any]]:
        """获取提供商的所有模型"""
        # 验证提供商存在
        self.provider_repo.get_by_id(provider_id)
        
        models = self.model_repo.get_all_by_provider(provider_id)
        return [self._format_model(model) for model in models]
    
    def get_model(self, model_id: int, provider_id: int) -> Dict[str, Any]:
        """获取特定的AI模型"""
        # 验证提供商存在
        self.provider_repo.get_by_id(provider_id)
        
        model = self.model_repo.get_by_id(model_id, provider_id)
        return self._format_model(model)
    
    def create_model(self, model_data: Dict[str, Any], provider_id: int, user_id: str) -> Dict[str, Any]:
        """
        创建新的AI模型
        
        参数:
            model_data: 模型数据
            provider_id: 提供商ID
            user_id: 用户ID
            
        返回:
            创建的模型信息
            
        异常:
            ValidationException: 验证失败
            NotFoundException: 提供商不存在
        """
        # 验证提供商存在且属于该用户
        self.provider_repo.get_by_id(provider_id, user_id)
        
        # 验证数据
        self._validate_model_data(model_data)
        
        # 设置提供商ID
        model_data["provider_id"] = provider_id
        
        # 创建模型
        model = self.model_repo.create(model_data)
        return self._format_model(model)
    
    def update_model(self, model_id: int, model_data: Dict[str, Any], provider_id: int, user_id: str) -> Dict[str, Any]:
        """
        更新AI模型
        
        参数:
            model_id: 模型ID
            model_data: 要更新的数据
            provider_id: 提供商ID
            user_id: 用户ID
            
        返回:
            更新后的模型信息
            
        异常:
            ValidationException: 验证失败
            NotFoundException: 提供商或模型不存在
        """
        # 验证提供商存在且属于该用户
        self.provider_repo.get_by_id(provider_id, user_id)
        
        # 验证数据
        if model_data:
            self._validate_model_data(model_data, is_update=True)
        
        # 禁止更新提供商ID
        if "provider_id" in model_data:
            del model_data["provider_id"]
        
        # 更新模型
        model = self.model_repo.update(model_id, provider_id, model_data)
        return self._format_model(model)
    
    def delete_model(self, model_id: int, provider_id: int, user_id: str) -> bool:
        """
        删除AI模型
        
        参数:
            model_id: 模型ID
            provider_id: 提供商ID
            user_id: 用户ID
            
        返回:
            操作是否成功
            
        异常:
            NotFoundException: 提供商或模型不存在
        """
        # 验证提供商存在且属于该用户
        self.provider_repo.get_by_id(provider_id, user_id)
        
        return self.model_repo.delete(model_id, provider_id)
    
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
            required_fields = ["name", "model_id"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                raise ValidationException(
                    f"缺少必填字段: {', '.join(missing_fields)}", 
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
            "description": model.description,
            "capabilities": model.capabilities,
            "context_window": model.context_window,
            "max_tokens": model.max_tokens,
            "token_price_input": model.token_price_input,
            "token_price_output": model.token_price_output,
            "is_available": model.is_available,
            "provider_id": model.provider_id,
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None
        }
    