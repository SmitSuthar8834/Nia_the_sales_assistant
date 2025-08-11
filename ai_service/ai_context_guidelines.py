"""
AI Context Guidelines for Sales Recommendations Engine

This module contains context and guidelines that help the AI provide consistent,
high-quality sales recommendations across all functions.
"""

# Sales methodology and best practices context
SALES_CONTEXT = {
    "company_profile": {
        "name": "NIA (Next Intelligence Assistant)",
        "industry": "AI-powered Sales Technology",
        "target_market": "B2B companies looking to improve sales efficiency",
        "value_proposition": "AI-driven sales assistance and lead management",
        "competitive_advantages": [
            "Advanced AI conversation analysis",
            "Real-time voice processing",
            "Intelligent lead scoring",
            "Industry-specific insights",
            "Automated workflow recommendations",
        ],
    },
    "sales_methodology": {
        "primary_approach": "Consultative Selling",
        "framework": "BANT (Budget, Authority, Need, Timeline)",
        "qualification_criteria": [
            "Budget availability and approval process",
            "Decision-making authority identification",
            "Pain points and business needs assessment",
            "Implementation timeline and urgency",
        ],
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
    },
    "lead_scoring_criteria": {
        "high_value_indicators": [
            "Clear budget allocation ($50K+)",
            "Urgent timeline (within 6 months)",
            "Multiple pain points identified",
            "Decision maker directly involved",
            "Previous solution evaluation experience",
            "Growing company (50+ employees)",
            "Technology-forward industry",
        ],
        "medium_value_indicators": [
            "Budget range mentioned but not confirmed",
            "Timeline within 12 months",
            "Some pain points identified",
            "Influencer involved in process",
            "Stable company size",
            "Traditional industry with digital initiatives",
        ],
        "low_value_indicators": [
            "No budget mentioned or very limited",
            "No specific timeline",
            "Vague or minimal pain points",
            "No decision-making authority",
            "Very small company (<10 employees)",
            "Highly regulated or slow-moving industry",
        ],
    },
    "industry_insights": {
        "technology": {
            "common_pain_points": [
                "Technical debt management",
                "Integration complexity",
                "Scalability challenges",
                "Developer productivity",
                "Security concerns",
            ],
            "decision_makers": ["CTO", "VP Engineering", "Head of Product"],
            "sales_approach": "Technical demonstration with deep-dive capabilities",
            "typical_sales_cycle": "3-6 months",
            "key_messaging": [
                "Technical superiority and innovation",
                "Integration ease and API capabilities",
                "Scalability and performance",
                "Developer experience and productivity",
            ],
        },
        "financial_services": {
            "common_pain_points": [
                "Regulatory compliance",
                "Data security and privacy",
                "Legacy system integration",
                "Customer experience improvement",
                "Operational efficiency",
            ],
            "decision_makers": [
                "CFO",
                "CRO",
                "Head of Operations",
                "Compliance Officer",
            ],
            "sales_approach": "Compliance-focused with ROI emphasis",
            "typical_sales_cycle": "6-12 months",
            "key_messaging": [
                "Regulatory compliance and security",
                "Risk mitigation and audit trails",
                "ROI and cost reduction",
                "Customer satisfaction improvement",
            ],
        },
        "healthcare": {
            "common_pain_points": [
                "Patient data management",
                "Workflow efficiency",
                "Compliance with HIPAA/regulations",
                "Cost reduction pressures",
                "Staff productivity",
            ],
            "decision_makers": ["CMO", "CIO", "Administrator", "Department Head"],
            "sales_approach": "Outcome-focused with compliance emphasis",
            "typical_sales_cycle": "6-18 months",
            "key_messaging": [
                "Patient outcome improvement",
                "Compliance and security",
                "Workflow optimization",
                "Cost reduction and efficiency",
            ],
        },
        "manufacturing": {
            "common_pain_points": [
                "Supply chain optimization",
                "Quality control",
                "Operational efficiency",
                "Predictive maintenance",
                "Inventory management",
            ],
            "decision_makers": [
                "COO",
                "Plant Manager",
                "VP Operations",
                "Quality Manager",
            ],
            "sales_approach": "Efficiency and cost-savings focused",
            "typical_sales_cycle": "4-8 months",
            "key_messaging": [
                "Operational efficiency gains",
                "Cost reduction and waste elimination",
                "Quality improvement",
                "Predictive capabilities",
            ],
        },
        "retail": {
            "common_pain_points": [
                "Customer experience",
                "Inventory optimization",
                "Sales forecasting",
                "Omnichannel integration",
                "Competitive pricing",
            ],
            "decision_makers": ["CMO", "VP Sales", "Merchandising Manager", "CTO"],
            "sales_approach": "Customer experience and revenue growth focused",
            "typical_sales_cycle": "3-6 months",
            "key_messaging": [
                "Customer experience enhancement",
                "Revenue growth and conversion",
                "Inventory optimization",
                "Competitive advantage",
            ],
        },
    },
    "objection_handling": {
        "budget_concerns": {
            "strategies": [
                "Focus on ROI and payback period",
                "Break down costs vs. current inefficiencies",
                "Offer phased implementation approach",
                "Provide financing or payment options",
                "Show competitive cost analysis",
            ],
            "responses": [
                "Let's look at the cost of not solving this problem",
                "What's the current cost of your existing process?",
                "We can structure this to fit your budget cycle",
                "Many clients see ROI within the first quarter",
            ],
        },
        "timing_concerns": {
            "strategies": [
                "Identify urgency drivers",
                "Show cost of delay",
                "Offer pilot or proof of concept",
                "Align with business cycles",
                "Create compelling events",
            ],
            "responses": [
                "What happens if you wait another year?",
                "We can start with a pilot to prove value",
                "When does your current contract expire?",
                "What's driving the need for change now?",
            ],
        },
        "authority_concerns": {
            "strategies": [
                "Identify all stakeholders",
                "Map decision-making process",
                "Provide materials for internal selling",
                "Offer to present to decision makers",
                "Build champion relationships",
            ],
            "responses": [
                "Who else would be involved in this decision?",
                "What information would help you make the case internally?",
                "I'd be happy to present to your team",
                "What's your typical approval process?",
            ],
        },
        "competition_concerns": {
            "strategies": [
                "Focus on unique differentiators",
                "Understand competitor weaknesses",
                "Provide comparison materials",
                "Emphasize total value proposition",
                "Share relevant case studies",
            ],
            "responses": [
                "What specific capabilities are most important to you?",
                "How are you evaluating the different options?",
                "Let me show you what makes us different",
                "What concerns do you have about other solutions?",
            ],
        },
    },
    "recommendation_guidelines": {
        "next_steps": {
            "immediate_actions": [
                "Schedule follow-up call/meeting",
                "Send relevant case studies or materials",
                "Provide technical documentation",
                "Arrange product demonstration",
                "Connect with reference customers",
            ],
            "short_term_actions": [
                "Conduct needs assessment",
                "Prepare custom proposal",
                "Arrange stakeholder meetings",
                "Provide pilot or trial access",
                "Schedule technical deep-dive",
            ],
            "long_term_actions": [
                "Develop implementation timeline",
                "Prepare contract negotiations",
                "Plan change management",
                "Design training program",
                "Establish success metrics",
            ],
        },
        "priority_matrix": {
            "high_priority": [
                "Decision maker engagement",
                "Budget confirmation",
                "Timeline validation",
                "Technical fit verification",
                "Competitive differentiation",
            ],
            "medium_priority": [
                "Stakeholder mapping",
                "Use case development",
                "ROI calculation",
                "Reference sharing",
                "Pilot planning",
            ],
            "low_priority": [
                "General relationship building",
                "Industry networking",
                "Long-term nurturing",
                "Educational content sharing",
                "Market research sharing",
            ],
        },
    },
    "confidence_scoring_rules": {
        "high_confidence_indicators": [
            "Complete lead data (8+ fields filled)",
            "Direct decision maker contact",
            "Specific budget range provided",
            "Urgent timeline (< 6 months)",
            "Multiple pain points identified",
            "Previous solution experience",
            "Industry match with our strengths",
        ],
        "medium_confidence_indicators": [
            "Moderate lead data (5-7 fields filled)",
            "Influencer or champion identified",
            "Budget range discussed",
            "Timeline within 12 months",
            "Some pain points identified",
            "General industry fit",
        ],
        "low_confidence_indicators": [
            "Limited lead data (< 5 fields filled)",
            "No clear contact authority",
            "No budget information",
            "No specific timeline",
            "Vague or no pain points",
            "Poor industry fit",
        ],
    },
}

