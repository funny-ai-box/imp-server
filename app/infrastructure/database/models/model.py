"""知识库和模型数据库模型"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from sqlalchemy import (
    Boolean, Column, DateTime, Enum as SQLAEnum, Float,
    ForeignKey, Integer, String, Table, Text, JSON
)
from sqlalchemy.orm import relationship

from app.extensions import db
from app.domains.knowledge_management.entities import (
    DocumentStatus, DocumentType, ChunkingStrategy, IndexStatus
)
from app.domains.model_management.entities import ModelType, ModelStatus, ModelProvider

class Model(db.Model):
    """AI模型数据库模型"""
    __tablename__ = 'models'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    type = Column(SQLAEnum(ModelType), nullable=False)
    provider = Column(SQLAEnum(ModelProvider), nullable=False)
    provider_model_id = Column(String(100), nullable=False)
    version = Column(String(50))
    status = Column(SQLAEnum(ModelStatus), default=ModelStatus.ACTIVE, nullable=False)
    
    # 模型属性
    capabilities = Column(JSON)  # 能力列表，JSON格式
    parameters = Column(JSON)  # 参数列表，JSON格式
    max_tokens = Column(Integer, default=4096)
    supports_streaming = Column(Boolean, default=False)
    context_length = Column(Integer, default=4096)
    
    # 系统信息
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    metadata = Column(JSON)  # 元数据，JSON格式
    
    # 统计信息
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    average_latency = Column(Float, default=0.0)
    last_used_at = Column(DateTime)
    
    # 关系
    applications = relationship("Application", secondary="application_model", back_populates="models")
    usage_records = relationship("TokenUsage", back_populates="model")
    
    def __repr__(self):
        return f"<Model {self.name} ({self.provider.value}/{self.provider_model_id})>"
    
    @property
    def is_active(self):
        """模型是否处于活跃状态"""
        return self.status == ModelStatus.ACTIVE
    
    def update_usage_stats(self, successful: bool, input_tokens: int, output_tokens: int, latency: float):
        """更新模型使用统计
        
        Args:
            successful: 请求是否成功
            input_tokens: 输入token数
            output_tokens: 输出token数
            latency: 请求延迟（毫秒）
        """
        self.total_requests += 1
        
        if successful:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += (input_tokens + output_tokens)
        
        # 计算移动平均延迟
        self.average_latency = ((self.average_latency * (self.total_requests - 1)) + latency) / self.total_requests
        
        self.last_used_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
