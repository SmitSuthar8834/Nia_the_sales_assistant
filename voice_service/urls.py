"""
URL configuration for voice service
"""

from django.urls import path
from . import views
from . import chat_views

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
    
    # Chat endpoints
    path('chat/create/', chat_views.create_chat_session, name='create_chat_session'),
    path('chat/sessions/', chat_views.get_chat_sessions, name='get_chat_sessions'),
    path('chat/session/<str:session_id>/', chat_views.get_chat_session, name='get_chat_session'),
    path('chat/session/<str:session_id>/end/', chat_views.end_chat_session, name='end_chat_session'),
    path('chat/session/<str:session_id>/upload/', chat_views.upload_chat_file, name='upload_chat_file'),
    path('chat/session/<str:session_id>/analytics/', chat_views.get_chat_analytics, name='get_chat_analytics'),
    path('chat/commands/', chat_views.get_bot_commands, name='get_bot_commands'),
    path('chat/search/', chat_views.search_chat_history, name='search_chat_history'),
]