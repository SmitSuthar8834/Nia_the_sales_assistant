"""
AI Configuration Settings for Sales Recommendations Engine

This file contains configurable settings that can be easily modified
to customize the AI's behavior and recommendations.
"""

# Company-specific configuration
COMPANY_CONFIG = {
    "name": "NIA (Next Intelligence Assistant)",
    "industry": "AI-powered Sales Technology",
    "target_market": "B2B companies looking to improve sales efficiency",
    "value_proposition": "AI-driven sales assistance and lead management",
    # These can be customized based on your actual competitive advantages
    "competitive_advantages": [
        "Advanced AI conversation analysis",
        "Real-time voice processing",
        "Intelligent lead scoring",
        "Industry-specific insights",
        "Automated workflow recommendations",
    ],
    # Typical deal characteristics
    "typical_deal_size_range": "$25,000 - $250,000",
    "average_sales_cycle": "3-6 months",
    "target_company_size": "50-500 employees",
}

# Sales methodology configuration
SALES_METHODOLOGY_CONFIG = {
    "primary_approach": "Consultative Selling",
    "qualification_framework": "BANT (Budget, Authority, Need, Timeline)",
    # Customize these based on your sales process
    "sales_stages": [
        "Prospecting",
        "Initial Contact",
        "Discovery",
        "Presentation/Demo",
        "Proposal",
        "Negotiation",
        "Closing",
        "Implementation",
    ],
    # Key qualification questions
    "qualification_criteria": [
        "Budget availability and approval process",
        "Decision-making authority identification",
        "Pain points and business needs assessment",
        "Implementation timeline and urgency",
    ],
}

# AI behavior configuration
AI_BEHAVIOR_CONFIG = {
    "tone": "professional_consultative",  # Options: professional_consultative, friendly_expert, authoritative
    "confidence_threshold": 70,  # Minimum confidence score for high-confidence recommendations
    "recommendation_count": 5,  # Default number of recommendations to generate
    "priority_focus": "impact_over_effort",  # Options: impact_over_effort, quick_wins, relationship_building
    # Response style preferences
    "include_reasoning": True,  # Include rationale for recommendations
    "include_metrics": True,  # Include success metrics
    "include_risks": True,  # Include risk factors
    "personalization_level": "high",  # Options: low, medium, high
}

# Industry-specific customization
INDUSTRY_CUSTOMIZATION = {
    "technology": {
        "emphasis": "technical_capabilities",
        "key_stakeholders": ["CTO", "VP Engineering", "Head of Product"],
        "common_objections": [
            "integration_complexity",
            "technical_debt",
            "resource_allocation",
        ],
        "success_metrics": [
            "developer_productivity",
            "system_performance",
            "integration_speed",
        ],
    },
    "financial_services": {
        "emphasis": "compliance_and_roi",
        "key_stakeholders": ["CFO", "CRO", "Head of Operations", "Compliance Officer"],
        "common_objections": [
            "regulatory_concerns",
            "security_requirements",
            "change_management",
        ],
        "success_metrics": [
            "compliance_score",
            "operational_efficiency",
            "risk_reduction",
        ],
    },
    "healthcare": {
        "emphasis": "patient_outcomes",
        "key_stakeholders": ["CMO", "CIO", "Administrator", "Department Head"],
        "common_objections": [
            "hipaa_compliance",
            "workflow_disruption",
            "training_requirements",
        ],
        "success_metrics": [
            "patient_satisfaction",
            "workflow_efficiency",
            "compliance_adherence",
        ],
    },
}

# Scoring and confidence configuration
SCORING_CONFIG = {
    "lead_quality_weights": {
        "data_completeness": 0.20,
        "engagement_level": 0.15,
        "budget_fit": 0.20,
        "timeline_urgency": 0.15,
        "decision_authority": 0.15,
        "pain_point_severity": 0.15,
    },
    "confidence_thresholds": {"high": 80, "medium": 60, "low": 40},
    "quality_tiers": {
        "high": {"min_score": 75, "conversion_probability": 65},
        "medium": {"min_score": 50, "conversion_probability": 35},
        "low": {"min_score": 0, "conversion_probability": 15},
    },
}

