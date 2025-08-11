from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import IntegrityError

User = get_user_model()


class Command(BaseCommand):
    help = "Create sample users for NIA Sales Assistant demo"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force", action="store_true", help="Force create even if users exist"
        )

    def handle(self, *args, **options):
        force = options["force"]

        self.stdout.write(
            self.style.SUCCESS("🤖 Setting up NIA Sales Assistant Sample Users...")
        )

        sample_users = [
            {
                "username": "admin",
                "email": "admin@nia.com",
                "password": "admin123",
                "first_name": "NIA",
                "last_name": "Administrator",
                "role": User.Role.ADMIN,
                "is_superuser": True,
                "is_staff": True,
                "department": "IT Administration",
            },
            {
                "username": "sales_manager",
                "email": "manager@nia.com",
                "password": "manager123",
                "first_name": "Sarah",
                "last_name": "Johnson",
                "role": User.Role.SALES_MANAGER,
                "is_staff": True,
                "department": "Sales",
                "phone": "+1-555-0101",
            },
            {
                "username": "sales_rep1",
                "email": "rep1@nia.com",
                "password": "rep123",
                "first_name": "Mike",
                "last_name": "Chen",
                "role": User.Role.SALES_REP,
                "is_staff": True,
                "department": "Sales",
                "phone": "+1-555-0102",
            },
            {
                "username": "sales_rep2",
                "email": "rep2@nia.com",
                "password": "rep123",
                "first_name": "Emily",
                "last_name": "Rodriguez",
                "role": User.Role.SALES_REP,
                "is_staff": True,
                "department": "Sales",
                "phone": "+1-555-0103",
            },
            {
                "username": "analyst",
                "email": "analyst@nia.com",
                "password": "analyst123",
                "first_name": "David",
                "last_name": "Kim",
                "role": User.Role.ANALYST,
                "is_staff": True,
                "department": "Analytics",
                "phone": "+1-555-0104",
            },
        ]

        created_count = 0
        updated_count = 0

        for user_data in sample_users:
            username = user_data["username"]

            try:
                # Check if user exists
                if User.objects.filter(username=username).exists():
                    if not force:
                        self.stdout.write(
                            self.style.WARNING(
                                f'⚠️  User "{username}" already exists, skipping...'
                            )
                        )
                        continue
                    else:
                        # Update existing user
                        user = User.objects.get(username=username)
                        for key, value in user_data.items():
                            if key != "password":
                                setattr(user, key, value)
                        user.set_password(user_data["password"])
                        user.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"✅ Updated user: {username}")
                        )
                        continue

                # Create new user
                password = user_data.pop("password")
                is_superuser = user_data.pop("is_superuser", False)

                if is_superuser:
                    user = User.objects.create_superuser(password=password, **user_data)
                else:
                    user = User.objects.create_user(password=password, **user_data)

                # Set user preferences based on role
                if user.role == User.Role.ADMIN:
                    preferences = {
                        "ai_assistance_level": "advanced",
                        "dashboard_layout": "full",
                        "notifications": {
                            "email": True,
                            "browser": True,
                            "lead_updates": True,
                        },
                        "ai_settings": {
                            "auto_analysis": True,
                            "confidence_threshold": 0.7,
                        },
                    }
                elif user.role == User.Role.SALES_MANAGER:
                    preferences = {
                        "ai_assistance_level": "advanced",
                        "dashboard_layout": "manager",
                        "notifications": {
                            "email": True,
                            "browser": True,
                            "team_updates": True,
                        },
                        "ai_settings": {
                            "auto_analysis": True,
                            "confidence_threshold": 0.8,
                        },
                    }
                else:
                    preferences = {
                        "ai_assistance_level": "standard",
                        "dashboard_layout": "simple",
                        "notifications": {"email": True, "browser": False},
                        "ai_settings": {
                            "auto_analysis": False,
                            "confidence_threshold": 0.75,
                        },
                    }

                user.preferences = preferences
                user.save()

                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Created user: {username} ({user.get_role_display()})"
                    )
                )

            except IntegrityError as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error creating user {username}: {e}")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Unexpected error for user {username}: {e}")
                )

        # Set up manager relationships
        try:
            manager = User.objects.get(username="sales_manager")
            sales_reps = User.objects.filter(role=User.Role.SALES_REP)
            sales_reps.update(manager=manager)

            self.stdout.write(self.style.SUCCESS(f"✅ Set up manager relationships"))
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"⚠️  Could not set up manager relationships: {e}")
            )

        self.stdout.write(self.style.SUCCESS(""))
        self.stdout.write(self.style.SUCCESS("📊 Summary:"))
        self.stdout.write(self.style.SUCCESS(f"   Created: {created_count} users"))
        self.stdout.write(self.style.SUCCESS(f"   Updated: {updated_count} users"))
        self.stdout.write(self.style.SUCCESS(""))
        self.stdout.write(
            self.style.SUCCESS("🚀 Sample users are ready! Login credentials:")
        )
        self.stdout.write(self.style.SUCCESS(""))

        for user_data in sample_users:
            self.stdout.write(
                self.style.SUCCESS(
                    f'   {user_data["username"]} / {user_data.get("password", "N/A")} ({user_data["role"]})'
                )
            )

        self.stdout.write(self.style.SUCCESS(""))
        self.stdout.write(
            self.style.SUCCESS("🌐 Admin panel: http://localhost:8000/admin/")
        )
        self.stdout.write(
            self.style.WARNING("⚠️  Remember to change passwords after first login!")
        )
