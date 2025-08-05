from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from admin_config.models import ConfigurationTemplate, IntegrationConfiguration
import json

# This should cause an error if this file is being loaded
print("LOADING SETUP_ADMIN_CONFIG FROM THE CORRECT FILE")

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up initial admin configuration templates and data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset existing templates and create new ones',
        )
        parser.add_argument(
            '--create-samples',
            action='store_true',
            help='Create sample integrations for testing',
        )

    def handle(self, *args, **options):
        self.stdout.write('Setting up admin configuration...')
        self.stdout.write('DEBUG: File timestamp check - this should appear!')
        
        if options['reset']:
            self.stdout.write('Resetting existing templates...')
            ConfigurationTemplate.objects.all().delete()

        # Get or create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Created admin user'))
        
        # Create configuration templates
        self.create_templates(admin_user)
        
        if options['create_samples']:
            self.create_sample_integrations(admin_user)
        
        self.stdout.write(self.style.SUCCESS('Admin configuration setup complete!'))

    def create_templates(self, user):
        """Create default configuration templates"""
        
        # Simple templates list for testing
        templates = [
            {
                'name': 'Test Template 1',
                'description': 'Test template 1',
                'category': 'crm',
                'configuration_schema': {'type': 'object', 'properties': {}},
                'default_configuration': {},
                'ui_schema': {}
            },
            {
                'name': 'Test Template 2',
                'description': 'Test template 2',
                'category': 'meeting',
                'configuration_schema': {'type': 'object', 'properties': {}},
                'default_configuration': {},
                'ui_schema': {}
            },
            {
                'name': 'Test Template 3',
                'description': 'Test template 3',
                'category': 'workflow',
                'configuration_schema': {'type': 'object', 'properties': {}},
                'default_configuration': {},
                'ui_schema': {}
            }
        ]
        
        self.stdout.write(f'Processing {len(templates)} templates...')
        
        for i, template_data in enumerate(templates):
            self.stdout.write(f'Processing template {i+1}: {template_data["name"]}')
            try:
                template, created = ConfigurationTemplate.objects.get_or_create(
                    name=template_data['name'],
                    defaults={
                        **template_data,
                        'created_by': user,
                        'is_official': True
                    }
                )
                
                if created:
                    self.stdout.write(f'Created template: {template.name}')
                else:
                    self.stdout.write(f'Template already exists: {template.name}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating template {template_data["name"]}: {str(e)}'))

    def create_sample_integrations(self, user):
        """Create sample integrations for testing"""
        
        # Get templates
        salesforce_template = ConfigurationTemplate.objects.filter(name='Salesforce CRM Integration').first()
        hubspot_template = ConfigurationTemplate.objects.filter(name='HubSpot CRM Integration').first()
        google_meet_template = ConfigurationTemplate.objects.filter(name='Google Meet Integration').first()
        teams_template = ConfigurationTemplate.objects.filter(name='Microsoft Teams Integration').first()
        gemini_template = ConfigurationTemplate.objects.filter(name='Gemini AI Integration').first()
        
        sample_integrations = [
            {
                'name': 'Production Salesforce',
                'description': 'Main production Salesforce instance',
                'integration_type': 'crm_salesforce',
                'template': salesforce_template,
                'configuration': {
                    'api_url': 'https://production.salesforce.com',
                    'api_version': 'v52.0',
                    'client_id': 'sample_client_id',
                    'client_secret': 'sample_secret',
                    'timeout': 30
                },
                'status': 'draft'
            },
            {
                'name': 'HubSpot Marketing',
                'description': 'HubSpot CRM for marketing automation',
                'integration_type': 'crm_hubspot',
                'template': hubspot_template,
                'configuration': {
                    'api_key': 'sample_hubspot_key',
                    'portal_id': '12345678',
                    'api_url': 'https://api.hubapi.com',
                    'timeout': 30
                },
                'status': 'draft'
            },
            {
                'name': 'Google Meet Meetings',
                'description': 'Google Meet integration for video calls',
                'integration_type': 'meeting_google',
                'template': google_meet_template,
                'configuration': {
                    'client_id': 'sample_google_client_id',
                    'client_secret': 'sample_google_secret',
                    'redirect_uri': 'http://localhost:8000/admin-config/oauth/callback/',
                    'scopes': 'https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/meetings.space.created'
                },
                'status': 'draft'
            },
            {
                'name': 'Microsoft Teams Meetings',
                'description': 'Microsoft Teams integration for meetings',
                'integration_type': 'meeting_teams',
                'template': teams_template,
                'configuration': {
                    'tenant_id': 'sample_tenant_id',
                    'client_id': 'sample_teams_client_id',
                    'client_secret': 'sample_teams_secret',
                    'redirect_uri': 'http://localhost:8000/admin-config/oauth/teams/callback/',
                    'scopes': 'https://graph.microsoft.com/OnlineMeetings.ReadWrite https://graph.microsoft.com/Calendars.ReadWrite'
                },
                'status': 'draft'
            },
            {
                'name': 'NIA AI Assistant',
                'description': 'Main AI service for lead analysis',
                'integration_type': 'ai_gemini',
                'template': gemini_template,
                'configuration': {
                    'api_key': 'sample_api_key',
                    'model': 'gemini-pro',
                    'temperature': 0.7,
                    'max_tokens': 1000
                },
                'status': 'draft'
            }
        ]
        
        for integration_data in sample_integrations:
            integration, created = IntegrationConfiguration.objects.get_or_create(
                name=integration_data['name'],
                created_by=user,
                defaults=integration_data
            )
            
            if created:
                self.stdout.write(f'Created sample integration: {integration.name}')
            else:
                self.stdout.write(f'Sample integration already exists: {integration.name}')