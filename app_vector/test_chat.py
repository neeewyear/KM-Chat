#!/usr/bin/env python
# coding:utf-8
"""
测试 RAG 聊天功能
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

def test_chat():
    """测试聊天功能"""
    print("=== 测试 RAG 聊天功能 ===")
    
    # 获取或创建测试用户
    try:
        user = User.objects.get(username='admin')
    except User.DoesNotExist:
        print("创建测试用户...")
        user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
    
    print(f"使用用户: {user.username}")
    
    # 测试消息
    test_message = "你好，请介绍一下这个系统"
    
    print(f"发送消息: {test_message}")
    
    try:
        # 调用聊天功能
        result = rag_service.chat(user, None, test_message)
        
        if 'error' in result:
            print(f"❌ 聊天失败: {result['error']}")
        else:
            print(f"✅ 聊天成功!")
            print(f"会话ID: {result['session_id']}")
            print(f"会话标题: {result['session_title']}")
            print(f"用户消息: {result['user_message']['content']}")
            print(f"AI回复: {result['assistant_message']['content']}")
            print(f"使用的Token: {result['assistant_message']['tokens_used']}")
            
            if result['assistant_message']['reference_docs']:
                print(f"参考文档数量: {len(result['assistant_message']['reference_docs'])}")
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_chat() 