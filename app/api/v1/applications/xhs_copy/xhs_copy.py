# app/api/v1/applications/xhs_copy/xhs_copy.py
from flask import Blueprint, request, g
from app.core.responses import success_response
from app.core.exceptions import ValidationException
from app.domains.applications.services.xhs_copy_service import (
    XhsCopyConfigService,
    XhsCopyGenerationService,
    
)
from app.infrastructure.database.repositories.xhs_copy_repository import (
    XhsCopyConfigRepository,
    XhsCopyGenerationRepository,
    XhsCopyTestRepository
)
from app.infrastructure.database.repositories.llm_repository import LLMProviderRepository, LLMModelRepository
from app.infrastructure.database.repositories.user_llm_config_repository import UserLLMConfigRepository
from app.api.middleware.auth import auth_required
import logging
import traceback

logger = logging.getLogger(__name__)

xhs_copy_bp = Blueprint("xhs_copy", __name__)

# 文案生成接口
@xhs_copy_bp.route("/generate", methods=["POST"])
@auth_required
def generate_content():
    """生成小红书文案（用户接口）"""
    try:
        user_id = g.user_id
        
        # 验证请求数据
        data = request.get_json()
        if not data:
            raise ValidationException("请求数据不能为空")
        
        # 提取数据
        prompt = data.get("prompt")
        if not prompt:
            raise ValidationException("提示词不能为空")
        
        image_urls = data.get("image_urls", [])
        config_id = data.get("config_id")
        
        # 验证图片URL格式
        if image_urls:
            for url in image_urls:
                if not url.startswith(('http://', 'https://')):
                    raise ValidationException(f"无效的图片URL: {url}")
        
        # 获取IP和用户代理
        ip_address = request.remote_addr
        user_agent = request.headers.get("User-Agent")
        
        # 初始化存储库和服务
        db_session = g.db_session
        generation_repo = XhsCopyGenerationRepository(db_session)
        config_repo = XhsCopyConfigRepository(db_session)
        provider_repo = LLMProviderRepository(db_session)
        model_repo = LLMModelRepository(db_session)
        user_llm_config_repo = UserLLMConfigRepository(db_session)
        
        generation_service = XhsCopyGenerationService(
            generation_repo, config_repo, provider_repo, model_repo, user_llm_config_repo
        )
        
        # 生成文案
        generation = generation_service.create_generation(
            prompt=prompt,
            image_urls=image_urls,
            config_id=config_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return success_response(generation, "生成小红书文案成功")
    except Exception as e:
        # 记录未知错误
        if not isinstance(e, ValidationException):
            logger.error(f"Error generating content: {str(e)}\n{traceback.format_exc()}")
        raise

@xhs_copy_bp.route("/generations", methods=["GET"])
@auth_required
def list_generations():
    """获取小红书文案生成历史记录"""
    try:
        user_id = g.user_id
        
        # 获取分页和过滤参数
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
        
        # 过滤条件
        filters = {}
        if "status" in request.args:
            filters["status"] = request.args.get("status")
        
        if "config_id" in request.args:
            filters["config_id"] = int(request.args.get("config_id"))
        
        if "app_id" in request.args:
            filters["app_id"] = int(request.args.get("app_id"))
        
        if "start_date" in request.args and "end_date" in request.args:
            filters["start_date"] = request.args.get("start_date")
            filters["end_date"] = request.args.get("end_date")
        
        # 初始化存储库和服务
        db_session = g.db_session
        generation_repo = XhsCopyGenerationRepository(db_session)
        config_repo = XhsCopyConfigRepository(db_session)
        provider_repo = LLMProviderRepository(db_session)
        model_repo = LLMModelRepository(db_session)
        user_llm_config_repo = UserLLMConfigRepository(db_session)
        
        generation_service = XhsCopyGenerationService(
            generation_repo, config_repo, provider_repo, model_repo, user_llm_config_repo
        )
        
        # 获取生成记录
        generations, total = generation_service.get_all_generations(
            user_id=user_id,
            page=page,
            per_page=per_page,
            **filters
        )
        
        return success_response({
            "items": generations,
            "total": total,
            "page": page,
            "per_page": per_page
        }, "获取小红书文案生成历史记录成功")
    except Exception as e:
        # 记录未知错误
        if not isinstance(e, ValidationException):
            logger.error(f"Error listing generations: {str(e)}\n{traceback.format_exc()}")
        raise

@xhs_copy_bp.route("/generation/<int:generation_id>", methods=["GET"])
@auth_required
def get_generation(generation_id):
    """获取特定生成记录"""
    try:
        user_id = g.user_id
        
        # 初始化存储库和服务
        db_session = g.db_session
        generation_repo = XhsCopyGenerationRepository(db_session)
        config_repo = XhsCopyConfigRepository(db_session)
        provider_repo = LLMProviderRepository(db_session)
        model_repo = LLMModelRepository(db_session)
        user_llm_config_repo = UserLLMConfigRepository(db_session)
        
        generation_service = XhsCopyGenerationService(
            generation_repo, config_repo, provider_repo, model_repo, user_llm_config_repo
        )
        
        # 获取生成记录
        generation = generation_service.get_generation(generation_id, user_id)
        
        return success_response(generation, "获取生成记录成功")
    except Exception as e:
        # 记录未知错误
        if not isinstance(e, ValidationException):
            logger.error(f"Error getting generation: {str(e)}\n{traceback.format_exc()}")
        raise

@xhs_copy_bp.route("/generation/<int:generation_id>/rate", methods=["POST"])
@auth_required
def rate_generation(generation_id):
    """对生成内容评分"""
    try:
        user_id = g.user_id
        
        # 验证请求数据
        data = request.get_json()
        if not data:
            raise ValidationException("请求数据不能为空")
        
        rating = data.get("rating")
        if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
            raise ValidationException("评分必须是1-5之间的整数")
            
        feedback = data.get("feedback")
        
        # 初始化存储库和服务
        db_session = g.db_session
        generation_repo = XhsCopyGenerationRepository(db_session)
        config_repo = XhsCopyConfigRepository(db_session)
        provider_repo = LLMProviderRepository(db_session)
        model_repo = LLMModelRepository(db_session)
        user_llm_config_repo = UserLLMConfigRepository(db_session)
        
        generation_service = XhsCopyGenerationService(
            generation_repo, config_repo, provider_repo, model_repo, user_llm_config_repo
        )
        
        # 提交评分
        generation = generation_service.rate_generation(
            generation_id=generation_id,
            user_id=user_id,
            rating=rating,
            feedback=feedback
        )
        
        return success_response(generation, "评分成功")
    except Exception as e:
        # 记录未知错误
        if not isinstance(e, ValidationException):
            logger.error(f"Error rating generation: {str(e)}\n{traceback.format_exc()}")
        raise

@xhs_copy_bp.route("/delete_generation", methods=["POST"])
@auth_required
def delete_generation():
    """删除生成记录"""
    try:
        user_id = g.user_id
        
        # 验证请求数据
        data = request.get_json()
        if not data or "generation_id" not in data:
            raise ValidationException("缺少必填参数: generation_id")
            
        generation_id = data["generation_id"]
        
        # 初始化存储库和服务
        db_session = g.db_session
        generation_repo = XhsCopyGenerationRepository(db_session)
        config_repo = XhsCopyConfigRepository(db_session)
        provider_repo = LLMProviderRepository(db_session)
        model_repo = LLMModelRepository(db_session)
        user_llm_config_repo = UserLLMConfigRepository(db_session)
        
        generation_service = XhsCopyGenerationService(
            generation_repo, config_repo, provider_repo, model_repo, user_llm_config_repo
        )
        
        # 删除生成记录
        result = generation_service.delete_generation(generation_id, user_id)
        
        return success_response({"success": result}, "删除生成记录成功")
    except Exception as e:
        # 记录未知错误
        if not isinstance(e, ValidationException):
            logger.error(f"Error deleting generation: {str(e)}\n{traceback.format_exc()}")
        raise

@xhs_copy_bp.route("/statistics", methods=["GET"])
@auth_required
def get_statistics():
    """获取统计数据"""
    try:
        user_id = g.user_id
        
        # 获取统计日期范围
        days = int(request.args.get("days", 30))
        
        # 初始化存储库和服务
        db_session = g.db_session
        generation_repo = XhsCopyGenerationRepository(db_session)
        config_repo = XhsCopyConfigRepository(db_session)
        provider_repo = LLMProviderRepository(db_session)
        model_repo = LLMModelRepository(db_session)
        user_llm_config_repo = UserLLMConfigRepository(db_session)
        
        generation_service = XhsCopyGenerationService(
            generation_repo, config_repo, provider_repo, model_repo, user_llm_config_repo
        )
        
        # 获取统计数据
        statistics = generation_service.get_statistics(user_id, days)
        
        return success_response(statistics, "获取统计数据成功")
    except Exception as e:
        # 记录未知错误
        if not isinstance(e, ValidationException):
            logger.error(f"Error getting statistics: {str(e)}\n{traceback.format_exc()}")
        raise