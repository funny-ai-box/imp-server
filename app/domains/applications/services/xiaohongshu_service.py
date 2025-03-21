# app/domains/content_generation/services/xiaohongshu_service.py
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.infrastructure.database.repositories.xiaohongshu_repository import (
    XiaohongshuConfigRepository, 
    XiaohongshuGenerationRepository,
    XiaohongshuTestRepository
)
from app.infrastructure.database.repositories.llm_repository import LLMProviderRepository,LLMModelRepository

from app.infrastructure.llm_providers.factory import LLMProviderFactory
from app.core.exceptions import ValidationException, NotFoundException, APIException
from app.core.status_codes import CONFIG_NOT_FOUND, PARAMETER_ERROR, GENERATION_FAILED

class XiaohongshuConfigService:
    """小红书配置服务"""
    
    def __init__(
        self, 
        config_repository: XiaohongshuConfigRepository,
        provider_repository: LLMProviderRepository,
        model_repository: LLMModelRepository
    ):
        """初始化服务"""
        self.config_repo = config_repository
        self.provider_repo = provider_repository
        self.model_repo = model_repository
    
    def get_all_configs(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户所有配置"""
        configs = self.config_repo.get_all_by_user(user_id)
        return [self._format_config(config) for config in configs]
    
    def get_config(self, config_id: int, user_id: str) -> Dict[str, Any]:
        """获取特定配置"""
        config = self.config_repo.get_by_id(config_id, user_id)
        return self._format_config(config)
    
    def get_default_config(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取默认配置"""
        config = self.config_repo.get_default(user_id)
        if not config:
            return None
        return self._format_config(config)
    
    def create_config(self, config_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """创建新配置"""
        # 验证数据
        self._validate_config_data(config_data)
        
        # 验证提供商和模型
        provider_id = config_data.get("provider_id")
        model_id = config_data.get("model_id")
        
        # 确保提供商存在且属于用户
        provider = self.provider_repo.get_by_id(provider_id, user_id)
        
        # 确保模型存在且属于提供商
        model = self.model_repo.get_by_id(model_id, provider_id)
        
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
        
        # 验证提供商和模型
        provider_id = config_data.get("provider_id")
        model_id = config_data.get("model_id")
        
        if provider_id:
            # 确保提供商存在且属于用户
            self.provider_repo.get_by_id(provider_id, user_id)
        
        if model_id and provider_id:
            # 确保模型存在且属于提供商
            self.model_repo.get_by_id(model_id, provider_id)
        elif model_id:
            # 如果只提供了model_id，获取当前配置的provider_id
            current_config = self.config_repo.get_by_id(config_id, user_id)
            # 确保模型存在且属于提供商
            self.model_repo.get_by_id(model_id, current_config.provider_id)
        
        # 禁止更新用户ID
        if "user_id" in config_data:
            del config_data["user_id"]
        
        # 更新配置
        config = self.config_repo.update(config_id, user_id, config_data)
        return self._format_config(config)
    
    def delete_config(self, config_id: int, user_id: str) -> bool:
        """删除配置"""
        # 获取配置
        config = self.config_repo.get_by_id(config_id, user_id)
        
        # 如果是默认配置，检查是否有其他配置可设为默认
        if config.is_default:
            other_configs = [c for c in self.config_repo.get_all_by_user(user_id) if c.id != config_id]
            if other_configs:
                # 将第一个配置设为默认
                self.config_repo.set_as_default(other_configs[0].id, user_id)
        
        # 删除配置
        return self.config_repo.delete(config_id, user_id)
    
    def set_default_config(self, config_id: int, user_id: str) -> Dict[str, Any]:
        """设置默认配置"""
        config = self.config_repo.set_as_default(config_id, user_id)
        return self._format_config(config)
    
    def _validate_config_data(self, data: Dict[str, Any], is_update: bool = False) -> None:
        """验证配置数据"""
        if not is_update:
            # 必填字段验证
            required_fields = ["name", "provider_id", "model_id", "user_prompt_template"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                raise ValidationException(
                    f"缺少必填字段: {', '.join(missing_fields)}", 
                    PARAMETER_ERROR
                )
        
        # 温度参数验证
        if "temperature" in data:
            temp = data["temperature"]
            if not (0 <= temp <= 1):
                raise ValidationException("temperature必须在0-1之间", PARAMETER_ERROR)
        
        # 令牌数验证
        if "max_tokens" in data:
            tokens = data["max_tokens"]
            if tokens < 100 or tokens > 4000:
                raise ValidationException("max_tokens必须在100-4000之间", PARAMETER_ERROR)
        
        # 标题长度验证
        if "title_length" in data:
            length = data["title_length"]
            if length < 10 or length > 100:
                raise ValidationException("title_length必须在10-100之间", PARAMETER_ERROR)
        
        # 内容长度验证
        if "content_length" in data:
            length = data["content_length"]
            if length < 100 or length > 2000:
                raise ValidationException("content_length必须在100-2000之间", PARAMETER_ERROR)
        
        # 标签数量验证
        if "tags_count" in data:
            count = data["tags_count"]
            if count < 1 or count > 20:
                raise ValidationException("tags_count必须在1-20之间", PARAMETER_ERROR)
    
    def _format_config(self, config) -> Dict[str, Any]:
        """格式化配置数据"""
        return {
            "id": config.id,
            "name": config.name,
            "description": config.description,
            "provider_id": config.provider_id,
            "provider_name": config.provider.name if hasattr(config, "provider") and config.provider else None,
            "model_id": config.model_id,
            "model_name": config.model.name if hasattr(config, "model") and config.model else None,
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


class XiaohongshuGenerationService:
    """小红书文案生成服务"""
    
    def __init__(
        self, 
        generation_repository: XiaohongshuGenerationRepository,
        config_repository: XiaohongshuConfigRepository,
        provider_repository: LLMProviderRepository,
        model_repository: LLMModelRepository
    ):
        """初始化服务"""
        self.generation_repo = generation_repository
        self.config_repo = config_repository
        self.provider_repo = provider_repository
        self.model_repo = model_repository
    
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
        if not prompt:
            raise ValidationException("提示词不能为空", PARAMETER_ERROR)
        
        # 如果没有指定配置ID，使用默认配置
        if not config_id:
            default_config = self.config_repo.get_default(user_id)
            if not default_config:
                raise NotFoundException("未找到默认配置，请先创建配置", CONFIG_NOT_FOUND)
            config_id = default_config.id
        
        # 获取配置
        config = self.config_repo.get_by_id(config_id, user_id)
        
        # 准备生成数据
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
        
        # 创建生成记录
        generation = self.generation_repo.create(generation_data)
        
        try:
            # 获取提供商
            provider = self.provider_repo.get_by_id(config.provider_id, user_id)
            
            # 获取模型
            model = self.model_repo.get_by_id(config.model_id, config.provider_id)
            
            # 创建AI提供商实例
            ai_provider = LLMProviderFactory.create_provider(
                provider.provider_type,
                provider.api_key,
                api_base_url=provider.api_base_url,
                api_version=provider.api_version
            )
            
            # 准备提示词
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
            
            # 生成文案
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = ai_provider.generate_chat_completion(
                messages=messages,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                model=model.model_id
            )
            
            # 解析生成结果
            content = response["message"]["content"]
            
            # 提取标题、正文和标签
            title = ""
            body = ""
            tags = []
            
            # 简单解析结果（可根据实际输出调整）
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
            
            # 计算tokens使用量
            tokens_used = response["usage"]["total_tokens"] if "usage" in response else 0
            
            # 计算处理时间
            duration_ms = int((time.time() - start_time) * 1000)
            
            # 更新生成记录
            update_data = {
                "status": "completed",
                "title": title,
                "content": body,
                "tags": tags,
                "tokens_used": tokens_used,
                "duration_ms": duration_ms
            }
            
            updated_generation = self.generation_repo.update(generation.id, user_id, update_data)
            return self._format_generation(updated_generation)
            
        except Exception as e:
            # 更新失败状态
            error_message = str(e)
            duration_ms = int((time.time() - start_time) * 1000)
            
            update_data = {
                "status": "failed",
                "error_message": error_message,
                "duration_ms": duration_ms
            }
            
            self.generation_repo.update(generation.id, user_id, update_data)
            
            # 重新抛出异常
            raise APIException(f"生成文案失败: {error_message}", GENERATION_FAILED)
    
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


class XiaohongshuTestService:
    """小红书测试服务"""
    
    def __init__(
        self, 
        test_repository: XiaohongshuTestRepository,
        generation_service: XiaohongshuGenerationService,
        config_repository: XiaohongshuConfigRepository
    ):
        """初始化服务"""
        self.test_repo = test_repository
        self.generation_service = generation_service
        self.config_repo = config_repository
    
    def get_all_tests(self, user_id: str, page: int = 1, per_page: int = 20) -> tuple[List[Dict[str, Any]], int]:
        """获取用户所有测试结果"""
        tests, total = self.test_repo.get_all_by_user(user_id, page, per_page)
        return [self._format_test(test) for test in tests], total
    
    def get_test(self, test_id: int, user_id: str) -> Dict[str, Any]:
        """获取特定测试结果"""
        test = self.test_repo.get_by_id(test_id, user_id)
        return self._format_test(test)
    
    def create_test(
        self, 
        test_name: str, 
        prompt: str, 
        image_urls: List[str], 
        config_ids: List[int], 
        user_id: str
    ) -> Dict[str, Any]:
        """创建并执行配置对比测试"""
        # 验证数据
        if not test_name:
            raise ValidationException("测试名称不能为空", PARAMETER_ERROR)
        
        if not prompt:
            raise ValidationException("提示词不能为空", PARAMETER_ERROR)
        
        if not config_ids or len(config_ids) < 2:
            raise ValidationException("至少需要两个配置进行对比", PARAMETER_ERROR)
        
        # 验证配置是否存在
        for config_id in config_ids:
            self.config_repo.get_by_id(config_id, user_id)
        
        # 创建测试记录
        test_data = {
            "test_name": test_name,
            "prompt": prompt,
            "image_urls": image_urls,
            "config_ids": config_ids,
            "user_id": user_id
        }
        
        test = self.test_repo.create(test_data)
        
        # 执行测试
        results = []
        
        for config_id in config_ids:
            try:
                # 生成文案
                generation = self.generation_service.create_generation(
                    prompt=prompt,
                    image_urls=image_urls,
                    config_id=config_id,
                    user_id=user_id
                )
                
                # 记录结果
                results.append({
                    "config_id": config_id,
                    "generation_id": generation["id"],
                    "status": "success",
                    "title": generation["title"],
                    "content": generation["content"],
                    "tags": generation["tags"],
                    "tokens_used": generation["tokens_used"],
                    "duration_ms": generation["duration_ms"]
                })
                
            except Exception as e:
                # 记录错误
                results.append({
                    "config_id": config_id,
                    "status": "failed",
                    "error_message": str(e)
                })
        
        # 更新测试结果
        update_data = {
            "results": results
        }
        
        updated_test = self.test_repo.update(test.id, user_id, update_data)
        return self._format_test(updated_test)
    
    def select_winner(self, test_id: int, winner_config_id: int, user_id: str) -> Dict[str, Any]:
        """选择测试的获胜配置"""
        # 获取测试
        test = self.test_repo.get_by_id(test_id, user_id)
        
        # 验证获胜配置在测试中
        if winner_config_id not in test.config_ids:
            raise ValidationException("获胜配置不在测试中", PARAMETER_ERROR)
        
        # 更新获胜配置
        update_data = {
            "winner_config_id": winner_config_id
        }
        
        updated_test = self.test_repo.update(test.id, user_id, update_data)
        return self._format_test(updated_test)
    
    def delete_test(self, test_id: int, user_id: str) -> bool:
        """删除测试结果"""
        return self.test_repo.delete(test_id, user_id)
    
    def _format_test(self, test) -> Dict[str, Any]:
        """格式化测试数据"""
        # 获取配置名称
        config_names = {}
        try:
            for config_id in test.config_ids:
                config = self.config_repo.get_by_id(config_id, test.user_id)
                config_names[config_id] = config.name
        except:
            pass
        
        return {
            "id": test.id,
            "test_name": test.test_name,
            "prompt": test.prompt,
            "image_urls": test.image_urls,
            "config_ids": test.config_ids,
            "config_names": config_names,
            "results": test.results,
            "winner_config_id": test.winner_config_id,
            "created_at": test.created_at.isoformat() if test.created_at else None,
            "updated_at": test.updated_at.isoformat() if test.updated_at else None
        }