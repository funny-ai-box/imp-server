# app/api/v1/content_management/forbidden_words.py
from flask import Blueprint, request, g
from app.core.responses import success_response
from app.core.exceptions import ValidationException
from app.domains.foundation.services.forbidden_words_service import ForbiddenWordsService
from app.infrastructure.database.repositories.forbidden_words_repository import ForbiddenWordsRepository
from app.api.middleware.auth import auth_required, admin_required

forbidden_words_bp = Blueprint("forbidden_words", __name__, url_prefix="/forbidden_words")

@forbidden_words_bp.route("", methods=["GET"])
@admin_required  # 仅管理员可访问
def get_forbidden_words():
    """获取违禁词列表"""
    # 获取查询参数
    application = request.args.get("application", "xiaohongshu")  # 默认为小红书应用
    query = request.args.get("query")
    
    # 初始化存储库和服务
    db_session = g.db_session
    forbidden_words_repo = ForbiddenWordsRepository(db_session)
    forbidden_words_service = ForbiddenWordsService(forbidden_words_repo)
    
    # 搜索或获取违禁词
    if query:
        words = forbidden_words_service.search_words(query, application)
    else:
        words = forbidden_words_service.get_all_words(application)
    
    return success_response(words, "获取违禁词列表成功")


@forbidden_words_bp.route("", methods=["POST"])
@admin_required
def add_forbidden_word():
    """添加违禁词"""
    # 验证请求数据
    data = request.get_json()
    if not data:
        raise ValidationException("请求数据不能为空")
    
    if "word" not in data:
        raise ValidationException("违禁词不能为空")
    
    if "application" not in data:
        raise ValidationException("应用场景不能为空")
    
    # 初始化存储库和服务
    db_session = g.db_session
    forbidden_words_repo = ForbiddenWordsRepository(db_session)
    forbidden_words_service = ForbiddenWordsService(forbidden_words_repo)
    
    # 添加违禁词
    admin_id = g.user_id
    word = forbidden_words_service.add_word(data, admin_id)
    
    return success_response(word, "添加违禁词成功")


@forbidden_words_bp.route("/<int:word_id>", methods=["PUT"])
@admin_required
def update_forbidden_word(word_id):
    """更新违禁词"""
    # 验证请求数据
    data = request.get_json()
    if not data:
        raise ValidationException("请求数据不能为空")
    
    # 初始化存储库和服务
    db_session = g.db_session
    forbidden_words_repo = ForbiddenWordsRepository(db_session)
    forbidden_words_service = ForbiddenWordsService(forbidden_words_repo)
    
    # 更新违禁词
    word = forbidden_words_service.update_word(word_id, data)
    
    return success_response(word, "更新违禁词成功")


@forbidden_words_bp.route("/<int:word_id>", methods=["DELETE"])
@admin_required
def delete_forbidden_word(word_id):
    """删除违禁词"""
    # 初始化存储库和服务
    db_session = g.db_session
    forbidden_words_repo = ForbiddenWordsRepository(db_session)
    forbidden_words_service = ForbiddenWordsService(forbidden_words_repo)
    
    # 删除违禁词
    forbidden_words_service.delete_word(word_id)
    
    return success_response(None, "删除违禁词成功")


@forbidden_words_bp.route("/logs", methods=["GET"])
@admin_required
def get_forbidden_word_logs():
    """获取违禁词检测日志"""
    # 获取查询参数
    application = request.args.get("application", "xiaohongshu")  # 默认为小红书应用
    limit = int(request.args.get("limit", 100))
    
    # 初始化存储库和服务
    db_session = g.db_session
    forbidden_words_repo = ForbiddenWordsRepository(db_session)
    forbidden_words_service = ForbiddenWordsService(forbidden_words_repo)
    
    # 获取日志
    logs = forbidden_words_service.get_logs(application, limit)
    
    return success_response(logs, "获取违禁词检测日志成功")


@forbidden_words_bp.route("/check", methods=["POST"])
@admin_required
def check_content():
    """检查内容是否包含违禁词（管理员工具）"""
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