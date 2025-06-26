# MrDoc RAG 智能问答功能

## 功能概述

MrDoc RAG 智能问答功能是基于检索增强生成（Retrieval-Augmented Generation）技术的智能文档助手。它能够：

1. **智能检索**：基于用户问题，从文档库中检索最相关的内容
2. **智能回答**：结合检索到的文档内容，生成准确、有用的回答
3. **对话管理**：支持多轮对话，保存对话历史
4. **参考文档**：显示回答所参考的文档来源

## 技术架构

### 核心组件

1. **向量数据库**：使用 Milvus 存储文档向量
2. **嵌入模型**：使用 OpenAI 的 text-embedding-ada-002 模型
3. **大语言模型**：使用 OpenAI GPT 系列模型生成回答
4. **RAG 服务**：协调检索和生成过程

### 工作流程

1. 用户输入问题
2. 将问题转换为向量
3. 在向量数据库中检索相似文档
4. 将检索到的文档作为上下文
5. 使用 LLM 生成回答
6. 返回回答和参考文档

## 安装配置

### 1. 安装依赖

```bash
pip install openai pymilvus
```

### 2. 配置环境变量

在 `MrDoc/settings.py` 中添加以下配置：

```python
# OpenAI 配置
OPENAI_API_KEY = 'your-openai-api-key'
OPENAI_BASE_URL = 'https://api.openai.com/v1'  # 可选，默认值
OPENAI_MODEL = 'gpt-3.5-turbo'  # 可选，默认值
OPENAI_MAX_TOKENS = 2000  # 可选，默认值
OPENAI_TEMPERATURE = 0.7  # 可选，默认值

# Milvus 配置
MILVUS_HOST = 'localhost'  # Milvus 服务器地址
MILVUS_PORT = '19530'  # Milvus 端口
MILVUS_COLLECTION_NAME = 'mrdoc_documents'  # 集合名称
MILVUS_DIMENSION = 1536  # 向量维度
```

### 3. 初始化数据库

```bash
python manage.py makemigrations app_vector
python manage.py migrate
```

### 4. 启动 Milvus 服务

使用 Docker 启动 Milvus：

```bash
docker run -d --name milvus_standalone -p 19530:19530 -p 9091:9091 milvusdb/milvus:latest standalone
```

## 使用方法

### 1. 访问智能问答页面

登录后访问：`http://your-domain/vector/chat/`

### 2. 开始对话

- 点击"新对话"开始新的会话
- 在输入框中输入您的问题
- 系统会自动检索相关文档并生成回答

### 3. 管理对话

- 左侧边栏显示所有对话历史
- 点击对话标题可以切换对话
- 点击删除按钮可以删除对话

### 4. 查看参考文档

AI 回答下方会显示参考的文档列表，包括：
- 文档标题
- 相似度分数
- 文档链接

## API 接口

### 获取会话列表

```
GET /vector/api/chat/sessions/
```

### 获取会话消息

```
GET /vector/api/chat/sessions/{session_id}/messages/
```

### 发送消息

```
POST /vector/api/chat/
Content-Type: application/json

{
    "session_id": null,  // 可选，null 表示新会话
    "message": "您的问题"
}
```

### 删除会话

```
DELETE /vector/api/chat/sessions/{session_id}/
```

## 功能特性

### 1. 智能检索

- 基于语义相似度检索相关文档
- 支持中文和英文混合查询
- 可配置检索文档数量

### 2. 上下文管理

- 自动维护对话上下文
- 智能截断长对话历史
- 避免 token 超限

### 3. 参考文档

- 显示检索到的相关文档
- 显示相似度分数
- 提供文档链接

### 4. 用户界面

- 现代化的聊天界面
- 响应式设计，支持移动端
- 实时消息更新
- 加载状态提示

## 配置选项

### OpenAI 配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| OPENAI_API_KEY | OpenAI API 密钥 | 必填 |
| OPENAI_BASE_URL | API 基础 URL | https://api.openai.com/v1 |
| OPENAI_MODEL | 使用的模型 | gpt-3.5-turbo |
| OPENAI_MAX_TOKENS | 最大 token 数 | 2000 |
| OPENAI_TEMPERATURE | 生成温度 | 0.7 |

### Milvus 配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| MILVUS_HOST | Milvus 服务器地址 | localhost |
| MILVUS_PORT | Milvus 端口 | 19530 |
| MILVUS_COLLECTION_NAME | 集合名称 | mrdoc_documents |
| MILVUS_DIMENSION | 向量维度 | 1536 |

## 故障排除

### 1. 向量服务不可用

检查 Milvus 服务是否正常运行：

```bash
docker ps | grep milvus
```

### 2. OpenAI API 错误

检查 API 密钥是否正确配置，网络连接是否正常。

### 3. 数据库迁移错误

确保已正确执行数据库迁移：

```bash
python manage.py migrate app_vector
```

### 4. 文档向量化失败

检查文档内容是否为空，向量服务是否正常。

## 开发说明

### 添加新的嵌入模型

在 `services.py` 中的 `VectorService` 类中添加新的嵌入模型支持。

### 自定义 RAG 流程

在 `rag_service.py` 中修改 `RAGService` 类来自定义检索和生成流程。

### 扩展用户界面

修改 `chat.html` 模板来自定义用户界面。

## 许可证

本功能遵循 MrDoc 项目的许可证。 