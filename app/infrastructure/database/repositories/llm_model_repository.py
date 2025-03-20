# app/infrastructure/database/repositories/ai_model_repository.py
from typing import List, Optional
from sqlalchemy.orm import Session
from app.infrastructure.database.models.llm_model import AIModel
from app.core.exceptions import NotFoundException
from app.core.status_codes import MODEL_NOT_FOUND


class AIModelRepository:
    """AI模型存储库"""
    
    def __init__(self, db_session: Session):
        """
        初始化存储库
        
        参数:
            db_session: 数据库会话
        """
        self.db = db_session
    
    def get_all_by_provider(self, provider_id: int) -> List[AIModel]:
        """
        获取提供商的所有模型
        
        参数:
            provider_id: 提供商ID
            
        返回:
            模型列表
        """
        return self.db.query(AIModel).filter(AIModel.provider_id == provider_id).all()
    
    def get_by_id(self, model_id: int, provider_id: int) -> AIModel:
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
        model = self.db.query(AIModel).filter(
            AIModel.id == model_id,
            AIModel.provider_id == provider_id
        ).first()
        
        if not model:
            raise NotFoundException(f"未找到ID为{model_id}的AI模型", MODEL_NOT_FOUND)
        
        return model
    
    def create(self, model_data: dict) -> AIModel:
        """
        创建新的AI模型
        
        参数:
            model_data: 模型数据
            
        返回:
            新创建的模型实例
        """
        model = AIModel(**model_data)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model
    
    def update(self, model_id: int, provider_id: int, model_data: dict) -> AIModel:
        """
        更新AI模型
        
        参数:
            model_id: 模型ID
            provider_id: 提供商ID
            model_data: 要更新的数据
            
        返回:
            更新后的模型实例
            
        异常:
            NotFoundException: 模型不存在
        """
        model = self.get_by_id(model_id, provider_id)
        
        for key, value in model_data.items():
            if hasattr(model, key):
                setattr(model, key, value)
        
        self.db.commit()
        self.db.refresh(model)
        return model
    
    def delete(self, model_id: int, provider_id: int) -> bool:
        """
        删除AI模型
        
        参数:
            model_id: 模型ID
            provider_id: 提供商ID
            
        返回:
            操作是否成功
            
        异常:
            NotFoundException: 模型不存在
        """
        model = self.get_by_id(model_id, provider_id)
        self.db.delete(model)
        self.db.commit()
        return True