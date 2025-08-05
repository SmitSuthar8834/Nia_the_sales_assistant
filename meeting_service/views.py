from django.shortcuts import render
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import MeetingSession, MeetingParticipant, MeetingStatusUpdate, MicrosoftTeamsCredentials
from .serializers import (
    MeetingSessionSerializer, MeetingParticipantSerializer, MeetingStatusUpdateSerializer,
    CreateTeamsMeetingSerializer, TeamsTeamSerializer, TeamsChannelSerializer,
    SendChannelMessageSerializer, MicrosoftTeamsCredentialsSerializer
)
from .microsoft_teams_service import MicrosoftTeamsService


class MeetingSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing meeting sessions"""
    serializer_class = MeetingSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get meetings for the current user"""
        user = self.request.user
        return MeetingSession.objects.filter(organizer=user).order_by('-scheduled_start_time')


class MeetingParticipantViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing meeting participants"""
    serializer_class = MeetingParticipantSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get participants for meetings the user has access to"""
        user = self.request.user
        accessible_meetings = MeetingSession.objects.filter(organizer=user)
        return MeetingParticipant.objects.filter(meeting__in=accessible_meetings).order_by('-created_at')


class MeetingStatusUpdateViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing meeting status updates"""
    serializer_class = MeetingStatusUpdateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get status updates for meetings the user has access to"""
        user = self.request.user
        accessible_meetings = MeetingSession.objects.filter(organizer=user)
        return MeetingStatusUpdate.objects.filter(meeting__in=accessible_meetings).order_by('-timestamp')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def google_oauth_initiate(request):
    """Initiate Google OAuth flow"""
    return Response({
        'message': 'Google OAuth integration coming soon'
    })


