"""
Tests for voice service functionality
"""

import uuid
from unittest.mock import Mock, patch

from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .consumers import VoiceConsumer
from .models import AudioChunk, CallSession, ConversationTurn, VoiceConfiguration
from .services import AudioBufferManager, VoiceProcessingService

User = get_user_model()


class CallSessionModelTest(TestCase):
    """Test CallSession model functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_call_session_creation(self):
        """Test creating a call session"""
        session = CallSession.objects.create(
            user=self.user, caller_id="123456789", status=CallSession.Status.ACTIVE
        )

        self.assertEqual(session.user, self.user)
        self.assertEqual(session.caller_id, "123456789")
        self.assertEqual(session.status, CallSession.Status.ACTIVE)
        self.assertIsNotNone(session.session_id)
        self.assertIsNotNone(session.start_time)

    def test_call_session_str_representation(self):
        """Test string representation of call session"""
        session = CallSession.objects.create(
            user=self.user, status=CallSession.Status.ACTIVE
        )

        expected = f"Call Session {session.session_id} - {self.user.username} (active)"
        self.assertEqual(str(session), expected)


class AudioChunkModelTest(TestCase):
    """Test AudioChunk model functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.session = CallSession.objects.create(
            user=self.user, status=CallSession.Status.ACTIVE
        )

    def test_audio_chunk_creation(self):
        """Test creating an audio chunk"""
        chunk = AudioChunk.objects.create(
            session=self.session,
            chunk_number=1,
            audio_data=b"fake_audio_data",
            duration_ms=1000,
        )

        self.assertEqual(chunk.session, self.session)
        self.assertEqual(chunk.chunk_number, 1)
        self.assertEqual(chunk.audio_data, b"fake_audio_data")
        self.assertEqual(chunk.duration_ms, 1000)
        self.assertFalse(chunk.is_processed)


class ConversationTurnModelTest(TestCase):
    """Test ConversationTurn model functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.session = CallSession.objects.create(
            user=self.user, status=CallSession.Status.ACTIVE
        )

    def test_conversation_turn_creation(self):
        """Test creating a conversation turn"""
        turn = ConversationTurn.objects.create(
            session=self.session,
            turn_number=1,
            speaker=ConversationTurn.Speaker.USER,
            content="Hello, this is a test message",
        )

        self.assertEqual(turn.session, self.session)
        self.assertEqual(turn.turn_number, 1)
        self.assertEqual(turn.speaker, ConversationTurn.Speaker.USER)
        self.assertEqual(turn.content, "Hello, this is a test message")


class VoiceConfigurationModelTest(TestCase):
    """Test VoiceConfiguration model functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_voice_configuration_creation(self):
        """Test creating voice configuration"""
        config = VoiceConfiguration.objects.create(
            user=self.user, language_code="en-US", voice_name="en-US-Wavenet-D"
        )

        self.assertEqual(config.user, self.user)
        self.assertEqual(config.language_code, "en-US")
        self.assertEqual(config.voice_name, "en-US-Wavenet-D")
        self.assertTrue(config.enable_automatic_punctuation)
        self.assertTrue(config.auto_answer)


