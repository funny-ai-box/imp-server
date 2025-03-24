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

    def get_by_app_id(self, app_id: str) -> AppTemplate:
        """根据应用ID获取应用模板"""
        template = (
            self.db.query(AppTemplate)
            .filter(AppTemplate.app_id == app_id, AppTemplate.is_active == True)
            .first()
        )

        if not template:
            raise NotFoundException(
                f"未找到应用ID为{app_id}的应用模板", APPLICATION_NOT_FOUND
            )

        return template

    def get_by_id(self, template_id: int) -> AppTemplate:
        """根据ID获取应用模板"""
        template = (
            self.db.query(AppTemplate)
            .filter(AppTemplate.id == template_id, AppTemplate.is_active == True)
            .first()
        )

        if not template:
            raise NotFoundException(
                f"未找到ID为{template_id}的应用模板"
            )

        return template

    # 以下方法仅供管理员使用
    def create(self, template_data: dict) -> AppTemplate:
        """创建新应用模板"""
        template = AppTemplate(**template_data)
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def update(self, template_id: int, template_data: dict) -> AppTemplate:
        """更新应用模板"""
        template = self.db.query(AppTemplate).get(template_id)

        if not template:
            raise NotFoundException(
                f"未找到ID为{template_id}的应用模板", APPLICATION_NOT_FOUND
            )

        for key, value in template_data.items():
            if hasattr(template, key):
                setattr(template, key, value)

        self.db.commit()
        self.db.refresh(template)
        return template

    def delete(self, template_id: int) -> bool:
        """删除应用模板（通常我们只设置为非活跃而不实际删除）"""
        template = self.db.query(AppTemplate).get(template_id)

        if not template:
            raise NotFoundException(
                f"未找到ID为{template_id}的应用模板", APPLICATION_NOT_FOUND
            )

        template.is_active = False
        self.db.commit()
        return True
