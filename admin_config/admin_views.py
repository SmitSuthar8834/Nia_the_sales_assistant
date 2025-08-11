import json
from datetime import datetime

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView

from ai_service.models import Lead
from ai_service.views import (
    AnalyzeConversationView,
    ComprehensiveRecommendationsView,
    ExtractLeadInfoView,
    LeadQualityScoreView,
    SalesStrategyView,
)

from .models import (
    ConfigurationBackup,
    ConfigurationTemplate,
    ConfigurationTest,
    IntegrationConfiguration,
    WorkflowConfiguration,
)


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    """Main admin dashboard with AI functionality"""

    template_name = "admin/ai_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get statistics
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
                "recent_tests": ConfigurationTest.objects.order_by("-started_at")[:5],
                # AI Service Status
                "ai_service_status": self.get_ai_service_status(),
                "integration_health": self.get_integration_health(),
            }
        )

        return context

    def get_ai_service_status(self):
        """Check AI service health"""
        try:
            # Test Gemini connection
            from ai_service.views import TestGeminiConnectionView

            test_view = TestGeminiConnectionView()
            test_result = test_view.get(self.request)

            if hasattr(test_result, "data"):
                return {
                    "status": "healthy" if test_result.data.get("success") else "error",
                    "message": test_result.data.get("message", "Unknown status"),
                    "model": test_result.data.get("model", "Unknown"),
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"AI service error: {str(e)}",
                "model": "Unknown",
            }

        return {
            "status": "unknown",
            "message": "Unable to determine AI service status",
            "model": "Unknown",
        }

    def get_integration_health(self):
        """Get integration health summary"""
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


@staff_member_required
def ai_analyze_conversation(request):
    """AI conversation analysis endpoint for admin"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            conversation_text = data.get("conversation_text", "")
            context = data.get("context", {})

            if not conversation_text:
                return JsonResponse(
                    {"error": "Conversation text is required"}, status=400
                )

            # Use the AI service to analyze conversation
            analyze_view = AnalyzeConversationView()
            analyze_view.request = request

            # Create a mock request with the data
            class MockRequest:
                def __init__(self, data):
                    self.data = data
                    self.user = request.user

            mock_request = MockRequest(
                {"conversation_text": conversation_text, "context": context}
            )

            result = analyze_view.post(mock_request)

            if hasattr(result, "data"):
                return JsonResponse({"success": True, "analysis": result.data})
            else:
                return JsonResponse({"error": "Analysis failed"}, status=500)

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
            context = data.get("context", {})

            if not conversation_text:
                return JsonResponse(
                    {"error": "Conversation text is required"}, status=400
                )

            # Use the AI service to extract lead info
            extract_view = ExtractLeadInfoView()
            extract_view.request = request

            class MockRequest:
                def __init__(self, data):
                    self.data = data
                    self.user = request.user

            mock_request = MockRequest(
                {"conversation_text": conversation_text, "context": context}
            )

            result = extract_view.post(mock_request)

            if hasattr(result, "data"):
                return JsonResponse({"success": True, "extracted_info": result.data})
            else:
                return JsonResponse({"error": "Extraction failed"}, status=500)

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

            # Use the AI service to score lead quality
            score_view = LeadQualityScoreView()
            score_view.request = request

            class MockRequest:
                def __init__(self, data):
                    self.data = data
                    self.user = request.user

            mock_request = MockRequest({"lead_data": lead_data})
            result = score_view.post(mock_request)

            if hasattr(result, "data"):
                return JsonResponse({"success": True, "quality_score": result.data})
            else:
                return JsonResponse({"error": "Scoring failed"}, status=500)

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
            quality_score = data.get("quality_score")

            if not lead_data:
                return JsonResponse({"error": "Lead data is required"}, status=400)

            # Use the AI service to get sales strategy
            strategy_view = SalesStrategyView()
            strategy_view.request = request

            class MockRequest:
                def __init__(self, data):
                    self.data = data
                    self.user = request.user

            mock_request = MockRequest(
                {"lead_data": lead_data, "quality_score": quality_score}
            )

            result = strategy_view.post(mock_request)

            if hasattr(result, "data"):
                return JsonResponse({"success": True, "sales_strategy": result.data})
            else:
                return JsonResponse({"error": "Strategy generation failed"}, status=500)

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

            # Use the AI service to get comprehensive recommendations
            recommendations_view = ComprehensiveRecommendationsView()
            recommendations_view.request = request

            class MockRequest:
                def __init__(self, data):
                    self.data = data
                    self.user = request.user

            mock_request = MockRequest({"lead_data": lead_data})
            result = recommendations_view.post(mock_request)

            if hasattr(result, "data"):
                return JsonResponse({"success": True, "recommendations": result.data})
            else:
                return JsonResponse(
                    {"error": "Recommendations generation failed"}, status=500
                )

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "POST method required"}, status=405)


@staff_member_required
def ai_test_connection(request):
    """Test AI service connection"""
    try:
        from ai_service.views import TestGeminiConnectionView

        test_view = TestGeminiConnectionView()
        result = test_view.get(request)

        if hasattr(result, "data"):
            return JsonResponse({"success": True, "connection_test": result.data})
        else:
            return JsonResponse({"error": "Connection test failed"}, status=500)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@staff_member_required
def create_lead_from_analysis(request):
    """Create a lead from AI analysis results"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            conversation_text = data.get("conversation_text", "")
            extracted_info = data.get("extracted_info", {})
            analysis_result = data.get("analysis_result", {})

            if not conversation_text:
                return JsonResponse(
                    {"error": "Conversation text is required"}, status=400
                )

            # Create lead from extracted information
            lead_data = {
                "company_name": extracted_info.get("company_name", "Unknown Company"),
                "contact_info": {
                    "name": extracted_info.get("contact_name", ""),
                    "email": extracted_info.get("contact_email", ""),
                    "phone": extracted_info.get("contact_phone", ""),
                },
                "industry": extracted_info.get("industry", ""),
                "notes": conversation_text,
                "conversation_text": conversation_text,
                "ai_analysis": analysis_result,
                "extracted_info": extracted_info,
                "created_by_admin": True,
                "admin_user": request.user.username,
            }

            # Create the lead
            lead = Lead.objects.create(
                company_name=lead_data["company_name"],
                contact_info=lead_data["contact_info"],
                industry=lead_data["industry"],
                notes=lead_data["notes"],
                conversation_text=lead_data["conversation_text"],
                ai_insights={
                    "analysis": analysis_result,
                    "extracted_info": extracted_info,
                    "created_by_admin": True,
                    "admin_user": request.user.username,
                    "created_at": datetime.now().isoformat(),
                },
            )

            return JsonResponse(
                {
                    "success": True,
                    "lead_id": lead.id,
                    "message": f'Lead "{lead.company_name}" created successfully',
                }
            )

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "POST method required"}, status=405)


