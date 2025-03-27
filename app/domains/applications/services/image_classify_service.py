"""图片分类服务"""

import logging
import time
import traceback
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from app.infrastructure.database.repositories.user_app_repository import (
    UserAppRepository,
)
from app.infrastructure.database.repositories.image_classify_repository import (
    ImageClassifyRepository,
)
from app.infrastructure.database.repositories.llm_repository import (
    LLMProviderRepository,
    LLMModelRepository,
    LLMProviderConfigRepository
)


from app.infrastructure.llm_providers.factory import LLMProviderFactory
from app.core.exceptions import ValidationException, NotFoundException, APIException
from app.core.status_codes import (
    APPLICATION_NOT_FOUND,
    PARAMETER_ERROR,
    CLASSIFICATION_FAILED,
    INVALID_IMAGE_URL,
    INVALID_CATEGORIES,
)

logger = logging.getLogger(__name__)


class ImageClassifyService:
    """图片分类服务"""

    def __init__(
        self,
        classify_repository: ImageClassifyRepository,
        user_app_repository: Optional[UserAppRepository] = None,
        provider_repository: Optional[LLMProviderRepository] = None,
        model_repository: Optional[LLMModelRepository] = None,
        llm_provider_config_repository: Optional[LLMProviderConfigRepository] = None,
    ):
        """初始化服务"""
        self.classify_repo = classify_repository
        self.user_app_repo = user_app_repository
        self.provider_repo = provider_repository
        self.model_repo = model_repository
        self.llm_provider_config_repo = llm_provider_config_repository

    def get_all_classifications(
        self, user_id: str, page: int = 1, per_page: int = 20, **filters
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取用户所有分类记录"""
        records, total = self.classify_repo.get_all_by_user(
            user_id=user_id, page=page, per_page=per_page, **filters
        )
        return [self._format_classification(record) for record in records], total

    def get_classification(self, classification_id: int, user_id: str) -> Dict[str, Any]:
        """获取特定分类记录"""
        record = self.classify_repo.get_by_id(classification_id, user_id)
        return self._format_classification(record)

    def create_classification(
        self,
        image_url: str,
        categories: List[Dict[str, str]],
        app_id: Optional[str] = None,
        user_id: str = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """创建并执行图片分类

        Args:
            image_url: 图片URL
            categories: 分类选项列表，格式为[{"id": "1", "text": "分类1"}, {"id": "2", "text": "分类2"}]
            app_id: 应用ID
            user_id: 用户ID
            ip_address: IP地址
            user_agent: 用户代理

        Returns:
            分类结果
        """
        start_time = time.time()

        # 验证数据
        self._validate_classification_input(image_url, categories)

        # 获取应用配置
        app = self._get_classification_app(app_id, user_id)
        config = app.config

        # 创建分类记录
        classification = self._create_classification_record(
            image_url, categories, app.id, user_id, ip_address, user_agent
        )

        try:
            # 检查配置中是否包含provider_type
            provider_type = config.get("provider_type")
            if not provider_type:
                raise ValidationException("应用配置中未指定provider_type")
                
            # 目前图片分类只支持Volcano提供商
            if provider_type != "Volcano":
                raise ValidationException("图片分类目前仅支持Volcano提供商", CLASSIFICATION_FAILED)

            # 获取LLM服务
            llm_provider_config = self._get_llm_provider_config(provider_type, user_id)
            ai_provider = self._create_llm_provider(llm_provider_config)

            # 准备提示词
            messages = self._prepare_prompts(config, image_url, categories)

            # 获取模型名称
            model_id = self._get_model_id(config)

            # 生成分类结果
            max_tokens = config.get("max_tokens", 2000)
            temperature = config.get("temperature", 0.2)  # 降低温度增加确定性

            response = self._call_llm_service(
                ai_provider=ai_provider,
                messages=messages,
                model=model_id,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            # 解析分类结果
            parsed_result = self._parse_classification_result(
                response["message"]["content"], categories
            )

            # 获取tokens使用量
            tokens_used = response.get("usage", {}).get("total_tokens", 0)

            # 计算处理时间
            duration_ms = int((time.time() - start_time) * 1000)

            # 更新分类记录
            updated_classification = self._update_classification_success(
                classification.id,
                user_id,
                parsed_result["category_id"],
                parsed_result["category_name"],
                parsed_result.get("confidence", 0.0),
                parsed_result.get("reasoning", ""),
                tokens_used,
                duration_ms,
                provider_type,
                model_id
            )

            return self._format_classification(updated_classification)

        except Exception as e:
            logger.error(f"Classification error: {str(e)}\n{traceback.format_exc()}")
            # 更新失败状态
            self._update_classification_failure(
                classification.id, user_id, str(e), int((time.time() - start_time) * 1000)
            )

            # 重新抛出异常
            if isinstance(e, APIException):
                raise
            raise APIException(f"图片分类失败: {str(e)}", CLASSIFICATION_FAILED)

    def _validate_classification_input(self, image_url: str, categories: List[Dict[str, str]]) -> None:
        """验证分类输入"""
        if not image_url:
            raise ValidationException("图片URL不能为空", INVALID_IMAGE_URL)

        # 验证图片URL格式
        if not image_url.startswith(("http://", "https://")):
            raise ValidationException(f"无效的图片URL: {image_url}", INVALID_IMAGE_URL)

        # 验证分类列表
        if not categories or not isinstance(categories, list) or len(categories) < 2:
            raise ValidationException("分类列表必须至少包含两个选项", INVALID_CATEGORIES)

        for category in categories:
            if not isinstance(category, dict) or "id" not in category or "text" not in category:
                raise ValidationException("分类列表格式错误，每项必须包含id和text字段", INVALID_CATEGORIES)

    def _get_classification_app(self, app_id: Optional[str], user_id: str):
        """获取分类应用配置"""
        if not self.user_app_repo:
            raise APIException("未配置应用存储库", CLASSIFICATION_FAILED)
            
        # 如果没有指定应用ID，使用默认应用
        if not app_id:
            default_app = self.user_app_repo.get_default_by_type(user_id, "image_classify")
            if not default_app:
                raise NotFoundException(
                    "未找到默认图片分类应用，请先创建应用", APPLICATION_NOT_FOUND
                )
            return default_app

        # 获取指定应用
        return self.user_app_repo.get_by_id(app_id, user_id)

    def _create_classification_record(
        self, image_url, categories, app_id, user_id, ip_address, user_agent
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
        return self.classify_repo.create(record_data)
    
    def _get_llm_provider_config(self, provider_type: str, user_id: str):
        """获取用户的LLM提供商配置"""
        if not self.llm_provider_config_repo:
            raise APIException("未配置LLM提供商存储库", CLASSIFICATION_FAILED)
            
        # 根据provider_type获取用户的默认配置
        llm_config = self.llm_provider_config_repo.get_default(user_id, provider_type)
        if not llm_config:
            raise NotFoundException(
                f"未找到{provider_type}的LLM配置，请先在LLM设置中配置", CLASSIFICATION_FAILED
            )
            
        # 检查配置是否激活
        if not llm_config.is_active:
            raise ValidationException(f"{provider_type}配置未激活", CLASSIFICATION_FAILED)
            
        return llm_config

    def _create_llm_provider(self, llm_provider_config):
        """根据配置创建LLM提供商实例"""
        provider_type = llm_provider_config.provider_type

        try:
            if provider_type == "Volcano":
                if not llm_provider_config.api_key:
                    raise APIException(
                        "您尚未配置火山引擎API密钥", CLASSIFICATION_FAILED
                    )

                # 火山引擎可能需要额外的配置项
                config = {
                    "timeout": llm_provider_config.request_timeout,
                    "max_retries": llm_provider_config.max_retries,
                }

                # 添加应用ID和密钥（如果有）
                if llm_provider_config.app_id:
                    config["app_id"] = llm_provider_config.app_id
                if llm_provider_config.app_secret:
                    config["app_secret"] = llm_provider_config.app_secret

                return LLMProviderFactory.create_provider(
                    "volcano", llm_provider_config.api_key, **config
                )
            else:
                # 目前图片分类只支持Volcano
                raise APIException(
                    f"图片分类不支持的LLM提供商类型: {provider_type}", CLASSIFICATION_FAILED
                )
        except Exception as e:
            logger.error(f"Failed to create LLM provider: {str(e)}")
            raise APIException(f"创建LLM提供商失败: {str(e)}", CLASSIFICATION_FAILED)

    def _prepare_prompts(self, config, image_url, categories):
        """准备提示词"""
        # 系统提示词
        system_prompt = config.get(
            "system_prompt", 
            "你是一位专业的图像分类助手，你的任务是判断图片属于哪个预定义分类。请仔细分析图片内容，如果图片不属于任何分类或信息值太低，请明确表示无法分类。"
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

        只能选择一个最匹配的分类。如果图片内容不清晰、信息值低或不属于任何一个给定分类，请返回以下JSON格式：
        {{
        "category_id": null,
        "category_name": null,
        "confidence": 0,
        "reasoning": "这里说明为什么无法对图片进行分类的原因"
        }}

        置信度为0-1之间的小数，推理过程需要详细说明为什么图片属于该分类或无法分类的原因。"""

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

    def _get_model_id(self, config):
        """获取模型名称，优先使用配置的模型"""
        # 从应用配置中获取模型名称
        model_id = config.get("model_id") or config.get("vision_model_id")
        
        # 如果配置中指定了模型，使用配置的模型
        if model_id:
            return model_id
        
        # 否则使用默认模型
        return "doubao-1.5-vision-pro-32k-250115"  # 默认火山引擎视觉模型

    def _call_llm_service(self, ai_provider, messages, model, max_tokens, temperature):
        """调用LLM服务"""
        return ai_provider.generate_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            model=model,
        )

    def _parse_classification_result(self, content, categories):
        """解析分类结果
        
        尝试从LLM响应中提取JSON格式的分类结果，包含category_id、category_name、confidence和reasoning
        支持无法分类的情况，返回null值
        """
        try:
            # 尝试获取JSON格式的响应
            json_content = self._extract_json(content)
            if json_content:
                result = json.loads(json_content)
                
                # 检查是否为无法分类的情况（空分类）
                if result.get("category_id") is None and result.get("category_name") is None:
                    return {
                        "category_id": None,
                        "category_name": None,
                        "confidence": 0,
                        "reasoning": result.get("reasoning", "无法对图片进行分类，信息值太低或不符合任何给定分类")
                    }
                
                # 验证结果中包含必需的字段
                if "category_id" not in result or "category_name" not in result:
                    logger.warning(f"分类结果缺少必要字段: {result}")
                    # 尝试推断分类或返回无法分类
                    if "无法分类" in content or "不属于任何分类" in content:
                        return {
                            "category_id": None,
                            "category_name": None,
                            "confidence": 0,
                            "reasoning": "根据LLM响应，图片无法分类"
                        }
                    return self._guess_classification(content, categories)
                
                # 确保所有必要字段都存在
                if "confidence" not in result:
                    result["confidence"] = 0.8  # 默认置信度
                if "reasoning" not in result:
                    result["reasoning"] = "未提供推理过程"
                
                # 验证category_id是否在提供的分类列表中
                valid_ids = [cat["id"] for cat in categories]
                if result["category_id"] not in valid_ids:
                    logger.warning(f"分类ID不在提供的列表中: {result['category_id']}")
                    # 尝试匹配最接近的ID
                    for cat in categories:
                        if cat["text"].lower() == result["category_name"].lower():
                            result["category_id"] = cat["id"]
                            break
                
                return result
            else:
                # 检查是否有明确表示无法分类的内容
                if "无法分类" in content or "不属于任何分类" in content:
                    return {
                        "category_id": None,
                        "category_name": None,
                        "confidence": 0,
                        "reasoning": "LLM表示无法分类，但未返回标准JSON格式"
                    }
                
                # 无法解析JSON，尝试推断分类
                return self._guess_classification(content, categories)
        except Exception as e:
            logger.error(f"解析分类结果失败: {str(e)}\n{traceback.format_exc()}")
            # 尝试推断分类
            return self._guess_classification(content, categories)

    def _extract_json(self, text):
        """从文本中提取JSON格式的内容"""
        # 尝试正则提取JSON格式内容
        json_pattern = r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}))*\}'
        matches = re.findall(json_pattern, text)
        
        if matches:
            # 尝试解析找到的每个JSON块
            for match in matches:
                try:
                    json.loads(match)
                    return match
                except:
                    continue
        
        return None

    def _guess_classification(self, content, categories):
        """从文本响应中推断分类结果"""
        content_lower = content.lower()
        best_match = None
        highest_score = 0
        reasoning = "通过文本分析推断的分类结果"
        
        # 简单的文本匹配算法
        for category in categories:
            category_name = category["text"].lower()
            score = content_lower.count(category_name)
            
            # 增加对ID的检测
            id_match = re.search(r'id[:\s]*["\']?' + re.escape(category["id"]) + r'["\']?', content_lower)
            if id_match:
                score += 5
            
            if score > highest_score:
                highest_score = score
                best_match = category
        
        # 如果没有找到匹配项，选择第一个分类
        if not best_match and categories:
            best_match = categories[0]
            reasoning = "无法确定明确分类，默认选择第一个分类"
        
        return {
            "category_id": best_match["id"],
            "category_name": best_match["text"],
            "confidence": min(highest_score * 0.1, 0.95) if highest_score > 0 else 0.5,
            "reasoning": reasoning
        }

    def _update_classification_success(
        self, classification_id, user_id, category_id, category_name, confidence, reasoning, tokens_used, duration_ms, provider_type, model_id
    ):
        """更新分类成功状态，支持无法分类的情况"""
        status = "completed" if category_id is not None else "unclassified"
        
        update_data = {
            "status": status,
            "category_id": category_id,
            "category_name": category_name,
            "confidence": confidence,
            "reasoning": reasoning,
            "tokens_used": tokens_used,
            "duration_ms": duration_ms,
            "provider_type": provider_type,
            "model_id": model_id
        }

        return self.classify_repo.update(classification_id, user_id, update_data)

    def _update_classification_failure(
        self, classification_id, user_id, error_message, duration_ms
    ):
        """更新分类失败状态"""
        update_data = {
            "status": "failed",
            "error_message": error_message,
            "duration_ms": duration_ms,
        }

        return self.classify_repo.update(classification_id, user_id, update_data)

    def _format_classification(self, record) -> Dict[str, Any]:
        """格式化分类记录数据"""
        return {
            "id": record.id,
            "image_url": record.image_url,
            "categories": record.categories,
            "app_id": record.app_id,
            "category_id": record.category_id,
            "category_name": record.category_name,
            "confidence": record.confidence,
            "reasoning": record.reasoning,
            "status": record.status,
            "error_message": record.error_message,
            "tokens_used": record.tokens_used,
            "provider_type": record.provider_type,
            "model_id": record.model_id,
            "duration_ms": record.duration_ms,
            "ip_address": record.ip_address,
            "user_rating": record.user_rating,
            "user_feedback": record.user_feedback,
            "created_at": (
                record.created_at.isoformat() if record.created_at else None
            ),
        }