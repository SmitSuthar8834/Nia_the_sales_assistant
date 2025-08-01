"""
WebSocket routing for voice service
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/voice/(?P<session_id>\w+)/$', consumers.VoiceConsumer.as_asgi()),
]