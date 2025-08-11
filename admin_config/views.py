import json
import logging
import uuid

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    ConfigurationAuditLog,
    ConfigurationBackup,
    ConfigurationTemplate,
    ConfigurationTest,
    IntegrationConfiguration,
    RolePermission,
    WorkflowConfiguration,
)
from .serializers import (
    ConfigurationAuditLogSerializer,
    ConfigurationBackupSerializer,
    ConfigurationTemplateSerializer,
    ConfigurationTestSerializer,
    ConfigurationValidationSerializer,
    DynamicFormSerializer,
    IntegrationConfigurationSerializer,
    RolePermissionSerializer,
    WorkflowConfigurationSerializer,
)
from .services_minimal import (
    AuditService,
    ConfigurationBackupService,
    ConfigurationTestService,
    PermissionService,
)

logger = logging.getLogger(__name__)


class ConfigurationTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for configuration templates"""

    queryset = ConfigurationTemplate.objects.all()
    serializer_class = ConfigurationTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get("category")
        is_official = self.request.query_params.get("is_official")

        if category:
            queryset = queryset.filter(category=category)
        if is_official is not None:
            queryset = queryset.filter(is_official=is_official.lower() == "true")

        return queryset.filter(is_active=True)

    @action(detail=True, methods=["post"])
    def use_template(self, request, pk=None):
        """Use a template to create a new configuration"""
        template = self.get_object()

        # Increment usage count
        template.usage_count += 1
        template.save()

        # Create new configuration from template
        config_data = {
            "name": request.data.get("name", f"{template.name} Configuration"),
            "description": request.data.get("description", template.description),
            "integration_type": request.data.get("integration_type"),
            "configuration": template.default_configuration,
            "template": template.id,
        }

        serializer = IntegrationConfigurationSerializer(
            data=config_data, context={"request": request}
        )
        if serializer.is_valid():
            config = serializer.save()
            AuditService.log_action(
                request.user, "create", config, {"template_used": template.name}
            )
            return Response(
                IntegrationConfigurationSerializer(config).data,
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def categories(self, request):
        """Get available template categories"""
        categories = [
            {"value": choice[0], "label": choice[1]}
            for choice in ConfigurationTemplate.TEMPLATE_CATEGORIES
        ]
        return Response(categories)


class IntegrationConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for integration configurations"""

    queryset = IntegrationConfiguration.objects.all()
    serializer_class = IntegrationConfigurationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        integration_type = self.request.query_params.get("integration_type")
        status_filter = self.request.query_params.get("status")

        if integration_type:
            queryset = queryset.filter(integration_type=integration_type)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by user's permissions
        if not PermissionService.has_permission(
            self.request.user, "view", "integration"
        ):
            queryset = queryset.filter(created_by=self.request.user)

        return queryset

    def perform_create(self, serializer):
        config = serializer.save()
        AuditService.log_action(
            self.request.user, "create", config, serializer.validated_data
        )

    def perform_update(self, serializer):
        old_values = {
            field: getattr(serializer.instance, field)
            for field in serializer.validated_data.keys()
        }
        config = serializer.save()
        AuditService.log_action(
            self.request.user, "update", config, serializer.validated_data, old_values
        )

    def perform_destroy(self, instance):
        AuditService.log_action(self.request.user, "delete", instance, {})
        super().perform_destroy(instance)

    @action(detail=True, methods=["post"])
    def test_configuration(self, request, pk=None):
        """Test a configuration"""
        config = self.get_object()
        test_type = request.data.get("test_type", "connection")

        # Check permissions
        if not PermissionService.has_permission(
            request.user, "test", "integration", config
        ):
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        # Create test record
        test = ConfigurationTest.objects.create(
            configuration=config,
            test_type=test_type,
            test_data=request.data.get("test_data", {}),
            expected_result=request.data.get("expected_result", {}),
            triggered_by=request.user,
        )

        # Run test asynchronously
        try:
            result = ConfigurationTestService.run_test(test)
            AuditService.log_action(
                request.user, "test", config, {"test_type": test_type}
            )
            return Response(ConfigurationTestSerializer(result).data)
        except Exception as e:
            logger.error(f"Configuration test failed: {str(e)}")
            test.status = "failed"
            test.error_message = str(e)
            test.save()
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """Activate a configuration"""
        config = self.get_object()
        config.status = "active"
        config.save()
        AuditService.log_action(request.user, "activate", config, {})
        return Response({"status": "activated"})

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        """Deactivate a configuration"""
        config = self.get_object()
        config.status = "inactive"
        config.save()
        AuditService.log_action(request.user, "deactivate", config, {})
        return Response({"status": "deactivated"})

    @action(detail=False, methods=["get"])
    def integration_types(self, request):
        """Get available integration types"""
        types = [
            {"value": choice[0], "label": choice[1]}
            for choice in IntegrationConfiguration.INTEGRATION_TYPES
        ]
        return Response(types)


class WorkflowConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for workflow configurations"""

    queryset = WorkflowConfiguration.objects.all()
    serializer_class = WorkflowConfigurationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by user's permissions
        if not PermissionService.has_permission(self.request.user, "view", "workflow"):
            queryset = queryset.filter(created_by=self.request.user)

        return queryset

    def perform_create(self, serializer):
        workflow = serializer.save()
        AuditService.log_action(
            self.request.user, "create", workflow, serializer.validated_data
        )

    def perform_update(self, serializer):
        old_values = {
            field: getattr(serializer.instance, field)
            for field in serializer.validated_data.keys()
        }
        workflow = serializer.save()
        AuditService.log_action(
            self.request.user, "update", workflow, serializer.validated_data, old_values
        )

    @action(detail=True, methods=["post"])
    def execute(self, request, pk=None):
        """Execute a workflow manually"""
        workflow = self.get_object()

        if not workflow.is_active:
            return Response(
                {"error": "Workflow is not active"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Execute workflow (implement workflow execution logic)
        try:
            # This would integrate with a workflow engine
            result = {"status": "executed", "execution_id": str(uuid.uuid4())}
            workflow.execution_count += 1
            workflow.last_execution = timezone.now()
            workflow.save()

            AuditService.log_action(
                request.user, "execute", workflow, {"manual_execution": True}
            )
            return Response(result)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConfigurationBackupViewSet(viewsets.ModelViewSet):
    """ViewSet for configuration backups"""

    queryset = ConfigurationBackup.objects.all()
    serializer_class = ConfigurationBackupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by user's permissions
        if not PermissionService.has_permission(self.request.user, "view", "backup"):
            queryset = queryset.filter(created_by=self.request.user)

        return queryset

    @action(detail=False, methods=["post"])
    def create_backup(self, request):
        """Create a new backup"""
        backup_type = request.data.get("backup_type", "manual")
        name = request.data.get(
            "name", f"Backup {timezone.now().strftime('%Y-%m-%d %H:%M')}"
        )
        description = request.data.get("description", "")

        try:
            backup = ConfigurationBackupService.create_backup(
                user=request.user,
                name=name,
                description=description,
                backup_type=backup_type,
            )
            AuditService.log_action(
                request.user, "backup", backup, {"backup_type": backup_type}
            )
            return Response(
                ConfigurationBackupSerializer(backup).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        """Restore from backup"""
        backup = self.get_object()

        if not PermissionService.has_permission(
            request.user, "restore", "backup", backup
        ):
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        try:
            result = ConfigurationBackupService.restore_backup(backup, request.user)
            backup.restored_count += 1
            backup.last_restored = timezone.now()
            backup.save()

            AuditService.log_action(request.user, "restore", backup, result)
            return Response(result)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        """Download backup file"""
        backup = self.get_object()

        # Generate backup file content
        backup_data = {
            "metadata": {
                "name": backup.name,
                "created_at": backup.created_at.isoformat(),
                "created_by": backup.created_by.username,
                "version": "1.0",
            },
            "configurations": backup.configurations,
            "workflows": backup.workflows,
            "templates": backup.templates,
        }

        response = HttpResponse(
            json.dumps(backup_data, indent=2), content_type="application/json"
        )
        response["Content-Disposition"] = f'attachment; filename="{backup.name}.json"'
        return response


class RolePermissionViewSet(viewsets.ModelViewSet):
    """ViewSet for role permissions"""

    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.query_params.get("user")
        resource_type = self.request.query_params.get("resource_type")

        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)

        return queryset.filter(is_active=True)


class ConfigurationAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for audit logs (read-only)"""

    queryset = ConfigurationAuditLog.objects.all()
    serializer_class = ConfigurationAuditLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.query_params.get("user")
        action = self.request.query_params.get("action")
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")

        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if action:
            queryset = queryset.filter(action=action)
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)

        return queryset


