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

    def update(
        self, classification_id: int, user_id: str, record_data: dict
    ) -> ImageClassification:
        """更新分类记录"""
        record = self.get_by_id(classification_id, user_id)

        for key, value in record_data.items():
            if hasattr(record, key):
                setattr(record, key, value)

        self.db.commit()
        self.db.refresh(record)
        return record

    def delete(self, classification_id: int, user_id: str) -> bool:
        """删除分类记录"""
        record = self.get_by_id(classification_id, user_id)
        self.db.delete(record)
        self.db.commit()
        return True

    def get_statistics(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """获取分类统计数据"""
        query = self.db.query(ImageClassification).filter(
            ImageClassification.user_id == user_id
        )

        if start_date and end_date:
            query = query.filter(
                ImageClassification.created_at >= start_date,
                ImageClassification.created_at <= end_date,
            )

        # 总分类次数
        total_classifications = query.count()

        # 成功分类次数
        successful_classifications = query.filter(
            ImageClassification.status == "completed"
        ).count()

        # 失败分类次数
        failed_classifications = query.filter(
            ImageClassification.status == "failed"
        ).count()

        # 平均处理时间
        avg_duration = (
            self.db.query(func.avg(ImageClassification.duration_ms))
            .filter(
                ImageClassification.user_id == user_id,
                ImageClassification.status == "completed",
            )
            .scalar()
            or 0
        )

        # 总Token使用量
        total_tokens = (
            self.db.query(func.sum(ImageClassification.tokens_used))
            .filter(ImageClassification.user_id == user_id)
            .scalar()
            or 0
        )

        # 最近一次分类时间
        latest_classification = query.order_by(ImageClassification.created_at.desc()).first()
        latest_time = latest_classification.created_at if latest_classification else None

        return {
            "total_classifications": total_classifications,
            "successful_classifications": successful_classifications,
            "failed_classifications": failed_classifications,
            "avg_duration_ms": float(avg_duration),
            "total_tokens_used": int(total_tokens),
            "latest_classification_time": latest_time.isoformat() if latest_time else None,
        }