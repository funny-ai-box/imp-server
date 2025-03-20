"""认证相关数据模型"""
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.extensions import db

class LoginHistory(db.Model):
    """登录历史模型"""
    __tablename__ = "login_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    login_time = Column(DateTime, default=datetime.utcnow, nullable=False, comment="登录时间")
    ip_address = Column(String(50), nullable=True, comment="IP地址")
    user_agent = Column(String(255), nullable=True, comment="用户代理")
    login_method = Column(String(20), nullable=False, comment="登录方式，如password, code, token")
    is_success = Column(Boolean, default=True, comment="是否登录成功")
    failure_reason = Column(String(100), nullable=True, comment="失败原因")
    
    # 关联关系
    user = relationship("User", back_populates="login_history")
    
    def __repr__(self):
        return f"<LoginHistory {self.user_id} - {self.login_time}>"


# 扩展 User 模型的关联关系
from app.infrastructure.database.models.user import User
User.login_history = relationship("LoginHistory", back_populates="user", cascade="all, delete-orphan")