# app/infrastructure/database/repositories/image_classification_repository.py
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.infrastructure.database.models.image_classification import ImageClassificationConfig, ImageClassification
from app.core.exceptions import NotFoundException
from app.core.status_codes import CONFIG_NOT_FOUND, CLASSIFICATION_NOT_FOUND

class ImageClassificationConfigRepository:
    """图片分类配置存储库"""
    
    def __init__(self, db_session: Session):
        """初始化存储库"""
        self.db = db_session
    
    def get_all_by_user(self, user_id: int) -> List[ImageClassificationConfig]:
        """获取用户的所有配置"""
        return self.db.query(ImageClassificationConfig).filter(
            ImageClassificationConfig.user_id == user_id
        ).order_by(ImageClassificationConfig.created_at.desc()).all()
    
    def get_by_id(self, config_id: int, user_id: int) -> ImageClassificationConfig:
        """根据ID获取配置"""
        config = self.db.query(ImageClassificationConfig).filter(
            ImageClassificationConfig.id == config_id,
            ImageClassificationConfig.user_id == user_id
        ).first()
        
        if not config:
            raise NotFoundException(f"未找到ID为{config_id}的图片分类配置", CONFIG_NOT_FOUND)
        
        return config
    
    def get_default(self, user_id: int) -> Optional[ImageClassificationConfig]:
        """获取用户的默认配置"""
        return self.db.query(ImageClassificationConfig).filter(
            ImageClassificationConfig.user_id == user_id,
            ImageClassificationConfig.is_default == True
        ).first()
    
    def create(self, config_data: dict) -> ImageClassificationConfig:
        """创建新配置"""
        config = ImageClassificationConfig(**config_data)
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config
    
    def update(self, config_id: int, user_id: int, config_data: dict) -> ImageClassificationConfig:
        """更新配置"""
        config = self.get_by_id(config_id, user_id)
        
        for key, value in config_data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        self.db.commit()
        self.db.refresh(config)
        return config
    
    def delete(self, config_id: int, user_id: int) -> bool:
        """删除配置"""
        config = self.get_by_id(config_id, user_id)
        self.db.delete(config)
        self.db.commit()
        return True
    
    def set_as_default(self, config_id: int, user_id: int) -> ImageClassificationConfig:
        """设置配置为默认"""
        # 先将所有配置设为非默认
        self.db.query(ImageClassificationConfig).filter(
            ImageClassificationConfig.user_id == user_id
        ).update({"is_default": False})
        
        # 将指定配置设为默认
        config = self.get_by_id(config_id, user_id)
        config.is_default = True
        self.db.commit()
        self.db.refresh(config)
        return config


class ImageClassificationRepository:
    """图片分类记录存储库"""
    
    def __init__(self, db_session: Session):
        """初始化存储库"""
        self.db = db_session
    
    def get_all_by_user(self, user_id: int, page: int = 1, per_page: int = 20, **filters) -> Tuple[List[ImageClassification], int]:
        """获取用户的所有分类记录"""
        query = self.db.query(ImageClassification).filter(
            ImageClassification.user_id == user_id
        )
        
        # 应用过滤条件
        if filters.get("status"):
            query = query.filter(ImageClassification.status == filters["status"])
        
        if filters.get("config_id"):
            query = query.filter(ImageClassification.config_id == filters["config_id"])
        
        if filters.get("app_id"):
            query = query.filter(ImageClassification.app_id == filters["app_id"])
        
        if filters.get("start_date") and filters.get("end_date"):
            query = query.filter(
                ImageClassification.created_at >= filters["start_date"],
                ImageClassification.created_at <= filters["end_date"]
            )
        
        # 计算总数
        total = query.count()
        
        # 分页
        classifications = query.order_by(ImageClassification.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        return classifications, total
    
    def get_by_id(self, classification_id: int, user_id: int) -> ImageClassification:
        """根据ID获取分类记录"""
        classification = self.db.query(ImageClassification).filter(
            ImageClassification.id == classification_id,
            ImageClassification.user_id == user_id
        ).first()
        
        if not classification:
            raise NotFoundException(f"未找到ID为{classification_id}的分类记录", CLASSIFICATION_NOT_FOUND)
        
        return classification
    
    def create(self, classification_data: dict) -> ImageClassification:
        """创建新分类记录"""
        classification = ImageClassification(**classification_data)
        self.db.add(classification)
        self.db.commit()
        self.db.refresh(classification)
        return classification
    
    def update(self, classification_id: int, user_id: int, classification_data: dict) -> ImageClassification:
        """更新分类记录"""
        classification = self.get_by_id(classification_id, user_id)
        
        for key, value in classification_data.items():
            if hasattr(classification, key):
                setattr(classification, key, value)
        
        self.db.commit()
        self.db.refresh(classification)
        return classification
    
    def delete(self, classification_id: int, user_id: int) -> bool:
        """删除分类记录"""
        classification = self.get_by_id(classification_id, user_id)
        self.db.delete(classification)
        self.db.commit()
        return True
    
    def get_statistics(self, user_id: int, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """获取分类统计数据"""
        query = self.db.query(ImageClassification).filter(
            ImageClassification.user_id == user_id
        )
        
        if start_date and end_date:
            query = query.filter(
                ImageClassification.created_at >= start_date,
                ImageClassification.created_at <= end_date
            )
        
        # 总分类次数
        total_classifications = query.count()
        
        # 成功分类次数
        successful_classifications = query.filter(ImageClassification.status == "completed").count()
        
        # 失败分类次数
        failed_classifications = query.filter(ImageClassification.status == "failed").count()
        
        # 平均处理时间
        avg_duration = self.db.query(func.avg(ImageClassification.duration_ms)).filter(
            ImageClassification.user_id == user_id,
            ImageClassification.status == "completed"
        ).scalar() or 0
        
        # 总Token使用量
        total_tokens = self.db.query(func.sum(ImageClassification.tokens_used)).filter(
            ImageClassification.user_id == user_id
        ).scalar() or 0
        
        # 最近一次分类时间
        latest_classification = query.order_by(ImageClassification.created_at.desc()).first()
        latest_time = latest_classification.created_at if latest_classification else None
        
        return {
            "total_classifications": total_classifications,
            "successful_classifications": successful_classifications,
            "failed_classifications": failed_classifications,
            "avg_duration_ms": float(avg_duration),
            "total_tokens_used": int(total_tokens),
            "latest_classification_time": latest_time.isoformat() if latest_time else None
        }