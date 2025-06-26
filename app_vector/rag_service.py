# coding:utf-8
import json
import logging
from typing import List, Dict, Optional, Tuple
from django.conf import settings
from django.core.cache import cache
from .models import ChatSession, ChatMessage, DocumentVector
from .services import vector_service

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available. Please install openai: pip install openai")


class RAGService:
    """RAG智能问答服务类"""
    
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
    
    def create_chat_session(self, user, title: str = None) -> ChatSession:
        """创建新的聊天会话"""
        if not title:
            title = f"新对话 {ChatSession.objects.filter(user=user).count() + 1}"
        
        session = ChatSession.objects.create(
            user=user,
            title=title
        )
        return session
    
    def get_user_sessions(self, user) -> List[ChatSession]:
        """获取用户的所有会话"""
        return ChatSession.objects.filter(user=user, is_active=True)
    
    def get_session_messages(self, session_id: int) -> List[ChatMessage]:
        """获取会话的所有消息"""
        try:
            session = ChatSession.objects.get(id=session_id)
            return ChatMessage.objects.filter(session=session)
        except ChatSession.DoesNotExist:
            return []
    
    def retrieve_relevant_docs(self, query: str, top_k: int = 5) -> List[Dict]:
        """检索相关文档"""
        try:
            # 使用向量服务搜索相似文档
            similar_docs = vector_service.search_similar_documents(query, top_k)
            
            # 格式化文档信息
            relevant_docs = []
            for doc_info in similar_docs:
                doc = doc_info.get('doc')
                if doc and isinstance(doc, dict):
                    relevant_docs.append({
                        'id': doc.get('id'),
                        'name': doc.get('name', ''),
                        'content': doc.get('content', '') or doc.get('pre_content', ''),
                        'url': f'/doc/{doc.get("id")}/',
                        'score': doc_info.get('score', 0)
                    })
            
            return relevant_docs
        except Exception as e:
            logger.error(f"Error retrieving relevant docs: {e}")
            return []
    
    def build_context_prompt(self, query: str, relevant_docs: List[Dict]) -> str:
        """构建上下文提示"""
        if not relevant_docs:
            return f"用户问题：{query}\n\n请基于您的知识回答这个问题。"
        
        context_parts = [f"用户问题：{query}\n\n"]
        context_parts.append("参考文档：\n")
        
        for i, doc in enumerate(relevant_docs, 1):
            context_parts.append(f"{i}. 文档标题：{doc['name']}")
            context_parts.append(f"   文档内容：{doc['content'][:500]}...")
            context_parts.append(f"   文档链接：{doc['url']}\n")
        
        context_parts.append("请基于以上参考文档回答用户问题。如果参考文档中没有相关信息，请说明无法从文档中找到相关信息。")
        
        return "".join(context_parts)
    
    def generate_response(self, query: str, relevant_docs: List[Dict], conversation_history: List[Dict] = None) -> Tuple[str, int]:
        """生成AI回复"""
        if not self.client:
            return "抱歉，AI服务未配置，无法生成回复。", 0
        
        try:
            # 构建上下文提示
            context_prompt = self.build_context_prompt(query, relevant_docs)
            
            # 构建消息列表
            messages = [
                {
                    "role": "system",
                    "content": "你是一个智能文档助手，基于用户提供的文档内容回答问题。请准确、简洁地回答用户问题，并在回答中引用相关的文档信息。"
                }
            ]
            
            # 添加对话历史（限制长度）
            if conversation_history:
                # 只保留最近的几条消息，避免token超限
                recent_history = conversation_history[-6:]  # 保留最近6条消息
                for msg in recent_history:
                    messages.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })
            
            # 添加当前问题
            messages.append({
                "role": "user",
                "content": context_prompt
            })
            
            # 确保 max_tokens 在有效范围内
            max_tokens = min(max(1, self.max_tokens), 8192)
            
            # 记录调试信息
            logger.info(f"Calling OpenAI API with model={self.model_name}, max_tokens={max_tokens}, temperature={self.temperature}")
            
            # 调用OpenAI API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=self.temperature
            )
            
            assistant_message = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            return assistant_message, tokens_used
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # 如果是 max_tokens 错误，提供更详细的错误信息
            if "max_tokens" in str(e).lower():
                return f"抱歉，生成回复时出现错误：max_tokens 参数无效。当前设置：{self.max_tokens}，有效范围：[1, 8192]。错误详情：{str(e)}", 0
            return f"抱歉，生成回复时出现错误：{str(e)}", 0
    
    def chat(self, user, session_id: int, message: str) -> Dict:
        """处理聊天消息"""
        try:
            # 获取或创建会话
            if session_id:
                try:
                    session = ChatSession.objects.get(id=session_id, user=user)
                except ChatSession.DoesNotExist:
                    session = self.create_chat_session(user)
            else:
                session = self.create_chat_session(user)
            
            # 保存用户消息
            user_message = ChatMessage.objects.create(
                session=session,
                role='user',
                content=message
            )
            
            # 检索相关文档
            relevant_docs = self.retrieve_relevant_docs(message)
            
            # 获取对话历史
            conversation_history = []
            previous_messages = ChatMessage.objects.filter(session=session).exclude(id=user_message.id)
            for msg in previous_messages:
                conversation_history.append({
                    'role': msg.role,
                    'content': msg.content
                })
            
            # 生成AI回复
            ai_response, tokens_used = self.generate_response(message, relevant_docs, conversation_history)
            
            # 保存AI回复
            assistant_message = ChatMessage.objects.create(
                session=session,
                role='assistant',
                content=ai_response,
                reference_docs=relevant_docs,
                tokens_used=tokens_used
            )
            
            # 更新会话标题（如果是第一条消息）
            if ChatMessage.objects.filter(session=session).count() == 2:  # 用户消息 + AI回复
                session.title = message[:50] + "..." if len(message) > 50 else message
                session.save()
            
            return {
                'session_id': session.id,
                'session_title': session.title,
                'user_message': {
                    'id': user_message.id,
                    'content': user_message.content,
                    'create_time': user_message.create_time.isoformat()
                },
                'assistant_message': {
                    'id': assistant_message.id,
                    'content': assistant_message.content,
                    'reference_docs': assistant_message.reference_docs,
                    'tokens_used': assistant_message.tokens_used,
                    'create_time': assistant_message.create_time.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return {
                'error': str(e)
            }
    
    def delete_session(self, user, session_id: int) -> bool:
        """删除会话"""
        try:
            session = ChatSession.objects.get(id=session_id, user=user)
            session.is_active = False
            session.save()
            return True
        except ChatSession.DoesNotExist:
            return False


# 创建全局RAG服务实例
rag_service = RAGService() 