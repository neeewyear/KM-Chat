# coding:utf-8
"""
AI搜索服务 - 参考Lepton AI实现，但使用本地Milvus和文档搜索
"""
import json
import logging
import re
from typing import List, Dict, Optional, Tuple, Any
from django.conf import settings
from django.core.cache import cache
from .models import DocumentVector
from .services import vector_service

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available. Please install openai: pip install openai")


class AISearchService:
    """AI搜索服务类 - 结合向量搜索和LLM对话"""
    
    def __init__(self):
        self.openai_api_key = getattr(settings, 'OPENAI_API_KEY', '')
        self.openai_base_url = getattr(settings, 'OPENAI_BASE_URL', 'https://api.openai.com/v1')
        self.model_name = getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo')
        self.max_tokens = getattr(settings, 'OPENAI_MAX_TOKENS', 2000)
        self.temperature = getattr(settings, 'OPENAI_TEMPERATURE', 0.7)
        
        self.client = None
        if self.openai_api_key and OPENAI_AVAILABLE:
            self.client = OpenAI(
                api_key=self.openai_api_key,
                base_url=self.openai_base_url
            )
    
    def search_documents(self, query: str, top_k: int = 10) -> List[Dict]:
        """搜索相关文档"""
        try:
            # 使用向量服务搜索相似文档
            similar_docs = vector_service.search_similar_documents(query, top_k)
            
            # 格式化文档信息
            search_results = []
            for doc_info in similar_docs:
                doc = doc_info.get('doc')
                if doc and isinstance(doc, dict):
                    search_results.append({
                        'id': doc.get('id'),
                        'name': doc.get('name', ''),
                        'content': doc.get('content', '') or doc.get('pre_content', ''),
                        'url': f'/doc/{doc.get("id")}/',
                        'score': doc_info.get('score', 0),
                        'project_name': doc.get('project_name', ''),
                        'create_time': doc.get('create_time', ''),
                        'modify_time': doc.get('modify_time', '')
                    })
            
            return search_results
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def extract_search_intent(self, query: str) -> Dict[str, Any]:
        """提取搜索意图"""
        if not self.client:
            return {
                'intent': 'search',
                'keywords': query,
                'filters': {}
            }
        
        try:
            system_prompt = """
            你是一个搜索意图分析器。分析用户的搜索查询，提取以下信息：
            1. 搜索意图（search, question, command等）
            2. 关键词
            3. 可能的过滤条件
            
            返回JSON格式：
            {
                "intent": "search|question|command",
                "keywords": "提取的关键词",
                "filters": {
                    "project": "项目名称",
                    "date_range": "时间范围",
                    "content_type": "内容类型"
                }
            }
            """
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"分析这个搜索查询：{query}"}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                # 如果JSON解析失败，返回默认结果
                return {
                    'intent': 'search',
                    'keywords': query,
                    'filters': {}
                }
                
        except Exception as e:
            logger.error(f"Error extracting search intent: {e}")
            return {
                'intent': 'search',
                'keywords': query,
                'filters': {}
            }
    
    def generate_search_summary(self, query: str, search_results: List[Dict]) -> str:
        """生成搜索摘要"""
        if not self.client:
            return f"找到 {len(search_results)} 个相关文档。"
        
        try:
            # 准备文档摘要
            docs_summary = []
            for i, doc in enumerate(search_results[:5], 1):  # 只取前5个文档
                docs_summary.append(f"{i}. {doc['name']} (相关度: {doc['score']:.2f})")
            
            system_prompt = """
            你是一个搜索助手。基于用户的搜索查询和找到的文档，生成一个简洁的搜索摘要。
            摘要应该包括：
            1. 找到的文档数量
            2. 最相关的几个文档
            3. 简要说明搜索结果的相关性
            
            用中文回答，简洁明了。
            """
            
            user_prompt = f"""
            用户搜索：{query}
            
            找到的文档：
            {chr(10).join(docs_summary)}
            
            请生成搜索摘要。
            """
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating search summary: {e}")
            return f"找到 {len(search_results)} 个相关文档。"
    
    def answer_question(self, question: str, search_results: List[Dict]) -> Tuple[str, List[Dict]]:
        """基于搜索结果回答问题"""
        if not self.client:
            return "抱歉，AI服务未配置，无法回答问题。", []
        
        try:
            # 构建上下文
            context_parts = []
            for i, doc in enumerate(search_results[:3], 1):  # 只使用前3个最相关的文档
                context_parts.append(f"文档{i}：{doc['name']}")
                context_parts.append(f"内容：{doc['content'][:800]}...")
                context_parts.append(f"链接：{doc['url']}\n")
            
            context = "\n".join(context_parts)
            
            # 判断是否为问题形式
            question_indicators = ['什么', '如何', '怎么', '为什么', '哪里', '哪个', '?', '？', '吗', '呢']
            is_question = any(indicator in question for indicator in question_indicators)
            
            if is_question:
                system_prompt = """
                你是一个智能文档助手。基于提供的文档内容回答用户问题。
                
                回答要求：
                1. 准确、简洁地回答用户问题
                2. 如果文档中有相关信息，请引用具体文档
                3. 如果文档中没有相关信息，请明确说明
                4. 提供文档链接供用户进一步查看
                5. 用中文回答
                """
            else:
                system_prompt = """
                你是一个智能文档助手。基于提供的文档内容，为用户提供关于搜索关键词的详细解释和总结。
                
                回答要求：
                1. 总结搜索关键词相关的核心信息
                2. 介绍相关文档的主要内容
                3. 提供实用的建议和指导
                4. 如果文档中有相关信息，请引用具体文档
                5. 用中文回答，语言友好易懂
                """
            
            user_prompt = f"""
            参考文档：
            {context}
            
            用户查询：{question}
            
            请基于以上文档内容{'回答问题' if is_question else '提供详细解释和总结'}。
            """
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            answer = response.choices[0].message.content
            
            # 提取引用的文档
            referenced_docs = []
            for doc in search_results[:3]:
                if doc['name'] in answer or str(doc['id']) in answer:
                    referenced_docs.append(doc)
            
            return answer, referenced_docs
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return f"抱歉，回答问题时出现错误：{str(e)}", []
    
    def smart_search(self, query: str, top_k: int = 10) -> Dict[str, Any]:
        """智能搜索 - 结合搜索意图分析和结果处理"""
        try:
            # 1. 提取搜索意图
            intent_info = self.extract_search_intent(query)
            
            # 2. 搜索文档
            search_results = self.search_documents(query, top_k)
            
            # 3. 生成搜索摘要
            summary = self.generate_search_summary(query, search_results)
            
            # 4. 根据意图处理结果
            if intent_info['intent'] == 'question':
                # 如果是问题，生成详细答案
                answer, referenced_docs = self.answer_question(query, search_results)
                
                return {
                    'type': 'question',
                    'query': query,
                    'intent': intent_info,
                    'answer': answer,
                    'summary': summary,
                    'search_results': search_results,
                    'referenced_docs': referenced_docs,
                    'total_results': len(search_results)
                }
            else:
                # 如果是普通搜索，也生成AI回答
                answer, referenced_docs = self.answer_question(query, search_results)
                
                return {
                    'type': 'search',
                    'query': query,
                    'intent': intent_info,
                    'answer': answer,
                    'summary': summary,
                    'search_results': search_results,
                    'referenced_docs': referenced_docs,
                    'total_results': len(search_results)
                }
                
        except Exception as e:
            logger.error(f"Error in smart search: {e}")
            return {
                'type': 'error',
                'query': query,
                'error': str(e),
                'search_results': [],
                'total_results': 0
            }
    
    def get_search_suggestions(self, query: str) -> List[str]:
        """获取搜索建议"""
        try:
            # 从缓存中获取历史搜索记录
            cache_key = f"search_history_{hash(query) % 1000}"
            search_history = cache.get(cache_key, [])
            
            # 基于当前查询生成建议
            suggestions = []
            
            # 1. 添加历史搜索建议
            for hist_query in search_history:
                if query.lower() in hist_query.lower() and hist_query != query:
                    suggestions.append(hist_query)
            
            # 2. 添加常见搜索模式
            common_patterns = [
                f"{query} 教程",
                f"{query} 文档",
                f"{query} 示例",
                f"{query} 配置",
                f"{query} 问题"
            ]
            
            for pattern in common_patterns:
                if pattern not in suggestions:
                    suggestions.append(pattern)
            
            # 限制建议数量
            return suggestions[:5]
            
        except Exception as e:
            logger.error(f"Error getting search suggestions: {e}")
            return []
    
    def save_search_history(self, query: str, results_count: int):
        """保存搜索历史"""
        try:
            cache_key = f"search_history_{hash(query) % 1000}"
            search_history = cache.get(cache_key, [])
            
            # 添加新查询到历史记录
            if query not in search_history:
                search_history.insert(0, query)
                # 只保留最近10条记录
                search_history = search_history[:10]
                cache.set(cache_key, search_history, 60 * 60 * 24 * 7)  # 保存7天
                
        except Exception as e:
            logger.error(f"Error saving search history: {e}")


# 创建全局实例
ai_search_service = AISearchService() 