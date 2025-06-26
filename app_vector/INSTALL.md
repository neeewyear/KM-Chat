# MrDoc RAG 智能问答功能安装指南

## 前置要求

1. **Python 3.8+**
2. **Django 3.0+**
3. **Milvus 向量数据库**
4. **OpenAI API 密钥**

## 安装步骤

### 1. 安装 Python 依赖

```bash
pip install openai pymilvus
```

### 2. 配置 Milvus 向量数据库

#### 使用 Docker 安装 Milvus

```bash
# 下载 docker-compose.yml
wget https://github.com/milvus-io/milvus/releases/download/v2.3.3/milvus-standalone-docker-compose.yml -O docker-compose.yml

# 启动 Milvus
docker-compose up -d

# 检查服务状态
docker-compose ps
```

#### 或者使用 Docker 单机版

```bash
docker run -d --name milvus_standalone -p 19530:19530 -p 9091:9091 milvusdb/milvus:latest standalone
```

### 3. 配置 MrDoc

#### 编辑配置文件

编辑 `config/config.ini` 文件，添加以下配置：

```ini
[milvus]
# Milvus向量数据库配置
host = localhost
port = 19530
collection_name = mrdoc_documents
dimension = 1536

[openai]
# OpenAI配置
api_key = your-openai-api-key-here
base_url = https://api.openai.com/v1
model = gpt-3.5-turbo
max_tokens = 2000
temperature = 0.7
```

#### 获取 OpenAI API 密钥

1. 访问 [OpenAI API](https://platform.openai.com/api-keys)
2. 登录或注册账户
3. 创建新的 API 密钥
4. 将密钥填入配置文件

### 4. 数据库迁移

```bash
# 创建迁移文件
python manage.py makemigrations app_vector

# 执行迁移
python manage.py migrate
```

### 5. 测试安装

运行测试脚本验证安装：

```bash
python app_vector/test_rag.py
```

### 6. 启动服务

```bash
python manage.py runserver
```

访问智能问答页面：`http://localhost:8000/vector/chat/`

## 故障排除

### 1. Milvus 连接失败

**错误信息**：`Failed to connect to Milvus`

**解决方案**：
- 检查 Milvus 服务是否正常运行：`docker ps | grep milvus`
- 检查端口是否正确：`netstat -an | grep 19530`
- 重启 Milvus 服务：`docker-compose restart`

### 2. OpenAI API 错误

**错误信息**：`OpenAI API error`

**解决方案**：
- 检查 API 密钥是否正确
- 检查网络连接是否正常
- 检查 API 配额是否充足

### 3. 数据库迁移错误

**错误信息**：`Migration failed`

**解决方案**：
- 检查数据库连接
- 确保数据库用户有足够权限
- 手动删除迁移文件重新生成

### 4. 向量化失败

**错误信息**：`Vectorization failed`

**解决方案**：
- 检查 OpenAI API 配置
- 检查网络连接
- 检查文本内容是否为空

## 性能优化

### 1. Milvus 优化

```yaml
# docker-compose.yml
version: '3.5'
services:
  etcd:
    container_name: milvus-etcd
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
    volumes:
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/etcd:/etcd
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd

  minio:
    container_name: milvus-minio
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    volumes:
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/minio:/minio_data
    command: minio server /minio_data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  standalone:
    container_name: milvus-standalone
    image: milvusdb/milvus:v2.3.3
    command: ["milvus", "run", "standalone"]
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/milvus:/var/lib/milvus
    ports:
      - "19530:19530"
      - "9091:9091"
    depends_on:
      - "etcd"
      - "minio"
```

### 2. 缓存配置

在 `settings.py` 中添加缓存配置：

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### 3. 异步处理

对于大量文档向量化，建议使用异步任务队列：

```python
# 使用 Celery 进行异步处理
from celery import shared_task

@shared_task
def vectorize_document_async(doc_id, content):
    return vector_service.store_document_vector(doc_id, content)
```

## 安全配置

### 1. API 密钥安全

- 不要在代码中硬编码 API 密钥
- 使用环境变量或配置文件
- 定期轮换 API 密钥

### 2. 访问控制

- 确保只有授权用户可以访问 RAG 功能
- 配置适当的 CORS 策略
- 使用 HTTPS 传输

### 3. 数据保护

- 定期备份向量数据
- 加密敏感数据
- 监控 API 使用情况

## 监控和维护

### 1. 日志监控

```python
import logging

logger = logging.getLogger(__name__)
logger.info("RAG service started")
```

### 2. 性能监控

- 监控 API 响应时间
- 监控向量检索性能
- 监控资源使用情况

### 3. 定期维护

- 清理过期会话数据
- 优化向量索引
- 更新依赖包

## 支持

如果遇到问题，请：

1. 查看日志文件
2. 运行测试脚本
3. 检查配置文件
4. 提交 Issue 到项目仓库 