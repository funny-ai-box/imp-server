# app/infrastructure/database/models/forbidden_words.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON

from app.extensions import db

class ForbiddenWord(db.Model):
    """违禁词模型"""
    __tablename__ = "forbidden_words"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String(255), nullable=False, index=True, comment="违禁词")
    application = Column(String(50), nullable=False, index=True, comment="应用场景，如xhs_copy")
    description = Column(Text, nullable=True, comment="描述")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    created_by = Column(Integer, nullable=True, comment="创建人ID")
    

    
    def __repr__(self):
        return f"<ForbiddenWord {self.word} - {self.application}>"

