# coding:utf-8
# @文件: import_utils.py
# @创建者：州的先生
# #日期：2020/6/17
# 博客地址：zmister.com
# 文集导入相关方法

from django.utils.translation import gettext_lazy as _
from app_doc.models import Doc,Project,Image
from app_doc.util_upload_img import upload_generation_dir
from app_doc.utils import libreoffice_wmf_conversion,image_trim
from django.db import transaction
from django.conf import settings
from loguru import logger
from markdownify import markdownify
import mammoth
import shutil
import os
import time
import re
import yaml
import sys
import tempfile
import json


# 导入Zip文集
class ImportZipProject():
    # 读取 Zip 压缩包
    def read_zip(self,zip_file_path,create_user):
        # 导入流程：
        # 1、解压zip压缩包文件到temp文件夹
        # 2、遍历temp文件夹内的解压后的.md文件
        # 3、读取.md文件的文本内容
        # 4、如果里面匹配到相对路径的静态文件，从指定文件夹里面读取
        # 5、上传图片，写入数据库，修改.md文件里面的url路径

        # 新建一个临时文件夹，用于存放解压的文件
        self.temp_dir = zip_file_path[:-4]
        os.mkdir(self.temp_dir)
        # 解压 zip 文件到指定临时文件夹
        shutil.unpack_archive(zip_file_path, extract_dir=self.temp_dir)

        # 处理文件夹和文件名的中文乱码
        sys_encoding = 'gbk'
        for root, dirs, files in os.walk(self.temp_dir):
            for dir in dirs:
                try:
                    new_dir = dir.encode('cp437').decode(sys_encoding)
                except:
                    new_dir = dir.encode('utf-8').decode('utf-8')
                # print(new_dir)
                os.rename(os.path.join(root, dir), os.path.join(root, new_dir))

            for file in files:
                try:
                    new_file = file.encode('cp437').decode(sys_encoding)
                except:
                    new_file = file.encode('utf-8').decode('utf-8')
                # print(root, new_file)
                os.rename(os.path.join(root, file), os.path.join(root, new_file))

        # 读取yaml文件
        try:
            with open(os.path.join(self.temp_dir ,'mrdoc.yaml'),'r',encoding='utf-8') as yaml_file:
                yaml_str = yaml.safe_load(yaml_file.read())
                project_name = yaml_str['project_name'] \
                    if 'project_name' in yaml_str.keys() else zip_file_path[:-4].split('/')[-1]
                project_desc = yaml_str['project_desc'] if 'project_desc' in yaml_str.keys() else ''
                project_role = yaml_str['project_role'] if 'project_role' in yaml_str.keys() else 1
                editor_mode = yaml_str['editor_mode'] if 'editor_mode' in yaml_str.keys() else 1
                project_toc = yaml_str['toc']
                toc_item_list = []
                for toc in project_toc:
                    # print(toc)
                    item = {
                        'name': toc['name'],
                        'file': toc['file'],
                        'parent': 0,
                    }
                    toc_item_list.append(item)
                    if 'children' in toc.keys():
                        for b in toc['children']:
                            item = {
                                'name': b['name'],
                                'file': b['file'],
                                'parent': toc['name']
                            }
                            toc_item_list.append(item)
                            if 'children' in b.keys():
                                for c in b['children']:
                                    item = {
                                        'name': c['name'],
                                        'file': c['file'],
                                        'parent': b['name']
                                    }
                                    toc_item_list.append(item)


        except:
            logger.error(_("未发现yaml文件"))
            project_name = zip_file_path[:-4].split('/')[-1]
            project_desc = ''
            project_role = 1
            editor_mode = 1
            project_toc = False

        # 开启事务
        with transaction.atomic():
            save_id = transaction.savepoint()
            try:
                # 新建文集
                project = Project.objects.create(
                    name=project_name,
                    intro=project_desc,
                    role=project_role,
                    create_user=create_user
                )
                if project_toc is False:
                    # 遍历临时文件夹中的所有文件和文件夹
                    for f in os.listdir(self.temp_dir):
                        # 获取 .md 文件
                        if f.endswith('.md'):
                            # print(f)
                            # 读取 .md 文件文本内容
                            with open(os.path.join(self.temp_dir,f),'r',encoding='utf-8') as md_file:
                                md_content = md_file.read()
                                md_content = self.operat_md_media(md_content,create_user)
                                # 新建文档
                                doc = Doc.objects.create(
                                    name = f[:-3],
                                    pre_content = md_content,
                                    top_doc = project.id,
                                    status = 0,
                                    editor_mode = editor_mode,
                                    create_user = create_user
                                )
                else:
                    for i in toc_item_list:
                        with open(os.path.join(self.temp_dir,i['file']),'r',encoding='utf-8') as md_file:
                            md_content = md_file.read()
                            md_content = self.operat_md_media(md_content, create_user)
                            # 新建文档
                            doc = Doc.objects.create(
                                name=i['name'],
                                pre_content=md_content,
                                top_doc=project.id,
                                parent_doc = (Doc.objects.get(top_doc=project.id,name=i['parent'])).id \
                                    if i['parent'] != 0 else 0,
                                status=0,
                                editor_mode=editor_mode,
                                create_user=create_user
                            )
            except:
                logger.exception(_("解析导入文件异常"))
                # 回滚事务
                transaction.savepoint_rollback(save_id)

            transaction.savepoint_commit(save_id)
        try:
            shutil.rmtree(self.temp_dir)
            os.remove(zip_file_path)
            return project.id
        except:
            logger.exception(_("删除临时文件异常"))
            return None

    # 处理MD内容中的静态文件
    def operat_md_media(self,md_content,create_user):
        # 查找MD内容中的静态文件
        pattern = r"\!\[.*?\]\(.*?\)"
        media_list = re.findall(pattern, md_content)
        # print(media_list)
        # 存在静态文件,进行遍历
        if len(media_list) > 0:
            for media in media_list:
                media_filename = media.split("(")[-1].split(")")[0] # 媒体文件的文件名
                # 存在本地图片路径
                if media_filename.startswith("./") or media_filename.startswith("/"):
                    # 获取文件后缀
                    file_suffix = media_filename.split('.')[-1]
                    if file_suffix.lower() not in settings.ALLOWED_IMG:
                        continue
                    # 判断本地图片路径是否存在
                    if media_filename.startswith("./"):
                        temp_media_file_path = os.path.join(self.temp_dir,media_filename[2:])
                    else :
                        temp_media_file_path = os.path.join(self.temp_dir, media_filename[1:])
                    if os.path.exists(temp_media_file_path):
                        # 如果存在，上传本地图片
                        dir_name = upload_generation_dir() # 获取当月文件夹名称

                        # 复制文件到媒体文件夹
                        copy2_filename = dir_name + '/' + str(time.time()) + '.' + file_suffix
                        new_media_file_path = shutil.copy2(
                            temp_media_file_path,
                            settings.MEDIA_ROOT + copy2_filename
                        )

                        # 替换MD内容的静态文件链接
                        new_media_filename = new_media_file_path.split(settings.MEDIA_ROOT,1)[-1]
                        new_media_filename = '/media' + new_media_filename

                        # 图片数据写入数据库
                        Image.objects.create(
                            user=create_user,
                            file_path=new_media_filename,
                            file_name=str(time.time())+'.'+file_suffix,
                            remark=_('本地上传'),
                        )
                        md_content = md_content.replace(media_filename, new_media_filename)
                else:
                    pass
            return md_content
        # 不存在静态文件，直接返回MD内容
        else:
            return md_content


