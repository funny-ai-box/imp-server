"""模型管理领域实体"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

class ModelType(Enum):
    """模型类型枚举"""
    TEXT_GENERATION = "text_generation"  # 文本生成
    CHAT_COMPLETION = "chat_completion"  # 对话完成
    EMBEDDINGS = "embeddings"  # 嵌入向量
    TEXT_CLASSIFICATION = "text_classification"  # 文本分类
    IMAGE_CLASSIFICATION = "image_classification"  # 图像分类
    CUSTOM = "custom"  # 自定义类型

class ModelStatus(Enum):
    """模型状态枚举"""
    ACTIVE = "active"  # 活跃可用
    INACTIVE = "inactive"  # 不活跃
    DEPRECATED = "deprecated"  # 已弃用
    MAINTENANCE = "maintenance"  # 维护中

class ModelProvider(Enum):
    """模型提供商枚举"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    CUSTOM = "custom"  # 自定义提供商

@dataclass
class ModelParameter:
    """模型参数定义"""
    name: str  # 参数名称
    description: str  # 参数描述
    type: str  # 参数类型（string, number, boolean等）
    required: bool = False  # 是否必需
    default: Optional[Any] = None  # 默认值
    min_value: Optional[float] = None  # 最小值（针对数值类型）
    max_value: Optional[float] = None  # 最大值（针对数值类型）
    options: List[Any] = field(default_factory=list)  # 可选值列表（针对枚举类型）

@dataclass
class ModelUsageStatistics:
    """模型使用统计信息"""
    total_requests: int = 0  # 总请求次数
    successful_requests: int = 0  # 成功请求次数
    failed_requests: int = 0  # 失败请求次数
    total_tokens: int = 0  # 总token数
    input_tokens: int = 0  # 输入token数
    output_tokens: int = 0  # 输出token数
    average_latency: float = 0.0  # 平均延迟（毫秒）
    last_used_at: Optional[datetime] = None  # 最后使用时间

