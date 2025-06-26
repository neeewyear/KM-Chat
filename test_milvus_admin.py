#!/usr/bin/env python
# coding:utf-8
"""
测试Milvus管理功能
"""

import os
import sys
import django

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MrDoc.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse

def test_milvus_admin():
    """测试Milvus管理功能"""
    print("=== 测试Milvus管理功能 ===")
    
    # 创建测试客户端
    client = Client()
    
    # 创建超级用户（如果不存在）
    try:
        user = User.objects.get(username='admin')
        # 确保用户是超级用户
        if not user.is_superuser:
            user.is_superuser = True
            user.is_staff = True
            user.save()
            print("已将用户设置为超级用户")
    except User.DoesNotExist:
        user = User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
        print("创建超级用户: admin/admin123")
    
    # 登录
    login_success = client.login(username='admin', password='admin123')
    print(f"登录状态: {'成功' if login_success else '失败'}")
    
    if not login_success:
        print("登录失败，无法继续测试")
        return
    
    # 测试访问Milvus管理页面
    print("\n1. 测试访问Milvus管理页面...")
    try:
        response = client.get(reverse('milvus_manage'))
        print(f"页面访问状态: {response.status_code}")
        if response.status_code == 200:
            print("✓ Milvus管理页面访问成功")
        else:
            print(f"✗ Milvus管理页面访问失败: {response.status_code}")
            print(f"响应内容: {response.content.decode()}")
    except Exception as e:
        print(f"✗ 访问Milvus管理页面异常: {e}")
    
    # 测试API接口
    print("\n2. 测试Milvus API接口...")
    try:
        response = client.get(reverse('api_milvus_collections'))
        print(f"API接口状态: {response.status_code}")
        if response.status_code == 200:
            print("✓ Milvus API接口访问成功")
            # 解析响应内容
            import json
            data = json.loads(response.content)
            print(f"响应数据: {data}")
        else:
            print(f"✗ Milvus API接口访问失败: {response.status_code}")
            print(f"响应内容: {response.content.decode()}")
    except Exception as e:
        print(f"✗ 访问Milvus API接口异常: {e}")
    
    # 测试菜单数据
    print("\n3. 测试菜单数据...")
    try:
        response = client.get(reverse('admin_center_menu'))
        print(f"菜单接口状态: {response.status_code}")
        if response.status_code == 200:
            print("✓ 菜单接口访问成功")
            # 检查是否包含Milvus菜单项
            import json
            menu_data = json.loads(response.content)
            milvus_menu = None
            for item in menu_data:
                if item.get('title') == 'Milvus知识库管理':
                    milvus_menu = item
                    break
            
            if milvus_menu:
                print("✓ Milvus菜单项已添加到后台管理菜单")
                print(f"菜单项信息: {milvus_menu}")
            else:
                print("✗ Milvus菜单项未找到")
        else:
            print(f"✗ 菜单接口访问失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 访问菜单接口异常: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    test_milvus_admin() 