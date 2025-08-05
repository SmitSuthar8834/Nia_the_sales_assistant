from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from .models import (
    ConfigurationTemplate, IntegrationConfiguration, WorkflowConfiguration,
    ConfigurationBackup, RolePermission, ConfigurationAuditLog, ConfigurationTest
)


@admin.register(ConfigurationTemplate)
class ConfigurationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'version', 'is_official', 'is_active', 'usage_count', 'created_at']
    list_filter = ['category', 'is_official', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'version', 'is_official', 'is_active')
        }),
        ('Configuration Schema', {
            'fields': ('configuration_schema', 'default_configuration', 'ui_schema'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'usage_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(IntegrationConfiguration)
class IntegrationConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'integration_type', 'status', 'health_status', 'created_by', 'last_tested', 'created_at']
    list_filter = ['integration_type', 'status', 'health_status', 'created_at']
    search_fields = ['name', 'description', 'organization']
    readonly_fields = ['created_at', 'updated_at', 'last_tested', 'last_sync', 'error_count']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'integration_type', 'status', 'organization')
        }),
        ('Configuration', {
            'fields': ('template', 'configuration', 'credentials'),
            'classes': ('collapse',)
        }),
        ('Health & Monitoring', {
            'fields': ('health_status', 'health_details', 'error_count', 'last_error'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'last_tested', 'last_sync'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_health_status_display(self, obj):
        colors = {
            'healthy': 'green',
            'warning': 'orange',
            'critical': 'red',
            'unknown': 'gray'
        }
        color = colors.get(obj.health_status, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.health_status.title()
        )
    get_health_status_display.short_description = 'Health Status'


@admin.register(WorkflowConfiguration)
class WorkflowConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'trigger_type', 'is_active', 'execution_count', 'success_rate', 'created_by', 'created_at']
    list_filter = ['trigger_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'execution_count', 'last_execution', 'success_rate']
    filter_horizontal = ['required_integrations']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Workflow Configuration', {
            'fields': ('trigger_type', 'trigger_config', 'workflow_steps', 'visual_config'),
            'classes': ('collapse',)
        }),
        ('Dependencies', {
            'fields': ('required_integrations',)
        }),
        ('Execution Statistics', {
            'fields': ('execution_count', 'last_execution', 'success_rate'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ConfigurationBackup)
class ConfigurationBackupAdmin(admin.ModelAdmin):
    list_display = ['name', 'backup_type', 'file_size_display', 'restored_count', 'created_by', 'created_at']
    list_filter = ['backup_type', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'file_size', 'restored_count', 'last_restored']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'backup_type')
        }),
        ('Backup Data', {
            'fields': ('configurations', 'workflows', 'templates'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('file_size', 'restored_count', 'last_restored'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def file_size_display(self, obj):
        if obj.file_size:
            if obj.file_size < 1024:
                return f"{obj.file_size} B"
            elif obj.file_size < 1024 * 1024:
                return f"{obj.file_size / 1024:.1f} KB"
            else:
                return f"{obj.file_size / (1024 * 1024):.1f} MB"
        return "0 B"
    file_size_display.short_description = 'File Size'


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'permission_type', 'resource_type', 'is_active', 'granted_by', 'granted_at', 'expires_at']
    list_filter = ['permission_type', 'resource_type', 'is_active', 'granted_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['granted_at']
    
    fieldsets = (
        ('Permission Details', {
            'fields': ('user', 'permission_type', 'resource_type', 'is_active')
        }),
        ('Resource Specific', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        ('Conditions & Expiry', {
            'fields': ('conditions', 'expires_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('granted_by', 'granted_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.granted_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ConfigurationAuditLog)
class ConfigurationAuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'content_type', 'success', 'ip_address']
    list_filter = ['action', 'success', 'timestamp', 'content_type']
    search_fields = ['user__username', 'user__email', 'changes']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Action Details', {
            'fields': ('user', 'action', 'content_type', 'object_id', 'success')
        }),
        ('Changes', {
            'fields': ('changes', 'old_values', 'new_values'),
            'classes': ('collapse',)
        }),
        ('Context', {
            'fields': ('ip_address', 'user_agent', 'session_key'),
            'classes': ('collapse',)
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(ConfigurationTest)
class ConfigurationTestAdmin(admin.ModelAdmin):
    list_display = ['configuration', 'test_type', 'status', 'success', 'duration_ms', 'triggered_by', 'started_at']
    list_filter = ['test_type', 'status', 'success', 'started_at']
    search_fields = ['configuration__name']
    readonly_fields = ['started_at', 'completed_at', 'duration_ms']
    
    fieldsets = (
        ('Test Details', {
            'fields': ('configuration', 'test_type', 'status', 'success')
        }),
        ('Test Data', {
            'fields': ('test_data', 'expected_result', 'actual_result'),
            'classes': ('collapse',)
        }),
        ('Execution Details', {
            'fields': ('started_at', 'completed_at', 'duration_ms', 'triggered_by'),
            'classes': ('collapse',)
        }),
        ('Results', {
            'fields': ('response_data', 'error_message'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.triggered_by = request.user
        super().save_model(request, obj, form, change)