from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class CallSession(models.Model):
    """Model to track voice call sessions"""
    
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        ENDED = 'ended', 'Ended'
        FAILED = 'failed', 'Failed'
        PAUSED = 'paused', 'Paused'
    
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='call_sessions')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    
    # Call metadata
    caller_id = models.CharField(max_length=50, blank=True)
    call_duration = models.DurationField(null=True, blank=True)
    audio_quality_score = models.FloatField(null=True, blank=True)
    
    # Session context
    conversation_context = models.JSONField(default=dict)
    session_metadata = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['start_time']),
        ]
    
    def __str__(self):
        return f"Call Session {self.session_id} - {self.user.username} ({self.status})"


class AudioChunk(models.Model):
    """Model to store audio chunks for processing"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    session = models.ForeignKey(CallSession, on_delete=models.CASCADE, related_name='audio_chunks')
    chunk_number = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Audio data
    audio_data = models.BinaryField()
    audio_format = models.CharField(max_length=20, default='wav')
    sample_rate = models.IntegerField(default=16000)
    duration_ms = models.IntegerField()
    
    # Processing status
    is_processed = models.BooleanField(default=False)
    transcription = models.TextField(blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    
    class Meta:
        ordering = ['chunk_number']
        unique_together = ['session', 'chunk_number']
        indexes = [
            models.Index(fields=['session', 'chunk_number']),
            models.Index(fields=['is_processed']),
        ]
    
    def __str__(self):
        return f"Audio Chunk {self.chunk_number} - Session {self.session.session_id}"


class ConversationTurn(models.Model):
    """Model to store conversation turns during a call"""
    
    class Speaker(models.TextChoices):
        USER = 'user', 'User'
        NIA = 'nia', 'NIA'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    session = models.ForeignKey(CallSession, on_delete=models.CASCADE, related_name='conversation_turns')
    turn_number = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Speaker and content
    speaker = models.CharField(max_length=10, choices=Speaker.choices)
    content = models.TextField()
    audio_url = models.URLField(blank=True)
    
    # Processing metadata
    extracted_entities = models.JSONField(default=dict)
    intent = models.CharField(max_length=100, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    processing_time_ms = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['turn_number']
        unique_together = ['session', 'turn_number']
        indexes = [
            models.Index(fields=['session', 'turn_number']),
            models.Index(fields=['speaker']),
        ]
    
    def __str__(self):
        return f"Turn {self.turn_number} - {self.speaker} in Session {self.session.session_id}"


class VoiceConfiguration(models.Model):
    """Model to store voice processing configuration per user"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='voice_config')
    
    # Speech-to-Text settings
    language_code = models.CharField(max_length=10, default='en-US')
    enable_automatic_punctuation = models.BooleanField(default=True)
    enable_word_time_offsets = models.BooleanField(default=True)
    speech_contexts = models.JSONField(default=list)  # Custom vocabulary
    
    # Text-to-Speech settings
    voice_name = models.CharField(max_length=50, default='en-US-Wavenet-D')
    speaking_rate = models.FloatField(default=1.0)
    pitch = models.FloatField(default=0.0)
    volume_gain_db = models.FloatField(default=0.0)
    
    # Call handling preferences
    auto_answer = models.BooleanField(default=True)
    max_call_duration_minutes = models.IntegerField(default=30)
    silence_timeout_seconds = models.IntegerField(default=10)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Voice Config for {self.user.username}"
# Import chat models to ensure they're registered with Django
from .chat_models import (
    ChatSession, ChatMessage, ChatBotCommand, 
    ChatAnalytics, ChatSearchHistory, ChatFile
)