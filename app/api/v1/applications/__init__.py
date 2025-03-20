# app/api/v1/ai_apps/__init__.py
from flask import Blueprint
from app.api.v1.applications.xiaohongshu import xiaohongshu_bp
from app.api.v1.applications.image_classification import image_classification_bp
# 导入其他应用蓝图

ai_apps_bp = Blueprint("applications", __name__, url_prefix="/applications")

# 注册各应用类型蓝图
ai_apps_bp.register_blueprint(xiaohongshu_bp)
ai_apps_bp.register_blueprint(image_classification_bp)
# 注册其他应用蓝图