class DynamicFormAPIView(APIView):
    """API for dynamic form generation"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Generate dynamic form based on schema"""
        serializer = DynamicFormSerializer(data=request.data)
        if serializer.is_valid():
            schema = serializer.validated_data["schema"]
            ui_schema = serializer.validated_data.get("ui_schema", {})

            # Generate form configuration
            form_config = self._generate_form_config(schema, ui_schema)
            return Response(form_config)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _generate_form_config(self, schema, ui_schema):
        """Generate form configuration from JSON schema"""
        form_fields = []

        for field_name, field_schema in schema.get("properties", {}).items():
            field_config = {
                "name": field_name,
                "type": field_schema.get("type", "string"),
                "label": field_schema.get(
                    "title", field_name.replace("_", " ").title()
                ),
                "description": field_schema.get("description", ""),
                "required": field_name in schema.get("required", []),
                "default": field_schema.get("default"),
            }

            # Add UI schema overrides
            if field_name in ui_schema:
                field_config.update(ui_schema[field_name])

            # Handle specific field types
            if field_schema.get("type") == "string":
                if "enum" in field_schema:
                    field_config["type"] = "select"
                    field_config["options"] = [
                        {"value": val, "label": val} for val in field_schema["enum"]
                    ]
                elif field_schema.get("format") == "password":
                    field_config["type"] = "password"
                elif field_schema.get("format") == "uri":
                    field_config["type"] = "url"

            form_fields.append(field_config)

        return {"fields": form_fields, "schema": schema, "ui_schema": ui_schema}


class ConfigurationValidationAPIView(APIView):
    """API for configuration validation"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Validate configuration data"""
        serializer = ConfigurationValidationSerializer(data=request.data)
        if serializer.is_valid():
            config_type = serializer.validated_data["configuration_type"]
            config_data = serializer.validated_data["configuration_data"]
            credentials = serializer.validated_data.get("credentials", {})

            # Perform validation
            validation_result = self._validate_configuration(
                config_type, config_data, credentials
            )
            return Response(validation_result)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _validate_configuration(self, config_type, config_data, credentials):
        """Validate configuration based on type"""
        errors = []
        warnings = []

        # Type-specific validation
        if config_type.startswith("crm_"):
            errors.extend(self._validate_crm_config(config_data, credentials))
        elif config_type.startswith("meeting_"):
            errors.extend(self._validate_meeting_config(config_data, credentials))
        elif config_type.startswith("ai_"):
            errors.extend(self._validate_ai_config(config_data, credentials))

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "suggestions": self._get_suggestions(config_type, config_data),
        }

    def _validate_crm_config(self, config_data, credentials):
        """Validate CRM configuration"""
        errors = []

        required_fields = ["api_url", "api_version"]
        for field in required_fields:
            if not config_data.get(field):
                errors.append(f"Missing required field: {field}")

        # Validate API URL format
        api_url = config_data.get("api_url", "")
        if api_url and not api_url.startswith(("http://", "https://")):
            errors.append("API URL must start with http:// or https://")

        return errors

    def _validate_meeting_config(self, config_data, credentials):
        """Validate meeting platform configuration"""
        errors = []

        required_fields = ["client_id", "redirect_uri"]
        for field in required_fields:
            if not config_data.get(field):
                errors.append(f"Missing required field: {field}")

        return errors

    def _validate_ai_config(self, config_data, credentials):
        """Validate AI service configuration"""
        errors = []

        if not credentials.get("api_key"):
            errors.append("API key is required for AI service")

        return errors

    def _get_suggestions(self, config_type, config_data):
        """Get configuration suggestions"""
        suggestions = []

        if config_type.startswith("crm_"):
            if not config_data.get("timeout"):
                suggestions.append("Consider setting a timeout value for API calls")
            if not config_data.get("retry_attempts"):
                suggestions.append(
                    "Consider setting retry attempts for failed API calls"
                )

        return suggestions


