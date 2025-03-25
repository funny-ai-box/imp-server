# app/api/v1/external/applications/image_classify.py
import time
import logging
import traceback
import json
from flask import Blueprint, request, g
from app.core.responses import success_response
from app.core.exceptions import APIException, ValidationException
from app.core.status_codes import CLASSIFICATION_FAILED
from app.infrastructure.database.repositories.user_app_repository import (
    UserAppRepository,
)
from app.infrastructure.database.repositories.user_llm_config_repository import (
    UserLLMConfigRepository,
)
from app.infrastructure.database.repositories.image_classify_repository import (
    ImageClassifyRepository,
)
from app.infrastructure.llm_providers.factory import LLMProviderFactory
from app.api.middleware.app_key_auth import app_key_required

logger = logging.getLogger(__name__)

external_image_classify_bp = Blueprint("external_image_classify", __name__, url_prefix="/image_classify")


# 辅助函数
def _validate_and_extract_params(request):
    """验证和提取请求参数"""
    data = request.get_json()
    if not data:
        raise ValidationException("请求数据不能为空")

    # 提取图片URL
    image_url = data.get("image_url")
    if not image_url:
        raise ValidationException("图片URL不能为空")

    # 验证图片URL格式
    if not image_url.startswith(("http://", "https://")):
        raise ValidationException(f"无效的图片URL: {image_url}")

    # 验证分类列表
    categories = data.get("categories")
    if not categories or not isinstance(categories, list) or len(categories) < 2:
        raise ValidationException("分类列表必须至少包含两个选项")

    for category in categories:
        if not isinstance(category, dict) or "id" not in category or "text" not in category:
            raise ValidationException("分类列表格式错误，每项必须包含id和text字段")

    return data


def _create_llm_provider(user_llm_config):
    """创建LLM提供商实例"""
    provider_type = user_llm_config.provider_type
    
    try:
        if provider_type == "Volcano":
            # 检查API密钥是否有效
            if not user_llm_config.api_key:
                raise APIException("您尚未配置火山引擎API密钥", CLASSIFICATION_FAILED)
                
            # 记录连接尝试（用于调试）
            print(f"正在尝试连接到火山引擎，基础URL为: {user_llm_config.api_base_url}")
            
            return LLMProviderFactory.create_provider(
                "volcano",
                user_llm_config.api_key,
                api_base_url=user_llm_config.api_base_url,
                api_version=user_llm_config.api_version,
                timeout=user_llm_config.request_timeout,
                max_retries=user_llm_config.max_retries,
            )
        else:
            raise APIException(f"图片分类仅支持Volcano提供商，当前配置: {provider_type}", CLASSIFICATION_FAILED)
    except Exception as e:
        print(f"创建LLM提供商失败: {str(e)}")
        print(f"详细错误: {traceback.format_exc()}")
        raise APIException(f"创建LLM提供商失败: {str(e)}", CLASSIFICATION_FAILED)


def _get_model_name():
    """获取模型名称"""
    return "doubao-1.5-vision-pro-32k-250115"  # 火山引擎视觉模型


def _prepare_prompts(config, image_url, categories):
    """准备提示词"""
    # 系统提示词
    system_prompt = config.get(
        "system_prompt", 
        "你是一位专业的图像分类助手，你的任务是判断图片属于哪个预定义分类。"
    )

    # 构建分类选项文本
    categories_text = "\n".join([f"ID: {cat['id']}, 分类: {cat['text']}" for cat in categories])
    
    # 用户提示词
    user_prompt = f"""请分析下面这张图片，并判断它应该属于以下哪个分类：

{categories_text}

请仔细分析图片内容，并给出你的分类结果和推理过程。
你的回答必须是以下JSON格式：
{{
  "category_id": "分类ID",
  "category_name": "分类名称",
  "confidence": 0.95,
  "reasoning": "这里是你对分类的推理过程"
}}

只能选择一个最匹配的分类，置信度为0-1之间的小数，推理过程需要详细说明为什么图片属于该分类。"""

    # 构建消息
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        }
    ]

    return messages