# Recommendation templates
RECOMMENDATION_TEMPLATES = {
    "immediate_actions": [
        "Schedule follow-up call within 24-48 hours",
        "Send personalized follow-up email with relevant resources",
        "Connect on LinkedIn with personalized message",
        "Share relevant case study or white paper",
        "Schedule product demonstration",
    ],
    "short_term_actions": [
        "Conduct comprehensive needs assessment",
        "Prepare customized proposal or quote",
        "Arrange stakeholder introductions",
        "Provide trial or pilot access",
        "Schedule technical deep-dive session",
    ],
    "long_term_actions": [
        "Develop implementation roadmap",
        "Prepare contract negotiations",
        "Plan change management strategy",
        "Design training and onboarding program",
        "Establish success metrics and KPIs",
    ],
}

# Customizable prompt modifiers
PROMPT_MODIFIERS = {
    "industry_focus": True,  # Include industry-specific context
    "company_size_focus": True,  # Adjust recommendations based on company size
    "urgency_awareness": True,  # Factor in timeline urgency
    "competitive_context": True,  # Include competitive positioning
    "roi_emphasis": True,  # Emphasize return on investment
    "risk_mitigation": True,  # Include risk factors and mitigation
}

# Integration settings
INTEGRATION_CONFIG = {
    "crm_sync": False,  # Enable CRM synchronization
    "email_automation": False,  # Enable automated email follow-ups
    "calendar_integration": False,  # Enable calendar scheduling
    "reporting_dashboard": True,  # Enable recommendation analytics
    # External service configurations
    "external_apis": {
        "company_data": None,  # Company enrichment API
        "industry_insights": None,  # Industry data API
        "competitive_intel": None,  # Competitive intelligence API
    },
}


def get_company_config():
    """Get company-specific configuration"""
    return COMPANY_CONFIG


def get_sales_methodology():
    """Get sales methodology configuration"""
    return SALES_METHODOLOGY_CONFIG


def get_ai_behavior_config():
    """Get AI behavior configuration"""
    return AI_BEHAVIOR_CONFIG


def get_industry_config(industry: str):
    """Get industry-specific configuration"""
    industry_key = industry.lower().replace(" ", "_").replace("-", "_")
    return INDUSTRY_CUSTOMIZATION.get(
        industry_key, INDUSTRY_CUSTOMIZATION["technology"]
    )


def get_scoring_config():
    """Get scoring and confidence configuration"""
    return SCORING_CONFIG


def get_recommendation_templates():
    """Get recommendation templates"""
    return RECOMMENDATION_TEMPLATES


def update_company_config(new_config: dict):
    """Update company configuration (for admin use)"""
    global COMPANY_CONFIG
    COMPANY_CONFIG.update(new_config)


def update_ai_behavior(new_behavior: dict):
    """Update AI behavior configuration (for admin use)"""
    global AI_BEHAVIOR_CONFIG
    AI_BEHAVIOR_CONFIG.update(new_behavior)


# Configuration validation
def validate_config():
    """Validate configuration settings"""
    errors = []

    # Validate required company fields
    required_company_fields = ["name", "industry", "target_market", "value_proposition"]
    for field in required_company_fields:
        if not COMPANY_CONFIG.get(field):
            errors.append(f"Missing required company config field: {field}")

    # Validate scoring weights sum to 1.0
    weights_sum = sum(SCORING_CONFIG["lead_quality_weights"].values())
    if abs(weights_sum - 1.0) > 0.01:
        errors.append(f"Lead quality weights sum to {weights_sum}, should be 1.0")

    # Validate confidence thresholds
    thresholds = SCORING_CONFIG["confidence_thresholds"]
    if not (thresholds["low"] < thresholds["medium"] < thresholds["high"]):
        errors.append("Confidence thresholds should be in ascending order")

    return errors


# Initialize and validate configuration on import
_config_errors = validate_config()
if _config_errors:
    import warnings

    for error in _config_errors:
        warnings.warn(f"AI Configuration Error: {error}")
