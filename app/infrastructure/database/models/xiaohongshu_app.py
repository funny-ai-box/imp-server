# app/infrastructure/database/models/xiaohongshu_app.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from app.extensions import db

class XiaohongshuAppConfig(db.Model):
    """小红书文案生成应用配置"""
    __tablename__ = "xiaohongshu_app_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="配置名称")
    description = Column(Text, nullable=True, comment="配置描述")
    
    # 模型配置
    provider_id = Column(Integer, ForeignKey("ai_providers.id"), nullable=False, comment="使用的AI提供商ID")
    model_id = Column(Integer, ForeignKey("ai_models.id"), nullable=False, comment="使用的AI模型ID")
    
    # 生成配置
    system_prompt = Column(Text, nullable=True, comment="系统提示词")
    user_prompt_template = Column(Text, nullable=False, comment="用户提示词模板")
    temperature = Column(Float, default=0.7, comment="温度参数")
    max_tokens = Column(Integer, default=2000, comment="最大生成令牌数")
    
    # 内容配置
    title_length = Column(Integer, default=50, comment="标题最大长度")
    content_length = Column(Integer, default=1000, comment="内容最大长度")
    tags_count = Column(Integer, default=5, comment="生成标签数量")
    include_emojis = Column(Boolean, default=True, comment="是否包含表情符号")
    
    # 其他配置
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_default = Column(Boolean, default=False, comment="是否为默认配置")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="所属用户ID")
    
    # 关联关系
    user = relationship("User", back_populates="xiaohongshu_configs")
    provider = relationship("AIProvider")
    model = relationship("AIModel")
    generations = relationship("XiaohongshuGeneration", back_populates="config")

    def __repr__(self):
        return f"<XiaohongshuAppConfig {self.name}>"


class XiaohongshuGeneration(db.Model):
    """小红书文案生成记录"""
    __tablename__ = "xiaohongshu_generations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 请求信息
    prompt = Column(Text, nullable=False, comment="用户提供的提示词")
    image_urls = Column(JSON, nullable=True, comment="图片URL列表")
    config_id = Column(Integer, ForeignKey("xiaohongshu_app_configs.id"), nullable=False, comment="使用的配置ID")
    app_id = Column(Integer, ForeignKey("applications.id"), nullable=True, comment="调用的应用ID")
    
    # 生成结果
    title = Column(String(255), nullable=True, comment="生成的标题")
    content = Column(Text, nullable=True, comment="生成的正文")
    tags = Column(JSON, nullable=True, comment="生成的标签列表")
    
    # 执行信息
    status = Column(String(20), default="pending", comment="处理状态")
    error_message = Column(Text, nullable=True, comment="错误信息")
    tokens_used = Column(Integer, default=0, comment="使用的令牌数")
    duration_ms = Column(Integer, default=0, comment="处理耗时(毫秒)")
    
    # 系统信息
    ip_address = Column(String(50), nullable=True, comment="请求IP")
    user_agent = Column(String(255), nullable=True, comment="用户代理")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="所属用户ID")
    
    # 评价信息
    user_rating = Column(Integer, nullable=True, comment="用户评分(1-5)")
    user_feedback = Column(Text, nullable=True, comment="用户反馈")
    
    # 关联关系
    user = relationship("User")
    config = relationship("XiaohongshuAppConfig", back_populates="generations")
    application = relationship("Application")

    def __repr__(self):
        return f"<XiaohongshuGeneration {self.id}>"


class XiaohongshuTestResult(db.Model):
    """小红书文案测试结果"""
    __tablename__ = "xiaohongshu_test_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 测试信息
    test_name = Column(String(100), nullable=False, comment="测试名称")
    prompt = Column(Text, nullable=False, comment="用户提供的提示词")
    image_urls = Column(JSON, nullable=True, comment="图片URL列表")
    
    # 配置信息
    config_ids = Column(JSON, nullable=False, comment="测试的配置ID列表")
    
    # 结果信息
    results = Column(JSON, nullable=True, comment="测试结果JSON")
    winner_config_id = Column(Integer, nullable=True, comment="获胜的配置ID")
    
    # 系统信息
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="所属用户ID")
    
    # 关联关系
    user = relationship("User")

    def __repr__(self):
        return f"<XiaohongshuTestResult {self.test_name}>"