# coding:utf-8
from django.core.management.base import BaseCommand
from app_vector.services import vector_service
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '初始化Milvus向量数据库集合'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制重新创建集合',
        )

    def handle(self, *args, **options):
        try:
            self.stdout.write('正在连接Milvus服务器...')
            
            # 连接Milvus
            if not vector_service.milvus_service.connect():
                self.stdout.write(
                    self.style.ERROR('无法连接到Milvus服务器，请检查配置')
                )
                return
            
            self.stdout.write('正在创建向量集合...')
            
            # 创建集合
            if vector_service.milvus_service.create_collection():
                self.stdout.write(
                    self.style.SUCCESS('Milvus集合创建成功！')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('Milvus集合创建失败！')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'初始化Milvus时发生错误: {e}')
            )
        finally:
            # 断开连接
            vector_service.milvus_service.disconnect() 