#!/usr/bin/env python
"""
测试配置文件加载
"""

import os
import sys
import django

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MrDoc.settings')
django.setup()

from django.conf import settings

def test_config():
    """测试配置加载"""
    print("=== 配置测试 ===")
    print(f"OPENAI_API_KEY: {getattr(settings, 'OPENAI_API_KEY', 'Not set')[:20]}...")
    print(f"OPENAI_BASE_URL: {getattr(settings, 'OPENAI_BASE_URL', 'Not set')}")
    print(f"OPENAI_MODEL: {getattr(settings, 'OPENAI_MODEL', 'Not set')}")
    print(f"OPENAI_MAX_TOKENS: {getattr(settings, 'OPENAI_MAX_TOKENS', 'Not set')}")
    print(f"OPENAI_TEMPERATURE: {getattr(settings, 'OPENAI_TEMPERATURE', 'Not set')}")
    
    # 测试RAG服务初始化
    from app_vector.rag_service import RAGService
    
    rag = RAGService()
    print(f"\n=== RAG服务配置 ===")
    print(f"max_tokens: {rag.max_tokens}")
    print(f"model_name: {rag.model_name}")
    print(f"temperature: {rag.temperature}")
    print(f"client: {'Available' if rag.client else 'Not available'}")

if __name__ == '__main__':
    test_config() 