"""
Calendar Integration Admin Interface

Provides admin interface for managing calendar integrations,
viewing sync status, and managing meeting scheduling.
"""

from datetime import timedelta

from django.contrib import admin, messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from ai_service.models import Lead

from .calendar_integration_service import CalendarIntegrationService
from .models import Meeting


class CalendarIntegrationAdmin:
    """Admin interface for calendar integration management"""

    def get_urls(self):
        """Get admin URLs for calendar integration"""
        urls = [
            path(
                "calendar-sync-status/",
                self.admin_site.admin_view(self.calendar_sync_status_view),
                name="calendar_sync_status",
            ),
            path(
                "connect-google-calendar/",
                self.admin_site.admin_view(self.connect_google_calendar),
                name="connect_google_calendar",
            ),
            path(
                "connect-outlook-calendar/",
                self.admin_site.admin_view(self.connect_outlook_calendar),
                name="connect_outlook_calendar",
            ),
            path(
                "schedule-meeting/<uuid:lead_id>/",
                self.admin_site.admin_view(self.schedule_meeting_view),
                name="schedule_meeting_with_lead",
            ),
            path(
                "meeting-conflicts/<uuid:meeting_id>/",
                self.admin_site.admin_view(self.check_meeting_conflicts),
                name="check_meeting_conflicts",
            ),
            path(
                "available-slots/",
                self.admin_site.admin_view(self.find_available_slots_view),
                name="find_available_slots",
            ),
        ]
        return urls

    @staff_member_required
    def calendar_sync_status_view(self, request):
        """View calendar sync status for all users"""
        calendar_service = CalendarIntegrationService()

        # Get sync status for current user
        user_sync_status = calendar_service.get_calendar_sync_status(request.user)

        # Get recent meetings
        recent_meetings = Meeting.objects.filter(
            lead__user=request.user,
            scheduled_at__gte=timezone.now() - timedelta(days=30),
        ).order_by("-scheduled_at")[:10]

        context = {
            "title": "Calendar Integration Status",
            "user_sync_status": user_sync_status,
            "recent_meetings": recent_meetings,
            "has_google_auth": user_sync_status["google_calendar"]["connected"],
            "has_outlook_auth": user_sync_status["outlook_calendar"]["connected"],
        }

        return render(
            request, "admin/meeting_service/calendar_sync_status.html", context
        )

    @staff_member_required
    def connect_google_calendar(self, request):
        """Initiate Google Calendar connection"""
        try:
            calendar_service = CalendarIntegrationService()
            auth_url = calendar_service.get_google_authorization_url(
                str(request.user.id)
            )
            return HttpResponseRedirect(auth_url)
        except Exception as e:
            messages.error(request, f"Error connecting to Google Calendar: {str(e)}")
            return HttpResponseRedirect(reverse("admin:calendar_sync_status"))

    @staff_member_required
    def connect_outlook_calendar(self, request):
        """Initiate Outlook Calendar connection"""
        try:
            calendar_service = CalendarIntegrationService()
            auth_url = calendar_service.get_outlook_authorization_url(
                str(request.user.id)
            )
            return HttpResponseRedirect(auth_url)
        except Exception as e:
            messages.error(request, f"Error connecting to Outlook Calendar: {str(e)}")
            return HttpResponseRedirect(reverse("admin:calendar_sync_status"))

    @staff_member_required
    def schedule_meeting_view(self, request, lead_id):
        """Schedule meeting with automatic conflict resolution"""
        lead = get_object_or_404(Lead, id=lead_id, user=request.user)

        if request.method == "POST":
            try:
                meeting_data = {
                    "title": request.POST.get(
                        "title", f"Meeting with {lead.company_name}"
                    ),
                    "description": request.POST.get("description", ""),
                    "duration_minutes": int(request.POST.get("duration_minutes", 60)),
                    "preferred_start_time": request.POST.get("preferred_start_time"),
                    "attendee_emails": request.POST.get("attendee_emails", "").split(
                        ","
                    ),
                }

                calendar_service = CalendarIntegrationService()
                success, result = (
                    calendar_service.schedule_meeting_with_conflict_resolution(
                        request.user, lead, meeting_data
                    )
                )

                if success:
                    messages.success(request, "Meeting scheduled successfully!")
                    return HttpResponseRedirect(
                        reverse(
                            "admin:meeting_service_meeting_change",
                            args=[result["meeting_id"]],
                        )
                    )
                else:
                    messages.error(
                        request,
                        f'Failed to schedule meeting: {result.get("error", "Unknown error")}',
                    )

            except Exception as e:
                messages.error(request, f"Error scheduling meeting: {str(e)}")

        # Get available time slots for the next 7 days
        calendar_service = CalendarIntegrationService()
        start_date = timezone.now() + timedelta(hours=1)
        end_date = start_date + timedelta(days=7)

        available_slots = calendar_service.find_available_time_slots(
            request.user, 60, start_date, end_date
        )[
            :10
        ]  # Top 10 slots

        context = {
            "title": f"Schedule Meeting with {lead.company_name}",
            "lead": lead,
            "available_slots": available_slots,
        }

        return render(request, "admin/meeting_service/schedule_meeting.html", context)

    @staff_member_required
    def check_meeting_conflicts(self, request, meeting_id):
        """Check conflicts for a specific meeting"""
        meeting = get_object_or_404(Meeting, id=meeting_id, lead__user=request.user)

        calendar_service = CalendarIntegrationService()
        end_time = meeting.scheduled_at + timedelta(minutes=meeting.duration_minutes)

        conflicts = calendar_service.detect_calendar_conflicts(
            request.user, meeting.scheduled_at, end_time, [str(meeting_id)]
        )

        return JsonResponse(
            {
                "meeting_id": str(meeting.id),
                "meeting_title": meeting.title,
                "scheduled_at": meeting.scheduled_at.isoformat(),
                "conflicts": [conflict.to_dict() for conflict in conflicts],
                "has_conflicts": len(conflicts) > 0,
            }
        )

    @staff_member_required
    def find_available_slots_view(self, request):
        """Find available time slots"""
        duration_minutes = int(request.GET.get("duration_minutes", 60))
        days_ahead = int(request.GET.get("days_ahead", 7))

        calendar_service = CalendarIntegrationService()
        start_date = timezone.now() + timedelta(hours=1)
        end_date = start_date + timedelta(days=days_ahead)

        available_slots = calendar_service.find_available_time_slots(
            request.user, duration_minutes, start_date, end_date
        )

        # Convert datetime objects to ISO strings for JSON response
        slots_data = []
        for slot in available_slots[:20]:  # Limit to 20 slots
            slots_data.append(
                {
                    "start_time": slot["start_time"].isoformat(),
                    "end_time": slot["end_time"].isoformat(),
                    "duration_minutes": slot["duration_minutes"],
                    "confidence_score": slot["confidence_score"],
                }
            )

        return JsonResponse(
            {
                "available_slots": slots_data,
                "search_criteria": {
                    "duration_minutes": duration_minutes,
                    "days_ahead": days_ahead,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                "total_slots": len(slots_data),
            }
        )


# Extend the Meeting admin with calendar integration features
class MeetingCalendarAdmin(admin.ModelAdmin):
    """Enhanced Meeting admin with calendar integration"""

    list_display = [
        "title",
        "lead_company_name",
        "scheduled_at",
        "status",
        "meeting_platform",
        "calendar_sync_status",
        "meeting_actions",
    ]
    list_filter = ["status", "meeting_platform", "scheduled_at"]
    search_fields = ["title", "lead__company_name", "description"]
    readonly_fields = ["created_at", "updated_at", "calendar_sync_info"]

    fieldsets = (
        (
            "Meeting Information",
            {"fields": ("lead", "title", "description", "meeting_type")},
        ),
        ("Scheduling", {"fields": ("scheduled_at", "duration_minutes", "status")}),
        (
            "Platform & Integration",
            {"fields": ("meeting_url", "meeting_platform", "participants")},
        ),
        (
            "AI Insights",
            {"fields": ("agenda", "ai_insights"), "classes": ("collapse",)},
        ),
        (
            "System Information",
            {
                "fields": ("created_at", "updated_at", "calendar_sync_info"),
                "classes": ("collapse",),
            },
        ),
    )

    def lead_company_name(self, obj):
        """Get company name from related lead"""
        return obj.lead.company_name if obj.lead else "N/A"

    lead_company_name.short_description = "Company"

    def calendar_sync_status(self, obj):
        """Show calendar sync status"""
        if obj.ai_insights.get("auto_scheduled"):
            return format_html('<span style="color: green;">✓ Auto-scheduled</span>')
        elif obj.meeting_url:
            return format_html('<span style="color: blue;">✓ Manual</span>')
        else:
            return format_html('<span style="color: orange;">⚠ No calendar sync</span>')

    calendar_sync_status.short_description = "Calendar Sync"

    def calendar_sync_info(self, obj):
        """Display calendar sync information"""
        if not obj.ai_insights:
            return "No sync information available"

        info = []
        if obj.ai_insights.get("auto_scheduled"):
            info.append("✓ Automatically scheduled")

        if obj.ai_insights.get("alternative_time_used"):
            info.append("⚠ Alternative time used due to conflicts")

        conflicts = obj.ai_insights.get("original_conflicts", [])
        if conflicts:
            info.append(f"🔄 Resolved {len(conflicts)} conflicts")

        integrations = obj.ai_insights.get("calendar_integrations", [])
        if integrations:
            info.append(f'📅 Synced to: {", ".join(integrations)}')

        return mark_safe("<br>".join(info)) if info else "No sync information"

    calendar_sync_info.short_description = "Calendar Sync Details"

    def meeting_actions(self, obj):
        """Custom actions for meetings"""
        actions = []

        # Check conflicts action
        actions.append(
            f'<a href="{reverse("admin:check_meeting_conflicts", args=[obj.id])}" '
            f'class="button" target="_blank">Check Conflicts</a>'
        )

        # Reschedule action
        if obj.status == "scheduled":
            actions.append(
                f'<a href="{reverse("admin:schedule_meeting_with_lead", args=[obj.lead.id])}" '
                f'class="button">Reschedule</a>'
            )

        return format_html(" ".join(actions))

    meeting_actions.short_description = "Actions"

    def get_urls(self):
        """Add custom URLs for calendar integration"""
        urls = super().get_urls()
        calendar_admin = CalendarIntegrationAdmin()
        calendar_admin.admin_site = self.admin_site
        custom_urls = calendar_admin.get_urls()
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        """Add calendar integration context to changelist"""
        extra_context = extra_context or {}

        # Add calendar sync status summary
        calendar_service = CalendarIntegrationService()
        sync_status = calendar_service.get_calendar_sync_status(request.user)

        extra_context.update(
            {
                "calendar_sync_status": sync_status,
                "show_calendar_integration": True,
            }
        )

        return super().changelist_view(request, extra_context)


# Register the enhanced admin
# Note: This would replace the existing Meeting admin registration
# admin.site.register(Meeting, MeetingCalendarAdmin)
