import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class GoogleMeetCredentials(models.Model):
    """Store Google OAuth credentials for users"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="google_meet_credentials"
    )
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

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="teams_credentials"
    )
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
        SCHEDULED = "scheduled", "Scheduled"
        ACTIVE = "active", "Active"
        ENDED = "ended", "Ended"
        CANCELLED = "cancelled", "Cancelled"

    class MeetingType(models.TextChoices):
        GOOGLE_MEET = "google_meet", "Google Meet"
        MICROSOFT_TEAMS = "microsoft_teams", "Microsoft Teams"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organizer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="organized_meetings"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    meeting_type = models.CharField(
        max_length=20, choices=MeetingType.choices, default=MeetingType.GOOGLE_MEET
    )

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
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SCHEDULED
    )
    max_participants = models.PositiveIntegerField(default=100)
    recording_enabled = models.BooleanField(default=False)
    recording_url = models.URLField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-scheduled_start_time"]
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
        return self.status == self.Status.ACTIVE or (
            self.scheduled_start_time <= now <= self.scheduled_end_time
            and self.status == self.Status.SCHEDULED
        )


class MeetingParticipant(models.Model):
    """Model for meeting participants"""

    class ParticipantStatus(models.TextChoices):
        INVITED = "invited", "Invited"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        TENTATIVE = "tentative", "Tentative"
        JOINED = "joined", "Joined"
        LEFT = "left", "Left"

    class ParticipantRole(models.TextChoices):
        ORGANIZER = "organizer", "Organizer"
        PRESENTER = "presenter", "Presenter"
        ATTENDEE = "attendee", "Attendee"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(
        MeetingSession, on_delete=models.CASCADE, related_name="participants"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    # Participant details
    email = models.EmailField()
    name = models.CharField(max_length=255)
    role = models.CharField(
        max_length=20, choices=ParticipantRole.choices, default=ParticipantRole.ATTENDEE
    )
    status = models.CharField(
        max_length=20,
        choices=ParticipantStatus.choices,
        default=ParticipantStatus.INVITED,
    )

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
        unique_together = ["meeting", "email"]
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
        CREATED = "created", "Meeting Created"
        STARTED = "started", "Meeting Started"
        ENDED = "ended", "Meeting Ended"
        CANCELLED = "cancelled", "Meeting Cancelled"
        PARTICIPANT_JOINED = "participant_joined", "Participant Joined"
        PARTICIPANT_LEFT = "participant_left", "Participant Left"
        RECORDING_STARTED = "recording_started", "Recording Started"
        RECORDING_STOPPED = "recording_stopped", "Recording Stopped"
        RESCHEDULED = "rescheduled", "Meeting Rescheduled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(
        MeetingSession, on_delete=models.CASCADE, related_name="status_updates"
    )
    update_type = models.CharField(max_length=30, choices=UpdateType.choices)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    # User who triggered the update (if applicable)
    triggered_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Meeting Status Update"
        verbose_name_plural = "Meeting Status Updates"

    def __str__(self):
        return f"{self.meeting.title} - {self.get_update_type_display()} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class MeetingInvitation(models.Model):
    """Model for managing meeting invitations"""

    class InvitationStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        DELIVERED = "delivered", "Delivered"
        FAILED = "failed", "Failed"
        RESENT = "resent", "Resent"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(
        MeetingSession, on_delete=models.CASCADE, related_name="invitations"
    )
    participant = models.ForeignKey(
        MeetingParticipant, on_delete=models.CASCADE, related_name="invitations"
    )

    # Invitation details
    subject = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING,
    )

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


class Meeting(models.Model):
    """Meeting model with lead relationship for NIA sales assistant"""

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class MeetingType(models.TextChoices):
        DISCOVERY = "discovery", "Discovery Call"
        DEMO = "demo", "Product Demo"
        PROPOSAL = "proposal", "Proposal Presentation"
        NEGOTIATION = "negotiation", "Negotiation"
        CLOSING = "closing", "Closing Call"
        FOLLOW_UP = "follow_up", "Follow-up"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Lead relationship - import Lead model from ai_service
    lead = models.ForeignKey(
        "ai_service.Lead", on_delete=models.CASCADE, related_name="meetings"
    )

    # Meeting basic information
    title = models.CharField(max_length=255, help_text="Meeting title or subject")
    description = models.TextField(blank=True, help_text="Meeting description or notes")
    meeting_type = models.CharField(
        max_length=20, choices=MeetingType.choices, default=MeetingType.DISCOVERY
    )

    # Meeting scheduling
    scheduled_at = models.DateTimeField(help_text="Scheduled meeting date and time")
    duration_minutes = models.PositiveIntegerField(
        default=60, help_text="Expected meeting duration in minutes"
    )

    # Meeting status and tracking
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SCHEDULED
    )

    # Meeting content and outcomes
    agenda = models.TextField(blank=True, help_text="Meeting agenda and talking points")
    outcome = models.TextField(
        blank=True, help_text="Meeting outcome and key takeaways"
    )
    action_items = models.JSONField(
        default=list, help_text="Action items and follow-up tasks"
    )

    # AI insights and analysis
    ai_insights = models.JSONField(
        default=dict, help_text="AI-generated insights and recommendations"
    )

    # Meeting platform integration
    meeting_url = models.URLField(
        blank=True, help_text="Meeting URL (Google Meet, Teams, etc.)"
    )
    meeting_platform = models.CharField(
        max_length=50, blank=True, help_text="Meeting platform used"
    )
    recording_url = models.URLField(blank=True, help_text="Recording URL if available")

    # Participants information
    participants = models.JSONField(
        default=list, help_text="List of meeting participants"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(
        null=True, blank=True, help_text="Actual meeting start time"
    )
    ended_at = models.DateTimeField(
        null=True, blank=True, help_text="Actual meeting end time"
    )

    class Meta:
        ordering = ["-scheduled_at"]
        verbose_name = "Meeting"
        verbose_name_plural = "Meetings"
        indexes = [
            models.Index(fields=["lead", "status"]),
            models.Index(fields=["scheduled_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.lead.company_name} ({self.get_status_display()})"

    @property
    def is_upcoming(self):
        """Check if meeting is scheduled for the future"""
        return (
            self.status == self.Status.SCHEDULED and self.scheduled_at > timezone.now()
        )

    @property
    def is_overdue(self):
        """Check if scheduled meeting is overdue"""
        return (
            self.status == self.Status.SCHEDULED and self.scheduled_at < timezone.now()
        )

    @property
    def actual_duration_minutes(self):
        """Calculate actual meeting duration in minutes"""
        if self.started_at and self.ended_at:
            delta = self.ended_at - self.started_at
            return int(delta.total_seconds() / 60)
        return None

    @property
    def lead_company_name(self):
        """Get the company name from the related lead"""
        return self.lead.company_name if self.lead else ""

    @property
    def lead_contact_name(self):
        """Get the primary contact name from the related lead"""
        return self.lead.contact_name if self.lead else ""

    def mark_as_started(self):
        """Mark meeting as started and set start time"""
        self.status = self.Status.IN_PROGRESS
        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at", "updated_at"])

    def mark_as_completed(self):
        """Mark meeting as completed and set end time"""
        self.status = self.Status.COMPLETED
        self.ended_at = timezone.now()
        self.save(update_fields=["status", "ended_at", "updated_at"])

    def mark_as_cancelled(self):
        """Mark meeting as cancelled"""
        self.status = self.Status.CANCELLED
        self.save(update_fields=["status", "updated_at"])


class MeetingQuestion(models.Model):
    """AI-generated questions for meetings to improve lead qualification and conversion"""

    class QuestionType(models.TextChoices):
        DISCOVERY = "discovery", "Discovery"
        BUDGET = "budget", "Budget Qualification"
        TIMELINE = "timeline", "Timeline & Urgency"
        DECISION_MAKERS = "decision_makers", "Decision Makers"
        PAIN_POINTS = "pain_points", "Pain Point Discovery"
        REQUIREMENTS = "requirements", "Requirements Qualification"
        COMPETITION = "competition", "Competitive Analysis"
        CURRENT_SOLUTION = "current_solution", "Current Solution Assessment"
        OBJECTION_HANDLING = "objection_handling", "Objection Handling"
        CLOSING = "closing", "Closing Questions"

    class Priority(models.TextChoices):
        HIGH = "high", "High Priority"
        MEDIUM = "medium", "Medium Priority"
        LOW = "low", "Low Priority"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Meeting relationship
    meeting = models.ForeignKey(
        Meeting, on_delete=models.CASCADE, related_name="questions"
    )

    # Question details
    question_text = models.TextField(help_text="The actual question to ask")
    question_type = models.CharField(
        max_length=20, choices=QuestionType.choices, help_text="Category of question"
    )
    priority = models.IntegerField(
        default=5, help_text="Priority ranking (1-10, higher is more important)"
    )
    priority_level = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )

    # AI generation context
    ai_generated = models.BooleanField(
        default=True, help_text="Whether this question was AI-generated"
    )
    generation_context = models.JSONField(
        default=dict, help_text="Context used for AI generation"
    )
    confidence_score = models.FloatField(
        default=0.0, help_text="AI confidence in question relevance (0-100)"
    )

    # Question targeting
    target_persona = models.CharField(
        max_length=100, blank=True, help_text="Target persona or role for this question"
    )
    industry_specific = models.BooleanField(
        default=False, help_text="Whether question is industry-specific"
    )

    # Usage tracking
    asked_at = models.DateTimeField(
        null=True, blank=True, help_text="When this question was asked"
    )
    response = models.TextField(
        blank=True, help_text="Response received to this question"
    )
    response_quality = models.CharField(
        max_length=20, blank=True, help_text="Quality of response received"
    )

    # Follow-up questions
    follow_up_questions = models.JSONField(
        default=list, help_text="Suggested follow-up questions based on response"
    )
    triggers_follow_up = models.BooleanField(
        default=False, help_text="Whether this question should trigger follow-ups"
    )

    # Question effectiveness
    effectiveness_score = models.FloatField(
        null=True, blank=True, help_text="Effectiveness score based on outcomes"
    )
    led_to_qualification = models.BooleanField(
        default=False, help_text="Whether question helped qualify the lead"
    )
    led_to_objection = models.BooleanField(
        default=False, help_text="Whether question surfaced objections"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who created/approved this question",
    )

    # Question ordering and flow
    sequence_order = models.PositiveIntegerField(
        default=0, help_text="Order in which question should be asked"
    )
    depends_on_question = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Question that should be asked before this one",
    )

    class Meta:
        ordering = ["sequence_order", "-priority", "question_type"]
        verbose_name = "Meeting Question"
        verbose_name_plural = "Meeting Questions"
        indexes = [
            models.Index(fields=["meeting", "question_type"]),
            models.Index(fields=["priority", "sequence_order"]),
            models.Index(fields=["ai_generated", "confidence_score"]),
        ]

    def __str__(self):
        return f"{self.get_question_type_display()}: {self.question_text[:50]}..."

    @property
    def is_high_priority(self):
        """Check if this is a high priority question"""
        return self.priority >= 8 or self.priority_level == self.Priority.HIGH

    @property
    def is_conversion_focused(self):
        """Check if this question is focused on conversion"""
        conversion_types = [
            self.QuestionType.BUDGET,
            self.QuestionType.TIMELINE,
            self.QuestionType.DECISION_MAKERS,
            self.QuestionType.CLOSING,
        ]
        return self.question_type in conversion_types

    @property
    def is_discovery_focused(self):
        """Check if this question is focused on discovery"""
        discovery_types = [
            self.QuestionType.DISCOVERY,
            self.QuestionType.PAIN_POINTS,
            self.QuestionType.REQUIREMENTS,
            self.QuestionType.CURRENT_SOLUTION,
        ]
        return self.question_type in discovery_types

    def mark_as_asked(self, response_text: str = ""):
        """Mark question as asked and optionally record response"""
        self.asked_at = timezone.now()
        if response_text:
            self.response = response_text
        self.save(update_fields=["asked_at", "response", "updated_at"])

    def calculate_effectiveness(self, outcome_data: dict = None):
        """Calculate and update effectiveness score based on outcomes"""
        # This would be implemented with actual effectiveness calculation logic
        # For now, we'll set a placeholder
        if outcome_data:
            # Example effectiveness calculation based on outcomes
            score = 0.0
            if outcome_data.get("led_to_qualification"):
                score += 30
                self.led_to_qualification = True
            if outcome_data.get("generated_follow_up"):
                score += 20
            if outcome_data.get("positive_response"):
                score += 25
            if outcome_data.get("moved_deal_forward"):
                score += 25

            self.effectiveness_score = min(score, 100.0)
            self.save(
                update_fields=[
                    "effectiveness_score",
                    "led_to_qualification",
                    "updated_at",
                ]
            )


class QuestionTemplate(models.Model):
    """Industry-specific question templates for different meeting types"""

    class TemplateType(models.TextChoices):
        DISCOVERY = "discovery", "Discovery Meeting"
        DEMO = "demo", "Demo Meeting"
        PROPOSAL = "proposal", "Proposal Meeting"
        CLOSING = "closing", "Closing Meeting"
        FOLLOW_UP = "follow_up", "Follow-up Meeting"

    class QuestionCategory(models.TextChoices):
        PAIN_POINTS = "pain_points", "Pain Point Questions"
        CURRENT_STATE = "current_state", "Current State Questions"
        STAKEHOLDERS = "stakeholders", "Stakeholder Questions"
        REQUIREMENTS = "requirements", "Requirements Questions"
        INTEGRATION = "integration", "Integration Questions"
        BUDGET = "budget", "Budget Questions"
        TIMELINE = "timeline", "Timeline Questions"
        DECISION_PROCESS = "decision_process", "Decision Process Questions"
        OBJECTION_HANDLING = "objection_handling", "Objection Handling Questions"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Template identification
    name = models.CharField(max_length=255, help_text="Template name")
    industry = models.CharField(max_length=100, help_text="Target industry")
    template_type = models.CharField(
        max_length=20, choices=TemplateType.choices, help_text="Meeting type"
    )
    question_category = models.CharField(
        max_length=20, choices=QuestionCategory.choices, help_text="Question category"
    )

    # Template content
    question_template = models.TextField(help_text="Question template with variables")
    variables = models.JSONField(default=list, help_text="List of template variables")
    rationale = models.TextField(
        help_text="Why this question is important for this industry"
    )
    expected_responses = models.JSONField(
        default=list, help_text="Typical response patterns"
    )
    follow_up_triggers = models.JSONField(
        default=list, help_text="Conditions that trigger follow-ups"
    )

    # Template metadata
    priority = models.IntegerField(default=5, help_text="Template priority (1-10)")
    confidence_score = models.FloatField(
        default=80.0, help_text="Confidence in template effectiveness"
    )
    usage_count = models.PositiveIntegerField(
        default=0, help_text="Number of times template has been used"
    )
    success_rate = models.FloatField(
        default=0.0, help_text="Success rate of questions generated from this template"
    )

    # Template targeting
    company_size_filter = models.JSONField(
        default=list, blank=True, help_text="Company sizes this template works best for"
    )
    meeting_stage_filter = models.JSONField(
        default=list,
        blank=True,
        help_text="Meeting stages where this template is most effective",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Template status
    is_active = models.BooleanField(
        default=True, help_text="Whether this template is active"
    )
    is_ai_generated = models.BooleanField(
        default=True, help_text="Whether this template was AI-generated"
    )

    class Meta:
        ordering = ["-priority", "industry", "template_type"]
        verbose_name = "Question Template"
        verbose_name_plural = "Question Templates"
        indexes = [
            models.Index(fields=["industry", "template_type"]),
            models.Index(fields=["question_category", "priority"]),
            models.Index(fields=["is_active", "success_rate"]),
        ]
        unique_together = [
            "industry",
            "template_type",
            "question_category",
            "question_template",
        ]

    def __str__(self):
        return f"{self.industry} - {self.get_template_type_display()} - {self.get_question_category_display()}"

    def increment_usage(self):
        """Increment usage count when template is used"""
        self.usage_count += 1
        self.save(update_fields=["usage_count", "updated_at"])

    def update_success_rate(self, effectiveness_score: float):
        """Update success rate based on question effectiveness"""
        if self.usage_count > 0:
            # Calculate weighted average of success rate
            current_total = self.success_rate * (self.usage_count - 1)
            new_total = current_total + effectiveness_score
            self.success_rate = new_total / self.usage_count
            self.save(update_fields=["success_rate", "updated_at"])


class QuestionEffectivenessLog(models.Model):
    """Log of question effectiveness for learning and improvement"""

    class EffectivenessTier(models.TextChoices):
        HIGH = "high", "High Effectiveness"
        MEDIUM = "medium", "Medium Effectiveness"
        LOW = "low", "Low Effectiveness"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Question reference
    question = models.ForeignKey(
        MeetingQuestion, on_delete=models.CASCADE, related_name="effectiveness_logs"
    )
    meeting = models.ForeignKey(
        Meeting, on_delete=models.CASCADE, related_name="question_effectiveness_logs"
    )

    # Effectiveness metrics
    effectiveness_score = models.FloatField(
        help_text="Overall effectiveness score (0-100)"
    )
    effectiveness_tier = models.CharField(
        max_length=10, choices=EffectivenessTier.choices
    )

    # Detailed breakdown
    response_quality_score = models.FloatField(
        default=0.0, help_text="Quality of response received"
    )
    information_value_score = models.FloatField(
        default=0.0, help_text="Value of information gathered"
    )
    engagement_score = models.FloatField(
        default=0.0, help_text="Level of engagement generated"
    )
    objective_advancement_score = models.FloatField(
        default=0.0, help_text="Progress toward meeting objectives"
    )
    pain_point_discovery_score = models.FloatField(
        default=0.0, help_text="Pain point discovery effectiveness"
    )
    process_advancement_score = models.FloatField(
        default=0.0, help_text="Sales process advancement"
    )

    # Response analysis
    response_text = models.TextField(help_text="The actual response received")
    response_word_count = models.PositiveIntegerField(
        default=0, help_text="Word count of response"
    )
    response_depth = models.CharField(
        max_length=20, default="moderate", help_text="Depth of response"
    )
    buying_signals_identified = models.JSONField(
        default=list, help_text="Buying signals identified in response"
    )
    concerns_raised = models.JSONField(
        default=list, help_text="Concerns or objections raised"
    )

    # Context factors
    question_timing = models.CharField(
        max_length=50, help_text="When in the meeting the question was asked"
    )
    conversation_context = models.JSONField(
        default=dict, help_text="Context when question was asked"
    )
    lead_engagement_level = models.CharField(
        max_length=20, default="medium", help_text="Lead engagement level"
    )

    # Learning insights
    what_worked_well = models.JSONField(
        default=list, help_text="What aspects worked well"
    )
    improvement_opportunities = models.JSONField(
        default=list, help_text="Areas for improvement"
    )
    context_factors = models.JSONField(
        default=list, help_text="Contextual factors that influenced effectiveness"
    )
    replication_potential = models.JSONField(
        default=list, help_text="How to replicate success"
    )

    # Recommendations
    question_modifications = models.JSONField(
        default=list, help_text="Suggested question improvements"
    )
    timing_adjustments = models.JSONField(
        default=list, help_text="Better timing recommendations"
    )
    follow_up_suggestions = models.JSONField(
        default=list, help_text="Recommended follow-up approaches"
    )

    # Outcome tracking
    led_to_qualification = models.BooleanField(
        default=False, help_text="Whether question helped qualify lead"
    )
    led_to_objection = models.BooleanField(
        default=False, help_text="Whether question surfaced objections"
    )
    generated_follow_ups = models.BooleanField(
        default=False, help_text="Whether question generated follow-ups"
    )
    moved_deal_forward = models.BooleanField(
        default=False, help_text="Whether question moved deal forward"
    )

    # Timestamps
    logged_at = models.DateTimeField(auto_now_add=True)
    analyzed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-logged_at"]
        verbose_name = "Question Effectiveness Log"
        verbose_name_plural = "Question Effectiveness Logs"
        indexes = [
            models.Index(fields=["question", "effectiveness_score"]),
            models.Index(fields=["meeting", "effectiveness_tier"]),
            models.Index(fields=["logged_at", "effectiveness_score"]),
        ]

    def __str__(self):
        return f"Effectiveness Log - {self.question.question_text[:50]}... - Score: {self.effectiveness_score}"

    @property
    def is_high_performing(self):
        """Check if this is a high-performing question"""
        return (
            self.effectiveness_score >= 80
            and self.effectiveness_tier == self.EffectivenessTier.HIGH
        )

    @property
    def generated_insights(self):
        """Check if this log generated valuable insights"""
        return (
            len(self.buying_signals_identified) > 0
            or self.led_to_qualification
            or self.moved_deal_forward
        )


class ConversationFlow(models.Model):
    """Track conversation flow and question sequences for optimization"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Meeting reference
    meeting = models.OneToOneField(
        Meeting, on_delete=models.CASCADE, related_name="conversation_flow"
    )

    # Flow tracking
    questions_asked_sequence = models.JSONField(
        default=list, help_text="Sequence of questions asked"
    )
    response_quality_progression = models.JSONField(
        default=list, help_text="Quality of responses over time"
    )
    engagement_progression = models.JSONField(
        default=list, help_text="Engagement level over time"
    )

    # Flow analysis
    optimal_sequence_score = models.FloatField(
        default=0.0, help_text="How optimal the question sequence was"
    )
    conversation_momentum = models.CharField(
        max_length=20, default="stable", help_text="Conversation momentum"
    )
    peak_engagement_point = models.IntegerField(
        null=True, blank=True, help_text="Question number with peak engagement"
    )

    # Adaptation tracking
    adaptations_made = models.PositiveIntegerField(
        default=0, help_text="Number of real-time adaptations made"
    )
    adaptation_effectiveness = models.FloatField(
        default=0.0, help_text="Effectiveness of adaptations made"
    )

    # Flow insights
    successful_transitions = models.JSONField(
        default=list, help_text="Successful question transitions"
    )
    problematic_transitions = models.JSONField(
        default=list, help_text="Problematic question transitions"
    )
    missed_opportunities = models.JSONField(
        default=list, help_text="Missed follow-up opportunities"
    )

    # Outcome correlation
    conversion_correlation = models.FloatField(
        default=0.0, help_text="Correlation between flow and conversion"
    )
    information_gathering_score = models.FloatField(
        default=0.0, help_text="Overall information gathering effectiveness"
    )

    # Timestamps
    flow_started_at = models.DateTimeField(auto_now_add=True)
    flow_completed_at = models.DateTimeField(null=True, blank=True)
    analyzed_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Conversation Flow"
        verbose_name_plural = "Conversation Flows"
        indexes = [
            models.Index(fields=["meeting", "optimal_sequence_score"]),
            models.Index(
                fields=["conversion_correlation", "information_gathering_score"]
            ),
        ]

    def __str__(self):
        return f"Conversation Flow - {self.meeting.title} - Score: {self.optimal_sequence_score}"

    def add_question_to_sequence(
        self, question: MeetingQuestion, response_quality: float, engagement_level: str
    ):
        """Add a question to the conversation sequence"""
        sequence_entry = {
            "question_id": str(question.id),
            "question_type": question.question_type,
            "question_text": question.question_text[:100],  # Truncated for storage
            "asked_at": timezone.now().isoformat(),
            "response_quality": response_quality,
            "engagement_level": engagement_level,
            "sequence_position": len(self.questions_asked_sequence) + 1,
        }

        self.questions_asked_sequence.append(sequence_entry)
        self.response_quality_progression.append(response_quality)
        self.engagement_progression.append(engagement_level)

        self.save(
            update_fields=[
                "questions_asked_sequence",
                "response_quality_progression",
                "engagement_progression",
                "analyzed_at",
            ]
        )

    def complete_flow(self):
        """Mark the conversation flow as completed and perform final analysis"""
        self.flow_completed_at = timezone.now()

        # Calculate final metrics
        if self.response_quality_progression:
            self.optimal_sequence_score = sum(self.response_quality_progression) / len(
                self.response_quality_progression
            )

        # Determine conversation momentum
        if len(self.response_quality_progression) >= 3:
            recent_avg = sum(self.response_quality_progression[-3:]) / 3
            early_avg = sum(self.response_quality_progression[:3]) / 3

            if recent_avg > early_avg * 1.2:
                self.conversation_momentum = "increasing"
            elif recent_avg < early_avg * 0.8:
                self.conversation_momentum = "decreasing"
            else:
                self.conversation_momentum = "stable"

        # Find peak engagement point
        if self.response_quality_progression:
            max_quality = max(self.response_quality_progression)
            self.peak_engagement_point = (
                self.response_quality_progression.index(max_quality) + 1
            )

        self.save()