class VoiceProcessingServiceTest(TestCase):
    """Test VoiceProcessingService functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.service = VoiceProcessingService()

    @patch("voice_service.services.speech.SpeechClient")
    @patch("voice_service.services.texttospeech.TextToSpeechClient")
    def test_service_initialization(self, mock_tts, mock_speech):
        """Test service initialization"""
        service = VoiceProcessingService()
        self.assertIsNotNone(service.speech_client)
        self.assertIsNotNone(service.tts_client)
        self.assertEqual(service.active_sessions, {})
        self.assertEqual(service.peer_connections, {})

    async def test_initiate_call(self):
        """Test call initiation"""
        session = await self.service.initiate_call(str(self.user.id))

        self.assertEqual(session.user, self.user)
        self.assertEqual(session.status, CallSession.Status.ACTIVE)
        self.assertIn(str(session.session_id), self.service.active_sessions)

    async def test_initiate_call_invalid_user(self):
        """Test call initiation with invalid user"""
        with self.assertRaises(ValueError):
            await self.service.initiate_call("invalid-user-id")

    @patch("voice_service.services.speech.SpeechClient")
    async def test_process_audio_stream(self, mock_speech_client):
        """Test audio stream processing"""
        # Mock speech recognition response
        mock_result = Mock()
        mock_result.alternatives = [Mock()]
        mock_result.alternatives[0].transcript = "Hello world"
        mock_result.alternatives[0].confidence = 0.95

        mock_response = Mock()
        mock_response.results = [mock_result]

        mock_speech_client.return_value.recognize.return_value = mock_response

        # Create session
        session = await self.service.initiate_call(str(self.user.id))

        # Process audio
        result = await self.service.process_audio_stream(
            str(session.session_id), b"fake_audio_data"
        )

        self.assertEqual(result["transcription"], "Hello world")
        self.assertEqual(result["confidence"], 0.95)
        self.assertEqual(result["session_id"], str(session.session_id))

    async def test_end_call(self):
        """Test ending a call"""
        session = await self.service.initiate_call(str(self.user.id))
        session_id = str(session.session_id)

        summary = await self.service.end_call(session_id)

        self.assertEqual(summary["session_id"], session_id)
        self.assertEqual(summary["status"], CallSession.Status.ENDED)
        self.assertNotIn(session_id, self.service.active_sessions)


class AudioBufferManagerTest(TestCase):
    """Test AudioBufferManager functionality"""

    def setUp(self):
        self.buffer_manager = AudioBufferManager()
        self.session_id = str(uuid.uuid4())

    async def test_add_and_get_audio_data(self):
        """Test adding and retrieving audio data"""
        audio_data = b"test_audio_data"

        await self.buffer_manager.add_audio_data(self.session_id, audio_data)
        retrieved_data = await self.buffer_manager.get_buffered_audio(self.session_id)

        self.assertEqual(retrieved_data, audio_data)

    async def test_clear_buffer(self):
        """Test clearing audio buffer"""
        audio_data = b"test_audio_data"

        await self.buffer_manager.add_audio_data(self.session_id, audio_data)
        await self.buffer_manager.clear_buffer(self.session_id)

        retrieved_data = await self.buffer_manager.get_buffered_audio(self.session_id)
        self.assertEqual(retrieved_data, b"")

    def test_remove_session_buffer(self):
        """Test removing session buffer"""
        self.buffer_manager.buffers[self.session_id] = Mock()
        self.buffer_manager.buffer_locks[self.session_id] = Mock()

        self.buffer_manager.remove_session_buffer(self.session_id)

        self.assertNotIn(self.session_id, self.buffer_manager.buffers)
        self.assertNotIn(self.session_id, self.buffer_manager.buffer_locks)


class VoiceServiceAPITest(APITestCase):
    """Test voice service API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_initiate_call_endpoint(self):
        """Test call initiation endpoint"""
        url = reverse("voice_service:initiate_call")
        data = {"caller_id": "123456789"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("session_id", response.data)
        self.assertEqual(response.data["status"], "active")

    def test_initiate_call_unauthenticated(self):
        """Test call initiation without authentication"""
        self.client.force_authenticate(user=None)
        url = reverse("voice_service:initiate_call")
        data = {"caller_id": "123456789"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_call_sessions_endpoint(self):
        """Test getting user's call sessions"""
        # Create test sessions
        CallSession.objects.create(
            user=self.user, status=CallSession.Status.ENDED, caller_id="123456789"
        )
        CallSession.objects.create(
            user=self.user, status=CallSession.Status.ACTIVE, caller_id="987654321"
        )

        url = reverse("voice_service:user_call_sessions")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["sessions"]), 2)

    def test_voice_configuration_get(self):
        """Test getting voice configuration"""
        url = reverse("voice_service:voice_configuration")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["language_code"], "en-US")
        self.assertEqual(response.data["voice_name"], "en-US-Wavenet-D")

    def test_voice_configuration_update(self):
        """Test updating voice configuration"""
        url = reverse("voice_service:voice_configuration")
        data = {
            "language_code": "es-ES",
            "voice_name": "es-ES-Wavenet-B",
            "speaking_rate": 1.2,
        }

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify configuration was updated
        config = VoiceConfiguration.objects.get(user=self.user)
        self.assertEqual(config.language_code, "es-ES")
        self.assertEqual(config.voice_name, "es-ES-Wavenet-B")
        self.assertEqual(config.speaking_rate, 1.2)


