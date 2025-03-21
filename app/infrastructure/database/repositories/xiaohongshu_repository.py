# app/infrastructure/database/repositories/xiaohongshu_repository.py
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.infrastructure.database.models.xiaohongshu_app import XiaohongshuAppConfig, XiaohongshuGeneration, XiaohongshuTestResult
from app.core.exceptions import NotFoundException
from app.core.status_codes import CONFIG_NOT_FOUND, GENERATION_NOT_FOUND, TEST_NOT_FOUND


class XiaohongshuConfigRepository:
    """小红书应用配置存储库"""
    
    def __init__(self, db_session: Session):
        """初始化存储库"""
        self.db = db_session
    
    def get_all_by_user(self, user_id: str) -> List[XiaohongshuAppConfig]:
        """获取用户的所有配置"""
        return self.db.query(XiaohongshuAppConfig).filter(
            XiaohongshuAppConfig.user_id == user_id
        ).order_by(XiaohongshuAppConfig.created_at.desc()).all()
    
    def get_by_id(self, config_id: int, user_id: str) -> XiaohongshuAppConfig:
        """根据ID获取配置"""
        config = self.db.query(XiaohongshuAppConfig).filter(
            XiaohongshuAppConfig.id == config_id,
            XiaohongshuAppConfig.user_id == user_id
        ).first()
        
        if not config:
            raise NotFoundException(f"未找到ID为{config_id}的小红书配置", CONFIG_NOT_FOUND)
        
        return config
    
    def get_default(self, user_id: str) -> Optional[XiaohongshuAppConfig]:
        """获取用户的默认配置"""
        return self.db.query(XiaohongshuAppConfig).filter(
            XiaohongshuAppConfig.user_id == user_id,
            XiaohongshuAppConfig.is_default == True
        ).first()
    
    def create(self, config_data: dict) -> XiaohongshuAppConfig:
        """创建新配置"""
        config = XiaohongshuAppConfig(**config_data)
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config
    
    def update(self, config_id: int, user_id: str, config_data: dict) -> XiaohongshuAppConfig:
        """更新配置"""
        config = self.get_by_id(config_id, user_id)
        
        for key, value in config_data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        self.db.commit()
        self.db.refresh(config)
        return config
    
    def delete(self, config_id: int, user_id: str) -> bool:
        """删除配置"""
        config = self.get_by_id(config_id, user_id)
        self.db.delete(config)
        self.db.commit()
        return True
    
    def set_as_default(self, config_id: int, user_id: str) -> XiaohongshuAppConfig:
        """设置配置为默认"""
        # 先将所有配置设为非默认
        self.db.query(XiaohongshuAppConfig).filter(
            XiaohongshuAppConfig.user_id == user_id
        ).update({"is_default": False})
        
        # 将指定配置设为默认
        config = self.get_by_id(config_id, user_id)
        config.is_default = True
        self.db.commit()
        self.db.refresh(config)
        return config


