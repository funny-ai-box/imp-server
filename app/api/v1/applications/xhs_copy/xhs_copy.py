# app/api/v1/endpoints/xhs_copy.py
from flask import Blueprint, request, g, current_app
from app.core.responses import success_response
from app.core.exceptions import ValidationException
from app.domains.applications.services.xhs_copy_service import (
    XhsCopyConfigService,
    XhsCopyGenerationService,
    XhsCopyTestService
)
from app.infrastructure.database.repositories.xhs_copy_repository import (
    XhsCopyConfigRepository,
    XhsCopyGenerationRepository,
    XhsCopyTestRepository
)
from app.infrastructure.database.repositories.llm_repository import LLMProviderRepository, LLMModelRepository, LLMProviderRepository

from app.infrastructure.database.repositories.application_repository import ApplicationRepository
from app.api.middleware.auth import auth_required
from app.api.middleware.app_key_auth import app_key_required

xhs_copy_bp = Blueprint("xhs_copy", __name__)


# 文案生成接口
@xhs_copy_bp.route("/generate", methods=["POST"])
@auth_required
def generate_content():
    """生成小红书文案（用户接口）"""
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
    
    # 获取IP和用户代理
    ip_address = request.remote_addr
    user_agent = request.headers.get("User-Agent")
    
    # 初始化存储库和服务
    db_session = g.db_session
    generation_repo = XhsCopyGenerationRepository(db_session)
    config_repo = XhsCopyConfigRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    generation_service = XhsCopyGenerationService(
        generation_repo, config_repo, provider_repo, model_repo
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


@xhs_copy_bp.route("/generations", methods=["GET"])
@auth_required
def list_generations():
    """获取小红书文案生成历史记录"""
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
    generation_service = XhsCopyGenerationService(
        generation_repo, config_repo, provider_repo, model_repo
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

