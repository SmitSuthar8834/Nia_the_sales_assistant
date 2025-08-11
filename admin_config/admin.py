import json

from django.contrib import admin
from django.db import models
from django.forms import Textarea
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    ConfigurationAuditLog,
    ConfigurationBackup,
    ConfigurationTemplate,
    ConfigurationTest,
    IntegrationConfiguration,
    WorkflowConfiguration,
)


class BaseAdminConfig:
    """Base configuration for all admin classes"""

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            readonly_fields.extend(["created_by", "created_at", "updated_at"])
        return readonly_fields


@admin.register(ConfigurationTemplate)
class ConfigurationTemplateAdmin(BaseAdminConfig, admin.ModelAdmin):
    list_display = [
        "name",
        "category",
        "version",
        "is_official",
        "is_active",
        "usage_count",
        "created_by",
        "created_at",
        "template_actions",
    ]
    list_filter = ["category", "is_official", "is_active", "created_at"]
    search_fields = ["name", "description", "category"]
    readonly_fields = ["id", "created_at", "updated_at", "usage_count"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "description", "category", "version")},
        ),
        ("Status", {"fields": ("is_official", "is_active", "usage_count")}),
        (
            "Configuration Schema",
            {
                "fields": (
                    "configuration_schema_display",
                    "default_configuration_display",
                    "ui_schema_display",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Raw Data (Advanced)",
            {
                "fields": (
                    "configuration_schema",
                    "default_configuration",
                    "ui_schema",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("id", "created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    formfield_overrides = {
        models.JSONField: {"widget": Textarea(attrs={"rows": 10, "cols": 80})},
    }

    def configuration_schema_display(self, obj):
        if obj.configuration_schema:
            formatted_json = json.dumps(obj.configuration_schema, indent=2)
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px;">{}</pre>',
                formatted_json,
            )
        return "No schema defined"

    configuration_schema_display.short_description = "Configuration Schema (Formatted)"

    def default_configuration_display(self, obj):
        if obj.default_configuration:
            formatted_json = json.dumps(obj.default_configuration, indent=2)
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px;">{}</pre>',
                formatted_json,
            )
        return "No default configuration"

    default_configuration_display.short_description = (
        "Default Configuration (Formatted)"
    )

    def ui_schema_display(self, obj):
        if obj.ui_schema:
            formatted_json = json.dumps(obj.ui_schema, indent=2)
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px;">{}</pre>',
                formatted_json,
            )
        return "No UI schema defined"

    ui_schema_display.short_description = "UI Schema (Formatted)"

    def template_actions(self, obj):
        actions = []

        # Use template action
        use_url = (
            reverse("admin:admin_config_integrationconfiguration_add")
            + f"?template={obj.id}"
        )
        actions.append(
            f'<a href="{use_url}" class="button" style="background: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">Use Template</a>'
        )

        # Export template action
        export_url = f"/admin/admin_config/configurationtemplate/{obj.id}/export/"
        actions.append(
            f'<a href="{export_url}" class="button" style="background: #17a2b8; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">Export</a>'
        )

        # Clone template action
        clone_url = f"/admin/admin_config/configurationtemplate/{obj.id}/clone/"
        actions.append(
            f'<a href="{clone_url}" class="button" style="background: #6c757d; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Clone</a>'
        )

        return format_html("".join(actions))

    template_actions.short_description = "Actions"
    template_actions.allow_tags = True

    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(IntegrationConfiguration)
class IntegrationConfigurationAdmin(BaseAdminConfig, admin.ModelAdmin):
    list_display = [
        "name",
        "integration_type_badge",
        "status_badge",
        "template_link",
        "health_status_badge",
        "last_tested",
        "created_by",
        "integration_actions",
    ]
    list_filter = [
        "integration_type",
        "status",
        "health_status",
        "created_at",
        "template",
    ]
    search_fields = ["name", "description", "organization"]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "last_tested",
        "last_sync",
        "health_status",
        "health_details_display",
        "error_count",
        "last_error",
    ]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "name",
                    "description",
                    "integration_type",
                    "status",
                    "organization",
                )
            },
        ),
        (
            "Template & Configuration",
            {
                "fields": ("template", "configuration_display", "credentials_display"),
            },
        ),
        (
            "Health & Monitoring",
            {
                "fields": (
                    "health_status",
                    "health_details_display",
                    "error_count",
                    "last_error",
                    "last_tested",
                    "last_sync",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Raw Data (Advanced)",
            {"fields": ("configuration", "credentials"), "classes": ("collapse",)},
        ),
        (
            "Metadata",
            {
                "fields": ("id", "created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    formfield_overrides = {
        models.JSONField: {"widget": Textarea(attrs={"rows": 8, "cols": 80})},
    }

    def integration_type_badge(self, obj):
        colors = {
            "crm_salesforce": "#1f77b4",
            "crm_hubspot": "#ff7f0e",
            "crm_pipedrive": "#2ca02c",
            "meeting_google": "#d62728",
            "meeting_teams": "#9467bd",
            "ai_gemini": "#8c564b",
        }
        color = colors.get(obj.integration_type, "#17a2b8")
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            obj.get_integration_type_display(),
        )

    integration_type_badge.short_description = "Type"
    integration_type_badge.admin_order_field = "integration_type"

    def status_badge(self, obj):
        colors = {
            "draft": "#6c757d",
            "active": "#28a745",
            "inactive": "#ffc107",
            "error": "#dc3545",
            "testing": "#17a2b8",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"
    status_badge.admin_order_field = "status"

    def health_status_badge(self, obj):
        colors = {
            "healthy": "#28a745",
            "warning": "#ffc107",
            "error": "#dc3545",
            "unknown": "#6c757d",
        }
        color = colors.get(obj.health_status, "#6c757d")
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            obj.health_status.title(),
        )

    health_status_badge.short_description = "Health"
    health_status_badge.admin_order_field = "health_status"

    def template_link(self, obj):
        if obj.template:
            url = reverse(
                "admin:admin_config_configurationtemplate_change",
                args=[obj.template.id],
            )
            return format_html(
                '<a href="{}" style="color: #007cba;">{}</a>', url, obj.template.name
            )
        return "No template"

    template_link.short_description = "Template"

    def configuration_display(self, obj):
        if obj.configuration:
            formatted_json = json.dumps(obj.configuration, indent=2)
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; max-height: 300px; overflow-y: auto;">{}</pre>',
                formatted_json,
            )
        return "No configuration"

    configuration_display.short_description = "Configuration (Formatted)"

    def credentials_display(self, obj):
        if obj.credentials:
            # Mask sensitive data
            masked_creds = {}
            for key, value in obj.credentials.items():
                if any(
                    sensitive in key.lower()
                    for sensitive in ["password", "secret", "key", "token"]
                ):
                    masked_creds[key] = "***MASKED***"
                else:
                    masked_creds[key] = value
            formatted_json = json.dumps(masked_creds, indent=2)
            return format_html(
                '<pre style="background: #fff3cd; padding: 10px; border-radius: 4px; max-height: 200px; overflow-y: auto;">{}</pre>',
                formatted_json,
            )
        return "No credentials"

    credentials_display.short_description = "Credentials (Masked)"

    def health_details_display(self, obj):
        if obj.health_details:
            formatted_json = json.dumps(obj.health_details, indent=2)
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; max-height: 200px; overflow-y: auto;">{}</pre>',
                formatted_json,
            )
        return "No health details"

    health_details_display.short_description = "Health Details"

    def integration_actions(self, obj):
        actions = []

        # Test integration
        test_url = f"/admin/admin_config/integrationconfiguration/{obj.id}/test/"
        actions.append(
            f'<a href="{test_url}" class="button" style="background: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">Test</a>'
        )

        # Activate/Deactivate
        if obj.status == "active":
            toggle_url = (
                f"/admin/admin_config/integrationconfiguration/{obj.id}/deactivate/"
            )
            actions.append(
                f'<a href="{toggle_url}" class="button" style="background: #ffc107; color: black; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">Deactivate</a>'
            )
        else:
            toggle_url = (
                f"/admin/admin_config/integrationconfiguration/{obj.id}/activate/"
            )
            actions.append(
                f'<a href="{toggle_url}" class="button" style="background: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">Activate</a>'
            )

        # Export configuration
        export_url = f"/admin/admin_config/integrationconfiguration/{obj.id}/export/"
        actions.append(
            f'<a href="{export_url}" class="button" style="background: #17a2b8; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Export</a>'
        )

        return format_html("".join(actions))

    integration_actions.short_description = "Actions"
    integration_actions.allow_tags = True

    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(WorkflowConfiguration)
class WorkflowConfigurationAdmin(BaseAdminConfig, admin.ModelAdmin):
    list_display = [
        "name",
        "trigger_type_badge",
        "is_active_badge",
        "execution_count",
        "success_rate_display",
        "last_execution",
        "workflow_actions",
    ]
    list_filter = ["trigger_type", "is_active", "created_at", "last_execution"]
    search_fields = ["name", "description"]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "execution_count",
        "last_execution",
        "success_rate",
    ]
    filter_horizontal = ["required_integrations"]

    fieldsets = (
        ("Basic Information", {"fields": ("name", "description", "is_active")}),
        (
            "Trigger Configuration",
            {"fields": ("trigger_type", "trigger_config_display")},
        ),
        (
            "Workflow Steps",
            {
                "fields": ("workflow_steps_display", "visual_config_display"),
            },
        ),
        ("Dependencies", {"fields": ("required_integrations",)}),
        (
            "Execution Statistics",
            {
                "fields": ("execution_count", "last_execution", "success_rate"),
                "classes": ("collapse",),
            },
        ),
        (
            "Raw Data (Advanced)",
            {
                "fields": ("trigger_config", "workflow_steps", "visual_config"),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("id", "created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def trigger_type_badge(self, obj):
        colors = {
            "manual": "#6c757d",
            "schedule": "#28a745",
            "event": "#17a2b8",
            "webhook": "#ffc107",
            "api_call": "#dc3545",
        }
        color = colors.get(obj.trigger_type, "#6c757d")
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            obj.get_trigger_type_display(),
        )

    trigger_type_badge.short_description = "Trigger"
    trigger_type_badge.admin_order_field = "trigger_type"

    def is_active_badge(self, obj):
        color = "#28a745" if obj.is_active else "#dc3545"
        text = "Active" if obj.is_active else "Inactive"
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            text,
        )

    is_active_badge.short_description = "Status"
    is_active_badge.admin_order_field = "is_active"

    def success_rate_display(self, obj):
        if obj.success_rate is not None:
            color = (
                "#28a745"
                if obj.success_rate >= 80
                else "#ffc107" if obj.success_rate >= 60 else "#dc3545"
            )
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
                color,
                obj.success_rate,
            )
        return "N/A"

    success_rate_display.short_description = "Success Rate"
    success_rate_display.admin_order_field = "success_rate"

    def trigger_config_display(self, obj):
        if obj.trigger_config:
            formatted_json = json.dumps(obj.trigger_config, indent=2)
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; max-height: 200px; overflow-y: auto;">{}</pre>',
                formatted_json,
            )
        return "No trigger configuration"

    trigger_config_display.short_description = "Trigger Configuration"

    def workflow_steps_display(self, obj):
        if obj.workflow_steps:
            formatted_json = json.dumps(obj.workflow_steps, indent=2)
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; max-height: 300px; overflow-y: auto;">{}</pre>',
                formatted_json,
            )
        return "No workflow steps defined"

    workflow_steps_display.short_description = "Workflow Steps"

    def visual_config_display(self, obj):
        if obj.visual_config:
            formatted_json = json.dumps(obj.visual_config, indent=2)
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; max-height: 200px; overflow-y: auto;">{}</pre>',
                formatted_json,
            )
        return "No visual configuration"

    visual_config_display.short_description = "Visual Configuration"

    def workflow_actions(self, obj):
        actions = []

        # Execute workflow
        execute_url = f"/admin/admin_config/workflowconfiguration/{obj.id}/execute/"
        actions.append(
            f'<a href="{execute_url}" class="button" style="background: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">Execute</a>'
        )

        # Toggle active status
        if obj.is_active:
            toggle_url = (
                f"/admin/admin_config/workflowconfiguration/{obj.id}/deactivate/"
            )
            actions.append(
                f'<a href="{toggle_url}" class="button" style="background: #ffc107; color: black; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">Deactivate</a>'
            )
        else:
            toggle_url = f"/admin/admin_config/workflowconfiguration/{obj.id}/activate/"
            actions.append(
                f'<a href="{toggle_url}" class="button" style="background: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">Activate</a>'
            )

        # View execution history
        history_url = f"/admin/admin_config/workflowconfiguration/{obj.id}/history/"
        actions.append(
            f'<a href="{history_url}" class="button" style="background: #17a2b8; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">History</a>'
        )

        return format_html("".join(actions))

    workflow_actions.short_description = "Actions"
    workflow_actions.allow_tags = True

    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ConfigurationBackup)
