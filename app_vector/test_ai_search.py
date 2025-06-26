# coding:utf-8
"""
AI搜索功能测试脚本
"""
import os
import sys
import django

# 添加项目根目录到Python路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MrDoc.settings')
django.setup()

from app_vector.ai_search_service import ai_search_service


def test_ai_search_service():
    """测试AI搜索服务"""
    print("=" * 50)
    print("AI搜索服务测试")
    print("=" * 50)
    
    # 测试1: 检查服务状态
    print("\n1. 检查服务状态...")
    try:
        from app_vector.services import vector_service
        milvus_connected = vector_service.milvus_service.connect()
        print(f"   Milvus连接状态: {'✓ 已连接' if milvus_connected else '✗ 连接失败'}")
        if milvus_connected:
            vector_service.milvus_service.disconnect()
    except Exception as e:
        print(f"   Milvus连接错误: {e}")
    
    print(f"   OpenAI服务状态: {'✓ 可用' if ai_search_service.client else '✗ 未配置'}")
    print(f"   使用模型: {ai_search_service.model_name}")
    
    # 测试2: 搜索意图识别
    print("\n2. 测试搜索意图识别...")
    test_queries = [
        "如何配置数据库",
        "Python教程",
        "搜索关于Django的文档",
        "什么是向量数据库"
    ]
    
    for query in test_queries:
        try:
            intent = ai_search_service.extract_search_intent(query)
            print(f"   查询: '{query}' -> 意图: {intent['intent']}")
        except Exception as e:
            print(f"   查询: '{query}' -> 错误: {e}")
    
    # 测试3: 文档搜索
    print("\n3. 测试文档搜索...")
    test_search = "Python"
    try:
        results = ai_search_service.search_documents(test_search, top_k=3)
        print(f"   搜索 '{test_search}' 找到 {len(results)} 个文档")
        for i, doc in enumerate(results[:2], 1):
            print(f"   {i}. {doc['name']} (相关度: {doc['score']:.2f})")
    except Exception as e:
        print(f"   搜索失败: {e}")
    
    # 测试4: 搜索建议
    print("\n4. 测试搜索建议...")
    try:
        suggestions = ai_search_service.get_search_suggestions("Python")
        print(f"   'Python' 的建议: {suggestions}")
    except Exception as e:
        print(f"   获取建议失败: {e}")
    
    # 测试5: 智能搜索
    print("\n5. 测试智能搜索...")
    test_questions = [
        "什么是Python",
        "如何安装Django"
    ]
    
    for question in test_questions:
        try:
            result = ai_search_service.smart_search(question, top_k=3)
            print(f"   问题: '{question}'")
            print(f"   类型: {result['type']}")
            print(f"   找到文档数: {result['total_results']}")
            if result['type'] == 'question' and result.get('answer'):
                print(f"   AI回答: {result['answer'][:100]}...")
            print()
        except Exception as e:
            print(f"   问题 '{question}' 处理失败: {e}")
    
    print("=" * 50)
    print("测试完成")
    print("=" * 50)


def test_configuration():
    """测试配置"""
    print("\n配置检查:")
    print(f"OpenAI API Key: {'✓ 已配置' if ai_search_service.openai_api_key else '✗ 未配置'}")
    print(f"OpenAI Base URL: {ai_search_service.openai_base_url}")
    print(f"模型: {ai_search_service.model_name}")
    print(f"最大Token: {ai_search_service.max_tokens}")
    print(f"温度: {ai_search_service.temperature}")


if __name__ == "__main__":
    print("AI搜索功能测试")
    print("请确保已配置OpenAI API Key和Milvus服务")
    
    test_configuration()
    test_ai_search_service() 