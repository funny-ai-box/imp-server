"""AI提供商工厂模块，负责创建和管理AI提供商实例"""
import logging
from typing import Dict, Any, Optional

from app.infrastructure.llm_providers.base import LLMProviderInterface
from app.infrastructure.llm_providers.openai_provider import OpenLLMProvider
from app.infrastructure.llm_providers.anthropic_provider import AnthropicProvider
from app.core.exceptions import APIException
from app.core.status_codes import EXTERNAL_API_ERROR

logger = logging.getLogger(__name__)

class LLMProviderFactory:
    """AI提供商工厂类，负责创建和管理AI提供商实例"""
    
    # 支持的提供商映射
    PROVIDERS = {
        "openai": OpenLLMProvider,
        "anthropic": AnthropicProvider,
    }
    
    @classmethod
    def create_provider(cls, provider_name: str, api_key: str, **config) -> LLMProviderInterface:
        """创建AI提供商实例
        
        Args:
            provider_name: 提供商名称，如"openai"、"anthropic"
            api_key: API密钥
            **config: 其他配置参数
            
        Returns:
            初始化好的AI提供商实例
            
        Raises:
            APIException: 如果提供商不支持或初始化失败
        """
        provider_name = provider_name.lower()
        
        if provider_name not in cls.PROVIDERS:
            logger.error(f"Unsupported AI provider: {provider_name}")
            raise APIException(
                f"不支持的AI提供商: {provider_name}，支持的提供商: {', '.join(cls.PROVIDERS.keys())}", 
                EXTERNAL_API_ERROR
            )
        
        try:
            # 创建提供商实例
            provider = cls.PROVIDERS[provider_name]()
            
            # 初始化提供商
            provider.initialize(api_key, **config)
            
            logger.info(f"Successfully created and initialized {provider_name} provider")
            return provider
        except Exception as e:
            logger.error(f"Failed to create {provider_name} provider: {str(e)}")
            if isinstance(e, APIException):
                raise
            raise APIException(f"创建AI提供商失败: {str(e)}", EXTERNAL_API_ERROR)
    
    @classmethod
    def get_available_providers(cls) -> Dict[str, Dict[str, Any]]:
        """获取所有可用的AI提供商信息
        
        Returns:
            提供商信息字典，键为提供商名称，值为提供商描述
        """
        return {
            "openai": {
                "name": "OpenAI",
                "description": "OpenAI API服务，提供GPT系列模型和嵌入模型",
                "features": ["text_generation", "chat_completion", "embeddings"],
                "default_models": {
                    "text": "gpt-4o",
                    "chat": "gpt-4o",
                    "embeddings": "text-embedding-3-large"
                }
            },
            "anthropic": {
                "name": "Anthropic",
                "description": "Anthropic API服务，提供Claude系列模型",
                "features": ["text_generation", "chat_completion"],
                "default_models": {
                    "text": "claude-3-opus-20240229",
                    "chat": "claude-3-opus-20240229"
                }
            }
        }