# coding:utf-8
from django.contrib import admin
from .models import DocumentVector, VectorCollection, ChatSession, ChatMessage


@admin.register(DocumentVector)
class DocumentVectorAdmin(admin.ModelAdmin):
    list_display = ['doc', 'vector_id', 'content_hash', 'create_time', 'update_time']
    list_filter = ['create_time', 'update_time']
    search_fields = ['doc__name', 'vector_id', 'content_hash']
    readonly_fields = ['create_time', 'update_time']


@admin.register(VectorCollection)
class VectorCollectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'dimension', 'is_active', 'create_time']
    list_filter = ['is_active', 'create_time']
    search_fields = ['name', 'description']
    readonly_fields = ['create_time']


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'is_active', 'create_time', 'update_time']
    list_filter = ['is_active', 'create_time', 'update_time']
    search_fields = ['user__username', 'title']
    readonly_fields = ['create_time', 'update_time']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'role', 'content_preview', 'tokens_used', 'create_time']
    list_filter = ['role', 'create_time']
    search_fields = ['session__title', 'content']
    readonly_fields = ['create_time']
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = '内容预览'
