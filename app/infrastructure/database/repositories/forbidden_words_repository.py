# app/infrastructure/database/repositories/forbidden_words_repository.py
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from app.infrastructure.database.models.forbidden_words import ForbiddenWord

class ForbiddenWordsRepository:
    """违禁词存储库"""
    
    def __init__(self, db_session: Session):
        """初始化存储库"""
        self.db = db_session
    
    def get_all_words(self, application: str) -> List[Dict[str, Any]]:
        """
        获取特定应用的所有违禁词
        
        Args:
            application: 应用场景
            
        Returns:
            违禁词列表
        """
        words = self.db.query(ForbiddenWord).filter(
            ForbiddenWord.application == application
        ).all()
        
        return [self._format_word(word) for word in words]

    
    def _format_word(self, word: ForbiddenWord) -> Dict[str, Any]:
        """格式化违禁词数据"""
        return {
            "id": word.id,
            "word": word.word,
            "application": word.application,
            "description": word.description,
            "created_at": word.created_at.isoformat() if word.created_at else None,
            "updated_at": word.updated_at.isoformat() if word.updated_at else None,
            "created_by": word.created_by
        }