class XiaohongshuGenerationRepository:
    """小红书文案生成记录存储库"""
    
    def __init__(self, db_session: Session):
        """初始化存储库"""
        self.db = db_session
    
    def get_all_by_user(self, user_id: str, page: int = 1, per_page: int = 20, **filters) -> tuple[List[XiaohongshuGeneration], int]:
        """获取用户的所有生成记录"""
        query = self.db.query(XiaohongshuGeneration).filter(
            XiaohongshuGeneration.user_id == user_id
        )
        
        # 应用过滤条件
        if filters.get("status"):
            query = query.filter(XiaohongshuGeneration.status == filters["status"])
        
        if filters.get("config_id"):
            query = query.filter(XiaohongshuGeneration.config_id == filters["config_id"])
        
        if filters.get("app_id"):
            query = query.filter(XiaohongshuGeneration.app_id == filters["app_id"])
        
        if filters.get("start_date") and filters.get("end_date"):
            query = query.filter(
                XiaohongshuGeneration.created_at >= filters["start_date"],
                XiaohongshuGeneration.created_at <= filters["end_date"]
            )
        
        # 计算总数
        total = query.count()
        
        # 分页
        generations = query.order_by(XiaohongshuGeneration.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        return generations, total
    
    def get_by_id(self, generation_id: int, user_id: str) -> XiaohongshuGeneration:
        """根据ID获取生成记录"""
        generation = self.db.query(XiaohongshuGeneration).filter(
            XiaohongshuGeneration.id == generation_id,
            XiaohongshuGeneration.user_id == user_id
        ).first()
        
        if not generation:
            raise NotFoundException(f"未找到ID为{generation_id}的生成记录", GENERATION_NOT_FOUND)
        
        return generation
    
    def create(self, generation_data: dict) -> XiaohongshuGeneration:
        """创建新生成记录"""
        generation = XiaohongshuGeneration(**generation_data)
        self.db.add(generation)
        self.db.commit()
        self.db.refresh(generation)
        return generation
    
    def update(self, generation_id: int, user_id: str, generation_data: dict) -> XiaohongshuGeneration:
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
    
    def get_statistics(self, user_id: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """获取生成统计数据"""
        query = self.db.query(XiaohongshuGeneration).filter(
            XiaohongshuGeneration.user_id == user_id
        )
        
        if start_date and end_date:
            query = query.filter(
                XiaohongshuGeneration.created_at >= start_date,
                XiaohongshuGeneration.created_at <= end_date
            )
        
        # 总生成次数
        total_generations = query.count()
        
        # 成功生成次数
        successful_generations = query.filter(XiaohongshuGeneration.status == "completed").count()
        
        # 失败生成次数
        failed_generations = query.filter(XiaohongshuGeneration.status == "failed").count()
        
        # 平均处理时间
        avg_duration = self.db.query(func.avg(XiaohongshuGeneration.duration_ms)).filter(
            XiaohongshuGeneration.user_id == user_id,
            XiaohongshuGeneration.status == "completed"
        ).scalar() or 0
        
        # 总Token使用量
        total_tokens = self.db.query(func.sum(XiaohongshuGeneration.tokens_used)).filter(
            XiaohongshuGeneration.user_id == user_id
        ).scalar() or 0
        
        # 最近一次生成时间
        latest_generation = query.order_by(XiaohongshuGeneration.created_at.desc()).first()
        latest_time = latest_generation.created_at if latest_generation else None
        
        return {
            "total_generations": total_generations,
            "successful_generations": successful_generations,
            "failed_generations": failed_generations,
            "avg_duration_ms": float(avg_duration),
            "total_tokens_used": int(total_tokens),
            "latest_generation_time": latest_time.isoformat() if latest_time else None
        }


class XiaohongshuTestRepository:
    """小红书测试结果存储库"""
    
    def __init__(self, db_session: Session):
        """初始化存储库"""
        self.db = db_session
    
    def get_all_by_user(self, user_id: str, page: int = 1, per_page: int = 20) -> tuple[List[XiaohongshuTestResult], int]:
        """获取用户的所有测试结果"""
        query = self.db.query(XiaohongshuTestResult).filter(
            XiaohongshuTestResult.user_id == user_id
        )
        
        # 计算总数
        total = query.count()
        
        # 分页
        tests = query.order_by(XiaohongshuTestResult.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        return tests, total
    
    def get_by_id(self, test_id: int, user_id: str) -> XiaohongshuTestResult:
        """根据ID获取测试结果"""
        test = self.db.query(XiaohongshuTestResult).filter(
            XiaohongshuTestResult.id == test_id,
            XiaohongshuTestResult.user_id == user_id
        ).first()
        
        if not test:
            raise NotFoundException(f"未找到ID为{test_id}的测试结果", TEST_NOT_FOUND)
        
        return test
    
    def create(self, test_data: dict) -> XiaohongshuTestResult:
        """创建新测试结果"""
        test = XiaohongshuTestResult(**test_data)
        self.db.add(test)
        self.db.commit()
        self.db.refresh(test)
        return test
    
    def update(self, test_id: int, user_id: str, test_data: dict) -> XiaohongshuTestResult:
        """更新测试结果"""
        test = self.get_by_id(test_id, user_id)
        
        for key, value in test_data.items():
            if hasattr(test, key):
                setattr(test, key, value)
        
        self.db.commit()
        self.db.refresh(test)
        return test
    
    def delete(self, test_id: int, user_id: str) -> bool:
        """删除测试结果"""
        test = self.get_by_id(test_id, user_id)
        self.db.delete(test)
        self.db.commit()
        return True