def _parse_classification_result(content, categories):
    """解析分类结果"""
    try:
        # 尝试从文本中提取JSON
        json_start = content.find('{')
        json_end = content.rfind('}')
        
        if json_start != -1 and json_end != -1:
            json_str = content[json_start:json_end+1]
            try:
                result = json.loads(json_str)
                
                # 验证结果中包含必需的字段
                if "category_id" not in result or "category_name" not in result:
                    logger.warning(f"分类结果缺少必要字段: {result}")
                    # 尝试从文本中推断结果
                    return _guess_classification(content, categories)
                
                # 确保所有必要字段都存在
                if "confidence" not in result:
                    result["confidence"] = 0.8  # 默认置信度
                if "reasoning" not in result:
                    result["reasoning"] = "未提供推理过程"
                
                return result
            except json.JSONDecodeError:
                logger.warning(f"JSON解析失败: {json_str}")
                
        # 如果无法解析JSON，尝试从文本中推断结果
        return _guess_classification(content, categories)
    except Exception as e:
        logger.error(f"解析分类结果失败: {str(e)}")
        return _guess_classification(content, categories)


def _guess_classification(content, categories):
    """从文本响应中推断分类结果"""
    content_lower = content.lower()
    best_match = None
    highest_score = 0
    
    # 简单的文本匹配算法
    for category in categories:
        category_name = category["text"].lower()
        score = content_lower.count(category_name)
        
        # 检查是否明确提到该分类ID
        id_mentions = content_lower.count(category["id"].lower())
        score += id_mentions * 2
        
        if score > highest_score:
            highest_score = score
            best_match = category
    
    # 如果没有找到匹配项，选择第一个分类
    if not best_match and categories:
        best_match = categories[0]
    
    return {
        "category_id": best_match["id"],
        "category_name": best_match["text"],
        "confidence": min(highest_score * 0.1, 0.9) if highest_score > 0 else 0.5,
        "reasoning": "通过文本分析推断的分类结果"
    }


def _create_classification_record(
    classify_repo, image_url, categories, app_id, user_id, ip_address, user_agent
):
    """创建分类记录"""
    record_data = {
        "image_url": image_url,
        "categories": categories,
        "app_id": app_id,
        "user_id": user_id,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "status": "processing",
    }
    return classify_repo.create(record_data)


def _update_classification_success(
    classify_repo,
    classification_id,
    user_id,
    category_id,
    category_name,
    confidence,
    reasoning,
    tokens_used,
    duration_ms,
):
    """更新分类成功状态"""
    update_data = {
        "status": "completed",
        "category_id": category_id,
        "category_name": category_name,
        "confidence": confidence,
        "reasoning": reasoning,
        "tokens_used": tokens_used,
        "duration_ms": duration_ms,
    }

    return classify_repo.update(classification_id, user_id, update_data)


def _update_classification_failure(
    classify_repo, classification_id, user_id, error_message, duration_ms
):
    """更新分类失败状态"""
    update_data = {
        "status": "failed",
        "error_message": error_message,
        "duration_ms": duration_ms,
    }

    return classify_repo.update(classification_id, user_id, update_data)


