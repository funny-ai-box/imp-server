"""用户数据库模型"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Enum as SQLAEnum,
     Integer, String, Table, Text
)

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

    # API相关
    api_key = Column(String(64), unique=True, index=True)
    api_secret = Column(String(128))
    

    
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
