# app/api/v1/applications/__init__.py (更新)
from flask import Blueprint
from app.api.v1.applications.user_app import user_app_bp
from app.api.v1.applications.app_store import app_store_bp
from app.api.v1.applications.xhs_copy import xhs_copy_bp

ai_apps_bp = Blueprint("applications", __name__, url_prefix="/applications")

# 注册应用管理蓝图
ai_apps_bp.register_blueprint(user_app_bp)
ai_apps_bp.register_blueprint(app_store_bp)

# 注册各应用类型蓝图
ai_apps_bp.register_blueprint(xhs_copy_bp)
