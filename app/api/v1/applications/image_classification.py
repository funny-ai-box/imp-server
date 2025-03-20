# app/api/v1/ai_apps/image_classification.py
from flask import Blueprint, request, g, current_app
from app.core.responses import success_response
from app.core.exceptions import ValidationException
from app.domains.applications.services.image_classification_service import ImageClassificationService
from app.infrastructure.database.repositories.image_classification_repository import (
    ImageClassificationConfigRepository,
    ImageClassificationRepository
)
from app.infrastructure.database.repositories.llm_repository import AIProviderRepository
from app.infrastructure.database.repositories.llm_model_repository import AIModelRepository
from app.api.middleware.auth import auth_required
from app.api.middleware.app_key_auth import app_key_required

image_classification_bp = Blueprint("image_classification", __name__, url_prefix="/image_classification")

# 配置管理接口
@image_classification_bp.route("/configs", methods=["GET"])
@auth_required
def list_configs():
    """获取图片分类应用配置列表"""
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = ImageClassificationConfigRepository(db_session)
    provider_repo = AIProviderRepository(db_session)
    model_repo = AIModelRepository(db_session)
    classification_repo = ImageClassificationRepository(db_session)
    service = ImageClassificationService(classification_repo, config_repo, provider_repo, model_repo)
    
    # 获取配置列表
    configs = service.get_all_configs(user_id)
    
    return success_response(configs, "获取图片分类配置列表成功")


@image_classification_bp.route("/configs/<int:config_id>", methods=["GET"])
@auth_required
def get_config(config_id):
    """获取特定图片分类应用配置"""
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = ImageClassificationConfigRepository(db_session)
    provider_repo = AIProviderRepository(db_session)
    model_repo = AIModelRepository(db_session)
    classification_repo = ImageClassificationRepository(db_session)
    service = ImageClassificationService(classification_repo, config_repo, provider_repo, model_repo)
    
    # 获取配置
    config = service.get_config(config_id, user_id)
    
    return success_response(config, "获取图片分类配置成功")


@image_classification_bp.route("/configs/default", methods=["GET"])
@auth_required
def get_default_config():
    """获取默认图片分类应用配置"""
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = ImageClassificationConfigRepository(db_session)
    provider_repo = AIProviderRepository(db_session)
    model_repo = AIModelRepository(db_session)
    classification_repo = ImageClassificationRepository(db_session)
    service = ImageClassificationService(classification_repo, config_repo, provider_repo, model_repo)
    
    # 获取默认配置
    config = service.get_default_config(user_id)
    
    if not config:
        return success_response(None, "未找到默认配置")
    
    return success_response(config, "获取默认图片分类配置成功")


@image_classification_bp.route("/configs", methods=["POST"])
@auth_required
def create_config():
    """创建图片分类应用配置"""
    user_id = g.user_id
    
    # 验证请求数据
    data = request.get_json()
    if not data:
        raise ValidationException("请求数据不能为空")
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = ImageClassificationConfigRepository(db_session)
    provider_repo = AIProviderRepository(db_session)
    model_repo = AIModelRepository(db_session)
    classification_repo = ImageClassificationRepository(db_session)
    service = ImageClassificationService(classification_repo, config_repo, provider_repo, model_repo)
    
    # 创建配置
    config = service.create_config(data, user_id)
    
    return success_response(config, "创建图片分类配置成功")


@image_classification_bp.route("/configs/<int:config_id>", methods=["PUT"])
@auth_required
def update_config(config_id):
    """更新图片分类应用配置"""
    user_id = g.user_id
    
    # 验证请求数据
    data = request.get_json()
    if not data:
        raise ValidationException("请求数据不能为空")
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = ImageClassificationConfigRepository(db_session)
    provider_repo = AIProviderRepository(db_session)
    model_repo = AIModelRepository(db_session)
    classification_repo = ImageClassificationRepository(db_session)
    service = ImageClassificationService(classification_repo, config_repo, provider_repo, model_repo)
    
    # 更新配置
    config = service.update_config(config_id, data, user_id)
    
    return success_response(config, "更新图片分类配置成功")


