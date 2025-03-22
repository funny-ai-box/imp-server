# app/domains/applications/services/user_app_service.py
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import logging
import json

from app.core.exceptions import ValidationException, NotFoundException
from app.core.status_codes import PARAMETER_ERROR, APPLICATION_NOT_FOUND
from app.infrastructure.database.repositories.app_template_repository import (
    AppTemplateRepository,
)
from app.infrastructure.database.repositories.user_app_repository import (
    UserAppRepository,
)
from app.infrastructure.database.repositories.user_llm_config_repository import (
    UserLLMConfigRepository,
)

logger = logging.getLogger(__name__)


class UserAppService:
    """用户应用服务"""

    def __init__(
        self,
        user_app_repository: UserAppRepository,
        app_template_repository: Optional[AppTemplateRepository] = None,
        user_llm_config_repository: Optional[UserLLMConfigRepository] = None,
    ):
        """初始化服务"""
        self.user_app_repo = user_app_repository
        self.app_template_repo = app_template_repository
        self.user_llm_config_repo = user_llm_config_repository

    def instantiate_from_template(
        self, template_id: int, user_id: str, custom_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """从应用模板实例化用户应用

        Args:
            template_id: 应用模板ID
            user_id: 用户ID
            custom_config: 用户自定义配置（可选）

        Returns:
            创建的应用实例
        """
        if not self.app_template_repo:
            raise ValidationException(
                "不支持从模板实例化，缺少应用模板存储库", PARAMETER_ERROR
            )

        # 获取应用模板
        template = self.app_template_repo.get_by_id(template_id)

        # 创建应用数据
        app_data = {
            "user_id": user_id,
            "app_type": template.app_type,
            "name": template.name,
            "description": template.description,
            "template_id": template.id,
            "app_key": self._generate_app_key(),
            "created_at": datetime.utcnow(),
        }

        # 合并默认配置和自定义配置
        config = template.config_template.copy() if template.config_template else {}
        if custom_config:
            config.update(custom_config)
        app_data["config"] = config

        # 检查是否是第一个同类型应用，如果是，设为默认
        existing_apps = self.user_app_repo.get_all_by_type(user_id, template.app_type)
        if not existing_apps:
            app_data["is_default"] = True

        # 创建应用
        app = self.user_app_repo.create(app_data)
        return self._format_app(app)

    def get_all_apps(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户所有应用"""
        apps = self.user_app_repo.get_all_by_user(user_id)
        return [self._format_app(app) for app in apps]

    def get_app(self, app_id: int, user_id: str) -> Dict[str, Any]:
        """获取用户特定应用"""
        app = self.user_app_repo.get_by_id(app_id, user_id)
        return self._format_app(app)

    def get_app_by_key(self, app_key: str) -> Optional[Dict[str, Any]]:
        """根据应用密钥获取应用"""
        app = self.user_app_repo.get_by_app_key(app_key)
        if not app:
            return None
        return self._format_app(app)

    def get_apps_by_type(self, user_id: str, app_type: str) -> List[Dict[str, Any]]:
        """获取用户特定类型的所有应用"""
        apps = self.user_app_repo.get_all_by_type(user_id, app_type)
        return [self._format_app(app) for app in apps]

    def get_default_app(self, user_id: str, app_type: str) -> Optional[Dict[str, Any]]:
        """获取用户特定类型的默认应用"""
        app = self.user_app_repo.get_default_by_type(user_id, app_type)
        if not app:
            return None
        return self._format_app(app)

    def add_app(self, app_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """添加应用到用户列表"""
        # 验证数据
        self._validate_app_data(app_data)

        # 验证LLM配置
        if (
            "user_llm_config_id" in app_data
            and app_data["user_llm_config_id"]
            and self.user_llm_config_repo
        ):
            try:
                llm_config = self.user_llm_config_repo.get_by_id(
                    app_data["user_llm_config_id"], user_id
                )
                # 验证LLM配置是否有效
                if not llm_config.is_active:
                    raise ValidationException("选择的LLM配置未激活", PARAMETER_ERROR)
            except Exception as e:
                logger.error(f"LLM config validation error: {str(e)}")
                raise ValidationException(
                    f"指定的LLM配置无效: {str(e)}", PARAMETER_ERROR
                )

        # 设置用户ID和创建时间
        app_data["user_id"] = user_id
        app_data["created_at"] = datetime.utcnow()

        # 生成应用密钥
        app_data["app_key"] = self._generate_app_key()

        # 设置初始状态
        app_data["published"] = False
        app_data["published_config"] = None

        # 检查是否是第一个同类型应用，如果是，设为默认
        app_type = app_data.get("app_type")
        if app_type:
            existing_apps = self.user_app_repo.get_all_by_type(user_id, app_type)
            if not existing_apps:
                app_data["is_default"] = True

        # 创建应用
        app = self.user_app_repo.create(app_data)
        return self._format_app(app)

    def update_app(
        self, app_id: int, app_data: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """更新用户应用配置"""
        # 获取当前应用
        app = self.user_app_repo.get_by_id(app_id, user_id)

        # 验证数据
        if app_data:
            self._validate_app_data(app_data, is_update=True)

        # 验证LLM配置
        if (
            "user_llm_config_id" in app_data
            and app_data["user_llm_config_id"]
            and self.user_llm_config_repo
        ):
            try:
                llm_config = self.user_llm_config_repo.get_by_id(
                    app_data["user_llm_config_id"], user_id
                )
                # 验证LLM配置是否有效
                if not llm_config.is_active:
                    raise ValidationException("选择的LLM配置未激活", PARAMETER_ERROR)
            except NotFoundException:
                raise ValidationException(
                    "指定的LLM配置不存在或不属于当前用户", PARAMETER_ERROR
                )
            except Exception as e:
                raise ValidationException(
                    f"指定的LLM配置无效: {str(e)}", PARAMETER_ERROR
                )

        # 禁止更新用户ID、应用密钥和发布状态
        if "user_id" in app_data:
            del app_data["user_id"]
        if "app_key" in app_data:
            del app_data["app_key"]
        if "published" in app_data:
            del app_data["published"]
        if "published_config" in app_data:
            del app_data["published_config"]

        # 更新应用
        app_data["updated_at"] = datetime.utcnow()
        app = self.user_app_repo.update(app_id, user_id, app_data)
        return self._format_app(app)

    def publish_app(self, app_id: int, user_id: str) -> Dict[str, Any]:
        """发布应用配置"""
        # 获取当前应用
        app = self.user_app_repo.get_by_id(app_id, user_id)

        # 验证应用配置中包含必要的大模型设置
        if not app.config:
            raise ValidationException("应用配置不能为空", PARAMETER_ERROR)

        # 如果有关联的LLM配置，验证该配置是否有效
        user_llm_config_id = app.user_llm_config_id
        if user_llm_config_id and self.user_llm_config_repo:
            try:
                user_llm_config = self.user_llm_config_repo.get_by_id(
                    user_llm_config_id, user_id
                )
                if not user_llm_config.is_active:
                    raise ValidationException(
                        "关联的LLM配置未激活，无法发布", PARAMETER_ERROR
                    )
            except NotFoundException:
                raise ValidationException(
                    "关联的LLM配置不存在，无法发布", PARAMETER_ERROR
                )
        else:
            raise ValidationException("未关联LLM配置，无法发布", PARAMETER_ERROR)

        # 根据应用类型验证必要配置
        self._validate_app_config_by_type(app.app_type, app.config)

        # 保存当前配置作为发布配置
        published_config = {
            "app_type": app.app_type,
            "name": app.name,
            "description": app.description,
            "config": app.config,
            "user_llm_config_id": app.user_llm_config_id,
            "published_at": datetime.utcnow().isoformat(),
        }

        # 更新发布状态和配置
        update_data = {
            "published": True,
            "published_config": published_config,
            "updated_at": datetime.utcnow(),
        }

        app = self.user_app_repo.update(app_id, user_id, update_data)
        return self._format_app(app)

    def unpublish_app(self, app_id: int, user_id: str) -> Dict[str, Any]:
        """取消发布应用"""
        # 更新发布状态
        update_data = {"published": False, "updated_at": datetime.utcnow()}

        app = self.user_app_repo.update(app_id, user_id, update_data)
        return self._format_app(app)

    def delete_app(self, app_id: int, user_id: str) -> bool:
        """从用户列表删除应用"""
        # 获取应用信息，用于处理默认应用的转移
        app = self.user_app_repo.get_by_id(app_id, user_id)

        # 如果是默认应用，尝试将同类型的另一个应用设为默认
        if app.is_default:
            other_apps = self.user_app_repo.get_all_by_type(user_id, app.app_type)
            other_apps = [a for a in other_apps if a.id != app_id]
            if other_apps:
                self.user_app_repo.set_as_default(other_apps[0].id, user_id)

        return self.user_app_repo.delete(app_id, user_id)

    def set_default_app(self, app_id: int, user_id: str) -> Dict[str, Any]:
        """设置默认应用"""
        app = self.user_app_repo.set_as_default(app_id, user_id)
        return self._format_app(app)

    def regenerate_app_key(self, app_id: int, user_id: str) -> Dict[str, Any]:
        """重新生成应用密钥"""
        # 生成新密钥
        new_key = self._generate_app_key()

        # 更新应用
        update_data = {"app_key": new_key, "updated_at": datetime.utcnow()}

        app = self.user_app_repo.update(app_id, user_id, update_data)
        return self._format_app(app)

    def _validate_app_data(self, data: Dict[str, Any], is_update: bool = False) -> None:
        """验证应用数据"""
        if not is_update:
            # 必填字段验证
            required_fields = ["name", "app_type"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                raise ValidationException(
                    f"缺少必填字段: {', '.join(missing_fields)}", PARAMETER_ERROR
                )

        # 应用类型验证
        if "app_type" in data:
            valid_types = ["xhs_copy"]  # 后续可以添加更多支持的类型
            if data["app_type"] not in valid_types:
                raise ValidationException(
                    f"无效的应用类型: {data['app_type']}，有效类型: {', '.join(valid_types)}",
                    PARAMETER_ERROR,
                )

        # 如果包含配置数据，验证配置
        if "config" in data and data["config"]:
            app_type = data.get("app_type")
            if not app_type and is_update:
                # 更新操作中可能没有app_type，此时需要从数据库获取
                # 这种情况在实际使用时需要特殊处理
                pass
            elif app_type:
                self._validate_app_config_by_type(app_type, data["config"])

    def _validate_app_config_by_type(
        self, app_type: str, config: Dict[str, Any]
    ) -> None:
        """根据应用类型验证配置"""
        if app_type == "xhs_copy":
            # 验证小红书文案生成应用配置
            self._validate_xhs_copy_config(config)

    def _validate_xhs_copy_config(self, config: Dict[str, Any]) -> None:
        """验证小红书文案生成应用配置"""
        # 验证必要字段
        required_fields = ["system_prompt", "user_prompt_template"]
        missing_fields = [field for field in required_fields if field not in config]

        if missing_fields:
            raise ValidationException(
                f"缺少必要的配置字段: {', '.join(missing_fields)}", PARAMETER_ERROR
            )

        # 验证温度参数
        if "temperature" in config:
            temp = config["temperature"]
            if not isinstance(temp, (int, float)) or temp < 0 or temp > 1:
                raise ValidationException("temperature必须在0-1之间", PARAMETER_ERROR)

        # 验证令牌数
        if "max_tokens" in config:
            tokens = config["max_tokens"]
            if not isinstance(tokens, int) or tokens < 100 or tokens > 4000:
                raise ValidationException(
                    "max_tokens必须在100-4000之间", PARAMETER_ERROR
                )

        # 验证标题长度
        if "title_length" in config:
            length = config["title_length"]
            if not isinstance(length, int) or length < 10 or length > 100:
                raise ValidationException(
                    "title_length必须在10-100之间", PARAMETER_ERROR
                )

        # 验证内容长度
        if "content_length" in config:
            length = config["content_length"]
            if not isinstance(length, int) or length < 100 or length > 2000:
                raise ValidationException(
                    "content_length必须在100-2000之间", PARAMETER_ERROR
                )

    def _generate_app_key(self) -> str:
        """生成应用密钥"""
        return str(uuid.uuid4()).replace("-", "")

    def _format_app(self, app) -> Dict[str, Any]:
        """格式化应用数据"""
        result = {
            "id": app.id,
            "name": app.name,
            "app_type": app.app_type,
            "description": app.description,
            "config": app.config,
            "user_llm_config_id": app.user_llm_config_id,
            "app_key": app.app_key,
            "published": app.published,
            "is_default": app.is_default,
            "created_at": app.created_at.isoformat() if app.created_at else None,
            "updated_at": app.updated_at.isoformat() if app.updated_at else None,
        }

        # 添加发布配置信息
        if app.published and app.published_config:
            result["published_config"] = app.published_config
            # 添加发布日期
            if "published_at" in app.published_config:
                result["published_at"] = app.published_config["published_at"]

        # 添加LLM配置名称（如果可用）
        if app.user_llm_config_id and self.user_llm_config_repo:
            try:
                llm_config = self.user_llm_config_repo.get_by_id(
                    app.user_llm_config_id, app.user_id
                )
                result["llm_config_name"] = llm_config.name
                result["llm_provider_type"] = llm_config.provider_type
            except Exception as e:
                logger.error(f"Error fetching LLM config details: {str(e)}")

        return result
