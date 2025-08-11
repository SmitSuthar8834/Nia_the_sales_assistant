from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import IntegrityError

User = get_user_model()


class Command(BaseCommand):
    help = "Create an admin user for NIA Sales Assistant"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username", type=str, help="Admin username", default="admin"
        )
        parser.add_argument(
            "--email", type=str, help="Admin email", default="admin@nia.com"
        )
        parser.add_argument(
            "--password", type=str, help="Admin password", default="admin123"
        )
        parser.add_argument(
            "--force", action="store_true", help="Force create even if user exists"
        )

    def handle(self, *args, **options):
        username = options["username"]
        email = options["email"]
        password = options["password"]
        force = options["force"]

        self.stdout.write(
            self.style.SUCCESS("🤖 Creating NIA Sales Assistant Admin User...")
        )

        try:
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                if not force:
                    self.stdout.write(
                        self.style.WARNING(
                            f'❌ User "{username}" already exists. Use --force to recreate.'
                        )
                    )
                    return
                else:
                    # Delete existing user
                    User.objects.filter(username=username).delete()
                    self.stdout.write(
                        self.style.WARNING(f'🗑️ Deleted existing user "{username}"')
                    )

            # Create admin user
            admin_user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name="NIA",
                last_name="Administrator",
                role=User.Role.ADMIN,
            )

            # Set admin preferences
            admin_user.preferences = {
                "ai_assistance_level": "advanced",
                "dashboard_layout": "full",
                "notifications": {
                    "email": True,
                    "browser": True,
                    "lead_updates": True,
                    "ai_insights": True,
                },
                "ai_settings": {
                    "auto_analysis": True,
                    "confidence_threshold": 0.7,
                    "preferred_model": "gemini-1.5-flash",
                },
            }
            admin_user.save()

            self.stdout.write(self.style.SUCCESS("✅ Admin user created successfully!"))
            self.stdout.write(self.style.SUCCESS(""))
            self.stdout.write(self.style.SUCCESS("📋 Admin User Details:"))
            self.stdout.write(self.style.SUCCESS(f"   Username: {username}"))
            self.stdout.write(self.style.SUCCESS(f"   Email: {email}"))
            self.stdout.write(self.style.SUCCESS(f"   Password: {password}"))
            self.stdout.write(
                self.style.SUCCESS(f"   Role: {admin_user.get_role_display()}")
            )
            self.stdout.write(self.style.SUCCESS(""))
            self.stdout.write(
                self.style.SUCCESS("🚀 You can now login to the admin panel at:")
            )
            self.stdout.write(self.style.SUCCESS("   http://localhost:8000/admin/"))
            self.stdout.write(self.style.SUCCESS(""))
            self.stdout.write(
                self.style.WARNING(
                    "⚠️  Remember to change the password after first login!"
                )
            )

        except IntegrityError as e:
            self.stdout.write(self.style.ERROR(f"❌ Error creating admin user: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Unexpected error: {e}"))
