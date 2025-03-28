# app/infrastructure/database/repositories/user_app_repository.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.infrastructure.database.models.user_app import UserApp
from app.core.exceptions import NotFoundException
from app.core.status_codes import APPLICATION_NOT_FOUND


class UserAppRepository:
    """用户应用存储库"""

    def __init__(self, db_session: Session):
        """初始化存储库"""
        self.db = db_session

    def get_all_by_user(self, user_id: str) -> List[UserApp]:
        """获取用户的所有应用"""
        return self.db.query(UserApp).filter(UserApp.user_id == user_id).all()

    def get_by_id(self, id: str, user_id: str) -> UserApp:
        """根据ID获取用户应用"""
        app = (
            self.db.query(UserApp)
            .filter(UserApp.id == id, UserApp.user_id == user_id)
            .first()
        )

        if not app:
            raise NotFoundException(f"未找到ID为{id}的应用")

        return app
    
    def get_by_app_id(self, app_id: str, user_id: str) -> UserApp:
        """根据应用ID获取应用"""
        print("get_by_app_id")
        print(f"app_id: {app_id}, user_id: {user_id}")
        app= (
            self.db.query(UserApp)
            .filter(UserApp.app_id == app_id, UserApp.user_id == user_id)
            .first()
        )

        if not app:
            raise NotFoundException(f"未找到A1PP_ID为{app_id}的应用")

        return app

    def get_by_app_key(self, app_key: str) -> Optional[UserApp]:
        """根据应用密钥获取应用"""
        return self.db.query(UserApp).filter(UserApp.app_key == app_key).first()

    def get_all_by_type(self, user_id: str, app_type: str) -> List[UserApp]:
        """获取用户特定类型的所有应用"""
        return (
            self.db.query(UserApp)
            .filter(UserApp.user_id == user_id, UserApp.app_type == app_type)
            .all()
        )

    def get_default_by_type(self, user_id: str, app_type: str) -> Optional[UserApp]:
        """获取用户特定类型的默认应用"""
        return (
            self.db.query(UserApp)
            .filter(
                UserApp.user_id == user_id,
                UserApp.app_type == app_type,
                UserApp.is_default == True,
            )
            .first()
        )

    def create(self, app_data: dict) -> UserApp:
        """创建新应用"""
        app = UserApp(**app_data)
        self.db.add(app)
        self.db.commit()
        self.db.refresh(app)
        return app

    def update(self, app_id: str, user_id: str, app_data: dict) -> UserApp:
        """更新应用"""
        app = self.get_by_app_id(app_id, user_id)

        for key, value in app_data.items():
            if hasattr(app, key):
                setattr(app, key, value)

        self.db.commit()
        self.db.refresh(app)
        return app

    def delete(self, app_id: str, user_id: str) -> bool:
        """删除应用"""
        app = self.get_by_id(app_id, user_id)
        self.db.delete(app)
        self.db.commit()
        return True

    def set_as_default(self, app_id: str, user_id: str) -> UserApp:
        """设置应用为默认"""
        # 获取当前应用
        app = self.get_by_id(app_id, user_id)

        # 取消同类型应用的默认状态
        self.db.query(UserApp).filter(
            UserApp.user_id == user_id,
            UserApp.app_type == app.app_type,
            UserApp.id != app_id,
        ).update({"is_default": False})

        # 设置当前应用为默认
        app.is_default = True
        self.db.commit()
        self.db.refresh(app)

        return app
