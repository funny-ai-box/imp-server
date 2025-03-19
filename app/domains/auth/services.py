"""认证领域服务实现"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

import jwt
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash

from app.core.exceptions import APIException, AuthenticationException
from app.core.status_codes import (
    AUTH_FAILED, TOKEN_EXPIRED, INVALID_TOKEN, 
    ACCOUNT_LOCKED, PASSWORD_ERROR, USER_NOT_FOUND
)
from app.domains.auth.interfaces import AuthServiceInterface
from app.infrastructure.database.models.user import User, UserStatus
from app.infrastructure.database.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

class AuthService(AuthServiceInterface):
    """认证服务实现"""
    
    def __init__(self, user_repository: UserRepository):
        """初始化认证服务
        
        Args:
            user_repository: 用户存储库
        """
        self.user_repository = user_repository
    
    def authenticate(self, username_or_email: str, password: str) -> Tuple[User, str]:
        """用户认证
        
        Args:
            username_or_email: 用户名或邮箱
            password: 密码
            
        Returns:
            Tuple[User, str]: 认证成功的用户对象和JWT令牌
            
        Raises:
            AuthenticationException: 认证失败
        """
        try:
            # 查找用户
            user = self.user_repository.find_by_username_or_email(username_or_email)
            
            if not user:
                logger.warning(f"Authentication failed: User not found - {username_or_email}")
                raise AuthenticationException("用户名或密码不正确", AUTH_FAILED)
            
            # 检查用户状态
            if user.status != UserStatus.ACTIVE:
                logger.warning(f"Authentication failed: User not active - {username_or_email}")
                raise AuthenticationException("账户不可用或已被锁定", ACCOUNT_LOCKED)
            
            # 验证密码
            if not check_password_hash(user.password_hash, password):
                logger.warning(f"Authentication failed: Invalid password - {username_or_email}")
                raise AuthenticationException("用户名或密码不正确", PASSWORD_ERROR)
            
            # 生成访问令牌
            token = self.generate_jwt_token(user)
            
            # 更新最后登录时间
            user.last_login_at = datetime.utcnow()
            self.user_repository.update(user)
            
            logger.info(f"User authenticated successfully: {user.username}")
            return user, token
            
        except Exception as e:
            if isinstance(e, AuthenticationException):
                raise
            logger.error(f"Authentication error: {str(e)}")
            raise AuthenticationException("认证过程中发生错误", AUTH_FAILED)
    
    def authenticate_token(self, token: str) -> User:
        """验证JWT令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            认证成功的用户对象
            
        Raises:
            AuthenticationException: 令牌无效或已过期
        """
        try:
            # 解码令牌
            secret_key = current_app.config.get('JWT_SECRET_KEY')
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            
            # 获取用户ID并检索用户
            user_id = payload.get('sub')
            if not user_id:
                raise AuthenticationException("无效的令牌", INVALID_TOKEN)
            
            user = self.user_repository.find_by_id(user_id)
            if not user:
                raise AuthenticationException("令牌对应的用户不存在", USER_NOT_FOUND)
            
            # 检查用户状态
            if user.status != UserStatus.ACTIVE:
                raise AuthenticationException("用户账户已被禁用或锁定", ACCOUNT_LOCKED)
                
            return user
            
        except jwt.ExpiredSignatureError:
            logger.warning(f"Authentication failed: Token expired")
            raise AuthenticationException("令牌已过期", TOKEN_EXPIRED)
        except jwt.InvalidTokenError:
            logger.warning(f"Authentication failed: Invalid token")
            raise AuthenticationException("无效的令牌", INVALID_TOKEN)
        except Exception as e:
            if isinstance(e, AuthenticationException):
                raise
            logger.error(f"Token authentication error: {str(e)}")
            raise AuthenticationException("令牌验证过程中发生错误", INVALID_TOKEN)
    
    def authenticate_api_key(self, api_key: str) -> User:
        """API密钥认证
        
        Args:
            api_key: API密钥
            
        Returns:
            认证成功的用户对象
            
        Raises:
            AuthenticationException: API密钥无效
        """
        try:
            # 查找API密钥
            api_key_record = self.user_repository.find_api_key(api_key)
            
            if not api_key_record:
                logger.warning(f"API Key authentication failed: Key not found")
                raise AuthenticationException("无效的API密钥", INVALID_TOKEN)
            
            # 检查密钥是否有效
            if not api_key_record.is_valid:
                if api_key_record.is_expired:
                    logger.warning(f"API Key authentication failed: Key expired")
                    raise AuthenticationException("API密钥已过期", TOKEN_EXPIRED)
                else:
                    logger.warning(f"API Key authentication failed: Key inactive")
                    raise AuthenticationException("API密钥已被禁用", INVALID_TOKEN)
            
            # 获取用户
            user = api_key_record.user
            
            # 检查用户状态
            if user.status != UserStatus.ACTIVE:
                logger.warning(f"API Key authentication failed: User not active")
                raise AuthenticationException("用户账户已被禁用或锁定", ACCOUNT_LOCKED)
            
            # 更新密钥最后使用时间
            api_key_record.last_used_at = datetime.utcnow()
            self.user_repository.update_api_key(api_key_record)
            
            return user
            
        except Exception as e:
            if isinstance(e, AuthenticationException):
                raise
            logger.error(f"API Key authentication error: {str(e)}")
            raise AuthenticationException("API密钥验证过程中发生错误", INVALID_TOKEN)
    
    def generate_jwt_token(self, user: User) -> str:
        """生成JWT令牌
        
        Args:
            user: 用户对象
            
        Returns:
            JWT令牌
        """
        now = datetime.utcnow()
        token_ttl = current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', timedelta(hours=24))
        
        payload = {
            'sub': user.id,
            'iat': now,
            'exp': now + token_ttl,
            'username': user.username,
            'role': user.role.value
        }
        
        secret_key = current_app.config.get('JWT_SECRET_KEY')
        return jwt.encode(payload, secret_key, algorithm="HS256")
    
    def hash_password(self, password: str) -> str:
        """哈希密码
        
        Args:
            password: 明文密码
            
        Returns:
            哈希后的密码
        """
        return generate_password_hash(password, method='pbkdf2:sha256')
    
    def register_user(self, username: str, email: str, password: str, **user_data) -> User:
        """注册新用户
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            **user_data: 其他用户数据
            
        Returns:
            创建的用户对象
            
        Raises:
            APIException: 用户创建失败
        """
        try:
            # 检查用户名和邮箱是否已存在
            if self.user_repository.find_by_username(username):
                raise APIException("用户名已被使用", 30002)
                
            if self.user_repository.find_by_email(email):
                raise APIException("邮箱已被使用", 30002)
            
            # 创建新用户
            hashed_password = self.hash_password(password)
            
            user = User(
                username=username,
                email=email,
                password_hash=hashed_password,
                **user_data
            )
            
            # 生成邮箱验证令牌
            user.email_verification_token = str(uuid.uuid4())
            
            # 保存用户
            created_user = self.user_repository.create(user)
            
            logger.info(f"User registered successfully: {username}")
            return created_user
            
        except Exception as e:
            if isinstance(e, APIException):
                raise
            logger.error(f"User registration error: {str(e)}")
            raise APIException(f"用户注册失败: {str(e)}", 30003)
    
    def verify_email(self, token: str) -> bool:
        """验证用户邮箱
        
        Args:
            token: 邮箱验证令牌
            
        Returns:
            验证是否成功
        """
        try:
            user = self.user_repository.find_by_email_verification_token(token)
            
            if not user:
                logger.warning(f"Email verification failed: Invalid token")
                return False
            
            # 更新邮箱验证状态
            user.email_verified = True
            user.email_verification_token = None
            self.user_repository.update(user)
            
            logger.info(f"Email verified successfully for user: {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Email verification error: {str(e)}")
            return False
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """修改用户密码
        
        Args:
            user_id: 用户ID
            current_password: 当前密码
            new_password: 新密码
            
        Returns:
            操作是否成功
            
        Raises:
            APIException: 密码修改失败
        """
        try:
            # 查找用户
            user = self.user_repository.find_by_id(user_id)
            
            if not user:
                raise APIException("用户不存在", USER_NOT_FOUND)
            
            # 验证当前密码
            if not check_password_hash(user.password_hash, current_password):
                raise APIException("当前密码不正确", PASSWORD_ERROR)
            
            # 更新密码
            user.password_hash = self.hash_password(new_password)
            self.user_repository.update(user)
            
            logger.info(f"Password changed successfully for user: {user.username}")
            return True
            
        except Exception as e:
            if isinstance(e, APIException):
                raise
            logger.error(f"Password change error: {str(e)}")
            raise APIException(f"密码修改失败: {str(e)}", 30003)
    
    def generate_reset_token(self, email: str) -> Optional[str]:
        """生成密码重置令牌
        
        Args:
            email: 用户邮箱
            
        Returns:
            重置令牌，如果用户不存在则返回None
        """
        try:
            user = self.user_repository.find_by_email(email)
            
            if not user:
                logger.warning(f"Password reset token generation failed: User not found - {email}")
                return None
            
            # 生成重置令牌
            reset_token = str(uuid.uuid4())
            
            # 设置令牌有效期（24小时）
            expiry = datetime.utcnow() + timedelta(hours=24)
            
            # 保存重置令牌
            user.reset_password_token = reset_token
            user.reset_password_expires = expiry
            self.user_repository.update(user)
            
            logger.info(f"Password reset token generated for user: {user.username}")
            return reset_token
            
        except Exception as e:
            logger.error(f"Password reset token generation error: {str(e)}")
            return None
    
    def reset_password(self, token: str, new_password: str) -> bool:
        """重置用户密码
        
        Args:
            token: 重置令牌
            new_password: 新密码
            
        Returns:
            重置是否成功
        """
        try:
            # 查找用户
            user = self.user_repository.find_by_reset_token(token)
            
            if not user:
                logger.warning(f"Password reset failed: Invalid token")
                return False
            
            # 检查令牌是否过期
            if user.reset_password_expires and user.reset_password_expires < datetime.utcnow():
                logger.warning(f"Password reset failed: Token expired")
                return False
            
            # 更新密码
            user.password_hash = self.hash_password(new_password)
            user.reset_password_token = None
            user.reset_password_expires = None
            self.user_repository.update(user)
            
            logger.info(f"Password reset successfully for user: {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Password reset error: {str(e)}")
            return False
    
    def create_api_key(self, user_id: int, name: str, description: Optional[str] = None, expires_at: Optional[datetime] = None, permissions: Optional[str] = None) -> Dict[str, Any]:
        """为用户创建API密钥
        
        Args:
            user_id: 用户ID
            name: 密钥名称
            description: 密钥描述
            expires_at: 过期时间
            permissions: 权限字符串
            
        Returns:
            API密钥信息
            
        Raises:
            APIException: 密钥创建失败
        """
        try:
            # 查找用户
            user = self.user_repository.find_by_id(user_id)
            
            if not user:
                raise APIException("用户不存在", USER_NOT_FOUND)
            
            # 生成API密钥
            api_key = f"imp_{uuid.uuid4().hex}"
            
            # 创建API密钥记录
            api_key_data = {
                'user_id': user_id,
                'key': api_key,
                'name': name,
                'description': description,
                'expires_at': expires_at,
                'permissions': permissions
            }
            
            # 保存API密钥
            api_key_record = self.user_repository.create_api_key(api_key_data)
            
            logger.info(f"API key created for user: {user.username}")
            
            # 返回密钥信息（创建后唯一一次返回完整密钥）
            return {
                'id': api_key_record.id,
                'key': api_key,
                'name': api_key_record.name,
                'created_at': api_key_record.created_at.isoformat(),
                'expires_at': api_key_record.expires_at.isoformat() if api_key_record.expires_at else None
            }
            
        except Exception as e:
            if isinstance(e, APIException):
                raise
            logger.error(f"API key creation error: {str(e)}")
            raise APIException(f"API密钥创建失败: {str(e)}", 30003)