# AI behavior guidelines
AI_GUIDELINES = {
    "tone_and_style": {
        "professional": "Maintain professional, consultative tone",
        "confident": "Provide confident recommendations based on data",
        "helpful": "Focus on actionable, practical advice",
        "specific": "Give specific, measurable recommendations",
        "empathetic": "Understand and acknowledge customer challenges",
    },
    "recommendation_principles": {
        "data_driven": "Base recommendations on available lead data",
        "prioritized": "Rank recommendations by impact and urgency",
        "actionable": "Provide clear, executable next steps",
        "measurable": "Include success metrics where possible",
        "realistic": "Consider resource constraints and timelines",
        "personalized": "Tailor to specific industry and company size",
    },
    "quality_standards": {
        "accuracy": "Ensure recommendations align with lead characteristics",
        "relevance": "Focus on industry-specific and role-appropriate advice",
        "completeness": "Provide comprehensive analysis when data allows",
        "consistency": "Maintain consistent scoring and recommendation logic",
        "transparency": "Explain reasoning behind recommendations",
    },
    "error_handling": {
        "missing_data": "Acknowledge limitations and suggest data gathering",
        "low_confidence": "Provide general best practices with caveats",
        "conflicting_data": "Highlight inconsistencies and seek clarification",
        "edge_cases": "Provide conservative recommendations with explanations",
    },
}

