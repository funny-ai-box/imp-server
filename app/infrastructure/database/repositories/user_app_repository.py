# app/infrastructure/database/repositories/user_app_repository.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.infrastructure.database.models.user_app import UserApp
from app.core.exceptions import NotFoundException
from app.core.status_codes import APPLICATION_NOT_FOUND

class UserAppRepository:
    """用户应用存储库"""
    
    def __init__(self, db_session: Session):
        """初始化存储库"""
        self.db = db_session
    
    def get_all_by_user(self, user_id: int) -> List[UserApp]:
        """获取用户的所有应用"""
        return self.db.query(UserApp).filter(UserApp.user_id == user_id).all()
    
    def get_by_id(self, app_id: int, user_id: int) -> UserApp:
        """根据ID获取用户应用"""
        app = self.db.query(UserApp).filter(
            UserApp.id == app_id,
            UserApp.user_id == user_id
        ).first()
        
        if not app:
            raise NotFoundException(f"未找到ID为{app_id}的应用", APPLICATION_NOT_FOUND)
        
        return app
    
    def get_by_app_key(self, app_key: str) -> Optional[UserApp]:
        """根据应用密钥获取应用"""
        return self.db.query(UserApp).filter(UserApp.app_key == app_key).first()
    
    def get_all_by_type(self, user_id: int, app_type: str) -> List[UserApp]:
        """获取用户特定类型的所有应用"""
        return self.db.query(UserApp).filter(
            UserApp.user_id == user_id,
            UserApp.app_type == app_type
        ).all()
    
    def create(self, app_data: dict) -> UserApp:
        """创建新应用"""
        app = UserApp(**app_data)
        self.db.add(app)
        self.db.commit()
        self.db.refresh(app)
        return app
    
    def update(self, app_id: int, user_id: int, app_data: dict) -> UserApp:
        """更新应用"""
        app = self.get_by_id(app_id, user_id)
        
        for key, value in app_data.items():
            if hasattr(app, key):
                setattr(app, key, value)
        
        self.db.commit()
        self.db.refresh(app)
        return app
    
    def delete(self, app_id: int, user_id: int) -> bool:
        """删除应用"""
        app = self.get_by_id(app_id, user_id)
        self.db.delete(app)
        self.db.commit()
        return True