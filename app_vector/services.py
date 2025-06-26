# coding:utf-8
import hashlib
import logging
from typing import List, Dict, Optional, Tuple
from django.conf import settings
from django.core.cache import cache
from .models import DocumentVector, VectorCollection

logger = logging.getLogger(__name__)

try:
    from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False
    logger.warning("Milvus not available. Please install pymilvus: pip install pymilvus")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available. Please install openai: pip install openai")


class MilvusService:
    """Milvus向量数据库服务类"""
    
    def __init__(self):
        self.collection_name = getattr(settings, 'MILVUS_COLLECTION_NAME', 'mrdoc_documents')
        self.dimension = getattr(settings, 'MILVUS_DIMENSION', 1536)
        self.host = getattr(settings, 'MILVUS_HOST', 'localhost')
        self.port = getattr(settings, 'MILVUS_PORT', '19530')
        self.connected = False
        
    def connect(self) -> bool:
        """连接到Milvus服务器"""
        if not MILVUS_AVAILABLE:
            logger.error("Milvus not available")
            return False
            
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port
            )
            self.connected = True
            logger.info(f"Connected to Milvus at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            return False
    
    def disconnect(self):
        """断开Milvus连接"""
        if self.connected and MILVUS_AVAILABLE:
            try:
                connections.disconnect("default")
                self.connected = False
                logger.info("Disconnected from Milvus")
            except Exception as e:
                logger.error(f"Failed to disconnect from Milvus: {e}")
    
    def create_collection(self) -> bool:
        """创建向量集合"""
        if not self.connected:
            if not self.connect():
                return False
        
        try:
            # 检查集合是否已存在
            if utility.has_collection(self.collection_name):
                logger.info(f"Collection {self.collection_name} already exists")
                return True
            
            # 定义字段
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="doc_id", dtype=DataType.INT64, description="文档ID"),
                FieldSchema(name="content_hash", dtype=DataType.VARCHAR, max_length=64, description="内容哈希"),
                FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.dimension, description="文档向量"),
            ]
            
            # 创建集合模式
            schema = CollectionSchema(fields=fields, description="MrDoc文档向量集合")
            
            # 创建集合
            collection = Collection(name=self.collection_name, schema=schema)
            
            # 创建索引
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            collection.create_index(field_name="vector", index_params=index_params)
            
            logger.info(f"Created collection {self.collection_name} with dimension {self.dimension}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            return False
    
    def insert_vectors(self, vectors_data: List[Dict]) -> List[str]:
        """插入向量数据"""
        if not self.connected:
            if not self.connect():
                return []
        
        try:
            collection = Collection(self.collection_name)
            collection.load()
            
            # 准备数据
            doc_ids = [item['doc_id'] for item in vectors_data]
            content_hashes = [item['content_hash'] for item in vectors_data]
            vectors = [item['vector'] for item in vectors_data]
            
            # 插入数据
            insert_result = collection.insert([
                doc_ids,
                content_hashes,
                vectors
            ])
            
            collection.flush()
            logger.info(f"Inserted {len(vectors_data)} vectors")
            return insert_result.primary_keys
            
        except Exception as e:
            logger.error(f"Failed to insert vectors: {e}")
            return []
    
    def search_vectors(self, query_vector: List[float], top_k: int = 10) -> List[Dict]:
        """搜索相似向量"""
        if not self.connected:
            if not self.connect():
                return []
        
        try:
            collection = Collection(self.collection_name)
            collection.load()
            
            # 搜索参数
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            # 执行搜索
            results = collection.search(
                data=[query_vector],
                anns_field="vector",
                param=search_params,
                limit=top_k,
                output_fields=["doc_id", "content_hash"]
            )
            
            # 格式化结果
            search_results = []
            for hits in results:
                for hit in hits:
                    search_results.append({
                        'doc_id': hit.entity.get('doc_id'),
                        'content_hash': hit.entity.get('content_hash'),
                        'score': hit.score,
                        'id': hit.id
                    })
            
            return search_results
            
        except Exception as e:
            logger.error(f"Failed to search vectors: {e}")
            return []
    
    def delete_vectors(self, doc_ids: List[int]) -> bool:
        """删除向量数据"""
        if not self.connected:
            if not self.connect():
                return False
        
        try:
            collection = Collection(self.collection_name)
            collection.load()
            
            # 删除数据
            collection.delete(f"doc_id in {doc_ids}")
            collection.flush()
            
            logger.info(f"Deleted vectors for doc_ids: {doc_ids}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")
            return False


class VectorService:
    """向量服务类，处理文档向量化"""
    
    def __init__(self):
        self.milvus_service = MilvusService()
        self.embedding_client = None
        self._init_embedding_model()
    
    def _init_embedding_model(self):
        """初始化嵌入模型"""
        try:
            # 获取配置
            api_key = getattr(settings, 'OPENAI_API_KEY', '')
            base_url = getattr(settings, 'OPENAI_BASE_URL', 'https://api.openai.com/v1')
            
            if api_key and OPENAI_AVAILABLE:
                self.embedding_client = OpenAI(
                    api_key=api_key,
                    base_url=base_url
                )
                logger.info("Initialized embedding model with OpenAI/DeepSeek API")
            else:
                logger.warning("No API key configured or OpenAI not available, using fallback embedding")
                
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
    
    def get_text_embedding(self, text: str) -> List[float]:
        """获取文本的向量表示"""
        if self.embedding_client:
            try:
                # 尝试使用不同的嵌入模型
                embedding_models = [
                    "text-embedding-ada-002",  # OpenAI 标准模型
                    "text-embedding-3-small",  # OpenAI 新模型
                    "embedding-2",  # DeepSeek 可能的模型名
                    "text-embedding-v1"  # 通用模型名
                ]
                
                for model in embedding_models:
                    try:
                        response = self.embedding_client.embeddings.create(
                            model=model,
                            input=text
                        )
                        logger.info(f"Successfully used embedding model: {model}")
                        return response.data[0].embedding
                    except Exception as e:
                        logger.debug(f"Failed to use embedding model {model}: {e}")
                        continue
                
                # 如果所有模型都失败，使用回退方法
                logger.warning("All embedding models failed, using fallback method")
                return self._get_fallback_embedding(text)
                
            except Exception as e:
                logger.error(f"Error getting embedding from API: {e}")
                # 如果API调用失败，回退到哈希方法
                return self._get_fallback_embedding(text)
        else:
            # 使用回退方法
            return self._get_fallback_embedding(text)
    
    def _get_fallback_embedding(self, text: str) -> List[float]:
        """回退的嵌入方法，使用改进的哈希算法"""
        import hashlib
        import numpy as np
        
        # 生成文本哈希
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        
        # 使用更复杂的哈希算法生成向量
        vector = []
        
        # 方法1：使用字符频率
        char_freq = {}
        for char in text:
            char_freq[char] = char_freq.get(char, 0) + 1
        
        # 将字符频率转换为数值
        freq_values = list(char_freq.values())
        if freq_values:
            # 归一化频率值
            max_freq = max(freq_values)
            normalized_freq = [f / max_freq for f in freq_values]
            vector.extend(normalized_freq)
        
        # 方法2：使用文本长度和哈希值
        text_length = len(text)
        vector.append(text_length / 1000.0)  # 归一化长度
        
        # 方法3：使用哈希值生成向量
        for i in range(0, min(len(text_hash), self.milvus_service.dimension * 2), 2):
            if len(vector) >= self.milvus_service.dimension:
                break
            hex_pair = text_hash[i:i+2]
            vector.append(float(int(hex_pair, 16)) / 255.0)
        
        # 如果向量长度不足，用0填充
        while len(vector) < self.milvus_service.dimension:
            vector.append(0.0)
        
        # 归一化向量
        vector = np.array(vector[:self.milvus_service.dimension])
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector.tolist()
    
    def get_content_hash(self, content: str) -> str:
        """获取内容的哈希值"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def store_document_vector(self, doc_id: int, content: str) -> bool:
        """存储文档向量"""
        try:
            # 获取内容哈希
            content_hash = self.get_content_hash(content)
            
            # 检查是否已存在相同的向量
            existing_vector = DocumentVector.objects.filter(
                doc_id=doc_id,
                content_hash=content_hash
            ).first()
            
            if existing_vector:
                logger.info(f"Vector already exists for doc {doc_id}")
                return True
            
            # 生成向量
            vector = self.get_text_embedding(content)
            
            # 存储到Milvus
            vector_data = [{
                'doc_id': doc_id,
                'content_hash': content_hash,
                'vector': vector
            }]
            
            vector_ids = self.milvus_service.insert_vectors(vector_data)
            
            if vector_ids:
                # 保存到数据库
                DocumentVector.objects.create(
                    doc_id=doc_id,
                    vector_id=str(vector_ids[0]),
                    content_hash=content_hash
                )
                logger.info(f"Stored vector for doc {doc_id}")
                return True
            else:
                logger.error(f"Failed to store vector for doc {doc_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing document vector: {e}")
            return False
    
    def search_similar_documents(self, query_text: str, top_k: int = 10) -> List[Dict]:
        """搜索相似文档"""
        try:
            # 生成查询向量
            query_vector = self.get_text_embedding(query_text)
            
            # 在Milvus中搜索
            search_results = self.milvus_service.search_vectors(query_vector, top_k)
            
            # 获取文档信息
            doc_ids = [result['doc_id'] for result in search_results]
            documents = {}
            
            from app_doc.models import Doc
            for doc in Doc.objects.filter(id__in=doc_ids):
                documents[doc.id] = {
                    'id': doc.id,
                    'name': doc.name,
                    'content': doc.content,
                    'pre_content': doc.pre_content,
                    'create_time': doc.create_time,
                    'create_user': doc.create_user.username
                }
            
            # 格式化结果
            results = []
            for result in search_results:
                doc_id = result['doc_id']
                if doc_id in documents:
                    doc_info = documents[doc_id]
                    results.append({
                        'doc': doc_info,
                        'score': result['score'],
                        'vector_id': result['id']
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar documents: {e}")
            return []
    
    def delete_document_vector(self, doc_id: int) -> bool:
        """删除文档向量"""
        try:
            # 从数据库删除记录
            DocumentVector.objects.filter(doc_id=doc_id).delete()
            
            # 从Milvus删除向量
            self.milvus_service.delete_vectors([doc_id])
            
            logger.info(f"Deleted vector for doc {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document vector: {e}")
            return False


# 全局向量服务实例
vector_service = VectorService() 