"""小红书文案生成服务"""

import logging
import time
import traceback
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from app.infrastructure.database.repositories.user_llm_config_repository import (
    UserLLMConfigRepository,
)
from app.infrastructure.database.repositories.user_app_repository import (
    UserAppRepository,
)
from app.infrastructure.database.repositories.xhs_copy_repository import (
    XhsCopyGenerationRepository,
)
from app.infrastructure.database.repositories.llm_repository import (
    LLMProviderRepository,
    LLMModelRepository,
)

from app.infrastructure.llm_providers.factory import LLMProviderFactory
from app.core.exceptions import ValidationException, NotFoundException, APIException
from app.core.status_codes import (
    APPLICATION_NOT_FOUND,
    PARAMETER_ERROR,
    GENERATION_FAILED,
)

logger = logging.getLogger(__name__)


class XhsCopyGenerationService:
    """小红书文案生成服务"""

    def __init__(
        self,
        generation_repository: XhsCopyGenerationRepository,
        user_app_repository: UserAppRepository,
        provider_repository: LLMProviderRepository,
        model_repository: LLMModelRepository,
        user_llm_config_repository: Optional[UserLLMConfigRepository] = None,
    ):
        """初始化服务"""
        self.generation_repo = generation_repository
        self.user_app_repo = user_app_repository
        self.provider_repo = provider_repository
        self.model_repo = model_repository
        self.user_llm_config_repo = user_llm_config_repository

    def get_all_generations(
        self, user_id: str, page: int = 1, per_page: int = 20, **filters
    ) -> tuple[List[Dict[str, Any]], int]:
        """获取用户所有生成记录"""
        generations, total = self.generation_repo.get_all_by_user(
            user_id, page, per_page, **filters
        )
        return [self._format_generation(gen) for gen in generations], total

    def get_generation(self, generation_id: int, user_id: str) -> Dict[str, Any]:
        """获取特定生成记录"""
        generation = self.generation_repo.get_by_id(generation_id, user_id)
        return self._format_generation(generation)

    def create_generation(
        self,
        prompt: str,
        image_urls: List[str],
        app_id: Optional[int] = None,
        user_id: str = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """创建并执行文案生成

        Args:
            prompt: 生成提示词
            image_urls: 图片URL列表
            app_id: 应用ID
            user_id: 用户ID
            ip_address: IP地址
            user_agent: 用户代理

        Returns:
            生成结果
        """
        start_time = time.time()

        # 验证数据
        self._validate_generation_input(prompt, image_urls)

        # 获取应用配置
        app = self._get_generation_app(app_id, user_id)
        config = app.config

        # 创建生成记录
        generation = self._create_generation_record(
            prompt, image_urls, app.id, user_id, ip_address, user_agent
        )

        try:
            # 获取LLM服务
            ai_provider = self._get_llm_provider(app, user_id)

            # 准备提示词
            messages = self._prepare_prompts(config, prompt, image_urls)

            # 获取模型名称
            provider_type = self._get_provider_type(app, user_id)
            model_name = self._get_model_name(provider_type, ai_provider)

            # 生成文案
            max_tokens = config.get("max_tokens", 2000)
            temperature = config.get("temperature", 0.7)

            response = self._call_llm_service(
                ai_provider=ai_provider,
                messages=messages,
                model=model_name,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            # 解析生成结果
            parsed_result = self._parse_generation_result(
                response["message"]["content"], config
            )

            # 获取tokens使用量
            tokens_used = response.get("usage", {}).get("total_tokens", 0)

            # 计算处理时间
            duration_ms = int((time.time() - start_time) * 1000)

            # 更新生成记录
            updated_generation = self._update_generation_success(
                generation.id,
                user_id,
                parsed_result["title"],
                parsed_result["body"],
                parsed_result["tags"],
                tokens_used,
                duration_ms,
            )

            return self._format_generation(updated_generation)

        except Exception as e:
            logger.error(f"Generation error: {str(e)}\n{traceback.format_exc()}")
            # 更新失败状态
            self._update_generation_failure(
                generation.id, user_id, str(e), int((time.time() - start_time) * 1000)
            )

            # 重新抛出异常
            if isinstance(e, APIException):
                raise
            raise APIException(f"生成文案失败: {str(e)}", GENERATION_FAILED)

    def _validate_generation_input(self, prompt: str, image_urls: List[str]) -> None:
        """验证生成输入"""
        if not prompt:
            raise ValidationException("提示词不能为空", PARAMETER_ERROR)

        # 验证图片URL格式
        if image_urls:
            for url in image_urls:
                if not url.startswith(("http://", "https://")):
                    raise ValidationException(f"无效的图片URL: {url}", PARAMETER_ERROR)

    def _get_generation_app(self, app_id: Optional[int], user_id: str):
        """获取生成应用配置"""
        # 如果没有指定应用ID，使用默认应用
        if not app_id:
            default_app = self.user_app_repo.get_default_by_type(user_id, "xhs_copy")
            if not default_app:
                raise NotFoundException(
                    "未找到默认小红书文案生成应用，请先创建应用", APPLICATION_NOT_FOUND
                )
            return default_app

        # 获取指定应用
        return self.user_app_repo.get_by_id(app_id, user_id)

    def _create_generation_record(
        self, prompt, image_urls, app_id, user_id, ip_address, user_agent
    ):
        """创建生成记录"""
        generation_data = {
            "prompt": prompt,
            "image_urls": image_urls,
            "app_id": app_id,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "status": "processing",
        }
        return self.generation_repo.create(generation_data)

    def _get_provider_type(self, app, user_id):
        """获取提供商类型"""
        # 验证用户LLM配置
        if not app.user_llm_config_id or not self.user_llm_config_repo:
            raise APIException(
                "未配置LLM服务，请先为应用绑定LLM配置", GENERATION_FAILED
            )

        try:
            user_llm_config = self.user_llm_config_repo.get_by_id(
                app.user_llm_config_id, user_id
            )
            return user_llm_config.provider_type
        except Exception as e:
            raise APIException(f"无法获取LLM配置: {str(e)}", GENERATION_FAILED)

    def _get_llm_provider(self, app, user_id):
        """获取LLM服务提供商"""
        # 验证用户LLM配置
        if not app.user_llm_config_id:
            raise APIException(
                "未配置LLM服务，请先为应用绑定LLM配置", GENERATION_FAILED
            )

        if not self.user_llm_config_repo:
            raise APIException("系统未配置LLM服务接口", GENERATION_FAILED)

        try:
            user_llm_config = self.user_llm_config_repo.get_by_id(
                app.user_llm_config_id, user_id
            )
        except Exception as e:
            raise APIException(f"无法获取LLM配置: {str(e)}", GENERATION_FAILED)

        # 创建AI提供商实例
        provider_type = user_llm_config.provider_type

        if provider_type == "OpenAI":
            if not user_llm_config.api_key:
                raise APIException(
                    "您尚未配置OpenAI API密钥，请先在LLM配置中设置API密钥",
                    GENERATION_FAILED,
                )

            return LLMProviderFactory.create_provider(
                "openai",
                user_llm_config.api_key,
                api_base_url=user_llm_config.api_base_url,
                api_version=user_llm_config.api_version,
                timeout=user_llm_config.request_timeout,
                max_retries=user_llm_config.max_retries,
            )
        elif provider_type == "Claude":
            if not user_llm_config.api_key:
                raise APIException(
                    "您尚未配置Claude API密钥，请先在LLM配置中设置API密钥",
                    GENERATION_FAILED,
                )

            return LLMProviderFactory.create_provider(
                "anthropic",
                user_llm_config.api_key,
                api_base_url=user_llm_config.api_base_url,
                timeout=user_llm_config.request_timeout,
                max_retries=user_llm_config.max_retries,
            )
        elif provider_type == "Volcano":
            if not user_llm_config.api_key:
                raise APIException(
                    "您尚未配置火山引擎API密钥，请先在LLM配置中设置API密钥",
                    GENERATION_FAILED,
                )

            # 火山引擎可能需要额外的配置项
            config = {
                "timeout": user_llm_config.request_timeout,
                "max_retries": user_llm_config.max_retries,
            }

            # 添加应用ID和密钥（如果有）
            if user_llm_config.app_id:
                config["app_id"] = user_llm_config.app_id
            if user_llm_config.app_secret:
                config["app_secret"] = user_llm_config.app_secret

            return LLMProviderFactory.create_provider(
                "volcano", user_llm_config.api_key, **config
            )
        else:
            raise APIException(
                f"不支持的LLM提供商类型: {provider_type}", GENERATION_FAILED
            )

    def _prepare_prompts(self, config, prompt, image_urls):
        """准备提示词"""
        system_prompt = config.get(
            "system_prompt", "你是一位专业的小红书博主，擅长编写吸引人的小红书文案。"
        )

        # 获取用户提示词模板
        user_prompt_template = config.get(
            "user_prompt_template",
            "请根据以下内容，创作一篇吸引人的小红书文案：\n{prompt}",
        )

        # 替换模板中的变量
        user_prompt = user_prompt_template
        if "{prompt}" in user_prompt:
            user_prompt = user_prompt.replace("{prompt}", prompt)
        else:
            user_prompt = f"{user_prompt}\n\n{prompt}"

        # 添加图片描述
        if image_urls:
            image_descriptions = "\n\n参考以下图片URL："
            for i, url in enumerate(image_urls, 1):
                image_descriptions += f"\n图片{i}：{url}"
            user_prompt += image_descriptions

        # 添加配置要求
        requirements = "\n\n请按以下要求生成文案："
        requirements += f"\n1. 标题长度不超过{config.get('title_length', 50)}个字"
        requirements += f"\n2. 正文内容{config.get('content_length', 1000)}字左右"
        requirements += f"\n3. 生成{config.get('tags_count', 5)}个适合的标签"
        if config.get("include_emojis", True):
            requirements += "\n4. 适当地使用表情符号增加趣味性"
        requirements += (
            "\n\n请按照以下格式输出：\n【标题】\n【正文】\n【标签】标签1 标签2 标签3..."
        )

        user_prompt += requirements

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _get_model_name(self, provider_type, ai_provider):
        """获取模型名称"""
        if provider_type == "OpenAI":
            return "gpt-4o"  # 默认使用gpt-4o
        elif provider_type == "Claude":
            return "claude-3-opus-20240229"  # 默认使用Claude-3-Opus
        elif provider_type == "Volcano":
            return "deepseek-r1-250120"  # 默认使用Deepseek
        else:
            # 使用提供商的默认模型
            return None

    def _call_llm_service(self, ai_provider, messages, model, max_tokens, temperature):
        """调用LLM服务"""
        return ai_provider.generate_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            model=model,
        )

    def _parse_generation_result(self, content, config):
        """解析生成结果"""
        title = ""
        body = ""
        tags = []

        # 尝试解析标题、正文和标签
        if "【标题】" in content:
            title_parts = content.split("【标题】")
            if len(title_parts) > 1:
                title_content = (
                    title_parts[1].split("【正文】")[0]
                    if "【正文】" in title_parts[1]
                    else title_parts[1]
                )
                title = title_content.strip()

        if "【正文】" in content:
            body_parts = content.split("【正文】")
            if len(body_parts) > 1:
                body_content = (
                    body_parts[1].split("【标签】")[0]
                    if "【标签】" in body_parts[1]
                    else body_parts[1]
                )
                body = body_content.strip()

        if "【标签】" in content:
            tags_part = (
                content.split("【标签】")[1]
                if len(content.split("【标签】")) > 1
                else ""
            )
            # 提取标签
            tag_candidates = [tag.strip() for tag in tags_part.split() if tag.strip()]
            # 过滤非空标签
            tags = [tag for tag in tag_candidates if tag]

        # 如果没有按格式输出，尝试更灵活地解析
        if not title and not body:
            # 可能是自由格式输出，尝试智能提取
            lines = content.split("\n")
            if lines:
                # 第一行可能是标题
                title = lines[0].strip()
                # 剩余内容作为正文
                body = "\n".join(lines[1:]).strip()

        # 如果标签为空但有标签配置，尝试提取一些标签
        if not tags and config.get("tags_count", 0) > 0:
            # 简单地从正文中提取一些词作为标签（实际应用中可能需要更复杂的逻辑）
            words = body.split()
            # 选择一些长度合适的词作为标签
            potential_tags = [word for word in words if 2 <= len(word) <= 10]
            # 取唯一值并限制数量
            tags = list(set(potential_tags))[: config.get("tags_count", 5)]

        return {"title": title, "body": body, "tags": tags}

    def _update_generation_success(
        self, generation_id, user_id, title, body, tags, tokens_used, duration_ms
    ):
        """更新生成成功状态"""
        update_data = {
            "status": "completed",
            "title": title,
            "content": body,
            "tags": tags,
            "tokens_used": tokens_used,
            "duration_ms": duration_ms,
        }

        return self.generation_repo.update(generation_id, user_id, update_data)

    def _update_generation_failure(
        self, generation_id, user_id, error_message, duration_ms
    ):
        """更新生成失败状态"""
        update_data = {
            "status": "failed",
            "error_message": error_message,
            "duration_ms": duration_ms,
        }

        return self.generation_repo.update(generation_id, user_id, update_data)

    def delete_generation(self, generation_id: int, user_id: str) -> bool:
        """删除生成记录"""
        return self.generation_repo.delete(generation_id, user_id)

    def get_statistics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """获取生成统计数据"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        return self.generation_repo.get_statistics(user_id, start_date, end_date)

    def rate_generation(
        self,
        generation_id: int,
        user_id: str,
        rating: int,
        feedback: Optional[str] = None,
    ) -> Dict[str, Any]:
        """对生成结果评分"""
        # 验证评分
        if rating < 1 or rating > 5:
            raise ValidationException("评分必须在1-5之间", PARAMETER_ERROR)

        # 更新评分
        update_data = {"user_rating": rating}

        if feedback:
            update_data["user_feedback"] = feedback

        generation = self.generation_repo.update(generation_id, user_id, update_data)
        return self._format_generation(generation)

    def _format_generation(self, generation) -> Dict[str, Any]:
        """格式化生成记录数据"""
        return {
            "id": generation.id,
            "prompt": generation.prompt,
            "image_urls": generation.image_urls,
            "app_id": generation.app_id,
            "title": generation.title,
            "content": generation.content,
            "tags": generation.tags,
            "status": generation.status,
            "error_message": generation.error_message,
            "tokens_used": generation.tokens_used,
            "duration_ms": generation.duration_ms,
            "ip_address": generation.ip_address,
            "user_rating": generation.user_rating,
            "user_feedback": generation.user_feedback,
            "created_at": (
                generation.created_at.isoformat() if generation.created_at else None
            ),
        }
