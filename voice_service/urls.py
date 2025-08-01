"""
URL configuration for voice service
"""

from django.urls import path
from . import views

app_name = 'voice_service'

urlpatterns = [
    # Call management endpoints
    path('initiate/', views.initiate_call, name='initiate_call'),
    path('webrtc/setup/', views.setup_webrtc, name='setup_webrtc'),
    path('end/', views.end_call, name='end_call'),
    
    # Audio processing endpoints
    path('process-audio/', views.process_audio, name='process_audio'),
    path('generate-speech/', views.generate_speech, name='generate_speech'),
    
    # Session management endpoints
    path('session/<str:session_id>/status/', views.session_status, name='session_status'),
    path('sessions/', views.user_call_sessions, name='user_call_sessions'),
    
    # Configuration endpoints
    path('config/', views.voice_configuration, name='voice_configuration'),
    
    # Conversation management endpoints
    path('session/<str:session_id>/context/', views.conversation_context, name='conversation_context'),
    path('session/<str:session_id>/summary/', views.conversation_summary, name='conversation_summary'),
    path('session/<str:session_id>/audio-files/', views.session_audio_files, name='session_audio_files'),
    path('session/<str:session_id>/audio/<str:filename>/', views.download_audio_file, name='download_audio_file'),
]