# 导入Word文档(.docx)
class ImportDocxDoc():
    def __init__(self,docx_file_path,editor_mode,create_user):
        self.docx_file_path = docx_file_path # docx文件绝对路径
        self.tmp_img_dir = self.docx_file_path.split('.')
        self.create_user = create_user
        self.editor_mode = int(editor_mode)

    # 转存docx文件中的图片
    def convert_img(self,image):
        image = libreoffice_wmf_conversion(image, post_process=image_trim)
        if image.alt_text:
            alt = image.alt_text.replace('\n', '').replace('\r', '')
        else:
            alt = ''
        with image.open() as image_bytes:
            file_suffix = image.content_type.split("/")[1]
            file_time_name = str(time.time())
            dir_name = upload_generation_dir()  # 获取当月文件夹名称
            # 图片在媒体文件夹内的路径，形如 /202012/12542542.jpg
            copy2_filename = dir_name + '/' + file_time_name + '.' + file_suffix
            # 文件的绝对路径 形如/home/MrDoc/media/202012/12542542.jpg
            new_media_file_path = settings.MEDIA_ROOT + copy2_filename
            # 图片文件的相对url路径
            file_url = '/media' + copy2_filename

            # 图片数据写入数据库
            Image.objects.create(
                user=self.create_user,
                file_path=file_url,
                file_name=file_time_name + '.' + file_suffix,
                remark=_('本地上传'),
            )
            with open(new_media_file_path, 'wb') as f:
                f.write(image_bytes.read())
        return {"src": file_url,"alt_text":alt,"alt":alt}

    # 转换docx文件内容为HTML和Markdown
    def convert_docx(self):
        # 读取Word文件
        with open(self.docx_file_path, "rb") as docx_file:
            # 转化Word文档为HTML
            result = mammoth.convert_to_html(docx_file, convert_image=mammoth.images.img_element(self.convert_img))
            # 获取HTML内容
            html = result.value
            if self.editor_mode in [1,2]:
                # 转化HTML为Markdown
                md = markdownify(html, heading_style="ATX")
                return md
            else:
                return html

    def run(self):
        try:
            result = self.convert_docx()
            os.remove(self.docx_file_path)
            return {'status':True,'data':result}
        except:
            os.remove(self.docx_file_path)
            return {'status':False,'data':_('读取异常')}


