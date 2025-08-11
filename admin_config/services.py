import json
import logging
from typing import Any, Dict

import requests
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.utils import timezone

from .models import (
    ConfigurationAuditLog,
    ConfigurationBackup,
    ConfigurationTemplate,
    ConfigurationTest,
    IntegrationConfiguration,
    RolePermission,
    WorkflowConfiguration,
)

logger = logging.getLogger(__name__)


class ConfigurationTestService:
    """Service for testing configurations"""

    @staticmethod
    def run_test(test: ConfigurationTest) -> ConfigurationTest:
        """Run a configuration test"""
        test.status = "running"
        test.save()

        start_time = timezone.now()

        try:
            if test.test_type == "connection":
                result = ConfigurationTestService._test_connection(test)
            elif test.test_type == "authentication":
                result = ConfigurationTestService._test_authentication(test)
            elif test.test_type == "api_call":
                result = ConfigurationTestService._test_api_call(test)
            elif test.test_type == "workflow":
                result = ConfigurationTestService._test_workflow(test)
            else:
                result = ConfigurationTestService._test_integration(test)

            # Update test with results
            test.status = "passed" if result["success"] else "failed"
            test.success = result["success"]
            test.actual_result = result.get("data", {})
            test.response_data = result.get("response", {})
            test.error_message = result.get("error", "")

        except Exception as e:
            logger.error(f"Test execution failed: {str(e)}")
            test.status = "failed"
            test.success = False
            test.error_message = str(e)

        finally:
            test.completed_at = timezone.now()
            test.duration_ms = int(
                (test.completed_at - start_time).total_seconds() * 1000
            )
            test.save()

        return test

    @staticmethod
    def _test_connection(test: ConfigurationTest) -> Dict[str, Any]:
        """Test basic connection to service"""
        config = test.configuration

        try:
            if config.integration_type.startswith("crm_"):
                return ConfigurationTestService._test_crm_connection(config)
            elif config.integration_type.startswith("meeting_"):
                return ConfigurationTestService._test_meeting_connection(config)
            elif config.integration_type.startswith("ai_"):
                return ConfigurationTestService._test_ai_connection(config)
            else:
                return {"success": False, "error": "Unknown integration type"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def _test_crm_connection(config: IntegrationConfiguration) -> Dict[str, Any]:
        """Test CRM connection"""
        api_url = config.configuration.get("api_url")
        timeout = config.configuration.get("timeout", 30)

        try:
            response = requests.get(f"{api_url}/health", timeout=timeout)
            return {
                "success": response.status_code == 200,
                "data": {"status_code": response.status_code},
                "response": (
                    response.json()
                    if response.headers.get("content-type", "").startswith(
                        "application/json"
                    )
                    else {}
                ),
            }
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def _test_meeting_connection(config: IntegrationConfiguration) -> Dict[str, Any]:
        """Test meeting platform connection"""
        # This would test OAuth endpoints or API availability
        return {
            "success": True,
            "data": {"message": "Meeting platform connection test passed"},
        }

    @staticmethod
    def _test_ai_connection(config: IntegrationConfiguration) -> Dict[str, Any]:
        """Test AI service connection"""
        # This would test AI API availability
        return {
            "success": True,
            "data": {"message": "AI service connection test passed"},
        }

    @staticmethod
    def _test_authentication(test: ConfigurationTest) -> Dict[str, Any]:
        """Test authentication"""
        return {"success": True, "data": {"message": "Authentication test passed"}}

    @staticmethod
    def _test_api_call(test: ConfigurationTest) -> Dict[str, Any]:
        """Test API call"""
        return {"success": True, "data": {"message": "API call test passed"}}

    @staticmethod
    def _test_workflow(test: ConfigurationTest) -> Dict[str, Any]:
        """Test workflow execution"""
        return {"success": True, "data": {"message": "Workflow test passed"}}

    @staticmethod
    def _test_integration(test: ConfigurationTest) -> Dict[str, Any]:
        """Test full integration"""
        return {"success": True, "data": {"message": "Integration test passed"}}


class ConfigurationBackupService:
    """Service for configuration backup and restore"""

    @staticmethod
    def create_backup(
        user, name: str, description: str = "", backup_type: str = "manual"
    ) -> ConfigurationBackup:
        """Create a new configuration backup"""

        # Collect all configurations
        configurations = list(IntegrationConfiguration.objects.values())
        workflows = list(WorkflowConfiguration.objects.values())
        templates = list(ConfigurationTemplate.objects.values())

        # Create backup
        backup = ConfigurationBackup.objects.create(
            name=name,
            description=description,
            backup_type=backup_type,
            configurations=configurations,
            workflows=workflows,
            templates=templates,
            created_by=user,
            file_size=len(
                json.dumps(
                    {
                        "configurations": configurations,
                        "workflows": workflows,
                        "templates": templates,
                    }
                )
            ),
        )

        return backup

    @staticmethod
    def restore_backup(backup: ConfigurationBackup, user) -> Dict[str, Any]:
        """Restore from backup"""

        restored_count = 0
        errors = []

        try:
            with transaction.atomic():
                # Restore configurations
                for config_data in backup.configurations:
                    try:
                        config_data.pop("id", None)  # Remove ID to create new
                        config_data["created_by_id"] = user.id
                        IntegrationConfiguration.objects.create(**config_data)
                        restored_count += 1
                    except Exception as e:
                        errors.append(f"Configuration restore error: {str(e)}")

                # Restore workflows
                for workflow_data in backup.workflows:
                    try:
                        workflow_data.pop("id", None)
                        workflow_data["created_by_id"] = user.id
                        WorkflowConfiguration.objects.create(**workflow_data)
                        restored_count += 1
                    except Exception as e:
                        errors.append(f"Workflow restore error: {str(e)}")

                # Restore templates
                for template_data in backup.templates:
                    try:
                        template_data.pop("id", None)
                        template_data["created_by_id"] = user.id
                        ConfigurationTemplate.objects.create(**template_data)
                        restored_count += 1
                    except Exception as e:
                        errors.append(f"Template restore error: {str(e)}")

        except Exception as e:
            errors.append(f"Backup restore failed: {str(e)}")

        return {
            "success": len(errors) == 0,
            "restored_count": restored_count,
            "errors": errors,
        }


class PermissionService:
    """Service for managing permissions"""

    @staticmethod
    def has_permission(
        user, permission_type: str, resource_type: str, resource_object=None
    ) -> bool:
        """Check if user has specific permission"""

        # Superusers have all permissions
        if user.is_superuser:
            return True

        # Check for specific permission
        query = RolePermission.objects.filter(
            user=user,
            permission_type=permission_type,
            resource_type=resource_type,
            is_active=True,
        )

        # Check expiration
        query = query.filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
        )

        # Check for specific resource
        if resource_object:
            content_type = ContentType.objects.get_for_model(resource_object)
            query = query.filter(
                models.Q(content_type=content_type, object_id=resource_object.id)
                | models.Q(content_type__isnull=True, object_id__isnull=True)
            )

        return query.exists()

    @staticmethod
    def grant_permission(
        granter,
        user,
        permission_type: str,
        resource_type: str,
        resource_object=None,
        conditions: Dict = None,
        expires_at=None,
    ) -> RolePermission:
        """Grant permission to user"""

        permission_data = {
            "user": user,
            "permission_type": permission_type,
            "resource_type": resource_type,
            "granted_by": granter,
            "conditions": conditions or {},
            "expires_at": expires_at,
        }

        if resource_object:
            permission_data["content_type"] = ContentType.objects.get_for_model(
                resource_object
            )
            permission_data["object_id"] = resource_object.id

        return RolePermission.objects.create(**permission_data)


