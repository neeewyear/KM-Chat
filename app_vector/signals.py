# coding:utf-8
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from app_doc.models import Doc
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Doc)
def handle_doc_save(sender, instance, created, **kwargs):
    """处理文档保存信号"""
    try:
        # 延迟导入向量服务，避免启动时出错
        from .services import vector_service
        
        # 获取文档内容
        content = instance.content or instance.pre_content or ""
        
        if content.strip():
            # 存储文档向量
            success = vector_service.store_document_vector(instance.id, content)
            if success:
                logger.info(f"Successfully stored vector for doc {instance.id}")
            else:
                logger.error(f"Failed to store vector for doc {instance.id}")
        else:
            logger.warning(f"Doc {instance.id} has no content, skipping vector storage")
            
    except ImportError as e:
        logger.warning(f"Vector service not available, skipping vector storage for doc {instance.id}: {e}")
    except Exception as e:
        logger.error(f"Error handling doc save signal: {e}")


@receiver(post_delete, sender=Doc)
def handle_doc_delete(sender, instance, **kwargs):
    """处理文档删除信号"""
    try:
        # 延迟导入向量服务，避免启动时出错
        from .services import vector_service
        
        # 删除文档向量
        success = vector_service.delete_document_vector(instance.id)
        if success:
            logger.info(f"Successfully deleted vector for doc {instance.id}")
        else:
            logger.error(f"Failed to delete vector for doc {instance.id}")
            
    except ImportError as e:
        logger.warning(f"Vector service not available, skipping vector deletion for doc {instance.id}: {e}")
    except Exception as e:
        logger.error(f"Error handling doc delete signal: {e}") 