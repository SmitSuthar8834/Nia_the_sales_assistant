import json
from dataclasses import asdict
from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .meeting_outcome_service import MeetingOutcomeService
from .microsoft_teams_service import MicrosoftTeamsService
from .models import (
    Meeting,
    MeetingParticipant,
    MeetingQuestion,
    MeetingSession,
    MeetingStatusUpdate,
    MicrosoftTeamsCredentials,
)
from .pre_meeting_intelligence import PreMeetingIntelligenceService
from .question_service import MeetingQuestionService
from .serializers import (
    CreateTeamsMeetingSerializer,
    MeetingParticipantSerializer,
    MeetingSessionSerializer,
    MeetingStatusUpdateSerializer,
    MicrosoftTeamsCredentialsSerializer,
    SendChannelMessageSerializer,
    TeamsChannelSerializer,
    TeamsTeamSerializer,
)


class MeetingSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing meeting sessions"""

    serializer_class = MeetingSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get meetings for the current user"""
        user = self.request.user
        return MeetingSession.objects.filter(organizer=user).order_by(
            "-scheduled_start_time"
        )


class MeetingParticipantViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing meeting participants"""

    serializer_class = MeetingParticipantSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get participants for meetings the user has access to"""
        user = self.request.user
        accessible_meetings = MeetingSession.objects.filter(organizer=user)
        return MeetingParticipant.objects.filter(
            meeting__in=accessible_meetings
        ).order_by("-created_at")


class MeetingStatusUpdateViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing meeting status updates"""

    serializer_class = MeetingStatusUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get status updates for meetings the user has access to"""
        user = self.request.user
        accessible_meetings = MeetingSession.objects.filter(organizer=user)
        return MeetingStatusUpdate.objects.filter(
            meeting__in=accessible_meetings
        ).order_by("-timestamp")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def google_oauth_initiate(request):
    """Initiate Google OAuth flow"""
    return Response({"message": "Google OAuth integration coming soon"})


