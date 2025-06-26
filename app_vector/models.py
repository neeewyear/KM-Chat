# coding:utf-8
from django.db import models
from django.contrib.auth.models import User


class DocumentVector(models.Model):
    """文档向量模型"""
    doc = models.ForeignKey('app_doc.Doc', on_delete=models.CASCADE, verbose_name="文档")
    vector_id = models.CharField(max_length=100, verbose_name="向量ID")
    content_hash = models.CharField(max_length=64, verbose_name="内容哈希")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = '文档向量'
        verbose_name_plural = verbose_name
        unique_together = ['doc', 'vector_id']
        indexes = [
            models.Index(fields=['doc']),
            models.Index(fields=['content_hash']),
        ]
    
    def __str__(self):
        return f"{self.doc.name} - {self.vector_id}"


class VectorCollection(models.Model):
    """向量集合模型"""
    name = models.CharField(max_length=100, verbose_name="集合名称")
    dimension = models.IntegerField(default=1536, verbose_name="向量维度")
    description = models.TextField(blank=True, null=True, verbose_name="描述")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        verbose_name = '向量集合'
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return self.name


class ChatSession(models.Model):
    """聊天会话模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    title = models.CharField(max_length=200, verbose_name="会话标题")
    is_active = models.BooleanField(default=True, verbose_name="是否活跃")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = '聊天会话'
        verbose_name_plural = verbose_name
        ordering = ['-update_time']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class ChatMessage(models.Model):
    """聊天消息模型"""
    ROLE_CHOICES = [
        ('user', '用户'),
        ('assistant', '助手'),
        ('system', '系统'),
    ]
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, verbose_name="会话")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, verbose_name="角色")
    content = models.TextField(verbose_name="消息内容")
    reference_docs = models.JSONField(default=list, blank=True, verbose_name="参考文档")
    tokens_used = models.IntegerField(default=0, verbose_name="使用的令牌数")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        verbose_name = '聊天消息'
        verbose_name_plural = verbose_name
        ordering = ['create_time']
    
    def __str__(self):
        return f"{self.session.title} - {self.role} - {self.content[:50]}"
