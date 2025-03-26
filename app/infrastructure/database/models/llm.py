"""LLM提供商模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Float

from app.extensions import db


class LLMProvider(db.Model):
    """AI提供商模型"""
    __tablename__ = "llm_providers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="提供商名称")
    provider_type = Column(String(20), nullable=False, comment="提供商类型，如OpenAI, Claude, Volcano")
    api_key = Column(Text, nullable=False, comment="API密钥")
    api_base_url = Column(String(255), nullable=True, comment="API基础URL(可选)")
    api_version = Column(String(50), nullable=True, comment="API版本(可选)")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
   

    def __repr__(self):
        return f"<LLMProvider {self.name} - {self.provider_type}>"




    
class LLMModel(db.Model):
    """LLM模型模型"""
    __tablename__ = "llm_models"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="模型名称")
    model_id = Column(String(100), nullable=False, comment="模型标识符，如gpt-4-turbo")
    model_type = Column(String(50), nullable=False, comment="模型类型,文本:text, 视觉:visual, 语音:speech")
    description = Column(Text, nullable=True, comment="模型描述")
    capabilities = Column(Text, nullable=True, comment="模型能力描述")
    context_window = Column(Integer, nullable=True, comment="上下文窗口大小")
    max_tokens = Column(Integer, nullable=True, comment="最大生成令牌数")
    token_price_input = Column(Float, nullable=True, comment="输入令牌价格")
    token_price_output = Column(Float, nullable=True, comment="输出令牌价格")
    is_available = Column(Boolean, default=True, comment="是否可用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    provider_id = Column(Integer,  nullable=False, comment="所属提供商ID")

    def __repr__(self):
        return f"<LLMModel {self.name}>"