from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'ai_service'

# Create router for ViewSets
router = DefaultRouter()
router.register(r'leads', views.LeadViewSet, basename='lead')

urlpatterns = [
    # Lead management endpoints (Task 4)
    path('', include(router.urls)),
    path('analytics/', views.LeadAnalyticsView.as_view(), name='lead_analytics'),
    
    # Main analysis endpoint
    path('analyze/', views.AnalyzeConversationView.as_view(), name='analyze_conversation'),
    
    # Debug endpoint for testing
    path('debug-test/', views.DebugTestView.as_view(), name='debug_test'),
    
    # Dedicated extraction endpoints
    path('extract-lead/', views.ExtractLeadInfoView.as_view(), name='extract_lead_info'),
    path('extract-entities/', views.ExtractEntitiesView.as_view(), name='extract_entities'),
    path('validate-lead/', views.ValidateLeadDataView.as_view(), name='validate_lead_data'),
    
    # AI-powered sales recommendations endpoints (Task 3)
    path('lead-quality-score/', views.LeadQualityScoreView.as_view(), name='lead_quality_score'),
    path('sales-strategy/', views.SalesStrategyView.as_view(), name='sales_strategy'),
    path('industry-insights/', views.IndustryInsightsView.as_view(), name='industry_insights'),
    path('comprehensive-recommendations/', views.ComprehensiveRecommendationsView.as_view(), name='comprehensive_recommendations'),
    path('next-steps/', views.NextStepsRecommendationsView.as_view(), name='next_steps_recommendations'),
    
    # Utility endpoints
    path('test-connection/', views.TestGeminiConnectionView.as_view(), name='test_connection'),
    path('quota-status/', views.GeminiQuotaStatusView.as_view(), name='quota_status'),
    path('history/', views.ConversationHistoryView.as_view(), name='conversation_history'),
]