@dataclass
class Model:
    """AI模型实体"""
    id: str  # 模型ID
    name: str  # 模型名称
    description: str  # 模型描述
    type: ModelType  # 模型类型
    provider: ModelProvider  # 模型提供商
    provider_model_id: str  # 提供商原始模型ID
    version: str  # 模型版本
    status: ModelStatus  # 模型状态
    capabilities: List[str] = field(default_factory=list)  # 模型能力列表
    parameters: List[ModelParameter] = field(default_factory=list)  # 模型参数列表
    max_tokens: int = 4096  # 最大token限制
    supports_streaming: bool = False  # 是否支持流式输出
    context_length: int = 4096  # 上下文长度
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间
    updated_at: datetime = field(default_factory=datetime.now)  # 更新时间
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    usage_statistics: ModelUsageStatistics = field(default_factory=ModelUsageStatistics)  # 使用统计

    def is_active(self) -> bool:
        """检查模型是否处于活跃状态
        
        Returns:
            是否活跃
        """
        return self.status == ModelStatus.ACTIVE
    
    def update_status(self, status: ModelStatus) -> None:
        """更新模型状态
        
        Args:
            status: 新状态
        """
        self.status = status
        self.updated_at = datetime.now()
    
    def update_statistics(self, 
                         successful: bool, 
                         input_tokens: int = 0, 
                         output_tokens: int = 0,
                         latency: float = 0.0) -> None:
        """更新模型使用统计
        
        Args:
            successful: 请求是否成功
            input_tokens: 输入token数
            output_tokens: 输出token数
            latency: 请求延迟（毫秒）
        """
        stats = self.usage_statistics
        
        # 更新请求计数
        stats.total_requests += 1
        if successful:
            stats.successful_requests += 1
        else:
            stats.failed_requests += 1
        
        # 更新token计数
        stats.input_tokens += input_tokens
        stats.output_tokens += output_tokens
        stats.total_tokens += (input_tokens + output_tokens)
        
        # 更新延迟统计（移动平均）
        if stats.total_requests > 1:
            stats.average_latency = (
                (stats.average_latency * (stats.total_requests - 1) + latency) / 
                stats.total_requests
            )
        else:
            stats.average_latency = latency
        
        # 更新最后使用时间
        stats.last_used_at = datetime.now()
        
        # 更新模型的更新时间
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """将模型实体转换为字典
        
        Returns:
            字典表示
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "provider": self.provider.value,
            "provider_model_id": self.provider_model_id,
            "version": self.version,
            "status": self.status.value,
            "capabilities": self.capabilities,
            "parameters": [
                {
                    "name": param.name,
                    "description": param.description,
                    "type": param.type,
                    "required": param.required,
                    "default": param.default,
                    "min_value": param.min_value,
                    "max_value": param.max_value,
                    "options": param.options
                }
                for param in self.parameters
            ],
            "max_tokens": self.max_tokens,
            "supports_streaming": self.supports_streaming,
            "context_length": self.context_length,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "usage_statistics": {
                "total_requests": self.usage_statistics.total_requests,
                "successful_requests": self.usage_statistics.successful_requests,
                "failed_requests": self.usage_statistics.failed_requests,
                "total_tokens": self.usage_statistics.total_tokens,
                "input_tokens": self.usage_statistics.input_tokens,
                "output_tokens": self.usage_statistics.output_tokens,
                "average_latency": self.usage_statistics.average_latency,
                "last_used_at": self.usage_statistics.last_used_at.isoformat() if self.usage_statistics.last_used_at else None
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Model':
        """从字典创建模型实体
        
        Args:
            data: 字典数据
            
        Returns:
            模型实体实例
        """
        # 处理枚举值
        model_type = ModelType(data["type"])
        provider = ModelProvider(data["provider"])
        status = ModelStatus(data["status"])
        
        # 处理日期时间
        created_at = datetime.fromisoformat(data["created_at"]) if isinstance(data["created_at"], str) else data["created_at"]
        updated_at = datetime.fromisoformat(data["updated_at"]) if isinstance(data["updated_at"], str) else data["updated_at"]
        
        # 处理参数列表
        parameters = [
            ModelParameter(
                name=param["name"],
                description=param["description"],
                type=param["type"],
                required=param.get("required", False),
                default=param.get("default"),
                min_value=param.get("min_value"),
                max_value=param.get("max_value"),
                options=param.get("options", [])
            )
            for param in data.get("parameters", [])
        ]
        
        # 处理使用统计
        usage_stats_data = data.get("usage_statistics", {})
        last_used_at = None
        if usage_stats_data.get("last_used_at"):
            last_used_at = datetime.fromisoformat(usage_stats_data["last_used_at"]) if isinstance(usage_stats_data["last_used_at"], str) else usage_stats_data["last_used_at"]
            
        usage_statistics = ModelUsageStatistics(
            total_requests=usage_stats_data.get("total_requests", 0),
            successful_requests=usage_stats_data.get("successful_requests", 0),
            failed_requests=usage_stats_data.get("failed_requests", 0),
            total_tokens=usage_stats_data.get("total_tokens", 0),
            input_tokens=usage_stats_data.get("input_tokens", 0),
            output_tokens=usage_stats_data.get("output_tokens", 0),
            average_latency=usage_stats_data.get("average_latency", 0.0),
            last_used_at=last_used_at
        )
        
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            type=model_type,
            provider=provider,
            provider_model_id=data["provider_model_id"],
            version=data["version"],
            status=status,
            capabilities=data.get("capabilities", []),
            parameters=parameters,
            max_tokens=data.get("max_tokens", 4096),
            supports_streaming=data.get("supports_streaming", False),
            context_length=data.get("context_length", 4096),
            created_at=created_at,
            updated_at=updated_at,
            metadata=data.get("metadata", {}),
            usage_statistics=usage_statistics
        )