class ConfigurationBackupAdmin(BaseAdminConfig, admin.ModelAdmin):
    list_display = [
        "name",
        "backup_type_badge",
        "file_size_display",
        "restored_count",
        "created_by",
        "created_at",
        "backup_actions",
    ]
    list_filter = ["backup_type", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = [
        "id",
        "created_at",
        "file_size",
        "restored_count",
        "last_restored",
        "configurations_summary",
        "workflows_summary",
        "templates_summary",
    ]

    fieldsets = (
        ("Basic Information", {"fields": ("name", "description", "backup_type")}),
        (
            "Backup Contents Summary",
            {
                "fields": (
                    "configurations_summary",
                    "workflows_summary",
                    "templates_summary",
                ),
            },
        ),
        (
            "Statistics",
            {
                "fields": ("file_size", "restored_count", "last_restored"),
                "classes": ("collapse",),
            },
        ),
        (
            "Raw Backup Data (Advanced)",
            {
                "fields": ("configurations", "workflows", "templates"),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {"fields": ("id", "created_by", "created_at"), "classes": ("collapse",)},
        ),
    )

    def backup_type_badge(self, obj):
        colors = {
            "manual": "#6c757d",
            "automatic": "#28a745",
            "pre_change": "#ffc107",
            "scheduled": "#17a2b8",
        }
        color = colors.get(obj.backup_type, "#6c757d")
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            obj.get_backup_type_display(),
        )

    backup_type_badge.short_description = "Type"
    backup_type_badge.admin_order_field = "backup_type"

    def file_size_display(self, obj):
        if obj.file_size:
            if obj.file_size < 1024:
                return f"{obj.file_size} B"
            elif obj.file_size < 1024 * 1024:
                return f"{obj.file_size / 1024:.1f} KB"
            else:
                return f"{obj.file_size / (1024 * 1024):.1f} MB"
        return "Unknown"

    file_size_display.short_description = "Size"
    file_size_display.admin_order_field = "file_size"

    def configurations_summary(self, obj):
        count = len(obj.configurations) if obj.configurations else 0
        return format_html("<strong>{}</strong> configurations backed up", count)

    configurations_summary.short_description = "Configurations"

    def workflows_summary(self, obj):
        count = len(obj.workflows) if obj.workflows else 0
        return format_html("<strong>{}</strong> workflows backed up", count)

    workflows_summary.short_description = "Workflows"

    def templates_summary(self, obj):
        count = len(obj.templates) if obj.templates else 0
        return format_html("<strong>{}</strong> templates backed up", count)

    templates_summary.short_description = "Templates"

    def backup_actions(self, obj):
        actions = []

        # Restore backup
        restore_url = f"/admin/admin_config/configurationbackup/{obj.id}/restore/"
        actions.append(
            f'<a href="{restore_url}" class="button" style="background: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;" onclick="return confirm(\'Are you sure you want to restore this backup? This will overwrite current configurations.\')">Restore</a>'
        )

        # Download backup
        download_url = f"/admin/admin_config/configurationbackup/{obj.id}/download/"
        actions.append(
            f'<a href="{download_url}" class="button" style="background: #17a2b8; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">Download</a>'
        )

        # View contents
        view_url = f"/admin/admin_config/configurationbackup/{obj.id}/view/"
        actions.append(
            f'<a href="{view_url}" class="button" style="background: #6c757d; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">View Contents</a>'
        )

        return format_html("".join(actions))

    backup_actions.short_description = "Actions"
    backup_actions.allow_tags = True

    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ConfigurationAuditLog)
