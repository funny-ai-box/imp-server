from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.infrastructure.database.base import Base


class LLMModel(Base):
    """AI模型模型"""
    __tablename__ = "llm_models"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="模型名称")
    model_id = Column(String(100), nullable=False, comment="模型标识符，如gpt-4-turbo")
    description = Column(Text, nullable=True, comment="模型描述")
    capabilities = Column(Text, nullable=True, comment="模型能力描述")
    context_window = Column(Integer, nullable=True, comment="上下文窗口大小")
    max_tokens = Column(Integer, nullable=True, comment="最大生成令牌数")
    token_price_input = Column(Float, nullable=True, comment="输入令牌价格")
    token_price_output = Column(Float, nullable=True, comment="输出令牌价格")
    is_available = Column(Boolean, default=True, comment="是否可用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    provider_id = Column(Integer, ForeignKey("ai_providers.id"), nullable=False, comment="所属提供商ID")
    
    # 关联关系
    provider = relationship("LLMProvider", back_populates="models")

    def __repr__(self):
        return f"<AIModel {self.name}>"
