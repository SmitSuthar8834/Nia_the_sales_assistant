import logging

from celery import shared_task
from django.utils import timezone

from .models import AIInsights, Lead
from .services import GeminiAIService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def analyze_lead_with_ai(self, lead_id, conversation_text=None):
    """
    Asynchronous task to analyze lead with AI and create/update insights

    Args:
        lead_id (str): UUID of the lead to analyze
        conversation_text (str): Optional conversation text to analyze

    Returns:
        dict: Analysis results and status
    """
    try:
        # Get the lead
        lead = Lead.objects.get(id=lead_id)

        # Initialize AI service
        ai_service = GeminiAIService()

        # Use provided conversation text or lead's conversation history
        text_to_analyze = conversation_text or lead.conversation_history

        if not text_to_analyze:
            logger.warning(f"No conversation text available for lead {lead_id}")
            return {
                "status": "skipped",
                "reason": "No conversation text available",
                "lead_id": str(lead_id),
            }

        # Extract lead information from conversation
        extracted_data = ai_service.extract_lead_info(text_to_analyze)

        # Update lead with extracted information if not already set
        _update_lead_from_extraction(lead, extracted_data)

        # Generate comprehensive AI insights
        quality_score = ai_service.calculate_lead_quality_score(extracted_data)
        recommendations = ai_service.generate_recommendations(extracted_data)
        sales_strategy = ai_service.generate_sales_strategy(
            extracted_data, quality_score
        )
        industry_insights = ai_service.generate_industry_insights(extracted_data)

        # Create or update AI insights
        ai_insights, created = AIInsights.objects.get_or_create(
            lead=lead,
            defaults=_build_insights_data(
                quality_score, recommendations, sales_strategy, industry_insights
            ),
        )

        if not created:
            # Update existing insights
            for key, value in _build_insights_data(
                quality_score, recommendations, sales_strategy, industry_insights
            ).items():
                setattr(ai_insights, key, value)
            ai_insights.save()

        logger.info(f"Successfully analyzed lead {lead_id} with AI")

        return {
            "status": "success",
            "lead_id": str(lead_id),
            "insights_id": str(ai_insights.id),
            "lead_score": ai_insights.lead_score,
            "quality_tier": ai_insights.quality_tier,
            "created": created,
        }

    except Lead.DoesNotExist:
        logger.error(f"Lead {lead_id} not found")
        return {"status": "error", "error": "Lead not found", "lead_id": str(lead_id)}

    except Exception as exc:
        logger.error(f"Error analyzing lead {lead_id}: {exc}")

        # Retry the task with exponential backoff
        if self.request.retries < self.max_retries:
            retry_delay = 2**self.request.retries  # Exponential backoff
            raise self.retry(countdown=retry_delay, exc=exc)

        return {
            "status": "error",
            "error": str(exc),
            "lead_id": str(lead_id),
            "retries_exhausted": True,
        }


def _update_lead_from_extraction(lead, extracted_data):
    """Update lead fields from AI extraction if they're not already set"""
    updated = False

    # Update company name if not set
    if not lead.company_name and extracted_data.get("company_name"):
        lead.company_name = extracted_data["company_name"]
        updated = True

    # Update industry if not set
    if not lead.industry and extracted_data.get("industry"):
        lead.industry = extracted_data["industry"]
        updated = True

    # Update company size if not set
    if not lead.company_size and extracted_data.get("company_size"):
        lead.company_size = extracted_data["company_size"]
        updated = True

    # Update contact info if not comprehensive
    if extracted_data.get("contact_details"):
        contact_details = extracted_data["contact_details"]
        current_contact = lead.contact_info or {}

        # Merge contact information
        for key, value in contact_details.items():
            if value and not current_contact.get(key):
                current_contact[key] = value
                updated = True

        lead.contact_info = current_contact

    # Update pain points if not set
    if not lead.pain_points and extracted_data.get("pain_points"):
        lead.pain_points = extracted_data["pain_points"]
        updated = True

    # Update requirements if not set
    if not lead.requirements and extracted_data.get("requirements"):
        lead.requirements = extracted_data["requirements"]
        updated = True

    # Update budget info if not set
    if not lead.budget_info and extracted_data.get("budget_info"):
        lead.budget_info = extracted_data["budget_info"]
        updated = True

    # Update timeline if not set
    if not lead.timeline and extracted_data.get("timeline"):
        lead.timeline = extracted_data["timeline"]
        updated = True

    # Update decision makers if not set
    if not lead.decision_makers and extracted_data.get("decision_makers"):
        lead.decision_makers = extracted_data["decision_makers"]
        updated = True

    # Update urgency level if not set
    if not lead.urgency_level and extracted_data.get("urgency_level"):
        urgency_mapping = {
            "high": Lead.UrgencyLevel.HIGH,
            "medium": Lead.UrgencyLevel.MEDIUM,
            "low": Lead.UrgencyLevel.LOW,
        }
        mapped_urgency = urgency_mapping.get(extracted_data["urgency_level"].lower())
        if mapped_urgency:
            lead.urgency_level = mapped_urgency
            updated = True

    # Update current solution if not set
    if not lead.current_solution and extracted_data.get("current_solution"):
        lead.current_solution = extracted_data["current_solution"]
        updated = True

    # Update competitors mentioned if not set
    if not lead.competitors_mentioned and extracted_data.get("competitors_mentioned"):
        lead.competitors_mentioned = extracted_data["competitors_mentioned"]
        updated = True

    if updated:
        lead.save()
        logger.info(f"Updated lead {lead.id} with extracted data")


