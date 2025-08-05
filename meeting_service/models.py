from django.db import models
from django.contrib.auth import get_user_model
import uuid
from django.utils import timezone

User = get_user_model()


class GoogleMeetCredentials(models.Model):
    """Store Google OAuth credentials for users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='google_meet_credentials')
    access_token = models.TextField()
    refresh_token = models.TextField()
    token_expiry = models.DateTimeField()
    scope = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Google Meet Credentials"
        verbose_name_plural = "Google Meet Credentials"
    
    def __str__(self):
        return f"Google Meet credentials for {self.user.email}"
    
    def is_token_expired(self):
        """Check if the access token is expired"""
        return timezone.now() >= self.token_expiry


class MicrosoftTeamsCredentials(models.Model):
    """Store Microsoft Teams OAuth credentials for users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teams_credentials')
    access_token = models.TextField()
    refresh_token = models.TextField()
    token_expiry = models.DateTimeField()
    scope = models.TextField()
    tenant_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Microsoft Teams Credentials"
        verbose_name_plural = "Microsoft Teams Credentials"
    
    def __str__(self):
        return f"Microsoft Teams credentials for {self.user.email}"
    
    def is_token_expired(self):
        """Check if the access token is expired"""
        return timezone.now() >= self.token_expiry


class MeetingSession(models.Model):
    """Model for Google Meet sessions"""
    
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        ACTIVE = 'active', 'Active'
        ENDED = 'ended', 'Ended'
        CANCELLED = 'cancelled', 'Cancelled'
    
    class MeetingType(models.TextChoices):
        GOOGLE_MEET = 'google_meet', 'Google Meet'
        MICROSOFT_TEAMS = 'microsoft_teams', 'Microsoft Teams'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_meetings')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    meeting_type = models.CharField(max_length=20, choices=MeetingType.choices, default=MeetingType.GOOGLE_MEET)
    
    # Google Meet specific fields
    google_meet_url = models.URLField(blank=True)
    google_calendar_event_id = models.CharField(max_length=255, blank=True)
    google_meet_space_id = models.CharField(max_length=255, blank=True)
    
    # Microsoft Teams specific fields
    teams_meeting_url = models.URLField(blank=True)
    teams_meeting_id = models.CharField(max_length=255, blank=True)
    teams_join_url = models.URLField(blank=True)
    teams_conference_id = models.CharField(max_length=255, blank=True)
    teams_organizer_id = models.CharField(max_length=255, blank=True)
    
    # Meeting timing
    scheduled_start_time = models.DateTimeField()
    scheduled_end_time = models.DateTimeField()
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    
    # Meeting status and metadata
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    max_participants = models.PositiveIntegerField(default=100)
    recording_enabled = models.BooleanField(default=False)
    recording_url = models.URLField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_start_time']
        verbose_name = "Meeting Session"
        verbose_name_plural = "Meeting Sessions"
    
    def __str__(self):
        return f"{self.title} - {self.scheduled_start_time.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def duration_minutes(self):
        """Calculate scheduled duration in minutes"""
        if self.scheduled_end_time and self.scheduled_start_time:
            delta = self.scheduled_end_time - self.scheduled_start_time
            return int(delta.total_seconds() / 60)
        return 0
    
    @property
    def actual_duration_minutes(self):
        """Calculate actual duration in minutes"""
        if self.actual_end_time and self.actual_start_time:
            delta = self.actual_end_time - self.actual_start_time
            return int(delta.total_seconds() / 60)
        return 0
    
    def is_active(self):
        """Check if meeting is currently active"""
        now = timezone.now()
        return (self.status == self.Status.ACTIVE or 
                (self.scheduled_start_time <= now <= self.scheduled_end_time and 
                 self.status == self.Status.SCHEDULED))


class MeetingParticipant(models.Model):
    """Model for meeting participants"""
    
    class ParticipantStatus(models.TextChoices):
        INVITED = 'invited', 'Invited'
        ACCEPTED = 'accepted', 'Accepted'
        DECLINED = 'declined', 'Declined'
        TENTATIVE = 'tentative', 'Tentative'
        JOINED = 'joined', 'Joined'
        LEFT = 'left', 'Left'
    
    class ParticipantRole(models.TextChoices):
        ORGANIZER = 'organizer', 'Organizer'
        PRESENTER = 'presenter', 'Presenter'
        ATTENDEE = 'attendee', 'Attendee'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(MeetingSession, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Participant details
    email = models.EmailField()
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ParticipantRole.choices, default=ParticipantRole.ATTENDEE)
    status = models.CharField(max_length=20, choices=ParticipantStatus.choices, default=ParticipantStatus.INVITED)
    
    # Participation tracking
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)
    total_duration_minutes = models.PositiveIntegerField(default=0)
    
    # Invitation details
    invitation_sent_at = models.DateTimeField(null=True, blank=True)
    invitation_response_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['meeting', 'email']
        verbose_name = "Meeting Participant"
        verbose_name_plural = "Meeting Participants"
    
    def __str__(self):
        return f"{self.name} ({self.email}) - {self.meeting.title}"
    
    @property
    def participation_duration_minutes(self):
        """Calculate actual participation duration"""
        if self.joined_at and self.left_at:
            delta = self.left_at - self.joined_at
            return int(delta.total_seconds() / 60)
        elif self.joined_at and not self.left_at:
            # Still in meeting
            delta = timezone.now() - self.joined_at
            return int(delta.total_seconds() / 60)
        return 0


class MeetingStatusUpdate(models.Model):
    """Model for tracking meeting status changes and events"""
    
    class UpdateType(models.TextChoices):
        CREATED = 'created', 'Meeting Created'
        STARTED = 'started', 'Meeting Started'
        ENDED = 'ended', 'Meeting Ended'
        CANCELLED = 'cancelled', 'Meeting Cancelled'
        PARTICIPANT_JOINED = 'participant_joined', 'Participant Joined'
        PARTICIPANT_LEFT = 'participant_left', 'Participant Left'
        RECORDING_STARTED = 'recording_started', 'Recording Started'
        RECORDING_STOPPED = 'recording_stopped', 'Recording Stopped'
        RESCHEDULED = 'rescheduled', 'Meeting Rescheduled'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(MeetingSession, on_delete=models.CASCADE, related_name='status_updates')
    update_type = models.CharField(max_length=30, choices=UpdateType.choices)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # User who triggered the update (if applicable)
    triggered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Meeting Status Update"
        verbose_name_plural = "Meeting Status Updates"
    
    def __str__(self):
        return f"{self.meeting.title} - {self.get_update_type_display()} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class MeetingInvitation(models.Model):
    """Model for managing meeting invitations"""
    
    class InvitationStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'
        DELIVERED = 'delivered', 'Delivered'
        FAILED = 'failed', 'Failed'
        RESENT = 'resent', 'Resent'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(MeetingSession, on_delete=models.CASCADE, related_name='invitations')
    participant = models.ForeignKey(MeetingParticipant, on_delete=models.CASCADE, related_name='invitations')
    
    # Invitation details
    subject = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=InvitationStatus.choices, default=InvitationStatus.PENDING)
    
    # Delivery tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Meeting Invitation"
        verbose_name_plural = "Meeting Invitations"
    
    def __str__(self):
        return f"Invitation to {self.participant.email} for {self.meeting.title}"