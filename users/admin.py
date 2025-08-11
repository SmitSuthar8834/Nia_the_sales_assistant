import json

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.models import Group, Permission
from django.utils.html import format_html

from .models import User


class CustomUserCreationForm(UserCreationForm):
    """Custom user creation form for admin"""

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "role")


class CustomUserChangeForm(UserChangeForm):
    """Custom user change form for admin"""

    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Enhanced User admin with role management and activity tracking"""

    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "is_active",
        "is_staff",
        "last_login",
        "user_stats",
        "user_actions",
    ]
    list_filter = [
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
        "date_joined",
        "last_login",
    ]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering = ["-date_joined"]

    readonly_fields = [
        "id",
        "date_joined",
        "created_at",
        "updated_at",
        "last_login",
        "preferences_display",
    ]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("username", "email", "first_name", "last_name")},
        ),
        (
            "Role & Permissions",
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Password",
            {
                "fields": ("password",),
                "description": "Use the password change form to update the password",
            },
        ),
        (
            "User Preferences",
            {
                "fields": ("preferences", "preferences_display"),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "id",
                    "date_joined",
                    "created_at",
                    "updated_at",
                    "last_login",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    add_fieldsets = (
        (
            "Create New User",
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "first_name",
                    "last_name",
                    "role",
                    "password1",
                    "password2",
                ),
            },
        ),
        (
            "Permissions",
            {
                "classes": ("wide",),
                "fields": ("is_active", "is_staff", "is_superuser"),
            },
        ),
    )

    def preferences_display(self, obj):
        """Display user preferences in a formatted way"""
        if obj.preferences:
            formatted_json = json.dumps(obj.preferences, indent=2)
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; max-height: 200px; overflow-y: auto;">{}</pre>',
                formatted_json,
            )
        return "No preferences set"

    preferences_display.short_description = "Preferences (Formatted)"

    def user_stats(self, obj):
        """Display user statistics"""
        try:
            # Get user's leads count
            leads_count = obj.leads.count() if hasattr(obj, "leads") else 0

            # Get user's conversation analyses count
            analyses_count = (
                obj.conversationanalysis_set.count()
                if hasattr(obj, "conversationanalysis_set")
                else 0
            )

            return format_html(
                '<div style="text-align: center;">'
                '<div style="font-weight: bold; color: #0073aa;">📊 Stats</div>'
                '<div style="font-size: 12px;">'
                "📋 Leads: {} | 💬 Analyses: {}"
                "</div>"
                "</div>",
                leads_count,
                analyses_count,
            )
        except:
            return "Stats unavailable"

    user_stats.short_description = "Activity Stats"

    def user_actions(self, obj):
        """Display action buttons for user management"""
        actions = []

        # View user's leads
        actions.append(
            f'<a href="/admin/ai_service/lead/?user__id__exact={obj.id}" '
            f'class="button" style="background: #0073aa; color: white; padding: 5px 10px; '
            f'text-decoration: none; border-radius: 3px; margin-right: 5px;">📋 View Leads</a>'
        )

        # View user's analyses
        actions.append(
            f'<a href="/admin/ai_service/conversationanalysis/?user__id__exact={obj.id}" '
            f'class="button" style="background: #17a2b8; color: white; padding: 5px 10px; '
            f'text-decoration: none; border-radius: 3px; margin-right: 5px;">💬 View Analyses</a>'
        )

        # Reset password (if staff)
        if obj.is_active:
            actions.append(
                f'<a href="/admin/auth/user/{obj.id}/password/" '
                f'class="button" style="background: #28a745; color: white; padding: 5px 10px; '
                f'text-decoration: none; border-radius: 3px;">🔑 Reset Password</a>'
            )

        return format_html("".join(actions))

    user_actions.short_description = "Actions"
    user_actions.allow_tags = True

    def get_queryset(self, request):
        """Optimize queryset with related data"""
        return (
            super()
            .get_queryset(request)
            .select_related()
            .prefetch_related("groups", "user_permissions")
        )


# Register Permission model for admin access
@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """Enhanced Permission admin for better permission management"""

    list_display = ["name", "content_type", "codename"]
    list_filter = ["content_type"]
    search_fields = ["name", "codename", "content_type__model"]
    ordering = ["content_type", "codename"]

    def has_add_permission(self, request):
        """Only superusers can add permissions"""
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete permissions"""
        return request.user.is_superuser


# Enhanced Group admin
class GroupAdmin(admin.ModelAdmin):
    """Enhanced Group admin with better permission management"""

    list_display = ["name", "permission_count"]
    search_fields = ["name"]
    filter_horizontal = ["permissions"]

    def permission_count(self, obj):
        """Display number of permissions in the group"""
        count = obj.permissions.count()
        return format_html(
            '<span style="background: #0073aa; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">{}</span>',
            count,
        )

    permission_count.short_description = "Permissions"


# Unregister the default Group admin and register our enhanced version
admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)

# Custom admin site configuration for better user management
admin.site.site_header = "🤖 NIA Sales Assistant - Admin Panel"
admin.site.site_title = "NIA Admin"
admin.site.index_title = "Welcome to NIA Sales Assistant Administration"
