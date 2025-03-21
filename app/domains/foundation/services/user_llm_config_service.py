# app/domains/foundation/services/user_llm_config_service.py
from typing import List, Dict, Any, Optional
from app.infrastructure.database.repositories.user_llm_config_repository import (
    UserLLMConfigRepository,
)
from app.core.exceptions import ValidationException
from app.core.status_codes import PARAMETER_ERROR


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

        # 创建配置
        config = self.config_repo.create(config_data)
        return self._format_config(config)

    def update_config(
        self, config_id: int, config_data: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """更新LLM配置"""
        # 验证数据
        if config_data:
            self._validate_config_data(config_data, is_update=True)

        # 更新配置
        config = self.config_repo.update(config_id, user_id, config_data)
        return self._format_config(config)

    def delete_config(self, config_id: int, user_id: str) -> bool:
        """删除LLM配置"""
        return self.config_repo.delete(config_id, user_id)

    def set_default_config(self, config_id: int, user_id: str) -> Dict[str, Any]:
        """设置默认LLM配置"""
        config = self.config_repo.set_as_default(config_id, user_id)
        return self._format_config(config)

    def _format_config(self, config) -> Dict[str, Any]:
        """格式化配置数据"""
        result = {
            "id": config.id,
            "name": config.name,
            "provider_type": config.provider_type,
            "api_key": (
                f"***{config.api_key[-4:]}"
                if config.api_key and len(config.api_key) > 4
                else None
            ),
            "api_secret": (
                f"***{config.api_secret[-4:]}"
                if config.api_secret and len(config.api_secret) > 4
                else None
            ),
            "app_id": config.app_id,
            "app_key": (
                f"***{config.app_key[-4:]}"
                if config.app_key and len(config.app_key) > 4
                else None
            ),
            "app_secret": (
                f"***{config.app_secret[-4:]}"
                if config.app_secret and len(config.app_secret) > 4
                else None
            ),
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
        if config.provider_type in ["OpenAI", "Claude"]:
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
            if provider_type == "OpenAI" and not is_update:
                if "api_key" not in data:
                    raise ValidationException(
                        "OpenAI配置必须提供api_key", PARAMETER_ERROR
                    )
            elif provider_type == "Claude" and not is_update:
                if "api_key" not in data:
                    raise ValidationException(
                        "Claude配置必须提供api_key", PARAMETER_ERROR
                    )
            elif provider_type == "Volcano" and not is_update:
                if (
                    "app_id" not in data
                    or "app_key" not in data
                    or "app_secret" not in data
                ):
                    raise ValidationException(
                        "火山引擎配置必须提供app_id、app_key和app_secret",
                        PARAMETER_ERROR,
                    )
            elif provider_type == "Baidu" and not is_update:
                if "app_key" not in data or "app_secret" not in data:
                    raise ValidationException(
                        "百度AI配置必须提供app_key和app_secret", PARAMETER_ERROR
                    )
            elif provider_type == "Aliyun" and not is_update:
                if "app_key" not in data or "app_secret" not in data:
                    raise ValidationException(
                        "阿里云配置必须提供app_key和app_secret", PARAMETER_ERROR
                    )
            elif provider_type == "Tencent" and not is_update:
                if (
                    "app_id" not in data
                    or "app_key" not in data
                    or "app_secret" not in data
                ):
                    raise ValidationException(
                        "腾讯云配置必须提供app_id、app_key和app_secret", PARAMETER_ERROR
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
