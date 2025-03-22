# app/infrastructure/database/models/app_template.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from app.extensions import db


class AppTemplate(db.Model):
    """应用模板模型 - 系统预置的应用模板"""

    __tablename__ = "app_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    app_id = Column(String(50), nullable=False, unique=True, comment="应用唯一标识符")
    app_type = Column(String(50), nullable=False, index=True, comment="应用类型分类")
    name = Column(String(100), nullable=False, comment="应用名称")
    version = Column(String(20), nullable=False, default="1.0", comment="应用版本")
    description = Column(Text, nullable=True, comment="应用描述")
    icon = Column(String(255), nullable=True, comment="图标URL")
    capabilities = Column(JSON, nullable=True, comment="功能列表")

    # 应用模板配置结构
    config_template = Column(JSON, nullable=False, comment="配置模板结构")

    # 支持的模型
    supported_models = Column(
        JSON, nullable=True, comment="支持的模型列表，按提供商分类"
    )

    # 示例提示词
    example_prompts = Column(JSON, nullable=True, comment="示例提示词")

    # 系统信息
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    def __repr__(self):
        return f"<AppTemplate {self.name} - {self.app_id} - v{self.version}>"
