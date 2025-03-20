# app/infrastructure/database/models/user_llm_config.py
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.extensions import db


class UserLLMConfig(db.Model):
    """用户LLM配置模型"""

    __tablename__ = "user_llm_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, comment="所属用户ID")
    provider_type = Column(
        String(50), nullable=False, comment="提供商类型，如OpenAI, Claude, Volcano"
    )
    name = Column(String(100), nullable=False, comment="配置名称")

    # 鉴权信息
    api_key = Column(Text, nullable=True, comment="API密钥")
    api_secret = Column(Text, nullable=True, comment="API密钥密文")
    app_id = Column(String(100), nullable=True, comment="应用ID")
    app_key = Column(String(100), nullable=True, comment="应用Key")
    app_secret = Column(Text, nullable=True, comment="应用密钥")

    # 服务配置
    api_base_url = Column(String(255), nullable=True, comment="API基础URL(可选)")
    api_version = Column(String(50), nullable=True, comment="API版本(可选)")
    region = Column(String(50), nullable=True, comment="区域设置")

    # 运行配置
    is_default = Column(Boolean, default=False, comment="是否为默认配置")
    is_active = Column(Boolean, default=True, comment="是否启用")
    request_timeout = Column(Integer, default=60, comment="请求超时时间(秒)")
    max_retries = Column(Integer, default=3, comment="最大重试次数")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )
    remark = Column(Text, nullable=True, comment="备注")

    def __repr__(self):
        return f"<UserLLMConfig {self.name} - {self.provider_type}>"