@image_classification_bp.route("/configs/<int:config_id>", methods=["DELETE"])
@auth_required
def delete_config(config_id):
    """删除图片分类应用配置"""
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = ImageClassificationConfigRepository(db_session)
    provider_repo = AIProviderRepository(db_session)
    model_repo = AIModelRepository(db_session)
    classification_repo = ImageClassificationRepository(db_session)
    service = ImageClassificationService(classification_repo, config_repo, provider_repo, model_repo)
    
    # 删除配置
    service.delete_config(config_id, user_id)
    
    return success_response(None, "删除图片分类配置成功")


@image_classification_bp.route("/configs/<int:config_id>/set_default", methods=["POST"])
@auth_required
def set_default_config(config_id):
    """设置默认图片分类应用配置"""
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = ImageClassificationConfigRepository(db_session)
    provider_repo = AIProviderRepository(db_session)
    model_repo = AIModelRepository(db_session)
    classification_repo = ImageClassificationRepository(db_session)
    service = ImageClassificationService(classification_repo, config_repo, provider_repo, model_repo)
    
    # 设置默认配置
    config = service.set_default_config(config_id, user_id)
    
    return success_response(config, "设置默认图片分类配置成功")


# 图片分类接口
@image_classification_bp.route("/classify", methods=["POST"])
@auth_required
def classify_image():
    """图片分类（用户接口）"""
    user_id = g.user_id
    
    # 验证请求数据
    data = request.get_json()
    if not data:
        raise ValidationException("请求数据不能为空")
    
    # 提取数据
    image_url = data.get("image_url")
    if not image_url:
        raise ValidationException("图片URL不能为空")
    
    categories = data.get("categories", [])
    if not categories:
        raise ValidationException("分类类别不能为空")
    
    config_id = data.get("config_id")
    
    # 获取IP和用户代理
    ip_address = request.remote_addr
    user_agent = request.headers.get("User-Agent")
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = ImageClassificationConfigRepository(db_session)
    provider_repo = AIProviderRepository(db_session)
    model_repo = AIModelRepository(db_session)
    classification_repo = ImageClassificationRepository(db_session)
    service = ImageClassificationService(classification_repo, config_repo, provider_repo, model_repo)
    
    # 执行图片分类
    classification = service.classify_image(
        image_url=image_url,
        categories=categories,
        config_id=config_id,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return success_response(classification, "图片分类成功")


@image_classification_bp.route("/history", methods=["GET"])
@auth_required
def list_classifications():
    """获取图片分类历史记录"""
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
    config_repo = ImageClassificationConfigRepository(db_session)
    provider_repo = AIProviderRepository(db_session)
    model_repo = AIModelRepository(db_session)
    classification_repo = ImageClassificationRepository(db_session)
    service = ImageClassificationService(classification_repo, config_repo, provider_repo, model_repo)
    
    # 获取分类记录
    classifications, total = service.get_all_classifications(
        user_id=user_id,
        page=page,
        per_page=per_page,
        **filters
    )
    
    return success_response({
        "items": classifications,
        "total": total,
        "page": page,
        "per_page": per_page
    }, "获取图片分类历史记录成功")


@image_classification_bp.route("/history/<int:classification_id>", methods=["GET"])
@auth_required
def get_classification(classification_id):
    """获取特定图片分类记录"""
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = ImageClassificationConfigRepository(db_session)
    provider_repo = AIProviderRepository(db_session)
    model_repo = AIModelRepository(db_session)
    classification_repo = ImageClassificationRepository(db_session)
    service = ImageClassificationService(classification_repo, config_repo, provider_repo, model_repo)
    
    # 获取分类记录
    classification = service.get_classification(classification_id, user_id)
    
    return success_response(classification, "获取图片分类记录成功")


@image_classification_bp.route("/history/<int:classification_id>/rate", methods=["POST"])
@auth_required
def rate_classification(classification_id):
    """对图片分类结果评分"""
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
    config_repo = ImageClassificationConfigRepository(db_session)
    provider_repo = AIProviderRepository(db_session)
    model_repo = AIModelRepository(db_session)
    classification_repo = ImageClassificationRepository(db_session)
    service = ImageClassificationService(classification_repo, config_repo, provider_repo, model_repo)
    
    # 评分分类记录
    classification = service.rate_classification(
        classification_id=classification_id,
        user_id=user_id,
        rating=rating,
        feedback=feedback
    )
    
    return success_response(classification, "评分图片分类结果成功")


@image_classification_bp.route("/history/<int:classification_id>", methods=["DELETE"])
@auth_required
def delete_classification(classification_id):
    """删除图片分类记录"""
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = ImageClassificationConfigRepository(db_session)
    provider_repo = AIProviderRepository(db_session)
    model_repo = AIModelRepository(db_session)
    classification_repo = ImageClassificationRepository(db_session)
    service = ImageClassificationService(classification_repo, config_repo, provider_repo, model_repo)
    
    # 删除分类记录
    service.delete_classification(classification_id, user_id)
    
    return success_response(None, "删除图片分类记录成功")


@image_classification_bp.route("/statistics", methods=["GET"])
@auth_required
def get_statistics():
    """获取图片分类统计数据"""
    user_id = g.user_id
    
    # 获取时间范围参数
    days = int(request.args.get("days", 30))
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = ImageClassificationConfigRepository(db_session)
    provider_repo = AIProviderRepository(db_session)
    model_repo = AIModelRepository(db_session)
    classification_repo = ImageClassificationRepository(db_session)
    service = ImageClassificationService(classification_repo, config_repo, provider_repo, model_repo)
    
    # 获取统计数据
    statistics = service.get_statistics(user_id, days)
    
    return success_response(statistics, "获取图片分类统计数据成功")


# 外部应用调用接口
@image_classification_bp.route("/external/classify", methods=["POST"])
@app_key_required
def external_classify():
    """图片分类（外部应用调用）"""
    # 获取应用和用户信息
    application = g.application
    user_id = g.user_id
    app_id = application.get("id")
    
    # 验证请求数据
    data = request.get_json()
    if not data:
        raise ValidationException("请求数据不能为空")
    
    # 提取数据
    image_url = data.get("image_url")
    if not image_url:
        raise ValidationException("图片URL不能为空")
    
    categories = data.get("categories", [])
    if not categories:
        raise ValidationException("分类类别不能为空")
    
    config_id = data.get("config_id")  # 可选，如果不提供则使用默认配置
    
    # 获取IP和用户代理
    ip_address = request.remote_addr
    user_agent = request.headers.get("User-Agent")
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = ImageClassificationConfigRepository(db_session)
    provider_repo = AIProviderRepository(db_session)
    model_repo = AIModelRepository(db_session)
    classification_repo = ImageClassificationRepository(db_session)
    service = ImageClassificationService(classification_repo, config_repo, provider_repo, model_repo)
    
    # 执行图片分类
    classification = service.classify_image(
        image_url=image_url,
        categories=categories,
        config_id=config_id,
        app_id=app_id,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return success_response(classification, "图片分类成功")


@image_classification_bp.route("/external/config", methods=["GET"])
@app_key_required
def external_get_config():
    """获取图片分类应用配置（外部应用调用）"""
    user_id = g.user_id
    
    # 初始化存储库和服务
    db_session = g.db_session
    config_repo = ImageClassificationConfigRepository(db_session)
    provider_repo = AIProviderRepository(db_session)
    model_repo = AIModelRepository(db_session)
    classification_repo = ImageClassificationRepository(db_session)
    service = ImageClassificationService(classification_repo, config_repo, provider_repo, model_repo)
    
    # 获取默认配置
    config = service.get_default_config(user_id)
    
    if not config:
        return success_response(None, "未找到默认配置")
    
    # 简化配置信息，只返回必要字段
    simplified_config = {
        "id": config["id"],
        "name": config["name"],
        "confidence_threshold": config["confidence_threshold"]
    }
    
    return success_response(simplified_config, "获取图片分类配置成功")