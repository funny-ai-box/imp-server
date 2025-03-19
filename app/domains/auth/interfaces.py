"""认证服务接口定义"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from app.infrastructure.database.models.user import User

class AuthServiceInterface(ABC):
    """认证服务接口"""
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def authenticate_token(self, token: str) -> User:
        """验证JWT令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            认证成功的用户对象
            
        Raises:
            AuthenticationException: 令牌无效或已过期
        """
        pass
    
    @abstractmethod
    def authenticate_api_key(self, api_key: str) -> User:
        """API密钥认证
        
        Args:
            api_key: API密钥
            
        Returns:
            认证成功的用户对象
            
        Raises:
            AuthenticationException: API密钥无效
        """
        pass
    
    @abstractmethod
    def generate_jwt_token(self, user: User) -> str:
        """生成JWT令牌
        
        Args:
            user: 用户对象
            
        Returns:
            JWT令牌
        """
        pass
    
    @abstractmethod
    def hash_password(self, password: str) -> str:
        """哈希密码
        
        Args:
            password: 明文密码
            
        Returns:
            哈希后的密码
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def verify_email(self, token: str) -> bool:
        """验证用户邮箱
        
        Args:
            token: 邮箱验证令牌
            
        Returns:
            验证是否成功
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def generate_reset_token(self, email: str) -> Optional[str]:
        """生成密码重置令牌
        
        Args:
            email: 用户邮箱
            
        Returns:
            重置令牌，如果用户不存在则返回None
        """
        pass
    
    @abstractmethod
    def reset_password(self, token: str, new_password: str) -> bool:
        """重置用户密码
        
        Args:
            token: 重置令牌
            new_password: 新密码
            
        Returns:
            重置是否成功
        """
        pass
    
    @abstractmethod
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
        pass