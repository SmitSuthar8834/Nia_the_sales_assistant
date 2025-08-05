from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import IntegrationConfiguration, WorkflowConfiguration, ConfigurationAuditLog


@receiver(post_save, sender=IntegrationConfiguration)
def log_integration_save(sender, instance, created, **kwargs):
    """Log integration configuration changes"""
    action = 'create' if created else 'update'
    
    # Get the user from the current request context if available
    # In a real implementation, you'd use middleware to track the current user
    user = getattr(instance, '_current_user', None)
    if user:
        ConfigurationAuditLog.objects.create(
            user=user,
            action=action,
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
            changes={'name': instance.name, 'status': instance.status},
            success=True
        )


@receiver(post_delete, sender=IntegrationConfiguration)
def log_integration_delete(sender, instance, **kwargs):
    """Log integration configuration deletion"""
    user = getattr(instance, '_current_user', None)
    if user:
        ConfigurationAuditLog.objects.create(
            user=user,
            action='delete',
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
            changes={'name': instance.name},
            success=True
        )


@receiver(post_save, sender=WorkflowConfiguration)
def log_workflow_save(sender, instance, created, **kwargs):
    """Log workflow configuration changes"""
    action = 'create' if created else 'update'
    
    user = getattr(instance, '_current_user', None)
    if user:
        ConfigurationAuditLog.objects.create(
            user=user,
            action=action,
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
            changes={'name': instance.name, 'is_active': instance.is_active},
            success=True
        )