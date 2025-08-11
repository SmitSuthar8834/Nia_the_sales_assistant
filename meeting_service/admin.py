from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html

from .meeting_outcome_service import MeetingOutcomeService
from .models import (
    ConversationFlow,
    GoogleMeetCredentials,
    Meeting,
    MeetingInvitation,
    MeetingParticipant,
    MeetingQuestion,
    MeetingSession,
    MeetingStatusUpdate,
    MicrosoftTeamsCredentials,
    QuestionEffectivenessLog,
    QuestionTemplate,
)
from .pre_meeting_intelligence import PreMeetingIntelligenceService


class MeetingQuestionInline(admin.TabularInline):
    """Inline admin for meeting questions"""

    model = MeetingQuestion
    extra = 0
    fields = [
        "question_text",
        "question_type",
        "priority",
        "priority_level",
        "confidence_score",
        "asked_at",
        "response",
    ]
    readonly_fields = ["confidence_score", "asked_at"]
    ordering = ["-priority", "sequence_order"]


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    """Enhanced admin interface for Meeting model with lead context and conversation analysis"""

    list_display = [
        "title",
        "lead_company_display",
        "meeting_type",
        "scheduled_at",
        "status_display",
        "duration_minutes",
        "meeting_actions",
    ]

    list_filter = [
        "status",
        "meeting_type",
        "scheduled_at",
        "created_at",
        "lead__status",
        "lead__urgency_level",
    ]

    search_fields = [
        "title",
        "description",
        "lead__company_name",
        "lead__contact_info__name",
        "lead__contact_info__email",
    ]

    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "started_at",
        "ended_at",
        "actual_duration_minutes",
        "lead_context_display",
        "ai_insights_display",
    ]

    fieldsets = (
        (
            "Meeting Information",
            {"fields": ("title", "description", "meeting_type", "lead")},
        ),
        ("Scheduling", {"fields": ("scheduled_at", "duration_minutes", "status")}),
        (
            "Meeting Platform",
            {
                "fields": ("meeting_platform", "meeting_url", "recording_url"),
                "classes": ("collapse",),
            },
        ),
        (
            "Content & Outcomes",
            {
                "fields": ("agenda", "outcome", "action_items", "participants"),
                "classes": ("collapse",),
            },
        ),
        (
            "AI Analysis",
            {
                "fields": ("ai_insights", "ai_insights_display"),
                "classes": ("collapse",),
            },
        ),
        (
            "Lead Context",
            {"fields": ("lead_context_display",), "classes": ("collapse",)},
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "id",
                    "created_at",
                    "updated_at",
                    "started_at",
                    "ended_at",
                    "actual_duration_minutes",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    raw_id_fields = ("lead",)
    inlines = [MeetingQuestionInline]
    actions = [
        "generate_meeting_preparation_materials",
        "generate_meeting_agenda",
        "generate_talking_points",
        "generate_competitive_analysis",
        "generate_meeting_summary",
        "extract_action_items",
        "schedule_follow_up_actions",
        "update_lead_scoring",
        "process_complete_meeting_outcome",
    ]

    def lead_company_display(self, obj):
        """Display lead company name with link to lead admin"""
        if obj.lead:
            lead_url = reverse("admin:ai_service_lead_change", args=[obj.lead.id])
            return format_html(
                '<a href="{}" target="_blank">{}</a>', lead_url, obj.lead.company_name
            )
        return "-"

    lead_company_display.short_description = "Company"
    lead_company_display.admin_order_field = "lead__company_name"

    def status_display(self, obj):
        """Display meeting status with color coding"""
        status_colors = {
            "scheduled": "#007cba",
            "in_progress": "#28a745",
            "completed": "#6c757d",
            "cancelled": "#dc3545",
        }
        color = status_colors.get(obj.status, "#6c757d")

        # Add urgency indicator for overdue meetings
        extra_info = ""
        if obj.is_overdue:
            extra_info = " ⚠️"
        elif obj.is_upcoming:
            extra_info = " 📅"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{}</span>',
            color,
            obj.get_status_display(),
            extra_info,
        )

    status_display.short_description = "Status"
    status_display.admin_order_field = "status"

    def meeting_actions(self, obj):
        """Display action buttons for meeting management"""
        actions = []

        # Meeting status actions
        if obj.status == Meeting.Status.SCHEDULED:
            if obj.is_upcoming:
                actions.append(
                    '<button onclick="startMeeting(\'{}\');" class="button" style="background: #28a745; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;">▶️ Start</button>'.format(
                        obj.id
                    )
                )
            actions.append(
                '<button onclick="cancelMeeting(\'{}\');" class="button" style="background: #dc3545; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;">❌ Cancel</button>'.format(
                    obj.id
                )
            )
        elif obj.status == Meeting.Status.IN_PROGRESS:
            actions.append(
                '<button onclick="completeMeeting(\'{}\');" class="button" style="background: #6c757d; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;">✅ Complete</button>'.format(
                    obj.id
                )
            )

        # Live meeting support actions
        if obj.status == Meeting.Status.IN_PROGRESS:
            actions.append(
                '<button onclick="startLiveMeetingSession(\'{}\');" class="button" style="background: #17a2b8; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;">🎤 Live Support</button>'.format(
                    obj.id
                )
            )

        # Pre-meeting intelligence actions
        if obj.status in [Meeting.Status.SCHEDULED, Meeting.Status.IN_PROGRESS]:
            actions.append(
                '<button onclick="generatePreparationMaterials(\'{}\');" class="button" style="background: #6f42c1; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;">🎯 Prep Materials</button>'.format(
                    obj.id
                )
            )
            actions.append(
                '<button onclick="generateMeetingAgenda(\'{}\');" class="button" style="background: #17a2b8; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;">📋 Agenda</button>'.format(
                    obj.id
                )
            )
            actions.append(
                '<button onclick="generateTalkingPoints(\'{}\');" class="button" style="background: #fd7e14; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;">💬 Talking Points</button>'.format(
                    obj.id
                )
            )
            actions.append(
                '<button onclick="generateCompetitiveAnalysis(\'{}\');" class="button" style="background: #e83e8c; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;">🏆 Competitive</button>'.format(
                    obj.id
                )
            )

        # Post-meeting outcome tracking actions
        if obj.status == Meeting.Status.COMPLETED:
            actions.append(
                '<button onclick="generateMeetingSummary(\'{}\');" class="button" style="background: #28a745; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;">📝 Summary</button>'.format(
                    obj.id
                )
            )
            actions.append(
                '<button onclick="extractActionItems(\'{}\');" class="button" style="background: #ffc107; color: black; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;">✅ Actions</button>'.format(
                    obj.id
                )
            )
            actions.append(
                '<button onclick="scheduleFollowUp(\'{}\');" class="button" style="background: #17a2b8; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;">📅 Follow-up</button>'.format(
                    obj.id
                )
            )
            actions.append(
                '<button onclick="updateLeadScoring(\'{}\');" class="button" style="background: #6f42c1; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;">📊 Update Score</button>'.format(
                    obj.id
                )
            )
            actions.append(
                '<button onclick="processCompleteOutcome(\'{}\');" class="button" style="background: #dc3545; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;">🚀 Process All</button>'.format(
                    obj.id
                )
            )

        # Always show view lead button
        if obj.lead:
            lead_url = reverse("admin:ai_service_lead_change", args=[obj.lead.id])
            actions.append(
                '<a href="{}" target="_blank" class="button" style="background: #007cba; color: white; text-decoration: none; padding: 4px 8px; border-radius: 3px;">👤 View Lead</a>'.format(
                    lead_url
                )
            )

        return format_html(" ".join(actions))

    meeting_actions.short_description = "Actions"

    def lead_context_display(self, obj):
        """Display comprehensive lead context information"""
        if not obj.lead:
            return "No lead associated"

        lead = obj.lead
        context_html = f"""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
            <h3 style="margin-top: 0; color: #007cba;">Lead Context: {lead.company_name}</h3>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div>
                    <h4>Company Information</h4>
                    <p><strong>Industry:</strong> {lead.industry or 'Not specified'}</p>
                    <p><strong>Company Size:</strong> {lead.company_size or 'Not specified'}</p>
                    <p><strong>Status:</strong> <span style="color: #007cba; font-weight: bold;">{lead.get_status_display()}</span></p>
                    <p><strong>Urgency:</strong> {lead.get_urgency_level_display() if lead.urgency_level else 'Not specified'}</p>
                </div>
                
                <div>
                    <h4>Contact Information</h4>
                    <p><strong>Name:</strong> {lead.contact_name or 'Not specified'}</p>
                    <p><strong>Email:</strong> {lead.contact_email or 'Not specified'}</p>
                    <p><strong>Phone:</strong> {lead.contact_phone or 'Not specified'}</p>
                    <p><strong>Title:</strong> {lead.contact_info.get('title', 'Not specified')}</p>
                </div>
            </div>
            
            <div style="margin-top: 15px;">
                <h4>Business Context</h4>
                <p><strong>Pain Points:</strong> {', '.join(lead.pain_points) if lead.pain_points else 'None identified'}</p>
                <p><strong>Requirements:</strong> {', '.join(lead.requirements) if lead.requirements else 'None specified'}</p>
                <p><strong>Budget Info:</strong> {lead.budget_info or 'Not discussed'}</p>
                <p><strong>Timeline:</strong> {lead.timeline or 'Not specified'}</p>
                <p><strong>Decision Makers:</strong> {', '.join(lead.decision_makers) if lead.decision_makers else 'Not identified'}</p>
            </div>
        </div>
        """
        return format_html(context_html)

    lead_context_display.short_description = "Lead Context"

    def ai_insights_display(self, obj):
        """Display AI insights and conversation analysis"""
        if not obj.lead or not hasattr(obj.lead, "ai_insights"):
            return "No AI insights available"

        try:
            insights = obj.lead.ai_insights
            insights_html = f"""
            <div style="background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 10px 0;">
                <h3 style="margin-top: 0; color: #0056b3;">🤖 AI Conversation Analysis</h3>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div>
                        <h4>Lead Quality Metrics</h4>
                        <p><strong>Lead Score:</strong> <span style="color: #28a745; font-weight: bold;">{insights.lead_score}/100</span></p>
                        <p><strong>Conversion Probability:</strong> <span style="color: #007cba; font-weight: bold;">{insights.conversion_probability}%</span></p>
                        <p><strong>Quality Tier:</strong> {insights.get_quality_tier_display()}</p>
                        <p><strong>Opportunity Conversion Score:</strong> {insights.opportunity_conversion_score}/100</p>
                    </div>
                    
                    <div>
                        <h4>Strategic Insights</h4>
                        <p><strong>Primary Strategy:</strong> {insights.primary_strategy or 'Not defined'}</p>
                        <p><strong>Competitive Risk:</strong> {insights.get_competitive_risk_display()}</p>
                        <p><strong>Estimated Deal Size:</strong> {insights.estimated_deal_size or 'Not estimated'}</p>
                        <p><strong>Sales Cycle Prediction:</strong> {insights.sales_cycle_prediction or 'Not predicted'}</p>
                    </div>
                </div>
                
                <div style="margin-top: 15px;">
                    <h4>Recommendations for Meeting</h4>
                    <div style="background: white; padding: 10px; border-radius: 3px;">
                        <p><strong>Next Best Action:</strong> {insights.next_best_action or 'No specific action recommended'}</p>
                        <p><strong>Key Messaging Points:</strong></p>
                        <ul>
                            {''.join([f'<li>{msg}</li>' for msg in insights.key_messaging]) if insights.key_messaging else '<li>No specific messaging points</li>'}
                        </ul>
                        <p><strong>Recommended Actions:</strong></p>
                        <ul>
                            {''.join([f'<li>{action}</li>' for action in insights.recommended_actions]) if insights.recommended_actions else '<li>No specific actions recommended</li>'}
                        </ul>
                    </div>
                </div>
                
                <div style="margin-top: 15px;">
                    <h4>Risk & Opportunity Analysis</h4>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div>
                            <p><strong>Risk Factors:</strong></p>
                            <ul style="color: #dc3545;">
                                {''.join([f'<li>{risk}</li>' for risk in insights.risk_factors]) if insights.risk_factors else '<li>No significant risks identified</li>'}
                            </ul>
                        </div>
                        <div>
                            <p><strong>Opportunities:</strong></p>
                            <ul style="color: #28a745;">
                                {''.join([f'<li>{opp}</li>' for opp in insights.opportunities]) if insights.opportunities else '<li>No specific opportunities identified</li>'}
                            </ul>
                        </div>
                    </div>
                </div>
                
                <div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid #ccc;">
                    <small style="color: #6c757d;">
                        Last analyzed: {insights.last_analyzed.strftime('%Y-%m-%d %H:%M:%S')} | 
                        Confidence: {insights.confidence_score}% | 
                        Data Completeness: {insights.data_completeness}%
                    </small>
                </div>
            </div>
            """
            return format_html(insights_html)
        except Exception as e:
            return f"Error loading AI insights: {str(e)}"

    ai_insights_display.short_description = "AI Insights & Conversation Analysis"

    def generate_meeting_preparation_materials(self, request, queryset):
        """Admin action to generate comprehensive preparation materials for selected meetings"""
        intelligence_service = PreMeetingIntelligenceService()
        success_count = 0
        error_count = 0

        for meeting in queryset:
            try:
                result = intelligence_service.generate_preparation_materials(
                    meeting, regenerate=True
                )
                if result.get("success"):
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"Error generating materials for {meeting.title}: {str(e)}",
                    level=messages.ERROR,
                )

        if success_count > 0:
            self.message_user(
                request,
                f"Successfully generated preparation materials for {success_count} meeting(s).",
                level=messages.SUCCESS,
            )
        if error_count > 0:
            self.message_user(
                request,
                f"Failed to generate materials for {error_count} meeting(s).",
                level=messages.WARNING,
            )

    generate_meeting_preparation_materials.short_description = (
        "🎯 Generate comprehensive preparation materials"
    )

    def generate_meeting_agenda(self, request, queryset):
        """Admin action to generate AI-powered meeting agendas"""
        intelligence_service = PreMeetingIntelligenceService()
        success_count = 0
        error_count = 0

        for meeting in queryset:
            try:
                result = intelligence_service.generate_meeting_agenda(
                    meeting, regenerate=True
                )
                if result.get("success"):
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"Error generating agenda for {meeting.title}: {str(e)}",
                    level=messages.ERROR,
                )

        if success_count > 0:
            self.message_user(
                request,
                f"Successfully generated agendas for {success_count} meeting(s).",
                level=messages.SUCCESS,
            )
        if error_count > 0:
            self.message_user(
                request,
                f"Failed to generate agendas for {error_count} meeting(s).",
                level=messages.WARNING,
            )

    generate_meeting_agenda.short_description = "📋 Generate AI meeting agenda"

    def generate_talking_points(self, request, queryset):
        """Admin action to generate AI-powered talking points"""
        intelligence_service = PreMeetingIntelligenceService()
        success_count = 0
        error_count = 0

        for meeting in queryset:
            try:
                result = intelligence_service.generate_talking_points(meeting)
                if result.get("success"):
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"Error generating talking points for {meeting.title}: {str(e)}",
                    level=messages.ERROR,
                )

        if success_count > 0:
            self.message_user(
                request,
                f"Successfully generated talking points for {success_count} meeting(s).",
                level=messages.SUCCESS,
            )
        if error_count > 0:
            self.message_user(
                request,
                f"Failed to generate talking points for {error_count} meeting(s).",
                level=messages.WARNING,
            )

    generate_talking_points.short_description = "💬 Generate talking points"

    def generate_competitive_analysis(self, request, queryset):
        """Admin action to generate competitive analysis"""
        intelligence_service = PreMeetingIntelligenceService()
        success_count = 0
        error_count = 0

        for meeting in queryset:
            try:
                result = intelligence_service.generate_competitive_analysis(meeting)
                if result.get("success"):
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"Error generating competitive analysis for {meeting.title}: {str(e)}",
                    level=messages.ERROR,
                )

        if success_count > 0:
            self.message_user(
                request,
                f"Successfully generated competitive analysis for {success_count} meeting(s).",
                level=messages.SUCCESS,
            )
        if error_count > 0:
            self.message_user(
                request,
                f"Failed to generate competitive analysis for {error_count} meeting(s).",
                level=messages.WARNING,
            )

    generate_competitive_analysis.short_description = "🏆 Generate competitive analysis"

    def generate_meeting_summary(self, request, queryset):
        """Admin action to generate post-meeting summaries"""
        outcome_service = MeetingOutcomeService()
        success_count = 0
        error_count = 0

        for meeting in queryset:
            if meeting.status != Meeting.Status.COMPLETED:
                self.message_user(
                    request,
                    f'Meeting "{meeting.title}" is not completed yet.',
                    level=messages.WARNING,
                )
                continue

            try:
                result = outcome_service.generate_meeting_summary(
                    meeting, regenerate=True
                )
                if result.get("success"):
                    success_count += 1
                else:
                    error_count += 1
                    self.message_user(
                        request,
                        f'Error generating summary for {meeting.title}: {result.get("error", "Unknown error")}',
                        level=messages.ERROR,
                    )
            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"Error generating summary for {meeting.title}: {str(e)}",
                    level=messages.ERROR,
                )

        if success_count > 0:
            self.message_user(
                request,
                f"Successfully generated meeting summaries for {success_count} meeting(s).",
                level=messages.SUCCESS,
            )
        if error_count > 0:
            self.message_user(
                request,
                f"Failed to generate summaries for {error_count} meeting(s).",
                level=messages.WARNING,
            )

    generate_meeting_summary.short_description = "📝 Generate post-meeting summaries"

    def extract_action_items(self, request, queryset):
        """Admin action to extract action items from meetings"""
        outcome_service = MeetingOutcomeService()
        success_count = 0
        error_count = 0

        for meeting in queryset:
            if meeting.status != Meeting.Status.COMPLETED:
                self.message_user(
                    request,
                    f'Meeting "{meeting.title}" is not completed yet.',
                    level=messages.WARNING,
                )
                continue

            try:
                result = outcome_service.extract_action_items(meeting, regenerate=True)
                if result.get("success"):
                    success_count += 1
                else:
                    error_count += 1
                    self.message_user(
                        request,
                        f'Error extracting action items for {meeting.title}: {result.get("error", "Unknown error")}',
                        level=messages.ERROR,
                    )
            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"Error extracting action items for {meeting.title}: {str(e)}",
                    level=messages.ERROR,
                )

        if success_count > 0:
            self.message_user(
                request,
                f"Successfully extracted action items for {success_count} meeting(s).",
                level=messages.SUCCESS,
            )
        if error_count > 0:
            self.message_user(
                request,
                f"Failed to extract action items for {error_count} meeting(s).",
                level=messages.WARNING,
            )

    extract_action_items.short_description = "✅ Extract action items and assignments"

    def schedule_follow_up_actions(self, request, queryset):
        """Admin action to schedule follow-up actions"""
        outcome_service = MeetingOutcomeService()
        success_count = 0
        error_count = 0

        for meeting in queryset:
            if meeting.status != Meeting.Status.COMPLETED:
                self.message_user(
                    request,
                    f'Meeting "{meeting.title}" is not completed yet.',
                    level=messages.WARNING,
                )
                continue

            try:
                result = outcome_service.schedule_follow_up_actions(meeting)
                if result.get("success"):
                    success_count += 1
                else:
                    error_count += 1
                    self.message_user(
                        request,
                        f'Error scheduling follow-up for {meeting.title}: {result.get("error", "Unknown error")}',
                        level=messages.ERROR,
                    )
            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"Error scheduling follow-up for {meeting.title}: {str(e)}",
                    level=messages.ERROR,
                )

        if success_count > 0:
            self.message_user(
                request,
                f"Successfully scheduled follow-up actions for {success_count} meeting(s).",
                level=messages.SUCCESS,
            )
        if error_count > 0:
            self.message_user(
                request,
                f"Failed to schedule follow-up for {error_count} meeting(s).",
                level=messages.WARNING,
            )

    schedule_follow_up_actions.short_description = (
        "📅 Schedule next steps and follow-up"
    )

    def update_lead_scoring(self, request, queryset):
        """Admin action to update lead scoring based on meeting outcomes"""
        outcome_service = MeetingOutcomeService()
        success_count = 0
        error_count = 0

        for meeting in queryset:
            if meeting.status != Meeting.Status.COMPLETED:
                self.message_user(
                    request,
                    f'Meeting "{meeting.title}" is not completed yet.',
                    level=messages.WARNING,
                )
                continue

            if not meeting.lead:
                self.message_user(
                    request,
                    f'Meeting "{meeting.title}" has no associated lead.',
                    level=messages.WARNING,
                )
                continue

            try:
                result = outcome_service.update_lead_scoring(meeting)
                if result.get("success"):
                    success_count += 1
                    # Show score changes in message
                    score_changes = result.get("score_changes", {})
                    if score_changes:
                        changes_text = ", ".join(
                            [
                                f"{k}: {v:+.1f}"
                                for k, v in score_changes.items()
                                if v != 0
                            ]
                        )
                        self.message_user(
                            request,
                            f"Updated scoring for {meeting.lead.company_name}: {changes_text}",
                            level=messages.INFO,
                        )
                else:
                    error_count += 1
                    self.message_user(
                        request,
                        f'Error updating scoring for {meeting.title}: {result.get("error", "Unknown error")}',
                        level=messages.ERROR,
                    )
            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"Error updating scoring for {meeting.title}: {str(e)}",
                    level=messages.ERROR,
                )

        if success_count > 0:
            self.message_user(
                request,
                f"Successfully updated lead scoring for {success_count} meeting(s).",
                level=messages.SUCCESS,
            )
        if error_count > 0:
            self.message_user(
                request,
                f"Failed to update scoring for {error_count} meeting(s).",
                level=messages.WARNING,
            )

    update_lead_scoring.short_description = "📊 Update lead scoring based on outcomes"

    def process_complete_meeting_outcome(self, request, queryset):
        """Admin action to process complete meeting outcome (all components)"""
        outcome_service = MeetingOutcomeService()
        success_count = 0
        error_count = 0

        for meeting in queryset:
            if meeting.status != Meeting.Status.COMPLETED:
                self.message_user(
                    request,
                    f'Meeting "{meeting.title}" is not completed yet.',
                    level=messages.WARNING,
                )
                continue

            try:
                result = outcome_service.process_complete_meeting_outcome(
                    meeting, regenerate=True
                )
                if result.get("overall_success"):
                    success_count += 1
                    self.message_user(
                        request,
                        f'Successfully processed all outcomes for "{meeting.title}".',
                        level=messages.SUCCESS,
                    )
                else:
                    error_count += 1
                    failed_components = [
                        name
                        for name, component in result.get("components", {}).items()
                        if not component.get("success", False)
                    ]
                    self.message_user(
                        request,
                        f'Partial success for {meeting.title}. Failed: {", ".join(failed_components)}',
                        level=messages.WARNING,
                    )
            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"Error processing outcomes for {meeting.title}: {str(e)}",
                    level=messages.ERROR,
                )

        if success_count > 0:
            self.message_user(
                request,
                f"Successfully processed complete outcomes for {success_count} meeting(s).",
                level=messages.SUCCESS,
            )
        if error_count > 0:
            self.message_user(
                request,
                f"Had issues processing {error_count} meeting(s).",
                level=messages.WARNING,
            )

    process_complete_meeting_outcome.short_description = (
        "🚀 Process all meeting outcomes (summary, actions, follow-up, scoring)"
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related for better performance"""
        return super().get_queryset(request).select_related("lead", "lead__ai_insights")

    class Media:
        js = ("admin/js/meeting_actions.js", "admin/js/live_meeting_support.js")
        css = {"all": ("admin/css/meeting_admin.css",)}


# Register other meeting-related models for completeness
@admin.register(MeetingSession)
class MeetingSessionAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "organizer",
        "meeting_type",
        "scheduled_start_time",
        "status",
    ]
    list_filter = ["status", "meeting_type", "scheduled_start_time"]
    search_fields = ["title", "description", "organizer__username"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(MeetingParticipant)
class MeetingParticipantAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "meeting", "role", "status"]
    list_filter = ["role", "status", "meeting__meeting_type"]
    search_fields = ["name", "email", "meeting__title"]


@admin.register(MeetingStatusUpdate)
class MeetingStatusUpdateAdmin(admin.ModelAdmin):
    list_display = ["meeting", "update_type", "timestamp", "triggered_by"]
    list_filter = ["update_type", "timestamp"]
    search_fields = ["meeting__title", "description"]
    readonly_fields = ["timestamp"]


@admin.register(MeetingInvitation)
class MeetingInvitationAdmin(admin.ModelAdmin):
    list_display = ["participant", "meeting", "status", "sent_at"]
    list_filter = ["status", "sent_at"]
    search_fields = ["participant__name", "participant__email", "meeting__title"]


@admin.register(GoogleMeetCredentials)
class GoogleMeetCredentialsAdmin(admin.ModelAdmin):
    list_display = ["user", "created_at", "token_expiry", "is_expired"]
    readonly_fields = ["created_at", "updated_at"]

    def is_expired(self, obj):
        return obj.is_token_expired()

    is_expired.boolean = True
    is_expired.short_description = "Token Expired"


@admin.register(MicrosoftTeamsCredentials)
class MicrosoftTeamsCredentialsAdmin(admin.ModelAdmin):
    list_display = ["user", "created_at", "token_expiry", "is_expired"]
    readonly_fields = ["created_at", "updated_at"]

    def is_expired(self, obj):
        return obj.is_token_expired()

    is_expired.boolean = True
    is_expired.short_description = "Token Expired"


@admin.register(MeetingQuestion)
class MeetingQuestionAdmin(admin.ModelAdmin):
    """Enhanced admin interface for AI-generated meeting questions with manual override capabilities"""

    list_display = [
        "question_preview",
        "meeting_title",
        "question_type",
        "priority_display",
        "confidence_score",
        "asked_status",
        "ai_generated",
        "question_actions",
    ]

    list_filter = [
        "question_type",
        "priority_level",
        "ai_generated",
        "industry_specific",
        "asked_at",
        "meeting__meeting_type",
        "meeting__status",
        "effectiveness_score",
    ]

    search_fields = [
        "question_text",
        "meeting__title",
        "meeting__lead__company_name",
        "response",
        "target_persona",
    ]

    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "generation_context_display",
        "effectiveness_display",
        "question_analytics_display",
    ]

    fieldsets = (
        (
            "Question Details",
            {"fields": ("meeting", "question_text", "question_type", "target_persona")},
        ),
        (
            "Manual Override Controls",
            {
                "fields": (
                    "priority",
                    "priority_level",
                    "sequence_order",
                    "depends_on_question",
                    "ai_generated",
                    "confidence_score",
                    "industry_specific",
                ),
                "description": "Use these fields to manually override AI-generated settings and customize question behavior.",
            },
        ),
        (
            "AI Generation Context",
            {"fields": ("generation_context_display",), "classes": ("collapse",)},
        ),
        (
            "Usage & Response Tracking",
            {
                "fields": (
                    "asked_at",
                    "response",
                    "response_quality",
                    "triggers_follow_up",
                    "follow_up_questions",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Performance Analytics",
            {
                "fields": (
                    "effectiveness_score",
                    "led_to_qualification",
                    "led_to_objection",
                    "effectiveness_display",
                    "question_analytics_display",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("id", "created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    raw_id_fields = ("meeting", "depends_on_question", "created_by")
    actions = [
        "mark_as_manual_override",
        "reset_ai_generation",
        "bulk_update_priority",
        "export_question_analytics",
    ]

    def question_preview(self, obj):
        """Display truncated question text"""
        return (
            obj.question_text[:80] + "..."
            if len(obj.question_text) > 80
            else obj.question_text
        )

    question_preview.short_description = "Question"

    def meeting_title(self, obj):
        """Display meeting title with link"""
        meeting_url = reverse(
            "admin:meeting_service_meeting_change", args=[obj.meeting.id]
        )
        return format_html(
            '<a href="{}" target="_blank">{}</a>', meeting_url, obj.meeting.title
        )

    meeting_title.short_description = "Meeting"
    meeting_title.admin_order_field = "meeting__title"

    def priority_display(self, obj):
        """Display priority with visual indicators"""
        priority_colors = {"high": "#dc3545", "medium": "#ffc107", "low": "#28a745"}
        color = priority_colors.get(obj.priority_level, "#6c757d")

        priority_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        icon = priority_icons.get(obj.priority_level, "⚪")

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {} ({})</span>',
            color,
            icon,
            obj.get_priority_level_display(),
            obj.priority,
        )

    priority_display.short_description = "Priority"
    priority_display.admin_order_field = "priority"

    def asked_status(self, obj):
        """Display whether question has been asked"""
        if obj.asked_at:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✅ Asked</span><br>'
                "<small>{}</small>",
                obj.asked_at.strftime("%Y-%m-%d %H:%M"),
            )
        else:
            return format_html('<span style="color: #6c757d;">⏳ Not Asked</span>')

    asked_status.short_description = "Status"

    def question_actions(self, obj):
        """Display action buttons for question management"""
        actions = []

        if not obj.asked_at:
            actions.append(
                '<button onclick="markQuestionAsked(\'{}\');" class="button" style="background: #28a745; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;">✅ Mark Asked</button>'.format(
                    obj.id
                )
            )

        # Manual override button
        if obj.ai_generated:
            actions.append(
                '<button onclick="toggleManualOverride(\'{}\');" class="button" style="background: #ffc107; color: black; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;">✏️ Override</button>'.format(
                    obj.id
                )
            )

        # Effectiveness update button
        actions.append(
            '<button onclick="updateQuestionEffectiveness(\'{}\');" class="button" style="background: #6f42c1; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;">📊 Update Score</button>'.format(
                obj.id
            )
        )

        if obj.is_conversion_focused:
            actions.append(
                '<span style="background: #007cba; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">🎯 Conversion</span>'
            )

        if obj.industry_specific:
            actions.append(
                '<span style="background: #6f42c1; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">🏢 Industry</span>'
            )

        # View meeting button
        meeting_url = reverse(
            "admin:meeting_service_meeting_change", args=[obj.meeting.id]
        )
        actions.append(
            '<a href="{}" target="_blank" class="button" style="background: #007cba; color: white; text-decoration: none; padding: 4px 8px; border-radius: 3px;">📅 Meeting</a>'.format(
                meeting_url
            )
        )

        return format_html(" ".join(actions))

    question_actions.short_description = "Actions"

    def question_analytics_display(self, obj):
        """Display comprehensive question analytics and performance metrics"""
        if not obj.asked_at:
            return format_html(
                '<p style="color: #6c757d;">Question not yet asked - no analytics available.</p>'
            )

        # Calculate analytics
        response_length = len(obj.response.split()) if obj.response else 0
        effectiveness_tier = (
            "High"
            if (obj.effectiveness_score or 0) >= 80
            else "Medium" if (obj.effectiveness_score or 0) >= 60 else "Low"
        )
        tier_color = (
            "#28a745"
            if (obj.effectiveness_score or 0) >= 80
            else "#ffc107" if (obj.effectiveness_score or 0) >= 60 else "#dc3545"
        )

        analytics_html = f"""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
            <h3 style="margin-top: 0; color: #007cba;">📈 Question Performance Analytics</h3>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                <div style="text-align: center; padding: 10px; background: white; border-radius: 5px;">
                    <h4 style="margin: 0; color: {tier_color};">{obj.effectiveness_score or 0:.1f}</h4>
                    <small>Effectiveness Score</small>
                </div>
                <div style="text-align: center; padding: 10px; background: white; border-radius: 5px;">
                    <h4 style="margin: 0; color: #007cba;">{obj.confidence_score:.1f}%</h4>
                    <small>AI Confidence</small>
                </div>
                <div style="text-align: center; padding: 10px; background: white; border-radius: 5px;">
                    <h4 style="margin: 0; color: #6c757d;">{response_length}</h4>
                    <small>Response Words</small>
                </div>
                <div style="text-align: center; padding: 10px; background: white; border-radius: 5px;">
                    <h4 style="margin: 0; color: {tier_color};">{effectiveness_tier}</h4>
                    <small>Performance Tier</small>
                </div>
            </div>
            
            <div style="margin-top: 15px;">
                <h4>Question Impact Analysis</h4>
                <div style="background: white; padding: 10px; border-radius: 3px;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div>
                            <p><strong>Qualification Impact:</strong> {'✅ Yes' if obj.led_to_qualification else '❌ No'}</p>
                            <p><strong>Objection Surfaced:</strong> {'⚠️ Yes' if obj.led_to_objection else '✅ No'}</p>
                            <p><strong>Follow-up Triggered:</strong> {'✅ Yes' if obj.triggers_follow_up else '❌ No'}</p>
                        </div>
                        <div>
                            <p><strong>Question Type:</strong> {obj.get_question_type_display()}</p>
                            <p><strong>Priority Level:</strong> {obj.get_priority_level_display()}</p>
                            <p><strong>Response Quality:</strong> {obj.response_quality or 'Not rated'}</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div style="margin-top: 15px;">
                <h4>Optimization Insights</h4>
                <div style="background: white; padding: 10px; border-radius: 3px;">
                    {'<p style="color: #28a745;">🎯 High-performing question! Consider using similar questions for this question type.</p>' if (obj.effectiveness_score or 0) >= 80 else ''}
                    {'<p style="color: #ffc107;">📊 Moderate performance. Consider refining the question or timing.</p>' if 60 <= (obj.effectiveness_score or 0) < 80 else ''}
                    {'<p style="color: #dc3545;">🔧 Low performance. This question may need significant revision or different context.</p>' if (obj.effectiveness_score or 0) < 60 else ''}
                    
                    <p><strong>Improvement Suggestions:</strong></p>
                    <ul>
                        <li>{'Analyze response patterns for similar questions' if (obj.effectiveness_score or 0) >= 60 else 'Consider rewording for clarity and engagement'}</li>
                        <li>{'Use as template for similar scenarios' if (obj.effectiveness_score or 0) >= 80 else 'Test different timing in conversation flow'}</li>
                        <li>{'Monitor for consistent high performance' if (obj.effectiveness_score or 0) >= 80 else 'Review industry-specific customization needs'}</li>
                    </ul>
                </div>
            </div>
            
            <div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid #ccc;">
                <small style="color: #6c757d;">
                    Asked: {obj.asked_at.strftime('%Y-%m-%d %H:%M:%S')} | 
                    Meeting: {obj.meeting.title} | 
                    Lead: {obj.meeting.lead.company_name}
                </small>
            </div>
        </div>
        """
        return format_html(analytics_html)

    question_analytics_display.short_description = "Question Analytics"

    def mark_as_manual_override(self, request, queryset):
        """Admin action to mark questions as manually overridden"""
        updated = queryset.update(ai_generated=False, created_by=request.user)
        self.message_user(
            request, f"Successfully marked {updated} question(s) as manual override."
        )

    mark_as_manual_override.short_description = "Mark as manual override"

    def reset_ai_generation(self, request, queryset):
        """Admin action to reset questions to AI-generated status"""
        updated = queryset.update(ai_generated=True)
        self.message_user(
            request, f"Successfully reset {updated} question(s) to AI-generated status."
        )

    reset_ai_generation.short_description = "Reset to AI-generated"

    def bulk_update_priority(self, request, queryset):
        """Admin action to bulk update question priorities"""
        # This would open a form to set new priority
        self.message_user(
            request,
            f"Bulk priority update functionality coming soon for {queryset.count()} question(s).",
        )

    bulk_update_priority.short_description = "Bulk update priority"

    def export_question_analytics(self, request, queryset):
        """Admin action to export question analytics"""
        # This would generate a CSV/Excel export of question performance
        self.message_user(
            request,
            f"Question analytics export functionality coming soon for {queryset.count()} question(s).",
        )

    export_question_analytics.short_description = "Export analytics"

    def generation_context_display(self, obj):
        """Display AI generation context in a readable format"""
        if not obj.generation_context:
            return "No generation context available"

        context = obj.generation_context
        context_html = f"""
        <div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">
            <h4 style="margin-top: 0;">AI Generation Context</h4>
            <p><strong>Rationale:</strong> {context.get('rationale', 'Not provided')}</p>
            <p><strong>Expected Insights:</strong></p>
            <ul>
                {''.join([f'<li>{insight}</li>' for insight in context.get('expected_insights', [])]) or '<li>None specified</li>'}
            </ul>
            <p><strong>Follow-up Triggers:</strong></p>
            <ul>
                {''.join([f'<li>{trigger}</li>' for trigger in context.get('follow_up_triggers', [])]) or '<li>None specified</li>'}
            </ul>
            <p><strong>Category:</strong> {context.get('category', 'Not specified')}</p>
        </div>
        """
        return format_html(context_html)

    generation_context_display.short_description = "Generation Context"

    def effectiveness_display(self, obj):
        """Display question effectiveness metrics"""
        if obj.effectiveness_score is None:
            return "Not yet measured"

        effectiveness_html = f"""
        <div style="background: #e8f4fd; padding: 10px; border-radius: 5px;">
            <h4 style="margin-top: 0;">Effectiveness Metrics</h4>
            <p><strong>Effectiveness Score:</strong> <span style="color: #007cba; font-weight: bold;">{obj.effectiveness_score}/100</span></p>
            <p><strong>Led to Qualification:</strong> {'✅ Yes' if obj.led_to_qualification else '❌ No'}</p>
            <p><strong>Led to Objection:</strong> {'⚠️ Yes' if obj.led_to_objection else '✅ No'}</p>
            {f'<p><strong>Response Quality:</strong> {obj.response_quality}</p>' if obj.response_quality else ''}
        </div>
        """
        return format_html(effectiveness_html)

    effectiveness_display.short_description = "Effectiveness"

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return (
            super()
            .get_queryset(request)
            .select_related(
                "meeting", "meeting__lead", "depends_on_question", "created_by"
            )
        )

    class Media:
        js = ("admin/js/meeting_question_actions.js",)
        css = {"all": ("admin/css/meeting_question_admin.css",)}


@admin.register(QuestionTemplate)
class QuestionTemplateAdmin(admin.ModelAdmin):
    """Enhanced admin interface for industry-specific question templates with customization and analytics"""

    list_display = [
        "name",
        "industry",
        "template_type",
        "question_category",
        "priority",
        "success_rate_display",
        "usage_count",
        "is_active",
        "template_actions",
    ]

    list_filter = [
        "industry",
        "template_type",
        "question_category",
        "is_active",
        "is_ai_generated",
        "priority",
        "created_at",
    ]

    search_fields = ["name", "question_template", "rationale", "industry"]

    readonly_fields = [
        "id",
        "usage_count",
        "success_rate",
        "created_at",
        "updated_at",
        "performance_analytics_display",
        "template_preview",
    ]

    fieldsets = (
        (
            "Template Information",
            {"fields": ("name", "industry", "template_type", "question_category")},
        ),
        (
            "Template Content",
            {
                "fields": (
                    "question_template",
                    "template_preview",
                    "variables",
                    "rationale",
                )
            },
        ),
        (
            "Template Metadata",
            {
                "fields": (
                    "priority",
                    "confidence_score",
                    "expected_responses",
                    "follow_up_triggers",
                )
            },
        ),
        (
            "Targeting & Filtering",
            {
                "fields": ("company_size_filter", "meeting_stage_filter"),
                "classes": ("collapse",),
            },
        ),
        (
            "Performance Analytics",
            {"fields": ("performance_analytics_display",), "classes": ("collapse",)},
        ),
        (
            "Usage Statistics",
            {
                "fields": (
                    "usage_count",
                    "success_rate",
                    "is_active",
                    "is_ai_generated",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("id", "created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    raw_id_fields = ("created_by",)
    actions = [
        "duplicate_template",
        "activate_templates",
        "deactivate_templates",
        "export_templates",
    ]

    def success_rate_display(self, obj):
        """Display success rate with visual indicator"""
        if obj.success_rate == 0:
            return format_html('<span style="color: #6c757d;">No data</span>')

        color = (
            "#28a745"
            if obj.success_rate >= 70
            else "#ffc107" if obj.success_rate >= 50 else "#dc3545"
        )
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color,
            obj.success_rate,
        )

    success_rate_display.short_description = "Success Rate"
    success_rate_display.admin_order_field = "success_rate"

    def template_actions(self, obj):
        """Display action buttons for template management"""
        actions = []

        # Test template button
        actions.append(
            '<button onclick="testTemplate(\'{}\');" class="button" style="background: #007cba; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;">🧪 Test</button>'.format(
                obj.id
            )
        )

        # Duplicate template button
        actions.append(
            '<button onclick="duplicateTemplate(\'{}\');" class="button" style="background: #28a745; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;">📋 Duplicate</button>'.format(
                obj.id
            )
        )

        # View analytics button
        actions.append(
            '<button onclick="viewTemplateAnalytics(\'{}\');" class="button" style="background: #6f42c1; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;">📊 Analytics</button>'.format(
                obj.id
            )
        )

        return format_html(" ".join(actions))

    template_actions.short_description = "Actions"

    def template_preview(self, obj):
        """Display a preview of how the template would look with sample data"""
        sample_variables = {
            "company_name": "Acme Corp",
            "industry": obj.industry,
            "contact_name": "John Smith",
            "pain_point": "inefficient processes",
        }

        try:
            # Simple variable substitution for preview
            preview_text = obj.question_template
            for var, value in sample_variables.items():
                preview_text = preview_text.replace(f"{{{var}}}", value)

            return format_html(
                '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px; border-left: 4px solid #007cba;">'
                '<h4 style="margin-top: 0; color: #007cba;">Template Preview</h4>'
                '<p style="font-style: italic;">"{}"</p>'
                '<small style="color: #6c757d;">Sample variables: {}</small>'
                "</div>",
                preview_text,
                ", ".join([f"{k}={v}" for k, v in sample_variables.items()]),
            )
        except Exception as e:
            return format_html(
                '<span style="color: #dc3545;">Error generating preview: {}</span>',
                str(e),
            )

    template_preview.short_description = "Template Preview"

    def performance_analytics_display(self, obj):
        """Display detailed performance analytics for the template"""
        if obj.usage_count == 0:
            return format_html(
                '<p style="color: #6c757d;">No usage data available yet.</p>'
            )

        # Calculate performance metrics
        effectiveness_tier = (
            "High"
            if obj.success_rate >= 70
            else "Medium" if obj.success_rate >= 50 else "Low"
        )
        tier_color = (
            "#28a745"
            if obj.success_rate >= 70
            else "#ffc107" if obj.success_rate >= 50 else "#dc3545"
        )

        analytics_html = f"""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
            <h3 style="margin-top: 0; color: #007cba;">📊 Performance Analytics</h3>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-bottom: 15px;">
                <div style="text-align: center; padding: 10px; background: white; border-radius: 5px;">
                    <h4 style="margin: 0; color: #007cba;">{obj.usage_count}</h4>
                    <small>Times Used</small>
                </div>
                <div style="text-align: center; padding: 10px; background: white; border-radius: 5px;">
                    <h4 style="margin: 0; color: {tier_color};">{obj.success_rate:.1f}%</h4>
                    <small>Success Rate</small>
                </div>
                <div style="text-align: center; padding: 10px; background: white; border-radius: 5px;">
                    <h4 style="margin: 0; color: {tier_color};">{effectiveness_tier}</h4>
                    <small>Performance Tier</small>
                </div>
            </div>
            
            <div style="margin-top: 15px;">
                <h4>Template Effectiveness Insights</h4>
                <div style="background: white; padding: 10px; border-radius: 3px;">
                    <p><strong>Confidence Score:</strong> {obj.confidence_score}%</p>
                    <p><strong>Industry Specialization:</strong> {obj.industry.title()}</p>
                    <p><strong>Best Use Case:</strong> {obj.get_template_type_display()} meetings</p>
                    <p><strong>Question Category:</strong> {obj.get_question_category_display()}</p>
                </div>
            </div>
            
            <div style="margin-top: 15px;">
                <h4>Optimization Recommendations</h4>
                <div style="background: white; padding: 10px; border-radius: 3px;">
                    {'<p style="color: #28a745;">✅ This template is performing well! Consider using it as a baseline for similar templates.</p>' if obj.success_rate >= 70 else ''}
                    {'<p style="color: #ffc107;">⚠️ This template has moderate performance. Consider A/B testing variations.</p>' if 50 <= obj.success_rate < 70 else ''}
                    {'<p style="color: #dc3545;">❌ This template needs improvement. Review and update the question text or targeting.</p>' if obj.success_rate < 50 else ''}
                    <p><strong>Suggested Actions:</strong></p>
                    <ul>
                        <li>Review recent question responses for improvement opportunities</li>
                        <li>Test variations with different wording or approach</li>
                        <li>Consider industry-specific customizations</li>
                        <li>Analyze follow-up trigger effectiveness</li>
                    </ul>
                </div>
            </div>
        </div>
        """
        return format_html(analytics_html)

    performance_analytics_display.short_description = "Performance Analytics"

    def duplicate_template(self, request, queryset):
        """Admin action to duplicate selected templates"""
        duplicated_count = 0
        for template in queryset:
            # Create a duplicate with modified name
            template.pk = None
            template.name = f"{template.name} (Copy)"
            template.usage_count = 0
            template.success_rate = 0.0
            template.created_by = request.user
            template.save()
            duplicated_count += 1

        self.message_user(
            request, f"Successfully duplicated {duplicated_count} template(s)."
        )

    duplicate_template.short_description = "Duplicate selected templates"

    def activate_templates(self, request, queryset):
        """Admin action to activate selected templates"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Successfully activated {updated} template(s).")

    activate_templates.short_description = "Activate selected templates"

    def deactivate_templates(self, request, queryset):
        """Admin action to deactivate selected templates"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Successfully deactivated {updated} template(s).")

    deactivate_templates.short_description = "Deactivate selected templates"

    def export_templates(self, request, queryset):
        """Admin action to export selected templates"""
        # This would implement template export functionality
        self.message_user(
            request,
            f"Template export functionality coming soon for {queryset.count()} template(s).",
        )

    export_templates.short_description = "Export selected templates"

    class Media:
        js = ("admin/js/question_template_actions.js",)
        css = {"all": ("admin/css/question_template_admin.css",)}


@admin.register(QuestionEffectivenessLog)
class QuestionEffectivenessLogAdmin(admin.ModelAdmin):
    """Admin interface for question effectiveness tracking"""

    list_display = [
        "question_preview",
        "meeting_title",
        "effectiveness_score_display",
        "effectiveness_tier",
        "response_word_count",
        "logged_at",
    ]

    list_filter = [
        "effectiveness_tier",
        "logged_at",
        "led_to_qualification",
        "led_to_objection",
        "generated_follow_ups",
        "moved_deal_forward",
        "question__question_type",
        "meeting__meeting_type",
    ]

    search_fields = [
        "question__question_text",
        "meeting__title",
        "response_text",
        "meeting__lead__company_name",
    ]

    readonly_fields = [
        "id",
        "logged_at",
        "analyzed_at",
        "response_word_count",
        "effectiveness_breakdown_display",
        "learning_insights_display",
    ]

    fieldsets = (
        ("Question & Meeting", {"fields": ("question", "meeting")}),
        (
            "Effectiveness Metrics",
            {
                "fields": (
                    "effectiveness_score",
                    "effectiveness_tier",
                    "effectiveness_breakdown_display",
                )
            },
        ),
        (
            "Response Analysis",
            {
                "fields": (
                    "response_text",
                    "response_word_count",
                    "response_depth",
                    "buying_signals_identified",
                    "concerns_raised",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Context & Timing",
            {
                "fields": (
                    "question_timing",
                    "conversation_context",
                    "lead_engagement_level",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Outcomes",
            {
                "fields": (
                    "led_to_qualification",
                    "led_to_objection",
                    "generated_follow_ups",
                    "moved_deal_forward",
                )
            },
        ),
        (
            "Learning Insights",
            {
                "fields": (
                    "learning_insights_display",
                    "question_modifications",
                    "timing_adjustments",
                    "follow_up_suggestions",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("id", "logged_at", "analyzed_at"), "classes": ("collapse",)},
        ),
    )

    raw_id_fields = ("question", "meeting")

    def question_preview(self, obj):
        """Display truncated question text"""
        return (
            obj.question.question_text[:60] + "..."
            if len(obj.question.question_text) > 60
            else obj.question.question_text
        )

    question_preview.short_description = "Question"

    def meeting_title(self, obj):
        """Display meeting title with link"""
        meeting_url = reverse(
            "admin:meeting_service_meeting_change", args=[obj.meeting.id]
        )
        return format_html(
            '<a href="{}" target="_blank">{}</a>', meeting_url, obj.meeting.title
        )

    meeting_title.short_description = "Meeting"

    def effectiveness_score_display(self, obj):
        """Display effectiveness score with color coding"""
        color = (
            "#28a745"
            if obj.effectiveness_score >= 80
            else "#ffc107" if obj.effectiveness_score >= 60 else "#dc3545"
        )
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}</span>',
            color,
            obj.effectiveness_score,
        )

    effectiveness_score_display.short_description = "Score"
    effectiveness_score_display.admin_order_field = "effectiveness_score"

    def effectiveness_breakdown_display(self, obj):
        """Display detailed effectiveness breakdown"""
        breakdown_html = f"""
        <div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">
            <h4 style="margin-top: 0;">Effectiveness Breakdown</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                <div>
                    <p><strong>Response Quality:</strong> {obj.response_quality_score:.1f}</p>
                    <p><strong>Information Value:</strong> {obj.information_value_score:.1f}</p>
                    <p><strong>Engagement:</strong> {obj.engagement_score:.1f}</p>
                </div>
                <div>
                    <p><strong>Objective Advancement:</strong> {obj.objective_advancement_score:.1f}</p>
                    <p><strong>Pain Point Discovery:</strong> {obj.pain_point_discovery_score:.1f}</p>
                    <p><strong>Process Advancement:</strong> {obj.process_advancement_score:.1f}</p>
                </div>
            </div>
        </div>
        """
        return format_html(breakdown_html)

    effectiveness_breakdown_display.short_description = "Breakdown"

    def learning_insights_display(self, obj):
        """Display learning insights"""
        insights_html = f"""
        <div style="background: #e8f4fd; padding: 10px; border-radius: 5px;">
            <h4 style="margin-top: 0;">Learning Insights</h4>
            <div>
                <p><strong>What Worked Well:</strong></p>
                <ul>
                    {''.join([f'<li>{item}</li>' for item in obj.what_worked_well]) if obj.what_worked_well else '<li>No insights recorded</li>'}
                </ul>
                <p><strong>Improvement Opportunities:</strong></p>
                <ul>
                    {''.join([f'<li>{item}</li>' for item in obj.improvement_opportunities]) if obj.improvement_opportunities else '<li>No improvements identified</li>'}
                </ul>
                <p><strong>Context Factors:</strong></p>
                <ul>
                    {''.join([f'<li>{item}</li>' for item in obj.context_factors]) if obj.context_factors else '<li>No context factors noted</li>'}
                </ul>
            </div>
        </div>
        """
        return format_html(insights_html)

    learning_insights_display.short_description = "Learning Insights"


@admin.register(ConversationFlow)
class ConversationFlowAdmin(admin.ModelAdmin):
    """Admin interface for conversation flow tracking"""

    list_display = [
        "meeting_title",
        "optimal_sequence_score_display",
        "conversation_momentum",
        "peak_engagement_point",
        "adaptations_made",
        "flow_status",
    ]

    list_filter = [
        "conversation_momentum",
        "flow_completed_at",
        "flow_started_at",
        "meeting__meeting_type",
        "meeting__status",
    ]

    search_fields = ["meeting__title", "meeting__lead__company_name"]

    readonly_fields = [
        "id",
        "flow_started_at",
        "flow_completed_at",
        "analyzed_at",
        "questions_sequence_display",
        "flow_analysis_display",
    ]

    fieldsets = (
        ("Meeting Information", {"fields": ("meeting",)}),
        (
            "Flow Metrics",
            {
                "fields": (
                    "optimal_sequence_score",
                    "conversation_momentum",
                    "peak_engagement_point",
                )
            },
        ),
        (
            "Adaptation Tracking",
            {"fields": ("adaptations_made", "adaptation_effectiveness")},
        ),
        (
            "Flow Analysis",
            {
                "fields": ("flow_analysis_display", "questions_sequence_display"),
                "classes": ("collapse",),
            },
        ),
        (
            "Correlation Metrics",
            {
                "fields": ("conversion_correlation", "information_gathering_score"),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("id", "flow_started_at", "flow_completed_at", "analyzed_at"),
                "classes": ("collapse",),
            },
        ),
    )

    raw_id_fields = ("meeting",)

    def meeting_title(self, obj):
        """Display meeting title with link"""
        meeting_url = reverse(
            "admin:meeting_service_meeting_change", args=[obj.meeting.id]
        )
        return format_html(
            '<a href="{}" target="_blank">{}</a>', meeting_url, obj.meeting.title
        )

    meeting_title.short_description = "Meeting"

    def optimal_sequence_score_display(self, obj):
        """Display optimal sequence score with color coding"""
        color = (
            "#28a745"
            if obj.optimal_sequence_score >= 80
            else "#ffc107" if obj.optimal_sequence_score >= 60 else "#dc3545"
        )
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}</span>',
            color,
            obj.optimal_sequence_score,
        )

    optimal_sequence_score_display.short_description = "Sequence Score"
    optimal_sequence_score_display.admin_order_field = "optimal_sequence_score"

    def flow_status(self, obj):
        """Display flow completion status"""
        if obj.flow_completed_at:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✅ Completed</span>'
            )
        else:
            return format_html(
                '<span style="color: #ffc107; font-weight: bold;">⏳ In Progress</span>'
            )

    flow_status.short_description = "Status"

    def questions_sequence_display(self, obj):
        """Display the sequence of questions asked"""
        if not obj.questions_asked_sequence:
            return "No questions recorded"

        sequence_html = """
        <div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">
            <h4 style="margin-top: 0;">Question Sequence</h4>
            <ol>
        """

        for i, question_data in enumerate(obj.questions_asked_sequence):
            sequence_html += f"""
                <li style="margin-bottom: 10px;">
                    <strong>{question_data.get('question_type', 'Unknown')}:</strong> 
                    {question_data.get('question_text', 'No text')}<br>
                    <small style="color: #6c757d;">
                        Quality: {question_data.get('response_quality', 0):.1f} | 
                        Engagement: {question_data.get('engagement_level', 'Unknown')} | 
                        Asked: {question_data.get('asked_at', 'Unknown')}
                    </small>
                </li>
            """

        sequence_html += "</ol></div>"
        return format_html(sequence_html)

    questions_sequence_display.short_description = "Question Sequence"

    def flow_analysis_display(self, obj):
        """Display comprehensive flow analysis"""
        analysis_html = f"""
        <div style="background: #e8f4fd; padding: 10px; border-radius: 5px;">
            <h4 style="margin-top: 0;">Flow Analysis</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                <div>
                    <p><strong>Successful Transitions:</strong></p>
                    <ul>
                        {''.join([f'<li>{item}</li>' for item in obj.successful_transitions]) if obj.successful_transitions else '<li>No successful transitions recorded</li>'}
                    </ul>
                </div>
                <div>
                    <p><strong>Problematic Transitions:</strong></p>
                    <ul>
                        {''.join([f'<li>{item}</li>' for item in obj.problematic_transitions]) if obj.problematic_transitions else '<li>No problematic transitions identified</li>'}
                    </ul>
                </div>
            </div>
            <div style="margin-top: 10px;">
                <p><strong>Missed Opportunities:</strong></p>
                <ul>
                    {''.join([f'<li>{item}</li>' for item in obj.missed_opportunities]) if obj.missed_opportunities else '<li>No missed opportunities identified</li>'}
                </ul>
            </div>
        </div>
        """
        return format_html(analysis_html)

    flow_analysis_display.short_description = "Flow Analysis"
