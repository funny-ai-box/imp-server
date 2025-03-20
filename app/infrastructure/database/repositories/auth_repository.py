"""认证相关存储库"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.infrastructure.database.models.auth import LoginHistory
from app.infrastructure.database.models.user import User, UserRole, UserStatus

logger = logging.getLogger(__name__)

class AuthRepository:
    """认证存储库，用于处理登录历史"""
    
    def __init__(self, db_session: Session):
        """初始化存储库
        
        Args:
            db_session: 数据库会话
        """
        self.db = db_session
    
    def record_login(self, user_id: int, login_method: str, is_success: bool = True, ip_address: Optional[str] = None, user_agent: Optional[str] = None, failure_reason: Optional[str] = None) -> LoginHistory:
        """记录登录历史
        
        Args:
            user_id: 用户ID
            login_method: 登录方式
            is_success: 是否登录成功
            ip_address: IP地址
            user_agent: 用户代理
            failure_reason: 失败原因
            
        Returns:
            登录历史对象
            
        Raises:
            SQLAlchemyError: 数据库操作失败
        """
        try:
            # 创建登录历史对象
            login_record = LoginHistory(
                user_id=user_id,
                login_method=login_method,
                is_success=is_success,
                ip_address=ip_address,
                user_agent=user_agent,
                failure_reason=failure_reason
            )
            
            # 保存到数据库
            self.db.add(login_record)
            self.db.commit()
            self.db.refresh(login_record)
            
            logger.info(f"Recorded login for user: {user_id}, success: {is_success}")
            return login_record
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to record login: {str(e)}")
            raise
    
    def register_user(self, phone: str, password_hash: str, username: Optional[str] = None, **user_data) -> User:
        """注册新用户
        
        Args:
            phone: 手机号码
            password_hash: 哈希密码
            username: 用户名（可选，默认使用手机号）
            **user_data: 其他用户数据
            
        Returns:
            创建的用户对象
            
        Raises:
            SQLAlchemyError: 数据库操作失败
        """
        try:
            # 如果未提供用户名，使用手机号
            if not username:
                username = phone
            print(username)
            # 创建用户对象
            user = User(
                username=username,
                phone=phone,
                password_hash=password_hash,
                role=UserRole.ADMIN,  # 默认设置为管理员角色
                status=UserStatus.ACTIVE,
                **user_data
            )
            
            # 保存到数据库
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"Registered new user with phone: {phone}")
            return user
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to register user: {str(e)}")
            raise
    
    def find_user_by_phone(self, phone: str) -> Optional[User]:
        """通过手机号查找用户
        
        Args:
            phone: 手机号码
            
        Returns:
            用户对象或None
        """
        print("find_user_by_phone")
        try:
            return self.db.query(User).filter(User.phone == phone).first()
        except SQLAlchemyError as e:
            print(e)
            logger.error(f"Error finding user by phone: {str(e)}")
            return None