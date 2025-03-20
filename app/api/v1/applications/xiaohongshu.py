# app/api/v1/endpoints/xiaohongshu.py
from flask import Blueprint, request, g, current_app
from app.core.responses import success_response
from app.core.exceptions import ValidationException
from app.domains.applications.services.xiaohongshu_service import (
    XiaohongshuConfigService,
    XiaohongshuGenerationService,
    XiaohongshuTestService
)
from app.infrastructure.database.repositories.xiaohongshu_repository import (
    XiaohongshuConfigRepository,
    XiaohongshuGenerationRepository,
    XiaohongshuTestRepository
)
from app.infrastructure.database.repositories.llm_repository import LLMProviderRepository, LLMModelRepository, LLMProviderRepository

from app.infrastructure.database.repositories.application_repository import ApplicationRepository
from app.api.middleware.auth import auth_required
from app.api.middleware.app_key_auth import app_key_required

xiaohongshu_bp = Blueprint("xiaohongshu", __name__)

# 配置管理接口
@xiaohongshu_bp.route("/configs", methods=["GET"])
@auth_required
def list_configs():
    """获取小红书应用配置列表"""
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = XiaohongshuConfigRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    config_service = XiaohongshuConfigService(config_repo, provider_repo, model_repo)
    
    # 获取配置列表
    configs = config_service.get_all_configs(user_id)
    
    return success_response(configs, "获取小红书配置列表成功")


@xiaohongshu_bp.route("/configs/<int:config_id>", methods=["GET"])
@auth_required
def get_config(config_id):
    """获取特定小红书应用配置"""
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = XiaohongshuConfigRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    config_service = XiaohongshuConfigService(config_repo, provider_repo, model_repo)
    
    # 获取配置
    config = config_service.get_config(config_id, user_id)
    
    return success_response(config, "获取小红书配置成功")


@xiaohongshu_bp.route("/configs/default", methods=["GET"])
@auth_required
def get_default_config():
    """获取默认小红书应用配置"""
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = XiaohongshuConfigRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    config_service = XiaohongshuConfigService(config_repo, provider_repo, model_repo)
    
    # 获取默认配置
    config = config_service.get_default_config(user_id)
    
    if not config:
        return success_response(None, "未找到默认配置")
    
    return success_response(config, "获取默认小红书配置成功")


@xiaohongshu_bp.route("/configs", methods=["POST"])
@auth_required
def create_config():
    """创建小红书应用配置"""
    user_id = g.user_id
    
    # 验证请求数据
    data = request.get_json()
    if not data:
        raise ValidationException("请求数据不能为空")
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = XiaohongshuConfigRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    config_service = XiaohongshuConfigService(config_repo, provider_repo, model_repo)
    
    # 创建配置
    config = config_service.create_config(data, user_id)
    
    return success_response(config, "创建小红书配置成功")


@xiaohongshu_bp.route("/configs/<int:config_id>", methods=["PUT"])
@auth_required
def update_config(config_id):
    """更新小红书应用配置"""
    user_id = g.user_id
    
    # 验证请求数据
    data = request.get_json()
    if not data:
        raise ValidationException("请求数据不能为空")
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = XiaohongshuConfigRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    config_service = XiaohongshuConfigService(config_repo, provider_repo, model_repo)
    
    # 更新配置
    config = config_service.update_config(config_id, data, user_id)
    
    return success_response(config, "更新小红书配置成功")


@xiaohongshu_bp.route("/configs/<int:config_id>", methods=["DELETE"])
@auth_required
def delete_config(config_id):
    """删除小红书应用配置"""
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = XiaohongshuConfigRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    config_service = XiaohongshuConfigService(config_repo, provider_repo, model_repo)
    
    # 删除配置
    config_service.delete_config(config_id, user_id)
    
    return success_response(None, "删除小红书配置成功")


@xiaohongshu_bp.route("/configs/<int:config_id>/set_default", methods=["POST"])
@auth_required
def set_default_config(config_id):
    """设置默认小红书应用配置"""
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = XiaohongshuConfigRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    config_service = XiaohongshuConfigService(config_repo, provider_repo, model_repo)
    
    # 设置默认配置
    config = config_service.set_default_config(config_id, user_id)
    
    return success_response(config, "设置默认小红书配置成功")


