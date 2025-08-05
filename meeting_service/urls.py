from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'meetings', views.MeetingSessionViewSet, basename='meeting')
router.register(r'participants', views.MeetingParticipantViewSet, basename='participant')
router.register(r'status-updates', views.MeetingStatusUpdateViewSet, basename='status-update')

app_name = 'meeting_service'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Google OAuth endpoints
    path('oauth/google/initiate/', views.google_oauth_initiate, name='google_oauth_initiate'),
    path('oauth/google/callback/', views.google_oauth_callback, name='google_oauth_callback'),
    path('oauth/google/status/', views.google_auth_status, name='google_auth_status'),
    
    # Microsoft Teams OAuth endpoints
    path('oauth/teams/initiate/', views.teams_oauth_initiate, name='teams_oauth_initiate'),
    path('oauth/teams/callback/', views.teams_oauth_callback, name='teams_oauth_callback'),
    path('oauth/teams/status/', views.teams_auth_status, name='teams_auth_status'),
    
    # Teams meeting endpoints
    path('api/teams/meetings/create/', views.create_teams_meeting, name='create_teams_meeting'),
    path('api/teams/meetings/<str:meeting_id>/recordings/', views.get_meeting_recordings, name='get_meeting_recordings'),
    path('api/teams/meetings/<str:meeting_id>/transcripts/', views.get_meeting_transcripts, name='get_meeting_transcripts'),
    
    # Teams organization endpoints
    path('api/teams/teams/', views.get_user_teams, name='get_user_teams'),
    path('api/teams/teams/<str:team_id>/channels/', views.get_team_channels, name='get_team_channels'),
    path('api/teams/channels/message/', views.send_channel_message, name='send_channel_message'),
    
    # Dashboard endpoints
    path('api/dashboard/', views.meeting_dashboard, name='meeting_dashboard'),
    path('api/teams/dashboard/', views.teams_meeting_dashboard, name='teams_meeting_dashboard'),
    
    # Unified meeting endpoints
    path('api/unified/meetings/create/', views.create_unified_meeting, name='create_unified_meeting'),
    path('api/unified/dashboard/', views.unified_meeting_dashboard, name='unified_meeting_dashboard'),
    
    # Intelligent meeting management endpoints
    path('api/intelligent/availability/', views.analyze_user_availability, name='analyze_user_availability'),
    path('api/intelligent/recommend-time/', views.recommend_meeting_time, name='recommend_meeting_time'),
    path('api/intelligent/detect-conflicts/', views.detect_meeting_conflicts, name='detect_meeting_conflicts'),
    path('api/intelligent/reschedule-options/', views.suggest_reschedule_options, name='suggest_reschedule_options'),
    path('api/intelligent/schedule-followup/', views.schedule_post_meeting_followup, name='schedule_post_meeting_followup'),
    path('api/intelligent/patterns/', views.analyze_meeting_patterns, name='analyze_meeting_patterns'),
    path('api/intelligent/sync-status/', views.get_calendar_sync_status, name='get_calendar_sync_status'),
    path('api/intelligent/dashboard/', views.intelligent_meeting_dashboard, name='intelligent_meeting_dashboard'),
    
    # NIA Meeting Scheduler endpoints
    path('api/nia/available-slots/', views.get_nia_available_slots, name='get_nia_available_slots'),
    path('api/nia/schedule/', views.schedule_nia_meeting, name='schedule_nia_meeting'),
    path('api/nia/summary/', views.generate_meeting_summary, name='generate_meeting_summary'),
    path('api/nia/analytics/', views.get_nia_meeting_analytics, name='get_nia_meeting_analytics'),
    path('api/nia/meeting-types/', views.get_nia_meeting_types, name='get_nia_meeting_types'),
    path('api/nia/dashboard/', views.nia_meeting_dashboard, name='nia_meeting_dashboard'),
]