class ConfigurationAuditLogAdmin(admin.ModelAdmin):
    list_display = [
        "timestamp",
        "user",
        "action_badge",
        "content_type",
        "object_id",
        "success_badge",
        "ip_address",
    ]
    list_filter = ["action", "success", "timestamp", "content_type"]
    search_fields = ["user__username", "object_id", "ip_address"]
    readonly_fields = [
        "id",
        "user",
        "action",
        "content_type",
        "object_id",
        "changes_display",
        "old_values_display",
        "new_values_display",
        "ip_address",
        "user_agent",
        "session_key",
        "timestamp",
        "success",
        "error_message",
    ]

    fieldsets = (
        (
            "Action Information",
            {"fields": ("timestamp", "user", "action", "success", "error_message")},
        ),
        ("Target Object", {"fields": ("content_type", "object_id")}),
        (
            "Changes",
            {
                "fields": (
                    "changes_display",
                    "old_values_display",
                    "new_values_display",
                ),
            },
        ),
        (
            "Session Information",
            {
                "fields": ("ip_address", "user_agent", "session_key"),
                "classes": ("collapse",),
            },
        ),
        (
            "Raw Data (Advanced)",
            {
                "fields": ("changes", "old_values", "new_values"),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request):
        return False  # Audit logs should not be manually created

    def has_change_permission(self, request, obj=None):
        return False  # Audit logs should not be modified

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can delete audit logs

    def action_badge(self, obj):
        colors = {
            "create": "#28a745",
            "update": "#17a2b8",
            "delete": "#dc3545",
            "test": "#ffc107",
            "backup": "#6c757d",
            "restore": "#fd7e14",
            "export": "#20c997",
            "import": "#6f42c1",
            "activate": "#28a745",
            "deactivate": "#ffc107",
        }
        color = colors.get(obj.action, "#6c757d")
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            obj.get_action_display(),
        )

    action_badge.short_description = "Action"
    action_badge.admin_order_field = "action"

    def success_badge(self, obj):
        color = "#28a745" if obj.success else "#dc3545"
        text = "Success" if obj.success else "Failed"
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            text,
        )

    success_badge.short_description = "Result"
    success_badge.admin_order_field = "success"

    def changes_display(self, obj):
        if obj.changes:
            formatted_json = json.dumps(obj.changes, indent=2)
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; max-height: 200px; overflow-y: auto;">{}</pre>',
                formatted_json,
            )
        return "No changes recorded"

    changes_display.short_description = "Changes"

    def old_values_display(self, obj):
        if obj.old_values:
            formatted_json = json.dumps(obj.old_values, indent=2)
            return format_html(
                '<pre style="background: #f8d7da; padding: 10px; border-radius: 4px; max-height: 200px; overflow-y: auto;">{}</pre>',
                formatted_json,
            )
        return "No old values"

    old_values_display.short_description = "Old Values"

    def new_values_display(self, obj):
        if obj.new_values:
            formatted_json = json.dumps(obj.new_values, indent=2)
            return format_html(
                '<pre style="background: #d4edda; padding: 10px; border-radius: 4px; max-height: 200px; overflow-y: auto;">{}</pre>',
                formatted_json,
            )
        return "No new values"

    new_values_display.short_description = "New Values"


