# app/infrastructure/database/repositories/app_template_repository.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.infrastructure.database.models.app_template import AppTemplate
from app.core.exceptions import NotFoundException
from app.core.status_codes import APPLICATION_NOT_FOUND


class AppTemplateRepository:
    """应用模板存储库"""

    def __init__(self, db_session: Session):
        """初始化存储库"""
        self.db = db_session

    def get_all_active(self) -> List[AppTemplate]:
        """获取所有活跃的应用模板"""
        return self.db.query(AppTemplate).filter(AppTemplate.is_active == True).all()

    def get_by_type(self, app_type: str) -> AppTemplate:
        """根据类型获取应用模板"""
        template = (
            self.db.query(AppTemplate)
            .filter(AppTemplate.app_type == app_type, AppTemplate.is_active == True)
            .first()
        )

        if not template:
            raise NotFoundException(
                f"未找到类型为{app_type}的应用模板", APPLICATION_NOT_FOUND
            )

        return template


    def get_by_id(self, id: str) -> AppTemplate:
        """根据ID获取应用模板"""
        template = (
            self.db.query(AppTemplate)
            .filter(AppTemplate.id == id, AppTemplate.is_active == True)
            .first()
        )

        if not template:
            raise NotFoundException(
                f"未找到ID为{id}的应用模板"
            )

        return template
