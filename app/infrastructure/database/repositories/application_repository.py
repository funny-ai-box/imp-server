from typing import List, Optional
from sqlalchemy.orm import Session
from app.infrastructure.database.models.application import Application
from app.core.exceptions import NotFoundException
from app.core.status_codes import APPLICATION_NOT_FOUND


class ApplicationRepository:
    """应用存储库"""
    
    def __init__(self, db_session: Session):
        """
        初始化存储库
        
        参数:
            db_session: 数据库会话
        """
        self.db = db_session
    
    def get_all_by_user(self, user_id: str) -> List[Application]:
        """
        获取用户的所有应用
        
        参数:
            user_id: 用户ID
            
        返回:
            应用列表
        """
        return self.db.query(Application).filter(Application.user_id == user_id).all()
    
    def get_by_id(self, app_id: int, user_id: str) -> Application:
        """
        根据ID获取指定用户的应用
        
        参数:
            app_id: 应用ID
            user_id: 用户ID
            
        返回:
            应用实例
            
        异常:
            NotFoundException: 应用不存在
        """
        app = self.db.query(Application).filter(
            Application.id == app_id,
            Application.user_id == user_id
        ).first()
        
        if not app:
            raise NotFoundException(f"未找到ID为{app_id}的应用", APPLICATION_NOT_FOUND)
        
        return app
    
    def get_by_app_key(self, app_key: str) -> Optional[Application]:
        """
        根据应用密钥获取应用
        
        参数:
            app_key: 应用密钥
            
        返回:
            应用实例，如果不存在则返回None
        """
        return self.db.query(Application).filter(Application.app_key == app_key).first()
    
    def create(self, app_data: dict) -> Application:
        """
        创建新的应用
        
        参数:
            app_data: 应用数据
            
        返回:
            新创建的应用实例
        """
        app = Application(**app_data)
        self.db.add(app)
        self.db.commit()
        self.db.refresh(app)
        return app
    
    def update(self, app_id: int, user_id: str, app_data: dict) -> Application:
        """
        更新应用
        
        参数:
            app_id: 应用ID
            user_id: 用户ID
            app_data: 要更新的数据
            
        返回:
            更新后的应用实例
            
        异常:
            NotFoundException: 应用不存在
        """
        app = self.get_by_id(app_id, user_id)
        
        for key, value in app_data.items():
            if hasattr(app, key):
                setattr(app, key, value)
        
        self.db.commit()
        self.db.refresh(app)
        return app
    
    def delete(self, app_id: int, user_id: str) -> bool:
        """
        删除应用
        
        参数:
            app_id: 应用ID
            user_id: 用户ID
            
        返回:
            操作是否成功
            
        异常:
            NotFoundException: 应用不存在
        """
        app = self.get_by_id(app_id, user_id)
        self.db.delete(app)
        self.db.commit()
        return True