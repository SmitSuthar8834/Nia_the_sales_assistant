from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    GoogleMeetCredentials, MicrosoftTeamsCredentials, MeetingSession, MeetingParticipant, 
    MeetingStatusUpdate, MeetingInvitation
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']


class MeetingParticipantSerializer(serializers.ModelSerializer):
    """Serializer for MeetingParticipant model"""
    user = UserSerializer(read_only=True)
    participation_duration_minutes = serializers.ReadOnlyField()
    
    class Meta:
        model = MeetingParticipant
        fields = [
            'id', 'user', 'email', 'name', 'role', 'status',
            'joined_at', 'left_at', 'total_duration_minutes',
            'participation_duration_minutes', 'invitation_sent_at',
            'invitation_response_at', 'created_at', 'updated_at'
        ]


class MeetingStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for MeetingStatusUpdate model"""
    triggered_by = UserSerializer(read_only=True)
    update_type_display = serializers.CharField(source='get_update_type_display', read_only=True)
    
    class Meta:
        model = MeetingStatusUpdate
        fields = [
            'id', 'update_type', 'update_type_display', 'description',
            'metadata', 'triggered_by', 'timestamp'
        ]


class MeetingSessionSerializer(serializers.ModelSerializer):
    """Serializer for MeetingSession model"""
    organizer = UserSerializer(read_only=True)
    participants = MeetingParticipantSerializer(many=True, read_only=True)
    status_updates = MeetingStatusUpdateSerializer(many=True, read_only=True)
    duration_minutes = serializers.ReadOnlyField()
    actual_duration_minutes = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    meeting_type_display = serializers.CharField(source='get_meeting_type_display', read_only=True)
    
    class Meta:
        model = MeetingSession
        fields = [
            'id', 'organizer', 'title', 'description', 'meeting_type',
            'meeting_type_display', 'google_meet_url', 'google_calendar_event_id',
            'google_meet_space_id', 'teams_meeting_url', 'teams_meeting_id',
            'teams_join_url', 'teams_conference_id', 'teams_organizer_id',
            'scheduled_start_time', 'scheduled_end_time',
            'actual_start_time', 'actual_end_time', 'status', 'status_display',
            'max_participants', 'recording_enabled', 'recording_url',
            'duration_minutes', 'actual_duration_minutes', 'is_active',
            'participants', 'status_updates', 'created_at', 'updated_at'
        ]


class CreateMeetingSerializer(serializers.Serializer):
    """Serializer for creating a new meeting"""
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    scheduled_start_time = serializers.DateTimeField()
    scheduled_end_time = serializers.DateTimeField()
    attendee_emails = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        allow_empty=True
    )
    recording_enabled = serializers.BooleanField(default=False)
    max_participants = serializers.IntegerField(default=100, min_value=1, max_value=250)
    
    def validate(self, data):
        """Validate meeting data"""
        start_time = data['scheduled_start_time']
        end_time = data['scheduled_end_time']
        
        if end_time <= start_time:
            raise serializers.ValidationError(
                "End time must be after start time"
            )
        
        # Check if meeting duration is reasonable (max 8 hours)
        duration = end_time - start_time
        if duration.total_seconds() > 8 * 60 * 60:
            raise serializers.ValidationError(
                "Meeting duration cannot exceed 8 hours"
            )
        
        # Check if meeting is not too far in the past
        from django.utils import timezone
        if start_time < timezone.now() - timezone.timedelta(minutes=5):
            raise serializers.ValidationError(
                "Meeting start time cannot be in the past"
            )
        
        return data


class MeetingInvitationSerializer(serializers.ModelSerializer):
    """Serializer for MeetingInvitation model"""
    participant = MeetingParticipantSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = MeetingInvitation
        fields = [
            'id', 'participant', 'subject', 'message', 'status',
            'status_display', 'sent_at', 'delivered_at', 'error_message',
            'retry_count', 'created_at', 'updated_at'
        ]


class GoogleMeetCredentialsSerializer(serializers.ModelSerializer):
    """Serializer for GoogleMeetCredentials model (limited fields for security)"""
    is_token_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = GoogleMeetCredentials
        fields = [
            'scope', 'token_expiry', 'is_token_expired',
            'created_at', 'updated_at'
        ]
        # Exclude sensitive fields like access_token and refresh_token


class MicrosoftTeamsCredentialsSerializer(serializers.ModelSerializer):
    """Serializer for MicrosoftTeamsCredentials model (limited fields for security)"""
    is_token_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = MicrosoftTeamsCredentials
        fields = [
            'scope', 'tenant_id', 'token_expiry', 'is_token_expired',
            'created_at', 'updated_at'
        ]
        # Exclude sensitive fields like access_token and refresh_token

class CreateTeamsMeetingSerializer(serializers.Serializer):
    """Serializer for creating a new Teams meeting"""
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    scheduled_start_time = serializers.DateTimeField()
    scheduled_end_time = serializers.DateTimeField()
    attendee_emails = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        allow_empty=True
    )
    recording_enabled = serializers.BooleanField(default=False)
    max_participants = serializers.IntegerField(default=250, min_value=1, max_value=1000)
    
    def validate(self, data):
        """Validate Teams meeting data"""
        start_time = data['scheduled_start_time']
        end_time = data['scheduled_end_time']
        
        if end_time <= start_time:
            raise serializers.ValidationError(
                "End time must be after start time"
            )
        
        # Check if meeting duration is reasonable (max 24 hours for Teams)
        duration = end_time - start_time
        if duration.total_seconds() > 24 * 60 * 60:
            raise serializers.ValidationError(
                "Meeting duration cannot exceed 24 hours"
            )
        
        # Check if meeting is not too far in the past
        from django.utils import timezone
        if start_time < timezone.now() - timezone.timedelta(minutes=5):
            raise serializers.ValidationError(
                "Meeting start time cannot be in the past"
            )
        
        return data


class TeamsChannelSerializer(serializers.Serializer):
    """Serializer for Teams channel information"""
    id = serializers.CharField()
    displayName = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    webUrl = serializers.URLField(required=False)
    membershipType = serializers.CharField(required=False)


class TeamsTeamSerializer(serializers.Serializer):
    """Serializer for Teams team information"""
    id = serializers.CharField()
    displayName = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    webUrl = serializers.URLField(required=False)
    channels = TeamsChannelSerializer(many=True, required=False)


class SendChannelMessageSerializer(serializers.Serializer):
    """Serializer for sending a message to a Teams channel"""
    team_id = serializers.CharField()
    channel_id = serializers.CharField()
    message = serializers.CharField()
    content_type = serializers.ChoiceField(
        choices=[('text', 'Text'), ('html', 'HTML')],
        default='html'
    )