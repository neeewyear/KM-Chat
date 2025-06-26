#!/usr/bin/env python
# coding:utf-8
"""
RAG功能测试脚本
"""

import os
import sys
import django

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MrDoc.settings')
django.setup()

from django.contrib.auth.models import User
from app_vector.rag_service import rag_service
from app_vector.services import vector_service


def test_vector_service():
    """测试向量服务"""
    print("=== 测试向量服务 ===")
    
    # 测试连接
    print("1. 测试Milvus连接...")
    connected = vector_service.milvus_service.connect()
    print(f"连接状态: {'成功' if connected else '失败'}")
    
    if connected:
        # 测试创建集合
        print("2. 测试创建集合...")
        created = vector_service.milvus_service.create_collection()
        print(f"集合创建: {'成功' if created else '失败'}")
        
        # 测试向量化
        print("3. 测试文本向量化...")
        test_text = "这是一个测试文档"
        embedding = vector_service.get_text_embedding(test_text)
        print(f"向量维度: {len(embedding) if embedding else 0}")
        
        vector_service.milvus_service.disconnect()
    
    print()


def test_rag_service():
    """测试RAG服务"""
    print("=== 测试RAG服务 ===")
    
    # 检查OpenAI配置
    print("1. 检查OpenAI配置...")
    if not rag_service.openai_api_key:
        print("警告: OpenAI API密钥未配置")
        return
    
    print("OpenAI配置正常")
    
    # 测试创建会话
    print("2. 测试创建会话...")
    try:
        user = User.objects.first()
        if not user:
            print("错误: 没有找到用户")
            return
        
        session = rag_service.create_chat_session(user, "测试会话")
        print(f"会话创建成功: {session.id}")
        
        # 测试获取会话列表
        print("3. 测试获取会话列表...")
        sessions = rag_service.get_user_sessions(user)
        print(f"用户会话数量: {len(sessions)}")
        
        # 测试删除会话
        print("4. 测试删除会话...")
        deleted = rag_service.delete_session(user, session.id)
        print(f"会话删除: {'成功' if deleted else '失败'}")
        
    except Exception as e:
        print(f"测试失败: {e}")
    
    print()


def test_chat_function():
    """测试聊天功能"""
    print("=== 测试聊天功能 ===")
    
    if not rag_service.openai_api_key:
        print("跳过聊天测试: OpenAI API密钥未配置")
        return
    
    try:
        user = User.objects.first()
        if not user:
            print("错误: 没有找到用户")
            return
        
        # 测试聊天
        print("1. 测试聊天功能...")
        result = rag_service.chat(user, None, "你好，请介绍一下自己")
        
        if 'error' in result:
            print(f"聊天失败: {result['error']}")
        else:
            print("聊天成功")
            print(f"会话ID: {result['session_id']}")
            print(f"会话标题: {result['session_title']}")
            print(f"AI回复: {result['assistant_message']['content'][:100]}...")
            print(f"参考文档数量: {len(result['assistant_message']['reference_docs'])}")
        
    except Exception as e:
        print(f"聊天测试失败: {e}")
    
    print()


def main():
    """主函数"""
    print("MrDoc RAG功能测试")
    print("=" * 50)
    
    # 测试向量服务
    test_vector_service()
    
    # 测试RAG服务
    test_rag_service()
    
    # 测试聊天功能
    test_chat_function()
    
    print("测试完成")


if __name__ == '__main__':
    main() 