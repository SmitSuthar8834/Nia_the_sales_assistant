from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Debug template list"

    def handle(self, *args, **options):
        templates = [
            {
                "name": "Salesforce CRM Integration",
                "description": "Standard Salesforce CRM integration template",
                "category": "crm",
            },
            {
                "name": "Google Meet Integration",
                "description": "Google Meet meeting platform integration",
                "category": "meeting",
            },
            {
                "name": "Microsoft Teams Integration",
                "description": "Microsoft Teams meeting platform integration",
                "category": "meeting",
            },
            {
                "name": "HubSpot CRM Integration",
                "description": "HubSpot CRM integration template",
                "category": "crm",
            },
            {
                "name": "Pipedrive CRM Integration",
                "description": "Pipedrive CRM integration template",
                "category": "crm",
            },
            {
                "name": "Gemini AI Integration",
                "description": "Google Gemini AI service integration",
                "category": "workflow",
            },
        ]

        self.stdout.write(f"Templates list has {len(templates)} items:")
        for i, template in enumerate(templates):
            self.stdout.write(f'{i+1}. {template["name"]} ({template["category"]})')
