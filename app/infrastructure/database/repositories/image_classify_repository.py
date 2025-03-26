# app/infrastructure/database/repositories/image_classify_repository.py
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.infrastructure.database.models.image_classify import ImageClassification
from app.core.exceptions import NotFoundException
from app.core.status_codes import CLASSIFICATION_NOT_FOUND

class ImageClassifyRepository:
    """图片分类存储库"""

    def __init__(self, db_session: Session):
        """初始化存储库"""
        self.db = db_session

    def get_all_by_user(
        self, user_id: str, page: int = 1, per_page: int = 20, **filters
    ) -> Tuple[List[ImageClassification], int]:
        """获取用户的所有分类记录"""
        query = self.db.query(ImageClassification).filter(
            ImageClassification.user_id == user_id
        )

        # 应用过滤条件
        if filters.get("status"):
            query = query.filter(ImageClassification.status == filters["status"])

        if filters.get("app_id"):
            query = query.filter(ImageClassification.app_id == filters["app_id"])

        if filters.get("start_date") and filters.get("end_date"):
            query = query.filter(
                ImageClassification.created_at >= filters["start_date"],
                ImageClassification.created_at <= filters["end_date"],
            )

        # 计算总数
        total = query.count()

        # 分页
        records = (
            query.order_by(ImageClassification.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return records, total

    def get_by_id(self, classification_id: int, user_id: str) -> ImageClassification:
        """根据ID获取分类记录"""
        record = (
            self.db.query(ImageClassification)
            .filter(
                ImageClassification.id == classification_id,
                ImageClassification.user_id == user_id,
            )
            .first()
        )

        if not record:
            raise NotFoundException(
                f"未找到ID为{classification_id}的分类记录", CLASSIFICATION_NOT_FOUND
            )

        return record

    def create(self, record_data: dict) -> ImageClassification:
        """创建新分类记录"""
        record = ImageClassification(**record_data)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def update(self, classification_id: int, user_id: str, update_data: dict) -> ImageClassification:
        """更新分类记录"""
        record = self.get_by_id(classification_id, user_id)

        for key, value in update_data.items():
            if hasattr(record, key):
                setattr(record, key, value)

        self.db.commit()
        self.db.refresh(record)
        return record