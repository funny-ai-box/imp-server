# app/infrastructure/database/repositories/ai_provider_repository.py
from typing import List, Optional
from sqlalchemy.orm import Session
from app.infrastructure.database.models.llm_provider import AIProvider
from app.core.exceptions import NotFoundException
from app.core.status_codes import PROVIDER_NOT_FOUND


class AIProviderRepository:
    """AI提供商存储库"""
    
    def __init__(self, db_session: Session):
        """
        初始化存储库
        
        参数:
            db_session: 数据库会话
        """
        self.db = db_session
    
    def get_all_by_user(self, user_id: int) -> List[AIProvider]:
        """
        获取用户的所有AI提供商
        
        参数:
            user_id: 用户ID
            
        返回:
            提供商列表
        """
        return self.db.query(AIProvider).filter(AIProvider.user_id == user_id).all()
    
    def get_by_id(self, provider_id: int, user_id: int) -> AIProvider:
        """
        根据ID获取指定用户的AI提供商
        
        参数:
            provider_id: 提供商ID
            user_id: 用户ID
            
        返回:
            提供商实例
            
        异常:
            NotFoundException: 提供商不存在
        """
        provider = self.db.query(AIProvider).filter(
            AIProvider.id == provider_id,
            AIProvider.user_id == user_id
        ).first()
        
        if not provider:
            raise NotFoundException(f"未找到ID为{provider_id}的AI提供商", PROVIDER_NOT_FOUND)
        
        return provider
    
    def create(self, provider_data: dict) -> AIProvider:
        """
        创建新的AI提供商
        
        参数:
            provider_data: 提供商数据
            
        返回:
            新创建的提供商实例
        """
        provider = AIProvider(**provider_data)
        self.db.add(provider)
        self.db.commit()
        self.db.refresh(provider)
        return provider
    
    def update(self, provider_id: int, user_id: int, provider_data: dict) -> AIProvider:
        """
        更新AI提供商
        
        参数:
            provider_id: 提供商ID
            user_id: 用户ID
            provider_data: 要更新的数据
            
        返回:
            更新后的提供商实例
            
        异常:
            NotFoundException: 提供商不存在
        """
        provider = self.get_by_id(provider_id, user_id)
        
        for key, value in provider_data.items():
            if hasattr(provider, key):
                setattr(provider, key, value)
        
        self.db.commit()
        self.db.refresh(provider)
        return provider
    
    def delete(self, provider_id: int, user_id: int) -> bool:
        """
        删除AI提供商
        
        参数:
            provider_id: 提供商ID
            user_id: 用户ID
            
        返回:
            操作是否成功
            
        异常:
            NotFoundException: 提供商不存在
        """
        provider = self.get_by_id(provider_id, user_id)
        self.db.delete(provider)
        self.db.commit()
        return True

