"""LLM 相关服务"""
from typing import List, Dict, Any, Optional, Tuple
from app.infrastructure.database.repositories.llm_repository import LLMAuditLogRepository, LLMProviderRepository,LLMModelRepository

from app.infrastructure.database.repositories.user_repository import UserRepository
from app.core.exceptions import ValidationException, ConflictException
from app.core.status_codes import PROVIDER_VALIDATION_ERROR, PROVIDER_ALREADY_EXISTS, MODEL_VALIDATION_ERROR

class LLMProviderService:
    """AI提供商服务"""
    
    def __init__(self, provider_repository: LLMProviderRepository, user_repository: UserRepository):
        """
        初始化服务
        
        参数:
            provider_repository: AI提供商存储库
            user_repository: 用户存储库
        """
        self.provider_repo = provider_repository
        self.user_repo = user_repository
    
    def get_all_providers(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取用户的所有AI提供商
        
        参数:
            user_id: 用户ID
            
        返回:
            提供商列表
        """
        providers = self.provider_repo.get_all_by_user(user_id)
        return [self._format_provider(provider) for provider in providers]
    
    def get_provider(self, provider_id: int, user_id: int) -> Dict[str, Any]:
        """
        获取特定的AI提供商
        
        参数:
            provider_id: 提供商ID
            user_id: 用户ID
            
        返回:
            提供商信息
        """
        provider = self.provider_repo.get_by_id(provider_id, user_id)
        return self._format_provider(provider)
    
    def create_provider(self, provider_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """
        创建新的AI提供商
        
        参数:
            provider_data: 提供商数据
            user_id: 用户ID
            
        返回:
            创建的提供商信息
            
        异常:
            ValidationException: 验证失败
            ConflictException: 提供商已存在
        """
        # 验证数据
        self._validate_provider_data(provider_data)
        
        # 设置用户ID
        provider_data["user_id"] = user_id
        
        # 创建提供商
        try:
            provider = self.provider_repo.create(provider_data)
            return self._format_provider(provider)
        except Exception as e:
            raise ConflictException(
                f"创建AI提供商失败: {str(e)}", 
                PROVIDER_ALREADY_EXISTS
            )
    
    def update_provider(self, provider_id: int, provider_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """
        更新AI提供商
        
        参数:
            provider_id: 提供商ID
            provider_data: 要更新的数据
            user_id: 用户ID
            
        返回:
            更新后的提供商信息
        """
        # 验证数据
        if provider_data:
            self._validate_provider_data(provider_data, is_update=True)
        
        # 禁止更新用户ID
        if "user_id" in provider_data:
            del provider_data["user_id"]
        
        # 更新提供商
        provider = self.provider_repo.update(provider_id, user_id, provider_data)
        return self._format_provider(provider)
    
    def delete_provider(self, provider_id: int, user_id: int) -> bool:
        """
        删除AI提供商
        
        参数:
            provider_id: 提供商ID
            user_id: 用户ID
            
        返回:
            操作是否成功
        """
        return self.provider_repo.delete(provider_id, user_id)
    
    def _validate_provider_data(self, data: Dict[str, Any], is_update: bool = False) -> None:
        """
        验证提供商数据
        
        参数:
            data: 要验证的数据
            is_update: 是否为更新操作
            
        异常:
            ValidationException: 验证失败
        """
        if not is_update:
            # 必填字段验证
            required_fields = ["name", "provider_type", "api_key"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                raise ValidationException(
                    f"缺少必填字段: {', '.join(missing_fields)}", 
                    PROVIDER_VALIDATION_ERROR
                )
        
        # 提供商类型验证
        if "provider_type" in data:
            valid_types = ["OpenAI", "Claude", "Volcano"]
            if data["provider_type"] not in valid_types:
                raise ValidationException(
                    f"无效的提供商类型: {data['provider_type']}，有效类型: {', '.join(valid_types)}", 
                    PROVIDER_VALIDATION_ERROR
                )
            
            # 基于提供商类型验证必要的字段
            if data["provider_type"] == "OpenAI" and "api_key" in data:
                if not data["api_key"]:
                    raise ValidationException("OpenAI平台需要提供有效的API密钥", PROVIDER_VALIDATION_ERROR)
            
            elif data["provider_type"] == "Claude" and "api_key" in data:
                if not data["api_key"]:
                    raise ValidationException("Claude平台需要提供有效的API密钥", PROVIDER_VALIDATION_ERROR)
            
            elif data["provider_type"] == "Volcano" and "api_key" in data:
                # 火山引擎可能需要更多配置
                if not data["api_key"]:
                    raise ValidationException("火山引擎平台需要提供有效的API密钥", PROVIDER_VALIDATION_ERROR)
    
    def _format_provider(self, provider) -> Dict[str, Any]:
        """
        格式化提供商数据
        
        参数:
            provider: 提供商实例
            
        返回:
            格式化后的提供商数据
        """
        # 获取用户信息(可选，如果需要在响应中包含用户信息)
        user = None
        if self.user_repo:
            try:
                user = self.user_repo.find_by_id(provider.user_id)
            except:
                pass
        
        user_info = {
            "id": provider.user_id,
            "username": user.username if user else "未知用户"
        } if user else {"id": provider.user_id}
        
        return {
            "id": provider.id,
            "name": provider.name,
            "provider_type": provider.provider_type,
            "api_key": "***" + provider.api_key[-4:] if provider.api_key else None,  # 隐藏API密钥
            "api_base_url": provider.api_base_url,
            "api_version": provider.api_version,
            "is_active": provider.is_active,
            "created_at": provider.created_at.isoformat() if provider.created_at else None,
            "updated_at": provider.updated_at.isoformat() if provider.updated_at else None,
            "user": user_info  # 包含用户信息，明确表示这是用户自己的配置
        }

class LLMModelService:
    """AI模型服务"""
    
    def __init__(self, model_repository: LLMModelRepository, provider_repository: LLMProviderRepository):
        """
        初始化服务
        
        参数:
            model_repository: AI模型存储库
            provider_repository: AI提供商存储库
        """
        self.model_repo = model_repository
        self.provider_repo = provider_repository
    
    def get_all_models(self, provider_id: int, user_id: int) -> List[Dict[str, Any]]:
        """
        获取提供商的所有模型
        
        参数:
            provider_id: 提供商ID
            user_id: 用户ID
            
        返回:
            模型列表
            
        异常:
            NotFoundException: 提供商不存在
        """
        # 验证提供商存在且属于该用户
        self.provider_repo.get_by_id(provider_id, user_id)
        
        models = self.model_repo.get_all_by_provider(provider_id)
        return [self._format_model(model) for model in models]
    
    def get_model(self, model_id: int, provider_id: int, user_id: int) -> Dict[str, Any]:
        """
        获取特定的AI模型
        
        参数:
            model_id: 模型ID
            provider_id: 提供商ID
            user_id: 用户ID
            
        返回:
            模型信息
            
        异常:
            NotFoundException: 提供商或模型不存在
        """
        # 验证提供商存在且属于该用户
        self.provider_repo.get_by_id(provider_id, user_id)
        
        model = self.model_repo.get_by_id(model_id, provider_id)
        return self._format_model(model)
    
    def create_model(self, model_data: Dict[str, Any], provider_id: int, user_id: int) -> Dict[str, Any]:
        """
        创建新的AI模型
        
        参数:
            model_data: 模型数据
            provider_id: 提供商ID
            user_id: 用户ID
            
        返回:
            创建的模型信息
            
        异常:
            ValidationException: 验证失败
            NotFoundException: 提供商不存在
        """
        # 验证提供商存在且属于该用户
        self.provider_repo.get_by_id(provider_id, user_id)
        
        # 验证数据
        self._validate_model_data(model_data)
        
        # 设置提供商ID
        model_data["provider_id"] = provider_id
        
        # 创建模型
        model = self.model_repo.create(model_data)
        return self._format_model(model)
    
    def update_model(self, model_id: int, model_data: Dict[str, Any], provider_id: int, user_id: int) -> Dict[str, Any]:
        """
        更新AI模型
        
        参数:
            model_id: 模型ID
            model_data: 要更新的数据
            provider_id: 提供商ID
            user_id: 用户ID
            
        返回:
            更新后的模型信息
            
        异常:
            ValidationException: 验证失败
            NotFoundException: 提供商或模型不存在
        """
        # 验证提供商存在且属于该用户
        self.provider_repo.get_by_id(provider_id, user_id)
        
        # 验证数据
        if model_data:
            self._validate_model_data(model_data, is_update=True)
        
        # 禁止更新提供商ID
        if "provider_id" in model_data:
            del model_data["provider_id"]
        
        # 更新模型
        model = self.model_repo.update(model_id, provider_id, model_data)
        return self._format_model(model)
    
    def delete_model(self, model_id: int, provider_id: int, user_id: int) -> bool:
        """
        删除AI模型
        
        参数:
            model_id: 模型ID
            provider_id: 提供商ID
            user_id: 用户ID
            
        返回:
            操作是否成功
            
        异常:
            NotFoundException: 提供商或模型不存在
        """
        # 验证提供商存在且属于该用户
        self.provider_repo.get_by_id(provider_id, user_id)
        
        return self.model_repo.delete(model_id, provider_id)
    
    def _validate_model_data(self, data: Dict[str, Any], is_update: bool = False) -> None:
        """
        验证模型数据
        
        参数:
            data: 要验证的数据
            is_update: 是否为更新操作
            
        异常:
            ValidationException: 验证失败
        """
        if not is_update:
            # 必填字段验证
            required_fields = ["name", "model_id"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                raise ValidationException(
                    f"缺少必填字段: {', '.join(missing_fields)}", 
                    MODEL_VALIDATION_ERROR
                )
    
    def _format_model(self, model) -> Dict[str, Any]:
        """
        格式化模型数据
        
        参数:
            model: 模型实例
            
        返回:
            格式化后的模型数据
        """
        return {
            "id": model.id,
            "name": model.name,
            "model_id": model.model_id,
            "description": model.description,
            "capabilities": model.capabilities,
            "context_window": model.context_window,
            "max_tokens": model.max_tokens,
            "token_price_input": model.token_price_input,
            "token_price_output": model.token_price_output,
            "is_available": model.is_available,
            "provider_id": model.provider_id,
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None
        }
    
class LLMAuditService:
    """LLM审计服务"""
    
    def __init__(
        self, 
        audit_repository: LLMAuditLogRepository,
        provider_repository: Optional[LLMProviderRepository] = None,
        model_repository: Optional[LLMModelRepository] = None,
        user_repository: Optional[UserRepository] = None
    ):
        """
        初始化服务
        
        参数:
            audit_repository: 审计日志存储库
            provider_repository: 提供商存储库
            model_repository: 模型存储库
            user_repository: 用户存储库
        """
        self.audit_repo = audit_repository
        self.provider_repo = provider_repository
        self.model_repo = model_repository
        self.user_repo = user_repository
    
    def log_request(
        self,
        user_id: int,
        provider_id: int,
        model_id: int,
        request_type: str,
        prompt: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        app_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        记录请求
        
        参数:
            user_id: 用户ID
            provider_id: 提供商ID
            model_id: 模型ID
            request_type: 请求类型
            prompt: 提示词
            parameters: 请求参数
            app_id: 应用ID
            ip_address: IP地址
            user_agent: 用户代理
            
        返回:
            日志对象
        """
        # 开始计时
        start_time = time.time()
        
        # 创建日志记录
        log_data = {
            "user_id": user_id,
            "provider_id": provider_id,
            "model_id": model_id,
            "request_type": request_type,
            "prompt": prompt,
            "parameters": parameters,
            "app_id": app_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "status": "processing"
        }
        
        log = self.audit_repo.create_log(log_data)
        
        # 返回日志对象和开始时间（用于后续更新）
        return {
            "log_id": log.id,
            "start_time": start_time
        }
    
    def update_log_success(
        self,
        log_id: int,
        response: str,
        tokens_used: int,
        tokens_prompt: int,
        tokens_completion: int,
        start_time: float,
        estimated_cost: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        更新成功日志
        
        参数:
            log_id: 日志ID
            response: 响应内容
            tokens_used: 使用的令牌数
            tokens_prompt: 提示词的令牌数
            tokens_completion: 补全的令牌数
            start_time: 开始时间
            estimated_cost: 估计成本
            
        返回:
            更新后的日志对象
        """
        # 计算延迟
        latency_ms = int((time.time() - start_time) * 1000)
        
        # 获取日志对象
        log = self.audit_repo.get_by_id(log_id)
        
        # 更新日志
        log_data = {
            "response": response,
            "tokens_used": tokens_used,
            "tokens_prompt": tokens_prompt,
            "tokens_completion": tokens_completion,
            "latency_ms": latency_ms,
            "status": "success",
            "estimated_cost": estimated_cost or 0
        }
        
        for key, value in log_data.items():
            setattr(log, key, value)
        
        self.audit_repo.db.commit()
        self.audit_repo.db.refresh(log)
        
        return self._format_log(log)
    
    def update_log_error(
        self,
        log_id: int,
        error_message: str,
        start_time: float
    ) -> Dict[str, Any]:
        """
        更新错误日志
        
        参数:
            log_id: 日志ID
            error_message: 错误信息
            start_time: 开始时间
            
        返回:
            更新后的日志对象
        """
        # 计算延迟
        latency_ms = int((time.time() - start_time) * 1000)
        
        # 获取日志对象
        log = self.audit_repo.get_by_id(log_id)
        
        # 更新日志
        log_data = {
            "error_message": error_message,
            "latency_ms": latency_ms,
            "status": "error"
        }
        
        for key, value in log_data.items():
            setattr(log, key, value)
        
        self.audit_repo.db.commit()
        self.audit_repo.db.refresh(log)
        
        return self._format_log(log)
    
    def get_user_logs(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 20,
        **filters
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取用户日志
        
        参数:
            user_id: 用户ID
            page: 页码
            per_page: 每页数量
            **filters: 过滤条件
            
        返回:
            (日志列表, 总数)
        """
        logs, total = self.audit_repo.get_by_user(user_id, page, per_page, **filters)
        return [self._format_log(log) for log in logs], total
    
    def get_user_statistics(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取用户统计数据
        
        参数:
            user_id: 用户ID
            days: 天数
            
        返回:
            统计数据
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        stats = self.audit_repo.get_user_statistics(user_id, start_date, end_date)
        
        # 添加日期范围信息
        stats["start_date"] = start_date.isoformat()
        stats["end_date"] = end_date.isoformat()
        stats["days"] = days
        
        return stats
    
    def _format_log(self, log) -> Dict[str, Any]:
        """
        格式化日志
        
        参数:
            log: 日志对象
            
        返回:
            格式化后的日志
        """
        result = {
            "id": log.id,
            "user_id": log.user_id,
            "provider_id": log.provider_id,
            "model_id": log.model_id,
            "app_id": log.app_id,
            "request_type": log.request_type,
            "prompt": log.prompt,
            "parameters": log.parameters,
            "response": log.response,
            "tokens_used": log.tokens_used,
            "tokens_prompt": log.tokens_prompt,
            "tokens_completion": log.tokens_completion,
            "latency_ms": log.latency_ms,
            "status": log.status,
            "error_message": log.error_message,
            "estimated_cost": log.estimated_cost,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at.isoformat() if log.created_at else None
        }
        
        # 添加关联信息（如果有对应的存储库）
        if self.provider_repo and hasattr(log, "provider") and log.provider:
            result["provider_name"] = log.provider.name
            result["provider_type"] = log.provider.provider_type
        
        if self.model_repo and hasattr(log, "model") and log.model:
            result["model_name"] = log.model.name
            result["model_id_str"] = log.model.model_id
        
        if self.user_repo and hasattr(log, "user") and log.user:
            result["username"] = log.user.username
        
        return result