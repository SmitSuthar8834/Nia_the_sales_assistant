"""
Integration tests for voice processing pipeline
"""

import asyncio
import json
import os
import tempfile
import wave
from unittest.mock import Mock, patch, AsyncMock
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.conf import settings
from django.test.utils import override_settings
from rest_framework.test import APITestCase
from rest_framework import status
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async

from .models import CallSession, ConversationTurn, AudioChunk, VoiceConfiguration
from .services import (
    VoiceProcessingService, 
    ConversationContextManager, 
    ConversationSummaryService,
    AudioFileStorageService
)
from .consumers import VoiceConsumer

User = get_user_model()


class VoiceProcessingIntegrationTest(TransactionTestCase):
    """Integration tests for complete voice processing pipeline"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.voice_service = VoiceProcessingService()
        
    def tearDown(self):
        # Clean up any test files
        if hasattr(self, 'test_audio_files'):
            for file_path in self.test_audio_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
    
    def create_test_audio_data(self, duration_seconds=1, sample_rate=16000):
        """Create test audio data"""
        import numpy as np
        
        # Generate sine wave
        frequency = 440  # A4 note
        samples = int(duration_seconds * sample_rate)
        t = np.linspace(0, duration_seconds, samples, False)
        audio_data = np.sin(2 * np.pi * frequency * t)
        
        # Convert to 16-bit PCM
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Create WAV file in memory
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            with wave.open(temp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            with open(temp_file.name, 'rb') as f:
                audio_bytes = f.read()
            
            if not hasattr(self, 'test_audio_files'):
                self.test_audio_files = []
            self.test_audio_files.append(temp_file.name)
            
            return audio_bytes
    
    @patch('voice_service.services.speech.SpeechClient')
    @patch('voice_service.services.texttospeech.TextToSpeechClient')
    async def test_complete_voice_call_workflow(self, mock_tts_client, mock_speech_client):
        """Test complete voice call workflow from initiation to summary"""
        
        # Mock speech recognition response
        mock_recognition_result = Mock()
        mock_recognition_result.alternatives = [Mock()]
        mock_recognition_result.alternatives[0].transcript = "Hello, I have a lead from Acme Corp"
        mock_recognition_result.alternatives[0].confidence = 0.95
        
        mock_speech_response = Mock()
        mock_speech_response.results = [mock_recognition_result]
        mock_speech_client.return_value.recognize.return_value = mock_speech_response
        
        # Mock TTS response
        mock_tts_response = Mock()
        mock_tts_response.audio_content = b'fake_audio_content'
        mock_tts_client.return_value.synthesize_speech.return_value = mock_tts_response
        
        # 1. Initiate call
        session = await self.voice_service.initiate_call(str(self.user.id))
        self.assertIsNotNone(session)
        self.assertEqual(session.status, CallSession.Status.ACTIVE)
        
        # Verify conversation context was initialized
        context = self.voice_service.context_manager.get_context(str(session.session_id))
        self.assertIsNotNone(context)
        self.assertEqual(context['conversation_state'], 'greeting')
        
        # 2. Process audio input
        test_audio = self.create_test_audio_data()
        result = await self.voice_service.process_audio_stream(
            str(session.session_id), 
            test_audio
        )
        
        self.assertEqual(result['transcription'], "Hello, I have a lead from Acme Corp")
        self.assertEqual(result['confidence'], 0.95)
        self.assertIn('entities', result)
        
        # Verify conversation turn was created
        turns = await ConversationTurn.objects.filter(session=session).acount()
        self.assertEqual(turns, 1)
        
        # Verify context was updated
        updated_context = self.voice_service.context_manager.get_context(str(session.session_id))
        self.assertEqual(len(updated_context['conversation_flow']), 1)
        self.assertIn('companies', updated_context['extracted_entities'])
        
        # 3. Generate speech response
        response_audio = await self.voice_service.generate_speech_response(
            "Thank you for calling NIA. Tell me more about this lead.",
            str(session.session_id)
        )
        
        self.assertEqual(response_audio, b'fake_audio_content')
        
        # Verify NIA response turn was created
        turns = await ConversationTurn.objects.filter(session=session).acount()
        self.assertEqual(turns, 2)
        
        # 4. Process another user input
        result2 = await self.voice_service.process_audio_stream(
            str(session.session_id),
            test_audio
        )
        
        # 5. End call and get summary
        summary = await self.voice_service.end_call(str(session.session_id))
        
        self.assertEqual(summary['status'], CallSession.Status.ENDED)
        self.assertEqual(summary['conversation_turns'], 3)
        self.assertIn('conversation_summary', summary)
        self.assertIn('lead_information', summary)
        
        # Verify session was properly ended
        await session.arefresh_from_db()
        self.assertEqual(session.status, CallSession.Status.ENDED)
        self.assertIsNotNone(session.end_time)
        self.assertIsNotNone(session.call_duration)
    
    async def test_conversation_context_management(self):
        """Test conversation context tracking across multiple turns"""
        
        context_manager = ConversationContextManager()
        session_id = "test-session-123"
        user_id = str(self.user.id)
        
        # Initialize context
        context = context_manager.initialize_context(session_id, user_id)
        self.assertEqual(context['session_id'], session_id)
        self.assertEqual(context['user_id'], user_id)
        self.assertEqual(context['conversation_state'], 'greeting')
        
        # Update context with extracted entities
        updates = {
            'extracted_entities': {
                'companies': ['Acme Corp'],
                'emails': ['john@acme.com']
            },
            'conversation_state': 'lead_discussion',
            'current_topic': 'company_info'
        }
        
        updated_context = context_manager.update_context(session_id, updates)
        self.assertIn('Acme Corp', updated_context['extracted_entities']['companies'])
        self.assertEqual(updated_context['conversation_state'], 'lead_discussion')
        
        # Add conversation flow
        flow_update = {
            'conversation_flow': [{
                'turn': 1,
                'speaker': 'user',
                'content': 'I have a lead from Acme Corp',
                'timestamp': '2024-01-01T10:00:00Z'
            }]
        }
        
        context_manager.update_context(session_id, flow_update)
        final_context = context_manager.get_context(session_id)
        self.assertEqual(len(final_context['conversation_flow']), 1)
        
        # Clear context
        context_manager.clear_context(session_id)
        self.assertEqual(context_manager.get_context(session_id), {})
    
    @patch('voice_service.services.genai')
    async def test_conversation_summary_generation(self, mock_genai):
        """Test conversation summary generation with AI"""
        
        # Create test session and conversation turns
        session = await CallSession.objects.acreate(
            user=self.user,
            status=CallSession.Status.ENDED
        )
        
        # Create conversation turns
        await ConversationTurn.objects.acreate(
            session=session,
            turn_number=1,
            speaker=ConversationTurn.Speaker.USER,
            content="Hi, I have a potential lead from Acme Corporation. They're looking for a CRM solution."
        )
        
        await ConversationTurn.objects.acreate(
            session=session,
            turn_number=2,
            speaker=ConversationTurn.Speaker.NIA,
            content="Great! Tell me more about their requirements and pain points."
        )
        
        await ConversationTurn.objects.acreate(
            session=session,
            turn_number=3,
            speaker=ConversationTurn.Speaker.USER,
            content="They have 50 employees and need better lead tracking. Budget is around $10,000."
        )
        
        # Mock AI response
        mock_response = Mock()
        mock_response.text = json.dumps({
            'summary': 'Discussion about Acme Corporation CRM needs',
            'lead_information': {
                'company_name': 'Acme Corporation',
                'contact_details': {},
                'pain_points': ['lead tracking'],
                'requirements': ['CRM solution'],
                'budget_info': {'amount': '$10,000'},
                'timeline': ''
            },
            'key_points': ['50 employees', 'CRM solution needed', '$10,000 budget'],
            'action_items': ['Follow up with proposal'],
            'next_steps': ['Prepare CRM demo', 'Send pricing information'],
            'lead_quality_score': 85,
            'conversion_probability': 0.7
        })
        
        mock_model = Mock()
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Generate summary
        summary_service = ConversationSummaryService()
        summary_service._model = mock_model
        
        summary = await summary_service.generate_conversation_summary(str(session.session_id))
        
        self.assertEqual(summary['lead_information']['company_name'], 'Acme Corporation')
        self.assertIn('lead tracking', summary['lead_information']['pain_points'])
        self.assertEqual(summary['lead_quality_score'], 85)
        self.assertEqual(summary['conversion_probability'], 0.7)
    
    async def test_audio_file_storage_and_retrieval(self):
        """Test audio file storage and retrieval system"""
        
        storage_service = AudioFileStorageService()
        session_id = "test-session-456"
        test_audio = self.create_test_audio_data()
        
        # Store audio file
        file_path = await storage_service.store_audio_file(
            session_id,
            test_audio,
            'wav',
            {'test': 'metadata'}
        )
        
        self.assertTrue(os.path.exists(file_path))
        self.assertIn(session_id, file_path)
        
        # Retrieve audio file
        retrieved_audio = await storage_service.retrieve_audio_file(file_path)
        self.assertEqual(len(retrieved_audio), len(test_audio))
        
        # Get session audio files
        session_files = await storage_service.get_session_audio_files(session_id)
        self.assertEqual(len(session_files), 1)
        self.assertEqual(session_files[0], file_path)
        
        # Clean up
        await storage_service.delete_session_audio_files(session_id)
        self.assertFalse(os.path.exists(file_path))


class VoiceAPIIntegrationTest(APITestCase):
    """Integration tests for voice service API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_complete_api_workflow(self):
        """Test complete API workflow"""
        
        # 1. Initiate call
        response = self.client.post('/api/voice/initiate/', {
            'caller_id': '+1234567890'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        session_id = response.data['session_id']
        
        # 2. Get session status
        response = self.client.get(f'/api/voice/session/{session_id}/status/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'active')
        
        # 3. Get conversation context
        response = self.client.get(f'/api/voice/session/{session_id}/context/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('conversation_state', response.data)
        
        # 4. End call
        response = self.client.post('/api/voice/end/', {
            'session_id': session_id
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('conversation_summary', response.data)
        
        # 5. Get conversation summary
        response = self.client.get(f'/api/voice/session/{session_id}/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('summary', response.data)
    
    def test_voice_configuration_management(self):
        """Test voice configuration API"""
        
        # Get default configuration
        response = self.client.get('/api/voice/config/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['language_code'], 'en-US')
        
        # Update configuration
        response = self.client.put('/api/voice/config/', {
            'language_code': 'es-ES',
            'speaking_rate': 1.2,
            'pitch': 0.5
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify update
        response = self.client.get('/api/voice/config/')
        self.assertEqual(response.data['language_code'], 'es-ES')
        self.assertEqual(response.data['speaking_rate'], 1.2)


class VoiceWebSocketIntegrationTest(TransactionTestCase):
    """Integration tests for WebSocket voice processing"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    async def test_websocket_voice_processing(self):
        """Test WebSocket voice processing workflow"""
        
        # Create call session
        session = await CallSession.objects.acreate(
            user=self.user,
            status=CallSession.Status.ACTIVE
        )
        
        # Create WebSocket communicator
        communicator = WebsocketCommunicator(
            VoiceConsumer.as_asgi(),
            f"/ws/voice/{session.session_id}/"
        )
        communicator.scope['user'] = self.user
        
        # Connect
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Receive connection confirmation
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'connection_established')
        
        # Send start recording message
        await communicator.send_json_to({
            'type': 'start_recording'
        })
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'recording_started')
        
        # Send audio data (mock)
        test_audio = b'fake_audio_data'
        await communicator.send_bytes_to(test_audio)
        
        # Should receive transcription (mocked)
        # Note: This would require mocking the speech recognition service
        
        # Send end call message
        await communicator.send_json_to({
            'type': 'end_call'
        })
        
        # Should receive call ended message and connection close
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'call_ended')
        
        # Disconnect
        await communicator.disconnect()


class VoiceProcessingPerformanceTest(TransactionTestCase):
    """Performance tests for voice processing pipeline"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.voice_service = VoiceProcessingService()
    
    async def test_concurrent_voice_sessions(self):
        """Test handling multiple concurrent voice sessions"""
        
        session_count = 5
        sessions = []
        
        # Create multiple sessions
        for i in range(session_count):
            session = await self.voice_service.initiate_call(str(self.user.id))
            sessions.append(session)
        
        # Verify all sessions are active
        self.assertEqual(len(self.voice_service.active_sessions), session_count)
        
        # End all sessions
        summaries = []
        for session in sessions:
            summary = await self.voice_service.end_call(str(session.session_id))
            summaries.append(summary)
        
        # Verify all sessions ended properly
        self.assertEqual(len(summaries), session_count)
        self.assertEqual(len(self.voice_service.active_sessions), 0)
    
    async def test_large_conversation_processing(self):
        """Test processing large conversations"""
        
        session = await self.voice_service.initiate_call(str(self.user.id))
        
        # Create many conversation turns
        turn_count = 50
        for i in range(turn_count):
            await ConversationTurn.objects.acreate(
                session=session,
                turn_number=i + 1,
                speaker=ConversationTurn.Speaker.USER if i % 2 == 0 else ConversationTurn.Speaker.NIA,
                content=f"This is conversation turn number {i + 1}"
            )
        
        # Generate summary
        summary_service = ConversationSummaryService()
        summary = await summary_service.generate_conversation_summary(str(session.session_id))
        
        self.assertIsNotNone(summary)
        self.assertIn('summary', summary)
        
        # End session
        final_summary = await self.voice_service.end_call(str(session.session_id))
        self.assertEqual(final_summary['conversation_turns'], turn_count)