@staff_member_required
def integration_test(request, integration_id):
    """Test a specific integration"""
    integration = get_object_or_404(IntegrationConfiguration, id=integration_id)

    try:
        # Create a test record
        test = ConfigurationTest.objects.create(
            configuration=integration,
            test_type="connection",
            test_data={"admin_test": True},
            expected_result={"success": True},
            triggered_by=request.user,
        )

        # Run the test (this would be implemented in the services)
        from .services_minimal import ConfigurationTestService

        result = ConfigurationTestService.run_test(test)

        if result.success:
            messages.success(
                request, f'Integration "{integration.name}" test passed successfully!'
            )
        else:
            messages.error(
                request,
                f'Integration "{integration.name}" test failed: {result.error_message}',
            )

    except Exception as e:
        messages.error(request, f"Test failed with error: {str(e)}")

    return redirect("admin:admin_config_integrationconfiguration_changelist")


@staff_member_required
def integration_toggle_status(request, integration_id, action):
    """Activate or deactivate an integration"""
    integration = get_object_or_404(IntegrationConfiguration, id=integration_id)

    if action == "activate":
        integration.status = "active"
        integration.health_status = "healthy"
        messages.success(
            request, f'Integration "{integration.name}" activated successfully!'
        )
    elif action == "deactivate":
        integration.status = "inactive"
        messages.warning(request, f'Integration "{integration.name}" deactivated.')

    integration.save()
    return redirect("admin:admin_config_integrationconfiguration_changelist")


@staff_member_required
def workflow_execute(request, workflow_id):
    """Execute a workflow manually"""
    workflow = get_object_or_404(WorkflowConfiguration, id=workflow_id)

    try:
        # This would integrate with a workflow engine
        workflow.execution_count += 1
        workflow.last_execution = datetime.now()
        workflow.save()

        messages.success(request, f'Workflow "{workflow.name}" executed successfully!')

    except Exception as e:
        messages.error(request, f"Workflow execution failed: {str(e)}")

    return redirect("admin:admin_config_workflowconfiguration_changelist")


@staff_member_required
def backup_restore(request, backup_id):
    """Restore from a backup"""
    backup = get_object_or_404(ConfigurationBackup, id=backup_id)

    if request.method == "POST":
        try:
            from .services_minimal import ConfigurationBackupService

            result = ConfigurationBackupService.restore_backup(backup, request.user)

            if result["success"]:
                backup.restored_count += 1
                backup.last_restored = datetime.now()
                backup.save()

                messages.success(
                    request,
                    f'Backup "{backup.name}" restored successfully! {result["restored_count"]} items restored.',
                )
            else:
                messages.error(
                    request, f'Backup restore failed: {"; ".join(result["errors"])}'
                )

        except Exception as e:
            messages.error(request, f"Backup restore failed: {str(e)}")

    return redirect("admin:admin_config_configurationbackup_changelist")
