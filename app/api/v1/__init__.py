# app/api/v1/__init__.py
from flask import Blueprint

# 创建API v1主蓝图
api_v1_bp = Blueprint("api_v1", __name__)

# 导入认证相关蓝图
from app.api.v1.auth.auth import auth_bp

# 导入基础能力蓝图
from app.api.v1.foundation.forbidden_words import forbidden_words_bp
from app.api.v1.foundation.llm import llm_providers_bp, llm_models_bp
from app.api.v1.foundation.user_llm_config import user_llm_config_bp

# 导入应用相关蓝图
from app.api.v1.applications.xhs_copy import xhs_copy_bp
from app.api.v1.applications.user_app import user_app_bp
from app.api.v1.applications.app_store import app_store_bp


# 导入外部接口相关蓝图
from app.api.v1.external.foundation.forbidden_words import external_forbidden_words_bp
from app.api.v1.external.applications.xhs_copy import external_xhs_copy_bp

# 注册认证蓝图
api_v1_bp.register_blueprint(auth_bp, url_prefix="/auth")



# 创建并注册基础能力蓝图
foundation_bp = Blueprint("foundation", __name__, url_prefix="/foundation")
foundation_bp.register_blueprint(forbidden_words_bp)
foundation_bp.register_blueprint(llm_providers_bp, url_prefix="/llm_providers")
foundation_bp.register_blueprint(llm_models_bp, url_prefix="/llm_models")
foundation_bp.register_blueprint(user_llm_config_bp, url_prefix="/user_llm_configs")
api_v1_bp.register_blueprint(foundation_bp)


# 创建并注册应用蓝图
applications_bp = Blueprint("applications", __name__, url_prefix="/applications")

# 注册各应用类型蓝图
applications_bp.register_blueprint(xhs_copy_bp, url_prefix="/xhs_copy")
applications_bp.register_blueprint(user_app_bp, url_prefix="/user_app")
applications_bp.register_blueprint(app_store_bp, url_prefix="/store")

# 注册应用蓝图到主蓝图
api_v1_bp.register_blueprint(applications_bp)

# 创建并注册外部接口蓝图
external_bp = Blueprint("external", __name__, url_prefix="/external")

# 外部接口的基础能力蓝图
external_foundation_bp = Blueprint(
    "external_foundation", __name__, url_prefix="/foundation"
)
external_foundation_bp.register_blueprint(external_forbidden_words_bp)
external_bp.register_blueprint(external_foundation_bp)

# 外部接口的应用蓝图
external_applications_bp = Blueprint(
    "external_applications", __name__, url_prefix="/applications"
)
external_applications_bp.register_blueprint(
    external_xhs_copy_bp, url_prefix="/xhs_copy"
)
external_bp.register_blueprint(external_applications_bp)

# 注册外部接口蓝图到主蓝图
api_v1_bp.register_blueprint(external_bp)

