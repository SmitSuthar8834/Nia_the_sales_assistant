from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid
import json

User = get_user_model()


class ConfigurationTemplate(models.Model):
    """Pre-built configuration templates for common organizational setups"""
    
    TEMPLATE_CATEGORIES = [
        ('crm', 'CRM Integration'),
        ('meeting', 'Meeting Platform'),
        ('workflow', 'Workflow Automation'),
        ('notification', 'Notification System'),
        ('security', 'Security Configuration'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=TEMPLATE_CATEGORIES)
    version = models.CharField(max_length=20, default='1.0.0')
    is_official = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Template configuration data
    configuration_schema = models.JSONField(help_text="JSON schema for configuration validation")
    default_configuration = models.JSONField(help_text="Default configuration values")
    ui_schema = models.JSONField(help_text="UI schema for form generation")
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['name', 'version']
    
    def __str__(self):
        return f"{self.name} v{self.version}"


class IntegrationConfiguration(models.Model):
    """Main configuration model for all integrations"""
    
    INTEGRATION_TYPES = [
        ('crm_salesforce', 'Salesforce CRM'),
        ('crm_hubspot', 'HubSpot CRM'),
        ('crm_pipedrive', 'Pipedrive CRM'),
        ('crm_creatio', 'Creatio CRM'),
        ('crm_sap_c4c', 'SAP C4C'),
        ('meeting_google', 'Google Meet'),
        ('meeting_teams', 'Microsoft Teams'),
        ('meeting_zoom', 'Zoom'),
        ('notification_email', 'Email Notifications'),
        ('notification_slack', 'Slack Notifications'),
        ('ai_gemini', 'Google Gemini AI'),
        ('ai_openai', 'OpenAI'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
        ('testing', 'Testing'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    integration_type = models.CharField(max_length=50, choices=INTEGRATION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Configuration data
    configuration = models.JSONField(help_text="Integration configuration data")
    credentials = models.JSONField(help_text="Encrypted credentials", default=dict)
    
    # Template reference
    template = models.ForeignKey(ConfigurationTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Ownership and permissions
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_integrations')
    organization = models.CharField(max_length=255, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_tested = models.DateTimeField(null=True, blank=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    
    # Health monitoring
    health_status = models.CharField(max_length=20, default='unknown')
    health_details = models.JSONField(default=dict)
    error_count = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-updated_at']
        unique_together = ['name', 'created_by']
    
    def __str__(self):
        return f"{self.name} ({self.get_integration_type_display()})"


class WorkflowConfiguration(models.Model):
    """Visual workflow builder configurations"""
    
    TRIGGER_TYPES = [
        ('manual', 'Manual Trigger'),
        ('schedule', 'Scheduled'),
        ('event', 'Event-based'),
        ('webhook', 'Webhook'),
        ('api_call', 'API Call'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    # Workflow definition
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES)
    trigger_config = models.JSONField(help_text="Trigger configuration")
    workflow_steps = models.JSONField(help_text="Workflow steps definition")
    
    # Visual editor data
    visual_config = models.JSONField(help_text="Visual editor configuration", default=dict)
    
    # Dependencies
    required_integrations = models.ManyToManyField(IntegrationConfiguration, blank=True)
    
    # Ownership
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Execution tracking
    execution_count = models.PositiveIntegerField(default=0)
    last_execution = models.DateTimeField(null=True, blank=True)
    success_rate = models.FloatField(default=0.0)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.name


class ConfigurationBackup(models.Model):
    """Configuration backup and version control"""
    
    BACKUP_TYPES = [
        ('manual', 'Manual Backup'),
        ('automatic', 'Automatic Backup'),
        ('pre_change', 'Pre-change Backup'),
        ('scheduled', 'Scheduled Backup'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    backup_type = models.CharField(max_length=20, choices=BACKUP_TYPES)
    
    # Backup data
    configurations = models.JSONField(help_text="Backed up configurations")
    workflows = models.JSONField(help_text="Backed up workflows")
    templates = models.JSONField(help_text="Backed up templates")
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    file_size = models.PositiveIntegerField(default=0)
    
    # Restore tracking
    restored_count = models.PositiveIntegerField(default=0)
    last_restored = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class RolePermission(models.Model):
    """Role-based access control for configurations"""
    
    PERMISSION_TYPES = [
        ('view', 'View'),
        ('create', 'Create'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
        ('test', 'Test'),
        ('backup', 'Backup'),
        ('restore', 'Restore'),
        ('export', 'Export'),
        ('import', 'Import'),
    ]
    
    RESOURCE_TYPES = [
        ('integration', 'Integration Configuration'),
        ('workflow', 'Workflow Configuration'),
        ('template', 'Configuration Template'),
        ('backup', 'Configuration Backup'),
        ('audit', 'Audit Logs'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='config_permissions')
    permission_type = models.CharField(max_length=20, choices=PERMISSION_TYPES)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    
    # Optional specific resource
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.UUIDField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Conditions
    conditions = models.JSONField(default=dict, help_text="Additional permission conditions")
    
    # Metadata
    granted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='granted_permissions')
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'permission_type', 'resource_type', 'object_id']
    
    def __str__(self):
        return f"{self.user.username} - {self.permission_type} {self.resource_type}"


class ConfigurationAuditLog(models.Model):
    """Audit logging for all configuration changes"""
    
    ACTION_TYPES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('test', 'Tested'),
        ('backup', 'Backed up'),
        ('restore', 'Restored'),
        ('export', 'Exported'),
        ('import', 'Imported'),
        ('activate', 'Activated'),
        ('deactivate', 'Deactivated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    
    # Target object
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Change details
    changes = models.JSONField(help_text="Details of changes made")
    old_values = models.JSONField(default=dict, help_text="Previous values")
    new_values = models.JSONField(default=dict, help_text="New values")
    
    # Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} {self.action} {self.content_object} at {self.timestamp}"


class ConfigurationTest(models.Model):
    """Real-time configuration testing results"""
    
    TEST_TYPES = [
        ('connection', 'Connection Test'),
        ('authentication', 'Authentication Test'),
        ('api_call', 'API Call Test'),
        ('workflow', 'Workflow Test'),
        ('integration', 'Integration Test'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('timeout', 'Timeout'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    configuration = models.ForeignKey(IntegrationConfiguration, on_delete=models.CASCADE, related_name='tests')
    test_type = models.CharField(max_length=20, choices=TEST_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Test details
    test_data = models.JSONField(help_text="Test input data")
    expected_result = models.JSONField(help_text="Expected test result")
    actual_result = models.JSONField(help_text="Actual test result")
    
    # Execution details
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    
    # Results
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    response_data = models.JSONField(default=dict)
    
    # Context
    triggered_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.configuration.name} - {self.test_type} ({self.status})"
