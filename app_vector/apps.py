# coding:utf-8
from django.apps import AppConfig


class AppVectorConfig(AppConfig):
    name = 'app_vector'
    verbose_name = '向量数据库'
    
    def ready(self):
        """应用启动时初始化"""
        import app_vector.signals
