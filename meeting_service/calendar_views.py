"""
Calendar Integration Views for NIA Sales Assistant

Provides API endpoints for calendar integration, conflict detection,
and automatic meeting scheduling.
"""

import logging
from datetime import timedelta

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ai_service.models import Lead

from .calendar_integration_service import CalendarIntegrationService
from .models import Meeting

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_calendar_authorization_urls(request):
    """Get authorization URLs for calendar integrations"""
    try:
        calendar_service = CalendarIntegrationService()
        user_id = str(request.user.id)

        google_url = calendar_service.get_google_authorization_url(user_id)
        outlook_url = calendar_service.get_outlook_authorization_url(user_id)

        return Response(
            {
                "google_calendar_auth_url": google_url,
                "outlook_calendar_auth_url": outlook_url,
                "message": "Redirect user to these URLs to authorize calendar access",
            }
        )

    except Exception as e:
        logger.error(f"Error getting calendar authorization URLs: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def google_calendar_oauth_callback(request):
    """Handle Google Calendar OAuth callback"""
    try:
        code = request.GET.get("code")
        state = request.GET.get("state")

        if not code or not state:
            return Response(
                {"error": "Missing authorization code or state parameter"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        calendar_service = CalendarIntegrationService()
        success = calendar_service.handle_google_oauth_callback(code, state)

        if success:
            return Response(
                {
                    "message": "Google Calendar authorization successful",
                    "redirect_url": "/admin/",  # Redirect to admin panel
                }
            )
        else:
            return Response(
                {"error": "Failed to process Google Calendar authorization"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Exception as e:
        logger.error(f"Error in Google Calendar OAuth callback: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def outlook_calendar_oauth_callback(request):
    """Handle Outlook Calendar OAuth callback"""
    try:
        code = request.GET.get("code")
        state = request.GET.get("state")

        if not code or not state:
            return Response(
                {"error": "Missing authorization code or state parameter"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        calendar_service = CalendarIntegrationService()
        success = calendar_service.handle_outlook_oauth_callback(code, state)

        if success:
            return Response(
                {
                    "message": "Outlook Calendar authorization successful",
                    "redirect_url": "/admin/",  # Redirect to admin panel
                }
            )
        else:
            return Response(
                {"error": "Failed to process Outlook Calendar authorization"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Exception as e:
        logger.error(f"Error in Outlook Calendar OAuth callback: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_calendar_events(request):
    """Get calendar events from all connected calendars"""
    try:
        # Get date range from query parameters
        start_date_str = request.GET.get("start_date")
        end_date_str = request.GET.get("end_date")

        if start_date_str and end_date_str:
            start_date = parse_datetime(start_date_str)
            end_date = parse_datetime(end_date_str)
        else:
            # Default to next 7 days
            start_date = timezone.now()
            end_date = start_date + timedelta(days=7)

        calendar_service = CalendarIntegrationService()
        events = calendar_service.get_all_calendar_events(
            request.user, start_date, end_date
        )

        # Convert datetime objects to ISO strings for JSON serialization
        for event in events:
            event["start_time"] = event["start_time"].isoformat()
            event["end_time"] = event["end_time"].isoformat()

        return Response(
            {
                "events": events,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "total_events": len(events),
            }
        )

    except Exception as e:
        logger.error(f"Error getting calendar events: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def detect_meeting_conflicts(request):
    """Detect conflicts for a proposed meeting time"""
    try:
        start_time_str = request.data.get("start_time")
        end_time_str = request.data.get("end_time")
        exclude_event_ids = request.data.get("exclude_event_ids", [])

        if not start_time_str or not end_time_str:
            return Response(
                {"error": "start_time and end_time are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_time = parse_datetime(start_time_str)
        end_time = parse_datetime(end_time_str)

        if not start_time or not end_time:
            return Response(
                {
                    "error": "Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        calendar_service = CalendarIntegrationService()
        conflicts = calendar_service.detect_calendar_conflicts(
            request.user, start_time, end_time, exclude_event_ids
        )

        return Response(
            {
                "conflicts": [conflict.to_dict() for conflict in conflicts],
                "has_conflicts": len(conflicts) > 0,
                "proposed_meeting": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                },
            }
        )

    except Exception as e:
        logger.error(f"Error detecting meeting conflicts: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def find_available_time_slots(request):
    """Find available time slots for scheduling meetings"""
    try:
        duration_minutes = request.data.get("duration_minutes", 60)
        start_date_str = request.data.get("start_date")
        end_date_str = request.data.get("end_date")
        working_hours = request.data.get("working_hours", [9, 17])
        exclude_weekends = request.data.get("exclude_weekends", True)

        if start_date_str and end_date_str:
            start_date = parse_datetime(start_date_str)
            end_date = parse_datetime(end_date_str)
        else:
            # Default to next 14 days
            start_date = timezone.now() + timedelta(hours=1)
            end_date = start_date + timedelta(days=14)

        if not start_date or not end_date:
            return Response(
                {
                    "error": "Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        calendar_service = CalendarIntegrationService()
        available_slots = calendar_service.find_available_time_slots(
            request.user,
            duration_minutes,
            start_date,
            end_date,
            tuple(working_hours),
            exclude_weekends,
        )

        # Convert datetime objects to ISO strings
        for slot in available_slots:
            slot["start_time"] = slot["start_time"].isoformat()
            slot["end_time"] = slot["end_time"].isoformat()

        return Response(
            {
                "available_slots": available_slots,
                "search_criteria": {
                    "duration_minutes": duration_minutes,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "working_hours": working_hours,
                    "exclude_weekends": exclude_weekends,
                },
                "total_slots": len(available_slots),
            }
        )

    except Exception as e:
        logger.error(f"Error finding available time slots: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def schedule_meeting_with_lead(request):
    """Schedule a meeting with automatic conflict resolution"""
    try:
        lead_id = request.data.get("lead_id")
        meeting_data = request.data.get("meeting_data", {})

        if not lead_id:
            return Response(
                {"error": "lead_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            lead = Lead.objects.get(id=lead_id, user=request.user)
        except Lead.DoesNotExist:
            return Response(
                {"error": "Lead not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        calendar_service = CalendarIntegrationService()
        success, result = calendar_service.schedule_meeting_with_conflict_resolution(
            request.user, lead, meeting_data
        )

        if success:
            return Response(
                {
                    "success": True,
                    "meeting": result,
                    "message": "Meeting scheduled successfully",
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {
                    "success": False,
                    "error": result.get("error", "Failed to schedule meeting"),
                    "details": result,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Exception as e:
        logger.error(f"Error scheduling meeting with lead: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def schedule_meeting_reminders(request):
    """Schedule reminders for a meeting"""
    try:
        meeting_id = request.data.get("meeting_id")
        reminder_times = request.data.get("reminder_times", [24 * 60, 60, 15])

        if not meeting_id:
            return Response(
                {"error": "meeting_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            meeting = Meeting.objects.get(id=meeting_id, lead__user=request.user)
        except Meeting.DoesNotExist:
            return Response(
                {"error": "Meeting not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        calendar_service = CalendarIntegrationService()
        success = calendar_service.schedule_meeting_reminders(meeting, reminder_times)

        if success:
            return Response(
                {
                    "success": True,
                    "message": f"Scheduled {len(reminder_times)} reminders for meeting",
                    "reminder_times": reminder_times,
                }
            )
        else:
            return Response(
                {"success": False, "error": "Failed to schedule meeting reminders"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        logger.error(f"Error scheduling meeting reminders: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_calendar_sync_status(request):
    """Get the status of calendar integrations"""
    try:
        calendar_service = CalendarIntegrationService()
        sync_status = calendar_service.get_calendar_sync_status(request.user)

        return Response({"sync_status": sync_status, "user_id": str(request.user.id)})

    except Exception as e:
        logger.error(f"Error getting calendar sync status: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def calendar_integration_dashboard(request):
    """Get comprehensive calendar integration dashboard data"""
    try:
        calendar_service = CalendarIntegrationService()

        # Get sync status
        sync_status = calendar_service.get_calendar_sync_status(request.user)

        # Get today's events
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        today_events = calendar_service.get_all_calendar_events(
            request.user, today_start, today_end
        )

        # Get upcoming events (next 7 days)
        week_start = timezone.now()
        week_end = week_start + timedelta(days=7)
        upcoming_events = calendar_service.get_all_calendar_events(
            request.user, week_start, week_end
        )

        # Find available slots for tomorrow
        tomorrow_start = timezone.now() + timedelta(days=1)
        tomorrow_start = tomorrow_start.replace(
            hour=9, minute=0, second=0, microsecond=0
        )
        tomorrow_end = tomorrow_start.replace(hour=17)

        available_slots = calendar_service.find_available_time_slots(
            request.user, 60, tomorrow_start, tomorrow_end
        )

        # Convert datetime objects to ISO strings
        for event in today_events + upcoming_events:
            event["start_time"] = event["start_time"].isoformat()
            event["end_time"] = event["end_time"].isoformat()

        for slot in available_slots:
            slot["start_time"] = slot["start_time"].isoformat()
            slot["end_time"] = slot["end_time"].isoformat()

        return Response(
            {
                "sync_status": sync_status,
                "today_events": today_events,
                "upcoming_events": upcoming_events[:10],  # Limit to 10 events
                "available_slots_tomorrow": available_slots[:5],  # Top 5 slots
                "statistics": {
                    "today_events_count": len(today_events),
                    "upcoming_events_count": len(upcoming_events),
                    "available_slots_count": len(available_slots),
                },
                "dashboard_generated_at": timezone.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error getting calendar integration dashboard: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_meeting_invitation(request):
    """Send meeting invitation with preparation materials"""
    try:
        meeting_id = request.data.get("meeting_id")

        if not meeting_id:
            return Response(
                {"error": "meeting_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            meeting = Meeting.objects.get(id=meeting_id, lead__user=request.user)
        except Meeting.DoesNotExist:
            return Response(
                {"error": "Meeting not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        calendar_service = CalendarIntegrationService()

        # Generate preparation materials
        from .pre_meeting_intelligence import PreMeetingIntelligenceService

        intelligence_service = PreMeetingIntelligenceService()
        preparation_materials = intelligence_service.generate_meeting_preparation(
            meeting
        )

        # Format invitation
        invitation_text = calendar_service.format_meeting_invitation(
            meeting, preparation_materials
        )

        return Response(
            {
                "success": True,
                "invitation_text": invitation_text,
                "preparation_materials": preparation_materials,
                "meeting_url": meeting.meeting_url,
            }
        )

    except Exception as e:
        logger.error(f"Error sending meeting invitation: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