@method_decorator(login_required, name="dispatch")
class AdminDashboardView(APIView):
    """Main admin dashboard view"""

    def get(self, request):
        """Get dashboard data"""
        # Get summary statistics
        stats = {
            "total_integrations": IntegrationConfiguration.objects.count(),
            "active_integrations": IntegrationConfiguration.objects.filter(
                status="active"
            ).count(),
            "total_workflows": WorkflowConfiguration.objects.count(),
            "active_workflows": WorkflowConfiguration.objects.filter(
                is_active=True
            ).count(),
            "total_templates": ConfigurationTemplate.objects.filter(
                is_active=True
            ).count(),
            "recent_tests": ConfigurationTest.objects.count(),
        }

        # Get recent activity
        recent_logs = ConfigurationAuditLog.objects.select_related("user").order_by(
            "-timestamp"
        )[:10]
        recent_activity = ConfigurationAuditLogSerializer(recent_logs, many=True).data

        # Get health status
        health_status = self._get_health_status()

        return Response(
            {
                "stats": stats,
                "recent_activity": recent_activity,
                "health_status": health_status,
                "user_permissions": self._get_user_permissions(request.user),
            }
        )

    def _get_health_status(self):
        """Get system health status"""
        total_configs = IntegrationConfiguration.objects.count()
        healthy_configs = IntegrationConfiguration.objects.filter(
            health_status="healthy"
        ).count()

        if total_configs == 0:
            health_percentage = 100
        else:
            health_percentage = (healthy_configs / total_configs) * 100

        return {
            "overall_health": health_percentage,
            "total_configurations": total_configs,
            "healthy_configurations": healthy_configs,
            "unhealthy_configurations": total_configs - healthy_configs,
        }

    def _get_user_permissions(self, user):
        """Get user's permissions"""
        permissions = {}
        resource_types = ["integration", "workflow", "template", "backup", "audit"]
        permission_types = [
            "view",
            "create",
            "edit",
            "delete",
            "test",
            "backup",
            "restore",
        ]

        for resource in resource_types:
            permissions[resource] = {}
            for permission in permission_types:
                permissions[resource][permission] = PermissionService.has_permission(
                    user, permission, resource
                )

        return permissions


# Template Views for Frontend


@method_decorator(login_required, name="dispatch")
class AdminDashboardTemplateView(TemplateView):
    """Main admin dashboard template view"""

    template_name = "admin_config/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Admin Dashboard"
        context["active_section"] = "dashboard"
        return context


@method_decorator(login_required, name="dispatch")
class IntegrationsTemplateView(TemplateView):
    """Integrations management template view"""

    template_name = "admin_config/integrations.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Integration Management"
        context["active_section"] = "integrations"
        return context


@method_decorator(login_required, name="dispatch")
class WorkflowsTemplateView(TemplateView):
    """Workflows management template view"""

    template_name = "admin_config/workflows.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Workflow Management"
        context["active_section"] = "workflows"
        return context


@method_decorator(login_required, name="dispatch")
class TemplatesTemplateView(TemplateView):
    """Templates management template view"""

    template_name = "admin_config/templates.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Configuration Templates"
        context["active_section"] = "templates"
        return context


@method_decorator(login_required, name="dispatch")
class BackupsTemplateView(TemplateView):
    """Backups management template view"""

    template_name = "admin_config/backups.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Configuration Backups"
        context["active_section"] = "backups"
        return context


@method_decorator(login_required, name="dispatch")
class PermissionsTemplateView(TemplateView):
    """Permissions management template view"""

    template_name = "admin_config/permissions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Role & Permissions"
        context["active_section"] = "permissions"
        return context


@method_decorator(login_required, name="dispatch")
class AuditTemplateView(TemplateView):
    """Audit logs template view"""

    template_name = "admin_config/audit.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Audit Logs"
        context["active_section"] = "audit"
        return context