@api_view(['GET'])
def google_oauth_callback(request):
    """Handle Google OAuth callback"""
    return Response({
        'message': 'OAuth callback handled'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def google_auth_status(request):
    """Check if user has valid Google credentials"""
    return Response({
        'authenticated': False,
        'message': 'Google authentication coming soon'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def meeting_dashboard(request):
    """Get dashboard data for meetings"""
    return Response({
        'today_meetings': 0,
        'upcoming_meetings': 0,
        'active_meetings': 0,
        'recent_meetings': [],
        'google_auth_status': False
    })

# Microsoft Teams Integration Views

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teams_oauth_initiate(request):
    """Initiate Microsoft Teams OAuth flow"""
    try:
        teams_service = MicrosoftTeamsService()
        auth_url = teams_service.get_authorization_url(str(request.user.id))
        
        return Response({
            'authorization_url': auth_url,
            'message': 'Redirect user to this URL to authorize Microsoft Teams access'
        })
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def teams_oauth_callback(request):
    """Handle Microsoft Teams OAuth callback"""
    try:
        code = request.GET.get('code')
        state = request.GET.get('state')  # This contains the user_id
        
        if not code or not state:
            return Response({
                'error': 'Missing authorization code or state parameter'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        teams_service = MicrosoftTeamsService()
        success = teams_service.handle_oauth_callback(code, state)
        
        if success:
            return Response({
                'message': 'Microsoft Teams authorization successful'
            })
        else:
            return Response({
                'error': 'Failed to process Microsoft Teams authorization'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teams_auth_status(request):
    """Check if user has valid Microsoft Teams credentials"""
    try:
        teams_creds = MicrosoftTeamsCredentials.objects.get(user=request.user)
        serializer = MicrosoftTeamsCredentialsSerializer(teams_creds)
        
        return Response({
            'authenticated': not teams_creds.is_token_expired(),
            'credentials': serializer.data
        })
    except MicrosoftTeamsCredentials.DoesNotExist:
        return Response({
            'authenticated': False,
            'message': 'No Microsoft Teams credentials found'
        })


@api_view(['POST'])
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
            title=serializer.validated_data['title'],
            description=serializer.validated_data.get('description', ''),
            start_time=serializer.validated_data['scheduled_start_time'],
            end_time=serializer.validated_data['scheduled_end_time'],
            attendee_emails=serializer.validated_data.get('attendee_emails', [])
        )
        
        if meeting_session:
            meeting_serializer = MeetingSessionSerializer(meeting_session)
            return Response(meeting_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Failed to create Microsoft Teams meeting'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_teams(request):
    """Get Teams that the user is a member of"""
    try:
        teams_service = MicrosoftTeamsService()
        teams = teams_service.get_user_teams(request.user)
        
        serializer = TeamsTeamSerializer(teams, many=True)
        return Response({
            'teams': serializer.data
        })
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_team_channels(request, team_id):
    """Get channels for a specific team"""
    try:
        teams_service = MicrosoftTeamsService()
        channels = teams_service.get_team_channels(request.user, team_id)
        
        serializer = TeamsChannelSerializer(channels, many=True)
        return Response({
            'channels': serializer.data
        })
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
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
            team_id=serializer.validated_data['team_id'],
            channel_id=serializer.validated_data['channel_id'],
            message=serializer.validated_data['message']
        )
        
        if success:
            return Response({
                'message': 'Message sent successfully'
            })
        else:
            return Response({
                'error': 'Failed to send message'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_meeting_recordings(request, meeting_id):
    """Get recordings for a specific meeting"""
    try:
        teams_service = MicrosoftTeamsService()
        recordings = teams_service.get_meeting_recordings(request.user, meeting_id)
        
        return Response({
            'recordings': recordings
        })
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_meeting_transcripts(request, meeting_id):
    """Get transcripts for a specific meeting"""
    try:
        teams_service = MicrosoftTeamsService()
        transcripts = teams_service.get_meeting_transcripts(request.user, meeting_id)
        
        return Response({
            'transcripts': transcripts
        })
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teams_meeting_dashboard(request):
    """Get dashboard data for Teams meetings"""
    try:
        teams_service = MicrosoftTeamsService()
        
        # Get user's Teams meetings
        all_meetings = teams_service.get_user_meetings(request.user)
        today_meetings = [m for m in all_meetings if m.scheduled_start_time.date() == timezone.now().date()]
        upcoming_meetings = [m for m in all_meetings if m.scheduled_start_time > timezone.now()]
        active_meetings = [m for m in all_meetings if m.is_active()]
        
        return Response({
            'today_meetings': len(today_meetings),
            'upcoming_meetings': len(upcoming_meetings),
            'active_meetings': len(active_meetings),
            'recent_meetings': MeetingSessionSerializer(all_meetings[:5], many=True).data,
            'teams_auth_status': True  # If we reach here, user has valid credentials
        })
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# Unified Meeting Interface

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_unified_meeting(request):
    """Create a meeting using either Google Meet or Microsoft Teams based on user preference"""
    try:
        meeting_type = request.data.get('meeting_type', 'google_meet')
        
        if meeting_type == 'microsoft_teams':
            serializer = CreateTeamsMeetingSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            teams_service = MicrosoftTeamsService()
            meeting_session = teams_service.create_meeting(
                user=request.user,
                title=serializer.validated_data['title'],
                description=serializer.validated_data.get('description', ''),
                start_time=serializer.validated_data['scheduled_start_time'],
                end_time=serializer.validated_data['scheduled_end_time'],
                attendee_emails=serializer.validated_data.get('attendee_emails', [])
            )
        else:
            # Default to Google Meet (existing functionality)
            from .serializers import CreateMeetingSerializer
            from .google_meet_service import GoogleMeetService
            
            serializer = CreateMeetingSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            google_service = GoogleMeetService()
            meeting_session = google_service.create_meeting(
                user=request.user,
                title=serializer.validated_data['title'],
                description=serializer.validated_data.get('description', ''),
                start_time=serializer.validated_data['scheduled_start_time'],
                end_time=serializer.validated_data['scheduled_end_time'],
                attendee_emails=serializer.validated_data.get('attendee_emails', [])
            )
        
        if meeting_session:
            meeting_serializer = MeetingSessionSerializer(meeting_session)
            return Response(meeting_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': f'Failed to create {meeting_type} meeting'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
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
        
        today_meetings = [m for m in all_meetings if m.scheduled_start_time.date() == today]
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
        
        return Response({
            'today_meetings': len(today_meetings),
            'upcoming_meetings': len(upcoming_meetings),
            'active_meetings': len(active_meetings),
            'recent_meetings': MeetingSessionSerializer(all_meetings[:10], many=True).data,
            'google_auth_status': google_auth,
            'teams_auth_status': teams_auth,
            'total_meetings': len(all_meetings)
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# Intelligent Meeting Management Views

from .intelligent_meeting_service import IntelligentMeetingService
from django.utils.dateparse import parse_datetime


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analyze_user_availability(request):
    """Analyze user's meeting patterns and availability"""
    try:
        # Get date range from query parameters
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
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
        
        return Response({
            'availability': availability,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recommend_meeting_time(request):
    """Get recommended meeting times based on user patterns"""
    try:
        duration_minutes = request.data.get('duration_minutes', 60)
        preferred_date_str = request.data.get('preferred_date')
        
        preferred_date = None
        if preferred_date_str:
            preferred_date = parse_datetime(preferred_date_str)
        
        intelligent_service = IntelligentMeetingService()
        recommendations = intelligent_service.recommend_meeting_time(
            request.user, duration_minutes, preferred_date
        )
        
        return Response({
            'recommendations': recommendations,
            'criteria': {
                'duration_minutes': duration_minutes,
                'preferred_date': preferred_date.isoformat() if preferred_date else None
            }
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def detect_meeting_conflicts(request):
    """Detect conflicts with a proposed meeting time"""
    try:
        start_time_str = request.data.get('start_time')
        end_time_str = request.data.get('end_time')
        
        if not start_time_str or not end_time_str:
            return Response({
                'error': 'start_time and end_time are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        start_time = parse_datetime(start_time_str)
        end_time = parse_datetime(end_time_str)
        
        proposed_meeting = {
            'start_time': start_time,
            'end_time': end_time
        }
        
        intelligent_service = IntelligentMeetingService()
        conflicts = intelligent_service.detect_meeting_conflicts(
            request.user, proposed_meeting
        )
        
        return Response({
            'conflicts': conflicts,
            'has_conflicts': len(conflicts) > 0,
            'proposed_meeting': {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def suggest_reschedule_options(request):
    """Suggest alternative times for a conflicted meeting"""
    try:
        meeting_id = request.data.get('meeting_id')
        
        if not meeting_id:
            return Response({
                'error': 'meeting_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            meeting = MeetingSession.objects.get(id=meeting_id, organizer=request.user)
        except MeetingSession.DoesNotExist:
            return Response({
                'error': 'Meeting not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        
        intelligent_service = IntelligentMeetingService()
        alternatives = intelligent_service.suggest_reschedule_options(
            request.user, meeting
        )
        
        return Response({
            'alternatives': alternatives,
            'original_meeting': {
                'id': str(meeting.id),
                'title': meeting.title,
                'start_time': meeting.scheduled_start_time.isoformat(),
                'end_time': meeting.scheduled_end_time.isoformat()
            }
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def schedule_post_meeting_followup(request):
    """Schedule intelligent follow-up actions after a meeting"""
    try:
        meeting_id = request.data.get('meeting_id')
        
        if not meeting_id:
            return Response({
                'error': 'meeting_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            meeting = MeetingSession.objects.get(
                id=meeting_id,
                organizer=request.user,
                status=MeetingSession.Status.ENDED
            )
        except MeetingSession.DoesNotExist:
            return Response({
                'error': 'Ended meeting not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        
        intelligent_service = IntelligentMeetingService()
        success = intelligent_service.schedule_post_meeting_follow_up(meeting)
        
        if success:
            return Response({
                'message': 'Follow-up scheduled successfully',
                'meeting_id': str(meeting.id)
            })
        else:
            return Response({
                'error': 'Failed to schedule follow-up'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analyze_meeting_patterns(request):
    """Analyze user's meeting patterns for optimization"""
    try:
        days_back = int(request.GET.get('days_back', 30))
        
        intelligent_service = IntelligentMeetingService()
        patterns = intelligent_service.analyze_meeting_patterns(
            request.user, days_back
        )
        
        return Response({
            'patterns': patterns,
            'analysis_period_days': days_back
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_calendar_sync_status(request):
    """Get the status of calendar integrations"""
    try:
        intelligent_service = IntelligentMeetingService()
        sync_status = intelligent_service.get_calendar_sync_status(request.user)
        
        return Response({
            'sync_status': sync_status
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
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
        
        return Response({
            'availability': availability,
            'patterns': patterns,
            'sync_status': sync_status,
            'recommendations': recommendations[:3],  # Top 3 recommendations
            'dashboard_generated_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# NIA Meeting Scheduler Views

from .nia_meeting_scheduler import NIAMeetingScheduler, NIAMeetingType


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_nia_available_slots(request):
    """Get available time slots for NIA meetings"""
    try:
        # Get parameters
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        meeting_type_str = request.GET.get('meeting_type', 'general_consultation')
        
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
        
        return Response({
            'available_slots': available_slots,
            'meeting_type': meeting_type.value,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def schedule_nia_meeting(request):
    """Schedule a meeting with NIA"""
    try:
        # Validate required fields
        start_time_str = request.data.get('start_time')
        meeting_type_str = request.data.get('meeting_type', 'general_consultation')
        platform = request.data.get('platform', 'google_meet')
        lead_id = request.data.get('lead_id')
        
        if not start_time_str:
            return Response({
                'error': 'start_time is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        start_time = parse_datetime(start_time_str)
        
        try:
            meeting_type = NIAMeetingType(meeting_type_str)
        except ValueError:
            return Response({
                'error': f'Invalid meeting type: {meeting_type_str}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Prepare meeting data
        meeting_data = {
            'start_time': start_time,
            'meeting_type': meeting_type.value,
            'platform': platform,
            'lead_id': lead_id
        }
        
        nia_scheduler = NIAMeetingScheduler()
        meeting_session = nia_scheduler.schedule_nia_meeting(request.user, meeting_data)
        
        if meeting_session:
            meeting_serializer = MeetingSessionSerializer(meeting_session)
            return Response({
                'meeting': meeting_serializer.data,
                'message': 'NIA meeting scheduled successfully'
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Failed to schedule NIA meeting'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_meeting_summary(request):
    """Generate post-meeting summary for NIA meeting"""
    try:
        meeting_id = request.data.get('meeting_id')
        
        if not meeting_id:
            return Response({
                'error': 'meeting_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            meeting = MeetingSession.objects.get(
                id=meeting_id,
                organizer=request.user,
                status=MeetingSession.Status.ENDED
            )
        except MeetingSession.DoesNotExist:
            return Response({
                'error': 'Ended meeting not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        
        nia_scheduler = NIAMeetingScheduler()
        summary = nia_scheduler.generate_meeting_summary(meeting)
        
        return Response({
            'summary': summary,
            'meeting_id': str(meeting.id)
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_nia_meeting_analytics(request):
    """Get analytics for NIA meetings"""
    try:
        # Get date range parameters
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        date_range = None
        if start_date_str and end_date_str:
            start_date = parse_datetime(start_date_str)
            end_date = parse_datetime(end_date_str)
            date_range = (start_date, end_date)
        
        nia_scheduler = NIAMeetingScheduler()
        analytics = nia_scheduler.get_meeting_analytics(request.user, date_range)
        
        return Response({
            'analytics': analytics
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_nia_meeting_types(request):
    """Get available NIA meeting types and their details"""
    try:
        nia_scheduler = NIAMeetingScheduler()
        
        meeting_types = []
        for meeting_type in NIAMeetingType:
            template = nia_scheduler.meeting_templates[meeting_type]
            meeting_types.append({
                'type': meeting_type.value,
                'name': meeting_type.value.replace('_', ' ').title(),
                'duration_minutes': template['duration'],
                'preparation_items': template['preparation_items'],
                'description': nia_scheduler._generate_meeting_description(meeting_type, request.user)
            })
        
        return Response({
            'meeting_types': meeting_types
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nia_meeting_dashboard(request):
    """Get comprehensive NIA meeting dashboard"""
    try:
        nia_scheduler = NIAMeetingScheduler()
        
        # Get upcoming NIA meetings
        upcoming_meetings = MeetingSession.objects.filter(
            organizer=request.user,
            scheduled_start_time__gt=timezone.now(),
            status_updates__description__icontains='NIA meeting'
        ).distinct().order_by('scheduled_start_time')[:5]
        
        # Get recent completed meetings
        recent_meetings = MeetingSession.objects.filter(
            organizer=request.user,
            status=MeetingSession.Status.ENDED,
            status_updates__description__icontains='NIA meeting'
        ).distinct().order_by('-scheduled_start_time')[:5]
        
        # Get analytics for last 30 days
        analytics = nia_scheduler.get_meeting_analytics(request.user)
        
        # Get available slots for next 7 days
        start_date = timezone.now()
        end_date = start_date + timedelta(days=7)
        available_slots = nia_scheduler.get_available_time_slots(
            request.user, (start_date, end_date)
        )
        
        return Response({
            'upcoming_meetings': MeetingSessionSerializer(upcoming_meetings, many=True).data,
            'recent_meetings': MeetingSessionSerializer(recent_meetings, many=True).data,
            'analytics': analytics,
            'available_slots': available_slots[:3],  # Next 3 available slots
            'dashboard_generated_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)