# app/api/v1/applications/app_store.py
from app.core.exceptions import ValidationException
from flask import Blueprint, request, g
from app.core.responses import success_response
from app.api.middleware.auth import auth_required

app_store_bp = Blueprint("app_store", __name__, url_prefix="/store")

@app_store_bp.route("/list", methods=["GET"])
@auth_required
def list_available_apps():
    """获取应用商店中可用的应用列表"""
    # 这里返回静态的应用列表信息
    available_apps = [
        {
            "app_type": "xhs_copy",
            "name": "小红书文案生成",
            "description": "快速生成符合小红书风格的内容文案和标签",
            "icon": "/static/icons/xhs_copy.png",
            "capabilities": ["文案生成", "标题生成", "标签生成"],
            "config_template": {
                "system_prompt": "你是一位专业的小红书博主，擅长编写吸引人的小红书文案。",
                "user_prompt_template": "请根据以下内容，创作一篇吸引人的小红书文案：\n{prompt}",
                "temperature": 0.7,
                "max_tokens": 2000,
                "title_length": 50,
                "content_length": 1000,
                "tags_count": 5,
                "include_emojis": True
            }
        },
  
    ]
    
    return success_response(available_apps, "获取可用应用列表成功")

@app_store_bp.route("/get", methods=["POST"])
@auth_required
def get_app_details():
    """获取特定应用类型的详细信息"""
    # 验证请求数据
    data = request.get_json()
    if not data or "app_type" not in data:
        raise ValidationException("缺少必填参数: app_type")
    
    app_type = data["app_type"]
    
    # 应用详情映射
    app_details = {
        "xhs_copy": {
            "app_type": "xhs_copy",
            "name": "小红书文案生成",
            "description": "快速生成符合小红书风格的内容文案和标签",
            "icon": "/static/icons/xhs_copy.png",
            "capabilities": ["文案生成", "标题生成", "标签生成"],
            "config_template": {
                "system_prompt": "你是一位专业的小红书博主，擅长编写吸引人的小红书文案。",
                "user_prompt_template": "请根据以下内容，创作一篇吸引人的小红书文案：\n{prompt}",
                "temperature": 0.7,
                "max_tokens": 2000,
                "title_length": 50,
                "content_length": 1000,
                "tags_count": 5,
                "include_emojis": True
            },
            "supported_models": {
                "OpenAI": ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
                "Claude": ["claude-3-opus-20240229", "claude-3-sonnet-20240229"],
                "Gemini": ["gemini-pro"],
                "Baidu": ["ernie-bot-4", "ernie-bot"],
                "Aliyun": ["qwen-max", "qwen-plus"],
                "Tencent": ["hunyuan"]
            },
            "instructions": "配置完成后，使用生成的App Key在您的应用中调用API接口即可生成小红书文案。请确保您已经配置了有效的LLM服务。",
            "example_prompts": [
                "分享一个复古风穿搭，搭配了牛仔外套和长裙。",
                "介绍我新买的咖啡机，说说它的特点和使用体验。",
                "分享一个周末旅行的经历，去了附近的一个小镇。"
            ]
        },

    }
    
    if app_type not in app_details:
        return success_response(None, "未找到指定应用类型的详情")
    
    return success_response(app_details[app_type], "获取应用详情成功")