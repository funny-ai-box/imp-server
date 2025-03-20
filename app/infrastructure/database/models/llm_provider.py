# app/infrastructure/database/models/ai_provider.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.extensions import db


class AIProvider(db.Model):
    """AI提供商模型"""
    __tablename__ = "ai_providers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="提供商名称")
    provider_type = Column(String(20), nullable=False, comment="提供商类型，如OpenAI, Claude, Volcano")
    api_key = Column(Text, nullable=False, comment="API密钥")
    api_base_url = Column(String(255), nullable=True, comment="API基础URL(可选)")
    api_version = Column(String(50), nullable=True, comment="API版本(可选)")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="所属用户ID")
    
    # 关联关系
    user = relationship("User", back_populates="ai_providers")
    models = relationship("AIModel", back_populates="provider", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AIProvider {self.name} - {self.provider_type}>"


# app/infrastructure/database/models/user.py (添加关系)
# 在现有的User模型中添加以下关系
ai_providers = relationship("AIProvider", back_populates="user", cascade="all, delete-orphan")