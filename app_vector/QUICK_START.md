# AI智能搜索 - 快速启动指南

## 🚀 5分钟快速启动

### 1. 安装依赖
```bash
pip install openai pymilvus
```

### 2. 配置OpenAI API
在 `config/config.ini` 中添加：
```ini
[openai]
api_key = your-openai-api-key-here
model = gpt-3.5-turbo
max_tokens = 2000
temperature = 0.7
```

### 3. 启动Milvus服务
```bash
# 使用Docker启动Milvus
docker run -d --name milvus-standalone \
  -p 19530:19530 \
  -p 9091:9091 \
  milvusdb/milvus:latest standalone
```

### 4. 初始化向量数据库
```bash
python manage.py shell
```
```python
from app_vector.management.commands.init_milvus import Command
cmd = Command()
cmd.handle()
```

### 5. 向量化现有文档
```bash
python manage.py batch_vectorize
```

### 6. 访问AI搜索页面
- 启动Django服务：`python manage.py runserver`
- 访问：`http://localhost:8000/vector/ai-search/`

## 🎯 功能演示

### 基本搜索
1. 输入关键词：`Python教程`
2. 系统返回相关文档列表

### 智能问答
1. 输入问题：`如何配置数据库？`
2. 系统生成答案并提供参考文档

### 高级功能
- 实时搜索建议
- 文档相关度评分
- 服务状态监控

## 🔧 故障排除

### 常见问题

**Q: 页面显示"OpenAI服务未配置"**
```
A: 检查config.ini中的api_key配置
```

**Q: 搜索无结果**
```
A: 运行 python manage.py batch_vectorize 向量化文档
```

**Q: Milvus连接失败**
```
A: 检查Milvus服务是否启动：docker ps | grep milvus
```

## 📚 更多信息

- 详细文档：`AI_SEARCH_README.md`
- 测试脚本：`python app_vector/test_ai_search.py`
- 配置文件：`config/ai_search_config.ini.example`

## 🎉 开始使用

现在您可以享受智能搜索功能了！

- 🔍 **智能搜索**：自动识别搜索意图
- 🤖 **AI问答**：基于文档内容生成答案  
- 💡 **搜索建议**：实时提供相关建议
- 📊 **状态监控**：实时查看服务状态 