# 已实现文件目录

## 基础结构
- `app/__init__.py` - Flask应用工厂
- `app/extensions.py` - Flask扩展实例
- `app/config.py` - 应用配置

## 核心模块
- `app/core/exceptions.py` - 自定义异常类
- `app/core/status_codes.py` - 业务状态码
- `app/core/responses.py` - 标准响应处理
- `app/api/middleware/error_handling.py` - 错误处理中间件

## AI提供商
- `app/infrastructure/ai_providers/base.py` - AI提供商基类
- `app/infrastructure/ai_providers/openai_provider.py` - OpenAI提供商实现
- `app/infrastructure/ai_providers/anthropic_provider.py` - Anthropic提供商实现
- `app/infrastructure/ai_providers/factory.py` - AI提供商工厂

## 向量存储
- `app/infrastructure/vector_stores/base.py` - 向量存储基类
- `app/infrastructure/vector_stores/pinecone.py` - Pinecone向量存储实现
- `app/infrastructure/vector_stores/factory.py` - 向量存储工厂

## 缓存
- `app/infrastructure/cache/base.py` - 缓存基类
- `app/infrastructure/cache/redis_cache.py` - Redis缓存实现
- `app/infrastructure/cache/memory_cache.py` - 内存缓存实现

## 领域实体
- `app/domains/model_management/entities.py` - 模型管理实体
- `app/domains/knowledge_management/entities.py` - 知识管理实体

## 数据库模型
- `app/infrastructure/database/models/user.py` - 用户模型
- `app/infrastructure/database/models/application.py` - 应用程序模型
- `app/infrastructure/database/models/knowledge_base.py` - 知识库和模型模型

## 认证服务
- `app/domains/auth/interfaces.py` - 认证服务接口
- `app/domains/auth/services.py` - 认证服务实现

## 存储库
- `app/infrastructure/database/repositories/user_repository.py` - 用户存储库