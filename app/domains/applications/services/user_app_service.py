# app/domains/applications/services/user_app_service.py
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from app.core.exceptions import ValidationException, NotFoundException
from app.core.status_codes import PARAMETER_ERROR, APPLICATION_NOT_FOUND
from app.infrastructure.database.repositories.user_app_repository import UserAppRepository
from app.infrastructure.database.repositories.user_llm_config_repository import UserLLMConfigRepository

class UserAppService:
    """用户应用服务"""
    
    def __init__(self, user_app_repository: UserAppRepository, user_llm_config_repository: UserLLMConfigRepository = None):
        """初始化服务"""
        self.user_app_repo = user_app_repository
        self.user_llm_config_repo = user_llm_config_repository
    
    def get_all_apps(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户所有应用"""
        apps = self.user_app_repo.get_all_by_user(user_id)
        return [self._format_app(app) for app in apps]
    
    def get_app(self, app_id: int, user_id: int) -> Dict[str, Any]:
        """获取用户特定应用"""
        app = self.user_app_repo.get_by_id(app_id, user_id)
        return self._format_app(app)
    
    def get_app_by_key(self, app_key: str) -> Optional[Dict[str, Any]]:
        """根据应用密钥获取应用"""
        app = self.user_app_repo.get_by_app_key(app_key)
        if not app:
            return None
        return self._format_app(app)
    
    def add_app(self, app_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """添加应用到用户列表"""
        # 验证数据
        self._validate_app_data(app_data)
        
        # 验证LLM配置
        if "user_llm_config_id" in app_data and app_data["user_llm_config_id"] and self.user_llm_config_repo:
            try:
                self.user_llm_config_repo.get_by_id(app_data["user_llm_config_id"], user_id)
            except Exception as e:
                raise ValidationException(f"指定的LLM配置无效: {str(e)}", PARAMETER_ERROR)
        
        # 设置用户ID和创建时间
        app_data["user_id"] = user_id
        app_data["created_at"] = datetime.utcnow()
        
        # 生成应用密钥
        app_data["app_key"] = self._generate_app_key()
        
        # 设置初始状态
        app_data["published"] = False
        app_data["published_config"] = None
        
        # 创建应用
        app = self.user_app_repo.create(app_data)
        return self._format_app(app)
    
    def update_app(self, app_id: int, app_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """更新用户应用配置"""
        # 获取当前应用
        app = self.user_app_repo.get_by_id(app_id, user_id)
        
        # 验证数据
        if app_data:
            self._validate_app_data(app_data, is_update=True)
        
        # 验证LLM配置
        if "user_llm_config_id" in app_data and app_data["user_llm_config_id"] and self.user_llm_config_repo:
            try:
                self.user_llm_config_repo.get_by_id(app_data["user_llm_config_id"], user_id)
            except Exception as e:
                raise ValidationException(f"指定的LLM配置无效: {str(e)}", PARAMETER_ERROR)
        
        # 禁止更新用户ID、应用密钥和发布状态
        if "user_id" in app_data:
            del app_data["user_id"]
        if "app_key" in app_data:
            del app_data["app_key"]
        if "published" in app_data:
            del app_data["published"]
        if "published_config" in app_data:
            del app_data["published_config"]
        
        # 更新应用
        app_data["updated_at"] = datetime.utcnow()
        app = self.user_app_repo.update(app_id, user_id, app_data)
        return self._format_app(app)
    
    def publish_app(self, app_id: int, user_id: int) -> Dict[str, Any]:
        """发布应用配置"""
        # 获取当前应用
        app = self.user_app_repo.get_by_id(app_id, user_id)
        
        # 验证应用配置中包含必要的大模型设置
        if not app.config:
            raise ValidationException("应用配置不能为空", PARAMETER_ERROR)
        
        if "provider_type" not in app.config:
            raise ValidationException("应用配置必须指定大模型提供商类型", PARAMETER_ERROR)
        
        if "model_id" not in app.config:
            raise ValidationException("应用配置必须指定模型ID", PARAMETER_ERROR)
        
        # 保存当前配置作为发布配置
        published_config = {
            "app_type": app.app_type,
            "name": app.name,
            "description": app.description,
            "config": app.config,
            "published_at": datetime.utcnow().isoformat()
        }
        
        # 更新发布状态和配置
        update_data = {
            "published": True,
            "published_config": published_config,
            "updated_at": datetime.utcnow()
        }
        
        app = self.user_app_repo.update(app_id, user_id, update_data)
        return self._format_app(app)
    
    def unpublish_app(self, app_id: int, user_id: int) -> Dict[str, Any]:
        """取消发布应用"""
        # 更新发布状态
        update_data = {
            "published": False,
            "updated_at": datetime.utcnow()
        }
        
        app = self.user_app_repo.update(app_id, user_id, update_data)
        return self._format_app(app)
    
    def delete_app(self, app_id: int, user_id: int) -> bool:
        """从用户列表删除应用"""
        return self.user_app_repo.delete(app_id, user_id)
    
    def regenerate_app_key(self, app_id: int, user_id: int) -> Dict[str, Any]:
        """重新生成应用密钥"""
        # 生成新密钥
        new_key = self._generate_app_key()
        
        # 更新应用
        update_data = {
            "app_key": new_key,
            "updated_at": datetime.utcnow()
        }
        
        app = self.user_app_repo.update(app_id, user_id, update_data)
        return self._format_app(app)
    
    def _validate_app_data(self, data: Dict[str, Any], is_update: bool = False) -> None:
        """验证应用数据"""
        if not is_update:
            # 必填字段验证
            required_fields = ["name", "app_type"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                raise ValidationException(
                    f"缺少必填字段: {', '.join(missing_fields)}", 
                    PARAMETER_ERROR
                )
        
        # 应用类型验证
        if "app_type" in data:
            valid_types = ["xhs_copy"] 
            if data["app_type"] not in valid_types:
                raise ValidationException(
                    f"无效的应用类型: {data['app_type']}，有效类型: {', '.join(valid_types)}", 
                    PARAMETER_ERROR
                )
    
    def _generate_app_key(self) -> str:
        """生成应用密钥"""
        return str(uuid.uuid4()).replace("-", "")
    
    def _format_app(self, app) -> Dict[str, Any]:
        """格式化应用数据"""
        result = {
            "id": app.id,
            "name": app.name,
            "app_type": app.app_type,
            "description": app.description,
            "config": app.config,
            "app_key": app.app_key,
            "user_llm_config_id": app.user_llm_config_id,
            "published": app.published,
            "created_at": app.created_at.isoformat() if app.created_at else None,
            "updated_at": app.updated_at.isoformat() if app.updated_at else None
        }
        
        # 添加发布配置信息
        if app.published and app.published_config:
            result["published_config"] = app.published_config
        
        return result