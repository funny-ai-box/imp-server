"""用户数据库模型"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Enum as SQLAEnum,
    ForeignKey, Integer, String, Table, Text
)
from sqlalchemy.orm import relationship

from app.extensions import db

# 用户角色枚举
class UserRole(str, Enum):
    ADMIN = "admin"  # 管理员
    OPERATOR = "operator"  # 运营人员
    DEVELOPER = "developer"  # 开发者
    USER = "user"  # 普通用户

# 用户状态枚举
class UserStatus(str, Enum):
    ACTIVE = "active"  # 活跃
    INACTIVE = "inactive"  # 非活跃
    SUSPENDED = "suspended"  # 已暂停
    PENDING = "pending"  # 待审核

# 用户-应用关联表
user_application = Table(
    'user_application',
    db.Model.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('application_id', Integer, ForeignKey('applications.id'), primary_key=True)
)

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLAEnum(UserRole), default=UserRole.USER, nullable=False)
    status = Column(SQLAEnum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    
    # 个人信息
    full_name = Column(String(100))
    avatar_url = Column(String(255))
    phone = Column(String(20))
    company = Column(String(100))
    title = Column(String(100))
    bio = Column(Text)
    
    # 系统相关
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    reset_password_token = Column(String(100))
    reset_password_expires = Column(DateTime)
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(100))
    
    # API相关
    api_key = Column(String(64), unique=True, index=True)
    api_secret = Column(String(128))
    
    # 配额和限制
    daily_token_limit = Column(Integer, default=10000)
    monthly_token_limit = Column(Integer, default=300000)
    
    # 关系
    applications = relationship("Application", secondary=user_application, back_populates="users")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.username}>"
    
    @property
    def is_active(self):
        """用户是否处于活跃状态"""
        return self.status == UserStatus.ACTIVE
    
    @property
    def is_admin(self):
        """用户是否为管理员"""
        return self.role == UserRole.ADMIN

class APIKey(db.Model):
    """API密钥模型"""
    __tablename__ = 'api_keys'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    key = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime)
    last_used_at = Column(DateTime)
    permissions = Column(String(255))  # 逗号分隔的权限列表
    
    # 关系
    user = relationship("User", back_populates="api_keys")
    
    def __repr__(self):
        return f"<APIKey {self.name}>"
    
    @property
    def is_expired(self):
        """API密钥是否已过期"""
        if not self.expires_at:
            return False
        return self.expires_at < datetime.utcnow()
    
    @property
    def is_valid(self):
        """API密钥是否有效"""
        return self.active and not self.is_expired

