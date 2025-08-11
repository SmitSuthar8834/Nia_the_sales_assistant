import uuid

from django.conf import settings
from django.db import models


class ConversationAnalysis(models.Model):
    """Store conversation analysis results from Gemini AI"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    conversation_text = models.TextField()
    extracted_data = models.JSONField(default=dict)
    analysis_timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-analysis_timestamp"]

    def __str__(self):
        return f"Analysis for {self.user.username} at {self.analysis_timestamp}"


class Lead(models.Model):
    """Lead model with company info, contact details, and AI-generated fields"""

    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        QUALIFIED = "qualified", "Qualified"
        CONVERTED = "converted", "Converted"
        LOST = "lost", "Lost"

    class UrgencyLevel(models.TextChoices):
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="leads"
    )

    # Company Information
    company_name = models.CharField(max_length=255)
    industry = models.CharField(max_length=100, blank=True)
    company_size = models.CharField(max_length=100, blank=True)

    # Contact Information (stored as JSON for flexibility)
    contact_info = models.JSONField(
        default=dict,
        help_text="Contact details including name, email, phone, title, department",
    )

    # Lead Status and Source
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    source = models.CharField(
        max_length=100, blank=True, help_text="How this lead was acquired"
    )

    # Business Information
    pain_points = models.JSONField(
        default=list, help_text="List of business challenges mentioned"
    )
    requirements = models.JSONField(
        default=list, help_text="List of specific needs or solutions requested"
    )
    budget_info = models.TextField(
        blank=True, help_text="Budget range, constraints, or approval process"
    )
    timeline = models.CharField(
        max_length=255, blank=True, help_text="Project timeline or urgency"
    )
    decision_makers = models.JSONField(
        default=list, help_text="Names or roles of decision makers"
    )

    # AI-Generated Fields
    urgency_level = models.CharField(
        max_length=10, choices=UrgencyLevel.choices, blank=True
    )
    current_solution = models.TextField(
        blank=True, help_text="Existing tools or solutions mentioned"
    )
    competitors_mentioned = models.JSONField(
        default=list, help_text="Competitor names or alternatives discussed"
    )

    # CRM Integration
    crm_record_id = models.CharField(
        max_length=255, blank=True, help_text="ID in external CRM system"
    )
    crm_system = models.CharField(
        max_length=50, blank=True, help_text="Which CRM system this syncs with"
    )

    # Conversation Context
    conversation_history = models.TextField(
        blank=True, help_text="Original conversation transcript"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["company_name"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.company_name} - {self.get_status_display()}"

    @property
    def contact_name(self):
        """Get primary contact name from contact_info"""
        return self.contact_info.get("name", "")

    @property
    def contact_email(self):
        """Get primary contact email from contact_info"""
        return self.contact_info.get("email", "")

    @property
    def contact_phone(self):
        """Get primary contact phone from contact_info"""
        return self.contact_info.get("phone", "")


# Opportunity models removed - not currently used in the application
# These were complex models that added unnecessary complexity
# If needed in the future, they can be re-added with a simpler design

# class Opportunity(models.Model):
# These models were removed to simplify the codebase
# They added unnecessary complexity and weren't being used in the application


class AIInsights(models.Model):
    """Store AI analysis results and recommendations for leads"""

    class QualityTier(models.TextChoices):
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

    class CompetitiveRisk(models.TextChoices):
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lead = models.OneToOneField(
        Lead, on_delete=models.CASCADE, related_name="ai_insights"
    )

    # Lead Quality Scoring
    lead_score = models.FloatField(
        default=0.0, help_text="Overall lead quality score (0-100)"
    )
    conversion_probability = models.FloatField(
        default=0.0, help_text="Probability of conversion (0-100)"
    )
    quality_tier = models.CharField(
        max_length=10, choices=QualityTier.choices, default=QualityTier.MEDIUM
    )

    # Score Breakdown
    score_breakdown = models.JSONField(
        default=dict, help_text="Detailed scoring breakdown"
    )

    # Deal Predictions
    estimated_deal_size = models.CharField(
        max_length=100, blank=True, help_text="Predicted deal value range"
    )
    sales_cycle_prediction = models.CharField(
        max_length=100, blank=True, help_text="Expected sales cycle duration"
    )

    # Opportunity Conversion Intelligence
    opportunity_conversion_score = models.FloatField(
        default=0.0, help_text="Lead-to-opportunity conversion score (0-100)"
    )
    recommended_for_conversion = models.BooleanField(
        default=False, help_text="AI recommends converting to opportunity"
    )
    conversion_readiness_factors = models.JSONField(
        default=list, help_text="Factors indicating conversion readiness"
    )

    # Strategic Insights
    key_strengths = models.JSONField(default=list, help_text="Lead's key strengths")
    improvement_areas = models.JSONField(
        default=list, help_text="Areas needing more qualification"
    )
    competitive_risk = models.CharField(
        max_length=10, choices=CompetitiveRisk.choices, default=CompetitiveRisk.MEDIUM
    )

    # Recommendations
    recommended_actions = models.JSONField(
        default=list, help_text="AI-generated action recommendations"
    )
    next_steps = models.JSONField(default=list, help_text="Suggested next steps")
    next_best_action = models.TextField(blank=True, help_text="Top priority action")

    # Risk and Opportunity Analysis
    risk_factors = models.JSONField(
        default=list, help_text="Potential risks identified"
    )
    opportunities = models.JSONField(default=list, help_text="Opportunities identified")

    # Sales Strategy
    primary_strategy = models.CharField(
        max_length=50, blank=True, help_text="Recommended sales approach"
    )
    key_messaging = models.JSONField(
        default=list, help_text="Recommended messaging points"
    )
    objection_handling = models.JSONField(
        default=dict, help_text="Objection handling strategies"
    )

    # Industry Insights
    industry_insights = models.JSONField(
        default=dict, help_text="Industry-specific insights and trends"
    )

    # Confidence and Metadata
    confidence_score = models.FloatField(
        default=0.0, help_text="Confidence in AI analysis (0-100)"
    )
    data_completeness = models.FloatField(
        default=0.0, help_text="Completeness of lead data (0-100)"
    )

    # Timestamps
    last_analyzed = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "AI Insights"
        verbose_name_plural = "AI Insights"
        ordering = ["-last_analyzed"]

    def __str__(self):
        return f"AI Insights for {self.lead.company_name} (Score: {self.lead_score})"

    @property
    def is_high_quality(self):
        """Check if this is a high-quality lead"""
        return self.quality_tier == self.QualityTier.HIGH or self.lead_score >= 80

    @property
    def needs_immediate_attention(self):
        """Check if lead needs immediate attention"""
        return (
            self.lead.urgency_level == Lead.UrgencyLevel.HIGH
            or self.conversion_probability >= 70
            or self.competitive_risk == self.CompetitiveRisk.HIGH
        )

    @property
    def should_convert_to_opportunity(self):
        """Check if lead should be converted to opportunity"""
        return (
            self.recommended_for_conversion
            and self.opportunity_conversion_score >= 60
            and self.conversion_probability >= 50
        )
