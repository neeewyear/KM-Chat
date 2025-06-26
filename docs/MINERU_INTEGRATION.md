# MinerU集成文档

## 概述

MrDoc现已集成[MinerU](https://github.com/opendatalab/MinerU)，支持导入更多文件格式，包括PDF、Excel、PowerPoint等文档格式。

## 支持的文件格式

- **PDF文档** (.pdf)
- **Excel表格** (.xlsx, .xls)
- **PowerPoint演示文稿** (.ppt, .pptx)
- **Word文档** (.doc, .docx)
- **Markdown文档** (.md)
- **文本文件** (.txt)

## 安装要求

### 1. 安装MinerU

```bash
pip install mineru>=2.0.0
```

### 2. 更新MrDoc依赖

确保`requirements.txt`中包含：

```
mineru>=2.0.0
```

然后运行：

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 在文档编辑器中导入文件

1. 打开文档编辑器
2. 点击"导入"菜单
3. 选择相应的文件格式：
   - **PDF文档** - 点击"PDF文档(.pdf)"
   - **Excel表格** - 点击"Excel表格(.xlsx/.xls)"
   - **PowerPoint** - 点击"PowerPoint(.ppt/.pptx)"
   - **Word文档** - 点击"Word文档(.docx)"
   - **文本文件** - 点击"文本文件"

### 2. 批量导入到文集

1. 进入文集管理页面
2. 选择"导入本地文档到文集"
3. 选择目标文集和编辑器模式
4. 点击上传按钮，支持所有上述文件格式

## 功能特性

### OCR处理

- **默认关闭OCR**：为了提高处理速度，默认关闭了OCR处理
- **自动文本提取**：MinerU会自动提取文档中的文本内容
- **表格识别**：支持表格结构的识别和转换
- **公式解析**：支持数学公式的识别和转换

### 输出格式

- **Markdown格式**：所有文档都会转换为Markdown格式
- **保持结构**：尽可能保持原文档的标题层级和结构
- **表格转换**：表格会被转换为Markdown表格格式

## 配置选项

### MinerU配置

在`app_doc/import_utils.py`中的`ImportMinerUDoc`类可以调整以下配置：

```python
mineru = MinerU(
    enable_ocr=False,      # 关闭OCR处理
    enable_formula=True,   # 启用公式解析
    enable_table=True,     # 启用表格解析
)
```

### 文件大小限制

- 默认文件大小限制：50MB
- 可在`views_import.py`中调整`52428800`这个值

## 故障排除

### 常见问题

1. **MinerU未安装**
   ```
   错误：MinerU未安装，请先安装MinerU: pip install mineru
   解决：运行 pip install mineru>=2.0.0
   ```

2. **文件格式不支持**
   ```
   错误：不支持的文件格式: .xxx
   解决：检查文件扩展名是否在支持列表中
   ```

3. **文件处理失败**
   ```
   错误：MinerU处理文件异常
   解决：检查文件是否损坏，或尝试其他文件
   ```

### 测试集成

运行测试脚本验证集成是否正常：

```bash
python test_mineru_integration.py
```

## 技术实现

### 核心组件

1. **ImportMinerUDoc类** (`app_doc/import_utils.py`)
   - 处理多种文件格式
   - 调用MinerU进行文档解析
   - 提取文本内容并转换为Markdown

2. **ImportLocalDoc API** (`app_doc/views_import.py`)
   - 处理文件上传
   - 根据文件格式选择处理方法
   - 创建文档记录

3. **前端界面** (`template/app_doc/editor/create_doc.html`)
   - 添加新的导入选项
   - 处理文件上传和响应

### 处理流程

1. 用户选择文件并上传
2. 系统检查文件格式是否支持
3. 根据文件格式选择处理方法：
   - `.md/.txt` - 直接读取
   - `.docx` - 使用现有的ImportDocxDoc
   - 其他格式 - 使用MinerU处理
4. 提取文本内容并转换为Markdown
5. 创建文档记录并返回结果

## 更新日志

### v1.0.0
- 集成MinerU支持多种文件格式
- 添加PDF、Excel、PowerPoint支持
- 关闭OCR处理以提高速度
- 支持表格和公式解析

## 贡献

如果您在使用过程中遇到问题或有改进建议，请：

1. 检查本文档的故障排除部分
2. 运行测试脚本验证环境
3. 提交Issue或Pull Request

## 许可证

MinerU遵循AGPL-3.0许可证，请确保您的使用符合许可证要求。 