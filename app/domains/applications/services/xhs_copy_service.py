"""小红书文案生成服务"""
import logging
import time
import traceback
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from app.infrastructure.database.repositories.user_llm_config_repository import UserLLMConfigRepository
from app.infrastructure.database.repositories.xhs_copy_repository import (
    XhsCopyConfigRepository, 
    XhsCopyGenerationRepository,
    XhsCopyTestRepository
)
from app.infrastructure.database.repositories.llm_repository import LLMProviderRepository, LLMModelRepository

from app.infrastructure.llm_providers.factory import LLMProviderFactory
from app.core.exceptions import ValidationException, NotFoundException, APIException
from app.core.status_codes import CONFIG_NOT_FOUND, PARAMETER_ERROR, GENERATION_FAILED

logger = logging.getLogger(__name__)

class XhsCopyConfigService:
    """小红书配置服务"""
    
    def __init__(
        self, 
        config_repository: XhsCopyConfigRepository,
        provider_repository: LLMProviderRepository,
        model_repository: LLMModelRepository,
        user_llm_config_repository: UserLLMConfigRepository
    ):
        """初始化服务"""
        self.config_repo = config_repository
        self.provider_repo = provider_repository
        self.model_repo = model_repository
        self.user_llm_config_repo = user_llm_config_repository
    
    def get_all_configs(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户所有配置"""
        configs = self.config_repo.get_all_by_user(user_id)
        result = []
        
        for config in configs:
            formatted_config = self._format_config(config)
            
            # 获取关联的用户LLM配置信息
            if config.user_llm_config_id:
                try:
                    llm_config = self.user_llm_config_repo.get_by_id(config.user_llm_config_id, user_id)
                    formatted_config["llm_config"] = {
                        "id": llm_config.id,
                        "name": llm_config.name,
                        "provider_type": llm_config.provider_type
                    }
                except Exception as e:
                    logger.error(f"Error fetching LLM config: {str(e)}")
                    formatted_config["llm_config"] = None
            else:
                formatted_config["llm_config"] = None
                
            result.append(formatted_config)
            
        return result
    
    def get_config(self, config_id: int, user_id: str) -> Dict[str, Any]:
        """获取特定配置"""
        config = self.config_repo.get_by_id(config_id, user_id)
        result = self._format_config(config)
        
        # 获取关联的用户LLM配置信息
        if config.user_llm_config_id:
            try:
                llm_config = self.user_llm_config_repo.get_by_id(config.user_llm_config_id, user_id)
                result["llm_config"] = {
                    "id": llm_config.id,
                    "name": llm_config.name,
                    "provider_type": llm_config.provider_type
                }
            except Exception as e:
                logger.error(f"Error fetching LLM config: {str(e)}")
                result["llm_config"] = None
        else:
            result["llm_config"] = None
            
        return result
    
    def get_default_config(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取默认配置"""
        config = self.config_repo.get_default(user_id)
        if not config:
            return None
            
        result = self._format_config(config)
        
        # 获取关联的用户LLM配置信息
        if config.user_llm_config_id:
            try:
                llm_config = self.user_llm_config_repo.get_by_id(config.user_llm_config_id, user_id)
                result["llm_config"] = {
                    "id": llm_config.id,
                    "name": llm_config.name,
                    "provider_type": llm_config.provider_type
                }
            except Exception as e:
                logger.error(f"Error fetching LLM config: {str(e)}")
                result["llm_config"] = None
        else:
            result["llm_config"] = None
            
        return result
    
    def create_config(self, config_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """创建新配置"""
        # 验证数据
        self._validate_config_data(config_data)
        
        # 验证用户LLM配置
        if "user_llm_config_id" in config_data and config_data["user_llm_config_id"]:
            try:
                llm_config = self.user_llm_config_repo.get_by_id(config_data["user_llm_config_id"], user_id)
                # 验证LLM配置是否有效
                if not llm_config.is_active:
                    raise ValidationException("选择的LLM配置未激活", PARAMETER_ERROR)
            except NotFoundException:
                raise ValidationException("指定的LLM配置不存在或不属于当前用户", PARAMETER_ERROR)
            except Exception as e:
                raise ValidationException(f"指定的LLM配置无效: {str(e)}", PARAMETER_ERROR)
        
        # 设置用户ID
        config_data["user_id"] = user_id
        
        # 如果是第一个配置，设为默认
        if len(self.config_repo.get_all_by_user(user_id)) == 0:
            config_data["is_default"] = True
        
        # 创建配置
        config = self.config_repo.create(config_data)
        return self._format_config(config)
    
    def update_config(self, config_id: int, config_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """更新配置"""
        # 验证数据
        if config_data:
            self._validate_config_data(config_data, is_update=True)
        
        # 验证用户LLM配置
        if "user_llm_config_id" in config_data and config_data["user_llm_config_id"]:
            try:
                llm_config = self.user_llm_config_repo.get_by_id(config_data["user_llm_config_id"], user_id)
                # 验证LLM配置是否有效
                if not llm_config.is_active:
                    raise ValidationException("选择的LLM配置未激活", PARAMETER_ERROR)
            except NotFoundException:
                raise ValidationException("指定的LLM配置不存在或不属于当前用户", PARAMETER_ERROR)
            except Exception as e:
                raise ValidationException(f"指定的LLM配置无效: {str(e)}", PARAMETER_ERROR)
        
        # 禁止更新用户ID
        if "user_id" in config_data:
            del config_data["user_id"]
        
        # 更新配置
        config = self.config_repo.update(config_id, user_id, config_data)
        return self._format_config(config)
    
    def _validate_config_data(self, data: Dict[str, Any], is_update: bool = False) -> None:
        """验证配置数据"""
        if not is_update:
            # 必填字段验证
            required_fields = ["name", "user_prompt_template"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                raise ValidationException(
                    f"缺少必填字段: {', '.join(missing_fields)}", 
                    PARAMETER_ERROR
                )
        
        # 温度参数验证
        if "temperature" in data:
            temp = data["temperature"]
            if not isinstance(temp, (int, float)) or temp < 0 or temp > 1:
                raise ValidationException("temperature必须在0-1之间", PARAMETER_ERROR)
        
        # 令牌数验证
        if "max_tokens" in data:
            tokens = data["max_tokens"]
            if not isinstance(tokens, int) or tokens < 100 or tokens > 4000:
                raise ValidationException("max_tokens必须在100-4000之间", PARAMETER_ERROR)
        
        # 标题长度验证
        if "title_length" in data:
            length = data["title_length"]
            if not isinstance(length, int) or length < 10 or length > 100:
                raise ValidationException("title_length必须在10-100之间", PARAMETER_ERROR)
        
        # 内容长度验证
        if "content_length" in data:
            length = data["content_length"]
            if not isinstance(length, int) or length < 100 or length > 2000:
                raise ValidationException("content_length必须在100-2000之间", PARAMETER_ERROR)
        
        # 标签数量验证
        if "tags_count" in data:
            count = data["tags_count"]
            if not isinstance(count, int) or count < 1 or count > 20:
                raise ValidationException("tags_count必须在1-20之间", PARAMETER_ERROR)
    
    def _format_config(self, config) -> Dict[str, Any]:
        """格式化配置数据"""
        return {
            "id": config.id,
            "name": config.name,
            "description": config.description,
            "user_llm_config_id": config.user_llm_config_id,
            "system_prompt": config.system_prompt,
            "user_prompt_template": config.user_prompt_template,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "title_length": config.title_length,
            "content_length": config.content_length,
            "tags_count": config.tags_count,
            "include_emojis": config.include_emojis,
            "is_active": config.is_active,
            "is_default": config.is_default,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None
        }


class XhsCopyGenerationService:
    """小红书文案生成服务"""
    
    def __init__(
        self, 
        generation_repository: XhsCopyGenerationRepository,
        config_repository: XhsCopyConfigRepository,
        provider_repository: LLMProviderRepository,
        model_repository: LLMModelRepository,
        user_llm_config_repository: Optional[UserLLMConfigRepository] = None
    ):
        """初始化服务"""
        self.generation_repo = generation_repository
        self.config_repo = config_repository
        self.provider_repo = provider_repository
        self.model_repo = model_repository
        self.user_llm_config_repo = user_llm_config_repository
    
    def get_all_generations(
        self, 
        user_id: str, 
        page: int = 1, 
        per_page: int = 20, 
        **filters
    ) -> tuple[List[Dict[str, Any]], int]:
        """获取用户所有生成记录"""
        generations, total = self.generation_repo.get_all_by_user(user_id, page, per_page, **filters)
        return [self._format_generation(gen) for gen in generations], total
    
    def get_generation(self, generation_id: int, user_id: str) -> Dict[str, Any]:
        """获取特定生成记录"""
        generation = self.generation_repo.get_by_id(generation_id, user_id)
        return self._format_generation(generation)
    
    def create_generation(
        self, 
        prompt: str, 
        image_urls: List[str], 
        config_id: Optional[int] = None,
        app_id: Optional[int] = None,
        user_id: str = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建并执行文案生成"""
        start_time = time.time()
        
        # 验证数据
        self._validate_generation_input(prompt, image_urls)
        
        # 获取配置
        config = self._get_generation_config(config_id, user_id)
        
        # 创建生成记录
        generation = self._create_generation_record(
            prompt, image_urls, config.id, app_id, user_id, ip_address, user_agent)
        
        try:
            # 获取LLM服务
            ai_provider = self._get_llm_provider(config, user_id)
            
            # 准备提示词
            messages = self._prepare_prompts(config, prompt, image_urls)
            
            # 获取模型名称
            model_name = self._get_model_name(config, ai_provider)
            
            # 生成文案
            response = self._call_llm_service(
                ai_provider=ai_provider,
                messages=messages,
                model=model_name,
                max_tokens=config.max_tokens,
                temperature=config.temperature
            )
            
            # 解析生成结果
            parsed_result = self._parse_generation_result(response["message"]["content"])
            
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
                duration_ms
            )
            
            return self._format_generation(updated_generation)
            
        except Exception as e:
            logger.error(f"Generation error: {str(e)}\n{traceback.format_exc()}")
            # 更新失败状态
            self._update_generation_failure(
                generation.id, user_id, str(e), int((time.time() - start_time) * 1000))
            
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
                if not url.startswith(('http://', 'https://')):
                    raise ValidationException(f"无效的图片URL: {url}", PARAMETER_ERROR)
    
    def _get_generation_config(self, config_id: Optional[int], user_id: str):
        """获取生成配置"""
        # 如果没有指定配置ID，使用默认配置
        if not config_id:
            default_config = self.config_repo.get_default(user_id)
            if not default_config:
                raise NotFoundException("未找到默认配置，请先创建配置", CONFIG_NOT_FOUND)
            return default_config
        
        # 获取指定配置
        return self.config_repo.get_by_id(config_id, user_id)
    
    def _create_generation_record(
        self, prompt, image_urls, config_id, app_id, user_id, ip_address, user_agent
    ):
        """创建生成记录"""
        generation_data = {
            "prompt": prompt,
            "image_urls": image_urls,
            "config_id": config_id,
            "app_id": app_id,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "status": "processing"
        }
        return self.generation_repo.create(generation_data)
    
    def _get_llm_provider(self, config, user_id):
        """获取LLM服务提供商"""
        # 验证用户LLM配置
        if not config.user_llm_config_id:
            raise APIException("未配置LLM服务，请先绑定LLM配置", GENERATION_FAILED)
            
        if not self.user_llm_config_repo:
            raise APIException("系统未配置LLM服务接口", GENERATION_FAILED)
        
        try:
            user_llm_config = self.user_llm_config_repo.get_by_id(config.user_llm_config_id, user_id)
        except Exception as e:
            raise APIException(f"无法获取LLM配置: {str(e)}", GENERATION_FAILED)
        
        # 创建AI提供商实例
        ai_provider = None
        
        if user_llm_config.provider_type == "OpenAI":
            if not user_llm_config.api_key:
                raise APIException("未配置OpenAI API密钥", GENERATION_FAILED)
                
            ai_provider = LLMProviderFactory.create_provider(
                "openai",
                user_llm_config.api_key,
                api_base_url=user_llm_config.api_base_url,
                api_version=user_llm_config.api_version,
                timeout=user_llm_config.request_timeout,
                max_retries=user_llm_config.max_retries
            )
        elif user_llm_config.provider_type == "Claude":
            if not user_llm_config.api_key:
                raise APIException("未配置Claude API密钥", GENERATION_FAILED)
                
            ai_provider = LLMProviderFactory.create_provider(
                "anthropic",
                user_llm_config.api_key,
                api_base_url=user_llm_config.api_base_url,
                timeout=user_llm_config.request_timeout,
                max_retries=user_llm_config.max_retries
            )
        elif user_llm_config.provider_type in ["Volcano", "Tencent", "Baidu", "Aliyun"]:
            # 这里需要根据不同平台实现对应的初始化
            raise APIException(f"暂不支持{user_llm_config.provider_type}平台", GENERATION_FAILED)
        else:
            raise APIException(f"不支持的LLM提供商类型: {user_llm_config.provider_type}", GENERATION_FAILED)
        
        if not ai_provider:
            raise APIException("初始化LLM提供商失败", GENERATION_FAILED)
            
        return ai_provider
    
    def _prepare_prompts(self, config, prompt, image_urls):
        """准备提示词"""
        system_prompt = config.system_prompt or "你是一位专业的小红书博主，擅长编写吸引人的小红书文案。"
        
        # 替换模板中的变量
        user_prompt = config.user_prompt_template
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
        requirements += f"\n1. 标题长度不超过{config.title_length}个字"
        requirements += f"\n2. 正文内容{config.content_length}字左右"
        requirements += f"\n3. 生成{config.tags_count}个适合的标签"
        if config.include_emojis:
            requirements += "\n4. 适当地使用表情符号增加趣味性"
        requirements += "\n\n请按照以下格式输出：\n【标题】\n【正文】\n【标签】标签1 标签2 标签3..."
        
        user_prompt += requirements
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def _get_model_name(self, config, ai_provider):
        """获取模型名称"""
        provider_name = ai_provider.get_provider_name()
        
        if provider_name == "OpenAI":
            return "gpt-4-turbo"  # 默认使用gpt-4-turbo
        elif provider_name == "Anthropic":
            return "claude-3-opus-20240229"  # 默认使用Claude-3-Opus
        else:
            # 根据提供商类型返回默认模型
            return None  # 将使用提供商的默认模型
    
    def _call_llm_service(self, ai_provider, messages, model, max_tokens, temperature):
        """调用LLM服务"""
        return ai_provider.generate_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            model=model
        )
    
    def _parse_generation_result(self, content):
        """解析生成结果"""
        title = ""
        body = ""
        tags = []
        
        # 尝试解析标题、正文和标签
        if "【标题】" in content:
            title_parts = content.split("【标题】")
            if len(title_parts) > 1:
                title_content = title_parts[1].split("【正文】")[0] if "【正文】" in title_parts[1] else title_parts[1]
                title = title_content.strip()
        
        if "【正文】" in content:
            body_parts = content.split("【正文】")
            if len(body_parts) > 1:
                body_content = body_parts[1].split("【标签】")[0] if "【标签】" in body_parts[1] else body_parts[1]
                body = body_content.strip()
        
        if "【标签】" in content:
            tags_part = content.split("【标签】")[1] if len(content.split("【标签】")) > 1 else ""
            # 提取标签
            tag_candidates = [tag.strip() for tag in tags_part.split() if tag.strip()]
            # 过滤非空标签
            tags = [tag for tag in tag_candidates if tag]
        
        # 如果没有按格式输出，尝试更灵活地解析
        if not title and not body:
            # 可能是自由格式输出，尝试智能提取
            lines = content.split('\n')
            if lines:
                # 第一行可能是标题
                title = lines[0].strip()
                # 剩余内容作为正文
                body = '\n'.join(lines[1:]).strip()
        
        return {
            "title": title,
            "body": body,
            "tags": tags
        }
    
    def _update_generation_success(self, generation_id, user_id, title, body, tags, tokens_used, duration_ms):
        """更新生成成功状态"""
        update_data = {
            "status": "completed",
            "title": title,
            "content": body,
            "tags": tags,
            "tokens_used": tokens_used,
            "duration_ms": duration_ms
        }
        
        return self.generation_repo.update(generation_id, user_id, update_data)
    
    def _update_generation_failure(self, generation_id, user_id, error_message, duration_ms):
        """更新生成失败状态"""
        update_data = {
            "status": "failed",
            "error_message": error_message,
            "duration_ms": duration_ms
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
    
    def rate_generation(self, generation_id: int, user_id: str, rating: int, feedback: Optional[str] = None) -> Dict[str, Any]:
        """对生成结果评分"""
        # 验证评分
        if rating < 1 or rating > 5:
            raise ValidationException("评分必须在1-5之间", PARAMETER_ERROR)
        
        # 更新评分
        update_data = {
            "user_rating": rating
        }
        
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
            "config_id": generation.config_id,
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
            "created_at": generation.created_at.isoformat() if generation.created_at else None
        }