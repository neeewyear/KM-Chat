#!/usr/bin/env python
# coding:utf-8
"""
测试 DeepSeek 嵌入模型
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
from openai import OpenAI

def test_embedding_models():
    """测试不同的嵌入模型"""
    print("=== 测试 DeepSeek 嵌入模型 ===")
    
    # 获取配置
    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    base_url = getattr(settings, 'OPENAI_BASE_URL', 'https://api.openai.com/v1')
    
    if not api_key:
        print("错误: 未配置 API 密钥")
        return
    
    print(f"API 基础 URL: {base_url}")
    print(f"API 密钥: {api_key[:10]}...")
    
    # 创建客户端
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    # 测试文本
    test_text = "这是一个测试文本"
    
    # 尝试不同的模型
    models_to_test = [
        "text-embedding-ada-002",
        "text-embedding-3-small", 
        "text-embedding-3-large",
        "embedding-2",
        "embedding-3",
        "text-embedding-v1",
        "deepseek-embedding",
        "deepseek-embedding-v1"
    ]
    
    for model in models_to_test:
        try:
            print(f"\n测试模型: {model}")
            response = client.embeddings.create(
                model=model,
                input=test_text
            )
            embedding = response.data[0].embedding
            print(f"✅ 成功! 向量维度: {len(embedding)}")
            print(f"向量前5个值: {embedding[:5]}")
            return model  # 返回第一个成功的模型
            
        except Exception as e:
            print(f"❌ 失败: {e}")
    
    print("\n所有模型都失败了，将使用回退方法")
    return None

def test_chat_model():
    """测试聊天模型"""
    print("\n=== 测试 DeepSeek 聊天模型 ===")
    
    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    base_url = getattr(settings, 'OPENAI_BASE_URL', 'https://api.openai.com/v1')
    model_name = getattr(settings, 'OPENAI_MODEL', 'deepseek-chat')
    
    if not api_key:
        print("错误: 未配置 API 密钥")
        return
    
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    try:
        print(f"测试聊天模型: {model_name}")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": "你好，请简单介绍一下自己"}
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        print(f"✅ 聊天模型测试成功!")
        print(f"回复: {content}")
        
    except Exception as e:
        print(f"❌ 聊天模型测试失败: {e}")

def main():
    """主函数"""
    print("DeepSeek API 测试")
    print("=" * 50)
    
    # 测试嵌入模型
    working_model = test_embedding_models()
    
    # 测试聊天模型
    test_chat_model()
    
    if working_model:
        print(f"\n建议在配置中使用嵌入模型: {working_model}")
    
    print("\n测试完成")

if __name__ == '__main__':
    main() 