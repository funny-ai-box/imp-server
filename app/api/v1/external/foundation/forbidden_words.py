# app/api/v1/external/forbidden_words.py
from flask import Blueprint, request, g
from app.core.responses import success_response
from app.core.exceptions import ValidationException
from app.domains.foundation.services.forbidden_words_service import ForbiddenWordsService
from app.infrastructure.database.repositories.forbidden_words_repository import ForbiddenWordsRepository
from app.api.middleware.app_key_auth import app_key_required

external_forbidden_words_bp = Blueprint("external_forbidden_words", __name__, url_prefix="/forbidden_words")

@external_forbidden_words_bp.route("/list", methods=["GET"])
@app_key_required
def get_forbidden_words_list():
    """获取违禁词列表（外部调用）"""
    # 获取查询参数
    application = request.args.get("application", "xiaohongshu")  # 默认为小红书应用
    
    # 初始化存储库和服务
    db_session = g.db_session
    forbidden_words_repo = ForbiddenWordsRepository(db_session)
    forbidden_words_service = ForbiddenWordsService(forbidden_words_repo)
    
    # 获取违禁词
    words = forbidden_words_service.get_all_words(application)
    
    # 简化输出，只返回词汇本身
    simplified_words = [word["word"] for word in words]
    
    return success_response(simplified_words, "获取违禁词列表成功")


@external_forbidden_words_bp.route("/check", methods=["POST"])
@app_key_required
def check_content():
    """检查内容是否包含违禁词（外部调用）"""
    # 验证请求数据
    data = request.get_json()
    if not data or "content" not in data:
        raise ValidationException("内容不能为空")
    
    content = data.get("content")
    application = data.get("application", "xiaohongshu")  # 默认为小红书应用
    
    # 初始化存储库和服务
    db_session = g.db_session
    forbidden_words_repo = ForbiddenWordsRepository(db_session)
    forbidden_words_service = ForbiddenWordsService(forbidden_words_repo)
    
    # 检查内容
    passed, detected_words = forbidden_words_service.check_content(content, application)
    
    return success_response({
        "passed": passed,
        "detected_words": detected_words
    }, "内容检查完成")


@external_forbidden_words_bp.route("/prompt", methods=["GET"])
@app_key_required
def get_ai_prompt():
    """获取给AI的提示词，告知违禁词列表（外部调用）"""
    # 获取查询参数
    application = request.args.get("application", "xiaohongshu")  # 默认为小红书应用
    
    # 初始化存储库和服务
    db_session = g.db_session
    forbidden_words_repo = ForbiddenWordsRepository(db_session)
    forbidden_words_service = ForbiddenWordsService(forbidden_words_repo)
    
    # 获取提示词
    prompt = forbidden_words_service.get_prompt_for_ai(application)
    
    return success_response({
        "prompt": prompt
    }, "获取AI提示词成功")