"""LLM模型存储库"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import func, desc, and_, or_
from sqlalchemy.orm import Session
from app.infrastructure.database.models.llm import LLMAuditLog, LLMModel, LLMProvider
from app.core.exceptions import NotFoundException
from app.core.status_codes import MODEL_NOT_FOUND


class LLMModelRepository:
    """AI模型存储库"""
    
    def __init__(self, db_session: Session):
        """
        初始化存储库
        
        参数:
            db_session: 数据库会话
        """
        self.db = db_session
    
    def get_all_by_provider(self, provider_id: int) -> List[LLMModel]:
        """
        获取提供商的所有模型
        
        参数:
            provider_id: 提供商ID
            
        返回:
            模型列表
        """
        return self.db.query(LLMModel).filter(LLMModel.provider_id == provider_id).all()
    
    def get_by_id(self, model_id: int, provider_id: int) -> LLMModel:
        """
        根据ID获取特定提供商的模型
        
        参数:
            model_id: 模型ID
            provider_id: 提供商ID
            
        返回:
            模型实例
            
        异常:
            NotFoundException: 模型不存在
        """
        model = self.db.query(LLMModel).filter(
            LLMModel.id == model_id,
            LLMModel.provider_id == provider_id
        ).first()
        
        if not model:
            raise NotFoundException(f"未找到ID为{model_id}的AI模型", MODEL_NOT_FOUND)
        
        return model
    
    def create(self, model_data: dict) -> LLMModel:
        """
        创建新的AI模型
        
        参数:
            model_data: 模型数据
            
        返回:
            新创建的模型实例
        """
        model = LLMModel(**model_data)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model
    
    def update(self, model_id: int, provider_id: int, model_data: dict) -> LLMModel:
        """
        更新AI模型
        
        参数:
            model_id: 模型ID
            provider_id: 提供商ID
            model_data: 要更新的数据
            
        返回:
            更新后的模型实例
            
        异常:
            NotFoundException: 模型不存在
        """
        model = self.get_by_id(model_id, provider_id)
        
        for key, value in model_data.items():
            if hasattr(model, key):
                setattr(model, key, value)
        
        self.db.commit()
        self.db.refresh(model)
        return model
    
    def delete(self, model_id: int, provider_id: int) -> bool:
        """
        删除AI模型
        
        参数:
            model_id: 模型ID
            provider_id: 提供商ID
            
        返回:
            操作是否成功
            
        异常:
            NotFoundException: 模型不存在
        """
        model = self.get_by_id(model_id, provider_id)
        self.db.delete(model)
        self.db.commit()
        return True
    
class LLMProviderRepository:
    """AI提供商存储库"""
    
    def __init__(self, db_session: Session):
        """
        初始化存储库
        
        参数:
            db_session: 数据库会话
        """
        self.db = db_session
    
    def get_all_by_user(self, user_id: int) -> List[LLMProvider]:
        """
        获取用户的所有AI提供商
        
        参数:
            user_id: 用户ID
            
        返回:
            提供商列表
        """
        return self.db.query(LLMProvider).filter(LLMProvider.user_id == user_id).all()
    
    def get_by_id(self, provider_id: int, user_id: int) -> LLMProvider:
        """
        根据ID获取指定用户的AI提供商
        
        参数:
            provider_id: 提供商ID
            user_id: 用户ID
            
        返回:
            提供商实例
            
        异常:
            NotFoundException: 提供商不存在
        """
        provider = self.db.query(LLMProvider).filter(
            LLMProvider.id == provider_id,
            LLMProvider.user_id == user_id
        ).first()
        
        if not provider:
            raise NotFoundException(f"未找到ID为{provider_id}的AI提供商", PROVIDER_NOT_FOUND)
        
        return provider
    
    def create(self, provider_data: dict) -> LLMProvider:
        """
        创建新的AI提供商
        
        参数:
            provider_data: 提供商数据
            
        返回:
            新创建的提供商实例
        """
        provider = LLMProvider(**provider_data)
        self.db.add(provider)
        self.db.commit()
        self.db.refresh(provider)
        return provider
    
    def update(self, provider_id: int, user_id: int, provider_data: dict) -> LLMProvider:
        """
        更新AI提供商
        
        参数:
            provider_id: 提供商ID
            user_id: 用户ID
            provider_data: 要更新的数据
            
        返回:
            更新后的提供商实例
            
        异常:
            NotFoundException: 提供商不存在
        """
        provider = self.get_by_id(provider_id, user_id)
        
        for key, value in provider_data.items():
            if hasattr(provider, key):
                setattr(provider, key, value)
        
        self.db.commit()
        self.db.refresh(provider)
        return provider
    
    def delete(self, provider_id: int, user_id: int) -> bool:
        """
        删除AI提供商
        
        参数:
            provider_id: 提供商ID
            user_id: 用户ID
            
        返回:
            操作是否成功
            
        异常:
            NotFoundException: 提供商不存在
        """
        provider = self.get_by_id(provider_id, user_id)
        self.db.delete(provider)
        self.db.commit()
        return True
        
    def get_by_type(self, provider_type: str, user_id: int) -> List[LLMProvider]:
        """
        根据类型获取用户的AI提供商
        
        参数:
            provider_type: 提供商类型
            user_id: 用户ID
            
        返回:
            提供商列表
        """
        return self.db.query(LLMProvider).filter(
            LLMProvider.provider_type == provider_type,
            LLMProvider.user_id == user_id
        ).all()
    
class LLMAuditRepository:
    """LLM审计日志存储库"""
    
    def __init__(self, db_session: Session):
        """
        初始化存储库
        
        参数:
            db_session: 数据库会话
        """
        self.db = db_session
    
    def create_log(self, log_data: Dict[str, Any]) -> LLMAuditLog:
        """
        创建审计日志
        
        参数:
            log_data: 日志数据
            
        返回:
            创建的日志对象
        """
        log = LLMAuditLog(**log_data)
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
    
    def get_by_id(self, log_id: int) -> LLMAuditLog:
        """
        根据ID获取日志
        
        参数:
            log_id: 日志ID
            
        返回:
            日志对象
            
        异常:
            NotFoundException: 日志不存在
        """
        log = self.db.query(LLMAuditLog).get(log_id)
        if not log:
            raise NotFoundException(f"未找到ID为{log_id}的审计日志", NOT_FOUND)
        return log
    
    def get_by_user(self, user_id: int, page: int = 1, per_page: int = 20, **filters) -> Tuple[List[LLMAuditLog], int]:
        """
        获取用户的审计日志
        
        参数:
            user_id: 用户ID
            page: 页码
            per_page: 每页数量
            **filters: 过滤条件
            
        返回:
            (日志列表, 总数)
        """
        query = self.db.query(LLMAuditLog).filter(LLMAuditLog.user_id == user_id)
        
        # 应用过滤条件
        query = self._apply_filters(query, filters)
        
        # 获取总数
        total = query.count()
        
        # 分页
        logs = query.order_by(desc(LLMAuditLog.created_at)).offset((page - 1) * per_page).limit(per_page).all()
        
        return logs, total
    
    def get_by_provider(self, provider_id: int, page: int = 1, per_page: int = 20, **filters) -> Tuple[List[LLMAuditLog], int]:
        """
        获取提供商的审计日志
        
        参数:
            provider_id: 提供商ID
            page: 页码
            per_page: 每页数量
            **filters: 过滤条件
            
        返回:
            (日志列表, 总数)
        """
        query = self.db.query(LLMAuditLog).filter(LLMAuditLog.provider_id == provider_id)
        
        # 应用过滤条件
        query = self._apply_filters(query, filters)
        
        # 获取总数
        total = query.count()
        
        # 分页
        logs = query.order_by(desc(LLMAuditLog.created_at)).offset((page - 1) * per_page).limit(per_page).all()
        
        return logs, total
    
    def get_by_model(self, model_id: int, page: int = 1, per_page: int = 20, **filters) -> Tuple[List[LLMAuditLog], int]:
        """
        获取模型的审计日志
        
        参数:
            model_id: 模型ID
            page: 页码
            per_page: 每页数量
            **filters: 过滤条件
            
        返回:
            (日志列表, 总数)
        """
        query = self.db.query(LLMAuditLog).filter(LLMAuditLog.model_id == model_id)
        
        # 应用过滤条件
        query = self._apply_filters(query, filters)
        
        # 获取总数
        total = query.count()
        
        # 分页
        logs = query.order_by(desc(LLMAuditLog.created_at)).offset((page - 1) * per_page).limit(per_page).all()
        
        return logs, total
    
    def get_user_statistics(self, user_id: int, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        获取用户的统计数据
        
        参数:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            
        返回:
            统计数据
        """
        query = self.db.query(LLMAuditLog).filter(LLMAuditLog.user_id == user_id)
        
        # 应用日期过滤
        if start_date:
            query = query.filter(LLMAuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(LLMAuditLog.created_at <= end_date)
        
        # 请求总数
        total_requests = query.count()
        
        # 成功和失败请求数
        success_count = query.filter(LLMAuditLog.status == "success").count()
        error_count = query.filter(LLMAuditLog.status == "error").count()
        
        # 令牌使用量
        tokens_data = self.db.query(
            func.sum(LLMAuditLog.tokens_used).label("total_tokens"),
            func.sum(LLMAuditLog.tokens_prompt).label("prompt_tokens"),
            func.sum(LLMAuditLog.tokens_completion).label("completion_tokens")
        ).filter(
            LLMAuditLog.user_id == user_id
        )
        
        if start_date:
            tokens_data = tokens_data.filter(LLMAuditLog.created_at >= start_date)
        if end_date:
            tokens_data = tokens_data.filter(LLMAuditLog.created_at <= end_date)
        
        tokens_result = tokens_data.first()
        
        # 估计成本
        total_cost = self.db.query(func.sum(LLMAuditLog.estimated_cost)).filter(
            LLMAuditLog.user_id == user_id
        )
        
        if start_date:
            total_cost = total_cost.filter(LLMAuditLog.created_at >= start_date)
        if end_date:
            total_cost = total_cost.filter(LLMAuditLog.created_at <= end_date)
        
        cost_result = total_cost.scalar() or 0
        
        # 平均延迟
        avg_latency = self.db.query(func.avg(LLMAuditLog.latency_ms)).filter(
            LLMAuditLog.user_id == user_id,
            LLMAuditLog.status == "success"
        )
        
        if start_date:
            avg_latency = avg_latency.filter(LLMAuditLog.created_at >= start_date)
        if end_date:
            avg_latency = avg_latency.filter(LLMAuditLog.created_at <= end_date)
        
        latency_result = avg_latency.scalar() or 0
        
        return {
            "total_requests": total_requests,
            "success_count": success_count,
            "error_count": error_count,
            "tokens_used": tokens_result.total_tokens or 0 if tokens_result else 0,
            "prompt_tokens": tokens_result.prompt_tokens or 0 if tokens_result else 0,
            "completion_tokens": tokens_result.completion_tokens or 0 if tokens_result else 0,
            "estimated_cost": float(cost_result),
            "avg_latency_ms": float(latency_result)
        }
    
    def _apply_filters(self, query, filters: Dict[str, Any]):
        """
        应用过滤条件
        
        参数:
            query: 查询对象
            filters: 过滤条件
            
        返回:
            过滤后的查询对象
        """
        # 日期过滤
        if "start_date" in filters and filters["start_date"]:
            query = query.filter(LLMAuditLog.created_at >= filters["start_date"])
        if "end_date" in filters and filters["end_date"]:
            query = query.filter(LLMAuditLog.created_at <= filters["end_date"])
        
        # 状态过滤
        if "status" in filters and filters["status"]:
            query = query.filter(LLMAuditLog.status == filters["status"])
        
        # 请求类型过滤
        if "request_type" in filters and filters["request_type"]:
            query = query.filter(LLMAuditLog.request_type == filters["request_type"])
        
        # 提供商ID过滤
        if "provider_id" in filters and filters["provider_id"]:
            query = query.filter(LLMAuditLog.provider_id == filters["provider_id"])
        
        # 模型ID过滤
        if "model_id" in filters and filters["model_id"]:
            query = query.filter(LLMAuditLog.model_id == filters["model_id"])
        
        # 应用ID过滤
        if "app_id" in filters and filters["app_id"]:
            query = query.filter(LLMAuditLog.app_id == filters["app_id"])
        
        # 关键词过滤
        if "keyword" in filters and filters["keyword"]:
            keyword = f"%{filters['keyword']}%"
            query = query.filter(
                or_(
                    LLMAuditLog.prompt.ilike(keyword),
                    LLMAuditLog.response.ilike(keyword),
                    LLMAuditLog.error_message.ilike(keyword)
                )
            )
        
        return query