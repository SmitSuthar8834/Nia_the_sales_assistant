"""
WebSocket consumers for voice service
"""

import json
import logging
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

from .services import voice_service, audio_buffer_manager
from .models import CallSession

User = get_user_model()
logger = logging.getLogger(__name__)


class VoiceConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time voice processing"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = None
        self.user = None
        self.call_session = None
        
    async def connect(self):
        """Handle WebSocket connection"""
        try:
            self.session_id = self.scope['url_route']['kwargs']['session_id']
            self.user = self.scope['user']
            
            if not self.user.is_authenticated:
                await self.close(code=4001)
                return
            
            # Verify session exists and belongs to user
            try:
                self.call_session = await database_sync_to_async(
                    CallSession.objects.get
                )(session_id=self.session_id, user=self.user)
            except CallSession.DoesNotExist:
                await self.close(code=4004)
                return
            
            # Join session group
            await self.channel_layer.group_add(
                f"voice_session_{self.session_id}",
                self.channel_name
            )
            
            await self.accept()
            
            # Send connection confirmation
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'session_id': self.session_id,
                'message': 'Connected to voice session'
            }))
            
            logger.info(f"WebSocket connected for session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Error connecting WebSocket: {str(e)}")
            await self.close(code=4000)
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        try:
            if self.session_id:
                # Leave session group
                await self.channel_layer.group_discard(
                    f"voice_session_{self.session_id}",
                    self.channel_name
                )
                
                # Clean up audio buffer
                audio_buffer_manager.remove_session_buffer(self.session_id)
                
                logger.info(f"WebSocket disconnected for session {self.session_id}")
                
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket: {str(e)}")
    
    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming WebSocket messages"""
        try:
            if text_data:
                # Handle text messages (control messages)
                await self._handle_text_message(text_data)
            elif bytes_data:
                # Handle binary messages (audio data)
                await self._handle_audio_data(bytes_data)
                
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def _handle_text_message(self, text_data):
        """Handle text-based control messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'start_recording':
                await self._start_recording()
            elif message_type == 'stop_recording':
                await self._stop_recording()
            elif message_type == 'generate_response':
                text = data.get('text', '')
                await self._generate_speech_response(text)
            elif message_type == 'end_call':
                await self._end_call()
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    async def _handle_audio_data(self, audio_data):
        """Handle incoming audio data"""
        try:
            # Add audio data to buffer
            await audio_buffer_manager.add_audio_data(self.session_id, audio_data)
            
            # Process audio for transcription
            result = await voice_service.process_audio_stream(
                self.session_id, audio_data
            )
            
            # Send transcription result
            await self.send(text_data=json.dumps({
                'type': 'transcription',
                'data': result
            }))
            
        except Exception as e:
            logger.error(f"Error processing audio data: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Audio processing error: {str(e)}'
            }))
    
    async def _start_recording(self):
        """Start audio recording"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'recording_started',
                'session_id': self.session_id,
                'message': 'Audio recording started'
            }))
            
        except Exception as e:
            logger.error(f"Error starting recording: {str(e)}")
    
    async def _stop_recording(self):
        """Stop audio recording"""
        try:
            # Clear audio buffer
            await audio_buffer_manager.clear_buffer(self.session_id)
            
            await self.send(text_data=json.dumps({
                'type': 'recording_stopped',
                'session_id': self.session_id,
                'message': 'Audio recording stopped'
            }))
            
        except Exception as e:
            logger.error(f"Error stopping recording: {str(e)}")
    
    async def _generate_speech_response(self, text):
        """Generate and send speech response"""
        try:
            # Generate speech audio
            audio_content = await voice_service.generate_speech_response(
                text, self.session_id
            )
            
            # Send audio response as binary data
            await self.send(bytes_data=audio_content)
            
            # Send confirmation message
            await self.send(text_data=json.dumps({
                'type': 'speech_generated',
                'text': text,
                'message': 'Speech response generated'
            }))
            
        except Exception as e:
            logger.error(f"Error generating speech: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Speech generation error: {str(e)}'
            }))
    
    async def _end_call(self):
        """End the call session"""
        try:
            # End call session
            summary = await voice_service.end_call(self.session_id)
            
            # Send call summary
            await self.send(text_data=json.dumps({
                'type': 'call_ended',
                'summary': summary
            }))
            
            # Close WebSocket connection
            await self.close()
            
        except Exception as e:
            logger.error(f"Error ending call: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error ending call: {str(e)}'
            }))
    
    # Group message handlers
    async def voice_message(self, event):
        """Handle voice messages sent to the group"""
        await self.send(text_data=json.dumps({
            'type': 'voice_message',
            'data': event['data']
        }))
    
    async def transcription_update(self, event):
        """Handle transcription updates sent to the group"""
        await self.send(text_data=json.dumps({
            'type': 'transcription_update',
            'data': event['data']
        }))