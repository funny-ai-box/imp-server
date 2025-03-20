"""LLM提供商模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="所属用户ID")
    
    # 关联关系
    user = relationship("User", back_populates="llm_providers")
    models = relationship("LLMModel", back_populates="provider", cascade="all, delete-orphan")
    audit_logs = relationship("LLMAuditLog", back_populates="provider")

    def __repr__(self):
        return f"<LLMProvider {self.name} - {self.provider_type}>"



class LLMAuditLog(db.Model):
    """LLM审计日志模型，记录LLM调用情况"""
    __tablename__ = "llm_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 关联信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    provider_id = Column(Integer, ForeignKey("llm_providers.id"), nullable=False, comment="提供商ID")
    model_id = Column(Integer, ForeignKey("llm_models.id"), nullable=False, comment="模型ID")
    app_id = Column(Integer, ForeignKey("applications.id"), nullable=True, comment="应用ID")
    
    # 请求信息
    request_type = Column(String(50), nullable=False, comment="请求类型，如chat, completion, embedding")
    prompt = Column(Text, nullable=True, comment="提示词")
    parameters = Column(JSON, nullable=True, comment="请求参数")
    
    # 响应信息
    response = Column(Text, nullable=True, comment="响应内容")
    tokens_used = Column(Integer, default=0, comment="使用的令牌数")
    tokens_prompt = Column(Integer, default=0, comment="提示词的令牌数")
    tokens_completion = Column(Integer, default=0, comment="补全的令牌数")
    
    # 性能信息
    latency_ms = Column(Integer, default=0, comment="延迟(毫秒)")
    status = Column(String(20), default="success", comment="状态，如success, error")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 计费信息
    estimated_cost = Column(Float, default=0.0, comment="估计成本")
    
    # 系统信息
    ip_address = Column(String(50), nullable=True, comment="IP地址")
    user_agent = Column(String(255), nullable=True, comment="用户代理")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    # 关联关系
    user = relationship("User", back_populates="llm_audit_logs")
    provider = relationship("LLMProvider", back_populates="audit_logs")
    model = relationship("LLMModel", back_populates="audit_logs")
    application = relationship("Application", back_populates="llm_audit_logs")

    def __repr__(self):
        return f"<LLMAuditLog {self.id}>"
    
class LLMModel(db.Model):
    """LLM模型模型"""
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
    provider_id = Column(Integer, ForeignKey("llm_providers.id"), nullable=False, comment="所属提供商ID")
    
    # 关联关系
    provider = relationship("LLMProvider", back_populates="models")
    audit_logs = relationship("LLMAuditLog", back_populates="model")

    def __repr__(self):
        return f"<LLMModel {self.name}>"