# app/api/v1/external/applications/xhs_copy.py
import logging
import traceback
from flask import Blueprint, request, g
from app.core.responses import success_response
from app.core.exceptions import ValidationException, NotFoundException, APIException
from app.core.status_codes import PARAMETER_ERROR, APPLICATION_NOT_FOUND, GENERATION_FAILED
from app.domains.applications.services.xhs_copy_service import XhsCopyGenerationService
from app.infrastructure.database.repositories.user_app_repository import UserAppRepository
from app.infrastructure.database.repositories.xhs_copy_repository import XhsCopyGenerationRepository
from app.infrastructure.database.repositories.llm_repository import (
    LLMProviderRepository,
    LLMModelRepository,
    LLMProviderConfigRepository
)
from app.domains.foundation.services.forbidden_words_service import ForbiddenWordsService
from app.infrastructure.database.repositories.forbidden_words_repository import ForbiddenWordsRepository
from app.api.middleware.app_key_auth import app_key_required

logger = logging.getLogger(__name__)

external_xhs_copy_bp = Blueprint("external_xhs_copy", __name__, url_prefix="/xhs_copy")

@external_xhs_copy_bp.route("/generate", methods=["POST"])
@app_key_required
def external_generate():
    """小红书文案生成API（外部接口）"""
    try:
        # 获取app_key_auth中间件已验证的应用和用户信息
        app_key = g.app_key
        user_id = g.user_id
        app = g.app

        # 验证应用类型和发布状态
        if app.app_type != "xhs_copy":
            raise ValidationException("该应用密钥不属于小红书文案生成应用", PARAMETER_ERROR)

        if not app.published or not app.published_config:
            raise ValidationException("该应用未发布配置", PARAMETER_ERROR)

        # 验证请求数据
        data = request.get_json()
        if not data:
            raise ValidationException("请求数据不能为空", PARAMETER_ERROR)

        # 提取关键参数
        prompt = data.get("prompt")
        if not prompt:
            raise ValidationException("提示词不能为空", PARAMETER_ERROR)

        # 获取其他可选参数
        image_urls = data.get("image_urls", [])
        custom_forbidden_words = data.get("forbidden_words", [])

        # 验证图片URL
        if image_urls:
            for url in image_urls:
                if not isinstance(url, str) or not url.startswith(("http://", "https://")):
                    raise ValidationException(f"无效的图片URL: {url}", PARAMETER_ERROR)

        # 获取IP和用户代理
        ip_address = request.remote_addr
        user_agent = request.headers.get("User-Agent")

        # 初始化存储库和服务
        db_session = g.db_session
        generation_repo = XhsCopyGenerationRepository(db_session)
        user_app_repo = UserAppRepository(db_session)
        provider_repo = LLMProviderRepository(db_session)
        model_repo = LLMModelRepository(db_session)
        llm_provider_config_repo = LLMProviderConfigRepository(db_session)
        forbidden_words_repo = ForbiddenWordsRepository(db_session)

        # 获取系统预置禁用词
        forbidden_words_service = ForbiddenWordsService(forbidden_words_repo)
        try:
            system_forbidden_words = [word["word"] for word in 
                                      forbidden_words_service.get_all_words("xhs_copy")]
        except Exception as e:
            logger.warning(f"无法获取系统预置禁用词: {str(e)}")
            system_forbidden_words = []

        # 合并系统预置和自定义禁用词
        all_forbidden_words = list(set(system_forbidden_words + custom_forbidden_words))

        # 初始化生成服务
        generation_service = XhsCopyGenerationService(
            generation_repo,
            user_app_repo,
            provider_repo,
            model_repo,
            llm_provider_config_repo,
        )

        # 创建文本生成请求数据
        generation_data = {
            "prompt": prompt,
            "image_urls": image_urls,
            "forbidden_words": all_forbidden_words,
            "app_id": app.id,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "use_published_config": True,
        }

        # 调用生成服务
        generation = generation_service.create_generation(**generation_data)

        # 创建调试信息对象
        debug_info = {
            "provider_type": generation.get("provider_type"),
            "model": generation.get("model_id"),
            "tokens": {
                "total": generation.get("tokens_used", 0)
            },
            "duration_ms": generation.get("duration_ms"),
            "app_id": app.id,
            "forbidden_words_detected": generation.get("detected_forbidden_words", [])
        }

        # 格式化结果
        result = {
            "id": generation.get("id"),
            "title": generation.get("title"),
            "content": generation.get("content"),
            "tags": generation.get("tags"),
            "status": generation.get("status"),
            "tokens_used": generation.get("tokens_used"),
            "duration_ms": generation.get("duration_ms"),
            "contains_forbidden_words": generation.get("contains_forbidden_words", False),
            "detected_forbidden_words": generation.get("detected_forbidden_words", []),
            "debug": debug_info
        }

        return success_response(result, "生成小红书文案成功")

    except ValidationException as e:
        logger.warning(f"Validation error: {str(e)}")
        raise
    except NotFoundException as e:
        logger.error(f"Not found error: {str(e)}")
        raise
    except APIException as e:
        logger.error(f"API error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
        raise APIException(f"生成文案失败: {str(e)}", GENERATION_FAILED)