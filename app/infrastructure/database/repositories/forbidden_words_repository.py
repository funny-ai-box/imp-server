# app/infrastructure/database/repositories/forbidden_words_repository.py
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from app.infrastructure.database.models.forbidden_words import ForbiddenWord, ForbiddenWordLog

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
    
    def get_word(self, word_id: int) -> Optional[ForbiddenWord]:
        """获取特定违禁词"""
        return self.db.query(ForbiddenWord).get(word_id)
    
    def add_word(self, word_data: Dict[str, Any]) -> ForbiddenWord:
        """添加违禁词"""
        word = ForbiddenWord(**word_data)
        self.db.add(word)
        self.db.commit()
        self.db.refresh(word)
        return word
    
    def update_word(self, word_id: int, word_data: Dict[str, Any]) -> Optional[ForbiddenWord]:
        """更新违禁词"""
        word = self.get_word(word_id)
        if not word:
            return None
            
        for key, value in word_data.items():
            if hasattr(word, key):
                setattr(word, key, value)
        
        self.db.commit()
        self.db.refresh(word)
        return word
    
    def delete_word(self, word_id: int) -> bool:
        """删除违禁词"""
        word = self.get_word(word_id)
        if not word:
            return False
            
        self.db.delete(word)
        self.db.commit()
        return True
    
    def search_words(self, query: str, application: str) -> List[Dict[str, Any]]:
        """
        搜索违禁词
        
        Args:
            query: 搜索关键词
            application: 应用场景
            
        Returns:
            匹配的违禁词列表
        """
        db_query = self.db.query(ForbiddenWord).filter(
            ForbiddenWord.application == application
        )
        
        # 添加搜索条件
        if query:
            db_query = db_query.filter(ForbiddenWord.word.ilike(f"%{query}%"))
        
        words = db_query.all()
        return [self._format_word(word) for word in words]
    
    def add_log(self, log_data: Dict[str, Any]) -> ForbiddenWordLog:
        """添加检测日志"""
        log = ForbiddenWordLog(**log_data)
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
    
    def get_logs(self, application: str, limit: int = 100) -> List[ForbiddenWordLog]:
        """获取检测日志"""
        return self.db.query(ForbiddenWordLog).filter(
            ForbiddenWordLog.application == application
        ).order_by(
            ForbiddenWordLog.detection_time.desc()
        ).limit(limit).all()
    
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