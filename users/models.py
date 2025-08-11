import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """Enhanced User model with role-based access and preferences"""

    class Role(models.TextChoices):
        ADMIN = "admin", "Administrator"
        SALES_MANAGER = "sales_manager", "Sales Manager"
        SALES_REP = "sales_rep", "Sales Representative"
        ANALYST = "analyst", "Sales Analyst"
        VIEWER = "viewer", "Viewer Only"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=50, choices=Role.choices, default=Role.SALES_REP)

    # User preferences for AI and interface customization
    preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="User preferences for AI behavior, interface settings, and notifications",
    )

    # Profile information
    phone = models.CharField(
        max_length=20, blank=True, help_text="Contact phone number"
    )
    department = models.CharField(
        max_length=100, blank=True, help_text="Department or team"
    )
    manager = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="team_members",
        help_text="Direct manager or supervisor",
    )

    # Activity tracking
    last_ai_interaction = models.DateTimeField(
        null=True, blank=True, help_text="Last AI service usage"
    )
    ai_usage_count = models.PositiveIntegerField(
        default=0, help_text="Total AI interactions"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["role", "is_active"]),
            models.Index(fields=["last_login"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def full_name(self):
        """Get user's full name"""
        return self.get_full_name() or self.username

    @property
    def is_sales_manager(self):
        """Check if user is a sales manager"""
        return self.role == self.Role.SALES_MANAGER

    @property
    def is_sales_rep(self):
        """Check if user is a sales representative"""
        return self.role == self.Role.SALES_REP

    @property
    def can_manage_leads(self):
        """Check if user can manage leads"""
        return self.role in [
            self.Role.ADMIN,
            self.Role.SALES_MANAGER,
            self.Role.SALES_REP,
        ]

    @property
    def can_use_ai(self):
        """Check if user can use AI features"""
        return self.role in [
            self.Role.ADMIN,
            self.Role.SALES_MANAGER,
            self.Role.SALES_REP,
            self.Role.ANALYST,
        ]

    @property
    def team_size(self):
        """Get number of team members if user is a manager"""
        return self.team_members.count()

    def update_ai_usage(self):
        """Update AI usage tracking"""
        self.ai_usage_count += 1
        self.last_ai_interaction = timezone.now()
        self.save(update_fields=["ai_usage_count", "last_ai_interaction"])

    def get_preference(self, key, default=None):
        """Get a specific user preference"""
        return self.preferences.get(key, default)

    def set_preference(self, key, value):
        """Set a specific user preference"""
        self.preferences[key] = value
        self.save(update_fields=["preferences"])

    def get_accessible_leads(self):
        """Get leads accessible to this user based on role"""
        if self.role == self.Role.ADMIN:
            from ai_service.models import Lead

            return Lead.objects.all()
        elif self.role == self.Role.SALES_MANAGER:
            # Managers can see their own leads and their team's leads
            from ai_service.models import Lead

            team_member_ids = list(self.team_members.values_list("id", flat=True))
            team_member_ids.append(self.id)
            return Lead.objects.filter(user_id__in=team_member_ids)
        else:
            # Sales reps and others can only see their own leads
            return self.leads.all()