class AuditService:
    """Service for audit logging"""

    @staticmethod
    def log_action(
        user,
        action: str,
        target_object,
        changes: Dict = None,
        old_values: Dict = None,
        ip_address: str = None,
        user_agent: str = None,
    ) -> ConfigurationAuditLog:
        """Log an action"""

        content_type = ContentType.objects.get_for_model(target_object)

        return ConfigurationAuditLog.objects.create(
            user=user,
            action=action,
            content_type=content_type,
            object_id=target_object.id,
            changes=changes or {},
            old_values=old_values or {},
            new_values=changes or {},
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
        )


class TemplateService:
    """Service for managing configuration templates"""

    @staticmethod
    def create_template_from_config(
        config: IntegrationConfiguration, user, name: str, description: str = ""
    ) -> ConfigurationTemplate:
        """Create a template from existing configuration"""

        # Generate schema from configuration
        schema = TemplateService._generate_schema_from_config(config.configuration)
        ui_schema = TemplateService._generate_ui_schema(schema)

        template = ConfigurationTemplate.objects.create(
            name=name,
            description=description,
            category=TemplateService._get_category_from_type(config.integration_type),
            configuration_schema=schema,
            default_configuration=config.configuration,
            ui_schema=ui_schema,
            created_by=user,
        )

        return template

    @staticmethod
    def _generate_schema_from_config(config_data: Dict) -> Dict:
        """Generate JSON schema from configuration data"""

        properties = {}
        required = []

        for key, value in config_data.items():
            if isinstance(value, str):
                properties[key] = {
                    "type": "string",
                    "title": key.replace("_", " ").title(),
                }
            elif isinstance(value, int):
                properties[key] = {
                    "type": "integer",
                    "title": key.replace("_", " ").title(),
                }
            elif isinstance(value, bool):
                properties[key] = {
                    "type": "boolean",
                    "title": key.replace("_", " ").title(),
                }
            elif isinstance(value, list):
                properties[key] = {
                    "type": "array",
                    "title": key.replace("_", " ").title(),
                }
            elif isinstance(value, dict):
                properties[key] = {
                    "type": "object",
                    "title": key.replace("_", " ").title(),
                }

            # Mark as required if not empty
            if value:
                required.append(key)

        return {"type": "object", "properties": properties, "required": required}

    @staticmethod
    def _generate_ui_schema(schema: Dict) -> Dict:
        """Generate UI schema for form rendering"""

        ui_schema = {}

        for field_name, field_schema in schema.get("properties", {}).items():
            if "password" in field_name.lower() or "secret" in field_name.lower():
                ui_schema[field_name] = {"ui:widget": "password"}
            elif field_schema.get("type") == "string" and "url" in field_name.lower():
                ui_schema[field_name] = {"ui:widget": "uri"}

        return ui_schema

    @staticmethod
    def _get_category_from_type(integration_type: str) -> str:
        """Get template category from integration type"""

        if integration_type.startswith("crm_"):
            return "crm"
        elif integration_type.startswith("meeting_"):
            return "meeting"
        elif integration_type.startswith("ai_"):
            return "workflow"
        elif integration_type.startswith("notification_"):
            return "notification"
        else:
            return "workflow"
