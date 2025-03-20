# app/domains/content_generation/services/image_classification_service.py
import time
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from app.infrastructure.database.repositories.image_classification_repository import (
    ImageClassificationConfigRepository,
    ImageClassificationRepository
)
from app.infrastructure.database.repositories.ai_provider_repository import AIProviderRepository
from app.infrastructure.database.repositories.ai_model_repository import AIModelRepository
from app.infrastructure.ai_providers.factory import AIProviderFactory
from app.core.exceptions import ValidationException, NotFoundException, APIException
from app.core.status_codes import (
    PARAMETER_ERROR, CLASSIFICATION_FAILED, 
    INVALID_IMAGE_URL, INVALID_CATEGORIES
)

class ImageClassificationService:
    """图片分类服务"""
    
    def __init__(
        self, 
        classification_repository: ImageClassificationRepository,
        config_repository: ImageClassificationConfigRepository,
        provider_repository: AIProviderRepository,
        model_repository: AIModelRepository
    ):
        """初始化服务"""
        self.classification_repo = classification_repository
        self.config_repo = config_repository
        self.provider_repo = provider_repository
        self.model_repo = model_repository
    
    def get_all_configs(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户所有配置"""
        configs = self.config_repo.get_all_by_user(user_id)
        return [self._format_config(config) for config in configs]
    
    def get_config(self, config_id: int, user_id: int) -> Dict[str, Any]:
        """获取特定配置"""
        config = self.config_repo.get_by_id(config_id, user_id)
        return self._format_config(config)
    
    def get_default_config(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取默认配置"""
        config = self.config_repo.get_default(user_id)
        if not config:
            return None
        return self._format_config(config)
    
    def create_config(self, config_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
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
    
    def update_config(self, config_id: int, config_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
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
    
    def delete_config(self, config_id: int, user_id: int) -> bool:
        """删除配置"""
        return self.config_repo.delete(config_id, user_id)
    
    def set_default_config(self, config_id: int, user_id: int) -> Dict[str, Any]:
        """设置默认配置"""
        config = self.config_repo.set_as_default(config_id, user_id)
        return self._format_config(config)
    
    def classify_image(
        self, 
        image_url: str, 
        categories: List[Dict[str, Any]], 
        config_id: Optional[int] = None,
        app_id: Optional[int] = None,
        user_id: int = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """分类图片"""
        start_time = time.time()
        
        # 验证数据
        if not image_url:
            raise ValidationException("图片URL不能为空", INVALID_IMAGE_URL)
        
        if not categories or not isinstance(categories, list) or len(categories) == 0:
            raise ValidationException("分类类别不能为空", INVALID_CATEGORIES)
        
        # 验证每个分类对象必须包含id和name
        for category in categories:
            if not isinstance(category, dict) or "id" not in category or "name" not in category:
                raise ValidationException("分类类别必须包含id和name", INVALID_CATEGORIES)
        
        # 如果没有指定配置ID，使用默认配置
        if not config_id:
            default_config = self.config_repo.get_default(user_id)
            if not default_config:
                raise NotFoundException("未找到默认配置，请先创建配置", CONFIG_NOT_FOUND)
            config_id = default_config.id
        
        # 获取配置
        config = self.config_repo.get_by_id(config_id, user_id)
        
        # 准备分类数据
        classification_data = {
            "image_url": image_url,
            "categories": categories,
            "config_id": config_id,
            "app_id": app_id,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "status": "processing"
        }
        
        # 创建分类记录
        classification = self.classification_repo.create(classification_data)
        
        try:
            # 获取提供商
            provider = self.provider_repo.get_by_id(config.provider_id, user_id)
            
            # 获取模型
            model = self.model_repo.get_by_id(config.model_id, config.provider_id)
            
            # 创建AI提供商实例
            ai_provider = AIProviderFactory.create_provider(
                provider.provider_type,
                provider.api_key,
                api_base_url=provider.api_base_url,
                api_version=provider.api_version
            )
            
            # 准备提示词
            system_prompt = config.system_prompt or "你是一位专业的图片分类器。你将根据提供的图片URL和候选类别，判断图片最可能属于哪个类别。"
            
            # 构建用户提示词
            categories_text = "\n".join([f"- ID: {cat['id']}, 类别: {cat['name']}" for cat in categories])
            
            user_prompt = config.user_prompt_template
            if "{image_url}" in user_prompt and "{categories}" in user_prompt:
                user_prompt = user_prompt.replace("{image_url}", image_url)
                user_prompt = user_prompt.replace("{categories}", categories_text)
            else:
                user_prompt = f"""请分析以下图片URL，并从给定的类别中选择最匹配的一个：

图片URL: {image_url}

候选类别:
{categories_text}

请以以下格式返回结果:
分类结果: [类别ID]
分类名称: [类别名称]
置信度: [0-1之间的数值]
解释: [简短说明为什么图片属于该类别]
"""
            
            # 生成分类结果
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
            
            # 提取分类结果
            result_category_id = None
            result_category_name = None
            confidence = None
            explanation = None
            all_results = []
            
            # 尝试解析结果
            if "分类结果:" in content or "分类结果：" in content:
                # 规范化冒号
                content = content.replace("：", ":")
                
                # 提取结果ID
                id_parts = content.split("分类结果:")[1].split("\n")[0] if "分类结果:" in content else ""
                result_category_id = id_parts.strip()
                
                # 提取结果名称
                name_parts = content.split("分类名称:")[1].split("\n")[0] if "分类名称:" in content else ""
                result_category_name = name_parts.strip()
                
                # 提取置信度
                confidence_parts = content.split("置信度:")[1].split("\n")[0] if "置信度:" in content else ""
                try:
                    # 尝试提取数字
                    import re
                    confidence_match = re.search(r'(\d+(\.\d+)?)', confidence_parts)
                    if confidence_match:
                        confidence = float(confidence_match.group(1))
                        # 确保置信度在0-1之间
                        if confidence > 1:
                            confidence = confidence / 100 if confidence <= 100 else 1
                except:
                    confidence = 0.7  # 默认值
                
                # 提取解释
                explanation_parts = content.split("解释:")[1] if "解释:" in content else ""
                explanation = explanation_parts.strip()
                
                # 尝试为每个类别解析置信度
                for category in categories:
                    category_confidence = 0.1  # 默认很低的置信度
                    
                    # 如果是匹配的分类，使用提取的置信度
                    if category["id"] == result_category_id:
                        category_confidence = confidence or 0.7
                    
                    all_results.append({
                        "id": category["id"],
                        "name": category["name"],
                        "confidence": category_confidence
                    })
            
            # 如果无法解析结构化结果，尝试查找类别ID和名称
            if not result_category_id or not result_category_name:
                # 简单地搜索每个类别ID和名称是否在响应中，取最可能的
                max_confidence = 0
                for category in categories:
                    # 计算简单匹配度（类别名称在内容中出现的次数）
                    matches = content.lower().count(category["name"].lower())
                    category_confidence = min(0.5 + (matches * 0.1), 0.9)  # 简单启发式
                    
                    all_results.append({
                        "id": category["id"],
                        "name": category["name"],
                        "confidence": category_confidence
                    })
                    
                    if category_confidence > max_confidence:
                        max_confidence = category_confidence
                        result_category_id = category["id"]
                        result_category_name = category["name"]
                        confidence = category_confidence
            
            # 计算tokens使用量
            tokens_used = response["usage"]["total_tokens"] if "usage" in response else 0
            
            # 计算处理时间
            duration_ms = int((time.time() - start_time) * 1000)
            
            # 更新分类记录
            update_data = {
                "status": "completed",
                "result_category_id": result_category_id,
                "result_category_name": result_category_name,
                "confidence": confidence,
                "all_results": all_results,
                "tokens_used": tokens_used,
                "duration_ms": duration_ms
            }
            
            updated_classification = self.classification_repo.update(classification.id, user_id, update_data)
            return self._format_classification(updated_classification)
            
        except Exception as e:
            # 更新失败状态
            error_message = str(e)
            duration_ms = int((time.time() - start_time) * 1000)
            
            update_data = {
                "status": "failed",
                "error_message": error_message,
                "duration_ms": duration_ms
            }
            
            self.classification_repo.update(classification.id, user_id, update_data)
            
            # 重新抛出异常
            raise APIException(f"图片分类失败: {error_message}", CLASSIFICATION_FAILED)
    
    def get_all_classifications(
        self, 
        user_id: int, 
        page: int = 1, 
        per_page: int = 20, 
        **filters
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取用户所有分类记录"""
        classifications, total = self.classification_repo.get_all_by_user(user_id, page, per_page, **filters)
        return [self._format_classification(cls) for cls in classifications], total
    
    def get_classification(self, classification_id: int, user_id: int) -> Dict[str, Any]:
        """获取特定分类记录"""
        classification = self.classification_repo.get_by_id(classification_id, user_id)
        return self._format_classification(classification)
    
    def delete_classification(self, classification_id: int, user_id: int) -> bool:
        """删除分类记录"""
        return self.classification_repo.delete(classification_id, user_id)
    
    def get_statistics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """获取分类统计数据"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        return self.classification_repo.get_statistics(user_id, start_date, end_date)
    
    def rate_classification(self, classification_id: int, user_id: int, rating: int, feedback: Optional[str] = None) -> Dict[str, Any]:
        """对分类结果评分"""
        # 验证评分
        if rating < 1 or rating > 5:
            raise ValidationException("评分必须在1-5之间", PARAMETER_ERROR)
        
        # 更新评分
        update_data = {
            "user_rating": rating
        }
        
        if feedback:
            update_data["user_feedback"] = feedback
        
        classification = self.classification_repo.update(classification_id, user_id, update_data)
        return self._format_classification(classification)
    
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
        
        # 置信度阈值验证
        if "confidence_threshold" in data:
            threshold = data["confidence_threshold"]
            if not (0 <= threshold <= 1):
                raise ValidationException("confidence_threshold必须在0-1之间", PARAMETER_ERROR)
        
        # 令牌数验证
        if "max_tokens" in data:
            tokens = data["max_tokens"]
            if tokens < 100 or tokens > 2000:
                raise ValidationException("max_tokens必须在100-2000之间", PARAMETER_ERROR)
    
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
            "confidence_threshold": config.confidence_threshold,
            "system_prompt": config.system_prompt,
            "user_prompt_template": config.user_prompt_template,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "is_active": config.is_active,
            "is_default": config.is_default,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None
        }
    
    def _format_classification(self, classification) -> Dict[str, Any]:
        """格式化分类记录数据"""
        return {
            "id": classification.id,
            "image_url": classification.image_url,
            "categories": classification.categories,
            "config_id": classification.config_id,
            "app_id": classification.app_id,
            "result_category_id": classification.result_category_id,
            "result_category_name": classification.result_category_name,
            "confidence": classification.confidence,
            "all_results": classification.all_results,
            "status": classification.status,
            "error_message": classification.error_message,
            "tokens_used": classification.tokens_used,
            "duration_ms": classification.duration_ms,
            "ip_address": classification.ip_address,
            "user_rating": classification.user_rating,
            "user_feedback": classification.user_feedback,
            "created_at": classification.created_at.isoformat() if classification.created_at else None
        }