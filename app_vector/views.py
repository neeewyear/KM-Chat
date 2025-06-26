from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json
import logging

logger = logging.getLogger(__name__)


@login_required
def rag_chat_page(request):
    """RAG智能问答页面"""
    try:
        return render(request, 'app_vector/chat.html')
    except Exception as e:
        logger.error(f"Error rendering RAG chat page: {e}")
        return render(request, '404.html', status=404)


@login_required
def vector_search_page(request):
    """向量搜索页面"""
    try:
        return render(request, 'app_vector/search.html')
    except Exception as e:
        logger.error(f"Error rendering vector search page: {e}")
        return render(request, '404.html', status=404)


@login_required
def vector_test_page(request):
    """向量搜索测试页面（不依赖向量服务）"""
    try:
        return render(request, 'app_vector/test.html')
    except Exception as e:
        logger.error(f"Error rendering vector test page: {e}")
        return render(request, '404.html', status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_get_chat_sessions(request):
    """获取用户的聊天会话列表"""
    try:
        from .rag_service import rag_service
        sessions = rag_service.get_user_sessions(request.user)
        
        session_list = []
        for session in sessions:
            session_list.append({
                'id': session.id,
                'title': session.title,
                'create_time': session.create_time.isoformat(),
                'update_time': session.update_time.isoformat()
            })
        
        return Response({
            'code': 0,
            'data': session_list
        })
        
    except Exception as e:
        logger.error(f"Error getting chat sessions: {e}")
        return Response({
            'code': 1,
            'message': '获取会话列表失败'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_get_session_messages(request, session_id):
    """获取会话的消息历史"""
    try:
        from .rag_service import rag_service
        messages = rag_service.get_session_messages(session_id)
        
        message_list = []
        for message in messages:
            message_list.append({
                'id': message.id,
                'role': message.role,
                'content': message.content,
                'reference_docs': message.reference_docs,
                'tokens_used': message.tokens_used,
                'create_time': message.create_time.isoformat()
            })
        
        return Response({
            'code': 0,
            'data': message_list
        })
        
    except Exception as e:
        logger.error(f"Error getting session messages: {e}")
        return Response({
            'code': 1,
            'message': '获取消息历史失败'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_chat(request):
    """处理聊天消息"""
    try:
        from .rag_service import rag_service
        
        session_id = request.data.get('session_id')
        message = request.data.get('message', '').strip()
        
        if not message:
            return Response({
                'code': 1,
                'message': '消息内容不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 处理聊天
        result = rag_service.chat(request.user, session_id, message)
        
        if 'error' in result:
            return Response({
                'code': 1,
                'message': result['error']
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'code': 0,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return Response({
            'code': 1,
            'message': '聊天处理失败'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def api_delete_session(request, session_id):
    """删除聊天会话"""
    try:
        from .rag_service import rag_service
        
        success = rag_service.delete_session(request.user, session_id)
        
        if success:
            return Response({
                'code': 0,
                'message': '会话删除成功'
            })
        else:
            return Response({
                'code': 1,
                'message': '会话不存在或删除失败'
            }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        return Response({
            'code': 1,
            'message': '删除会话失败'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_vector_status(request):
    """检查向量服务状态"""
    try:
        # 检查pymilvus是否可用
        try:
            import pymilvus
            pymilvus_available = True
        except ImportError:
            pymilvus_available = False
        
        # 检查向量服务是否可用
        try:
            from .services import vector_service
            vector_service_available = True
            
            # 尝试连接Milvus
            milvus_connected = vector_service.milvus_service.connect()
            if milvus_connected:
                vector_service.milvus_service.disconnect()
        except Exception as e:
            vector_service_available = False
            milvus_connected = False
            logger.error(f"Vector service error: {e}")
        
        status_info = {
            'pymilvus_available': pymilvus_available,
            'vector_service_available': vector_service_available,
            'milvus_connected': milvus_connected,
            'status': 'ok' if (pymilvus_available and vector_service_available and milvus_connected) else 'error'
        }
        
        return Response(status_info)
        
    except Exception as e:
        logger.error(f"Error checking vector status: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@require_http_methods(['POST'])
@login_required
def search_similar_documents(request):
    """搜索相似文档"""
    try:
        # 延迟导入向量服务，避免启动时出错
        from .services import vector_service
        
        data = json.loads(request.body)
        query_text = data.get('query', '').strip()
        top_k = data.get('top_k', 10)
        
        if not query_text:
            return JsonResponse({
                'status': False,
                'message': '查询文本不能为空'
            })
        
        # 搜索相似文档
        results = vector_service.search_similar_documents(query_text, top_k)
        
        return JsonResponse({
            'status': True,
            'data': results,
            'count': len(results)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': False,
            'message': '无效的JSON格式'
        })
    except ImportError as e:
        logger.error(f"Vector service not available: {e}")
        return JsonResponse({
            'status': False,
            'message': '向量服务不可用，请检查Milvus配置'
        })
    except Exception as e:
        logger.error(f"Error in search_similar_documents: {e}")
        return JsonResponse({
            'status': False,
            'message': '搜索失败'
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_search_similar_documents(request):
    """API搜索相似文档"""
    try:
        # 延迟导入向量服务
        from .services import vector_service
        
        query_text = request.data.get('query', '').strip()
        top_k = request.data.get('top_k', 10)
        
        if not query_text:
            return Response({
                'code': 1,
                'message': '查询文本不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 搜索相似文档
        results = vector_service.search_similar_documents(query_text, top_k)
        
        return Response({
            'code': 0,
            'data': results,
            'count': len(results)
        })
        
    except ImportError as e:
        logger.error(f"Vector service not available: {e}")
        return Response({
            'code': 1,
            'message': '向量服务不可用，请检查Milvus配置'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.error(f"Error in api_search_similar_documents: {e}")
        return Response({
            'code': 1,
            'message': '搜索失败'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_store_document_vector(request):
    """API手动存储文档向量"""
    try:
        # 延迟导入向量服务
        from .services import vector_service
        
        doc_id = request.data.get('doc_id')
        content = request.data.get('content', '').strip()
        
        if not doc_id or not content:
            return Response({
                'code': 1,
                'message': '文档ID和内容不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 存储文档向量
        success = vector_service.store_document_vector(doc_id, content)
        
        if success:
            return Response({
                'code': 0,
                'message': '向量存储成功'
            })
        else:
            return Response({
                'code': 1,
                'message': '向量存储失败'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except ImportError as e:
        logger.error(f"Vector service not available: {e}")
        return Response({
            'code': 1,
            'message': '向量服务不可用，请检查Milvus配置'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.error(f"Error in api_store_document_vector: {e}")
        return Response({
            'code': 1,
            'message': '向量存储失败'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def api_delete_document_vector(request, doc_id):
    """API删除文档向量"""
    try:
        # 延迟导入向量服务
        from .services import vector_service
        
        success = vector_service.delete_document_vector(doc_id)
        
        if success:
            return Response({
                'code': 0,
                'message': '向量删除成功'
            })
        else:
            return Response({
                'code': 1,
                'message': '向量删除失败'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except ImportError as e:
        logger.error(f"Vector service not available: {e}")
        return Response({
            'code': 1,
            'message': '向量服务不可用，请检查Milvus配置'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.error(f"Error in api_delete_document_vector: {e}")
        return Response({
            'code': 1,
            'message': '向量删除失败'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def api_vector_status_public(request):
    """公开的向量服务状态检查"""
    try:
        # 检查pymilvus是否可用
        try:
            import pymilvus
            pymilvus_available = True
        except ImportError:
            pymilvus_available = False
        
        # 检查向量服务是否可用
        try:
            from .services import vector_service
            vector_service_available = True
            
            # 尝试连接Milvus
            milvus_connected = vector_service.milvus_service.connect()
            if milvus_connected:
                vector_service.milvus_service.disconnect()
        except Exception as e:
            vector_service_available = False
            milvus_connected = False
            logger.error(f"Vector service error: {e}")
        
        status_info = {
            'pymilvus_available': pymilvus_available,
            'vector_service_available': vector_service_available,
            'milvus_connected': milvus_connected,
            'status': 'ok' if (pymilvus_available and vector_service_available and milvus_connected) else 'error'
        }
        
        return Response(status_info)
        
    except Exception as e:
        logger.error(f"Error checking vector status: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def vector_status_page(request):
    """向量服务状态页面"""
    try:
        return render(request, 'app_vector/status.html')
    except Exception as e:
        logger.error(f"Error rendering vector status page: {e}")
        return render(request, '404.html', status=404)


def vector_search_page_public(request):
    """公开的向量搜索页面"""
    try:
        return render(request, 'app_vector/search.html')
    except Exception as e:
        logger.error(f"Error rendering public vector search page: {e}")
        return render(request, '404.html', status=404)


@csrf_exempt
@require_http_methods(['POST'])
def search_similar_documents_public(request):
    """公开的相似文档搜索"""
    try:
        # 延迟导入向量服务，避免启动时出错
        from .services import vector_service
        
        data = json.loads(request.body)
        query_text = data.get('query', '').strip()
        top_k = data.get('top_k', 10)
        
        if not query_text:
            return JsonResponse({
                'status': False,
                'message': '查询文本不能为空'
            })
        
        # 搜索相似文档
        results = vector_service.search_similar_documents(query_text, top_k)
        
        return JsonResponse({
            'status': True,
            'data': results,
            'count': len(results)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': False,
            'message': '无效的JSON格式'
        })
    except ImportError as e:
        logger.error(f"Vector service not available: {e}")
        return JsonResponse({
            'status': False,
            'message': '向量服务不可用，请检查Milvus配置'
        })
    except Exception as e:
        logger.error(f"Error in search_similar_documents_public: {e}")
        return JsonResponse({
            'status': False,
            'message': '搜索失败'
        })


# AI搜索相关视图
@login_required
def ai_search_page(request):
    """AI智能搜索页面"""
    try:
        return render(request, 'app_vector/ai_search.html')
    except Exception as e:
        logger.error(f"Error rendering AI search page: {e}")
        return render(request, '404.html', status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_ai_search(request):
    """AI智能搜索API"""
    try:
        from .ai_search_service import ai_search_service
        
        query = request.data.get('query', '').strip()
        top_k = request.data.get('top_k', 10)
        
        if not query:
            return Response({
                'code': 1,
                'message': '搜索查询不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 执行智能搜索
        result = ai_search_service.smart_search(query, top_k)
        
        # 保存搜索历史
        ai_search_service.save_search_history(query, result.get('total_results', 0))
        
        return Response({
            'code': 0,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Error in AI search: {e}")
        return Response({
            'code': 1,
            'message': 'AI搜索失败'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_search_suggestions(request):
    """获取搜索建议API"""
    try:
        from .ai_search_service import ai_search_service
        
        query = request.GET.get('query', '').strip()
        
        if not query:
            return Response({
                'code': 0,
                'data': []
            })
        
        suggestions = ai_search_service.get_search_suggestions(query)
        
        return Response({
            'code': 0,
            'data': suggestions
        })
        
    except Exception as e:
        logger.error(f"Error getting search suggestions: {e}")
        return Response({
            'code': 1,
            'message': '获取搜索建议失败'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_ask_question(request):
    """直接提问API"""
    try:
        from .ai_search_service import ai_search_service
        
        question = request.data.get('question', '').strip()
        top_k = request.data.get('top_k', 5)
        
        if not question:
            return Response({
                'code': 1,
                'message': '问题不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 搜索相关文档
        search_results = ai_search_service.search_documents(question, top_k)
        
        # 生成答案
        answer, referenced_docs = ai_search_service.answer_question(question, search_results)
        
        result = {
            'question': question,
            'answer': answer,
            'search_results': search_results,
            'referenced_docs': referenced_docs,
            'total_results': len(search_results)
        }
        
        return Response({
            'code': 0,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Error asking question: {e}")
        return Response({
            'code': 1,
            'message': '提问失败'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def api_ai_search_status(request):
    """AI搜索服务状态检查"""
    try:
        from .ai_search_service import ai_search_service
        
        # 检查OpenAI服务
        openai_available = ai_search_service.client is not None
        
        # 检查向量服务
        try:
            from .services import vector_service
            vector_available = True
            milvus_connected = vector_service.milvus_service.connect()
            if milvus_connected:
                vector_service.milvus_service.disconnect()
        except Exception as e:
            vector_available = False
            milvus_connected = False
            logger.error(f"Vector service error: {e}")
        
        status_info = {
            'openai_available': openai_available,
            'vector_available': vector_available,
            'milvus_connected': milvus_connected,
            'model_name': ai_search_service.model_name,
            'service_ready': openai_available and vector_available
        }
        
        return Response({
            'code': 0,
            'data': status_info
        })
        
    except Exception as e:
        logger.error(f"Error checking AI search status: {e}")
        return Response({
            'code': 1,
            'message': '状态检查失败'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