# 使用MinerU导入多种文件格式
class ImportMinerUDoc():
    def __init__(self, file_path, editor_mode, create_user):
        self.file_path = file_path  # 文件绝对路径
        self.create_user = create_user
        self.editor_mode = int(editor_mode)
        self.supported_extensions = {
            '.pdf': 'PDF文档',
            '.xlsx': 'Excel表格',
            '.xls': 'Excel表格',
            '.ppt': 'PowerPoint演示文稿',
            '.pptx': 'PowerPoint演示文稿',
            '.md': 'Markdown文档',
            '.txt': '文本文件',
            '.doc': 'Word文档',
            '.docx': 'Word文档'
        }

    def get_file_extension(self):
        """获取文件扩展名"""
        extension = os.path.splitext(self.file_path)[1].lower()
        logger.info(f"文件路径: {self.file_path}, 扩展名: {extension}")
        return extension

    def is_supported_file(self):
        """检查文件是否支持"""
        extension = self.get_file_extension()
        is_supported = extension in self.supported_extensions
        logger.info(f"文件扩展名: {extension}, 是否支持: {is_supported}, 支持格式: {list(self.supported_extensions.keys())}")
        return is_supported

    def process_with_mineru(self):
        """使用MinerU处理文件"""
        try:
            # 创建临时输出目录
            with tempfile.TemporaryDirectory() as temp_output_dir:
                # 导入MinerU
                from mineru import MinerU
                
                # 初始化MinerU，关闭OCR处理
                mineru = MinerU(
                    enable_ocr=False,  # 关闭OCR处理
                    enable_formula=True,  # 启用公式解析
                    enable_table=True,  # 启用表格解析
                )
                
                # 处理文件
                result = mineru.process(
                    input_path=self.file_path,
                    output_path=temp_output_dir,
                    method='auto'  # 自动选择处理方法
                )
                
                # 读取生成的Markdown文件
                markdown_file = os.path.join(temp_output_dir, 'output.md')
                if os.path.exists(markdown_file):
                    with open(markdown_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return {'status': True, 'data': content}
                else:
                    # 如果没有生成Markdown文件，尝试读取JSON文件
                    json_file = os.path.join(temp_output_dir, 'output.json')
                    if os.path.exists(json_file):
                        with open(json_file, 'r', encoding='utf-8') as f:
                            json_data = json.load(f)
                        # 从JSON中提取文本内容
                        content = self.extract_text_from_json(json_data)
                        return {'status': True, 'data': content}
                    else:
                        return {'status': False, 'data': _('MinerU处理失败，未生成输出文件')}
                        
        except ImportError:
            return {'status': False, 'data': _('MinerU未安装，请先安装MinerU: pip install mineru')}
        except Exception as e:
            logger.exception(f"MinerU处理文件异常: {str(e)}")
            return {'status': False, 'data': _('MinerU处理文件异常: {}').format(str(e))}

    def extract_text_from_json(self, json_data):
        """从MinerU的JSON输出中提取文本内容"""
        try:
            content = ""
            if isinstance(json_data, dict):
                # 提取页面内容
                pages = json_data.get('pages', [])
                for page in pages:
                    # 提取文本块
                    text_blocks = page.get('text_blocks', [])
                    for block in text_blocks:
                        text = block.get('text', '')
                        if text:
                            content += text + '\n\n'
                    
                    # 提取表格
                    tables = page.get('tables', [])
                    for table in tables:
                        table_md = self.convert_table_to_markdown(table)
                        content += table_md + '\n\n'
            return content
        except Exception as e:
            logger.exception(f"提取JSON内容异常: {str(e)}")
            return str(json_data)

    def convert_table_to_markdown(self, table):
        """将表格转换为Markdown格式"""
        try:
            rows = table.get('rows', [])
            if not rows:
                return ""
            
            markdown_table = ""
            for i, row in enumerate(rows):
                cells = row.get('cells', [])
                if cells:
                    # 添加分隔符行
                    if i == 1:
                        separator = "|" + "|".join(["---"] * len(cells)) + "|\n"
                        markdown_table += separator
                    
                    # 添加数据行
                    row_content = "|" + "|".join([str(cell.get('text', '')) for cell in cells]) + "|\n"
                    markdown_table += row_content
            
            return markdown_table
        except Exception as e:
            logger.exception(f"转换表格异常: {str(e)}")
            return ""

    def run(self):
        """运行文件处理"""
        try:
            if not self.is_supported_file():
                return {'status': False, 'data': _('不支持的文件格式')}
            
            # 使用MinerU处理文件
            result = self.process_with_mineru()
            
            # 清理临时文件
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
            
            return result
            
        except Exception as e:
            logger.exception(f"ImportMinerUDoc处理异常: {str(e)}")
            # 清理临时文件
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
            return {'status': False, 'data': _('处理异常: {}').format(str(e))}
