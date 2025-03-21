# app/infrastructure/database/repositories/user_llm_config_repository.py
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.infrastructure.database.models.user_llm_config import UserLLMConfig
from app.core.exceptions import NotFoundException
from app.core.status_codes import CONFIG_NOT_FOUND


class UserLLMConfigRepository:
    """用户LLM配置存储库"""

    def __init__(self, db_session: Session):
        """初始化存储库"""
        self.db = db_session

    def get_all_by_user(self, user_id: str) -> List[UserLLMConfig]:
        """获取用户的所有LLM配置"""
        return (
            self.db.query(UserLLMConfig).filter(UserLLMConfig.user_id == user_id).all()
        )

    def get_by_id(self, config_id: int, user_id: str) -> UserLLMConfig:
        """根据ID获取特定用户的LLM配置"""
        config = (
            self.db.query(UserLLMConfig)
            .filter(UserLLMConfig.id == config_id, UserLLMConfig.user_id == user_id)
            .first()
        )

        if not config:
            raise NotFoundException(f"未找到ID为{config_id}的配置", CONFIG_NOT_FOUND)

        return config

    def get_default(
        self, user_id: str, provider_type: Optional[str] = None
    ) -> Optional[UserLLMConfig]:
        """获取用户的默认LLM配置"""
        query = self.db.query(UserLLMConfig).filter(
            UserLLMConfig.user_id == user_id, UserLLMConfig.is_default == True
        )

        if provider_type:
            query = query.filter(UserLLMConfig.provider_type == provider_type)

        return query.first()

    def create(self, config_data: dict) -> UserLLMConfig:
        """创建新配置"""
        # 如果设置为默认，将同一用户同一提供商类型的其他配置设为非默认
        if config_data.get("is_default", False):
            self.db.query(UserLLMConfig).filter(
                UserLLMConfig.user_id == config_data["user_id"],
                UserLLMConfig.provider_type == config_data["provider_type"],
                UserLLMConfig.is_default == True,
            ).update({"is_default": False})

        config = UserLLMConfig(**config_data)
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def update(self, config_id: int, user_id: str, config_data: dict) -> UserLLMConfig:
        """更新配置"""
        config = self.get_by_id(config_id, user_id)

        # 如果设置为默认，将同一用户同一提供商类型的其他配置设为非默认
        if config_data.get("is_default", False) and not config.is_default:
            self.db.query(UserLLMConfig).filter(
                UserLLMConfig.user_id == user_id,
                UserLLMConfig.provider_type == config.provider_type,
                UserLLMConfig.id != config_id,
                UserLLMConfig.is_default == True,
            ).update({"is_default": False})

        for key, value in config_data.items():
            if hasattr(config, key):
                setattr(config, key, value)

        self.db.commit()
        self.db.refresh(config)
        return config

    def delete(self, config_id: int, user_id: str) -> bool:
        """删除配置"""
        config = self.get_by_id(config_id, user_id)

        # 如果删除的是默认配置，尝试将同类型的另一个配置设为默认
        if config.is_default:
            other_config = (
                self.db.query(UserLLMConfig)
                .filter(
                    UserLLMConfig.user_id == user_id,
                    UserLLMConfig.provider_type == config.provider_type,
                    UserLLMConfig.id != config_id,
                )
                .first()
            )

            if other_config:
                other_config.is_default = True
                self.db.commit()

        self.db.delete(config)
        self.db.commit()
        return True

    def set_as_default(self, config_id: int, user_id: str) -> UserLLMConfig:
        """设置配置为默认"""
        config = self.get_by_id(config_id, user_id)

        # 将同一用户同一提供商类型的其他配置设为非默认
        self.db.query(UserLLMConfig).filter(
            UserLLMConfig.user_id == user_id,
            UserLLMConfig.provider_type == config.provider_type,
            UserLLMConfig.id != config_id,
        ).update({"is_default": False})

        config.is_default = True
        self.db.commit()
        self.db.refresh(config)
        return config
