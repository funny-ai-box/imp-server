#!/bin/bash

# 创建项目结构脚本
# 此脚本将创建智能中间件平台(IMP)的目录结构和文件

echo "开始创建项目目录结构..."

# 创建基础目录
mkdir -p app/{api/{v1,middleware},core,domains,infrastructure,utils}
mkdir -p app/api/v1/endpoints
mkdir -p app/domains/{analytics,auth,content_generation,knowledge_management,model_management}/{entities,interfaces,repositories,services}
mkdir -p app/infrastructure/{ai_providers,cache,database,storage,vector_stores}
mkdir -p app/infrastructure/database/{models,repositories,session}
mkdir -p docs/api
mkdir -p scripts
mkdir -p instance

# 创建核心文件
touch app/__init__.py
touch app/extensions.py
touch app/config.py

# 创建API层文件
touch app/api/__init__.py
touch app/api/middleware/__init__.py
touch app/api/middleware/error_handling.py
touch app/api/middleware/authentication.py
touch app/api/middleware/rate_limiting.py
touch app/api/v1/__init__.py
touch app/api/v1/auth.py
touch app/api/v1/models.py
touch app/api/v1/knowledge_bases.py
touch app/api/v1/applications.py
touch app/api/v1/endpoints/__init__.py
touch app/api/v1/endpoints/xiaohongshu.py
touch app/api/v1/endpoints/image_classification.py
touch app/api/v1/endpoints/comment_analysis.py

# 创建核心模块文件
touch app/core/__init__.py
touch app/core/exceptions.py
touch app/core/status_codes.py
touch app/core/responses.py
touch app/core/logging.py
touch app/core/pagination.py
touch app/core/security.py
touch app/core/validation.py

# 创建AI供应商相关文件
touch app/infrastructure/ai_providers/__init__.py
touch app/infrastructure/ai_providers/base.py
touch app/infrastructure/ai_providers/openai_provider.py
touch app/infrastructure/ai_providers/anthropic_provider.py
touch app/infrastructure/ai_providers/factory.py

# 创建向量存储相关文件
touch app/infrastructure/vector_stores/__init__.py
touch app/infrastructure/vector_stores/base.py
touch app/infrastructure/vector_stores/pinecone.py
touch app/infrastructure/vector_stores/factory.py

# 创建缓存相关文件
touch app/infrastructure/cache/__init__.py
touch app/infrastructure/cache/base.py
touch app/infrastructure/cache/redis_cache.py
touch app/infrastructure/cache/memory_cache.py

# 创建数据库模型文件
touch app/infrastructure/database/models/__init__.py
touch app/infrastructure/database/models/user.py
touch app/infrastructure/database/models/application.py
touch app/infrastructure/database/models/knowledge_base.py
touch app/infrastructure/database/models/model.py
touch app/infrastructure/database/models/audit_log.py

# 创建数据库存储库文件
touch app/infrastructure/database/repositories/__init__.py
touch app/infrastructure/database/repositories/user_repository.py
touch app/infrastructure/database/repositories/knowledge_repository.py
touch app/infrastructure/database/repositories/model_repository.py
touch app/infrastructure/database/session.py

# 创建领域实体文件
touch app/domains/auth/__init__.py
touch app/domains/auth/entities.py
touch app/domains/auth/interfaces.py
touch app/domains/auth/services.py
touch app/domains/auth/repositories.py

touch app/domains/model_management/__init__.py
touch app/domains/model_management/entities.py
touch app/domains/model_management/interfaces.py
touch app/domains/model_management/services.py
touch app/domains/model_management/repositories.py
touch app/domains/model_management/value_objects.py

touch app/domains/knowledge_management/__init__.py
touch app/domains/knowledge_management/entities.py
touch app/domains/knowledge_management/interfaces.py
touch app/domains/knowledge_management/services.py
touch app/domains/knowledge_management/repositories.py
touch app/domains/knowledge_management/vectorization.py

touch app/domains/content_generation/__init__.py
touch app/domains/content_generation/entities.py
touch app/domains/content_generation/interfaces.py
touch app/domains/content_generation/services.py
touch app/domains/content_generation/repositories.py
touch app/domains/content_generation/templates.py

touch app/domains/analytics/__init__.py
touch app/domains/analytics/entities.py
touch app/domains/analytics/interfaces.py
touch app/domains/analytics/services.py
touch app/domains/analytics/repositories.py
touch app/domains/analytics/processors.py

# 创建存储相关文件
touch app/infrastructure/storage/__init__.py
touch app/infrastructure/storage/base.py
touch app/infrastructure/storage/local.py
touch app/infrastructure/storage/s3.py

# 创建工具文件
touch app/utils/__init__.py
touch app/utils/converters.py
touch app/utils/validators.py
touch app/utils/formatters.py

# 创建文档文件
touch docs/api/openapi.yaml

# 创建脚本文件
touch scripts/setup_db.py
touch scripts/seed_data.py
touch scripts/generate_api_docs.py
touch scripts/setup_dev.sh

# 创建主应用文件
touch wsgi.py

echo "项目目录结构创建完成！"

# 输出目录结构
echo "生成的目录结构如下："
find app -type f | sort