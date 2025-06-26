# coding:utf-8
"""
简单的AI搜索功能测试
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

def test_ai_search():
    """测试AI搜索功能"""
    try:
        from app_vector.ai_search_service import ai_search_service
        
        print("=" * 50)
        print("AI搜索功能测试")
        print("=" * 50)
        
        # 测试配置
        print(f"OpenAI API Key: {'✓ 已配置' if ai_search_service.openai_api_key else '✗ 未配置'}")
        print(f"OpenAI Base URL: {ai_search_service.openai_base_url}")
        print(f"模型: {ai_search_service.model_name}")
        
        if not ai_search_service.openai_api_key:
            print("\n⚠️  请先配置OpenAI API Key")
            return
        
        # 测试搜索
        test_queries = [
            "Python教程",
            "如何配置数据库？",
            "Django框架",
            "什么是向量数据库？"
        ]
        
        for query in test_queries:
            print(f"\n🔍 测试查询: '{query}'")
            try:
                result = ai_search_service.smart_search(query, top_k=3)
                print(f"   类型: {result['type']}")
                print(f"   找到文档数: {result['total_results']}")
                print(f"   有AI回答: {'✓' if result.get('answer') else '✗'}")
                if result.get('answer'):
                    print(f"   AI回答预览: {result['answer'][:100]}...")
                print(f"   有摘要: {'✓' if result.get('summary') else '✗'}")
            except Exception as e:
                print(f"   错误: {e}")
        
        print("\n" + "=" * 50)
        print("测试完成")
        
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    test_ai_search() 