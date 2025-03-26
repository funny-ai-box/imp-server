# app/infrastructure/database/repositories/xhs_copy_repository.py
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.infrastructure.database.models.xhs_copy_app import XhsCopyGeneration
from app.core.exceptions import NotFoundException
from app.core.status_codes import CONFIG_NOT_FOUND, GENERATION_NOT_FOUND, TEST_NOT_FOUND


class XhsCopyGenerationRepository:
    """小红书文案生成记录存储库"""

    def __init__(self, db_session: Session):
        """初始化存储库"""
        self.db = db_session

    def get_all_by_user(
        self, user_id: str, page: int = 1, per_page: int = 20, **filters
    ) -> tuple[List[XhsCopyGeneration], int]:
        """获取用户的所有生成记录"""
        query = self.db.query(XhsCopyGeneration).filter(
            XhsCopyGeneration.user_id == user_id
        )

        # 应用过滤条件
        if filters.get("status"):
            query = query.filter(XhsCopyGeneration.status == filters["status"])

        if filters.get("config_id"):
            query = query.filter(XhsCopyGeneration.config_id == filters["config_id"])

        if filters.get("app_id"):
            query = query.filter(XhsCopyGeneration.app_id == filters["app_id"])

        if filters.get("start_date") and filters.get("end_date"):
            query = query.filter(
                XhsCopyGeneration.created_at >= filters["start_date"],
                XhsCopyGeneration.created_at <= filters["end_date"],
            )

        # 计算总数
        total = query.count()

        # 分页
        generations = (
            query.order_by(XhsCopyGeneration.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return generations, total

    def get_by_id(self, generation_id: int, user_id: str) -> XhsCopyGeneration:
        """根据ID获取生成记录"""
        generation = (
            self.db.query(XhsCopyGeneration)
            .filter(
                XhsCopyGeneration.id == generation_id,
                XhsCopyGeneration.user_id == user_id,
            )
            .first()
        )

        if not generation:
            raise NotFoundException(
                f"未找到ID为{generation_id}的生成记录", GENERATION_NOT_FOUND
            )

        return generation

    def create(self, generation_data: dict) -> XhsCopyGeneration:
        """创建新生成记录"""
        generation = XhsCopyGeneration(**generation_data)
        self.db.add(generation)
        self.db.commit()
        self.db.refresh(generation)
        return generation

    def update(
        self, generation_id: int, user_id: str, generation_data: dict
    ) -> XhsCopyGeneration:
        """更新生成记录"""
        generation = self.get_by_id(generation_id, user_id)

        for key, value in generation_data.items():
            if hasattr(generation, key):
                setattr(generation, key, value)

        self.db.commit()
        self.db.refresh(generation)
        return generation

    def delete(self, generation_id: int, user_id: str) -> bool:
        """删除生成记录"""
        generation = self.get_by_id(generation_id, user_id)
        self.db.delete(generation)
        self.db.commit()
        return True
