# app/infrastructure/database/models/xhs_copy_app.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Float
from app.extensions import db


class XhsCopyGeneration(db.Model):
    """小红书文案生成记录"""

    __tablename__ = "xhs_copy_generations"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 请求信息
    prompt = Column(Text, nullable=False, comment="用户提供的提示词")
    image_urls = Column(JSON, nullable=True, comment="图片URL列表")
    app_id = Column(Integer, nullable=False, comment="使用的应用ID")
    custom_forbidden_words = Column(JSON, nullable=True, comment="自定义禁用词列表")

    # 生成结果
    title = Column(String(255), nullable=True, comment="生成的标题")
    content = Column(Text, nullable=True, comment="生成的正文")
    tags = Column(JSON, nullable=True, comment="生成的标签列表")
    
    # 禁用词检测结果
    contains_forbidden_words = Column(Boolean, default=False, comment="是否包含禁用词")
    detected_forbidden_words = Column(JSON, nullable=True, comment="检测到的禁用词列表")

    # 执行信息
    status = Column(String(20), default="pending", comment="处理状态")
    error_message = Column(Text, nullable=True, comment="错误信息")
    tokens_used = Column(Integer, default=0, comment="使用的令牌数")
    tokens_prompt = Column(Integer, default=0, comment="提示词使用的令牌数")
    tokens_completion = Column(Integer, default=0, comment="补全使用的令牌数")
    duration_ms = Column(Integer, default=0, comment="处理耗时(毫秒)")

    # 模型信息
    provider_type = Column(String(50), nullable=True, comment="提供商类型(OpenAI/Claude/Volcano等)")
    model_name = Column(String(100), nullable=True, comment="使用的模型名称")
    model_version = Column(String(50), nullable=True, comment="模型版本")
    temperature = Column(Float, nullable=True, comment="使用的温度参数")
    max_tokens = Column(Integer, nullable=True, comment="设置的最大令牌数")
    user_llm_config_id = Column(Integer, nullable=True, comment="使用的LLM配置ID")
    
    # 成本信息
    estimated_cost = Column(Float, default=0.0, comment="估算成本")
    
    # 系统信息
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )
    user_id = Column(String(32), nullable=False, comment="所属用户ID")
    ip_address = Column(String(50), nullable=True, comment="请求IP")
    user_agent = Column(String(255), nullable=True, comment="用户代理")

    # 评价信息
    user_rating = Column(Integer, nullable=True, comment="用户评分(1-5)")
    user_feedback = Column(Text, nullable=True, comment="用户反馈")
    
    # 请求/响应原始数据
    raw_request = Column(JSON, nullable=True, comment="原始请求数据")
    raw_response = Column(JSON, nullable=True, comment="原始响应数据")

    def __repr__(self):
        return f"<XhsCopyGeneration {self.id}>"
