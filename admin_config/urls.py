from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for API endpoints
router = DefaultRouter()
router.register(r'templates', views.ConfigurationTemplateViewSet)
router.register(r'integrations', views.IntegrationConfigurationViewSet)
router.register(r'workflows', views.WorkflowConfigurationViewSet)
router.register(r'backups', views.ConfigurationBackupViewSet)
router.register(r'permissions', views.RolePermissionViewSet)
router.register(r'audit-logs', views.ConfigurationAuditLogViewSet)

app_name = 'admin_config'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Custom API endpoints
    path('api/dashboard/', views.AdminDashboardView.as_view(), name='dashboard-api'),
    path('api/dynamic-form/', views.DynamicFormAPIView.as_view(), name='dynamic-form'),
    path('api/validate-config/', views.ConfigurationValidationAPIView.as_view(), name='validate-config'),
    
    # Frontend views
    path('', views.AdminDashboardTemplateView.as_view(), name='dashboard'),
    path('integrations/', views.IntegrationsTemplateView.as_view(), name='integrations'),
    path('workflows/', views.WorkflowsTemplateView.as_view(), name='workflows'),
    path('templates/', views.TemplatesTemplateView.as_view(), name='templates'),
    path('backups/', views.BackupsTemplateView.as_view(), name='backups'),
    path('permissions/', views.PermissionsTemplateView.as_view(), name='permissions'),
    path('audit/', views.AuditTemplateView.as_view(), name='audit'),
]