# Prompt templates for consistent AI responses
PROMPT_TEMPLATES = {
    "lead_quality_score": """
    You are an expert sales analyst. Analyze this lead and provide a comprehensive quality assessment.
    
    Consider these factors in your analysis:
    - Data completeness and quality
    - Budget indicators and financial capacity
    - Timeline urgency and decision-making authority
    - Pain point severity and solution fit
    - Industry characteristics and competitive landscape
    - Company size and growth indicators
    
    Use the following scoring guidelines:
    - 80-100: High-quality lead with strong conversion potential
    - 60-79: Medium-quality lead requiring nurturing
    - 40-59: Low-quality lead needing significant qualification
    - 0-39: Poor-quality lead with minimal potential
    
    Provide specific, actionable insights based on the available data.
    """,
    "sales_strategy": """
    You are an expert sales strategist. Create a tailored sales approach for this lead.
    
    Consider these strategic elements:
    - Lead characteristics and decision-making style
    - Industry-specific sales approaches and best practices
    - Competitive landscape and differentiation opportunities
    - Stakeholder mapping and influence patterns
    - Objection handling and risk mitigation
    
    Recommend one of these primary strategies:
    - Consultative: Focus on discovery and problem-solving
    - Solution: Emphasize product capabilities and features
    - Relationship: Build trust and long-term partnership
    - Competitive: Differentiate against specific competitors
    
    Provide specific tactics and messaging for the recommended approach.
    """,
    "industry_insights": """
    You are an industry expert and sales consultant. Provide industry-specific insights and best practices.
    
    Focus on these areas:
    - Current industry trends and market dynamics
    - Common pain points and business challenges
    - Typical decision-making processes and stakeholders
    - Competitive landscape and vendor evaluation criteria
    - Regulatory or compliance considerations
    - Success patterns and case study examples
    
    Tailor your insights to the specific industry and company size.
    Provide actionable advice that can be immediately applied.
    """,
    "recommendations": """
    You are an expert sales advisor. Generate comprehensive, actionable recommendations.
    
    Provide recommendations across these categories:
    - Immediate next steps (within 1-3 days)
    - Short-term actions (within 1-2 weeks)
    - Medium-term strategy (within 1 month)
    - Long-term relationship building
    
    For each recommendation, include:
    - Specific action to take
    - Priority level and timeline
    - Expected outcome and success metrics
    - Resource requirements and effort level
    
    Prioritize recommendations based on impact and feasibility.
    """,
}


