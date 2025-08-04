"""
WebSocket routing for voice service
"""

from django.urls import re_path
from . import consumers
from . import chat_consumers

websocket_urlpatterns = [
    re_path(r'ws/voice/(?P<session_id>\w+)/$', consumers.VoiceConsumer.as_asgi()),
    re_path(r'ws/chat/(?P<session_id>\w+)/$', chat_consumers.ChatConsumer.as_asgi()),
]