@admin.register(ConfigurationTest)
class ConfigurationTestAdmin(admin.ModelAdmin):
    list_display = [
        "started_at",
        "configuration",
        "test_type_badge",
        "status_badge",
        "duration_display",
        "success_badge",
        "triggered_by",
    ]
    list_filter = ["test_type", "status", "success", "started_at"]
    search_fields = ["configuration__name", "triggered_by__username"]
    readonly_fields = [
        "id",
        "configuration",
        "test_type",
        "status",
        "test_data_display",
        "expected_result_display",
        "actual_result_display",
        "started_at",
        "completed_at",
        "duration_ms",
        "success",
        "error_message",
        "response_data_display",
        "triggered_by",
    ]

    fieldsets = (
        (
            "Test Information",
            {"fields": ("configuration", "test_type", "status", "triggered_by")},
        ),
        (
            "Test Data",
            {
                "fields": ("test_data_display", "expected_result_display"),
            },
        ),
        (
            "Results",
            {
                "fields": (
                    "success",
                    "actual_result_display",
                    "response_data_display",
                    "error_message",
                ),
            },
        ),
        (
            "Timing",
            {
                "fields": ("started_at", "completed_at", "duration_ms"),
                "classes": ("collapse",),
            },
        ),
        (
            "Raw Data (Advanced)",
            {
                "fields": (
                    "test_data",
                    "expected_result",
                    "actual_result",
                    "response_data",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request):
        return False  # Tests should be triggered through integrations

    def has_change_permission(self, request, obj=None):
        return False  # Test results should not be modified

    def test_type_badge(self, obj):
        colors = {
            "connection": "#17a2b8",
            "authentication": "#ffc107",
            "api_call": "#28a745",
            "workflow": "#6f42c1",
            "integration": "#fd7e14",
        }
        color = colors.get(obj.test_type, "#6c757d")
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            obj.get_test_type_display(),
        )

    test_type_badge.short_description = "Test Type"
    test_type_badge.admin_order_field = "test_type"

    def status_badge(self, obj):
        colors = {
            "pending": "#6c757d",
            "running": "#17a2b8",
            "passed": "#28a745",
            "failed": "#dc3545",
            "timeout": "#ffc107",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"
    status_badge.admin_order_field = "status"

    def success_badge(self, obj):
        if obj.status in ["pending", "running"]:
            return format_html('<span style="color: #6c757d;">-</span>')
        color = "#28a745" if obj.success else "#dc3545"
        text = "Pass" if obj.success else "Fail"
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            text,
        )

    success_badge.short_description = "Result"
    success_badge.admin_order_field = "success"

    def duration_display(self, obj):
        if obj.duration_ms is not None:
            if obj.duration_ms < 1000:
                return f"{obj.duration_ms}ms"
            else:
                return f"{obj.duration_ms / 1000:.2f}s"
        return "N/A"

    duration_display.short_description = "Duration"
    duration_display.admin_order_field = "duration_ms"

    def test_data_display(self, obj):
        if obj.test_data:
            formatted_json = json.dumps(obj.test_data, indent=2)
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; max-height: 200px; overflow-y: auto;">{}</pre>',
                formatted_json,
            )
        return "No test data"

    test_data_display.short_description = "Test Data"

    def expected_result_display(self, obj):
        if obj.expected_result:
            formatted_json = json.dumps(obj.expected_result, indent=2)
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; max-height: 200px; overflow-y: auto;">{}</pre>',
                formatted_json,
            )
        return "No expected result"

    expected_result_display.short_description = "Expected Result"

    def actual_result_display(self, obj):
        if obj.actual_result:
            formatted_json = json.dumps(obj.actual_result, indent=2)
            color = "#d4edda" if obj.success else "#f8d7da"
            return format_html(
                '<pre style="background: {}; padding: 10px; border-radius: 4px; max-height: 200px; overflow-y: auto;">{}</pre>',
                color,
                formatted_json,
            )
        return "No actual result"

    actual_result_display.short_description = "Actual Result"

    def response_data_display(self, obj):
        if obj.response_data:
            formatted_json = json.dumps(obj.response_data, indent=2)
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; max-height: 200px; overflow-y: auto;">{}</pre>',
                formatted_json,
            )
        return "No response data"

    response_data_display.short_description = "Response Data"


# Customize admin site
admin.site.site_header = "NIA Admin Configuration"
admin.site.site_title = "NIA Admin"
admin.site.index_title = "Welcome to NIA Administration"
