from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from app.extensions import db

class UserApp(db.Model):
    """用户应用模型"""
    __tablename__ = "user_apps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, comment="所属用户ID")
    app_type = Column(String(50), nullable=False, comment="应用类型，如xhs_copy")
    name = Column(String(100), nullable=False, comment="应用名称")
    description = Column(Text, nullable=True, comment="应用描述")
    config = Column(JSON, nullable=True, comment="应用配置") 
    app_key = Column(String(64), nullable=False, unique=True, comment="应用唯一标识")
    published = Column(Boolean, default=False, comment="是否已发布")
    published_config = Column(JSON, nullable=True, comment="已发布的配置")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    def __repr__(self):
        return f"<UserApp {self.name} - {self.app_type}>"