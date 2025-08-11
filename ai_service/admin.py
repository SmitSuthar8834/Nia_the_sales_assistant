import json

from django.contrib import admin
from django.utils.html import format_html

from .models import AIInsights, ConversationAnalysis, Lead


class MeetingInline(admin.TabularInline):
    """Inline admin for meetings related to a lead"""

    model = None  # Will be set dynamically
    extra = 0
    fields = [
        "title",
        "meeting_type",
        "scheduled_at",
        "status",
        "duration_minutes",
        "meeting_actions",
    ]
    readonly_fields = ["meeting_actions"]
    can_delete = False

    def meeting_actions(self, obj):
        """Display action buttons for meeting management"""
        if not obj.id:
            return "-"

        actions = []

        if obj.status == "scheduled":
            if obj.is_upcoming:
                actions.append(
                    f'<a href="/admin/meeting_service/meeting/{obj.id}/change/" class="button" style="background: #007cba; color: white; text-decoration: none; padding: 2px 6px; border-radius: 3px; font-size: 11px;">📝 Edit</a>'
                )
            actions.append(
                f'<button onclick="startMeeting(\'{obj.id}\');" class="button" style="background: #28a745; color: white; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 11px;">▶️ Start</button>'
            )
        elif obj.status == "in_progress":
            actions.append(
                f'<button onclick="completeMeeting(\'{obj.id}\');" class="button" style="background: #6c757d; color: white; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 11px;">✅ Complete</button>'
            )

        # Always show view button
        actions.append(
            f'<a href="/admin/meeting_service/meeting/{obj.id}/change/" target="_blank" class="button" style="background: #17a2b8; color: white; text-decoration: none; padding: 2px 6px; border-radius: 3px; font-size: 11px;">👁️ View</a>'
        )

        return format_html(" ".join(actions))

    meeting_actions.short_description = "Actions"


# Set the model dynamically to avoid circular import
try:
    from meeting_service.models import Meeting

    MeetingInline.model = Meeting
