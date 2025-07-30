from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import logging

from .services import GeminiAIService
from .models import ConversationAnalysis

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class AnalyzeConversationView(APIView):
    """API endpoint to analyze conversation text and extract lead information"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Analyze conversation text using Gemini AI
        
        Expected payload:
        {
            "conversation_text": "The conversation transcript..."
        }
        """
        try:
            conversation_text = request.data.get('conversation_text', '')
            
            if not conversation_text.strip():
                return Response(
                    {"error": "conversation_text is required and cannot be empty"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Initialize Gemini AI service
            ai_service = GeminiAIService()
            
            # Extract lead information
            extracted_data = ai_service.extract_lead_info(conversation_text)
            
            # Generate recommendations
            recommendations = ai_service.generate_recommendations(extracted_data)
            
            # Save analysis to database
            analysis = ConversationAnalysis.objects.create(
                user=request.user,
                conversation_text=conversation_text,
                extracted_data={
                    'lead_info': extracted_data,
                    'recommendations': recommendations
                }
            )
            
            return Response({
                "success": True,
                "analysis_id": str(analysis.id),
                "lead_info": extracted_data,
                "recommendations": recommendations,
                "message": "Conversation analyzed successfully"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error analyzing conversation: {e}")
            return Response(
                {"error": f"Failed to analyze conversation: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class TestGeminiConnectionView(APIView):
    """API endpoint to test Gemini AI connection"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Test the connection to Gemini AI"""
        try:
            ai_service = GeminiAIService()
            result = ai_service.test_connection()
            
            if result['success']:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
        except Exception as e:
            logger.error(f"Error testing Gemini connection: {e}")
            return Response(
                {"error": f"Connection test failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConversationHistoryView(APIView):
    """API endpoint to retrieve conversation analysis history"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get conversation analysis history for the current user"""
        try:
            analyses = ConversationAnalysis.objects.filter(user=request.user)[:10]
            
            history = []
            for analysis in analyses:
                history.append({
                    "id": str(analysis.id),
                    "timestamp": analysis.analysis_timestamp.isoformat(),
                    "conversation_preview": analysis.conversation_text[:100] + "..." if len(analysis.conversation_text) > 100 else analysis.conversation_text,
                    "extracted_data": analysis.extracted_data
                })
            
            return Response({
                "success": True,
                "history": history,
                "count": len(history)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            return Response(
                {"error": f"Failed to retrieve history: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
