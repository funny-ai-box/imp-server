# app/domains/content_management/services/forbidden_words_service.py
from typing import List, Dict, Any, Optional, Tuple
import re
import logging
from datetime import datetime

from app.infrastructure.database.repositories.forbidden_words_repository import ForbiddenWordsRepository
from app.core.exceptions import ValidationException, NotFoundException
from app.core.status_codes import CONTENT_FILTER_BLOCKED, NOT_FOUND

logger = logging.getLogger(__name__)

class ForbiddenWordsService:
    """违禁词服务"""
    
    def __init__(self, forbidden_words_repository: ForbiddenWordsRepository):
        """初始化服务"""
        self.repository = forbidden_words_repository
        self._cache = {}
        self._cache_time = {}
        self._cache_duration = 300  # 缓存5分钟
    
    def check_content(self, content: str, application: str) -> Tuple[bool, List[str]]:
        """
        检查内容是否包含违禁词
        
        Args:
            content: 要检查的内容
            application: 应用场景
            
        Returns:
            (是否通过, 违禁词列表)
        """
        if not content:
            return True, []
            
        # 获取违禁词列表
        words = self._get_forbidden_words(application)
        
        # 检测到的违禁词
        detected_words = []
        
        # 简单匹配
        content_lower = content.lower()
        for word_info in words:
            word = word_info["word"].lower()
            if word in content_lower:
                detected_words.append(word)
        
        return len(detected_words) == 0, detected_words
    
    def validate_content(self, content: str, application: str, error_message: str = "内容包含违禁词") -> None:
        """
        验证内容是否包含违禁词，包含则抛出异常
        
        Args:
            content: 要验证的内容
            application: 应用场景
            error_message: 错误消息
            
        Raises:
            ValidationException: 内容包含违禁词
        """
        passed, detected_words = self.check_content(content, application)
        if not passed:
            # 记录违禁词检测
            self._log_detection(content, detected_words, application)
            # 抛出异常
            raise ValidationException(
                f"{error_message}: {', '.join(detected_words)}", 
                CONTENT_FILTER_BLOCKED
            )
    
    def get_all_words(self, application: str) -> List[Dict[str, Any]]:
        """
        获取特定应用的所有违禁词
        
        Args:
            application: 应用场景
            
        Returns:
            违禁词列表
        """
        return self._get_forbidden_words(application)
    
    def get_word(self, word_id: int) -> Dict[str, Any]:
        """
        获取特定违禁词
        
        Args:
            word_id: 违禁词ID
            
        Returns:
            违禁词信息
        """
        word = self.repository.get_word(word_id)
        if not word:
            raise NotFoundException(f"未找到ID为{word_id}的违禁词", NOT_FOUND)
        
        return self.repository._format_word(word)
    
    def add_word(self, word_data: Dict[str, Any], admin_id: int) -> Dict[str, Any]:
        """
        添加违禁词
        
        Args:
            word_data: 违禁词数据
            admin_id: 管理员ID
            
        Returns:
            添加的违禁词
        """
        # 验证必要字段
        if "word" not in word_data:
            raise ValidationException("违禁词不能为空")
        
        if "application" not in word_data:
            raise ValidationException("应用场景不能为空")
        
        # 设置创建人
        word_data["created_by"] = admin_id
        
        # 添加违禁词
        word = self.repository.add_word(word_data)
        
        # 清除缓存
        if word.application in self._cache:
            del self._cache[word.application]
            del self._cache_time[word.application]
        
        return self.repository._format_word(word)
    
    def update_word(self, word_id: int, word_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新违禁词
        
        Args:
            word_id: 违禁词ID
            word_data: 违禁词数据
            
        Returns:
            更新后的违禁词
        """
        # 获取违禁词
        word = self.repository.get_word(word_id)
        if not word:
            raise NotFoundException(f"未找到ID为{word_id}的违禁词", NOT_FOUND)
        
        # 禁止修改应用场景
        if "application" in word_data:
            del word_data["application"]
        
        # 更新违禁词
        updated_word = self.repository.update_word(word_id, word_data)
        
        # 清除缓存
        if updated_word.application in self._cache:
            del self._cache[updated_word.application]
            del self._cache_time[updated_word.application]
        
        return self.repository._format_word(updated_word)
    
    def delete_word(self, word_id: int) -> bool:
        """
        删除违禁词
        
        Args:
            word_id: 违禁词ID
            
        Returns:
            操作是否成功
        """
        # 获取违禁词
        word = self.repository.get_word(word_id)
        if not word:
            raise NotFoundException(f"未找到ID为{word_id}的违禁词", NOT_FOUND)
        
        application = word.application
        
        # 删除违禁词
        result = self.repository.delete_word(word_id)
        
        # 清除缓存
        if application in self._cache:
            del self._cache[application]
            del self._cache_time[application]
        
        return result
    
    def search_words(self, query: str, application: str) -> List[Dict[str, Any]]:
        """
        搜索违禁词
        
        Args:
            query: 搜索关键词
            application: 应用场景
            
        Returns:
            匹配的违禁词列表
        """
        return self.repository.search_words(query, application)
    
    def get_logs(self, application: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取检测日志
        
        Args:
            application: 应用场景
            limit: 限制条数
            
        Returns:
            检测日志列表
        """
        logs = self.repository.get_logs(application, limit)
        return [
            {
                "id": log.id,
                "content_sample": log.content_sample,
                "detected_words": log.detected_words,
                "application": log.application,
                "detection_time": log.detection_time.isoformat() if log.detection_time else None
            }
            for log in logs
        ]
    
    def get_prompt_for_ai(self, application: str) -> str:
        """
        获取给AI的提示词，告知违禁词列表
        
        Args:
            application: 应用场景
            
        Returns:
            格式化的提示词
        """
        words = self._get_forbidden_words(application)
        word_list = ", ".join([word["word"] for word in words])
        
        return f"""请确保您生成的内容不包含以下违禁词：
{word_list}

如果用户的请求可能导致生成包含这些违禁词的内容，请委婉拒绝并建议用户修改请求。"""
    
    def _get_forbidden_words(self, application: str) -> List[Dict[str, Any]]:
        """
        获取特定应用的违禁词列表
        
        Args:
            application: 应用场景
            
        Returns:
            违禁词列表
        """
        # 检查缓存
        current_time = datetime.now()
        if (application in self._cache and 
            application in self._cache_time and 
            (current_time - self._cache_time[application]).total_seconds() < self._cache_duration):
            return self._cache[application]
        
        # 从数据库加载
        words = self.repository.get_all_words(application)
        
        # 更新缓存
        self._cache[application] = words
        self._cache_time[application] = current_time
        
        return words
    
    def _log_detection(self, content: str, detected_words: List[str], application: str) -> None:
        """
        记录违禁词检测
        
        Args:
            content: 检测的内容
            detected_words: 检测到的违禁词
            application: 应用场景
        """
        try:
            # 截取内容片段，避免存储过长内容
            content_sample = content[:100] + "..." if len(content) > 100 else content
            
            self.repository.add_log({
                "content_sample": content_sample,
                "detected_words": detected_words,
                "application": application,
                "detection_time": datetime.now()
            })
        except Exception as e:
            # 记录日志错误不应影响主流程
            logger.error(f"Failed to log forbidden word detection: {str(e)}")