@api_view(["GET"])
def google_oauth_callback(request):
    """Handle Google OAuth callback"""
    return Response({"message": "OAuth callback handled"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def google_auth_status(request):
    """Check if user has valid Google credentials"""
    return Response(
        {"authenticated": False, "message": "Google authentication coming soon"}
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def meeting_dashboard(request):
    """Get dashboard data for meetings"""
    return Response(
        {
            "today_meetings": 0,
            "upcoming_meetings": 0,
            "active_meetings": 0,
            "recent_meetings": [],
            "google_auth_status": False,
        }
    )


# Microsoft Teams Integration Views


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def teams_oauth_initiate(request):
    """Initiate Microsoft Teams OAuth flow"""
    try:
        teams_service = MicrosoftTeamsService()
        auth_url = teams_service.get_authorization_url(str(request.user.id))

        return Response(
            {
                "authorization_url": auth_url,
                "message": "Redirect user to this URL to authorize Microsoft Teams access",
            }
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def teams_oauth_callback(request):
    """Handle Microsoft Teams OAuth callback"""
    try:
        code = request.GET.get("code")
        state = request.GET.get("state")  # This contains the user_id

        if not code or not state:
            return Response(
                {"error": "Missing authorization code or state parameter"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        teams_service = MicrosoftTeamsService()
        success = teams_service.handle_oauth_callback(code, state)

        if success:
            return Response({"message": "Microsoft Teams authorization successful"})
        else:
            return Response(
                {"error": "Failed to process Microsoft Teams authorization"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def teams_auth_status(request):
    """Check if user has valid Microsoft Teams credentials"""
    try:
        teams_creds = MicrosoftTeamsCredentials.objects.get(user=request.user)
        serializer = MicrosoftTeamsCredentialsSerializer(teams_creds)

        return Response(
            {
                "authenticated": not teams_creds.is_token_expired(),
                "credentials": serializer.data,
            }
        )
    except MicrosoftTeamsCredentials.DoesNotExist:
        return Response(
            {"authenticated": False, "message": "No Microsoft Teams credentials found"}
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_teams_meeting(request):
    """Create a new Microsoft Teams meeting"""
    try:
        serializer = CreateTeamsMeetingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        teams_service = MicrosoftTeamsService()
        meeting_session = teams_service.create_meeting(
            user=request.user,
            title=serializer.validated_data["title"],
            description=serializer.validated_data.get("description", ""),
            start_time=serializer.validated_data["scheduled_start_time"],
            end_time=serializer.validated_data["scheduled_end_time"],
            attendee_emails=serializer.validated_data.get("attendee_emails", []),
        )

        if meeting_session:
            meeting_serializer = MeetingSessionSerializer(meeting_session)
            return Response(meeting_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {"error": "Failed to create Microsoft Teams meeting"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_teams(request):
    """Get Teams that the user is a member of"""
    try:
        teams_service = MicrosoftTeamsService()
        teams = teams_service.get_user_teams(request.user)

        serializer = TeamsTeamSerializer(teams, many=True)
        return Response({"teams": serializer.data})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_team_channels(request, team_id):
    """Get channels for a specific team"""
    try:
        teams_service = MicrosoftTeamsService()
        channels = teams_service.get_team_channels(request.user, team_id)

        serializer = TeamsChannelSerializer(channels, many=True)
        return Response({"channels": serializer.data})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_channel_message(request):
    """Send a message to a Teams channel"""
    try:
        serializer = SendChannelMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        teams_service = MicrosoftTeamsService()
        success = teams_service.send_channel_message(
            user=request.user,
            team_id=serializer.validated_data["team_id"],
            channel_id=serializer.validated_data["channel_id"],
            message=serializer.validated_data["message"],
        )

        if success:
            return Response({"message": "Message sent successfully"})
        else:
            return Response(
                {"error": "Failed to send message"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_meeting_recordings(request, meeting_id):
    """Get recordings for a specific meeting"""
    try:
        teams_service = MicrosoftTeamsService()
        recordings = teams_service.get_meeting_recordings(request.user, meeting_id)

        return Response({"recordings": recordings})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_meeting_transcripts(request, meeting_id):
    """Get transcripts for a specific meeting"""
    try:
        teams_service = MicrosoftTeamsService()
        transcripts = teams_service.get_meeting_transcripts(request.user, meeting_id)

        return Response({"transcripts": transcripts})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Video Platform Integration Views

from .video_platform_service import VideoPlatformService


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_meeting_with_agenda(request):
    """Create a meeting with structured agenda on preferred platform"""
    try:
        data = request.data

        # Validate required fields
        required_fields = ["title", "start_time", "end_time"]
        for field in required_fields:
            if field not in data:
                return Response(
                    {"error": f"Missing required field: {field}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        video_service = VideoPlatformService()

        meeting_session = video_service.create_meeting_with_agenda(
            user=request.user,
            title=data["title"],
            description=data.get("description", ""),
            start_time=data["start_time"],
            end_time=data["end_time"],
            attendee_emails=data.get("attendee_emails", []),
            agenda_items=data.get("agenda_items", []),
            platform=data.get("platform"),
        )

        if meeting_session:
            serializer = MeetingSessionSerializer(meeting_session)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {"error": "Failed to create meeting"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_meeting_recordings_unified(request, meeting_id):
    """Get recordings for a meeting regardless of platform"""
    try:
        meeting_session = get_object_or_404(MeetingSession, id=meeting_id)

        # Check if user has access to this meeting
        if (
            meeting_session.organizer != request.user
            and not meeting_session.participants.filter(user=request.user).exists()
        ):
            return Response(
                {"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN
            )

        video_service = VideoPlatformService()
        recordings = video_service.get_meeting_recordings(meeting_session)

        return Response(
            {
                "recordings": recordings,
                "meeting_id": str(meeting_id),
                "platform": meeting_session.meeting_type,
            }
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_meeting_transcripts_unified(request, meeting_id):
    """Get transcripts for a meeting regardless of platform"""
    try:
        meeting_session = get_object_or_404(MeetingSession, id=meeting_id)

        # Check if user has access to this meeting
        if (
            meeting_session.organizer != request.user
            and not meeting_session.participants.filter(user=request.user).exists()
        ):
            return Response(
                {"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN
            )

        video_service = VideoPlatformService()
        transcripts = video_service.get_meeting_transcripts(meeting_session)

        return Response(
            {
                "transcripts": transcripts,
                "meeting_id": str(meeting_id),
                "platform": meeting_session.meeting_type,
            }
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def share_meeting_link(request, meeting_id):
    """Share meeting link via email"""
    try:
        meeting_session = get_object_or_404(MeetingSession, id=meeting_id)

        # Check if user is the organizer
        if meeting_session.organizer != request.user:
            return Response(
                {"error": "Only the meeting organizer can share the link"},
                status=status.HTTP_403_FORBIDDEN,
            )

        recipient_emails = request.data.get("recipient_emails", [])
        custom_message = request.data.get("custom_message")

        if not recipient_emails:
            return Response(
                {"error": "recipient_emails is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        video_service = VideoPlatformService()
        success = video_service.share_meeting_link(
            meeting_session, recipient_emails, custom_message
        )

        if success:
            return Response(
                {
                    "message": "Meeting link shared successfully",
                    "recipients": len(recipient_emails),
                }
            )
        else:
            return Response(
                {"error": "Failed to share meeting link"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def generate_meeting_link(request, meeting_id):
    """Generate or retrieve meeting link"""
    try:
        meeting_session = get_object_or_404(MeetingSession, id=meeting_id)

        # Check if user has access to this meeting
        if (
            meeting_session.organizer != request.user
            and not meeting_session.participants.filter(user=request.user).exists()
        ):
            return Response(
                {"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN
            )

        video_service = VideoPlatformService()
        meeting_link = video_service.generate_meeting_link(meeting_session)

        if meeting_link:
            return Response(
                {
                    "meeting_link": meeting_link,
                    "meeting_id": str(meeting_id),
                    "platform": meeting_session.meeting_type,
                }
            )
        else:
            return Response(
                {"error": "Failed to generate meeting link"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def enable_meeting_recording(request, meeting_id):
    """Enable recording for a meeting"""
    try:
        meeting_session = get_object_or_404(MeetingSession, id=meeting_id)

        # Check if user is the organizer
        if meeting_session.organizer != request.user:
            return Response(
                {"error": "Only the meeting organizer can enable recording"},
                status=status.HTTP_403_FORBIDDEN,
            )

        video_service = VideoPlatformService()
        success = video_service.enable_meeting_recording(meeting_session)

        if success:
            return Response(
                {
                    "message": "Recording enabled successfully",
                    "meeting_id": str(meeting_id),
                }
            )
        else:
            return Response(
                {"error": "Failed to enable recording"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_platform_capabilities(request):
    """Get available video platform capabilities for the user"""
    try:
        video_service = VideoPlatformService()
        capabilities = video_service.get_platform_capabilities(request.user)

        return Response(
            {
                "capabilities": capabilities,
                "preferred_platform": video_service.get_user_preferred_platform(
                    request.user
                ),
            }
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_automated_meeting(request):
    """Create an automated meeting with AI-generated agenda"""
    try:
        data = request.data

        # Validate required fields
        if "lead_data" not in data:
            return Response(
                {"error": "lead_data is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        video_service = VideoPlatformService()

        meeting_session = video_service.create_automated_meeting(
            user=request.user,
            lead_data=data["lead_data"],
            meeting_type=data.get("meeting_type", "discovery"),
            platform=data.get("platform"),
        )

        if meeting_session:
            serializer = MeetingSessionSerializer(meeting_session)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {"error": "Failed to create automated meeting"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_video_platform_analytics(request):
    """Get analytics for video platform usage"""
    try:
        days_back = int(request.GET.get("days_back", 30))

        video_service = VideoPlatformService()
        analytics = video_service.get_meeting_analytics(request.user, days_back)

        return Response({"analytics": analytics, "period_days": days_back})

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def teams_meeting_dashboard(request):
    """Get dashboard data for Teams meetings"""
    try:
        teams_service = MicrosoftTeamsService()

        # Get user's Teams meetings
        all_meetings = teams_service.get_user_meetings(request.user)
        today_meetings = [
            m
            for m in all_meetings
            if m.scheduled_start_time.date() == timezone.now().date()
        ]
        upcoming_meetings = [
            m for m in all_meetings if m.scheduled_start_time > timezone.now()
        ]
        active_meetings = [m for m in all_meetings if m.is_active()]

        return Response(
            {
                "today_meetings": len(today_meetings),
                "upcoming_meetings": len(upcoming_meetings),
                "active_meetings": len(active_meetings),
                "recent_meetings": MeetingSessionSerializer(
                    all_meetings[:5], many=True
                ).data,
                "teams_auth_status": True,  # If we reach here, user has valid credentials
            }
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Unified Meeting Interface


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_unified_meeting(request):
    """Create a meeting using either Google Meet or Microsoft Teams based on user preference"""
    try:
        meeting_type = request.data.get("meeting_type", "google_meet")

        if meeting_type == "microsoft_teams":
            serializer = CreateTeamsMeetingSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            teams_service = MicrosoftTeamsService()
            meeting_session = teams_service.create_meeting(
                user=request.user,
                title=serializer.validated_data["title"],
                description=serializer.validated_data.get("description", ""),
                start_time=serializer.validated_data["scheduled_start_time"],
                end_time=serializer.validated_data["scheduled_end_time"],
                attendee_emails=serializer.validated_data.get("attendee_emails", []),
            )
        else:
            # Default to Google Meet (existing functionality)
            from .google_meet_service import GoogleMeetService
            from .serializers import CreateMeetingSerializer

            serializer = CreateMeetingSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            google_service = GoogleMeetService()
            meeting_session = google_service.create_meeting(
                user=request.user,
                title=serializer.validated_data["title"],
                description=serializer.validated_data.get("description", ""),
                start_time=serializer.validated_data["scheduled_start_time"],
                end_time=serializer.validated_data["scheduled_end_time"],
                attendee_emails=serializer.validated_data.get("attendee_emails", []),
            )

        if meeting_session:
            meeting_serializer = MeetingSessionSerializer(meeting_session)
            return Response(meeting_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {"error": f"Failed to create {meeting_type} meeting"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def unified_meeting_dashboard(request):
    """Get unified dashboard data for both Google Meet and Teams meetings"""
    try:
        from .google_meet_service import GoogleMeetService

        google_service = GoogleMeetService()
        teams_service = MicrosoftTeamsService()

        # Get meetings from both services
        google_meetings = google_service.get_user_meetings(request.user)
        teams_meetings = teams_service.get_user_meetings(request.user)

        # Combine and sort by date
        all_meetings = google_meetings + teams_meetings
        all_meetings.sort(key=lambda x: x.scheduled_start_time, reverse=True)

        # Calculate statistics
        today = timezone.now().date()
        now = timezone.now()

        today_meetings = [
            m for m in all_meetings if m.scheduled_start_time.date() == today
        ]
        upcoming_meetings = [m for m in all_meetings if m.scheduled_start_time > now]
        active_meetings = [m for m in all_meetings if m.is_active()]

        # Check authentication status
        google_auth = False
        teams_auth = False

        try:
            from .models import GoogleMeetCredentials

            google_creds = GoogleMeetCredentials.objects.get(user=request.user)
            google_auth = not google_creds.is_token_expired()
        except GoogleMeetCredentials.DoesNotExist:
            pass

        try:
            teams_creds = MicrosoftTeamsCredentials.objects.get(user=request.user)
            teams_auth = not teams_creds.is_token_expired()
        except MicrosoftTeamsCredentials.DoesNotExist:
            pass

        return Response(
            {
                "today_meetings": len(today_meetings),
                "upcoming_meetings": len(upcoming_meetings),
                "active_meetings": len(active_meetings),
                "recent_meetings": MeetingSessionSerializer(
                    all_meetings[:10], many=True
                ).data,
                "google_auth_status": google_auth,
                "teams_auth_status": teams_auth,
                "total_meetings": len(all_meetings),
            }
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Intelligent Meeting Management Views

from django.utils.dateparse import parse_datetime

from .intelligent_meeting_service import IntelligentMeetingService


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def analyze_user_availability(request):
    """Analyze user's meeting patterns and availability"""
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

        intelligent_service = IntelligentMeetingService()
        availability = intelligent_service.analyze_user_availability(
            request.user, (start_date, end_date)
        )

        return Response(
            {
                "availability": availability,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
            }
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def recommend_meeting_time(request):
    """Get recommended meeting times based on user patterns"""
    try:
        duration_minutes = request.data.get("duration_minutes", 60)
        preferred_date_str = request.data.get("preferred_date")

        preferred_date = None
        if preferred_date_str:
            preferred_date = parse_datetime(preferred_date_str)

        intelligent_service = IntelligentMeetingService()
        recommendations = intelligent_service.recommend_meeting_time(
            request.user, duration_minutes, preferred_date
        )

        return Response(
            {
                "recommendations": recommendations,
                "criteria": {
                    "duration_minutes": duration_minutes,
                    "preferred_date": (
                        preferred_date.isoformat() if preferred_date else None
                    ),
                },
            }
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def detect_meeting_conflicts(request):
    """Detect conflicts with a proposed meeting time"""
    try:
        start_time_str = request.data.get("start_time")
        end_time_str = request.data.get("end_time")

        if not start_time_str or not end_time_str:
            return Response(
                {"error": "start_time and end_time are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_time = parse_datetime(start_time_str)
        end_time = parse_datetime(end_time_str)

        proposed_meeting = {"start_time": start_time, "end_time": end_time}

        intelligent_service = IntelligentMeetingService()
        conflicts = intelligent_service.detect_meeting_conflicts(
            request.user, proposed_meeting
        )

        return Response(
            {
                "conflicts": conflicts,
                "has_conflicts": len(conflicts) > 0,
                "proposed_meeting": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                },
            }
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def suggest_reschedule_options(request):
    """Suggest alternative times for a conflicted meeting"""
    try:
        meeting_id = request.data.get("meeting_id")

        if not meeting_id:
            return Response(
                {"error": "meeting_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            meeting = MeetingSession.objects.get(id=meeting_id, organizer=request.user)
        except MeetingSession.DoesNotExist:
            return Response(
                {"error": "Meeting not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        intelligent_service = IntelligentMeetingService()
        alternatives = intelligent_service.suggest_reschedule_options(
            request.user, meeting
        )

        return Response(
            {
                "alternatives": alternatives,
                "original_meeting": {
                    "id": str(meeting.id),
                    "title": meeting.title,
                    "start_time": meeting.scheduled_start_time.isoformat(),
                    "end_time": meeting.scheduled_end_time.isoformat(),
                },
            }
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def schedule_post_meeting_followup(request):
    """Schedule intelligent follow-up actions after a meeting"""
    try:
        meeting_id = request.data.get("meeting_id")

        if not meeting_id:
            return Response(
                {"error": "meeting_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            meeting = MeetingSession.objects.get(
                id=meeting_id,
                organizer=request.user,
                status=MeetingSession.Status.ENDED,
            )
        except MeetingSession.DoesNotExist:
            return Response(
                {"error": "Ended meeting not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        intelligent_service = IntelligentMeetingService()
        success = intelligent_service.schedule_post_meeting_follow_up(meeting)

        if success:
            return Response(
                {
                    "message": "Follow-up scheduled successfully",
                    "meeting_id": str(meeting.id),
                }
            )
        else:
            return Response(
                {"error": "Failed to schedule follow-up"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def analyze_meeting_patterns(request):
    """Analyze user's meeting patterns for optimization"""
    try:
        days_back = int(request.GET.get("days_back", 30))

        intelligent_service = IntelligentMeetingService()
        patterns = intelligent_service.analyze_meeting_patterns(request.user, days_back)

        return Response({"patterns": patterns, "analysis_period_days": days_back})

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_calendar_sync_status(request):
    """Get the status of calendar integrations"""
    try:
        intelligent_service = IntelligentMeetingService()
        sync_status = intelligent_service.get_calendar_sync_status(request.user)

        return Response({"sync_status": sync_status})

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def intelligent_meeting_dashboard(request):
    """Get comprehensive intelligent meeting dashboard data"""
    try:
        intelligent_service = IntelligentMeetingService()

        # Get availability for next 7 days
        start_date = timezone.now()
        end_date = start_date + timedelta(days=7)
        availability = intelligent_service.analyze_user_availability(
            request.user, (start_date, end_date)
        )

        # Get meeting patterns for last 30 days
        patterns = intelligent_service.analyze_meeting_patterns(request.user, 30)

        # Get calendar sync status
        sync_status = intelligent_service.get_calendar_sync_status(request.user)

        # Get meeting recommendations for tomorrow
        tomorrow = timezone.now() + timedelta(days=1)
        recommendations = intelligent_service.recommend_meeting_time(
            request.user, 60, tomorrow
        )

        return Response(
            {
                "availability": availability,
                "patterns": patterns,
                "sync_status": sync_status,
                "recommendations": recommendations[:3],  # Top 3 recommendations
                "dashboard_generated_at": timezone.now().isoformat(),
            }
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Live Meeting Support Views

from .live_meeting_support import LiveMeetingSupportService


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def start_live_meeting_session(request):
    """Start a live meeting session for real-time analysis"""
    try:
        meeting_id = request.data.get("meeting_id")

        if not meeting_id:
            return Response(
                {"error": "meeting_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        live_service = LiveMeetingSupportService()
        result = live_service.start_live_meeting_session(
            meeting_id, str(request.user.id)
        )

        if result["success"]:
            return Response(result, status=status.HTTP_201_CREATED)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def process_conversation_turn(request):
    """Process a new conversation turn and get real-time analysis"""
    try:
        session_id = request.data.get("session_id")
        speaker = request.data.get("speaker")  # 'user' or 'prospect'
        content = request.data.get("content")

        if not all([session_id, speaker, content]):
            return Response(
                {"error": "session_id, speaker, and content are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if speaker not in ["user", "prospect"]:
            return Response(
                {"error": 'speaker must be either "user" or "prospect"'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        live_service = LiveMeetingSupportService()
        result = live_service.process_conversation_turn(session_id, speaker, content)

        if result["success"]:
            return Response(result)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_real_time_suggestions(request):
    """Get current real-time suggestions for the meeting"""
    try:
        session_id = request.GET.get("session_id")

        if not session_id:
            return Response(
                {"error": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        live_service = LiveMeetingSupportService()
        result = live_service.get_real_time_suggestions(session_id)

        if result["success"]:
            return Response(result)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_meeting_guidance(request):
    """Get AI meeting guidance for current session"""
    try:
        session_id = request.GET.get("session_id")

        if not session_id:
            return Response(
                {"error": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        live_service = LiveMeetingSupportService()
        result = live_service.get_real_time_suggestions(session_id)

        if result["success"]:
            # Extract meeting guidance from the session
            from django.core.cache import cache

            session_data = cache.get(session_id)

            if session_data:
                # Get recent conversation turns for guidance generation
                recent_turns = [
                    live_service.ConversationTurn(**turn_data)
                    for turn_data in session_data["conversation_turns"][-10:]
                ]

                if recent_turns:
                    meeting_id = session_data["meeting_id"]
                    meeting = Meeting.objects.get(id=meeting_id)
                    meeting_context = {
                        "meeting_type": meeting.meeting_type,
                        "lead_info": live_service._get_lead_context(meeting.lead),
                        "ai_insights": live_service._get_ai_insights_context(
                            meeting.lead
                        ),
                    }

                    # Generate meeting guidance
                    guidance = live_service.generate_meeting_guidance(
                        recent_turns, meeting_context
                    )

                    return Response(
                        {
                            "success": True,
                            "objection_handling": [
                                asdict(advice) for advice in guidance.objection_advice
                            ],
                            "closing_opportunities": [
                                asdict(opp) for opp in guidance.closing_opportunities
                            ],
                            "follow_up_recommendations": [
                                asdict(rec)
                                for rec in guidance.follow_up_recommendations
                            ],
                            "intervention_alerts": [
                                asdict(alert) for alert in guidance.intervention_alerts
                            ],
                            "overall_meeting_health": guidance.overall_meeting_health,
                            "guidance_timestamp": guidance.guidance_timestamp.isoformat(),
                        }
                    )

            return Response(
                {
                    "success": True,
                    "objection_handling": [],
                    "closing_opportunities": [],
                    "follow_up_recommendations": [],
                    "intervention_alerts": [],
                    "overall_meeting_health": "unknown",
                }
            )
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def handle_objection(request):
    """Get AI advice for handling a specific objection"""
    try:
        objection_text = request.data.get("objection_text")
        objection_type = request.data.get("objection_type", "general")
        session_id = request.data.get("session_id")

        if not objection_text:
            return Response(
                {"error": "objection_text is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        live_service = LiveMeetingSupportService()

        # Create a mock conversation turn for the objection
        objection_turn = live_service.ConversationTurn(
            timestamp=timezone.now(), speaker="prospect", content=objection_text
        )

        # Get meeting context if session_id provided
        meeting_context = {"meeting_type": "discovery"}
        if session_id:
            from django.core.cache import cache

            session_data = cache.get(session_id)
            if session_data:
                meeting_id = session_data["meeting_id"]
                meeting = Meeting.objects.get(id=meeting_id)
                meeting_context = {
                    "meeting_type": meeting.meeting_type,
                    "lead_info": live_service._get_lead_context(meeting.lead),
                }

        # Generate objection handling advice
        guidance = live_service.generate_meeting_guidance(
            [objection_turn], meeting_context
        )

        return Response(
            {
                "success": True,
                "objection_handling_advice": [
                    asdict(advice) for advice in guidance.objection_advice
                ],
                "recommended_responses": [
                    advice.recommended_response for advice in guidance.objection_advice
                ],
                "alternative_approaches": [
                    advice.alternative_approaches
                    for advice in guidance.objection_advice
                    if advice.alternative_approaches
                ],
            }
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def identify_closing_opportunity(request):
    """Identify closing opportunities in current conversation"""
    try:
        session_id = request.data.get("session_id")
        conversation_context = request.data.get("conversation_context", "")

        if not session_id:
            return Response(
                {"error": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        live_service = LiveMeetingSupportService()
        from django.core.cache import cache

        session_data = cache.get(session_id)

        if not session_data:
            return Response(
                {"error": "Session not found or expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get recent conversation turns
        recent_turns = [
            live_service.ConversationTurn(**turn_data)
            for turn_data in session_data["conversation_turns"][-5:]  # Last 5 turns
        ]

        if conversation_context:
            # Add the current context as a turn
            context_turn = live_service.ConversationTurn(
                timestamp=timezone.now(),
                speaker="prospect",
                content=conversation_context,
            )
            recent_turns.append(context_turn)

        # Get meeting context
        meeting_id = session_data["meeting_id"]
        meeting = Meeting.objects.get(id=meeting_id)
        meeting_context = {
            "meeting_type": meeting.meeting_type,
            "lead_info": live_service._get_lead_context(meeting.lead),
        }

        # Generate meeting guidance focused on closing
        guidance = live_service.generate_meeting_guidance(recent_turns, meeting_context)

        return Response(
            {
                "success": True,
                "closing_opportunities": [
                    asdict(opp) for opp in guidance.closing_opportunities
                ],
                "recommended_techniques": [
                    opp.recommended_closing_technique
                    for opp in guidance.closing_opportunities
                ],
                "closing_questions": [
                    opp.closing_questions
                    for opp in guidance.closing_opportunities
                    if opp.closing_questions
                ],
                "timing_recommendations": [
                    opp.timing_recommendation for opp in guidance.closing_opportunities
                ],
            }
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def get_follow_up_recommendations(request):
    """Get AI recommendations for follow-up actions"""
    try:
        session_id = request.data.get("session_id")
        meeting_outcome = request.data.get("meeting_outcome", "ongoing")

        if not session_id:
            return Response(
                {"error": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        live_service = LiveMeetingSupportService()
        from django.core.cache import cache

        session_data = cache.get(session_id)

        if not session_data:
            return Response(
                {"error": "Session not found or expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get all conversation turns
        conversation_turns = [
            live_service.ConversationTurn(**turn_data)
            for turn_data in session_data["conversation_turns"]
        ]

        # Get meeting context
        meeting_id = session_data["meeting_id"]
        meeting = Meeting.objects.get(id=meeting_id)
        meeting_context = {
            "meeting_type": meeting.meeting_type,
            "lead_info": live_service._get_lead_context(meeting.lead),
            "meeting_outcome": meeting_outcome,
        }

        # Generate meeting guidance focused on follow-up
        guidance = live_service.generate_meeting_guidance(
            conversation_turns, meeting_context
        )

        return Response(
            {
                "success": True,
                "follow_up_recommendations": [
                    asdict(rec) for rec in guidance.follow_up_recommendations
                ],
                "high_priority_actions": [
                    asdict(rec)
                    for rec in guidance.follow_up_recommendations
                    if rec.priority == "high"
                ],
                "immediate_actions": [
                    asdict(rec)
                    for rec in guidance.follow_up_recommendations
                    if rec.recommended_timing in ["immediate", "same_day"]
                ],
            }
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def check_intervention_alerts(request):
    """Check for intervention alerts in current meeting"""
    try:
        session_id = request.GET.get("session_id")

        if not session_id:
            return Response(
                {"error": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        live_service = LiveMeetingSupportService()
        from django.core.cache import cache

        session_data = cache.get(session_id)

        if not session_data:
            return Response(
                {"error": "Session not found or expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get recent conversation turns
        recent_turns = [
            live_service.ConversationTurn(**turn_data)
            for turn_data in session_data["conversation_turns"][-8:]  # Last 8 turns
        ]

        if not recent_turns:
            return Response(
                {
                    "success": True,
                    "intervention_alerts": [],
                    "requires_intervention": False,
                }
            )

        # Get meeting context
        meeting_id = session_data["meeting_id"]
        meeting = Meeting.objects.get(id=meeting_id)
        meeting_context = {
            "meeting_type": meeting.meeting_type,
            "lead_info": live_service._get_lead_context(meeting.lead),
        }

        # Generate meeting guidance focused on intervention alerts
        guidance = live_service.generate_meeting_guidance(recent_turns, meeting_context)

        # Check for critical alerts
        critical_alerts = [
            alert
            for alert in guidance.intervention_alerts
            if alert.severity in ["high", "critical"]
        ]

        return Response(
            {
                "success": True,
                "intervention_alerts": [
                    asdict(alert) for alert in guidance.intervention_alerts
                ],
                "critical_alerts": [asdict(alert) for alert in critical_alerts],
                "requires_intervention": len(critical_alerts) > 0,
                "overall_meeting_health": guidance.overall_meeting_health,
                "alert_count": len(guidance.intervention_alerts),
            }
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def analyze_conversation_sentiment(request):
    """Analyze sentiment of conversation segment"""
    try:
        session_id = request.data.get("session_id")
        conversation_text = request.data.get("conversation_text")

        if not session_id:
            return Response(
                {"error": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        live_service = LiveMeetingSupportService()

        # If conversation_text provided, analyze it directly
        if conversation_text:
            from django.utils import timezone

            from .live_meeting_support import ConversationTurn

            # Create temporary conversation turn for analysis
            conversation_turns = [
                ConversationTurn(
                    timestamp=timezone.now(), speaker="mixed", content=conversation_text
                )
            ]

            sentiment_analysis = live_service.analyze_conversation_sentiment(
                conversation_turns
            )

            return Response(
                {
                    "success": True,
                    "sentiment_analysis": {
                        "overall_sentiment": sentiment_analysis.overall_sentiment,
                        "sentiment_score": sentiment_analysis.sentiment_score,
                        "engagement_level": sentiment_analysis.engagement_level,
                        "engagement_score": sentiment_analysis.engagement_score,
                        "emotional_indicators": sentiment_analysis.emotional_indicators,
                        "confidence_level": sentiment_analysis.confidence_level,
                    },
                }
            )
        else:
            # Get sentiment from current session
            result = live_service.get_real_time_suggestions(session_id)
            if result["success"]:
                return Response(
                    {"success": True, "sentiment_analysis": result.get("sentiment", {})}
                )
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def identify_key_moments(request):
    """Identify key moments in conversation segment"""
    try:
        session_id = request.data.get("session_id")
        conversation_text = request.data.get("conversation_text")
        meeting_id = request.data.get("meeting_id")

        if not conversation_text:
            return Response(
                {"error": "conversation_text is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        live_service = LiveMeetingSupportService()

        # Create temporary conversation turns for analysis
        from django.utils import timezone

        from .live_meeting_support import ConversationTurn

        conversation_turns = [
            ConversationTurn(
                timestamp=timezone.now(), speaker="mixed", content=conversation_text
            )
        ]

        # Get meeting context if meeting_id provided
        meeting_context = {}
        if meeting_id:
            try:
                meeting = Meeting.objects.get(id=meeting_id)
                meeting_context = {
                    "meeting_type": meeting.meeting_type,
                    "company_name": meeting.lead.company_name,
                    "industry": meeting.lead.industry,
                }
            except Meeting.DoesNotExist:
                pass

        key_moments = live_service.identify_key_moments(
            conversation_turns, meeting_context
        )

        return Response(
            {
                "success": True,
                "key_moments": [
                    {
                        "moment_type": moment.moment_type,
                        "description": moment.description,
                        "importance_score": moment.importance_score,
                        "context": moment.context,
                        "suggested_response": moment.suggested_response,
                        "follow_up_actions": moment.follow_up_actions,
                        "timestamp": moment.timestamp.isoformat(),
                    }
                    for moment in key_moments
                ],
            }
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_question_suggestions(request):
    """Generate next question suggestions based on conversation flow"""
    try:
        session_id = request.data.get("session_id")
        conversation_text = request.data.get("conversation_text")
        meeting_id = request.data.get("meeting_id")

        if not conversation_text:
            return Response(
                {"error": "conversation_text is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        live_service = LiveMeetingSupportService()

        # Create temporary conversation turns for analysis
        from django.utils import timezone

        from .live_meeting_support import ConversationTurn

        conversation_turns = [
            ConversationTurn(
                timestamp=timezone.now(), speaker="mixed", content=conversation_text
            )
        ]

        # Get meeting context
        meeting_context = {}
        if meeting_id:
            try:
                meeting = Meeting.objects.get(id=meeting_id)
                meeting_context = {
                    "meeting_type": meeting.meeting_type,
                    "company_name": meeting.lead.company_name,
                    "industry": meeting.lead.industry,
                    "lead_info": {
                        "company_name": meeting.lead.company_name,
                        "industry": meeting.lead.industry,
                        "pain_points": meeting.lead.pain_points,
                        "requirements": meeting.lead.requirements,
                        "budget_info": meeting.lead.budget_info,
                        "timeline": meeting.lead.timeline,
                        "decision_makers": meeting.lead.decision_makers,
                    },
                }
            except Meeting.DoesNotExist:
                pass

        question_suggestions = live_service.generate_next_question_suggestions(
            conversation_turns, meeting_context
        )

        return Response(
            {
                "success": True,
                "question_suggestions": [
                    {
                        "question_text": suggestion.question_text,
                        "question_type": suggestion.question_type,
                        "priority_score": suggestion.priority_score,
                        "rationale": suggestion.rationale,
                        "timing_suggestion": suggestion.timing_suggestion,
                        "expected_outcome": suggestion.expected_outcome,
                        "follow_up_questions": suggestion.follow_up_questions,
                    }
                    for suggestion in question_suggestions
                ],
            }
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def end_live_meeting_session(request):
    """End the live meeting session and generate final summary"""
    try:
        session_id = request.data.get("session_id")

        if not session_id:
            return Response(
                {"error": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        live_service = LiveMeetingSupportService()
        result = live_service.end_live_meeting_session(session_id)

        if result["success"]:
            return Response(result)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_live_meeting_status(request):
    """Get status of all active live meeting sessions for the user"""
    try:
        from django.core.cache import cache

        # Get all cache keys for live meetings (this is a simplified approach)
        # In production, you might want to maintain a separate index of active sessions
        user_meetings = Meeting.objects.filter(
            lead__user=request.user, status=Meeting.Status.IN_PROGRESS
        )

        active_sessions = []
        for meeting in user_meetings:
            session_key = f"live_meeting_{meeting.id}"
            session_data = cache.get(session_key)

            if session_data:
                active_sessions.append(
                    {
                        "session_id": session_key,
                        "meeting_id": str(meeting.id),
                        "meeting_title": meeting.title,
                        "company_name": meeting.lead.company_name,
                        "start_time": session_data.get("start_time"),
                        "conversation_turns": len(
                            session_data.get("conversation_turns", [])
                        ),
                        "last_activity": session_data.get("last_analysis_time"),
                    }
                )

        return Response(
            {
                "success": True,
                "active_sessions": active_sessions,
                "total_active": len(active_sessions),
            }
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# NIA Meeting Scheduler Views

from .nia_meeting_scheduler import NIAMeetingScheduler, NIAMeetingType


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_nia_available_slots(request):
    """Get available time slots for NIA meetings"""
    try:
        # Get parameters
        start_date_str = request.GET.get("start_date")
        end_date_str = request.GET.get("end_date")
        meeting_type_str = request.GET.get("meeting_type", "general_consultation")

        if not start_date_str or not end_date_str:
            # Default to next 7 days
            start_date = timezone.now()
            end_date = start_date + timedelta(days=7)
        else:
            start_date = parse_datetime(start_date_str)
            end_date = parse_datetime(end_date_str)

        try:
            meeting_type = NIAMeetingType(meeting_type_str)
        except ValueError:
            meeting_type = NIAMeetingType.GENERAL_CONSULTATION

        nia_scheduler = NIAMeetingScheduler()
        available_slots = nia_scheduler.get_available_time_slots(
            request.user, (start_date, end_date), meeting_type
        )

        return Response(
            {
                "available_slots": available_slots,
                "meeting_type": meeting_type.value,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
            }
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def schedule_nia_meeting(request):
    """Schedule a meeting with NIA"""
    try:
        # Validate required fields
        start_time_str = request.data.get("start_time")
        meeting_type_str = request.data.get("meeting_type", "general_consultation")
        platform = request.data.get("platform", "google_meet")
        lead_id = request.data.get("lead_id")

        if not start_time_str:
            return Response(
                {"error": "start_time is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        start_time = parse_datetime(start_time_str)

        try:
            meeting_type = NIAMeetingType(meeting_type_str)
        except ValueError:
            return Response(
                {"error": f"Invalid meeting type: {meeting_type_str}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Prepare meeting data
        meeting_data = {
            "start_time": start_time,
            "meeting_type": meeting_type.value,
            "platform": platform,
            "lead_id": lead_id,
        }

        nia_scheduler = NIAMeetingScheduler()
        meeting_session = nia_scheduler.schedule_nia_meeting(request.user, meeting_data)

        if meeting_session:
            meeting_serializer = MeetingSessionSerializer(meeting_session)
            return Response(
                {
                    "meeting": meeting_serializer.data,
                    "message": "NIA meeting scheduled successfully",
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {"error": "Failed to schedule NIA meeting"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# AI Question Generation and Admin Views


@staff_member_required
@require_POST
@csrf_exempt
def mark_question_asked(request, question_id):
    """Admin view to mark a question as asked"""
    try:
        question = get_object_or_404(MeetingQuestion, id=question_id)
        response_text = request.POST.get("response", "")

        question.mark_as_asked(response_text)

        return JsonResponse(
            {
                "success": True,
                "message": "Question marked as asked successfully",
                "asked_at": (
                    question.asked_at.isoformat() if question.asked_at else None
                ),
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@staff_member_required
@require_POST
@csrf_exempt
def toggle_question_override(request, question_id):
    """Admin view to toggle manual override for a question"""
    try:
        question = get_object_or_404(MeetingQuestion, id=question_id)

        # Toggle AI generated status
        question.ai_generated = not question.ai_generated
        question.created_by = request.user if not question.ai_generated else None
        question.save(update_fields=["ai_generated", "created_by", "updated_at"])

        return JsonResponse(
            {
                "success": True,
                "message": f'Question {"manually overridden" if not question.ai_generated else "reset to AI-generated"}',
                "ai_generated": question.ai_generated,
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@staff_member_required
@require_POST
@csrf_exempt
def update_question_effectiveness(request, question_id):
    """Admin view to update question effectiveness score"""
    try:
        question = get_object_or_404(MeetingQuestion, id=question_id)
        effectiveness_score = float(request.POST.get("effectiveness_score", 0))

        if not (0 <= effectiveness_score <= 100):
            return JsonResponse(
                {
                    "success": False,
                    "error": "Effectiveness score must be between 0 and 100",
                },
                status=400,
            )

        question.effectiveness_score = effectiveness_score
        question.save(update_fields=["effectiveness_score", "updated_at"])

        return JsonResponse(
            {
                "success": True,
                "message": "Question effectiveness updated successfully",
                "effectiveness_score": effectiveness_score,
            }
        )
    except ValueError:
        return JsonResponse(
            {"success": False, "error": "Invalid effectiveness score format"},
            status=400,
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@staff_member_required
@require_POST
@csrf_exempt
def generate_meeting_questions(request, meeting_id):
    """Admin view to generate AI questions for a meeting"""
    try:
        meeting = get_object_or_404(Meeting, id=meeting_id)

        # Use the question service to generate questions
        question_service = MeetingQuestionService()
        questions = question_service.generate_questions_for_meeting(meeting)

        return JsonResponse(
            {
                "success": True,
                "message": f"Generated {len(questions)} questions for meeting",
                "questions_count": len(questions),
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@staff_member_required
@require_POST
@csrf_exempt
def regenerate_meeting_questions(request, meeting_id):
    """Admin view to regenerate all AI questions for a meeting"""
    try:
        meeting = get_object_or_404(Meeting, id=meeting_id)

        # Delete existing AI-generated questions
        deleted_count = meeting.questions.filter(ai_generated=True).delete()[0]

        # Generate new questions
        question_service = MeetingQuestionService()
        questions = question_service.generate_questions_for_meeting(meeting)

        return JsonResponse(
            {
                "success": True,
                "message": f"Regenerated questions: deleted {deleted_count}, created {len(questions)}",
                "deleted_count": deleted_count,
                "created_count": len(questions),
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@staff_member_required
@require_POST
@csrf_exempt
def bulk_update_question_priority(request):
    """Admin view to bulk update question priorities"""
    try:
        question_ids = request.POST.getlist("question_ids")
        new_priority = int(request.POST.get("new_priority", 5))

        if not (1 <= new_priority <= 10):
            return JsonResponse(
                {"success": False, "error": "Priority must be between 1 and 10"},
                status=400,
            )

        updated_count = MeetingQuestion.objects.filter(id__in=question_ids).update(
            priority=new_priority
        )

        return JsonResponse(
            {
                "success": True,
                "message": f"Updated priority for {updated_count} questions",
                "updated_count": updated_count,
                "new_priority": new_priority,
            }
        )
    except ValueError:
        return JsonResponse(
            {"success": False, "error": "Invalid priority format"}, status=400
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@staff_member_required
def export_question_analytics(request):
    """Admin view to export question analytics"""
    try:
        import csv
        from datetime import datetime

        from django.http import HttpResponse

        # Create CSV response
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="question_analytics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        )

        writer = csv.writer(response)

        # Write header
        writer.writerow(
            [
                "Question ID",
                "Meeting Title",
                "Company",
                "Question Type",
                "Question Text",
                "Priority",
                "AI Generated",
                "Asked At",
                "Response Length",
                "Effectiveness Score",
                "Led to Qualification",
                "Led to Objection",
                "Confidence Score",
            ]
        )

        # Write data
        questions = MeetingQuestion.objects.select_related(
            "meeting", "meeting__lead"
        ).all()

        for question in questions:
            writer.writerow(
                [
                    str(question.id),
                    question.meeting.title,
                    question.meeting.lead.company_name if question.meeting.lead else "",
                    question.get_question_type_display(),
                    (
                        question.question_text[:100] + "..."
                        if len(question.question_text) > 100
                        else question.question_text
                    ),
                    question.priority,
                    "Yes" if question.ai_generated else "No",
                    (
                        question.asked_at.strftime("%Y-%m-%d %H:%M:%S")
                        if question.asked_at
                        else ""
                    ),
                    len(question.response.split()) if question.response else 0,
                    question.effectiveness_score or 0,
                    "Yes" if question.led_to_qualification else "No",
                    "Yes" if question.led_to_objection else "No",
                    question.confidence_score,
                ]
            )

        return response
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# Question Template Admin Views


@staff_member_required
def question_template_test(request, template_id):
    """Admin view to test a question template"""
    try:
        from .models import QuestionTemplate

        template = get_object_or_404(QuestionTemplate, id=template_id)

        # Sample data for testing
        sample_data = {
            "company_name": "Acme Corporation",
            "industry": template.industry,
            "contact_name": "John Smith",
            "pain_point": "inefficient processes",
            "current_solution": "manual spreadsheets",
            "budget_range": "$50K - $100K",
            "timeline": "3-6 months",
            "decision_maker": "CTO",
        }

        # Generate test question
        test_question = template.question_template
        for key, value in sample_data.items():
            test_question = test_question.replace(f"{{{key}}}", str(value))

        context = {
            "template": template,
            "test_question": test_question,
            "sample_data": sample_data,
            "variables": template.variables,
        }

        return render(
            request,
            "admin/meeting_service/questiontemplate/test_template.html",
            context,
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@staff_member_required
@require_POST
@csrf_exempt
def duplicate_question_template(request, template_id):
    """Admin view to duplicate a question template"""
    try:
        from .models import QuestionTemplate

        template = get_object_or_404(QuestionTemplate, id=template_id)

        # Create duplicate
        template.pk = None
        template.name = f"{template.name} (Copy)"
        template.usage_count = 0
        template.success_rate = 0.0
        template.created_by = request.user
        template.save()

        return JsonResponse(
            {
                "success": True,
                "message": "Template duplicated successfully",
                "new_template_id": str(template.id),
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@staff_member_required
def question_template_analytics(request, template_id):
    """Admin view to show detailed template analytics"""
    try:
        from .models import QuestionTemplate

        template = get_object_or_404(QuestionTemplate, id=template_id)

        # Get questions generated from this template
        questions = MeetingQuestion.objects.filter(
            generation_context__template_id=str(template_id)
        ).select_related("meeting", "meeting__lead")

        # Calculate analytics
        total_questions = questions.count()
        asked_questions = questions.filter(asked_at__isnull=False).count()
        effective_questions = questions.filter(effectiveness_score__gte=70).count()

        avg_effectiveness = (
            questions.filter(effectiveness_score__isnull=False).aggregate(
                avg_score=models.Avg("effectiveness_score")
            )["avg_score"]
            or 0
        )

        # Performance by industry/meeting type
        performance_by_type = (
            questions.values("meeting__meeting_type")
            .annotate(
                count=models.Count("id"),
                avg_effectiveness=models.Avg("effectiveness_score"),
            )
            .order_by("-count")
        )

        context = {
            "template": template,
            "total_questions": total_questions,
            "asked_questions": asked_questions,
            "effective_questions": effective_questions,
            "avg_effectiveness": avg_effectiveness,
            "performance_by_type": performance_by_type,
            "recent_questions": questions.order_by("-created_at")[:10],
        }

        return render(
            request, "admin/meeting_service/questiontemplate/analytics.html", context
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# Meeting Admin Action Views


@staff_member_required
@require_POST
@csrf_exempt
def start_meeting_admin(request, meeting_id):
    """Admin action to start a meeting"""
    try:
        meeting = get_object_or_404(Meeting, id=meeting_id)
        meeting.mark_as_started()

        return JsonResponse(
            {
                "success": True,
                "message": "Meeting started successfully",
                "status": meeting.get_status_display(),
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@staff_member_required
@require_POST
@csrf_exempt
def complete_meeting_admin(request, meeting_id):
    """Admin action to complete a meeting"""
    try:
        meeting = get_object_or_404(Meeting, id=meeting_id)
        meeting.mark_as_completed()

        return JsonResponse(
            {
                "success": True,
                "message": "Meeting completed successfully",
                "status": meeting.get_status_display(),
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@staff_member_required
@require_POST
@csrf_exempt
def cancel_meeting_admin(request, meeting_id):
    """Admin action to cancel a meeting"""
    try:
        meeting = get_object_or_404(Meeting, id=meeting_id)
        meeting.mark_as_cancelled()

        return JsonResponse(
            {
                "success": True,
                "message": "Meeting cancelled successfully",
                "status": meeting.get_status_display(),
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@staff_member_required
def create_meeting_admin(request):
    """Admin view to create a new meeting"""
    if request.method == "POST":
        try:
            # This would handle meeting creation from admin
            # For now, redirect to standard admin add form
            from django.shortcuts import redirect

            return redirect("admin:meeting_service_meeting_add")
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    else:
        # Show meeting creation form
        from django.shortcuts import redirect

        return redirect("admin:meeting_service_meeting_add")


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_meeting_questions(request, meeting_id):
    """Generate AI-powered questions for a specific meeting"""
    try:
        # Get the meeting
        try:
            meeting = Meeting.objects.get(id=meeting_id)
        except Meeting.DoesNotExist:
            return Response(
                {"error": "Meeting not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if user has access to this meeting (through the lead)
        if meeting.lead.user != request.user:
            return Response(
                {"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN
            )

        # Get regenerate flag
        regenerate = request.data.get("regenerate", False)

        # Initialize question service and generate questions
        question_service = MeetingQuestionService()
        result = question_service.generate_questions_for_meeting(
            meeting, regenerate=regenerate
        )

        if result["success"]:
            return Response(
                {
                    "success": True,
                    "message": f"Successfully generated {result['questions_generated']} questions",
                    "questions_generated": result["questions_generated"],
                    "questions_by_type": result["questions_by_type"],
                    "generation_metadata": result.get("generation_metadata", {}),
                    "meeting_id": str(meeting.id),
                    "meeting_title": meeting.title,
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {
                    "success": False,
                    "error": result.get("error", "Unknown error occurred"),
                    "meeting_id": str(meeting.id),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_meeting_questions(request, meeting_id):
    """Get questions for a specific meeting"""
    try:
        # Get the meeting
        try:
            meeting = Meeting.objects.get(id=meeting_id)
        except Meeting.DoesNotExist:
            return Response(
                {"error": "Meeting not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if user has access to this meeting
        if meeting.lead.user != request.user:
            return Response(
                {"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN
            )

        # Get query parameters
        question_type = request.GET.get("type")
        limit = request.GET.get("limit")
        conversion_focused = request.GET.get("conversion_focused")

        question_service = MeetingQuestionService()

        if conversion_focused == "true":
            questions = question_service.get_conversion_focused_questions(meeting)
        elif question_type:
            questions = question_service.get_questions_by_type(meeting, question_type)
        else:
            questions = question_service.get_prioritized_questions(
                meeting, limit=int(limit) if limit else None
            )

        # Serialize questions
        questions_data = []
        for question in questions:
            questions_data.append(
                {
                    "id": str(question.id),
                    "question_text": question.question_text,
                    "question_type": question.question_type,
                    "question_type_display": question.get_question_type_display(),
                    "priority": question.priority,
                    "priority_level": question.priority_level,
                    "confidence_score": question.confidence_score,
                    "industry_specific": question.industry_specific,
                    "conversion_focused": question.is_conversion_focused,
                    "sequence_order": question.sequence_order,
                    "asked_at": (
                        question.asked_at.isoformat() if question.asked_at else None
                    ),
                    "response": question.response,
                    "generation_context": question.generation_context,
                    "effectiveness_score": question.effectiveness_score,
                    "created_at": question.created_at.isoformat(),
                }
            )

        return Response(
            {
                "questions": questions_data,
                "total_questions": len(questions_data),
                "meeting_id": str(meeting.id),
                "meeting_title": meeting.title,
                "filters_applied": {
                    "question_type": question_type,
                    "limit": limit,
                    "conversion_focused": conversion_focused,
                },
            }
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_question_asked(request, question_id):
    """Mark a question as asked and record response"""
    try:
        # Get the question
        try:
            question = MeetingQuestion.objects.get(id=question_id)
        except MeetingQuestion.DoesNotExist:
            return Response(
                {"error": "Question not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if user has access to this question
        if question.meeting.lead.user != request.user:
            return Response(
                {"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN
            )

        # Get response data
        response_text = request.data.get("response", "")
        response_quality = request.data.get("response_quality", "")

        # Mark question as asked
        question_service = MeetingQuestionService()
        success = question_service.mark_question_asked(
            question, response_text, response_quality
        )

        if success:
            return Response(
                {
                    "success": True,
                    "message": "Question marked as asked successfully",
                    "question_id": str(question.id),
                    "asked_at": (
                        question.asked_at.isoformat() if question.asked_at else None
                    ),
                }
            )
        else:
            return Response(
                {"success": False, "error": "Failed to mark question as asked"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_question_effectiveness(request, question_id):
    """Update question effectiveness based on outcomes"""
    try:
        # Get the question
        try:
            question = MeetingQuestion.objects.get(id=question_id)
        except MeetingQuestion.DoesNotExist:
            return Response(
                {"error": "Question not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if user has access to this question
        if question.meeting.lead.user != request.user:
            return Response(
                {"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN
            )

        # Get outcome data
        outcome_data = {
            "led_to_qualification": request.data.get("led_to_qualification", False),
            "generated_follow_up": request.data.get("generated_follow_up", False),
            "positive_response": request.data.get("positive_response", False),
            "moved_deal_forward": request.data.get("moved_deal_forward", False),
            "led_to_objection": request.data.get("led_to_objection", False),
        }

        # Update effectiveness
        question_service = MeetingQuestionService()
        success = question_service.update_question_effectiveness(question, outcome_data)

        if success:
            return Response(
                {
                    "success": True,
                    "message": "Question effectiveness updated successfully",
                    "question_id": str(question.id),
                    "effectiveness_score": question.effectiveness_score,
                }
            )
        else:
            return Response(
                {"success": False, "error": "Failed to update question effectiveness"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_meeting_summary(request):
    """Generate post-meeting summary for NIA meeting"""
    try:
        meeting_id = request.data.get("meeting_id")

        if not meeting_id:
            return Response(
                {"error": "meeting_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            meeting = MeetingSession.objects.get(
                id=meeting_id,
                organizer=request.user,
                status=MeetingSession.Status.ENDED,
            )
        except MeetingSession.DoesNotExist:
            return Response(
                {"error": "Ended meeting not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        nia_scheduler = NIAMeetingScheduler()
        summary = nia_scheduler.generate_meeting_summary(meeting)

        return Response({"summary": summary, "meeting_id": str(meeting.id)})

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Admin Action Views for Meeting Management


@staff_member_required
@require_POST
@csrf_exempt
def start_meeting_admin(request, meeting_id):
    """Admin action to start a meeting"""
    try:
        meeting = get_object_or_404(Meeting, id=meeting_id)

        if meeting.status != Meeting.Status.SCHEDULED:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Cannot start meeting with status: {meeting.get_status_display()}",
                }
            )

        meeting.mark_as_started()

        return JsonResponse(
            {
                "success": True,
                "message": f'Meeting "{meeting.title}" has been started',
                "new_status": meeting.get_status_display(),
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@staff_member_required
@require_POST
@csrf_exempt
def complete_meeting_admin(request, meeting_id):
    """Admin action to complete a meeting"""
    try:
        meeting = get_object_or_404(Meeting, id=meeting_id)

        if meeting.status != Meeting.Status.IN_PROGRESS:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Cannot complete meeting with status: {meeting.get_status_display()}",
                }
            )

        meeting.mark_as_completed()

        return JsonResponse(
            {
                "success": True,
                "message": f'Meeting "{meeting.title}" has been completed',
                "new_status": meeting.get_status_display(),
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@staff_member_required
@require_POST
@csrf_exempt
def cancel_meeting_admin(request, meeting_id):
    """Admin action to cancel a meeting"""
    try:
        meeting = get_object_or_404(Meeting, id=meeting_id)

        if meeting.status in [Meeting.Status.COMPLETED, Meeting.Status.CANCELLED]:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Cannot cancel meeting with status: {meeting.get_status_display()}",
                }
            )

        meeting.mark_as_cancelled()

        return JsonResponse(
            {
                "success": True,
                "message": f'Meeting "{meeting.title}" has been cancelled',
                "new_status": meeting.get_status_display(),
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@staff_member_required
@require_POST
@csrf_exempt
def create_meeting_admin(request):
    """Admin action to create a new meeting"""
    try:
        data = json.loads(request.body)

        # Get the lead
        from ai_service.models import Lead

        lead = get_object_or_404(Lead, id=data.get("lead"))

        # Create the meeting
        meeting = Meeting.objects.create(
            lead=lead,
            title=data.get("title", f"Meeting with {lead.company_name}"),
            description=data.get("description", ""),
            meeting_type=data.get("meeting_type", "discovery"),
            scheduled_at=data.get("scheduled_at"),
            duration_minutes=data.get("duration_minutes", 60),
            agenda=data.get("agenda", ""),
            status=Meeting.Status.SCHEDULED,
        )

        return JsonResponse(
            {
                "success": True,
                "message": f'Meeting "{meeting.title}" has been scheduled',
                "meeting_id": str(meeting.id),
                "meeting_url": f"/admin/meeting_service/meeting/{meeting.id}/change/",
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_nia_meeting_analytics(request):
    """Get analytics for NIA meetings"""
    try:
        # Get date range parameters
        start_date_str = request.GET.get("start_date")
        end_date_str = request.GET.get("end_date")

        date_range = None
        if start_date_str and end_date_str:
            start_date = parse_datetime(start_date_str)
            end_date = parse_datetime(end_date_str)
            date_range = (start_date, end_date)

        nia_scheduler = NIAMeetingScheduler()
        analytics = nia_scheduler.get_meeting_analytics(request.user, date_range)

        return Response({"analytics": analytics})

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_nia_meeting_types(request):
    """Get available NIA meeting types and their details"""
    try:
        nia_scheduler = NIAMeetingScheduler()

        meeting_types = []
        for meeting_type in NIAMeetingType:
            template = nia_scheduler.meeting_templates[meeting_type]
            meeting_types.append(
                {
                    "type": meeting_type.value,
                    "name": meeting_type.value.replace("_", " ").title(),
                    "duration_minutes": template["duration"],
                    "preparation_items": template["preparation_items"],
                    "description": nia_scheduler._generate_meeting_description(
                        meeting_type, request.user
                    ),
                }
            )

        return Response({"meeting_types": meeting_types})

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def nia_meeting_dashboard(request):
    """Get comprehensive NIA meeting dashboard"""
    try:
        nia_scheduler = NIAMeetingScheduler()

        # Get upcoming NIA meetings
        upcoming_meetings = (
            MeetingSession.objects.filter(
                organizer=request.user,
                scheduled_start_time__gt=timezone.now(),
                status_updates__description__icontains="NIA meeting",
            )
            .distinct()
            .order_by("scheduled_start_time")[:5]
        )

        # Get recent completed meetings
        recent_meetings = (
            MeetingSession.objects.filter(
                organizer=request.user,
                status=MeetingSession.Status.ENDED,
                status_updates__description__icontains="NIA meeting",
            )
            .distinct()
            .order_by("-scheduled_start_time")[:5]
        )

        # Get analytics for last 30 days
        analytics = nia_scheduler.get_meeting_analytics(request.user)

        # Get available slots for next 7 days
        start_date = timezone.now()
        end_date = start_date + timedelta(days=7)
        available_slots = nia_scheduler.get_available_time_slots(
            request.user, (start_date, end_date)
        )

        return Response(
            {
                "upcoming_meetings": MeetingSessionSerializer(
                    upcoming_meetings, many=True
                ).data,
                "recent_meetings": MeetingSessionSerializer(
                    recent_meetings, many=True
                ).data,
                "analytics": analytics,
                "available_slots": available_slots[:3],  # Next 3 available slots
                "dashboard_generated_at": timezone.now().isoformat(),
            }
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Admin Action Endpoints for Meeting Management


@staff_member_required
@require_POST
@csrf_exempt
def admin_start_meeting(request, meeting_id):
    """Admin action to start a meeting"""
    try:
        meeting = get_object_or_404(Meeting, id=meeting_id)

        if meeting.status != Meeting.Status.SCHEDULED:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Cannot start meeting with status: {meeting.get_status_display()}",
                }
            )

        meeting.mark_as_started()

        return JsonResponse(
            {
                "success": True,
                "message": f'Meeting "{meeting.title}" has been started',
                "new_status": meeting.get_status_display(),
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@staff_member_required
@require_POST
@csrf_exempt
def admin_complete_meeting(request, meeting_id):
    """Admin action to complete a meeting"""
    try:
        meeting = get_object_or_404(Meeting, id=meeting_id)

        if meeting.status not in [Meeting.Status.SCHEDULED, Meeting.Status.IN_PROGRESS]:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Cannot complete meeting with status: {meeting.get_status_display()}",
                }
            )

        meeting.mark_as_completed()

        return JsonResponse(
            {
                "success": True,
                "message": f'Meeting "{meeting.title}" has been completed',
                "new_status": meeting.get_status_display(),
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@staff_member_required
@require_POST
@csrf_exempt
def admin_cancel_meeting(request, meeting_id):
    """Admin action to cancel a meeting"""
    try:
        meeting = get_object_or_404(Meeting, id=meeting_id)

        if meeting.status == Meeting.Status.COMPLETED:
            return JsonResponse(
                {"success": False, "error": "Cannot cancel a completed meeting"}
            )

        meeting.mark_as_cancelled()

        return JsonResponse(
            {
                "success": True,
                "message": f'Meeting "{meeting.title}" has been cancelled',
                "new_status": meeting.get_status_display(),
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


# Admin Views for Question Management


@staff_member_required
@require_POST
def mark_question_asked(request, question_id):
    """Admin view to mark a question as asked"""
    try:
        question = get_object_or_404(MeetingQuestion, id=question_id)
        response_text = request.POST.get("response", "")

        question_service = MeetingQuestionService()
        success = question_service.mark_question_asked(question, response_text)

        if success:
            return JsonResponse(
                {"success": True, "message": f"Question marked as asked successfully"}
            )
        else:
            return JsonResponse(
                {"success": False, "error": "Failed to mark question as asked"},
                status=400,
            )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@staff_member_required
@require_POST
def toggle_question_override(request, question_id):
    """Admin view to toggle manual override for a question"""
    try:
        question = get_object_or_404(MeetingQuestion, id=question_id)

        # Toggle the ai_generated flag
        question.ai_generated = not question.ai_generated
        question.created_by = request.user if not question.ai_generated else None
        question.save(update_fields=["ai_generated", "created_by", "updated_at"])

        return JsonResponse(
            {
                "success": True,
                "message": f"Question override toggled successfully",
                "ai_generated": question.ai_generated,
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@staff_member_required
@require_POST
def update_question_effectiveness(request, question_id):
    """Admin view to update question effectiveness score"""
    try:
        question = get_object_or_404(MeetingQuestion, id=question_id)
        effectiveness_score = float(request.POST.get("effectiveness_score", 0))

        if not (0 <= effectiveness_score <= 100):
            return JsonResponse(
                {
                    "success": False,
                    "error": "Effectiveness score must be between 0 and 100",
                },
                status=400,
            )

        question_service = MeetingQuestionService()
        outcome_data = {
            "effectiveness_score": effectiveness_score,
            "led_to_qualification": effectiveness_score >= 70,
            "positive_response": effectiveness_score >= 60,
            "moved_deal_forward": effectiveness_score >= 80,
        }

        success = question_service.update_question_effectiveness(question, outcome_data)

        if success:
            return JsonResponse(
                {
                    "success": True,
                    "message": f"Question effectiveness updated successfully",
                    "effectiveness_score": effectiveness_score,
                }
            )
        else:
            return JsonResponse(
                {"success": False, "error": "Failed to update question effectiveness"},
                status=400,
            )

    except ValueError:
        return JsonResponse(
            {"success": False, "error": "Invalid effectiveness score format"},
            status=400,
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@staff_member_required
@require_POST
def generate_meeting_questions(request, meeting_id):
    """Admin view to generate questions for a meeting"""
    try:
        meeting = get_object_or_404(Meeting, id=meeting_id)

        question_service = MeetingQuestionService()
        result = question_service.generate_questions_for_meeting(
            meeting, regenerate=False
        )

        if result["success"]:
            return JsonResponse(
                {
                    "success": True,
                    "message": f'Generated {result["questions_generated"]} questions successfully',
                    "questions_generated": result["questions_generated"],
                    "questions_by_type": result["questions_by_type"],
                }
            )
        else:
            return JsonResponse(
                {
                    "success": False,
                    "error": result.get("error", "Failed to generate questions"),
                },
                status=400,
            )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@staff_member_required
@require_POST
def regenerate_meeting_questions(request, meeting_id):
    """Admin view to regenerate questions for a meeting"""
    try:
        meeting = get_object_or_404(Meeting, id=meeting_id)

        question_service = MeetingQuestionService()
        result = question_service.generate_questions_for_meeting(
            meeting, regenerate=True
        )

        if result["success"]:
            return JsonResponse(
                {
                    "success": True,
                    "message": f'Regenerated {result["questions_generated"]} questions successfully',
                    "questions_generated": result["questions_generated"],
                    "questions_by_type": result["questions_by_type"],
                }
            )
        else:
            return JsonResponse(
                {
                    "success": False,
                    "error": result.get("error", "Failed to regenerate questions"),
                },
                status=400,
            )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@staff_member_required
def question_template_test(request, template_id):
    """Admin view to test a question template"""
    try:
        from .models import QuestionTemplate

        template = get_object_or_404(QuestionTemplate, id=template_id)

        # Sample data for testing
        sample_data = {
            "company_name": "Acme Corporation",
            "industry": template.industry,
            "contact_name": "John Smith",
            "pain_point": "inefficient processes",
            "current_solution": "manual spreadsheets",
            "budget_range": "$50,000 - $100,000",
            "timeline": "3-6 months",
        }

        # Simple template variable substitution
        test_question = template.question_template
        for var, value in sample_data.items():
            test_question = test_question.replace(f"{{{var}}}", value)

        context = {
            "template": template,
            "test_question": test_question,
            "sample_data": sample_data,
            "variables": template.variables,
        }

        return render(
            request,
            "admin/meeting_service/questiontemplate/test_template.html",
            context,
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@staff_member_required
@require_POST
def duplicate_question_template(request, template_id):
    """Admin view to duplicate a question template"""
    try:
        from .models import QuestionTemplate

        template = get_object_or_404(QuestionTemplate, id=template_id)

        # Create a duplicate
        template.pk = None
        template.name = f"{template.name} (Copy)"
        template.usage_count = 0
        template.success_rate = 0.0
        template.created_by = request.user
        template.save()

        return JsonResponse(
            {
                "success": True,
                "message": f"Template duplicated successfully",
                "new_template_id": str(template.id),
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@staff_member_required
def question_template_analytics(request, template_id):
    """Admin view to show detailed template analytics"""
    try:
        from .models import QuestionTemplate

        template = get_object_or_404(QuestionTemplate, id=template_id)

        # Get questions generated from this template
        questions_from_template = MeetingQuestion.objects.filter(
            generation_context__template_id=str(template_id)
        ).select_related("meeting", "meeting__lead")

        # Calculate analytics
        total_questions = questions_from_template.count()
        asked_questions = questions_from_template.filter(asked_at__isnull=False)
        effective_questions = asked_questions.filter(effectiveness_score__gte=70)

        analytics = {
            "template": template,
            "total_questions_generated": total_questions,
            "questions_asked": asked_questions.count(),
            "effective_questions": effective_questions.count(),
            "ask_rate": (
                (asked_questions.count() / total_questions * 100)
                if total_questions > 0
                else 0
            ),
            "effectiveness_rate": (
                (effective_questions.count() / asked_questions.count() * 100)
                if asked_questions.count() > 0
                else 0
            ),
            "recent_questions": questions_from_template.order_by("-created_at")[:10],
            "performance_by_industry": {},
            "performance_by_meeting_type": {},
        }

        context = {"analytics": analytics}

        return render(
            request, "admin/meeting_service/questiontemplate/analytics.html", context
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@staff_member_required
@require_POST
def bulk_update_question_priority(request):
    """Admin view to bulk update question priorities"""
    try:
        question_ids = request.POST.getlist("question_ids")
        new_priority = int(request.POST.get("new_priority", 5))

        if not (1 <= new_priority <= 10):
            return JsonResponse(
                {"success": False, "error": "Priority must be between 1 and 10"},
                status=400,
            )

        # Determine priority level
        if new_priority >= 8:
            priority_level = MeetingQuestion.Priority.HIGH
        elif new_priority >= 6:
            priority_level = MeetingQuestion.Priority.MEDIUM
        else:
            priority_level = MeetingQuestion.Priority.LOW

        # Update questions
        updated_count = MeetingQuestion.objects.filter(id__in=question_ids).update(
            priority=new_priority, priority_level=priority_level
        )

        return JsonResponse(
            {
                "success": True,
                "message": f"Updated priority for {updated_count} questions",
                "updated_count": updated_count,
            }
        )

    except ValueError:
        return JsonResponse(
            {"success": False, "error": "Invalid priority value"}, status=400
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@staff_member_required
def export_question_analytics(request):
    """Admin view to export question analytics"""
    try:
        import csv

        from django.http import HttpResponse

        # Create CSV response
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="question_analytics.csv"'
        )

        writer = csv.writer(response)
        writer.writerow(
            [
                "Question ID",
                "Meeting",
                "Company",
                "Question Type",
                "Question Text",
                "Priority",
                "Confidence Score",
                "Asked At",
                "Response",
                "Effectiveness Score",
                "Led to Qualification",
                "AI Generated",
                "Created At",
            ]
        )

        # Get all questions with related data
        questions = MeetingQuestion.objects.select_related(
            "meeting", "meeting__lead"
        ).order_by("-created_at")

        for question in questions:
            writer.writerow(
                [
                    str(question.id),
                    question.meeting.title,
                    question.meeting.lead.company_name,
                    question.get_question_type_display(),
                    (
                        question.question_text[:100] + "..."
                        if len(question.question_text) > 100
                        else question.question_text
                    ),
                    question.priority,
                    question.confidence_score,
                    (
                        question.asked_at.strftime("%Y-%m-%d %H:%M:%S")
                        if question.asked_at
                        else ""
                    ),
                    (
                        question.response[:50] + "..."
                        if question.response and len(question.response) > 50
                        else question.response or ""
                    ),
                    question.effectiveness_score or "",
                    "Yes" if question.led_to_qualification else "No",
                    "Yes" if question.ai_generated else "No",
                    question.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                ]
            )

        return response

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# Pre-Meeting Intelligence Generation Views


@staff_member_required
@require_POST
@csrf_exempt
def generate_meeting_intelligence(request, meeting_id):
    """Generate pre-meeting intelligence materials via AJAX for admin interface"""
    try:
        # Parse JSON request body
        data = json.loads(request.body)
        intelligence_type = data.get("type")

        # Get the meeting
        try:
            meeting = Meeting.objects.get(id=meeting_id)
        except Meeting.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Meeting not found"}, status=404
            )

        # Initialize intelligence service
        intelligence_service = PreMeetingIntelligenceService()

        # Generate the requested intelligence type
        if intelligence_type == "preparation_materials":
            result = intelligence_service.generate_preparation_materials(
                meeting, regenerate=True
            )
            message = "Comprehensive preparation materials generated successfully"
        elif intelligence_type == "agenda":
            result = intelligence_service.generate_meeting_agenda(
                meeting, regenerate=True
            )
            message = "Meeting agenda generated successfully"
        elif intelligence_type == "talking_points":
            result = intelligence_service.generate_talking_points(meeting)
            message = "Talking points generated successfully"
        elif intelligence_type == "competitive_analysis":
            result = intelligence_service.generate_competitive_analysis(meeting)
            message = "Competitive analysis generated successfully"
        else:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Unknown intelligence type: {intelligence_type}",
                },
                status=400,
            )

        if result.get("success"):
            return JsonResponse(
                {
                    "success": True,
                    "message": message,
                    "data": result,
                    "reload": True,  # Trigger page reload to show updated data
                }
            )
        else:
            return JsonResponse(
                {
                    "success": False,
                    "error": result.get("error", "Unknown error occurred"),
                    "reload": False,
                }
            )

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Invalid JSON in request body"}, status=400
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@staff_member_required
@require_POST
@csrf_exempt
def update_meeting_status(request, meeting_id):
    """Update meeting status via AJAX for admin interface"""
    try:
        # Parse JSON request body
        data = json.loads(request.body)
        action = data.get("action")

        # Get the meeting
        try:
            meeting = Meeting.objects.get(id=meeting_id)
        except Meeting.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Meeting not found"}, status=404
            )

        # Perform the requested action
        if action == "start":
            meeting.mark_as_started()
            message = f'Meeting "{meeting.title}" started successfully'
        elif action == "complete":
            meeting.mark_as_completed()
            message = f'Meeting "{meeting.title}" marked as completed'
        elif action == "cancel":
            meeting.mark_as_cancelled()
            message = f'Meeting "{meeting.title}" cancelled'
        else:
            return JsonResponse(
                {"success": False, "error": f"Unknown action: {action}"}, status=400
            )

        return JsonResponse(
            {
                "success": True,
                "message": message,
                "new_status": meeting.status,
                "reload": True,
            }
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Invalid JSON in request body"}, status=400
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# Meeting Outcome Tracking Views


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_meeting_summary(request, meeting_id):
    """Generate post-meeting summary and key takeaways"""
    try:
        meeting = get_object_or_404(Meeting, id=meeting_id, lead__user=request.user)

        if meeting.status != Meeting.Status.COMPLETED:
            return Response(
                {"error": "Meeting must be completed to generate summary"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        regenerate = request.data.get("regenerate", False)

        outcome_service = MeetingOutcomeService()
        result = outcome_service.generate_meeting_summary(meeting, regenerate)

        if result.get("success"):
            return Response(
                {
                    "success": True,
                    "summary": result.get("summary"),
                    "message": result.get("message"),
                }
            )
        else:
            return Response(
                {"error": result.get("error", "Failed to generate meeting summary")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def extract_action_items(request, meeting_id):
    """Extract action items and assignments from meeting"""
    try:
        meeting = get_object_or_404(Meeting, id=meeting_id, lead__user=request.user)

        if meeting.status != Meeting.Status.COMPLETED:
            return Response(
                {"error": "Meeting must be completed to extract action items"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        regenerate = request.data.get("regenerate", False)

        outcome_service = MeetingOutcomeService()
        result = outcome_service.extract_action_items(meeting, regenerate)

        if result.get("success"):
            return Response(
                {
                    "success": True,
                    "action_items": result.get("action_items"),
                    "message": result.get("message"),
                }
            )
        else:
            return Response(
                {"error": result.get("error", "Failed to extract action items")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def schedule_follow_up_actions(request, meeting_id):
    """Schedule next steps and follow-up actions"""
    try:
        meeting = get_object_or_404(Meeting, id=meeting_id, lead__user=request.user)

        if meeting.status != Meeting.Status.COMPLETED:
            return Response(
                {"error": "Meeting must be completed to schedule follow-up"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        outcome_service = MeetingOutcomeService()
        result = outcome_service.schedule_follow_up_actions(meeting)

        if result.get("success"):
            return Response(
                {
                    "success": True,
                    "follow_up_plan": result.get("follow_up_plan"),
                    "follow_up_meetings": result.get("follow_up_meetings"),
                    "message": result.get("message"),
                }
            )
        else:
            return Response(
                {"error": result.get("error", "Failed to schedule follow-up actions")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_lead_scoring(request, meeting_id):
    """Update lead scoring based on meeting outcomes"""
    try:
        meeting = get_object_or_404(Meeting, id=meeting_id, lead__user=request.user)

        if meeting.status != Meeting.Status.COMPLETED:
            return Response(
                {"error": "Meeting must be completed to update lead scoring"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not meeting.lead:
            return Response(
                {"error": "No lead associated with this meeting"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        outcome_service = MeetingOutcomeService()
        result = outcome_service.update_lead_scoring(meeting)

        if result.get("success"):
            return Response(
                {
                    "success": True,
                    "updated_scores": result.get("updated_scores"),
                    "score_changes": result.get("score_changes"),
                    "meeting_impact": result.get("meeting_impact"),
                    "message": result.get("message"),
                }
            )
        else:
            return Response(
                {"error": result.get("error", "Failed to update lead scoring")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def process_complete_meeting_outcome(request, meeting_id):
    """Process complete meeting outcome (all components)"""
    try:
        meeting = get_object_or_404(Meeting, id=meeting_id, lead__user=request.user)

        if meeting.status != Meeting.Status.COMPLETED:
            return Response(
                {"error": "Meeting must be completed to process outcomes"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        regenerate = request.data.get("regenerate", False)

        outcome_service = MeetingOutcomeService()
        result = outcome_service.process_complete_meeting_outcome(meeting, regenerate)

        return Response(
            {
                "success": result.get("overall_success", False),
                "components": result.get("components", {}),
                "message": result.get("message", ""),
                "processing_time": {
                    "started_at": result.get("processing_started_at"),
                    "completed_at": result.get("processing_completed_at"),
                },
            }
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_meeting_outcome_status(request, meeting_id):
    """Get the current status of meeting outcome processing"""
    try:
        meeting = get_object_or_404(Meeting, id=meeting_id, lead__user=request.user)

        # Check what outcome components have been processed
        outcome_status = {
            "meeting_id": str(meeting.id),
            "meeting_status": meeting.status,
            "components": {
                "summary": {
                    "completed": bool(meeting.outcome),
                    "last_updated": (
                        meeting.updated_at.isoformat() if meeting.outcome else None
                    ),
                },
                "action_items": {
                    "completed": bool(meeting.action_items),
                    "count": len(meeting.action_items) if meeting.action_items else 0,
                    "last_updated": (
                        meeting.updated_at.isoformat() if meeting.action_items else None
                    ),
                },
                "follow_up_plan": {
                    "completed": "follow_up_plan" in meeting.ai_insights,
                    "last_updated": (
                        meeting.ai_insights.get("follow_up_generated_at")
                        if "follow_up_plan" in meeting.ai_insights
                        else None
                    ),
                },
                "lead_scoring": {
                    "completed": "lead_scoring_update" in meeting.ai_insights,
                    "last_updated": (
                        meeting.ai_insights.get("lead_scoring_update", {}).get(
                            "updated_at"
                        )
                        if "lead_scoring_update" in meeting.ai_insights
                        else None
                    ),
                },
            },
            "overall_completion": False,
        }

        # Calculate overall completion
        completed_components = sum(
            1 for comp in outcome_status["components"].values() if comp["completed"]
        )
        total_components = len(outcome_status["components"])
        outcome_status["overall_completion"] = completed_components == total_components
        outcome_status["completion_percentage"] = (
            completed_components / total_components
        ) * 100

        return Response(outcome_status)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_meeting_outcomes_dashboard(request):
    """Get dashboard data for meeting outcomes"""
    try:
        # Get user's completed meetings
        completed_meetings = Meeting.objects.filter(
            lead__user=request.user, status=Meeting.Status.COMPLETED
        ).order_by("-ended_at")[:20]

        dashboard_data = {
            "total_completed_meetings": completed_meetings.count(),
            "outcomes_processed": 0,
            "pending_processing": 0,
            "recent_meetings": [],
            "processing_stats": {
                "summaries_generated": 0,
                "action_items_extracted": 0,
                "follow_ups_scheduled": 0,
                "lead_scores_updated": 0,
            },
        }

        for meeting in completed_meetings:
            # Check processing status
            has_summary = bool(meeting.outcome)
            has_action_items = bool(meeting.action_items)
            has_follow_up = "follow_up_plan" in meeting.ai_insights
            has_scoring_update = "lead_scoring_update" in meeting.ai_insights

            processed_components = sum(
                [has_summary, has_action_items, has_follow_up, has_scoring_update]
            )
            is_fully_processed = processed_components == 4

            if is_fully_processed:
                dashboard_data["outcomes_processed"] += 1
            else:
                dashboard_data["pending_processing"] += 1

            # Update processing stats
            if has_summary:
                dashboard_data["processing_stats"]["summaries_generated"] += 1
            if has_action_items:
                dashboard_data["processing_stats"]["action_items_extracted"] += 1
            if has_follow_up:
                dashboard_data["processing_stats"]["follow_ups_scheduled"] += 1
            if has_scoring_update:
                dashboard_data["processing_stats"]["lead_scores_updated"] += 1

            # Add to recent meetings
            dashboard_data["recent_meetings"].append(
                {
                    "id": str(meeting.id),
                    "title": meeting.title,
                    "company_name": (
                        meeting.lead.company_name if meeting.lead else "No Lead"
                    ),
                    "ended_at": (
                        meeting.ended_at.isoformat() if meeting.ended_at else None
                    ),
                    "processing_status": {
                        "fully_processed": is_fully_processed,
                        "processed_components": processed_components,
                        "total_components": 4,
                        "completion_percentage": (processed_components / 4) * 100,
                    },
                }
            )

        return Response(dashboard_data)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Admin AJAX Views for Meeting Outcome Actions


@staff_member_required
@csrf_exempt
@require_POST
def admin_generate_meeting_summary(request):
    """Admin AJAX view for generating meeting summary"""
    try:
        meeting_id = request.POST.get("meeting_id")
        meeting = get_object_or_404(Meeting, id=meeting_id)

        outcome_service = MeetingOutcomeService()
        result = outcome_service.generate_meeting_summary(meeting, regenerate=True)

        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@staff_member_required
@csrf_exempt
@require_POST
def admin_extract_action_items(request):
    """Admin AJAX view for extracting action items"""
    try:
        meeting_id = request.POST.get("meeting_id")
        meeting = get_object_or_404(Meeting, id=meeting_id)

        outcome_service = MeetingOutcomeService()
        result = outcome_service.extract_action_items(meeting, regenerate=True)

        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@staff_member_required
@csrf_exempt
@require_POST
def admin_schedule_follow_up(request):
    """Admin AJAX view for scheduling follow-up"""
    try:
        meeting_id = request.POST.get("meeting_id")
        meeting = get_object_or_404(Meeting, id=meeting_id)

        outcome_service = MeetingOutcomeService()
        result = outcome_service.schedule_follow_up_actions(meeting)

        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@staff_member_required
@csrf_exempt
@require_POST
def admin_update_lead_scoring(request):
    """Admin AJAX view for updating lead scoring"""
    try:
        meeting_id = request.POST.get("meeting_id")
        meeting = get_object_or_404(Meeting, id=meeting_id)

        outcome_service = MeetingOutcomeService()
        result = outcome_service.update_lead_scoring(meeting)

        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@staff_member_required
@csrf_exempt
@require_POST
def admin_process_complete_outcome(request):
    """Admin AJAX view for processing complete meeting outcome"""
    try:
        meeting_id = request.POST.get("meeting_id")
        meeting = get_object_or_404(Meeting, id=meeting_id)

        outcome_service = MeetingOutcomeService()
        result = outcome_service.process_complete_meeting_outcome(
            meeting, regenerate=True
        )

        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})
