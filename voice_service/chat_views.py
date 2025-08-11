"""
API views for smart chat interface with voice fallback
"""

import logging

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .chat_models import (
    ChatAnalytics,
    ChatBotCommand,
    ChatFile,
    ChatMessage,
    ChatSession,
)

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_chat_session(request):
    """Create a new chat session"""
    try:
        priority = request.data.get("priority", ChatSession.Priority.MEDIUM)
        initial_message = request.data.get("initial_message", "")

        # Create chat session
        session = ChatSession.objects.create(
            user=request.user,
            priority=priority,
            status=ChatSession.Status.ACTIVE,
            chat_context={"created_via": "api", "initial_message": initial_message},
        )

        # Create analytics record
        ChatAnalytics.objects.create(session=session)

        # Send initial message if provided
        if initial_message:
            ChatMessage.objects.create(
                session=session,
                message_number=1,
                sender=ChatMessage.Sender.USER,
                content=initial_message,
            )

        return Response(
            {
                "session_id": str(session.session_id),
                "status": session.status,
                "websocket_url": f"/ws/chat/{session.session_id}/",
                "message": "Chat session created successfully",
            },
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        logger.error(f"Error creating chat session: {str(e)}")
        return Response(
            {"error": "Failed to create chat session", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_chat_sessions(request):
    """Get user's chat sessions"""
    try:
        sessions = (
            ChatSession.objects.filter(user=request.user)
            .select_related("voice_session")
            .prefetch_related("analytics")
        )

        sessions_data = []
        for session in sessions:
            session_data = {
                "session_id": str(session.session_id),
                "start_time": session.start_time.isoformat(),
                "end_time": session.end_time.isoformat() if session.end_time else None,
                "status": session.status,
                "priority": session.priority,
                "voice_session_id": (
                    str(session.voice_session.session_id)
                    if session.voice_session
                    else None
                ),
                "last_activity": session.last_activity.isoformat(),
                "message_count": (
                    session.analytics.total_messages
                    if hasattr(session, "analytics")
                    else 0
                ),
            }
            sessions_data.append(session_data)

        return Response({"sessions": sessions_data, "total_count": len(sessions_data)})

    except Exception as e:
        logger.error(f"Error getting chat sessions: {str(e)}")
        return Response(
            {"error": "Failed to get chat sessions", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_chat_session(request, session_id):
    """Get specific chat session details"""
    try:
        session = ChatSession.objects.select_related("voice_session", "analytics").get(
            session_id=session_id, user=request.user
        )

        # Get recent messages
        messages = ChatMessage.objects.filter(session=session).order_by(
            "message_number"
        )[:50]
        messages_data = [
            {
                "id": str(msg.id),
                "message_number": msg.message_number,
                "timestamp": msg.timestamp.isoformat(),
                "sender": msg.sender,
                "message_type": msg.message_type,
                "content": msg.content,
                "attachments": msg.attachments,
                "status": msg.status,
                "read_at": msg.read_at.isoformat() if msg.read_at else None,
            }
            for msg in messages
        ]

        session_data = {
            "session_id": str(session.session_id),
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "status": session.status,
            "priority": session.priority,
            "voice_session_id": (
                str(session.voice_session.session_id) if session.voice_session else None
            ),
            "user_available_for_voice": session.user_available_for_voice,
            "last_activity": session.last_activity.isoformat(),
            "messages": messages_data,
            "websocket_url": f"/ws/chat/{session.session_id}/",
            "analytics": (
                {
                    "total_messages": session.analytics.total_messages,
                    "user_messages": session.analytics.user_messages,
                    "nia_messages": session.analytics.nia_messages,
                    "session_duration": (
                        str(session.analytics.session_duration)
                        if session.analytics.session_duration
                        else None
                    ),
                }
                if hasattr(session, "analytics")
                else None
            ),
        }

        return Response(session_data)

    except ChatSession.DoesNotExist:
        return Response(
            {"error": "Chat session not found"}, status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error getting chat session: {str(e)}")
        return Response(
            {"error": "Failed to get chat session", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def end_chat_session(request, session_id):
    """End a chat session"""
    try:
        session = ChatSession.objects.get(session_id=session_id, user=request.user)

        session.status = ChatSession.Status.ENDED
        session.end_time = timezone.now()
        session.save()

        # Update analytics
        if hasattr(session, "analytics"):
            analytics = session.analytics
            analytics.session_duration = session.end_time - session.start_time
            analytics.save()

        return Response(
            {
                "message": "Chat session ended successfully",
                "session_id": str(session.session_id),
                "end_time": session.end_time.isoformat(),
            }
        )

    except ChatSession.DoesNotExist:
        return Response(
            {"error": "Chat session not found"}, status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error ending chat session: {str(e)}")
        return Response(
            {"error": "Failed to end chat session", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_bot_commands(request):
    """Get available bot commands"""
    try:
        commands = ChatBotCommand.objects.filter(is_active=True)
        commands_data = [
            {
                "command": f"/{cmd.command}",
                "type": cmd.command_type,
                "description": cmd.description,
                "usage": cmd.usage_example,
                "parameters": cmd.parameters,
            }
            for cmd in commands
        ]

        return Response({"commands": commands_data, "total_count": len(commands_data)})

    except Exception as e:
        logger.error(f"Error getting bot commands: {str(e)}")
        return Response(
            {"error": "Failed to get bot commands", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_chat_file(request, session_id):
    """Upload file to chat session"""
    try:
        session = ChatSession.objects.get(session_id=session_id, user=request.user)

        if "file" not in request.FILES:
            return Response(
                {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        uploaded_file = request.FILES["file"]

        # Create message with file attachment
        last_message = (
            ChatMessage.objects.filter(session=session)
            .order_by("-message_number")
            .first()
        )
        message_number = (last_message.message_number + 1) if last_message else 1

        message = ChatMessage.objects.create(
            session=session,
            message_number=message_number,
            sender=ChatMessage.Sender.USER,
            message_type=ChatMessage.MessageType.FILE,
            content=f"Shared file: {uploaded_file.name}",
            attachments=[
                {
                    "filename": uploaded_file.name,
                    "size": uploaded_file.size,
                    "content_type": uploaded_file.content_type,
                }
            ],
        )

        # Create file record
        ChatFile.objects.create(
            message=message,
            original_filename=uploaded_file.name,
            file_path=f"chat_files/{session_id}/{uploaded_file.name}",
            file_size=uploaded_file.size,
            file_type=ChatFile.FileType.DOCUMENT,  # Simplified for now
            mime_type=uploaded_file.content_type or "application/octet-stream",
        )

        return Response(
            {
                "message_id": str(message.id),
                "filename": uploaded_file.name,
                "size": uploaded_file.size,
                "message": "File uploaded successfully",
            },
            status=status.HTTP_201_CREATED,
        )

    except ChatSession.DoesNotExist:
        return Response(
            {"error": "Chat session not found"}, status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error uploading chat file: {str(e)}")
        return Response(
            {"error": "Failed to upload file", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search_chat_history(request):
    """Search chat history"""
    try:
        query = request.GET.get("query", "").strip()
        if not query:
            return Response(
                {"error": "Search query is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Search in chat messages
        messages = (
            ChatMessage.objects.filter(
                session__user=request.user, content__icontains=query
            )
            .select_related("session")
            .order_by("-timestamp")[:50]
        )

        results = []
        for message in messages:
            results.append(
                {
                    "message_id": str(message.id),
                    "session_id": str(message.session.session_id),
                    "timestamp": message.timestamp.isoformat(),
                    "sender": message.sender,
                    "content": message.content,
                    "message_type": message.message_type,
                    "session_start": message.session.start_time.isoformat(),
                }
            )

        return Response(
            {"query": query, "results": results, "total_count": len(results)}
        )

    except Exception as e:
        logger.error(f"Error searching chat history: {str(e)}")
        return Response(
            {"error": "Failed to search chat history", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_chat_analytics(request, session_id):
    """Get chat session analytics"""
    try:
        session = ChatSession.objects.get(session_id=session_id, user=request.user)

        analytics = session.analytics

        analytics_data = {
            "session_id": str(session.session_id),
            "total_messages": analytics.total_messages,
            "user_messages": analytics.user_messages,
            "nia_messages": analytics.nia_messages,
            "average_response_time": analytics.average_response_time,
            "session_duration": (
                str(analytics.session_duration) if analytics.session_duration else None
            ),
            "user_engagement_score": analytics.user_engagement_score,
            "conversation_quality_score": analytics.conversation_quality_score,
            "topics_discussed": analytics.topics_discussed,
            "sentiment_analysis": analytics.sentiment_analysis,
            "key_phrases": analytics.key_phrases,
            "voice_transition_requested": analytics.voice_transition_requested,
            "voice_transition_successful": analytics.voice_transition_successful,
            "leads_discussed": analytics.leads_discussed,
            "leads_created": analytics.leads_created,
            "opportunities_identified": analytics.opportunities_identified,
        }

        return Response(analytics_data)

    except ChatSession.DoesNotExist:
        return Response(
            {"error": "Chat session not found"}, status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error getting chat analytics: {str(e)}")
        return Response(
            {"error": "Failed to get chat analytics", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