except ImportError:
    # If meeting_service is not available, create a dummy inline
    class MeetingInline(admin.TabularInline):
        model = None
        extra = 0

        def has_add_permission(self, request, obj=None):
            return False

        def has_change_permission(self, request, obj=None):
            return False


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    inlines = [MeetingInline]
    list_display = [
        "company_name",
        "contact_name",
        "contact_email",
        "industry",
        "status",
        "urgency_level",
        "conversation_snippet",
        "created_at",
        "lead_actions",
    ]
    list_filter = ["status", "industry", "urgency_level", "created_at"]
    search_fields = ["company_name", "industry", "source"]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "contact_info_display",
        "conversation_display",
        "meeting_scheduling_widget",
    ]

    fieldsets = (
        ("Basic Information", {"fields": ("company_name", "industry", "status")}),
        ("Contact Information", {"fields": ("contact_info", "contact_info_display")}),
        ("Lead Details", {"fields": ("source", "urgency_level")}),
        (
            "Meeting Management",
            {
                "fields": ("meeting_scheduling_widget",),
                "description": "Schedule and manage meetings for this lead",
            },
        ),
        (
            "Conversation",
            {
                "fields": ("conversation_history", "conversation_display"),
                "description": "Original conversation transcript and analysis",
            },
        ),
        (
            "Business Information",
            {
                "fields": ("pain_points", "requirements", "budget_info", "timeline"),
                "classes": ("collapse",),
            },
        ),
        (
            "Raw Data",
            {
                "fields": ("decision_makers", "competitors_mentioned"),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def contact_name(self, obj):
        return obj.contact_info.get("name", "N/A") if obj.contact_info else "N/A"

    contact_name.short_description = "Contact Name"
    contact_name.admin_order_field = "contact_info"

    def contact_email(self, obj):
        return obj.contact_info.get("email", "N/A") if obj.contact_info else "N/A"

    contact_email.short_description = "Email"

    def conversation_snippet(self, obj):
        if obj.conversation_history:
            snippet = obj.conversation_history[:50].replace("\n", " ")
            if len(obj.conversation_history) > 50:
                snippet += "..."
            return format_html(
                '<span title="{}" style="font-family: monospace; background: #f8f9fa; padding: 2px 4px; border-radius: 2px;">💬 {}</span>',
                obj.conversation_history[:200],
                snippet,
            )
        return format_html('<span style="color: #6c757d;">—</span>')

    conversation_snippet.short_description = "Conversation"

    def contact_info_display(self, obj):
        if obj.contact_info:
            info = obj.contact_info
            return format_html(
                "<p><strong>Name:</strong> {}</p>"
                "<p><strong>Email:</strong> {}</p>"
                "<p><strong>Phone:</strong> {}</p>",
                info.get("name", "N/A"),
                info.get("email", "N/A"),
                info.get("phone", "N/A"),
            )
        return "No contact information"

    contact_info_display.short_description = "Contact Information"

    def ai_insights_display(self, obj):
        try:
            if hasattr(obj, "ai_insights") and obj.ai_insights:
                formatted_json = json.dumps(
                    obj.ai_insights.__dict__, indent=2, default=str
                )
                return format_html(
                    '<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; max-height: 300px; overflow-y: auto;">{}</pre>',
                    formatted_json,
                )
        except:
            pass
        return "No AI insights available"

    ai_insights_display.short_description = "AI Insights"

    def conversation_display(self, obj):
        from django.template.loader import render_to_string

        context = {
            "conversation_text": obj.conversation_history,
            "lead_id": obj.id,
        }

        return format_html(render_to_string("admin/conversation_widget.html", context))

    conversation_display.short_description = "Conversation Management"

    def meeting_scheduling_widget(self, obj):
        """Display meeting scheduling widget with auto-populated data from lead"""
        if not obj.id:
            return "Save the lead first to schedule meetings"

        # Get existing meetings for this lead
        try:
            from meeting_service.models import Meeting

            meetings = Meeting.objects.filter(lead=obj).order_by("-scheduled_at")[:5]
        except ImportError:
            meetings = []

        # Auto-populate meeting data from lead information
        suggested_title = f"Meeting with {obj.company_name}"
        suggested_description = f"Discussion with {obj.contact_info.get('name', 'contact')} from {obj.company_name}"

        # Add pain points and requirements to description
        if obj.pain_points:
            suggested_description += f"\n\nPain Points: {', '.join(obj.pain_points)}"
        if obj.requirements:
            suggested_description += f"\nRequirements: {', '.join(obj.requirements)}"

        # Determine suggested meeting type based on lead status and AI insights
        suggested_meeting_type = "discovery"
        if obj.status == "qualified":
            suggested_meeting_type = "demo"
        elif obj.status == "converted":
            suggested_meeting_type = "proposal"

        # Get AI recommendations for meeting
        ai_recommendations = ""
        try:
            if hasattr(obj, "ai_insights") and obj.ai_insights:
                insights = obj.ai_insights
                if insights.next_best_action:
                    ai_recommendations = (
                        f"AI Recommendation: {insights.next_best_action}"
                    )
                if insights.recommended_actions:
                    ai_recommendations += f"\nSuggested Actions: {', '.join(insights.recommended_actions[:3])}"
        except:
            pass

        obj_id = str(obj.id)
        widget_html = """
        <div class="meeting-scheduling-widget" style="background: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6;">
            <h3 style="margin-top: 0; color: #007cba; display: flex; align-items: center;">
                📅 Meeting Scheduling
                <button onclick="scheduleMeeting('{obj_id}')" class="button" style="background: #007cba; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-left: auto; font-size: 14px;">
                    ➕ Schedule New Meeting
                </button>
            </h3>""".format(
            obj_id=obj_id
        )

        widget_html += """
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                <div>
                    <h4 style="color: #495057; margin-bottom: 10px;">📋 Auto-Populated Meeting Details</h4>
                    <div style="background: white; padding: 15px; border-radius: 4px; border: 1px solid #e9ecef;">
                        <p><strong>Suggested Title:</strong> {suggested_title}</p>
                        <p><strong>Meeting Type:</strong> <span style="background: #e3f2fd; padding: 2px 8px; border-radius: 12px; font-size: 12px;">{suggested_meeting_type}</span></p>
                        <p><strong>Contact:</strong> {contact_name} ({contact_email})</p>
                        <p><strong>Company:</strong> {company_name}</p>
                        <p><strong>Industry:</strong> {industry}</p>
                        <p><strong>Urgency:</strong> <span style="color: {urgency_color}; font-weight: bold;">{urgency_display}</span></p>
                    </div>
                </div>""".format(
            suggested_title=suggested_title,
            suggested_meeting_type=suggested_meeting_type.title(),
            contact_name=(
                obj.contact_info.get("name", "N/A") if obj.contact_info else "N/A"
            ),
            contact_email=(
                obj.contact_info.get("email", "N/A") if obj.contact_info else "N/A"
            ),
            company_name=obj.company_name,
            industry=obj.industry or "Not specified",
            urgency_color=(
                "#dc3545"
                if obj.urgency_level == "high"
                else "#ffc107" if obj.urgency_level == "medium" else "#28a745"
            ),
            urgency_display=(
                obj.get_urgency_level_display()
                if obj.urgency_level
                else "Not specified"
            ),
        )

        widget_html += """
                <div>
                    <h4 style="color: #495057; margin-bottom: 10px;">🤖 AI Meeting Recommendations</h4>
                    <div style="background: #e8f4fd; padding: 15px; border-radius: 4px; border: 1px solid #b3d9ff;">
                        {ai_recommendations_html}
                    </div>
                    
                    <h4 style="color: #495057; margin-bottom: 10px; margin-top: 15px;">💼 Business Context</h4>
                    <div style="background: white; padding: 15px; border-radius: 4px; border: 1px solid #e9ecef; font-size: 13px;">
                        <p><strong>Pain Points:</strong> {pain_points}</p>
                        <p><strong>Requirements:</strong> {requirements}</p>
                        <p><strong>Budget:</strong> {budget}</p>
                        <p><strong>Timeline:</strong> {timeline}</p>
                    </div>
                </div>
            </div>""".format(
            ai_recommendations_html=(
                '<p style="margin: 0; font-size: 13px; line-height: 1.4;">'
                + ai_recommendations
                + "</p>"
                if ai_recommendations
                else '<p style="margin: 0; color: #6c757d; font-style: italic;">No AI recommendations available</p>'
            ),
            pain_points=(
                ", ".join(obj.pain_points) if obj.pain_points else "None identified"
            ),
            requirements=(
                ", ".join(obj.requirements) if obj.requirements else "None specified"
            ),
            budget=obj.budget_info or "Not discussed",
            timeline=obj.timeline or "Not specified",
        )

        # Build meetings HTML
        meetings_html = ""
        if meetings:
            for meeting in meetings:
                status_color = (
                    "#28a745"
                    if meeting.status == "completed"
                    else (
                        "#007cba"
                        if meeting.status == "scheduled"
                        else "#ffc107" if meeting.status == "in_progress" else "#dc3545"
                    )
                )
                start_button = (
                    "<button onclick=\"startMeeting('"
                    + str(meeting.id)
                    + '\');" class="button" style="background: #28a745; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer; font-size: 11px;">▶️ Start</button>'
                    if meeting.status == "scheduled" and meeting.is_upcoming
                    else ""
                )
                complete_button = (
                    "<button onclick=\"completeMeeting('"
                    + str(meeting.id)
                    + '\');" class="button" style="background: #6c757d; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer; font-size: 11px;">✅ Complete</button>'
                    if meeting.status == "in_progress"
                    else ""
                )

                meetings_html += """
                    <div style="padding: 12px; border-bottom: 1px solid #f8f9fa; display: flex; justify-content: between; align-items: center;">
                        <div style="flex: 1;">
                            <strong>{title}</strong>
                            <span style="color: #6c757d; font-size: 12px; margin-left: 10px;">
                                {scheduled_time} | 
                                <span style="color: {status_color};">
                                    {status_display}
                                </span>
                            </span>
                        </div>
                        <div style="display: flex; gap: 5px;">
                            <a href="/admin/meeting_service/meeting/{meeting_id}/change/" target="_blank" class="button" style="background: #17a2b8; color: white; text-decoration: none; padding: 4px 8px; border-radius: 3px; font-size: 11px;">👁️ View</a>
                            {start_button}
                            {complete_button}
                        </div>
                    </div>
                """.format(
                    title=meeting.title,
                    scheduled_time=meeting.scheduled_at.strftime("%Y-%m-%d %H:%M"),
                    status_color=status_color,
                    status_display=meeting.get_status_display(),
                    meeting_id=meeting.id,
                    start_button=start_button,
                    complete_button=complete_button,
                )
        else:
            meetings_html = '<div style="padding: 20px; text-align: center; color: #6c757d; font-style: italic;">No meetings scheduled yet</div>'

        widget_html += """
            <div>
                <h4 style="color: #495057; margin-bottom: 10px;">📊 Recent Meetings</h4>
                <div style="background: white; border-radius: 4px; border: 1px solid #e9ecef;">
                    {meetings_html}
                </div>
            </div>""".format(
            meetings_html=meetings_html
        )

        widget_html += """
            <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #dee2e6;">
                <div style="display: flex; gap: 10px; justify-content: center;">
                    <button onclick="scheduleMeeting('{obj_id}')" class="button" style="background: #007cba; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-size: 14px;">
                        📅 Schedule New Meeting
                    </button>
                    <a href="/admin/meeting_service/meeting/?lead__id__exact={obj_id}" target="_blank" class="button" style="background: #28a745; color: white; text-decoration: none; padding: 10px 20px; border-radius: 4px; font-size: 14px;">
                        📋 View All Meetings
                    </a>
                    <button onclick="generateMeetingAgenda('{obj_id}')" class="button" style="background: #17a2b8; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-size: 14px;">
                        🤖 Generate AI Agenda
                    </button>
                </div>
            </div>
        </div>
        """.format(
            obj_id=obj_id
        )

        return format_html(widget_html)

    meeting_scheduling_widget.short_description = "Meeting Scheduling & Management"

    class Media:
        js = ("admin/js/meeting_actions.js", "admin/js/lead_meeting_actions.js")
        css = {
            "all": ("admin/css/meeting_admin.css", "admin/css/lead_meeting_widget.css")
        }

    def lead_actions(self, obj):
        actions = []

        # Quick Schedule Meeting - Primary action for list view
        actions.append(
            "<button onclick=\"quickScheduleMeeting('"
            + str(obj.id)
            + "', '"
            + str(obj.company_name)
            + '\');" class="button" style="background: #007cba; color: white; border: none; padding: 5px 8px; border-radius: 3px; cursor: pointer; margin-right: 3px; font-size: 11px;" title="Quick schedule meeting">⚡📅</button>'
        )

        # Detailed Schedule Meeting
        actions.append(
            "<button onclick=\"scheduleMeeting('"
            + str(obj.id)
            + '\');" class="button" style="background: #0056b3; color: white; border: none; padding: 5px 8px; border-radius: 3px; cursor: pointer; margin-right: 3px; font-size: 11px;" title="Schedule meeting with details">📅</button>'
        )

        # Analyze with AI
        actions.append(
            f'<a href="/admin-config/ai-dashboard/?lead_id={obj.id}" class="button" style="background: #0073aa; color: white; padding: 5px 8px; text-decoration: none; border-radius: 3px; margin-right: 3px; font-size: 11px;" title="AI Analysis">🧠</a>'
        )

        # Re-analyze conversation if exists
        if obj.conversation_history:
            actions.append(
                f'<a href="/admin-config/ai-dashboard/?conversation_text={obj.conversation_history[:100]}" class="button" style="background: #17a2b8; color: white; padding: 5px 8px; text-decoration: none; border-radius: 3px; margin-right: 3px; font-size: 11px;" title="Re-analyze conversation">🔄</a>'
            )

        # View details
        actions.append(
            f'<a href="/admin/ai_service/lead/{obj.id}/change/" class="button" style="background: #28a745; color: white; padding: 5px 8px; text-decoration: none; border-radius: 3px; font-size: 11px;" title="View details">📋</a>'
        )

        return format_html("".join(actions))

    lead_actions.short_description = "Actions"
    lead_actions.allow_tags = True


@admin.register(ConversationAnalysis)
class ConversationAnalysisAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "conversation_snippet",
        "analysis_timestamp",
        "analysis_actions",
    ]
    list_filter = ["analysis_timestamp", "user"]
    search_fields = ["conversation_text", "user__username"]
    readonly_fields = ["id", "analysis_timestamp", "extracted_data_display"]

    fieldsets = (
        ("Basic Information", {"fields": ("user", "analysis_timestamp")}),
        ("Conversation", {"fields": ("conversation_text",)}),
        (
            "Analysis Results",
            {
                "fields": ("extracted_data_display",),
            },
        ),
        ("Raw Data", {"fields": ("extracted_data",), "classes": ("collapse",)}),
        ("Metadata", {"fields": ("id",), "classes": ("collapse",)}),
    )

    def conversation_snippet(self, obj):
        if obj.conversation_text:
            return (
                obj.conversation_text[:100] + "..."
                if len(obj.conversation_text) > 100
                else obj.conversation_text
            )
        return "No conversation text"

    conversation_snippet.short_description = "Conversation"

    def extracted_data_display(self, obj):
        if obj.extracted_data:
            formatted_json = json.dumps(obj.extracted_data, indent=2)
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; max-height: 200px; overflow-y: auto;">{}</pre>',
                formatted_json,
            )
        return "No extracted data"

    extracted_data_display.short_description = "Extracted Data"

    def analysis_actions(self, obj):
        actions = []

        # Re-analyze
        actions.append(
            f'<a href="/admin-config/ai-dashboard/?conversation_id={obj.id}" class="button" style="background: #0073aa; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">🔄 Re-analyze</a>'
        )

        # Create lead from analysis
        if obj.extracted_data:
            actions.append(
                f'<a href="/admin-config/ai/create-lead/?analysis_id={obj.id}" class="button" style="background: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">📋 Create Lead</a>'
            )

        return format_html("".join(actions))

    analysis_actions.short_description = "Actions"
    analysis_actions.allow_tags = True


@admin.register(AIInsights)
class AIInsightsAdmin(admin.ModelAdmin):
    list_display = [
        "lead",
        "quality_tier",
        "lead_score",
        "conversion_probability",
        "created_at",
        "insights_actions",
    ]
    list_filter = [
        "quality_tier",
        "competitive_risk",
        "created_at",
        "recommended_for_conversion",
    ]
    search_fields = ["lead__company_name", "primary_strategy"]
    readonly_fields = ["id", "created_at", "last_analyzed", "score_breakdown_display"]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "lead",
                    "quality_tier",
                    "lead_score",
                    "conversion_probability",
                )
            },
        ),
        (
            "Scoring Details",
            {
                "fields": (
                    "score_breakdown_display",
                    "confidence_score",
                    "data_completeness",
                )
            },
        ),
        (
            "Recommendations",
            {
                "fields": ("recommended_actions", "next_steps", "next_best_action"),
                "classes": ("collapse",),
            },
        ),
        (
            "Strategy",
            {
                "fields": ("primary_strategy", "key_messaging", "competitive_risk"),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {"fields": ("id", "created_at", "last_analyzed"), "classes": ("collapse",)},
        ),
    )

    def score_breakdown_display(self, obj):
        if obj.score_breakdown:
            formatted_json = json.dumps(obj.score_breakdown, indent=2)
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; max-height: 300px; overflow-y: auto;">{}</pre>',
                formatted_json,
            )
        return "No score breakdown available"

    score_breakdown_display.short_description = "Score Breakdown"

    def insights_actions(self, obj):
        actions = []

        # View lead
        actions.append(
            f'<a href="/admin/ai_service/lead/{obj.lead.id}/change/" class="button" style="background: #0073aa; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">📋 View Lead</a>'
        )

        # Refresh insights
        actions.append(
            f'<a href="/admin-config/ai/refresh-insights/?insight_id={obj.id}" class="button" style="background: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">🔄 Refresh</a>'
        )

        return format_html("".join(actions))

    insights_actions.short_description = "Actions"
    insights_actions.allow_tags = True
