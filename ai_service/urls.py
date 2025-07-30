from django.urls import path
from . import views

app_name = 'ai_service'

urlpatterns = [
    path('analyze/', views.AnalyzeConversationView.as_view(), name='analyze_conversation'),
    path('test-connection/', views.TestGeminiConnectionView.as_view(), name='test_connection'),
    path('history/', views.ConversationHistoryView.as_view(), name='conversation_history'),
]