def _build_insights_data(
    quality_score, recommendations, sales_strategy, industry_insights
):
    """Build AI insights data from analysis results"""
    return {
        # Lead Quality Scoring
        "lead_score": quality_score.get("overall_score", 50),
        "conversion_probability": quality_score.get("conversion_probability", 25),
        "quality_tier": quality_score.get("quality_tier", "medium"),
        "score_breakdown": quality_score.get("score_breakdown", {}),
        # Deal Predictions
        "estimated_deal_size": quality_score.get("estimated_deal_size", ""),
        "sales_cycle_prediction": quality_score.get("sales_cycle_prediction", ""),
        # Strategic Insights
        "key_strengths": quality_score.get("key_strengths", []),
        "improvement_areas": quality_score.get("improvement_areas", []),
        "competitive_risk": quality_score.get("competitive_risk", "medium"),
        # Recommendations
        "recommended_actions": recommendations.get("recommendations", []),
        "next_steps": recommendations.get("next_best_actions", []),
        "next_best_action": quality_score.get("next_best_action", ""),
        # Risk and Opportunity Analysis
        "risk_factors": recommendations.get("risk_factors", []),
        "opportunities": recommendations.get("opportunities", []),
        # Sales Strategy
        "primary_strategy": sales_strategy.get("primary_strategy", ""),
        "key_messaging": sales_strategy.get("key_messaging", []),
        "objection_handling": sales_strategy.get("objection_handling", {}),
        # Industry Insights
        "industry_insights": industry_insights,
        # Confidence and Metadata
        "confidence_score": recommendations.get("recommendation_confidence", 70),
        "data_completeness": quality_score.get("validation_metadata", {}).get(
            "confidence_level", 50
        ),
        # Timestamp
        "last_analyzed": timezone.now(),
    }


@shared_task
def refresh_lead_insights(lead_id):
    """
    Refresh AI insights for a specific lead

    Args:
        lead_id (str): UUID of the lead to refresh insights for

    Returns:
        dict: Refresh results and status
    """
    try:
        lead = Lead.objects.get(id=lead_id)

        if not lead.conversation_history:
            return {
                "status": "skipped",
                "reason": "No conversation history available",
                "lead_id": str(lead_id),
            }

        # Trigger full AI analysis
        result = analyze_lead_with_ai.delay(lead_id, lead.conversation_history)

        return {"status": "triggered", "task_id": result.id, "lead_id": str(lead_id)}

    except Lead.DoesNotExist:
        return {"status": "error", "error": "Lead not found", "lead_id": str(lead_id)}


@shared_task
def bulk_refresh_insights(lead_ids):
    """
    Refresh AI insights for multiple leads

    Args:
        lead_ids (list): List of lead UUIDs to refresh

    Returns:
        dict: Bulk refresh results
    """
    results = []

    for lead_id in lead_ids:
        result = refresh_lead_insights.delay(lead_id)
        results.append(
            {
                "lead_id": lead_id,
                "task_id": result.id if hasattr(result, "id") else None,
                "status": "triggered",
            }
        )

    return {
        "status": "bulk_triggered",
        "total_leads": len(lead_ids),
        "results": results,
    }
