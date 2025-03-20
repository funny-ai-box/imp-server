import uuid
from typing import List, Dict, Any, Optional
from app.infrastructure.database.repositories.application_repository import ApplicationRepository
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.core.exceptions import ValidationException, ConflictException, NotFoundException
from app.core.status_codes import APPLICATION_VALIDATION_ERROR, APPLICATION_ALREADY_EXISTS


class ApplicationService:
    """应用服务"""
    
    def __init__(self, application_repository: ApplicationRepository, user_repository: UserRepository):
        """
        初始化服务
        
        参数:
            application_repository: 应用存储库
            user_repository: 用户存储库
        """
        self.app_repo = application_repository
        self.user_repo = user_repository
    
    def get_all_applications(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取用户的所有应用
        
        参数:
            user_id: 用户ID
            
        返回:
            应用列表
        """
        apps = self.app_repo.get_all_by_user(user_id)
        return [self._format_application(app) for app in apps]
    
    def get_application(self, app_id: int, user_id: int) -> Dict[str, Any]:
        """
        获取特定的应用
        
        参数:
            app_id: 应用ID
            user_id: 用户ID
            
        返回:
            应用信息
        """
        app = self.app_repo.get_by_id(app_id, user_id)
        return self._format_application(app)
    
    def get_application_by_key(self, app_key: str) -> Optional[Dict[str, Any]]:
        """
        根据应用密钥获取应用
        
        参数:
            app_key: 应用密钥
            
        返回:
            应用信息，如果不存在则返回None
        """
        app = self.app_repo.get_by_app_key(app_key)
        if not app:
            return None
        return self._format_application(app)
    
    def create_application(self, app_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """
        创建新的应用
        
        参数:
            app_data: 应用数据
            user_id: 用户ID
            
        返回:
            创建的应用信息
            
        异常:
            ValidationException: 验证失败
            ConflictException: 应用已存在
        """
        # 验证数据
        self._validate_application_data(app_data)
        
        # 设置用户ID
        app_data["user_id"] = user_id
        
        # 生成应用密钥
        app_data["app_key"] = self._generate_app_key()
        
        # 创建应用
        try:
            app = self.app_repo.create(app_data)
            return self._format_application(app)
        except Exception as e:
            raise ConflictException(
                f"创建应用失败: {str(e)}", 
                APPLICATION_ALREADY_EXISTS
            )
    
    def update_application(self, app_id: int, app_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """
        更新应用
        
        参数:
            app_id: 应用ID
            app_data: 要更新的数据
            user_id: 用户ID
            
        返回:
            更新后的应用信息
        """
        # 验证数据
        if app_data:
            self._validate_application_data(app_data, is_update=True)
        
        # 禁止更新用户ID和应用密钥
        if "user_id" in app_data:
            del app_data["user_id"]
        if "app_key" in app_data:
            del app_data["app_key"]
        
        # 更新应用
        app = self.app_repo.update(app_id, user_id, app_data)
        return self._format_application(app)
    
    def delete_application(self, app_id: int, user_id: int) -> bool:
        """
        删除应用
        
        参数:
            app_id: 应用ID
            user_id: 用户ID
            
        返回:
            操作是否成功
        """
        return self.app_repo.delete(app_id, user_id)
    
    def _validate_application_data(self, data: Dict[str, Any], is_update: bool = False) -> None:
        """
        验证应用数据
        
        参数:
            data: 要验证的数据
            is_update: 是否为更新操作
            
        异常:
            ValidationException: 验证失败
        """
        if not is_update:
            # 必填字段验证
            required_fields = ["name"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                raise ValidationException(
                    f"缺少必填字段: {', '.join(missing_fields)}", 
                    APPLICATION_VALIDATION_ERROR
                )
    
    def _generate_app_key(self) -> str:
        """
        生成应用密钥
        
        返回:
            生成的应用密钥
        """
        return str(uuid.uuid4()).replace("-", "")
    
    def _format_application(self, app) -> Dict[str, Any]:
        """
        格式化应用数据
        
        参数:
            app: 应用实例
            
        返回:
            格式化后的应用数据
        """
        return {
            "id": app.id,
            "name": app.name,
            "app_key": app.app_key,
            "description": app.description,
            "is_active": app.is_active,
            "user_id": app.user_id,
            "created_at": app.created_at.isoformat() if app.created_at else None,
            "updated_at": app.updated_at.isoformat() if app.updated_at else None
        }