@external_image_classify_bp.route("/classify", methods=["POST"])
@app_key_required
def external_classify():
    """图片分类API（外部接口）"""
    try:
        # 获取app_key_auth中间件已验证的应用和用户信息
        app_key = g.app_key
        user_id = g.user_id
        app = g.app

        # 验证请求数据
        data = _validate_and_extract_params(request)

        # 验证应用类型和发布状态
        if app.app_type != "image_classify":
            raise ValidationException(
                "该应用密钥不属于图片分类应用"
            )

        if not app.published or not app.published_config:
            raise ValidationException("该应用未发布配置")

        # 获取IP和用户代理
        ip_address = request.remote_addr
        user_agent = request.headers.get("User-Agent")

        # 初始化服务和仓库
        db_session = g.db_session
        user_app_repo = UserAppRepository(db_session)
        user_llm_config_repo = UserLLMConfigRepository(db_session)
        classify_repo = ImageClassifyRepository(db_session)

        # 提取数据
        image_url = data["image_url"]
        categories = data["categories"]

        # 从应用中获取配置和关联的LLM配置
        config = app.published_config.get("config", {})
        user_llm_config_id = app.user_llm_config_id

        # 创建分类记录
        start_time = time.time()
        classification = _create_classification_record(
            classify_repo,
            image_url=image_url,
            categories=categories,
            app_id=app.id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        try:
            # 获取用户LLM配置
            user_llm_config = user_llm_config_repo.get_by_id(
                user_llm_config_id, user_id
            )

            # 创建LLM提供商实例
            ai_provider = _create_llm_provider(user_llm_config)

            # 准备提示词
            messages = _prepare_prompts(config, image_url, categories)

            # 确定模型名称
            model_name = _get_model_name()

            # 分类参数
            max_tokens = config.get("max_tokens", 2000)
            temperature = config.get("temperature", 0.2)  # 降低温度增加确定性

            # 调用LLM服务
            response = ai_provider.generate_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                model=model_name,
            )

            # 解析分类结果
            content = response["message"]["content"]
            parsed_result = _parse_classification_result(content, categories)

            # 获取tokens使用量
            tokens_used = response.get("usage", {}).get("total_tokens", 0)

            # 计算处理时间
            duration_ms = int((time.time() - start_time) * 1000)

            # 更新分类记录
            classification = _update_classification_success(
                classify_repo,
                classification_id=classification.id,
                user_id=user_id,
                category_id=parsed_result["category_id"],
                category_name=parsed_result["category_name"],
                confidence=parsed_result.get("confidence", 0.0),
                reasoning=parsed_result.get("reasoning", ""),
                tokens_used=tokens_used,
                duration_ms=duration_ms,
            )

            # 格式化结果
            result = {
                "id": classification.id,
                "category_id": classification.category_id,
                "category_name": classification.category_name,
                "confidence": classification.confidence,
                "reasoning": classification.reasoning,
                "tokens_used": classification.tokens_used,
                "duration_ms": classification.duration_ms,
                "status": classification.status,
            }

            return success_response(result, "图片分类成功")

        except Exception as e:
            logger.error(f"Classification error: {str(e)}\n{traceback.format_exc()}")
            # 更新失败状态
            _update_classification_failure(
                classify_repo,
                classification_id=classification.id,
                user_id=user_id,
                error_message=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )

            # 重新抛出异常
            if isinstance(e, APIException):
                raise
            raise APIException(f"图片分类失败: {str(e)}", CLASSIFICATION_FAILED)

    except ValidationException as e:
        # 参数验证失败
        logger.warning(f"Validation error: {str(e)}")
        raise
    except APIException as e:
        # 业务异常
        logger.error(f"API error: {str(e)}")
        raise
    except Exception as e:
        # 未预期的异常
        logger.error(
            f"Unexpected error in external classify: {str(e)}\n{traceback.format_exc()}"
        )
        raise APIException(f"图片分类失败: {str(e)}", CLASSIFICATION_FAILED)


@external_image_classify_bp.route("/rate", methods=["POST"])
@app_key_required
def rate_classification():
    """评价分类结果（外部应用调用）"""
    try:
        # app_key_auth中间件已验证密钥，并将应用和用户信息存储在g中
        user_id = g.user_id

        # 验证请求数据
        data = request.get_json()
        if not data:
            raise ValidationException("请求数据不能为空",)

        # 提取评分参数
        classification_id = data.get("classification_id")
        if not classification_id:
            raise ValidationException("缺少必填参数: classification_id",)

        rating = data.get("rating")
        if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
            raise ValidationException("评分必须是1-5之间的整数",)

        feedback = data.get("feedback")

        # 初始化存储库
        db_session = g.db_session
        classify_repo = ImageClassifyRepository(db_session)

        # 更新评分
        update_data = {"user_rating": rating, "user_feedback": feedback}

        classification = classify_repo.update(classification_id, user_id, update_data)

        return success_response({"success": True}, "评分提交成功")

    except ValidationException as e:
        raise
    except APIException as e:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error in rate classification: {str(e)}\n{traceback.format_exc()}"
        )
        raise APIException(f"评分提交失败: {str(e)}", CLASSIFICATION_FAILED)