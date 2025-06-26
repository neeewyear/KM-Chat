# MrDoc 向量数据库集成

本项目为MrDoc添加了基于Milvus的向量数据库功能，支持文档内容的语义搜索。

## 功能特性

- 自动向量化：新建或更新文档时自动生成向量并存储到Milvus
- 语义搜索：基于文档内容的语义相似度搜索
- 批量处理：支持批量向量化现有文档
- API接口：提供RESTful API接口
- 管理界面：Django Admin管理界面

## 安装配置

### 1. 安装依赖

```bash
pip install -r requirements_vector.txt
```

### 2. 安装并启动Milvus

#### 使用Docker Compose（推荐）

```bash
# 下载docker-compose.yml
wget https://github.com/milvus-io/milvus/releases/download/v2.3.0/milvus-standalone-docker-compose.yml -O docker-compose.yml

# 启动Milvus
docker-compose up -d
```

#### 使用Helm（Kubernetes）

```bash
helm repo add milvus https://milvus-io.github.io/milvus-helm-charts/
helm repo update
helm install my-release milvus/milvus
```

### 3. 配置MrDoc

在 `config/config.ini` 中添加Milvus配置：

```ini
[milvus]
# Milvus服务器地址
host = localhost
# Milvus服务器端口
port = 19530
# 向量集合名称
collection_name = mrdoc_documents
# 向量维度
dimension = 1536
```

### 4. 数据库迁移

```bash
python manage.py makemigrations app_vector
python manage.py migrate
```

### 5. 初始化Milvus集合

```bash
python manage.py init_milvus
```

### 6. 批量向量化现有文档

```bash
# 向量化所有文档
python manage.py batch_vectorize

# 向量化指定项目的文档
python manage.py batch_vectorize --project 1

# 限制处理数量
python manage.py batch_vectorize --limit 50
```

## 使用方法

### 1. 自动向量化

文档创建或更新时会自动生成向量并存储到Milvus，无需手动操作。

### 2. 向量搜索

#### Web界面

访问 `/vector/` 页面进行向量搜索。

#### API接口

```bash
# 搜索相似文档
curl -X POST http://localhost:8000/vector/api/search/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token your_token" \
  -d '{
    "query": "搜索内容",
    "top_k": 10
  }'

# 手动存储文档向量
curl -X POST http://localhost:8000/vector/api/store/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token your_token" \
  -d '{
    "doc_id": 1,
    "content": "文档内容"
  }'

# 删除文档向量
curl -X DELETE http://localhost:8000/vector/api/delete/1/ \
  -H "Authorization: Token your_token"
```

### 3. 管理界面

访问Django Admin界面管理向量数据：
- 文档向量管理
- 向量集合管理

## 高级配置

### 1. 使用更好的嵌入模型

当前实现使用简单的哈希方法生成向量。要使用更好的嵌入模型，可以修改 `app_vector/services.py` 中的 `get_text_embedding` 方法：

```python
# 使用sentence-transformers
from sentence_transformers import SentenceTransformer

class VectorService:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def get_text_embedding(self, text: str) -> List[float]:
        return self.embedding_model.encode(text).tolist()
```

### 2. 使用OpenAI嵌入

```python
import openai

class VectorService:
    def get_text_embedding(self, text: str) -> List[float]:
        response = openai.Embedding.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response['data'][0]['embedding']
```

### 3. 自定义向量维度

修改配置文件中的 `dimension` 参数，确保与嵌入模型的输出维度一致。

## 故障排除

### 1. 连接Milvus失败

- 检查Milvus服务是否正常运行
- 确认配置文件中的host和port设置正确
- 检查网络连接

### 2. 向量存储失败

- 检查Milvus集合是否已创建
- 确认向量维度设置正确
- 查看日志文件获取详细错误信息

### 3. 搜索无结果

- 确认文档已成功向量化
- 检查搜索参数设置
- 验证向量集合中有数据

## 性能优化

### 1. 批量处理

对于大量文档，建议使用批量处理命令，避免一次性处理过多数据。

### 2. 索引优化

根据数据量调整Milvus索引参数：

```python
index_params = {
    "metric_type": "COSINE",
    "index_type": "IVF_FLAT",  # 或使用 "HNSW" 获得更好的搜索性能
    "params": {"nlist": 1024}  # 根据数据量调整
}
```

### 3. 缓存策略

考虑添加Redis缓存来缓存搜索结果，提高响应速度。

## 注意事项

1. 确保Milvus服务稳定运行
2. 定期备份向量数据
3. 监控系统资源使用情况
4. 根据实际需求调整向量维度和索引参数

## 许可证

本功能遵循MrDoc的许可证。 