# 文案生成接口
@xiaohongshu_bp.route("/generate", methods=["POST"])
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
    generation_repo = XiaohongshuGenerationRepository(db_session)
    config_repo = XiaohongshuConfigRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    generation_service = XiaohongshuGenerationService(
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


@xiaohongshu_bp.route("/generations", methods=["GET"])
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
    generation_repo = XiaohongshuGenerationRepository(db_session)
    config_repo = XiaohongshuConfigRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    generation_service = XiaohongshuGenerationService(
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


@xiaohongshu_bp.route("/generations/<int:generation_id>", methods=["GET"])
@auth_required
def get_generation(generation_id):
    """获取特定小红书文案生成记录"""
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    generation_repo = XiaohongshuGenerationRepository(db_session)
    config_repo = XiaohongshuConfigRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    generation_service = XiaohongshuGenerationService(
        generation_repo, config_repo, provider_repo, model_repo
    )
    
    # 获取生成记录
    generation = generation_service.get_generation(generation_id, user_id)
    
    return success_response(generation, "获取小红书文案生成记录成功")


@xiaohongshu_bp.route("/generations/<int:generation_id>/rate", methods=["POST"])
@auth_required
def rate_generation(generation_id):
    """对小红书文案生成结果评分"""
    user_id = g.user_id
    
    # 验证请求数据
    data = request.get_json()
    if not data:
        raise ValidationException("请求数据不能为空")
    
    # 提取数据
    rating = data.get("rating")
    if rating is None:
        raise ValidationException("评分不能为空")
    
    feedback = data.get("feedback")
    
    # 初始化存储库和服务
    db_session = g.db_session
    generation_repo = XiaohongshuGenerationRepository(db_session)
    config_repo = XiaohongshuConfigRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    generation_service = XiaohongshuGenerationService(
        generation_repo, config_repo, provider_repo, model_repo
    )
    
    # 评分生成记录
    generation = generation_service.rate_generation(
        generation_id=generation_id,
        user_id=user_id,
        rating=rating,
        feedback=feedback
    )
    
    return success_response(generation, "评分小红书文案生成结果成功")


@xiaohongshu_bp.route("/generations/<int:generation_id>", methods=["DELETE"])
@auth_required
def delete_generation(generation_id):
    """删除小红书文案生成记录"""
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    generation_repo = XiaohongshuGenerationRepository(db_session)
    config_repo = XiaohongshuConfigRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    generation_service = XiaohongshuGenerationService(
        generation_repo, config_repo, provider_repo, model_repo
    )
    
    # 删除生成记录
    generation_service.delete_generation(generation_id, user_id)
    
    return success_response(None, "删除小红书文案生成记录成功")


@xiaohongshu_bp.route("/statistics", methods=["GET"])
@auth_required
def get_statistics():
    """获取小红书文案生成统计数据"""
    user_id = g.user_id
    
    # 获取时间范围参数
    days = int(request.args.get("days", 30))
    
    # 初始化存储库和服务
    db_session = g.db_session
    generation_repo = XiaohongshuGenerationRepository(db_session)
    config_repo = XiaohongshuConfigRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    generation_service = XiaohongshuGenerationService(
        generation_repo, config_repo, provider_repo, model_repo
    )
    
    # 获取统计数据
    statistics = generation_service.get_statistics(user_id, days)
    
    return success_response(statistics, "获取小红书文案生成统计数据成功")


# 测试接口
@xiaohongshu_bp.route("/tests", methods=["GET"])
@auth_required
def list_tests():
    """获取小红书文案测试历史记录"""
    user_id = g.user_id
    
    # 获取分页参数
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    
    # 初始化存储库和服务
    db_session = g.db_session
    test_repo = XiaohongshuTestRepository(db_session)
    config_repo = XiaohongshuConfigRepository(db_session)
    generation_repo = XiaohongshuGenerationRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    
    generation_service = XiaohongshuGenerationService(
        generation_repo, config_repo, provider_repo, model_repo
    )
    
    test_service = XiaohongshuTestService(test_repo, generation_service, config_repo)
    
    # 获取测试记录
    tests, total = test_service.get_all_tests(
        user_id=user_id,
        page=page,
        per_page=per_page
    )
    
    return success_response({
        "items": tests,
        "total": total,
        "page": page,
        "per_page": per_page
    }, "获取小红书文案测试历史记录成功")


@xiaohongshu_bp.route("/tests/<int:test_id>", methods=["GET"])
@auth_required
def get_test(test_id):
    """获取特定小红书文案测试记录"""
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    test_repo = XiaohongshuTestRepository(db_session)
    config_repo = XiaohongshuConfigRepository(db_session)
    generation_repo = XiaohongshuGenerationRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    
    generation_service = XiaohongshuGenerationService(
        generation_repo, config_repo, provider_repo, model_repo
    )
    
    test_service = XiaohongshuTestService(test_repo, generation_service, config_repo)
    
    # 获取测试记录
    test = test_service.get_test(test_id, user_id)
    
    return success_response(test, "获取小红书文案测试记录成功")


@xiaohongshu_bp.route("/tests", methods=["POST"])
@auth_required
def create_test():
    """创建小红书文案配置对比测试"""
    user_id = g.user_id
    
    # 验证请求数据
    data = request.get_json()
    if not data:
        raise ValidationException("请求数据不能为空")
    
    # 提取数据
    test_name = data.get("test_name")
    prompt = data.get("prompt")
    image_urls = data.get("image_urls", [])
    config_ids = data.get("config_ids", [])
    
    if not test_name:
        raise ValidationException("测试名称不能为空")
    
    if not prompt:
        raise ValidationException("提示词不能为空")
    
    if not config_ids or len(config_ids) < 2:
        raise ValidationException("至少需要两个配置进行对比")
    
    # 初始化存储库和服务
    db_session = g.db_session
    test_repo = XiaohongshuTestRepository(db_session)
    config_repo = XiaohongshuConfigRepository(db_session)
    generation_repo = XiaohongshuGenerationRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    
    generation_service = XiaohongshuGenerationService(
        generation_repo, config_repo, provider_repo, model_repo
    )
    
    test_service = XiaohongshuTestService(test_repo, generation_service, config_repo)
    
    # 创建测试
    test = test_service.create_test(
        test_name=test_name,
        prompt=prompt,
        image_urls=image_urls,
        config_ids=config_ids,
        user_id=user_id
    )
    
    return success_response(test, "创建小红书文案配置对比测试成功")


@xiaohongshu_bp.route("/tests/<int:test_id>/select_winner", methods=["POST"])
@auth_required
def select_winner(test_id):
    """选择测试获胜配置"""
    user_id = g.user_id
    
    # 验证请求数据
    data = request.get_json()
    if not data:
        raise ValidationException("请求数据不能为空")
    
    # 提取数据
    winner_config_id = data.get("winner_config_id")
    if not winner_config_id:
        raise ValidationException("获胜配置ID不能为空")
    
    # 初始化存储库和服务
    db_session = g.db_session
    test_repo = XiaohongshuTestRepository(db_session)
    config_repo = XiaohongshuConfigRepository(db_session)
    generation_repo = XiaohongshuGenerationRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    
    generation_service = XiaohongshuGenerationService(
        generation_repo, config_repo, provider_repo, model_repo
    )
    
    test_service = XiaohongshuTestService(test_repo, generation_service, config_repo)
    
    # 选择获胜配置
    test = test_service.select_winner(test_id, winner_config_id, user_id)
    
    return success_response(test, "选择测试获胜配置成功")


@xiaohongshu_bp.route("/tests/<int:test_id>", methods=["DELETE"])
@auth_required
def delete_test(test_id):
    """删除小红书文案测试记录"""
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    test_repo = XiaohongshuTestRepository(db_session)
    config_repo = XiaohongshuConfigRepository(db_session)
    generation_repo = XiaohongshuGenerationRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    
    generation_service = XiaohongshuGenerationService(
        generation_repo, config_repo, provider_repo, model_repo
    )
    
    test_service = XiaohongshuTestService(test_repo, generation_service, config_repo)
    
    # 删除测试记录
    test_service.delete_test(test_id, user_id)
    
    return success_response(None, "删除小红书文案测试记录成功")


# 外部应用调用接口
@xiaohongshu_bp.route("/external/generate", methods=["POST"])
@app_key_required
def external_generate():
    """生成小红书文案（外部应用调用）"""
    # 获取应用和用户信息
    application = g.application
    user_id = g.user_id
    app_id = application.get("id")
    
    # 验证请求数据
    data = request.get_json()
    if not data:
        raise ValidationException("请求数据不能为空")
    
    # 提取数据
    prompt = data.get("prompt")
    if not prompt:
        raise ValidationException("提示词不能为空")
    
    image_urls = data.get("image_urls", [])
    config_id = data.get("config_id")  # 可选，如果不提供则使用默认配置
    
    # 获取IP和用户代理
    ip_address = request.remote_addr
    user_agent = request.headers.get("User-Agent")
    
    # 初始化存储库和服务
    db_session = g.db_session
    generation_repo = XiaohongshuGenerationRepository(db_session)
    config_repo = XiaohongshuConfigRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    generation_service = XiaohongshuGenerationService(
        generation_repo, config_repo, provider_repo, model_repo
    )
    
    # 生成文案
    generation = generation_service.create_generation(
        prompt=prompt,
        image_urls=image_urls,
        config_id=config_id,
        app_id=app_id,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return success_response(generation, "生成小红书文案成功")


@xiaohongshu_bp.route("/external/config", methods=["GET"])
@app_key_required
def external_get_config():
    """获取小红书应用配置（外部应用调用）"""
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = XiaohongshuConfigRepository(db_session)
    provider_repo = LLMProviderRepository(db_session)
    model_repo = LLMModelRepository(db_session)
    config_service = XiaohongshuConfigService(config_repo, provider_repo, model_repo)
    
    # 获取默认配置
    config = config_service.get_default_config(user_id)
    
    if not config:
        return success_response(None, "未找到默认配置")
    
    # 简化配置信息，只返回必要字段
    simplified_config = {
        "id": config["id"],
        "name": config["name"],
        "title_length": config["title_length"],
        "content_length": config["content_length"],
        "tags_count": config["tags_count"],
        "include_emojis": config["include_emojis"]
    }
    
    return success_response(simplified_config, "获取小红书配置成功")