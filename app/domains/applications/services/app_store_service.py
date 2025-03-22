# app/domains/applications/services/app_store_service.py
from typing import List, Dict, Any, Optional
from app.infrastructure.database.repositories.app_template_repository import (
    AppTemplateRepository,
)
from app.core.exceptions import ValidationException, NotFoundException
from app.core.status_codes import PARAMETER_ERROR, APPLICATION_NOT_FOUND


class AppStoreService:
    """应用商店服务"""

    def __init__(self, app_template_repository: AppTemplateRepository):
        """初始化服务"""
        self.app_template_repo = app_template_repository

    def get_all_templates(self) -> List[Dict[str, Any]]:
        """获取所有应用模板"""
        templates = self.app_template_repo.get_all_active()
        return [self._format_template(template) for template in templates]

    def get_template_by_app_id(self, app_id: str) -> Dict[str, Any]:
        """根据应用ID获取应用模板"""
        template = self.app_template_repo.get_by_app_id(app_id)
        return self._format_template(template)

    def get_template_by_type(self, app_type: str) -> Dict[str, Any]:
        """根据类型获取应用模板"""
        template = self.app_template_repo.get_by_type(app_type)
        return self._format_template(template)

    def get_template_by_id(self, template_id: int) -> Dict[str, Any]:
        """根据ID获取应用模板"""
        template = self.app_template_repo.get_by_id(template_id)
        return self._format_template(template)

    def _format_template(self, template) -> Dict[str, Any]:
        """格式化应用模板数据"""
        return {
            "id": template.id,
            "app_type": template.app_type,
            "name": template.name,
            "description": template.description,
            "icon": template.icon,
            "capabilities": template.capabilities,
            "config_template": template.config_template,
            "supported_models": template.supported_models,
            "example_prompts": template.example_prompts,
            "is_active": template.is_active,
            "created_at": (
                template.created_at.isoformat() if template.created_at else None
            ),
            "updated_at": (
                template.updated_at.isoformat() if template.updated_at else None
            ),
        }

    # 以下方法仅供管理员使用
    def create_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建新应用模板"""
        # 验证数据
        self._validate_template_data(template_data)

        # 创建模板
        template = self.app_template_repo.create(template_data)
        return self._format_template(template)

    def update_template(
        self, template_id: int, template_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新应用模板"""
        # 验证数据
        if template_data:
            self._validate_template_data(template_data, is_update=True)

        # 更新模板
        template = self.app_template_repo.update(template_id, template_data)
        return self._format_template(template)

    def delete_template(self, template_id: int) -> bool:
        """删除应用模板"""
        return self.app_template_repo.delete(template_id)

    def _validate_template_data(
        self, data: Dict[str, Any], is_update: bool = False
    ) -> None:
        """验证模板数据"""
        if not is_update:
            # 必填字段验证
            required_fields = ["app_type", "name", "config_template"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                raise ValidationException(
                    f"缺少必填字段: {', '.join(missing_fields)}", PARAMETER_ERROR
                )

            # 验证app_type唯一性
            try:
                self.app_template_repo.get_by_type(data["app_type"])
                raise ValidationException(
                    f"应用类型 {data['app_type']} 已存在", PARAMETER_ERROR
                )
            except NotFoundException:
                # 未找到表示可以创建
                pass

        # 验证config_template结构
        if "config_template" in data:
            config_template = data["config_template"]
            if not isinstance(config_template, dict):
                raise ValidationException(
                    "config_template必须是字典类型", PARAMETER_ERROR
                )
