"""用户数据存储库"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Union

from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy.orm import Session
from app.infrastructure.database.models.user import User, UserRole, UserStatus
from app.infrastructure.database.models.llm import LLMAuditLog

logger = logging.getLogger(__name__)

class UserRepository:
    """用户数据存储库，负责用户相关数据的持久化操作"""

    def __init__(self, db_session: Session):
        """初始化存储库
        
        Args:
            db_session: 数据库会话
        """
        self.db = db_session
    
    def create(self, user: User) -> User:
        """创建新用户
        
        Args:
            user: 用户对象
            
        Returns:
            创建的用户对象
            
        Raises:
            SQLAlchemyError: 数据库操作失败
        """
        try:
            self.db.session.add(user)
            self.db.session.commit()
            logger.info(f"Created user: {user.username}")
            return user
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Failed to create user: {str(e)}")
            raise
    
    def update(self, user: User) -> User:
        """更新用户信息
        
        Args:
            user: 用户对象
            
        Returns:
            更新后的用户对象
            
        Raises:
            SQLAlchemyError: 数据库操作失败
        """
        try:
            user.updated_at = datetime.utcnow()
            self.db.session.commit()
            logger.info(f"Updated user: {user.username}")
            return user
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Failed to update user: {str(e)}")
            raise
    
    def delete(self, user_id: int) -> bool:
        """删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否成功删除
            
        Raises:
            SQLAlchemyError: 数据库操作失败
        """
        try:
            user = self.find_by_id(user_id)
            if not user:
                logger.warning(f"Cannot delete user: User with ID {user_id} not found")
                return False
            
            self.db.session.delete(user)
            self.db.session.commit()
            logger.info(f"Deleted user: {user.username}")
            return True
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Failed to delete user: {str(e)}")
            raise
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        """通过ID查找用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户对象或None
        """
        try:
            return User.query.get(user_id)
        except SQLAlchemyError as e:
            logger.error(f"Error finding user by ID: {str(e)}")
            return None
    
    def find_by_username(self, username: str) -> Optional[User]:
        """通过用户名查找用户
        
        Args:
            username: 用户名
            
        Returns:
            用户对象或None
        """
        try:
            return User.query.filter_by(username=username).first()
        except SQLAlchemyError as e:
            logger.error(f"Error finding user by username: {str(e)}")
            return None
    
    def find_by_email(self, email: str) -> Optional[User]:
        """通过邮箱查找用户
        
        Args:
            email: 邮箱
            
        Returns:
            用户对象或None
        """
        try:
            return User.query.filter_by(email=email).first()
        except SQLAlchemyError as e:
            logger.error(f"Error finding user by email: {str(e)}")
            return None
    
    def find_by_username_or_email(self, username_or_email: str) -> Optional[User]:
        """通过用户名或邮箱查找用户
        
        Args:
            username_or_email: 用户名或邮箱
            
        Returns:
            用户对象或None
        """
        try:
            return User.query.filter(
                (User.username == username_or_email) | (User.email == username_or_email)
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error finding user by username or email: {str(e)}")
            return None
    

    
    def find_by_reset_token(self, token: str) -> Optional[User]:
        """通过密码重置令牌查找用户
        
        Args:
            token: 重置令牌
            
        Returns:
            用户对象或None
        """
        try:
            return User.query.filter_by(reset_password_token=token).first()
        except SQLAlchemyError as e:
            logger.error(f"Error finding user by reset token: {str(e)}")
            return None
    
    def find_by_email_verification_token(self, token: str) -> Optional[User]:
        """通过邮箱验证令牌查找用户
        
        Args:
            token: 验证令牌
            
        Returns:
            用户对象或None
        """
        try:
            return User.query.filter_by(email_verification_token=token).first()
        except SQLAlchemyError as e:
            logger.error(f"Error finding user by email verification token: {str(e)}")
            return None
    
    def find_all(self, page: int = 1, per_page: int = 20, **filters) -> tuple[List[User], int]:
        """查询用户列表
        
        Args:
            page: 页码
            per_page: 每页记录数
            **filters: 过滤条件
            
        Returns:
            (用户列表, 总记录数)
        """
        try:
            query = User.query
            
            # 应用过滤条件
            if 'username' in filters and filters['username']:
                query = query.filter(User.username.like(f"%{filters['username']}%"))
            
            if 'email' in filters and filters['email']:
                query = query.filter(User.email.like(f"%{filters['email']}%"))
            
            if 'role' in filters and filters['role']:
                query = query.filter(User.role == filters['role'])
            
            if 'status' in filters and filters['status']:
                query = query.filter(User.status == filters['status'])
            
            # 计算总记录数
            total = query.count()
            
            # 应用分页
            users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page).items
            
            return users, total
        except SQLAlchemyError as e:
            logger.error(f"Error finding users: {str(e)}")
            return [], 0


    def log_activity(self, user_id: int, action: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None, details: Optional[str] = None, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> LLMAuditLog:
        """记录用户活动
        
        Args:
            user_id: 用户ID
            action: 操作类型
            resource_type: 资源类型
            resource_id: 资源ID
            details: 详细信息
            ip_address: IP地址
            user_agent: 用户代理
            
        Returns:
            创建的审计日志对象
            
        Raises:
            SQLAlchemyError: 数据库操作失败
        """
        try:
            log = LLMAuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent
            )
            self.db.session.add(log)
            self.db.session.commit()
            return log
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Failed to log activity: {str(e)}")
            raise
    
    def get_user_activity_logs(self, user_id: int, page: int = 1, per_page: int = 20) -> tuple[List[LLMAuditLog], int]:
        """获取用户活动日志
        
        Args:
            user_id: 用户ID
            page: 页码
            per_page: 每页记录数
            
        Returns:
            (日志列表, 总记录数)
        """
        try:
            query = LLMAuditLog.query.filter_by(user_id=user_id)
            
            # 计算总记录数
            total = query.count()
            
            # 应用分页
            logs = query.order_by(LLMAuditLog.created_at.desc()).paginate(page=page, per_page=per_page).items
            
            return logs, total
        except SQLAlchemyError as e:
            logger.error(f"Error getting user activity logs: {str(e)}")
            return [], 0