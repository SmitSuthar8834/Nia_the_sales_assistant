from django.contrib import admin
from .models import CallSession, AudioChunk, ConversationTurn, VoiceConfiguration


@admin.register(CallSession)
class CallSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user', 'status', 'start_time', 'end_time', 'call_duration']
    list_filter = ['status', 'start_time', 'user']
    search_fields = ['session_id', 'user__username', 'caller_id']
    readonly_fields = ['session_id', 'start_time', 'call_duration']
    ordering = ['-start_time']
    
    fieldsets = (
        ('Session Info', {
            'fields': ('session_id', 'user', 'status', 'caller_id')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time', 'call_duration')
        }),
        ('Metadata', {
            'fields': ('conversation_context', 'session_metadata', 'audio_quality_score'),
            'classes': ('collapse',)
        })
    )


@admin.register(AudioChunk)
class AudioChunkAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'chunk_number', 'timestamp', 'is_processed', 'confidence_score']
    list_filter = ['is_processed', 'audio_format', 'timestamp']
    search_fields = ['session__session_id', 'transcription']
    readonly_fields = ['id', 'timestamp', 'audio_data']
    ordering = ['session', 'chunk_number']
    
    fieldsets = (
        ('Chunk Info', {
            'fields': ('id', 'session', 'chunk_number', 'timestamp')
        }),
        ('Audio Data', {
            'fields': ('audio_format', 'sample_rate', 'duration_ms'),
        }),
        ('Processing', {
            'fields': ('is_processed', 'transcription', 'confidence_score')
        })
    )


@admin.register(ConversationTurn)
class ConversationTurnAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'turn_number', 'speaker', 'timestamp', 'confidence_score']
    list_filter = ['speaker', 'timestamp']
    search_fields = ['session__session_id', 'content', 'intent']
    readonly_fields = ['id', 'timestamp', 'processing_time_ms']
    ordering = ['session', 'turn_number']
    
    fieldsets = (
        ('Turn Info', {
            'fields': ('id', 'session', 'turn_number', 'timestamp', 'speaker')
        }),
        ('Content', {
            'fields': ('content', 'audio_url')
        }),
        ('Processing', {
            'fields': ('extracted_entities', 'intent', 'confidence_score', 'processing_time_ms'),
            'classes': ('collapse',)
        })
    )


@admin.register(VoiceConfiguration)
class VoiceConfigurationAdmin(admin.ModelAdmin):
    list_display = ['user', 'language_code', 'voice_name', 'auto_answer', 'updated_at']
    list_filter = ['language_code', 'auto_answer', 'updated_at']
    search_fields = ['user__username', 'voice_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Speech-to-Text Settings', {
            'fields': ('language_code', 'enable_automatic_punctuation', 
                      'enable_word_time_offsets', 'speech_contexts')
        }),
        ('Text-to-Speech Settings', {
            'fields': ('voice_name', 'speaking_rate', 'pitch', 'volume_gain_db')
        }),
        ('Call Handling', {
            'fields': ('auto_answer', 'max_call_duration_minutes', 'silence_timeout_seconds')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
