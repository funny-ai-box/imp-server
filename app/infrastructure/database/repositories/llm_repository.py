"""LLM模型存储库"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import func, desc, and_, or_
from sqlalchemy.orm import Session
from app.infrastructure.database.models.llm import  LLMModel, LLMProvider
from app.core.exceptions import NotFoundException
from app.core.status_codes import MODEL_NOT_FOUND


class LLMModelRepository:
    """AI模型存储库"""
    
    def __init__(self, db_session: Session):
        """
        初始化存储库
        
        参数:
            db_session: 数据库会话
        """
        self.db = db_session
    
    def get_all_by_provider(self, provider_id: int) -> List[LLMModel]:
        """
        获取提供商的所有模型
        
        参数:
            provider_id: 提供商ID
            
        返回:
            模型列表
        """
        return self.db.query(LLMModel).filter(LLMModel.provider_id == provider_id).all()
    
    def get_by_id(self, model_id: int, provider_id: int) -> LLMModel:
        """
        根据ID获取特定提供商的模型
        
        参数:
            model_id: 模型ID
            provider_id: 提供商ID
            
        返回:
            模型实例
            
        异常:
            NotFoundException: 模型不存在
        """
        model = self.db.query(LLMModel).filter(
            LLMModel.id == model_id,
            LLMModel.provider_id == provider_id
        ).first()
        
        if not model:
            raise NotFoundException(f"未找到ID为{model_id}的AI模型", MODEL_NOT_FOUND)
        
        return model

    
class LLMProviderRepository:
    """AI提供商存储库"""
    
    def __init__(self, db_session: Session):
        """
        初始化存储库
        
        参数:
            db_session: 数据库会话
        """
        self.db = db_session
    
    def get_all_providers(self) -> List[LLMProvider]:
        """
        获取用户的所有AI提供商

            
        返回:
            提供商列表
        """
        return self.db.query(LLMProvider).all()
    
    def get_by_id(self, provider_id: int) -> LLMProvider:
        """
        根据ID获取指定用户的AI提供商
        
        参数:
            provider_id: 提供商ID
  
            
        返回:
            提供商实例
            
        异常:
            NotFoundException: 提供商不存在
        """
        provider = self.db.query(LLMProvider).filter(
            LLMProvider.id == provider_id,
  
        ).first()
        
        if not provider:
            raise NotFoundException(f"未找到ID为{provider_id}的AI提供商")
        
        return provider
    
