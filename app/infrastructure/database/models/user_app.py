# app/infrastructure/database/models/user_app.py (修改)
from datetime import datetime
from app.core.security import generate_uuid
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from app.extensions import db


class UserApp(db.Model):
    """用户应用模型 - 用户创建的应用实例和配置"""

    __tablename__ = "user_apps"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), nullable=False, comment="所属用户ID")
    app_id = Column(String(32), nullable=False, comment="应用唯一标识符")
    app_type = Column(String(50), nullable=False, comment="应用类型，如xhs_copy")
    name = Column(String(100), nullable=False, comment="应用名称")
    description = Column(Text, nullable=True, comment="应用描述")

    # 添加明确的模板引用（可选，如果想直接关联模板ID）
    template_id = Column(Integer, nullable=True, comment="应用模板ID")

    # 应用配置 - 使用JSON存储所有特定应用类型的配置参数
    config = Column(JSON, nullable=True, comment="应用配置")

    # 应用密钥和状态
    app_key = Column(String(64), nullable=False, unique=True, comment="应用唯一标识")
    published = Column(Boolean, default=False, comment="是否已发布")
    published_config = Column(JSON, nullable=True, comment="已发布的配置")
    is_default = Column(Boolean, default=False, comment="是否为默认应用")

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )

    def __repr__(self):
        return f"<UserApp {self.name} - {self.app_type}>"