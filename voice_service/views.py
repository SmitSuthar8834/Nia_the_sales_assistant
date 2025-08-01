"""
Voice service API views
"""

import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from asgiref.sync import sync_to_async
import asyncio

from .services import voice_service, audio_buffer_manager
from .models import CallSession, VoiceConfiguration

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_call(request):
    """Initiate a new voice call session"""
    try:
        caller_id = request.data.get('caller_id', '')
        
        # Create session synchronously for now
        from .models import CallSession
        session = CallSession.objects.create(
            user=request.user,
            caller_id=caller_id,
            status=CallSession.Status.ACTIVE,
            conversation_context={},
            session_metadata={
                'initiated_at': timezone.now().isoformat(),
                'caller_id': caller_id
            }
        )
        
        # Initialize conversation context
        context = voice_service.context_manager.initialize_context(
            str(session.session_id), 
            str(request.user.id)
        )
        
        # Update session with initial context
        session.conversation_context = context
        session.save()
        
        # Store in active sessions
        voice_service.active_sessions[str(session.session_id)] = session
        
        return Response({
            'session_id': str(session.session_id),
            'status': session.status,
            'start_time': session.start_time.isoformat(),
            'message': 'Call session initiated successfully'
        }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        logger.error(f"Error initiating call: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setup_webrtc(request):
    """Setup WebRTC connection for voice call"""
    try:
        session_id = request.data.get('session_id')
        offer = request.data.get('offer')
        
        if not session_id or not offer:
            return Response({
                'error': 'session_id and offer are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            answer = loop.run_until_complete(
                voice_service.setup_webrtc_connection(session_id, offer)
            )
            
            return Response({
                'answer': answer,
                'message': 'WebRTC connection established'
            }, status=status.HTTP_200_OK)
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error setting up WebRTC: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_audio(request):
    """Process audio stream for transcription"""
    try:
        session_id = request.data.get('session_id')
        
        if not session_id:
            return Response({
                'error': 'session_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get audio data from request
        audio_data = request.FILES.get('audio')
        if not audio_data:
            return Response({
                'error': 'audio file is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Read audio data
        audio_bytes = audio_data.read()
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                voice_service.process_audio_stream(session_id, audio_bytes)
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_speech(request):
    """Generate speech response"""
    try:
        session_id = request.data.get('session_id')
        text = request.data.get('text')
        
        if not session_id or not text:
            return Response({
                'error': 'session_id and text are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            audio_content = loop.run_until_complete(
                voice_service.generate_speech_response(text, session_id)
            )
            
            # Return audio as HTTP response
            response = HttpResponse(audio_content, content_type='audio/wav')
            response['Content-Disposition'] = f'attachment; filename="response_{session_id}.wav"'
            return response
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error generating speech: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def end_call(request):
    """End voice call session"""
    try:
        session_id = request.data.get('session_id')
        
        if not session_id:
            return Response({
                'error': 'session_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get session from active sessions or database
        from .models import CallSession
        session = voice_service.active_sessions.get(session_id)
        if not session:
            try:
                session = CallSession.objects.get(session_id=session_id, user=request.user)
            except CallSession.DoesNotExist:
                return Response({
                    'error': f'Session {session_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Update session status
        session.status = CallSession.Status.ENDED
        session.end_time = timezone.now()
        session.call_duration = session.end_time - session.start_time
        session.save()
        
        # Remove from active sessions
        if session_id in voice_service.active_sessions:
            del voice_service.active_sessions[session_id]
        
        # Generate comprehensive conversation summary
        from .services import conversation_summary_service
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            conversation_summary = loop.run_until_complete(
                conversation_summary_service.generate_conversation_summary(session_id)
            )
        finally:
            loop.close()
        
        # Update session with final conversation context and summary
        if session_id in voice_service.context_manager.contexts:
            final_context = voice_service.context_manager.get_context(session_id)
            final_context['conversation_summary'] = conversation_summary
            session.conversation_context = final_context
            session.save()
            
            # Clear conversation context
            voice_service.context_manager.clear_context(session_id)
        
        # Generate call summary
        from .models import ConversationTurn, AudioChunk
        conversation_turns = ConversationTurn.objects.filter(session=session).count()
        audio_chunks = AudioChunk.objects.filter(session=session).count()
        
        summary = {
            'session_id': session_id,
            'duration': str(session.call_duration),
            'conversation_turns': conversation_turns,
            'audio_chunks_processed': audio_chunks,
            'end_time': session.end_time.isoformat(),
            'status': session.status,
            'conversation_summary': conversation_summary,
            'lead_information': conversation_summary.get('lead_information', {}),
            'key_points': conversation_summary.get('key_points', []),
            'action_items': conversation_summary.get('action_items', []),
            'next_steps': conversation_summary.get('next_steps', []),
            'lead_quality_score': conversation_summary.get('lead_quality_score', 0),
            'conversion_probability': conversation_summary.get('conversion_probability', 0.0)
        }
        
        return Response(summary, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error ending call: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def session_status(request, session_id):
    """Get call session status"""
    try:
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            status_info = loop.run_until_complete(
                voice_service.get_session_status(session_id)
            )
            
            return Response(status_info, status=status.HTTP_200_OK)
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error getting session status: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_call_sessions(request):
    """Get user's call sessions"""
    try:
        sessions = CallSession.objects.filter(user=request.user).order_by('-start_time')[:20]
        
        sessions_data = []
        for session in sessions:
            sessions_data.append({
                'session_id': str(session.session_id),
                'status': session.status,
                'start_time': session.start_time.isoformat(),
                'end_time': session.end_time.isoformat() if session.end_time else None,
                'duration': str(session.call_duration) if session.call_duration else None,
                'caller_id': session.caller_id
            })
        
        return Response({
            'sessions': sessions_data,
            'count': len(sessions_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting user sessions: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def voice_configuration(request):
    """Get or update user's voice configuration"""
    try:
        # Get or create voice configuration
        config, created = VoiceConfiguration.objects.get_or_create(
            user=request.user,
            defaults={
                'language_code': 'en-US',
                'voice_name': 'en-US-Wavenet-D',
                'speaking_rate': 1.0,
                'pitch': 0.0,
                'volume_gain_db': 0.0,
                'auto_answer': True,
                'max_call_duration_minutes': 30,
                'silence_timeout_seconds': 10
            }
        )
        
        if request.method == 'GET':
            return Response({
                'language_code': config.language_code,
                'enable_automatic_punctuation': config.enable_automatic_punctuation,
                'enable_word_time_offsets': config.enable_word_time_offsets,
                'speech_contexts': config.speech_contexts,
                'voice_name': config.voice_name,
                'speaking_rate': config.speaking_rate,
                'pitch': config.pitch,
                'volume_gain_db': config.volume_gain_db,
                'auto_answer': config.auto_answer,
                'max_call_duration_minutes': config.max_call_duration_minutes,
                'silence_timeout_seconds': config.silence_timeout_seconds
            }, status=status.HTTP_200_OK)
        
        elif request.method == 'PUT':
            # Update configuration
            for field in ['language_code', 'enable_automatic_punctuation', 
                         'enable_word_time_offsets', 'speech_contexts', 'voice_name',
                         'speaking_rate', 'pitch', 'volume_gain_db', 'auto_answer',
                         'max_call_duration_minutes', 'silence_timeout_seconds']:
                if field in request.data:
                    setattr(config, field, request.data[field])
            
            config.save()
            
            return Response({
                'message': 'Voice configuration updated successfully'
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error handling voice configuration: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversation_context(request, session_id):
    """Get conversation context for a session"""
    try:
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            context = loop.run_until_complete(
                voice_service.get_conversation_context(session_id)
            )
            
            return Response(context, status=status.HTTP_200_OK)
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error getting conversation context: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversation_summary(request, session_id):
    """Get conversation summary for a session"""
    try:
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            summary = loop.run_until_complete(
                voice_service.get_conversation_summary(session_id)
            )
            
            return Response(summary, status=status.HTTP_200_OK)
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error getting conversation summary: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def session_audio_files(request, session_id):
    """Get audio files for a session"""
    try:
        from .services import audio_storage_service
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            audio_files = loop.run_until_complete(
                audio_storage_service.get_session_audio_files(session_id)
            )
            
            return Response({
                'session_id': session_id,
                'audio_files': audio_files,
                'count': len(audio_files)
            }, status=status.HTTP_200_OK)
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error getting session audio files: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_audio_file(request, session_id, filename):
    """Download a specific audio file"""
    try:
        from .services import audio_storage_service
        import os
        
        # Construct file path
        file_path = os.path.join(audio_storage_service.storage_path, filename)
        
        # Verify file belongs to session
        if not filename.startswith(session_id):
            return Response({
                'error': 'File does not belong to this session'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            audio_data = loop.run_until_complete(
                audio_storage_service.retrieve_audio_file(file_path)
            )
            
            # Return audio file
            response = HttpResponse(audio_data, content_type='audio/wav')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        finally:
            loop.close()
            
    except FileNotFoundError:
        return Response({
            'error': 'Audio file not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error downloading audio file: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)