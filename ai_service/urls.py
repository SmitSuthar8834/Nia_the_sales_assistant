from django.urls import path
from . import views

app_name = 'ai_service'

urlpatterns = [
    # Main analysis endpoint
    path('analyze/', views.AnalyzeConversationView.as_view(), name='analyze_conversation'),
    
    # Dedicated extraction endpoints
    path('extract-lead/', views.ExtractLeadInfoView.as_view(), name='extract_lead_info'),
    path('extract-entities/', views.ExtractEntitiesView.as_view(), name='extract_entities'),
    path('validate-lead/', views.ValidateLeadDataView.as_view(), name='validate_lead_data'),
    
    # Utility endpoints
    path('test-connection/', views.TestGeminiConnectionView.as_view(), name='test_connection'),
    path('history/', views.ConversationHistoryView.as_view(), name='conversation_history'),
]