# app/infrastructure/database/repositories/user_llm_config_repository.py
from typing import List, Optional, Dict, Any, Tuple
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.infrastructure.database.models.user_llm_config import UserLLMConfig
from app.core.exceptions import NotFoundException
from app.core.status_codes import CONFIG_NOT_FOUND

logger = logging.getLogger(__name__)

class UserLLMConfigRepository:
    """用户LLM配置存储库"""

    def __init__(self, db_session: Session):
        """初始化存储库"""
        self.db = db_session

    def get_all_by_user(self, user_id: str) -> List[UserLLMConfig]:
        """获取用户的所有LLM配置"""
        try:
            return (
                self.db.query(UserLLMConfig).filter(UserLLMConfig.user_id == user_id).all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error fetching configs: {str(e)}")
            self.db.rollback()
            raise

    def get_by_id(self, config_id: int, user_id: str) -> UserLLMConfig:
        """根据ID获取特定用户的LLM配置"""
        try:
            config = (
                self.db.query(UserLLMConfig)
                .filter(UserLLMConfig.id == config_id, UserLLMConfig.user_id == user_id)
                .first()
            )

            if not config:
                raise NotFoundException(f"未找到ID为{config_id}的配置", CONFIG_NOT_FOUND)

            return config
        except SQLAlchemyError as e:
            logger.error(f"Error fetching config: {str(e)}")
            self.db.rollback()
            raise

    def get_default(
        self, user_id: str, provider_type: Optional[str] = None
    ) -> Optional[UserLLMConfig]:
        """获取用户的默认LLM配置"""
        try:
            query = self.db.query(UserLLMConfig).filter(
                UserLLMConfig.user_id == user_id, UserLLMConfig.is_default == True
            )

            if provider_type:
                query = query.filter(UserLLMConfig.provider_type == provider_type)

            return query.first()
        except SQLAlchemyError as e:
            logger.error(f"Error fetching default config: {str(e)}")
            self.db.rollback()
            raise

    def create(self, config_data: dict) -> UserLLMConfig:
        """创建新配置"""
        try:
            # 开始事务
            config = UserLLMConfig(**config_data)
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
            return config
        except SQLAlchemyError as e:
            logger.error(f"Error creating config: {str(e)}")
            self.db.rollback()
            raise

    def update(self, config_id: int, user_id: str, config_data: dict) -> UserLLMConfig:
        """更新配置"""
        try:
            # 获取配置
            config = self.get_by_id(config_id, user_id)
            
            # 更新字段
            for key, value in config_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            # 提交事务
            self.db.commit()
            self.db.refresh(config)
            return config
        except SQLAlchemyError as e:
            logger.error(f"Error updating config: {str(e)}")
            self.db.rollback()
            raise

    def delete(self, config_id: int, user_id: str) -> bool:
        """删除配置"""
        try:
            # 获取配置
            config = self.get_by_id(config_id, user_id)
            
            # 删除配置
            self.db.delete(config)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting config: {str(e)}")
            self.db.rollback()
            raise

    def set_as_default(self, config_id: int, user_id: str) -> UserLLMConfig:
        """设置配置为默认"""
        try:
            # 获取配置
            config = self.get_by_id(config_id, user_id)
            
            # 将所有同类型配置设为非默认
            self.db.query(UserLLMConfig).filter(
                UserLLMConfig.user_id == user_id,
                UserLLMConfig.provider_type == config.provider_type,
                UserLLMConfig.id != config_id
            ).update({"is_default": False})
            
            # 设置当前配置为默认
            config.is_default = True
            self.db.commit()
            self.db.refresh(config)
            return config
        except SQLAlchemyError as e:
            logger.error(f"Error setting default config: {str(e)}")
            self.db.rollback()
            raise