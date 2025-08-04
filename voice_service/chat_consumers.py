"""
WebSocket consumers for smart chat interface with voice fallback
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone

from .chat_models import ChatSession, ChatMessage, ChatBotCommand, ChatAnalytics
from .models import CallSession
from .services import voice_service

User = get_user_model()
logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time chat with voice fallback"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = None
        self.user = None
        self.chat_session = None
        self.room_group_name = None
        self.typing_timeout = None
        
    async def connect(self):
        """Handle WebSocket connection for chat"""
        try:
            self.session_id = self.scope['url_route']['kwargs']['session_id']
            self.user = self.scope['user']
            
            if not self.user.is_authenticated:
                await self.close(code=4001)
                return
            
            # Get or create chat session
            self.chat_session = await self.get_or_create_chat_session()
            
            # Join chat room group
            self.room_group_name = f"chat_{self.session_id}"
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # Send connection confirmation with session info
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'session_id': self.session_id,
                'status': self.chat_session.status,
                'voice_available': self.chat_session.user_available_for_voice,
                'message': 'Connected to chat session'
            }))
            
            # Send recent message history
            await self.send_message_history()
            
            # Send available bot commands
            await self.send_bot_commands()
            
            logger.info(f"Chat WebSocket connected for session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Error connecting chat WebSocket: {str(e)}")
            await self.close(code=4000)
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        try:
            if self.room_group_name:
                # Leave chat room group
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
            
            # Update last activity and stop typing indicator
            if self.chat_session:
                await self.update_session_activity(typing=False)
            
            # Cancel typing timeout if active
            if self.typing_timeout:
                self.typing_timeout.cancel()
            
            logger.info(f"Chat WebSocket disconnected for session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Error disconnecting chat WebSocket: {str(e)}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'typing_start':
                await self.handle_typing_start()
            elif message_type == 'typing_stop':
                await self.handle_typing_stop()
            elif message_type == 'mark_read':
                await self.handle_mark_read(data)
            elif message_type == 'bot_command':
                await self.handle_bot_command(data)
            elif message_type == 'request_voice_transition':
                await self.handle_voice_transition_request(data)
            elif message_type == 'update_availability':
                await self.handle_availability_update(data)
            elif message_type == 'file_upload':
                await self.handle_file_upload(data)
            elif message_type == 'search_history':
                await self.handle_search_history(data)
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
        except Exception as e:
            logger.error(f"Error handling chat message: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def handle_chat_message(self, data):
        """Handle incoming chat message"""
        try:
            content = data.get('content', '').strip()
            if not content:
                return
            
            # Create chat message
            message = await self.create_chat_message(
                content=content,
                sender=ChatMessage.Sender.USER,
                message_type=data.get('message_type', ChatMessage.MessageType.TEXT)
            )
            
            # Broadcast message to room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message_broadcast',
                    'message': await self.serialize_message(message)
                }
            )
            
            # Process message for AI analysis
            await self.process_message_ai(message)
            
            # Generate NIA response if needed
            await self.generate_nia_response(message)
            
        except Exception as e:
            logger.error(f"Error handling chat message: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to send message'
            }))
    
    async def handle_typing_start(self):
        """Handle typing indicator start"""
        try:
            await self.update_session_activity(typing=True)
            
            # Broadcast typing indicator
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': str(self.user.id),
                    'username': self.user.username,
                    'typing': True
                }
            )
            
            # Set timeout to automatically stop typing indicator
            if self.typing_timeout:
                self.typing_timeout.cancel()
            
            self.typing_timeout = asyncio.create_task(
                self.auto_stop_typing()
            )
            
        except Exception as e:
            logger.error(f"Error handling typing start: {str(e)}")
    
    async def handle_typing_stop(self):
        """Handle typing indicator stop"""
        try:
            await self.update_session_activity(typing=False)
            
            # Cancel timeout
            if self.typing_timeout:
                self.typing_timeout.cancel()
                self.typing_timeout = None
            
            # Broadcast typing stop
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': str(self.user.id),
                    'username': self.user.username,
                    'typing': False
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling typing stop: {str(e)}")
    
    async def auto_stop_typing(self):
        """Automatically stop typing indicator after timeout"""
        try:
            await asyncio.sleep(5)  # 5 second timeout
            await self.handle_typing_stop()
        except asyncio.CancelledError:
            pass
    
    async def handle_mark_read(self, data):
        """Handle message read receipts"""
        try:
            message_ids = data.get('message_ids', [])
            if message_ids:
                await self.mark_messages_read(message_ids)
                
                # Broadcast read receipts
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'read_receipt',
                        'message_ids': message_ids,
                        'user_id': str(self.user.id),
                        'read_at': timezone.now().isoformat()
                    }
                )
                
        except Exception as e:
            logger.error(f"Error handling mark read: {str(e)}")
    
    async def handle_bot_command(self, data):
        """Handle bot commands"""
        try:
            command = data.get('command', '').strip()
            if not command.startswith('/'):
                return
            
            command_name = command[1:].split()[0].lower()
            command_args = command.split()[1:] if len(command.split()) > 1 else []
            
            # Execute bot command
            response = await self.execute_bot_command(command_name, command_args, data)
            
            if response:
                # Create system message with command response
                message = await self.create_chat_message(
                    content=response['content'],
                    sender=ChatMessage.Sender.NIA,
                    message_type=ChatMessage.MessageType.SYSTEM,
                    metadata=response.get('metadata', {})
                )
                
                # Broadcast response
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message_broadcast',
                        'message': await self.serialize_message(message)
                    }
                )
                
        except Exception as e:
            logger.error(f"Error handling bot command: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to execute command'
            }))
    
    async def handle_voice_transition_request(self, data):
        """Handle request to transition to voice call"""
        try:
            reason = data.get('reason', 'user_request')
            
            # Update chat session status
            await self.update_chat_session_status(
                ChatSession.Status.VOICE_TRANSITION,
                voice_transition_requested=True,
                voice_transition_time=timezone.now()
            )
            
            # Create voice call session
            voice_session = await self.create_voice_session()
            
            # Link voice session to chat session
            await self.link_voice_session(voice_session)
            
            # Send voice transition response
            await self.send(text_data=json.dumps({
                'type': 'voice_transition_ready',
                'voice_session_id': str(voice_session.session_id),
                'webrtc_url': f'/ws/voice/{voice_session.session_id}/',
                'message': 'Voice call is ready. Click to join.'
            }))
            
            # Broadcast to room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'voice_transition_notification',
                    'voice_session_id': str(voice_session.session_id),
                    'reason': reason
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling voice transition: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to initiate voice call'
            }))
    
    async def handle_availability_update(self, data):
        """Handle user availability updates"""
        try:
            available_for_voice = data.get('available_for_voice', False)
            
            await self.update_user_availability(available_for_voice)
            
            # Broadcast availability update
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'availability_update',
                    'user_id': str(self.user.id),
                    'available_for_voice': available_for_voice
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling availability update: {str(e)}")
    
    async def handle_file_upload(self, data):
        """Handle file upload in chat"""
        try:
            file_info = data.get('file_info', {})
            
            # Create message with file attachment
            message = await self.create_chat_message(
                content=f"Shared file: {file_info.get('filename', 'Unknown')}",
                sender=ChatMessage.Sender.USER,
                message_type=ChatMessage.MessageType.FILE,
                attachments=[file_info]
            )
            
            # Broadcast file message
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message_broadcast',
                    'message': await self.serialize_message(message)
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling file upload: {str(e)}")
    
    async def handle_search_history(self, data):
        """Handle chat history search"""
        try:
            query = data.get('query', '').strip()
            if not query:
                return
            
            # Search chat history
            results = await self.search_chat_history(query)
            
            # Send search results
            await self.send(text_data=json.dumps({
                'type': 'search_results',
                'query': query,
                'results': results
            }))
            
        except Exception as e:
            logger.error(f"Error handling search history: {str(e)}")
    
    # Group message handlers
    async def chat_message_broadcast(self, event):
        """Handle chat message broadcast"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))
    
    async def typing_indicator(self, event):
        """Handle typing indicator broadcast"""
        # Don't send typing indicator to the user who is typing
        if event['user_id'] != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user_id': event['user_id'],
                'username': event['username'],
                'typing': event['typing']
            }))
    
    async def read_receipt(self, event):
        """Handle read receipt broadcast"""
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'message_ids': event['message_ids'],
            'user_id': event['user_id'],
            'read_at': event['read_at']
        }))
    
    async def voice_transition_notification(self, event):
        """Handle voice transition notification"""
        await self.send(text_data=json.dumps({
            'type': 'voice_transition_notification',
            'voice_session_id': event['voice_session_id'],
            'reason': event['reason']
        }))
    
    async def availability_update(self, event):
        """Handle availability update broadcast"""
        await self.send(text_data=json.dumps({
            'type': 'availability_update',
            'user_id': event['user_id'],
            'available_for_voice': event['available_for_voice']
        }))
    
    # Database operations
    @database_sync_to_async
    def get_or_create_chat_session(self):
        """Get or create chat session"""
        try:
            session = ChatSession.objects.get(session_id=self.session_id, user=self.user)
        except ChatSession.DoesNotExist:
            session = ChatSession.objects.create(
                session_id=self.session_id,
                user=self.user,
                status=ChatSession.Status.ACTIVE,
                chat_context={'created_via': 'websocket'}
            )
            
            # Create analytics record
            ChatAnalytics.objects.create(session=session)
        
        return session
    
    @database_sync_to_async
    def create_chat_message(self, content, sender, message_type=ChatMessage.MessageType.TEXT, 
                           attachments=None, metadata=None):
        """Create a new chat message"""
        # Get next message number
        last_message = ChatMessage.objects.filter(session=self.chat_session).order_by('-message_number').first()
        message_number = (last_message.message_number + 1) if last_message else 1
        
        message = ChatMessage.objects.create(
            session=self.chat_session,
            message_number=message_number,
            sender=sender,
            message_type=message_type,
            content=content,
            attachments=attachments or [],
            metadata=metadata or {}
        )
        
        # Update analytics
        analytics = self.chat_session.analytics
        analytics.total_messages += 1
        if sender == ChatMessage.Sender.USER:
            analytics.user_messages += 1
        elif sender == ChatMessage.Sender.NIA:
            analytics.nia_messages += 1
        analytics.save()
        
        return message
    
    @database_sync_to_async
    def serialize_message(self, message):
        """Serialize message for JSON response"""
        return {
            'id': str(message.id),
            'message_number': message.message_number,
            'timestamp': message.timestamp.isoformat(),
            'sender': message.sender,
            'message_type': message.message_type,
            'content': message.content,
            'attachments': message.attachments,
            'metadata': message.metadata,
            'status': message.status,
            'read_at': message.read_at.isoformat() if message.read_at else None
        }
    
    @database_sync_to_async
    def update_session_activity(self, typing=False):
        """Update session activity and typing status"""
        self.chat_session.last_activity = timezone.now()
        self.chat_session.typing_indicator_active = typing
        self.chat_session.save(update_fields=['last_activity', 'typing_indicator_active'])
    
    @database_sync_to_async
    def update_chat_session_status(self, status, **kwargs):
        """Update chat session status and other fields"""
        self.chat_session.status = status
        for field, value in kwargs.items():
            setattr(self.chat_session, field, value)
        self.chat_session.save()
    
    @database_sync_to_async
    def update_user_availability(self, available_for_voice):
        """Update user availability for voice calls"""
        self.chat_session.user_available_for_voice = available_for_voice
        self.chat_session.save(update_fields=['user_available_for_voice'])
    
    @database_sync_to_async
    def mark_messages_read(self, message_ids):
        """Mark messages as read"""
        ChatMessage.objects.filter(
            id__in=message_ids,
            session=self.chat_session
        ).update(
            status=ChatMessage.Status.READ,
            read_at=timezone.now()
        )
    
    @database_sync_to_async
    def create_voice_session(self):
        """Create a new voice call session"""
        return CallSession.objects.create(
            user=self.user,
            status=CallSession.Status.ACTIVE,
            conversation_context={'transitioned_from_chat': str(self.session_id)},
            session_metadata={'chat_session_id': str(self.session_id)}
        )
    
    @database_sync_to_async
    def link_voice_session(self, voice_session):
        """Link voice session to chat session"""
        self.chat_session.voice_session = voice_session
        self.chat_session.status = ChatSession.Status.VOICE_ACTIVE
        self.chat_session.save()
    
    async def send_message_history(self):
        """Send recent message history to client"""
        try:
            messages = await self.get_recent_messages()
            await self.send(text_data=json.dumps({
                'type': 'message_history',
                'messages': messages
            }))
        except Exception as e:
            logger.error(f"Error sending message history: {str(e)}")
    
    @database_sync_to_async
    def get_recent_messages(self, limit=50):
        """Get recent messages for the session"""
        messages = ChatMessage.objects.filter(
            session=self.chat_session
        ).order_by('-message_number')[:limit]
        
        return [
            {
                'id': str(msg.id),
                'message_number': msg.message_number,
                'timestamp': msg.timestamp.isoformat(),
                'sender': msg.sender,
                'message_type': msg.message_type,
                'content': msg.content,
                'attachments': msg.attachments,
                'status': msg.status,
                'read_at': msg.read_at.isoformat() if msg.read_at else None
            }
            for msg in reversed(messages)
        ]
    
    async def send_bot_commands(self):
        """Send available bot commands to client"""
        try:
            commands = await self.get_bot_commands()
            await self.send(text_data=json.dumps({
                'type': 'bot_commands',
                'commands': commands
            }))
        except Exception as e:
            logger.error(f"Error sending bot commands: {str(e)}")
    
    @database_sync_to_async
    def get_bot_commands(self):
        """Get available bot commands"""
        commands = ChatBotCommand.objects.filter(is_active=True)
        return [
            {
                'command': f"/{cmd.command}",
                'type': cmd.command_type,
                'description': cmd.description,
                'usage': cmd.usage_example,
                'parameters': cmd.parameters
            }
            for cmd in commands
        ]
    
    async def execute_bot_command(self, command_name, args, data):
        """Execute bot command and return response"""
        try:
            if command_name == 'help':
                return await self.cmd_help()
            elif command_name == 'schedule':
                return await self.cmd_schedule_call(args)
            elif command_name == 'lead':
                return await self.cmd_get_lead_info(args)
            elif command_name == 'voice':
                return await self.cmd_voice_transition()
            elif command_name == 'search':
                return await self.cmd_search_leads(args)
            else:
                return {
                    'content': f"Unknown command: /{command_name}. Type /help for available commands.",
                    'metadata': {'command_error': True}
                }
        except Exception as e:
            logger.error(f"Error executing bot command {command_name}: {str(e)}")
            return {
                'content': f"Error executing command: {str(e)}",
                'metadata': {'command_error': True}
            }
    
    async def cmd_help(self):
        """Help command implementation"""
        commands = await self.get_bot_commands()
        help_text = "Available commands:\n\n"
        for cmd in commands:
            help_text += f"{cmd['command']} - {cmd['description']}\n"
            help_text += f"Usage: {cmd['usage']}\n\n"
        
        return {
            'content': help_text,
            'metadata': {'command_type': 'help'}
        }
    
    async def cmd_schedule_call(self, args):
        """Schedule call command implementation"""
        # This would integrate with calendar systems
        return {
            'content': "Call scheduling feature coming soon! For now, you can request a voice transition using /voice.",
            'metadata': {'command_type': 'schedule_call'}
        }
    
    async def cmd_get_lead_info(self, args):
        """Get lead info command implementation"""
        if not args:
            return {
                'content': "Please specify a lead ID or company name. Usage: /lead <company_name>",
                'metadata': {'command_type': 'get_lead_info', 'error': 'missing_args'}
            }
        
        # This would query the lead database
        return {
            'content': f"Lead information for '{' '.join(args)}' - Feature coming soon!",
            'metadata': {'command_type': 'get_lead_info'}
        }
    
    async def cmd_voice_transition(self):
        """Voice transition command implementation"""
        return {
            'content': "Preparing voice call transition... Please wait.",
            'metadata': {'command_type': 'voice_transition', 'action': 'initiate'}
        }
    
    async def cmd_search_leads(self, args):
        """Search leads command implementation"""
        if not args:
            return {
                'content': "Please specify search terms. Usage: /search <search_terms>",
                'metadata': {'command_type': 'search_leads', 'error': 'missing_args'}
            }
        
        # This would search the lead database
        return {
            'content': f"Searching for leads matching '{' '.join(args)}'... Feature coming soon!",
            'metadata': {'command_type': 'search_leads'}
        }
    
    async def process_message_ai(self, message):
        """Process message with AI for entity extraction and intent recognition"""
        try:
            # This would integrate with the AI service
            # For now, we'll just log that processing would happen here
            logger.info(f"AI processing message {message.id} - content: {message.content[:100]}...")
        except Exception as e:
            logger.error(f"Error processing message with AI: {str(e)}")
    
    async def generate_nia_response(self, user_message):
        """Generate NIA response to user message"""
        try:
            # Simple response logic - in production this would use AI
            content = user_message.content.lower()
            
            response_content = None
            
            if any(word in content for word in ['hello', 'hi', 'hey']):
                response_content = "Hello! I'm NIA, your AI sales assistant. How can I help you today?"
            elif any(word in content for word in ['help', 'assist', 'support']):
                response_content = "I'm here to help! You can ask me about leads, schedule calls, or use commands like /help to see what I can do."
            elif any(word in content for word in ['lead', 'customer', 'prospect']):
                response_content = "I can help you with lead management. Would you like to create a new lead, search existing ones, or get insights on a specific lead?"
            elif any(word in content for word in ['call', 'voice', 'phone']):
                response_content = "Would you like to transition to a voice call? I can set that up for you right away. Just let me know when you're ready!"
            
            if response_content:
                # Create NIA response message
                response_message = await self.create_chat_message(
                    content=response_content,
                    sender=ChatMessage.Sender.NIA,
                    message_type=ChatMessage.MessageType.TEXT
                )
                
                # Broadcast NIA response
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message_broadcast',
                        'message': await self.serialize_message(response_message)
                    }
                )
                
        except Exception as e:
            logger.error(f"Error generating NIA response: {str(e)}")
    
    @database_sync_to_async
    def search_chat_history(self, query):
        """Search chat history"""
        from .chat_models import ChatSearchHistory
        
        # Simple search implementation
        search_results = ChatSearchHistory.objects.filter(
            user=self.user,
            searchable_content__icontains=query
        )[:10]
        
        return [
            {
                'session_id': str(result.session.session_id),
                'summary': result.conversation_summary,
                'created_at': result.created_at.isoformat(),
                'lead_info': result.lead_information
            }
            for result in search_results
        ]