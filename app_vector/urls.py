# coding:utf-8
from django.urls import path
from . import views

app_name = 'app_vector'

urlpatterns = [
    # RAG智能问答相关
    path('chat/', views.rag_chat_page, name='chat'),
    path('api/chat/sessions/', views.api_get_chat_sessions, name='api_get_chat_sessions'),
    path('api/chat/sessions/<int:session_id>/messages/', views.api_get_session_messages, name='api_get_session_messages'),
    path('api/chat/', views.api_chat, name='api_chat'),
    path('api/chat/sessions/<int:session_id>/', views.api_delete_session, name='api_delete_session'),
    
    # 向量搜索相关
    path('search/', views.vector_search_page, name='search'),
    path('test/', views.vector_test_page, name='test'),
    path('status/', views.vector_status_page, name='status'),
    
    # API接口
    path('api/status/', views.api_vector_status, name='api_status'),
    path('api/search/', views.api_search_similar_documents, name='api_search'),
    path('api/store/', views.api_store_document_vector, name='api_store'),
    path('api/delete/<int:doc_id>/', views.api_delete_document_vector, name='api_delete'),
    
    # 公开接口（不需要登录）
    path('search/public/', views.vector_search_page_public, name='search_public'),
    path('api/status/public/', views.api_vector_status_public, name='api_status_public'),
    path('search/public/api/', views.search_similar_documents_public, name='search_public_api'),
] 