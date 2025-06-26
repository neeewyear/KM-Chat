#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试MinerU集成的脚本
"""

import os
import sys
import tempfile
import json

def test_mineru_installation():
    """测试MinerU是否正确安装"""
    try:
        import mineru
        print("✓ MinerU已成功安装")
        return True
    except ImportError as e:
        print(f"✗ MinerU安装失败: {e}")
        print("请运行: pip install mineru>=2.0.0")
        return False

def test_mineru_basic_functionality():
    """测试MinerU基本功能"""
    try:
        from mineru import MinerU
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建一个简单的测试文件
            test_file_path = os.path.join(temp_dir, "test.txt")
            with open(test_file_path, 'w', encoding='utf-8') as f:
                f.write("这是一个测试文档\n\n包含一些内容用于测试MinerU的功能。")
            
            # 初始化MinerU
            mineru = MinerU(
                enable_ocr=False,  # 关闭OCR处理
                enable_formula=True,  # 启用公式解析
                enable_table=True,  # 启用表格解析
            )
            
            # 处理文件
            result = mineru.process(
                input_path=test_file_path,
                output_path=temp_dir,
                method='auto'
            )
            
            print("✓ MinerU基本功能测试通过")
            return True
            
    except Exception as e:
        print(f"✗ MinerU基本功能测试失败: {e}")
        return False

def test_import_utils():
    """测试ImportMinerUDoc类"""
    try:
        # 添加项目路径到sys.path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        from app_doc.import_utils import ImportMinerUDoc
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建一个简单的测试文件
            test_file_path = os.path.join(temp_dir, "test.txt")
            with open(test_file_path, 'w', encoding='utf-8') as f:
                f.write("这是一个测试文档\n\n包含一些内容用于测试ImportMinerUDoc的功能。")
            
            # 测试ImportMinerUDoc类
            importer = ImportMinerUDoc(
                file_path=test_file_path,
                editor_mode=1,
                create_user=None  # 测试时不创建用户
            )
            
            # 检查文件格式支持
            if importer.is_supported_file():
                print("✓ ImportMinerUDoc文件格式检查通过")
            else:
                print("✗ ImportMinerUDoc文件格式检查失败")
                return False
            
            print("✓ ImportMinerUDoc类测试通过")
            return True
            
    except Exception as e:
        print(f"✗ ImportMinerUDoc类测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试MinerU集成...")
    print("=" * 50)
    
    # 测试MinerU安装
    if not test_mineru_installation():
        return False
    
    # 测试MinerU基本功能
    if not test_mineru_basic_functionality():
        return False
    
    # 测试ImportMinerUDoc类
    if not test_import_utils():
        return False
    
    print("=" * 50)
    print("✓ 所有测试通过！MinerU集成成功。")
    print("\n支持的文件格式:")
    print("- PDF文档 (.pdf)")
    print("- Excel表格 (.xlsx, .xls)")
    print("- PowerPoint演示文稿 (.ppt, .pptx)")
    print("- Word文档 (.doc, .docx)")
    print("- Markdown文档 (.md)")
    print("- 文本文件 (.txt)")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 