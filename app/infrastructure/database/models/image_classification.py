# app/infrastructure/database/models/image_classification.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Float

from app.extensions import db

class ImageClassificationConfig(db.Model):
    """图片分类应用配置"""
    __tablename__ = "image_classification_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="配置名称")
    description = Column(Text, nullable=True, comment="配置描述")
    
    # 模型配置
    provider_id = Column(Integer, nullable=False, comment="使用的AI提供商ID")
    model_id = Column(Integer, nullable=False, comment="使用的AI模型ID")
    
    # 分类配置
    confidence_threshold = Column(Float, default=0.7, comment="置信度阈值")
    system_prompt = Column(Text, nullable=True, comment="系统提示词")
    user_prompt_template = Column(Text, nullable=False, comment="用户提示词模板")
    temperature = Column(Float, default=0.3, comment="温度参数")
    max_tokens = Column(Integer, default=500, comment="最大生成令牌数")
    
    # 其他配置
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_default = Column(Boolean, default=False, comment="是否为默认配置")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    user_id = Column(Integer, nullable=False, comment="所属用户ID")
    


    def __repr__(self):
        return f"<ImageClassificationConfig {self.name}>"


class ImageClassification(db.Model):
    """图片分类记录"""
    __tablename__ = "image_classifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 请求信息
    image_url = Column(String(512), nullable=False, comment="图片URL")
    categories = Column(JSON, nullable=False, comment="分类类别数组")
    config_id = Column(Integer,  nullable=False, comment="使用的配置ID")
    app_id = Column(Integer,  nullable=True, comment="调用的应用ID")
    
    # 分类结果
    result_category_id = Column(String(100), nullable=True, comment="结果分类ID")
    result_category_name = Column(String(100), nullable=True, comment="结果分类名称")
    confidence = Column(Float, nullable=True, comment="置信度")
    all_results = Column(JSON, nullable=True, comment="所有分类结果及置信度")
    
    # 执行信息
    status = Column(String(20), default="pending", comment="处理状态")
    error_message = Column(Text, nullable=True, comment="错误信息")
    tokens_used = Column(Integer, default=0, comment="使用的令牌数")
    duration_ms = Column(Integer, default=0, comment="处理耗时(毫秒)")
    
    # 系统信息
    ip_address = Column(String(50), nullable=True, comment="请求IP")
    user_agent = Column(String(255), nullable=True, comment="用户代理")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    user_id = Column(Integer, nullable=False, comment="所属用户ID")
    
    # 评价信息
    user_rating = Column(Integer, nullable=True, comment="用户评分(1-5)")
    user_feedback = Column(Text, nullable=True, comment="用户反馈")
    

    def __repr__(self):
        return f"<ImageClassification {self.id}>"