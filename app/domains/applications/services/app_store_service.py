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

    def get_template_by_id(self, template_id: str) -> Dict[str, Any]:
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

