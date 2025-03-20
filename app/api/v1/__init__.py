# app/api/v1/__init__.py
from flask import Blueprint

# 创建API v1蓝图
api_v1_bp = Blueprint("v1", __name__)

# 导入并注册蓝图模块
from app.api.v1.foundation.forbidden_words import forbidden_words_bp
from app.api.v1.external.foundation.forbidden_words import external_forbidden_words_bp
from app.api.v1.applications.xiaohongshu import xiaohongshu_bp
from app.api.v1.applications.image_classification import image_classification_bp
from app.api.v1.applications.base import applications_bp
from app.api.v1.foundation.llm import llm_providers_bp, ai_models_bp

# 注册智能应用蓝图
ai_apps_bp = Blueprint("ai_apps", __name__, url_prefix="/ai_apps")
ai_apps_bp.register_blueprint(xiaohongshu_bp)
ai_apps_bp.register_blueprint(image_classification_bp)
ai_apps_bp.register_blueprint(applications_bp, url_prefix="/base")
api_v1_bp.register_blueprint(ai_apps_bp)

# 注册基础能力蓝图
capabilities_bp = Blueprint("capabilities", __name__, url_prefix="/capabilities")
capabilities_bp.register_blueprint(forbidden_words_bp)
capabilities_bp.register_blueprint(llm_providers_bp, url_prefix="/llm_providers")
capabilities_bp.register_blueprint(ai_models_bp, url_prefix="/llm_models")
api_v1_bp.register_blueprint(capabilities_bp)

# 注册外部调用蓝图
external_bp = Blueprint("external", __name__, url_prefix="/external")

# 外部调用下的智能应用
external_ai_apps_bp = Blueprint("external_ai_apps", __name__, url_prefix="/ai_apps")
# 注册外部应用调用蓝图...
external_bp.register_blueprint(external_ai_apps_bp)

# 外部调用下的基础能力
external_capabilities_bp = Blueprint("external_capabilities", __name__, url_prefix="/capabilities")
external_capabilities_bp.register_blueprint(external_forbidden_words_bp)
external_bp.register_blueprint(external_capabilities_bp)

api_v1_bp.register_blueprint(external_bp)