class VoiceConsumerTest(TransactionTestCase):
    """Test VoiceConsumer WebSocket functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.session = CallSession.objects.create(
            user=self.user, status=CallSession.Status.ACTIVE
        )

    async def test_websocket_connect_authenticated(self):
        """Test WebSocket connection with authenticated user"""
        communicator = WebsocketCommunicator(
            VoiceConsumer.as_asgi(), f"/ws/voice/{self.session.session_id}/"
        )
        communicator.scope["user"] = self.user

        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)

        # Should receive connection confirmation
        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "connection_established")
        self.assertEqual(response["session_id"], str(self.session.session_id))

        await communicator.disconnect()

    async def test_websocket_connect_unauthenticated(self):
        """Test WebSocket connection without authentication"""
        from django.contrib.auth.models import AnonymousUser

        communicator = WebsocketCommunicator(
            VoiceConsumer.as_asgi(), f"/ws/voice/{self.session.session_id}/"
        )
        communicator.scope["user"] = AnonymousUser()

        connected, subprotocol = await communicator.connect()
        self.assertFalse(connected)

    async def test_websocket_invalid_session(self):
        """Test WebSocket connection with invalid session"""
        invalid_session_id = str(uuid.uuid4())

        communicator = WebsocketCommunicator(
            VoiceConsumer.as_asgi(), f"/ws/voice/{invalid_session_id}/"
        )
        communicator.scope["user"] = self.user

        connected, subprotocol = await communicator.connect()
        self.assertFalse(connected)

    async def test_websocket_text_message_handling(self):
        """Test handling text messages via WebSocket"""
        communicator = WebsocketCommunicator(
            VoiceConsumer.as_asgi(), f"/ws/voice/{self.session.session_id}/"
        )
        communicator.scope["user"] = self.user

        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)

        # Skip connection confirmation
        await communicator.receive_json_from()

        # Send start recording message
        await communicator.send_json_to({"type": "start_recording"})

        # Should receive recording started confirmation
        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "recording_started")

        await communicator.disconnect()


class VoiceServiceIntegrationTest(TransactionTestCase):
    """Integration tests for voice service components"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    async def test_complete_call_workflow(self):
        """Test complete call workflow from initiation to end"""
        service = VoiceProcessingService()

        # 1. Initiate call
        session = await service.initiate_call(str(self.user.id))
        self.assertEqual(session.status, CallSession.Status.ACTIVE)

        # 2. Verify session is active
        status_info = await service.get_session_status(str(session.session_id))
        self.assertEqual(status_info["status"], CallSession.Status.ACTIVE)

        # 3. End call
        summary = await service.end_call(str(session.session_id))
        self.assertEqual(summary["status"], CallSession.Status.ENDED)

        # 4. Verify session is ended
        updated_session = await CallSession.objects.aget(session_id=session.session_id)
        self.assertEqual(updated_session.status, CallSession.Status.ENDED)
        self.assertIsNotNone(updated_session.end_time)

    def test_voice_configuration_defaults(self):
        """Test voice configuration default creation"""
        config, created = VoiceConfiguration.objects.get_or_create(
            user=self.user,
            defaults={"language_code": "en-US", "voice_name": "en-US-Wavenet-D"},
        )

        self.assertTrue(created)
        self.assertEqual(config.language_code, "en-US")
        self.assertEqual(config.voice_name, "en-US-Wavenet-D")
        self.assertTrue(config.enable_automatic_punctuation)
        self.assertTrue(config.auto_answer)
