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
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )
    user_id = Column(String(32), nullable=False, comment="所属用户ID")

    ip_address = Column(String(50), nullable=True, comment="请求IP")
    user_agent = Column(String(255), nullable=True, comment="用户代理")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    user_id = Column(String(32), nullable=False, comment="所属用户ID")

    # 评价信息
    user_rating = Column(Integer, nullable=True, comment="用户评分(1-5)")
    user_feedback = Column(Text, nullable=True, comment="用户反馈")

    def __repr__(self):
        return f"<XhsCopyGeneration {self.id}>"
