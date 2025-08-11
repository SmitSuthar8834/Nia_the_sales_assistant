from django.core.management.base import BaseCommand

from admin_config.models import ConfigurationTemplate


class Command(BaseCommand):
    help = "Test template creation"

    def handle(self, *args, **options):
        self.stdout.write("Testing template creation...")

        # Simple test template
        template_data = {
            "name": "Test Template",
            "description": "Test template",
            "category": "crm",
            "configuration_schema": {"type": "object", "properties": {}},
            "default_configuration": {},
            "ui_schema": {},
        }

        from django.contrib.auth import get_user_model

        User = get_user_model()
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "is_staff": True,
                "is_superuser": True,
            },
        )

        template, created = ConfigurationTemplate.objects.get_or_create(
            name=template_data["name"],
            defaults={**template_data, "created_by": admin_user, "is_official": True},
        )

        if created:
            self.stdout.write(f"Created test template: {template.name}")
        else:
            self.stdout.write(f"Test template already exists: {template.name}")

        # Count all templates
        count = ConfigurationTemplate.objects.count()
        self.stdout.write(f"Total templates in database: {count}")

        # List all templates
        for t in ConfigurationTemplate.objects.all():
            self.stdout.write(f"- {t.name}")
