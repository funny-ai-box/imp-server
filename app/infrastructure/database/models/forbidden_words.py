# app/infrastructure/database/models/forbidden_words.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.extensions import db

class ForbiddenWord(db.Model):
    """违禁词模型"""
    __tablename__ = "forbidden_words"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String(255), nullable=False, index=True, comment="违禁词")
    application = Column(String(50), nullable=False, index=True, comment="应用场景，如xiaohongshu, image_classification等")
    description = Column(Text, nullable=True, comment="描述")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建人ID")
    
    # 关联关系
    creator = relationship("User")
    
    def __repr__(self):
        return f"<ForbiddenWord {self.word} - {self.application}>"

class ForbiddenWordLog(db.Model):
    """违禁词检测日志"""
    __tablename__ = "forbidden_word_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_sample = Column(Text, nullable=True, comment="内容样本")
    detected_words = Column(JSON, nullable=False, comment="检测到的违禁词")
    application = Column(String(50), nullable=False, comment="应用场景")
    detection_time = Column(DateTime, default=datetime.utcnow, comment="检测时间")
    
    def __repr__(self):
        return f"<ForbiddenWordLog {self.id}>"