from django.db import models
from django.conf import settings
import uuid


class ConversationAnalysis(models.Model):
    """Store conversation analysis results from Gemini AI"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    conversation_text = models.TextField()
    extracted_data = models.JSONField(default=dict)
    analysis_timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-analysis_timestamp']
    
    def __str__(self):
        return f"Analysis for {self.user.username} at {self.analysis_timestamp}"


class Lead(models.Model):
    """Lead model with company info, contact details, and AI-generated fields"""
    
    class Status(models.TextChoices):
        NEW = 'new', 'New'
        CONTACTED = 'contacted', 'Contacted'
        QUALIFIED = 'qualified', 'Qualified'
        CONVERTED = 'converted', 'Converted'
        LOST = 'lost', 'Lost'
    
    class UrgencyLevel(models.TextChoices):
        HIGH = 'high', 'High'
        MEDIUM = 'medium', 'Medium'
        LOW = 'low', 'Low'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leads')
    
    # Company Information
    company_name = models.CharField(max_length=255)
    industry = models.CharField(max_length=100, blank=True)
    company_size = models.CharField(max_length=100, blank=True)
    
    # Contact Information (stored as JSON for flexibility)
    contact_info = models.JSONField(default=dict, help_text="Contact details including name, email, phone, title, department")
    
    # Lead Status and Source
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    source = models.CharField(max_length=100, blank=True, help_text="How this lead was acquired")
    
    # Business Information
    pain_points = models.JSONField(default=list, help_text="List of business challenges mentioned")
    requirements = models.JSONField(default=list, help_text="List of specific needs or solutions requested")
    budget_info = models.TextField(blank=True, help_text="Budget range, constraints, or approval process")
    timeline = models.CharField(max_length=255, blank=True, help_text="Project timeline or urgency")
    decision_makers = models.JSONField(default=list, help_text="Names or roles of decision makers")
    
    # AI-Generated Fields
    urgency_level = models.CharField(max_length=10, choices=UrgencyLevel.choices, blank=True)
    current_solution = models.TextField(blank=True, help_text="Existing tools or solutions mentioned")
    competitors_mentioned = models.JSONField(default=list, help_text="Competitor names or alternatives discussed")
    
    # CRM Integration
    crm_record_id = models.CharField(max_length=255, blank=True, help_text="ID in external CRM system")
    crm_system = models.CharField(max_length=50, blank=True, help_text="Which CRM system this syncs with")
    
    # Conversation Context
    conversation_history = models.TextField(blank=True, help_text="Original conversation transcript")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['company_name']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.company_name} - {self.get_status_display()}"
    
    @property
    def contact_name(self):
        """Get primary contact name from contact_info"""
        return self.contact_info.get('name', '')
    
    @property
    def contact_email(self):
        """Get primary contact email from contact_info"""
        return self.contact_info.get('email', '')
    
    @property
    def contact_phone(self):
        """Get primary contact phone from contact_info"""
        return self.contact_info.get('phone', '')


class Opportunity(models.Model):
    """Opportunity model for tracking sales opportunities converted from leads"""
    
    class Stage(models.TextChoices):
        PROSPECTING = 'prospecting', 'Prospecting'
        QUALIFICATION = 'qualification', 'Qualification'
        PROPOSAL = 'proposal', 'Proposal'
        NEGOTIATION = 'negotiation', 'Negotiation'
        CLOSED_WON = 'closed_won', 'Closed Won'
        CLOSED_LOST = 'closed_lost', 'Closed Lost'
    
    class Priority(models.TextChoices):
        HIGH = 'high', 'High'
        MEDIUM = 'medium', 'Medium'
        LOW = 'low', 'Low'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='opportunities')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='opportunities')
    
    # Basic Opportunity Information
    name = models.CharField(max_length=255, help_text="Opportunity name/title")
    description = models.TextField(blank=True, help_text="Detailed opportunity description")
    
    # Financial Information
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2, help_text="Estimated deal value")
    probability = models.FloatField(help_text="Win probability percentage (0-100)")
    
    # Timeline Information
    expected_close_date = models.DateField(help_text="Expected close date")
    sales_cycle_days = models.IntegerField(null=True, blank=True, help_text="Predicted sales cycle in days")
    
    # Status and Stage
    stage = models.CharField(max_length=20, choices=Stage.choices, default=Stage.PROSPECTING)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    
    # CRM Integration
    crm_record_id = models.CharField(max_length=255, blank=True, help_text="ID in external CRM system")
    crm_system = models.CharField(max_length=50, blank=True, help_text="Which CRM system this syncs with")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'stage']),
            models.Index(fields=['expected_close_date']),
            models.Index(fields=['probability']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.get_stage_display()} ({self.probability}%)"
    
    @property
    def is_high_value(self):
        """Check if this is a high-value opportunity"""
        return self.estimated_value >= 50000  # Configurable threshold
    
    @property
    def days_to_close(self):
        """Calculate days until expected close"""
        from django.utils import timezone
        if self.expected_close_date:
            delta = self.expected_close_date - timezone.now().date()
            return delta.days
        return None


class OpportunityIntelligence(models.Model):
    """AI-powered opportunity conversion intelligence and predictions"""
    
    class ConversionLikelihood(models.TextChoices):
        VERY_HIGH = 'very_high', 'Very High (80-100%)'
        HIGH = 'high', 'High (60-79%)'
        MEDIUM = 'medium', 'Medium (40-59%)'
        LOW = 'low', 'Low (20-39%)'
        VERY_LOW = 'very_low', 'Very Low (0-19%)'
    
    class RiskLevel(models.TextChoices):
        HIGH = 'high', 'High Risk'
        MEDIUM = 'medium', 'Medium Risk'
        LOW = 'low', 'Low Risk'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    opportunity = models.OneToOneField(Opportunity, on_delete=models.CASCADE, related_name='intelligence')
    
    # Conversion Analysis
    conversion_probability = models.FloatField(help_text="AI-calculated conversion probability (0-100)")
    conversion_likelihood = models.CharField(max_length=15, choices=ConversionLikelihood.choices)
    conversion_confidence = models.FloatField(help_text="Confidence in conversion prediction (0-100)")
    
    # Deal Size and Timeline Predictions
    predicted_deal_size_min = models.DecimalField(max_digits=12, decimal_places=2, help_text="Minimum predicted deal size")
    predicted_deal_size_max = models.DecimalField(max_digits=12, decimal_places=2, help_text="Maximum predicted deal size")
    predicted_close_date = models.DateField(help_text="AI-predicted close date")
    sales_cycle_prediction_days = models.IntegerField(help_text="Predicted sales cycle duration in days")
    
    # Stage Recommendations
    recommended_stage = models.CharField(max_length=20, choices=Opportunity.Stage.choices, help_text="AI-recommended current stage")
    next_stage_probability = models.FloatField(help_text="Probability of advancing to next stage (0-100)")
    stage_advancement_timeline = models.CharField(max_length=100, help_text="Predicted timeline to advance stages")
    
    # Risk Analysis
    overall_risk_level = models.CharField(max_length=10, choices=RiskLevel.choices, default=RiskLevel.MEDIUM)
    risk_factors = models.JSONField(default=list, help_text="Identified risk factors")
    risk_mitigation_strategies = models.JSONField(default=list, help_text="Suggested risk mitigation strategies")
    
    # Competitive Analysis
    competitive_threats = models.JSONField(default=list, help_text="Identified competitive threats")
    competitive_advantages = models.JSONField(default=list, help_text="Our competitive advantages for this deal")
    win_strategy = models.TextField(blank=True, help_text="AI-recommended win strategy")
    
    # Historical Analysis
    similar_deals_count = models.IntegerField(default=0, help_text="Number of similar historical deals analyzed")
    historical_win_rate = models.FloatField(null=True, blank=True, help_text="Win rate for similar deals")
    benchmark_metrics = models.JSONField(default=dict, help_text="Benchmark metrics from similar deals")
    
    # Action Recommendations
    priority_actions = models.JSONField(default=list, help_text="High-priority recommended actions")
    next_best_actions = models.JSONField(default=list, help_text="Sequence of recommended next actions")
    resource_requirements = models.JSONField(default=list, help_text="Required resources and support")
    
    # Metadata
    last_analyzed = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Opportunity Intelligence"
        verbose_name_plural = "Opportunity Intelligence"
        ordering = ['-last_analyzed']
    
    def __str__(self):
        return f"Intelligence for {self.opportunity.name} ({self.conversion_probability}%)"
    
    @property
    def is_high_probability(self):
        """Check if this is a high-probability opportunity"""
        return self.conversion_probability >= 70
    
    @property
    def needs_attention(self):
        """Check if opportunity needs immediate attention"""
        return (self.overall_risk_level == self.RiskLevel.HIGH or 
                self.conversion_probability < 30 or
                len(self.risk_factors) > 3)


class AIInsights(models.Model):
    """Store AI analysis results and recommendations for leads"""
    
    class QualityTier(models.TextChoices):
        HIGH = 'high', 'High'
        MEDIUM = 'medium', 'Medium'
        LOW = 'low', 'Low'
    
    class CompetitiveRisk(models.TextChoices):
        HIGH = 'high', 'High'
        MEDIUM = 'medium', 'Medium'
        LOW = 'low', 'Low'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lead = models.OneToOneField(Lead, on_delete=models.CASCADE, related_name='ai_insights')
    
    # Lead Quality Scoring
    lead_score = models.FloatField(default=0.0, help_text="Overall lead quality score (0-100)")
    conversion_probability = models.FloatField(default=0.0, help_text="Probability of conversion (0-100)")
    quality_tier = models.CharField(max_length=10, choices=QualityTier.choices, default=QualityTier.MEDIUM)
    
    # Score Breakdown
    score_breakdown = models.JSONField(default=dict, help_text="Detailed scoring breakdown")
    
    # Deal Predictions
    estimated_deal_size = models.CharField(max_length=100, blank=True, help_text="Predicted deal value range")
    sales_cycle_prediction = models.CharField(max_length=100, blank=True, help_text="Expected sales cycle duration")
    
    # Opportunity Conversion Intelligence
    opportunity_conversion_score = models.FloatField(default=0.0, help_text="Lead-to-opportunity conversion score (0-100)")
    recommended_for_conversion = models.BooleanField(default=False, help_text="AI recommends converting to opportunity")
    conversion_readiness_factors = models.JSONField(default=list, help_text="Factors indicating conversion readiness")
    
    # Strategic Insights
    key_strengths = models.JSONField(default=list, help_text="Lead's key strengths")
    improvement_areas = models.JSONField(default=list, help_text="Areas needing more qualification")
    competitive_risk = models.CharField(max_length=10, choices=CompetitiveRisk.choices, default=CompetitiveRisk.MEDIUM)
    
    # Recommendations
    recommended_actions = models.JSONField(default=list, help_text="AI-generated action recommendations")
    next_steps = models.JSONField(default=list, help_text="Suggested next steps")
    next_best_action = models.TextField(blank=True, help_text="Top priority action")
    
    # Risk and Opportunity Analysis
    risk_factors = models.JSONField(default=list, help_text="Potential risks identified")
    opportunities = models.JSONField(default=list, help_text="Opportunities identified")
    
    # Sales Strategy
    primary_strategy = models.CharField(max_length=50, blank=True, help_text="Recommended sales approach")
    key_messaging = models.JSONField(default=list, help_text="Recommended messaging points")
    objection_handling = models.JSONField(default=dict, help_text="Objection handling strategies")
    
    # Industry Insights
    industry_insights = models.JSONField(default=dict, help_text="Industry-specific insights and trends")
    
    # Confidence and Metadata
    confidence_score = models.FloatField(default=0.0, help_text="Confidence in AI analysis (0-100)")
    data_completeness = models.FloatField(default=0.0, help_text="Completeness of lead data (0-100)")
    
    # Timestamps
    last_analyzed = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "AI Insights"
        verbose_name_plural = "AI Insights"
        ordering = ['-last_analyzed']
    
    def __str__(self):
        return f"AI Insights for {self.lead.company_name} (Score: {self.lead_score})"
    
    @property
    def is_high_quality(self):
        """Check if this is a high-quality lead"""
        return self.quality_tier == self.QualityTier.HIGH or self.lead_score >= 80
    
    @property
    def needs_immediate_attention(self):
        """Check if lead needs immediate attention"""
        return (self.lead.urgency_level == Lead.UrgencyLevel.HIGH or 
                self.conversion_probability >= 70 or 
                self.competitive_risk == self.CompetitiveRisk.HIGH)
    
    @property
    def should_convert_to_opportunity(self):
        """Check if lead should be converted to opportunity"""
        return (self.recommended_for_conversion and 
                self.opportunity_conversion_score >= 60 and
                self.conversion_probability >= 50)
