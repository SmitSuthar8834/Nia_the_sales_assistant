"""
Chat models for smart chat interface with voice fallback
"""

import uuid

from django.contrib.auth import get_user_model
from django.db import models

from .models import CallSession

User = get_user_model()


class ChatSession(models.Model):
    """Model to track chat sessions with voice fallback capability"""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        VOICE_TRANSITION = "voice_transition", "Transitioning to Voice"
        VOICE_ACTIVE = "voice_active", "Voice Call Active"
        ENDED = "ended", "Ended"
        PAUSED = "paused", "Paused"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chat_sessions"
    )
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )

    # Voice transition tracking
    voice_session = models.OneToOneField(
        CallSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chat_session",
    )
    voice_transition_requested = models.BooleanField(default=False)
    voice_transition_time = models.DateTimeField(null=True, blank=True)

    # Chat metadata
    participant_count = models.PositiveIntegerField(default=1)
    is_group_chat = models.BooleanField(default=False)
    chat_context = models.JSONField(default=dict)

    # User availability tracking
    user_available_for_voice = models.BooleanField(default=False)
    last_activity = models.DateTimeField(auto_now=True)
    typing_indicator_active = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_time"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["start_time"]),
            models.Index(fields=["last_activity"]),
        ]

    def __str__(self):
        return f"Chat Session {self.session_id} - {self.user.username} ({self.status})"


class ChatMessage(models.Model):
    """Model to store chat messages with rich content support"""

    class MessageType(models.TextChoices):
        TEXT = "text", "Text Message"
        FILE = "file", "File Attachment"
        IMAGE = "image", "Image"
        VOICE_NOTE = "voice_note", "Voice Note"
        SYSTEM = "system", "System Message"
        BOT_COMMAND = "bot_command", "Bot Command"
        SCREEN_SHARE = "screen_share", "Screen Share"
        LEAD_INFO = "lead_info", "Lead Information"

    class Sender(models.TextChoices):
        USER = "user", "User"
        NIA = "nia", "NIA"
        SYSTEM = "system", "System"

    class Status(models.TextChoices):
        SENT = "sent", "Sent"
        DELIVERED = "delivered", "Delivered"
        READ = "read", "Read"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="messages"
    )
    message_number = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    # Message content
    sender = models.CharField(max_length=10, choices=Sender.choices)
    message_type = models.CharField(
        max_length=20, choices=MessageType.choices, default=MessageType.TEXT
    )
    content = models.TextField()

    # Rich content support
    attachments = models.JSONField(default=list)  # File URLs, image URLs, etc.
    metadata = models.JSONField(default=dict)  # Additional message metadata

    # Message status tracking
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.SENT
    )
    read_at = models.DateTimeField(null=True, blank=True)

    # AI processing
    extracted_entities = models.JSONField(default=dict)
    intent = models.CharField(max_length=100, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)

    # Threading support
    reply_to = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True
    )
    thread_id = models.UUIDField(null=True, blank=True)

    class Meta:
        ordering = ["message_number"]
        unique_together = ["session", "message_number"]
        indexes = [
            models.Index(fields=["session", "message_number"]),
            models.Index(fields=["sender"]),
            models.Index(fields=["timestamp"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Message {self.message_number} - {self.sender} in Session {self.session.session_id}"


class ChatBotCommand(models.Model):
    """Model to store available chat bot commands"""

    class CommandType(models.TextChoices):
        SCHEDULE_CALL = "schedule_call", "Schedule Call"
        GET_LEAD_INFO = "get_lead_info", "Get Lead Info"
        CREATE_LEAD = "create_lead", "Create Lead"
        UPDATE_LEAD = "update_lead", "Update Lead"
        SEARCH_LEADS = "search_leads", "Search Leads"
        GET_ANALYTICS = "get_analytics", "Get Analytics"
        VOICE_TRANSITION = "voice_transition", "Transition to Voice"
        HELP = "help", "Help"

    command = models.CharField(max_length=50, unique=True)
    command_type = models.CharField(max_length=20, choices=CommandType.choices)
    description = models.TextField()
    usage_example = models.TextField()
    parameters = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["command"]

    def __str__(self):
        return f"/{self.command} - {self.description}"


class ChatFile(models.Model):
    """Model to store chat file attachments"""

    class FileType(models.TextChoices):
        DOCUMENT = "document", "Document"
        IMAGE = "image", "Image"
        AUDIO = "audio", "Audio"
        VIDEO = "video", "Video"
        ARCHIVE = "archive", "Archive"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    message = models.ForeignKey(
        ChatMessage, on_delete=models.CASCADE, related_name="files"
    )

    # File information
    original_filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField()  # Size in bytes
    file_type = models.CharField(max_length=20, choices=FileType.choices)
    mime_type = models.CharField(max_length=100)

    # File processing
    is_processed = models.BooleanField(default=False)
    processing_status = models.CharField(max_length=50, blank=True)
    extracted_text = models.TextField(blank=True)  # For document files

    # Security
    is_safe = models.BooleanField(default=True)
    scan_results = models.JSONField(default=dict)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["message"]),
            models.Index(fields=["file_type"]),
            models.Index(fields=["is_processed"]),
        ]

    def __str__(self):
        return f"File: {self.original_filename} ({self.file_type})"


class ChatAnalytics(models.Model):
    """Model to store chat analytics and conversation insights"""

    session = models.OneToOneField(
        ChatSession, on_delete=models.CASCADE, related_name="analytics"
    )

    # Message statistics
    total_messages = models.PositiveIntegerField(default=0)
    user_messages = models.PositiveIntegerField(default=0)
    nia_messages = models.PositiveIntegerField(default=0)

    # Timing statistics
    average_response_time = models.FloatField(null=True, blank=True)  # In seconds
    session_duration = models.DurationField(null=True, blank=True)

    # Engagement metrics
    user_engagement_score = models.FloatField(default=0.0)  # 0-100
    conversation_quality_score = models.FloatField(default=0.0)  # 0-100

    # Content analysis
    topics_discussed = models.JSONField(default=list)
    sentiment_analysis = models.JSONField(default=dict)
    key_phrases = models.JSONField(default=list)

    # Voice transition metrics
    voice_transition_requested = models.BooleanField(default=False)
    voice_transition_successful = models.BooleanField(default=False)
    voice_transition_reason = models.CharField(max_length=100, blank=True)

    # Lead generation metrics
    leads_discussed = models.PositiveIntegerField(default=0)
    leads_created = models.PositiveIntegerField(default=0)
    opportunities_identified = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analytics for Chat Session {self.session.session_id}"


class ChatSearchHistory(models.Model):
    """Model to store searchable chat history for analytics"""

    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="search_history"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chat_searches"
    )

    # Search content
    searchable_content = models.TextField()  # Concatenated message content
    conversation_summary = models.TextField(blank=True)

    # Search metadata
    lead_information = models.JSONField(default=dict)
    action_items = models.JSONField(default=list)
    decisions_made = models.JSONField(default=list)

    # Indexing
    search_vector = models.TextField(blank=True)  # For full-text search
    tags = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["session"]),
        ]

    def __str__(self):
        return f"Search History for Session {self.session.session_id}"
