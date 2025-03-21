# app/domains/foundation/services/user_llm_config_service.py
from typing import List, Dict, Any, Optional
import logging
from app.infrastructure.database.repositories.user_llm_config_repository import (
    UserLLMConfigRepository,
)
from app.core.exceptions import ValidationException, NotFoundException
from app.core.status_codes import PARAMETER_ERROR, CONFIG_NOT_FOUND

logger = logging.getLogger(__name__)

class UserLLMConfigService:
    """用户LLM配置服务"""

    def __init__(self, config_repository: UserLLMConfigRepository):
        """初始化服务"""
        self.config_repo = config_repository

    def get_all_configs(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户所有LLM配置"""
        configs = self.config_repo.get_all_by_user(user_id)
        return [self._format_config(config) for config in configs]

    def get_config(self, config_id: int, user_id: str) -> Dict[str, Any]:
        """获取特定LLM配置"""
        config = self.config_repo.get_by_id(config_id, user_id)
        return self._format_config(config)

    def get_default_config(
        self, user_id: str, provider_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """获取默认LLM配置"""
        config = self.config_repo.get_default(user_id, provider_type)
        if not config:
            return None
        return self._format_config(config)

    def create_config(
        self, config_data: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """创建新的LLM配置"""
        # 验证数据
        self._validate_config_data(config_data)

        # 设置用户ID
        config_data["user_id"] = user_id
        
        # 如果设置为默认配置或该类型没有其他配置，则设为默认
        is_default = config_data.get("is_default", False)
        if "provider_type" in config_data:
            # 检查是否已有同类型的配置
            existing_default = self.config_repo.get_default(user_id, config_data["provider_type"])
            if not existing_default or is_default:
                config_data["is_default"] = True
                
                # 如果要设为默认，先取消其他同类型配置的默认状态
                if is_default and existing_default:
                    try:
                        self.config_repo.update(existing_default.id, user_id, {"is_default": False})
                    except Exception as e:
                        logger.error(f"Failed to reset default status: {str(e)}")

        # 创建配置
        config = self.config_repo.create(config_data)
        return self._format_config(config)

    def update_config(
        self, config_id: int, config_data: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """更新LLM配置"""
        # 获取当前配置
        current_config = self.config_repo.get_by_id(config_id, user_id)
        
        # 验证数据
        if config_data:
            self._validate_config_data(config_data, is_update=True)

        # 如果要设置为默认且当前未设为默认
        if config_data.get("is_default", False) and not current_config.is_default:
            # 取消其他同类型配置的默认状态
            provider_type = config_data.get("provider_type", current_config.provider_type)
            try:
                existing_configs = self.config_repo.get_all_by_user(user_id)
                for config in existing_configs:
                    if (config.id != config_id and 
                        config.provider_type == provider_type and 
                        config.is_default):
                        self.config_repo.update(config.id, user_id, {"is_default": False})
            except Exception as e:
                logger.error(f"Failed to reset default status: {str(e)}")

        # 更新配置
        config = self.config_repo.update(config_id, user_id, config_data)
        return self._format_config(config)

    def delete_config(self, config_id: int, user_id: str) -> bool:
        """删除LLM配置"""
        # 获取当前配置
        config = self.config_repo.get_by_id(config_id, user_id)
        
        # 检查是否为默认配置
        if config.is_default:
            # 尝试将同类型的另一个配置设为默认
            try:
                other_configs = self.config_repo.get_all_by_user(user_id)
                alternatives = [c for c in other_configs 
                               if c.id != config_id and c.provider_type == config.provider_type]
                
                if alternatives:
                    # 选择第一个替代配置设为默认
                    self.config_repo.update(alternatives[0].id, user_id, {"is_default": True})
            except Exception as e:
                logger.error(f"Failed to set alternative default config: {str(e)}")
        
        return self.config_repo.delete(config_id, user_id)

    def set_default_config(self, config_id: int, user_id: str) -> Dict[str, Any]:
        """设置默认LLM配置"""
        # 获取当前配置
        config = self.config_repo.get_by_id(config_id, user_id)
        
        try:
            # 取消同类型其他配置的默认状态
            other_configs = self.config_repo.get_all_by_user(user_id)
            for other_config in other_configs:
                if (other_config.id != config_id and 
                    other_config.provider_type == config.provider_type and 
                    other_config.is_default):
                    self.config_repo.update(other_config.id, user_id, {"is_default": False})
            
            # 设置当前配置为默认
            config = self.config_repo.set_as_default(config_id, user_id)
            return self._format_config(config)
        except Exception as e:
            logger.error(f"Failed to set default config: {str(e)}")
            raise

    def _format_config(self, config) -> Dict[str, Any]:
        """格式化配置数据，保护敏感信息"""
        # 安全屏蔽敏感信息
        def mask_sensitive(value: Optional[str]) -> Optional[str]:
            if not value or len(value) < 8:
                return None
            return f"***{value[-4:]}"
        
        result = {
            "id": config.id,
            "name": config.name,
            "provider_type": config.provider_type,
            "api_key": mask_sensitive(config.api_key),
            "api_secret": mask_sensitive(config.api_secret),
            "app_id": config.app_id,
            "app_key": mask_sensitive(config.app_key),
            "app_secret": mask_sensitive(config.app_secret),
            "api_base_url": config.api_base_url,
            "api_version": config.api_version,
            "region": config.region,
            "is_default": config.is_default,
            "is_active": config.is_active,
            "request_timeout": config.request_timeout,
            "max_retries": config.max_retries,
            "remark": config.remark,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None,
        }

        # 对不同提供商返回不同的鉴权信息
        if config.provider_type in ["OpenAI", "Claude", "Gemini"]:
            # OpenAI和Claude使用api_key
            result["auth_type"] = "api_key"
        elif config.provider_type in ["Baidu", "Aliyun"]:
            # 百度和阿里云使用app_key和app_secret
            result["auth_type"] = "key_secret"
        elif config.provider_type in ["Volcano", "Tencent"]:
            # 火山引擎和腾讯云使用app_id、app_key和app_secret
            result["auth_type"] = "id_key_secret"

        return result

    def _validate_config_data(
        self, data: Dict[str, Any], is_update: bool = False
    ) -> None:
        """验证配置数据"""
        if not is_update:
            # 必填字段验证
            required_fields = ["name", "provider_type"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                raise ValidationException(
                    f"缺少必填字段: {', '.join(missing_fields)}", PARAMETER_ERROR
                )

        # 提供商类型验证
        if "provider_type" in data:
            valid_types = [
                "OpenAI",
                "Claude",
                "Volcano",
                "Gemini",
                "Baidu",
                "Aliyun",
                "Tencent",
            ]
            if data["provider_type"] not in valid_types:
                raise ValidationException(
                    f"无效的提供商类型: {data['provider_type']}，有效类型: {', '.join(valid_types)}",
                    PARAMETER_ERROR,
                )

            # 根据提供商类型验证必要的鉴权字段
            provider_type = data["provider_type"]
            if not is_update and provider_type in ["OpenAI", "Claude", "Gemini"]:
                if "api_key" not in data or not data["api_key"]:
                    raise ValidationException(
                        f"{provider_type}配置必须提供api_key", PARAMETER_ERROR
                    )
            elif not is_update and provider_type in ["Baidu", "Aliyun"]:
                if "app_key" not in data or not data["app_key"] or "app_secret" not in data or not data["app_secret"]:
                    raise ValidationException(
                        f"{provider_type}配置必须提供app_key和app_secret", PARAMETER_ERROR
                    )
            elif not is_update and provider_type in ["Volcano", "Tencent"]:
                if ("app_id" not in data or not data["app_id"] or
                    "app_key" not in data or not data["app_key"] or
                    "app_secret" not in data or not data["app_secret"]):
                    raise ValidationException(
                        f"{provider_type}配置必须提供app_id、app_key和app_secret", PARAMETER_ERROR
                    )

        # 超时时间验证
        if "request_timeout" in data:
            timeout = data["request_timeout"]
            if not isinstance(timeout, int) or timeout < 1 or timeout > 300:
                raise ValidationException(
                    "请求超时时间必须在1-300秒之间", PARAMETER_ERROR
                )

        # 重试次数验证
        if "max_retries" in data:
            retries = data["max_retries"]
            if not isinstance(retries, int) or retries < 0 or retries > 10:
                raise ValidationException("最大重试次数必须在0-10之间", PARAMETER_ERROR)