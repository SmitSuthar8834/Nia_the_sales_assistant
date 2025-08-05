from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from admin_config.models import ConfigurationTemplate, IntegrationConfiguration
import json

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
        
        templates = [
            {
                'name': 'Salesforce CRM Integration',
                'description': 'Standard Salesforce CRM integration template',
                'category': 'crm',
                'configuration_schema': {
                    'type': 'object',
                    'properties': {
                        'api_url': {
                            'type': 'string',
                            'title': 'Salesforce API URL',
                            'format': 'uri',
                            'description': 'Your Salesforce instance URL'
                        },
                        'api_version': {
                            'type': 'string',
                            'title': 'API Version',
                            'default': 'v52.0',
                            'description': 'Salesforce API version to use'
                        },
                        'client_id': {
                            'type': 'string',
                            'title': 'Client ID',
                            'description': 'OAuth Client ID from Salesforce Connected App'
                        },
                        'client_secret': {
                            'type': 'string',
                            'title': 'Client Secret',
                            'format': 'password',
                            'description': 'OAuth Client Secret from Salesforce Connected App'
                        },
                        'timeout': {
                            'type': 'integer',
                            'title': 'Request Timeout (seconds)',
                            'default': 30,
                            'minimum': 5,
                            'maximum': 300
                        }
                    },
                    'required': ['api_url', 'client_id', 'client_secret']
                },
                'default_configuration': {
                    'api_url': 'https://your-instance.salesforce.com',
                    'api_version': 'v52.0',
                    'timeout': 30
                },
                'ui_schema': {
                    'client_secret': {'ui:widget': 'password'},
                    'api_url': {'ui:widget': 'uri'}
                }
            },
            {
                'name': 'Google Meet Integration',
                'description': 'Google Meet meeting platform integration',
                'category': 'meeting',
                'configuration_schema': {
                    'type': 'object',
                    'properties': {
                        'client_id': {
                            'type': 'string',
                            'title': 'Google Client ID',
                            'description': 'OAuth 2.0 Client ID from Google Cloud Console'
                        },
                        'client_secret': {
                            'type': 'string',
                            'title': 'Client Secret',
                            'format': 'password',
                            'description': 'OAuth 2.0 Client Secret'
                        },
                        'redirect_uri': {
                            'type': 'string',
                            'title': 'Redirect URI',
                            'format': 'uri',
                            'description': 'OAuth redirect URI'
                        },
                        'scopes': {
                            'type': 'string',
                            'title': 'OAuth Scopes',
                            'default': 'https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/meetings.space.created'
                        }
                    },
                    'required': ['client_id', 'client_secret', 'redirect_uri']
                },
                'default_configuration': {
                    'redirect_uri': 'http://localhost:8000/admin-config/oauth/callback/',
                    'scopes': 'https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/meetings.space.created'
                },
                'ui_schema': {
                    'client_secret': {'ui:widget': 'password'},
                    'redirect_uri': {'ui:widget': 'uri'}
                }
            },
            {
                'name': 'Microsoft Teams Integration',
                'description': 'Microsoft Teams meeting platform integration',
                'category': 'meeting',
                'configuration_schema': {
                    'type': 'object',
                    'properties': {
                        'tenant_id': {
                            'type': 'string',
                            'title': 'Azure Tenant ID',
                            'description': 'Azure AD Tenant ID'
                        },
                        'client_id': {
                            'type': 'string',
                            'title': 'Application (Client) ID',
                            'description': 'Azure AD Application ID'
                        },
                        'client_secret': {
                            'type': 'string',
                            'title': 'Client Secret',
                            'format': 'password',
                            'description': 'Azure AD Application Secret'
                        },
                        'redirect_uri': {
                            'type': 'string',
                            'title': 'Redirect URI',
                            'format': 'uri',
                            'description': 'OAuth redirect URI'
                        },
                        'scopes': {
                            'type': 'string',
                            'title': 'OAuth Scopes',
                            'default': 'https://graph.microsoft.com/OnlineMeetings.ReadWrite https://graph.microsoft.com/Calendars.ReadWrite'
                        }
                    },
                    'required': ['tenant_id', 'client_id', 'client_secret', 'redirect_uri']
                },
                'default_configuration': {
                    'redirect_uri': 'http://localhost:8000/admin-config/oauth/teams/callback/',
                    'scopes': 'https://graph.microsoft.com/OnlineMeetings.ReadWrite https://graph.microsoft.com/Calendars.ReadWrite'
                },
                'ui_schema': {
                    'client_secret': {'ui:widget': 'password'},
                    'redirect_uri': {'ui:widget': 'uri'}
                }
            },
            {
                'name': 'HubSpot CRM Integration',
                'description': 'HubSpot CRM integration template',
                'category': 'crm',
                'configuration_schema': {
                    'type': 'object',
                    'properties': {
                        'api_key': {
                            'type': 'string',
                            'title': 'HubSpot API Key',
                            'format': 'password',
                            'description': 'HubSpot Private App API Key'
                        },
                        'portal_id': {
                            'type': 'string',
                            'title': 'Portal ID',
                            'description': 'HubSpot Portal (Hub) ID'
                        },
                        'api_url': {
                            'type': 'string',
                            'title': 'API Base URL',
                            'default': 'https://api.hubapi.com',
                            'format': 'uri'
                        },
                        'timeout': {
                            'type': 'integer',
                            'title': 'Request Timeout (seconds)',
                            'default': 30,
                            'minimum': 5,
                            'maximum': 300
                        }
                    },
                    'required': ['api_key', 'portal_id']
                },
                'default_configuration': {
                    'api_url': 'https://api.hubapi.com',
                    'timeout': 30
                },
                'ui_schema': {
                    'api_key': {'ui:widget': 'password'},
                    'api_url': {'ui:widget': 'uri'}
                }
            },
            {
                'name': 'Pipedrive CRM Integration',
                'description': 'Pipedrive CRM integration template',
                'category': 'crm',
                'configuration_schema': {
                    'type': 'object',
                    'properties': {
                        'api_token': {
                            'type': 'string',
                            'title': 'API Token',
                            'format': 'password',
                            'description': 'Pipedrive API Token'
                        },
                        'company_domain': {
                            'type': 'string',
                            'title': 'Company Domain',
                            'description': 'Your Pipedrive company domain (e.g., yourcompany)'
                        },
                        'api_url': {
                            'type': 'string',
                            'title': 'API Base URL',
                            'format': 'uri',
                            'description': 'Pipedrive API base URL'
                        },
                        'timeout': {
                            'type': 'integer',
                            'title': 'Request Timeout (seconds)',
                            'default': 30,
                            'minimum': 5,
                            'maximum': 300
                        }
                    },
                    'required': ['api_token', 'company_domain']
                },
                'default_configuration': {
                    'timeout': 30
                },
                'ui_schema': {
                    'api_token': {'ui:widget': 'password'},
                    'api_url': {'ui:widget': 'uri'}
                }
            },
            {
                'name': 'Gemini AI Integration',
                'description': 'Google Gemini AI service integration',
                'category': 'workflow',
                'configuration_schema': {
                    'type': 'object',
                    'properties': {
                        'api_key': {
                            'type': 'string',
                            'title': 'Gemini API Key',
                            'format': 'password',
                            'description': 'Google AI Studio API key'
                        },
                        'model': {
                            'type': 'string',
                            'title': 'Model',
                            'enum': ['gemini-pro', 'gemini-pro-vision'],
                            'default': 'gemini-pro'
                        },
                        'temperature': {
                            'type': 'number',
                            'title': 'Temperature',
                            'default': 0.7,
                            'minimum': 0,
                            'maximum': 1,
                            'description': 'Controls randomness in responses'
                        },
                        'max_tokens': {
                            'type': 'integer',
                            'title': 'Max Tokens',
                            'default': 1000,
                            'minimum': 1,
                            'maximum': 8192
                        }
                    },
                    'required': ['api_key']
                },
                'default_configuration': {
                    'model': 'gemini-pro',
                    'temperature': 0.7,
                    'max_tokens': 1000
                },
                'ui_schema': {
                    'api_key': {'ui:widget': 'password'}
                }
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