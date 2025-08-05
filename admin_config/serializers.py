from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    ConfigurationTemplate, IntegrationConfiguration, WorkflowConfiguration,
    ConfigurationBackup, RolePermission, ConfigurationAuditLog, ConfigurationTest
)

User = get_user_model()


class ConfigurationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for configuration templates"""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = ConfigurationTemplate
        fields = [
            'id', 'name', 'description', 'category', 'version', 'is_official', 'is_active',
            'configuration_schema', 'default_configuration', 'ui_schema',
            'created_by', 'created_by_name', 'created_at', 'updated_at', 'usage_count'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'usage_count']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class IntegrationConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for integration configurations"""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    integration_type_display = serializers.CharField(source='get_integration_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = IntegrationConfiguration
        fields = [
            'id', 'name', 'description', 'integration_type', 'integration_type_display',
            'status', 'status_display', 'configuration', 'credentials', 'template',
            'template_name', 'created_by', 'created_by_name', 'organization',
            'created_at', 'updated_at', 'last_tested', 'last_sync',
            'health_status', 'health_details', 'error_count', 'last_error'
        ]
        read_only_fields = [
            'id', 'created_by', 'created_at', 'updated_at', 'last_tested', 'last_sync',
            'health_status', 'health_details', 'error_count', 'last_error'
        ]
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class WorkflowConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for workflow configurations"""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    required_integrations_names = serializers.StringRelatedField(
        source='required_integrations', many=True, read_only=True
    )
    trigger_type_display = serializers.CharField(source='get_trigger_type_display', read_only=True)
    
    class Meta:
        model = WorkflowConfiguration
        fields = [
            'id', 'name', 'description', 'is_active', 'trigger_type', 'trigger_type_display',
            'trigger_config', 'workflow_steps', 'visual_config', 'required_integrations',
            'required_integrations_names', 'created_by', 'created_by_name',
            'created_at', 'updated_at', 'execution_count', 'last_execution', 'success_rate'
        ]
        read_only_fields = [
            'id', 'created_by', 'created_at', 'updated_at',
            'execution_count', 'last_execution', 'success_rate'
        ]
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ConfigurationBackupSerializer(serializers.ModelSerializer):
    """Serializer for configuration backups"""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    backup_type_display = serializers.CharField(source='get_backup_type_display', read_only=True)
    
    class Meta:
        model = ConfigurationBackup
        fields = [
            'id', 'name', 'description', 'backup_type', 'backup_type_display',
            'configurations', 'workflows', 'templates', 'created_by', 'created_by_name',
            'created_at', 'file_size', 'restored_count', 'last_restored'
        ]
        read_only_fields = [
            'id', 'created_by', 'created_at', 'file_size', 'restored_count', 'last_restored'
        ]
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class RolePermissionSerializer(serializers.ModelSerializer):
    """Serializer for role permissions"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    granted_by_name = serializers.CharField(source='granted_by.get_full_name', read_only=True)
    permission_type_display = serializers.CharField(source='get_permission_type_display', read_only=True)
    resource_type_display = serializers.CharField(source='get_resource_type_display', read_only=True)
    
    class Meta:
        model = RolePermission
        fields = [
            'id', 'user', 'user_name', 'permission_type', 'permission_type_display',
            'resource_type', 'resource_type_display', 'content_type', 'object_id',
            'conditions', 'granted_by', 'granted_by_name', 'granted_at',
            'expires_at', 'is_active'
        ]
        read_only_fields = ['id', 'granted_by', 'granted_at']
    
    def create(self, validated_data):
        validated_data['granted_by'] = self.context['request'].user
        return super().create(validated_data)


class ConfigurationAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for audit logs"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    content_type_name = serializers.CharField(source='content_type.name', read_only=True)
    
    class Meta:
        model = ConfigurationAuditLog
        fields = [
            'id', 'user', 'user_name', 'action', 'action_display',
            'content_type', 'content_type_name', 'object_id', 'changes',
            'old_values', 'new_values', 'ip_address', 'user_agent',
            'session_key', 'timestamp', 'success', 'error_message'
        ]
        read_only_fields = '__all__'


class ConfigurationTestSerializer(serializers.ModelSerializer):
    """Serializer for configuration tests"""
    
    configuration_name = serializers.CharField(source='configuration.name', read_only=True)
    triggered_by_name = serializers.CharField(source='triggered_by.get_full_name', read_only=True)
    test_type_display = serializers.CharField(source='get_test_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ConfigurationTest
        fields = [
            'id', 'configuration', 'configuration_name', 'test_type', 'test_type_display',
            'status', 'status_display', 'test_data', 'expected_result', 'actual_result',
            'started_at', 'completed_at', 'duration_ms', 'success', 'error_message',
            'response_data', 'triggered_by', 'triggered_by_name'
        ]
        read_only_fields = [
            'id', 'started_at', 'completed_at', 'duration_ms',
            'success', 'error_message', 'response_data', 'triggered_by'
        ]
    
    def create(self, validated_data):
        validated_data['triggered_by'] = self.context['request'].user
        return super().create(validated_data)


class DynamicFormSerializer(serializers.Serializer):
    """Serializer for dynamic form generation"""
    
    schema = serializers.JSONField()
    ui_schema = serializers.JSONField(required=False)
    form_data = serializers.JSONField(required=False)
    
    def validate_schema(self, value):
        """Validate JSON schema format"""
        required_fields = ['type', 'properties']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Schema must contain '{field}' field")
        return value


class ConfigurationValidationSerializer(serializers.Serializer):
    """Serializer for configuration validation"""
    
    configuration_type = serializers.ChoiceField(choices=IntegrationConfiguration.INTEGRATION_TYPES)
    configuration_data = serializers.JSONField()
    credentials = serializers.JSONField(required=False)
    
    def validate(self, data):
        """Validate configuration data based on type"""
        config_type = data['configuration_type']
        config_data = data['configuration_data']
        
        # Add type-specific validation logic here
        if config_type.startswith('crm_'):
            required_fields = ['api_url', 'api_version']
            for field in required_fields:
                if field not in config_data:
                    raise serializers.ValidationError(f"CRM configuration must contain '{field}' field")
        
        elif config_type.startswith('meeting_'):
            required_fields = ['client_id', 'redirect_uri']
            for field in required_fields:
                if field not in config_data:
                    raise serializers.ValidationError(f"Meeting configuration must contain '{field}' field")
        
        return data