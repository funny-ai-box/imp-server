"""应用和Token使用数据库模型"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Enum as SQLAEnum,
    ForeignKey, Integer, String, Table, Text, Float, JSON
)
from sqlalchemy.orm import relationship

from app.extensions import db

# 应用状态枚举
class ApplicationStatus(str, Enum):
    ACTIVE = "active"  # 活跃
    INACTIVE = "inactive"  # 非活跃
    DEVELOPMENT = "development"  # 开发中
    ARCHIVED = "archived"  # 已归档

# 应用-模型关联表
application_model = Table(
    'application_model',
    db.Model.metadata,
    Column('application_id', Integer, ForeignKey('applications.id'), primary_key=True),
    Column('model_id', Integer, ForeignKey('models.id'), primary_key=True)
)

# 应用-知识库关联表
application_kb = Table(
    'application_kb',
    db.Model.metadata,
    Column('application_id', Integer, ForeignKey('applications.id'), primary_key=True),
    Column('knowledge_base_id', Integer, ForeignKey('knowledge_bases.id'), primary_key=True)
)

class Application(db.Model):
    """应用模型"""
    __tablename__ = 'applications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    status = Column(SQLAEnum(ApplicationStatus), default=ApplicationStatus.DEVELOPMENT, nullable=False)
    
    # 应用设置
    allowed_domains = Column(String(255))  # 允许的域名，逗号分隔
    allowed_ips = Column(String(255))  # 允许的IP地址，逗号分隔
    logo_url = Column(String(255))  # 应用logo URL
    primary_color = Column(String(20))  # 主颜色
    custom_css = Column(Text)  # 自定义CSS
    custom_js = Column(Text)  # 自定义JavaScript
    
    # 系统相关
    api_key = Column(String(64), unique=True)
    api_secret = Column(String(128))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 配额和限制
    daily_token_limit = Column(Integer, default=50000)
    monthly_token_limit = Column(Integer, default=1500000)
    rate_limit = Column(Integer, default=60)  # 每分钟最大请求数
    
    # 提示词模板
    system_prompt = Column(Text)  # 系统提示词
    prompt_templates = Column(JSON)  # JSON格式的提示词模板
    
    # 配置
    config = Column(JSON)  # 应用配置，JSON格式
    
    # 关系
    users = relationship("User", secondary="user_application", back_populates="applications")
    models = relationship("Model", secondary=application_model, back_populates="applications")
    knowledge_bases = relationship("KnowledgeBase", secondary=application_kb, back_populates="applications")
    usage_records = relationship("TokenUsage", back_populates="application", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Application {self.name}>"
    
    @property
    def is_active(self):
        """应用是否处于活跃状态"""
        return self.status == ApplicationStatus.ACTIVE

class TokenUsage(db.Model):
    """Token使用记录模型"""
    __tablename__ = 'token_usage'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    application_id = Column(Integer, ForeignKey('applications.id'))
    model_id = Column(Integer, ForeignKey('models.id'))
    
    # 使用统计
    prompt_tokens = Column(Integer, default=0)  # 提示词tokens
    completion_tokens = Column(Integer, default=0)  # 补全tokens
    total_tokens = Column(Integer, default=0)  # 总tokens
    
    # 请求信息
    request_id = Column(String(36))  # 请求ID
    request_type = Column(String(20))  # 请求类型：chat, completion, embedding等
    latency = Column(Float)  # 请求延迟（毫秒）
    status_code = Column(Integer)  # 响应状态码
    success = Column(Boolean, default=True)  # 请求是否成功
    error_message = Column(Text)  # 错误信息
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    date = Column(DateTime, nullable=False)  # 记录日期，用于按天统计
    
    # 元数据
    metadata = Column(JSON)  # 额外元数据，JSON格式
    
    # 关系
    user = relationship("User")
    application = relationship("Application", back_populates="usage_records")
    model = relationship("Model", back_populates="usage_records")
    
    def __repr__(self):
        return f"<TokenUsage {self.id} - {self.total_tokens} tokens>"

class DailyUsageSummary(db.Model):
    """每日使用统计摘要"""
    __tablename__ = 'daily_usage_summary'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    application_id = Column(Integer, ForeignKey('applications.id'), nullable=True, index=True)
    model_id = Column(Integer, ForeignKey('models.id'), nullable=True, index=True)
    
    # 统计数据
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    request_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    avg_latency = Column(Float, default=0.0)
    
    # 关系
    user = relationship("User")
    application = relationship("Application")
    model = relationship("Model")
    
    __table_args__ = (
        # 联合唯一约束，确保每天每个组合只有一条记录
        db.UniqueConstraint('date', 'user_id', 'application_id', 'model_id', name='uix_daily_usage'),
    )
    
    def __repr__(self):
        return f"<DailyUsageSummary {self.date} - {self.total_tokens} tokens>"