from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import admin_views_simple as admin_views
from . import views

# Create router for API endpoints
router = DefaultRouter()
router.register(r"templates", views.ConfigurationTemplateViewSet)
router.register(r"integrations", views.IntegrationConfigurationViewSet)
router.register(r"workflows", views.WorkflowConfigurationViewSet)
router.register(r"backups", views.ConfigurationBackupViewSet)
router.register(r"permissions", views.RolePermissionViewSet)
router.register(r"audit-logs", views.ConfigurationAuditLogViewSet)

app_name = "admin_config"

urlpatterns = [
    # API endpoints
    path("api/", include(router.urls)),
    # Custom API endpoints
    path("api/dashboard/", views.AdminDashboardView.as_view(), name="dashboard-api"),
    path("api/dynamic-form/", views.DynamicFormAPIView.as_view(), name="dynamic-form"),
    path(
        "api/validate-config/",
        views.ConfigurationValidationAPIView.as_view(),
        name="validate-config",
    ),
    # Frontend views
    path("", views.AdminDashboardTemplateView.as_view(), name="dashboard"),
    path(
        "integrations/", views.IntegrationsTemplateView.as_view(), name="integrations"
    ),
    path("workflows/", views.WorkflowsTemplateView.as_view(), name="workflows"),
    path("templates/", views.TemplatesTemplateView.as_view(), name="templates"),
    path("backups/", views.BackupsTemplateView.as_view(), name="backups"),
    path("permissions/", views.PermissionsTemplateView.as_view(), name="permissions"),
    path("audit/", views.AuditTemplateView.as_view(), name="audit"),
]

# Add AI Dashboard URLs directly to main urlpatterns
urlpatterns += [
    # AI Dashboard
    path(
        "ai-dashboard/", admin_views.AdminDashboardView.as_view(), name="ai_dashboard"
    ),
    # AI API endpoints for admin
    path(
        "ai/analyze-conversation/",
        admin_views.ai_analyze_conversation,
        name="ai_analyze_conversation",
    ),
    path(
        "ai/extract-lead-info/",
        admin_views.ai_extract_lead_info,
        name="ai_extract_lead_info",
    ),
    path(
        "ai/lead-quality-score/",
        admin_views.ai_lead_quality_score,
        name="ai_lead_quality_score",
    ),
    path("ai/sales-strategy/", admin_views.ai_sales_strategy, name="ai_sales_strategy"),
    path(
        "ai/comprehensive-recommendations/",
        admin_views.ai_comprehensive_recommendations,
        name="ai_comprehensive_recommendations",
    ),
    path(
        "ai/test-connection/", admin_views.ai_test_connection, name="ai_test_connection"
    ),
    path(
        "ai/create-lead/", admin_views.create_lead_from_analysis, name="ai_create_lead"
    ),
]
