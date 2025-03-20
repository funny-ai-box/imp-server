from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.infrastructure.database.base import Base


class Application(Base):
    """应用模型，用于外部系统关联用户和配置"""
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="应用名称")
    app_key = Column(String(64), nullable=False, unique=True, comment="应用唯一标识")
    description = Column(Text, nullable=True, comment="应用描述")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="所属用户ID")
    
    # 关联关系
    user = relationship("User", back_populates="applications")

    def __repr__(self):
        return f"<Application {self.name}>"