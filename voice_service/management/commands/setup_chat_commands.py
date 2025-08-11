"""
Management command to set up initial chat bot commands
"""

from django.core.management.base import BaseCommand

from voice_service.chat_models import ChatBotCommand


class Command(BaseCommand):
    help = "Set up initial chat bot commands"

    def handle(self, *args, **options):
        commands = [
            {
                "command": "help",
                "command_type": ChatBotCommand.CommandType.HELP,
                "description": "Show all available commands and their usage",
                "usage_example": "/help",
                "parameters": {},
            },
            {
                "command": "schedule",
                "command_type": ChatBotCommand.CommandType.SCHEDULE_CALL,
                "description": "Schedule a call with NIA",
                "usage_example": "/schedule tomorrow 2pm",
                "parameters": {"date": "optional", "time": "optional"},
            },
            {
                "command": "lead",
                "command_type": ChatBotCommand.CommandType.GET_LEAD_INFO,
                "description": "Get information about a specific lead",
                "usage_example": "/lead Acme Corp",
                "parameters": {"company_name": "required"},
            },
            {
                "command": "create",
                "command_type": ChatBotCommand.CommandType.CREATE_LEAD,
                "description": "Create a new lead from conversation",
                "usage_example": "/create",
                "parameters": {},
            },
            {
                "command": "update",
                "command_type": ChatBotCommand.CommandType.UPDATE_LEAD,
                "description": "Update an existing lead",
                "usage_example": "/update Acme Corp status=qualified",
                "parameters": {
                    "company_name": "required",
                    "field": "required",
                    "value": "required",
                },
            },
            {
                "command": "search",
                "command_type": ChatBotCommand.CommandType.SEARCH_LEADS,
                "description": "Search for leads by company name or criteria",
                "usage_example": "/search tech companies",
                "parameters": {"query": "required"},
            },
            {
                "command": "analytics",
                "command_type": ChatBotCommand.CommandType.GET_ANALYTICS,
                "description": "Get lead analytics and insights",
                "usage_example": "/analytics",
                "parameters": {},
            },
            {
                "command": "voice",
                "command_type": ChatBotCommand.CommandType.VOICE_TRANSITION,
                "description": "Transition to voice call",
                "usage_example": "/voice",
                "parameters": {},
            },
        ]

        created_count = 0
        updated_count = 0

        for cmd_data in commands:
            command, created = ChatBotCommand.objects.get_or_create(
                command=cmd_data["command"],
                defaults={
                    "command_type": cmd_data["command_type"],
                    "description": cmd_data["description"],
                    "usage_example": cmd_data["usage_example"],
                    "parameters": cmd_data["parameters"],
                    "is_active": True,
                },
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Created command: /{command.command}")
                )
            else:
                # Update existing command
                command.command_type = cmd_data["command_type"]
                command.description = cmd_data["description"]
                command.usage_example = cmd_data["usage_example"]
                command.parameters = cmd_data["parameters"]
                command.is_active = True
                command.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f"Updated command: /{command.command}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully set up {created_count} new commands and updated {updated_count} existing commands"
            )
        )
