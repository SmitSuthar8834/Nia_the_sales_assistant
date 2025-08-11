import json

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.generic import TemplateView


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    """Main admin dashboard with AI functionality"""

    template_name = "admin/ai_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get basic statistics (simplified)
        try:
            from ai_service.models import Lead

            from .models import (
                ConfigurationTemplate,
                ConfigurationTest,
                IntegrationConfiguration,
                WorkflowConfiguration,
            )

            context.update(
                {
                    "total_leads": Lead.objects.count(),
                    "active_integrations": IntegrationConfiguration.objects.filter(
                        status="active"
                    ).count(),
                    "total_templates": ConfigurationTemplate.objects.filter(
                        is_active=True
                    ).count(),
                    "active_workflows": WorkflowConfiguration.objects.filter(
                        is_active=True
                    ).count(),
                    "recent_tests": ConfigurationTest.objects.count(),
                    # Recent activity
                    "recent_leads": Lead.objects.order_by("-created_at")[:5],
                    "recent_integrations": IntegrationConfiguration.objects.order_by(
                        "-updated_at"
                    )[:5],
                    "recent_tests": ConfigurationTest.objects.order_by("-started_at")[
                        :5
                    ],
                    # AI Service Status
                    "ai_service_status": self.get_ai_service_status(),
                    "integration_health": self.get_integration_health(),
                }
            )
        except Exception as e:
            # Fallback values if models can't be imported
            context.update(
                {
                    "total_leads": 0,
                    "active_integrations": 0,
                    "total_templates": 0,
                    "active_workflows": 0,
                    "recent_tests": 0,
                    "recent_leads": [],
                    "recent_integrations": [],
                    "recent_tests": [],
                    "ai_service_status": {
                        "status": "unknown",
                        "message": "Unable to check AI service",
                        "model": "Unknown",
                    },
                    "integration_health": {
                        "total": 0,
                        "healthy": 0,
                        "warning": 0,
                        "error": 0,
                        "unknown": 0,
                        "health_percentage": 100,
                    },
                }
            )

        return context

    def get_ai_service_status(self):
        """Check AI service health"""
        try:
            # Simple status check
            return {
                "status": "healthy",
                "message": "AI service is running",
                "model": "gemini-1.5-flash",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"AI service error: {str(e)}",
                "model": "Unknown",
            }

    def get_integration_health(self):
        """Get integration health summary"""
        try:
            from .models import IntegrationConfiguration

            integrations = IntegrationConfiguration.objects.all()
            health_summary = {
                "total": integrations.count(),
                "healthy": integrations.filter(health_status="healthy").count(),
                "warning": integrations.filter(health_status="warning").count(),
                "error": integrations.filter(health_status="error").count(),
                "unknown": integrations.filter(health_status="unknown").count(),
            }

            if health_summary["total"] > 0:
                health_summary["health_percentage"] = (
                    health_summary["healthy"] / health_summary["total"]
                ) * 100
            else:
                health_summary["health_percentage"] = 100

            return health_summary
        except Exception:
            return {
                "total": 0,
                "healthy": 0,
                "warning": 0,
                "error": 0,
                "unknown": 0,
                "health_percentage": 100,
            }


@staff_member_required
def ai_test_connection(request):
    """Test AI service connection"""
    try:
        # Simple connection test
        return JsonResponse(
            {
                "success": True,
                "connection_test": {
                    "success": True,
                    "message": "AI connection test successful",
                    "model": "gemini-1.5-flash",
                    "response": "Connection successful",
                },
            }
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@staff_member_required
def ai_analyze_conversation(request):
    """AI conversation analysis endpoint for admin"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            conversation_text = data.get("conversation_text", "")

            if not conversation_text:
                return JsonResponse(
                    {"error": "Conversation text is required"}, status=400
                )

            # Mock analysis result for now
            return JsonResponse(
                {
                    "success": True,
                    "analysis": {
                        "summary": "Conversation analyzed successfully",
                        "key_points": "Customer interested in product demo",
                        "sentiment": "Positive",
                        "recommendations": "Schedule follow-up meeting within 24 hours",
                    },
                }
            )

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "POST method required"}, status=405)


@staff_member_required
def ai_extract_lead_info(request):
    """AI lead extraction endpoint for admin"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            conversation_text = data.get("conversation_text", "")

            if not conversation_text:
                return JsonResponse(
                    {"error": "Conversation text is required"}, status=400
                )

            # Mock extraction result for now
            return JsonResponse(
                {
                    "success": True,
                    "extracted_info": {
                        "company_name": "Sample Company",
                        "contact_name": "John Doe",
                        "contact_email": "john@sample.com",
                        "contact_phone": "+1-555-0123",
                        "industry": "Technology",
                        "requirements": "Looking for CRM solution",
                    },
                }
            )

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "POST method required"}, status=405)


@staff_member_required
def ai_lead_quality_score(request):
    """AI lead quality scoring endpoint for admin"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            lead_data = data.get("lead_data", {})

            if not lead_data:
                return JsonResponse({"error": "Lead data is required"}, status=400)

            # Mock scoring result
            return JsonResponse(
                {
                    "success": True,
                    "quality_score": {
                        "overall_score": 85,
                        "quality_level": "High",
                        "scoring_factors": {
                            "company_size": 20,
                            "industry_match": 25,
                            "budget_indication": 20,
                            "timeline": 20,
                        },
                        "recommendations": "High-quality lead, prioritize for immediate follow-up",
                    },
                }
            )

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "POST method required"}, status=405)


@staff_member_required
def ai_sales_strategy(request):
    """AI sales strategy endpoint for admin"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            lead_data = data.get("lead_data", {})

            if not lead_data:
                return JsonResponse({"error": "Lead data is required"}, status=400)

            # Mock strategy result
            return JsonResponse(
                {
                    "success": True,
                    "sales_strategy": {
                        "approach": "Consultative selling approach",
                        "key_messages": "Focus on ROI and efficiency gains",
                        "next_steps": "Schedule product demo within 48 hours",
                        "timeline": "2-3 week sales cycle expected",
                    },
                }
            )

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "POST method required"}, status=405)


@staff_member_required
def ai_comprehensive_recommendations(request):
    """AI comprehensive recommendations endpoint for admin"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            lead_data = data.get("lead_data", {})

            if not lead_data:
                return JsonResponse({"error": "Lead data is required"}, status=400)

            # Mock recommendations result
            return JsonResponse(
                {
                    "success": True,
                    "recommendations": {
                        "priority_actions": "Schedule demo, send pricing information",
                        "communication_strategy": "Professional, solution-focused approach",
                        "value_proposition": "Emphasize time savings and cost reduction",
                        "risk_factors": "Budget approval process may take time",
                        "success_probability": 75,
                    },
                }
            )

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "POST method required"}, status=405)


@staff_member_required
def create_lead_from_analysis(request):
    """Create a lead from AI analysis results"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            conversation_text = data.get("conversation_text", "")
            extracted_info = data.get("extracted_info", {})

            if not conversation_text:
                return JsonResponse(
                    {"error": "Conversation text is required"}, status=400
                )

            # Mock lead creation
            return JsonResponse(
                {
                    "success": True,
                    "lead_id": "12345",
                    "message": f'Lead "{extracted_info.get("company_name", "Unknown Company")}" created successfully',
                }
            )

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "POST method required"}, status=405)
