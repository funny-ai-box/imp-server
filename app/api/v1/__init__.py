from flask import Blueprint

# 创建API v1蓝图
api_v1_bp = Blueprint('api_v1', __name__)

# 导入路由
from app.api.v1 import auth, models, knowledge_bases, applications
from app.api.v1.endpoints import xiaohongshu, image_classification, comment_analysis
