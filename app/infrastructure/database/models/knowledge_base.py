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

class KnowledgeBase(db.Model):
    """知识库数据库模型"""
    __tablename__ = 'knowledge_bases'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # 配置信息
    embedding_model = Column(String(100), default="text-embedding-ada-002")
    embedding_dimension = Column(Integer, default=1536)
    vector_store = Column(String(50), default="pinecone")
    index_name = Column(String(100), unique=True)
    chunking_strategy = Column(SQLAEnum(ChunkingStrategy), default=ChunkingStrategy.PARAGRAPH)
    chunk_size = Column(Integer, default=1000)
    chunk_overlap = Column(Integer, default=200)
    
    # 状态信息
    index_status = Column(SQLAEnum(IndexStatus), default=IndexStatus.CREATING)
    
    # 系统信息
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    metadata = Column(JSON)  # 元数据，JSON格式
    tags = Column(String(255))  # 标签，逗号分隔
    
    # 关系
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")
    applications = relationship("Application", secondary="application_kb", back_populates="knowledge_bases")
    
    def __repr__(self):
        return f"<KnowledgeBase {self.name}>"

class Document(db.Model):
    """文档数据库模型"""
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    knowledge_base_id = Column(Integer, ForeignKey('knowledge_bases.id'), nullable=False)
    type = Column(SQLAEnum(DocumentType), nullable=False)
    status = Column(SQLAEnum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False)
    
    # 文档信息
    content_length = Column(Integer, default=0)
    source_url = Column(String(512))
    file_path = Column(String(512))
    file_size = Column(Integer)
    embedding_model = Column(String(100))
    
    # 处理信息
    error_message = Column(Text)
    
    # 系统信息
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    metadata = Column(JSON)  # 元数据，JSON格式
    
    # 关系
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    chunks = relationship("TextChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document {self.title} ({self.type.value})>"
    
    @property
    def is_processed(self):
        """文档是否已处理完成"""
        return self.status == DocumentStatus.PROCESSED
    
    @property
    def chunk_count(self):
        """文档包含的文本块数量"""
        return len(self.chunks)

class TextChunk(db.Model):
    """文本块数据库模型"""
    __tablename__ = 'text_chunks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    text = Column(Text, nullable=False)
    
    # 块信息
    position = Column(Integer)  # 在文档中的位置
    page_number = Column(Integer)  # 页码（如适用）
    tokens = Column(Integer)  # Token数量
    
    # 向量信息
    embedding_id = Column(String(100))  # 向量存储中的ID
    
    # 系统信息
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata = Column(JSON)  # 元数据，JSON格式
    
    # 关系
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<TextChunk {self.id} - Doc {self.document_id}>"