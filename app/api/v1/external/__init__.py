from flask import Blueprint
from app.api.v1.external.applications.xhs_copy import external_xhs_copy_bp
from app.api.v1.external.applications.image_classify import external_image_classify_bp
from app.api.v1.external.foundation.forbidden_words import external_forbidden_words_bp
external_bp = Blueprint("external", __name__, url_prefix="/external")

# 外部调用蓝图
external_apps_bp = Blueprint("external_applications", __name__, url_prefix="/applications")
external_apps_bp.register_blueprint(external_xhs_copy_bp)
external_apps_bp.register_blueprint(external_image_classify_bp)

# 外部调用基础能力蓝图
external_foundation_bp = Blueprint("external_foundation", __name__, url_prefix="/foundation")
external_foundation_bp.register_blueprint(external_forbidden_words_bp)
external_apps_bp.register_blueprint(external_foundation_bp)

external_bp.register_blueprint(external_apps_bp)