def get_context_for_industry(industry: str) -> dict:
    """Get industry-specific context and guidelines"""
    industry_key = industry.lower().replace(" ", "_").replace("-", "_")

    # Map common industry variations
    industry_mapping = {
        "software": "technology",
        "tech": "technology",
        "it": "technology",
        "fintech": "financial_services",
        "banking": "financial_services",
        "insurance": "financial_services",
        "medical": "healthcare",
        "pharma": "healthcare",
        "pharmaceutical": "healthcare",
        "ecommerce": "retail",
        "e_commerce": "retail",
        "consumer": "retail",
    }

    industry_key = industry_mapping.get(industry_key, industry_key)

    return SALES_CONTEXT["industry_insights"].get(
        industry_key,
        SALES_CONTEXT["industry_insights"]["technology"],  # Default fallback
    )


def get_confidence_guidelines() -> dict:
    """Get confidence scoring guidelines"""
    return SALES_CONTEXT["confidence_scoring_rules"]


def get_objection_handling_strategies() -> dict:
    """Get objection handling strategies"""
    return SALES_CONTEXT["objection_handling"]


def get_recommendation_guidelines() -> dict:
    """Get recommendation guidelines"""
    return SALES_CONTEXT["recommendation_guidelines"]


def build_context_prompt(prompt_type: str, additional_context: dict = None) -> str:
    """Build a context-aware prompt for AI interactions"""
    base_prompt = PROMPT_TEMPLATES.get(prompt_type, "")

    # Add company context
    company_context = f"""
    
    COMPANY CONTEXT:
    You are providing recommendations for {SALES_CONTEXT['company_profile']['name']}, 
    an {SALES_CONTEXT['company_profile']['industry']} company that helps 
    {SALES_CONTEXT['company_profile']['target_market']}.
    
    Our value proposition: {SALES_CONTEXT['company_profile']['value_proposition']}
    
    Key differentiators:
    {chr(10).join(f"- {advantage}" for advantage in SALES_CONTEXT['company_profile']['competitive_advantages'])}
    """

    # Add methodology context
    methodology_context = f"""
    
    SALES METHODOLOGY:
    Use {SALES_CONTEXT['sales_methodology']['primary_approach']} approach with 
    {SALES_CONTEXT['sales_methodology']['framework']} qualification framework.
    
    Key qualification criteria:
    {chr(10).join(f"- {criteria}" for criteria in SALES_CONTEXT['sales_methodology']['qualification_criteria'])}
    """

    # Add behavioral guidelines
    behavior_context = f"""
    
    BEHAVIORAL GUIDELINES:
    - Tone: {AI_GUIDELINES['tone_and_style']['professional']}, {AI_GUIDELINES['tone_and_style']['confident']}
    - Approach: {AI_GUIDELINES['recommendation_principles']['data_driven']}, {AI_GUIDELINES['recommendation_principles']['actionable']}
    - Quality: {AI_GUIDELINES['quality_standards']['accuracy']}, {AI_GUIDELINES['quality_standards']['relevance']}
    """

    # Combine all context
    full_prompt = base_prompt + company_context + methodology_context + behavior_context

    # Add any additional context
    if additional_context:
        additional_context_str = f"""
        
        ADDITIONAL CONTEXT:
        {chr(10).join(f"- {key}: {value}" for key, value in additional_context.items())}
        """
        full_prompt += additional_context_str

    return full_prompt
