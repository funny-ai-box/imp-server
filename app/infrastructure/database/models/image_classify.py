# app/infrastructure/database/models/image_classify.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Float
from app.extensions import db


class ImageClassification(db.Model):
    """图片分类记录"""

    __tablename__ = "image_classifications"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 请求信息
    image_url = Column(String(1024), nullable=False, comment="图片URL")
    categories = Column(JSON, nullable=False, comment="分类选项列表")
    app_id = Column(String(32), nullable=False, comment="使用的应用ID")

    # 分类结果
    category_id = Column(String(64), nullable=True, comment="识别的分类ID")
    category_name = Column(String(255), nullable=True, comment="识别的分类名称")
    confidence = Column(Float, nullable=True, comment="识别置信度")
    reasoning = Column(Text, nullable=True, comment="分类推理过程")

    # 执行信息
    status = Column(String(20), default="pending", comment="处理状态")
    error_message = Column(Text, nullable=True, comment="错误信息")
    tokens_used = Column(Integer, default=0, comment="使用的令牌数")
    duration_ms = Column(Integer, default=0, comment="处理耗时(毫秒)")
    provider_type = Column(String(50), nullable=True, comment="提供商类型(OpenAI/Claude/Volcano等)")
    model_id = Column(String(100), nullable=True, comment="使用的模型名称")

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

    def __repr__(self):
        return f"<ImageClassification {self.id}>"