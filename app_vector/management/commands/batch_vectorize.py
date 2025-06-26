# coding:utf-8
from django.core.management.base import BaseCommand
from app_doc.models import Doc
from app_vector.services import vector_service
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '批量向量化现有文档'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project',
            type=int,
            help='指定项目ID，只处理该项目的文档',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='每次处理的文档数量限制',
        )

    def handle(self, *args, **options):
        try:
            self.stdout.write('开始批量向量化文档...')
            
            # 获取文档查询集
            docs = Doc.objects.filter(status=1)  # 只处理已发布的文档
            
            if options['project']:
                docs = docs.filter(top_doc=options['project'])
                self.stdout.write(f'只处理项目ID为 {options["project"]} 的文档')
            
            total_docs = docs.count()
            self.stdout.write(f'总共需要处理 {total_docs} 个文档')
            
            processed = 0
            success = 0
            failed = 0
            
            # 分批处理
            batch_size = options['limit']
            for i in range(0, total_docs, batch_size):
                batch_docs = docs[i:i + batch_size]
                
                for doc in batch_docs:
                    try:
                        # 获取文档内容
                        content = doc.content or doc.pre_content or ""
                        
                        if content.strip():
                            # 存储向量
                            if vector_service.store_document_vector(doc.id, content):
                                success += 1
                                self.stdout.write(f'✓ 文档 {doc.id} ({doc.name}) 向量化成功')
                            else:
                                failed += 1
                                self.stdout.write(f'✗ 文档 {doc.id} ({doc.name}) 向量化失败')
                        else:
                            self.stdout.write(f'- 文档 {doc.id} ({doc.name}) 内容为空，跳过')
                            
                    except Exception as e:
                        failed += 1
                        self.stdout.write(f'✗ 文档 {doc.id} ({doc.name}) 处理异常: {e}')
                    
                    processed += 1
                    
                    # 显示进度
                    if processed % 10 == 0:
                        self.stdout.write(f'进度: {processed}/{total_docs}')
            
            # 显示最终结果
            self.stdout.write(
                self.style.SUCCESS(
                    f'批量向量化完成！\n'
                    f'总计: {total_docs}\n'
                    f'成功: {success}\n'
                    f'失败: {failed}\n'
                    f'跳过: {total_docs - success - failed}'
                )
            )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'批量向量化时发生错误: {e}')
            ) 