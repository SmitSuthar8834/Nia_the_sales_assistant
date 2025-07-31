from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import logging
from typing import Dict, Any

from .services import GeminiAIService
from .models import ConversationAnalysis

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class AnalyzeConversationView(APIView):
    """Enhanced API endpoint to analyze conversation text and extract lead information"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Analyze conversation text using enhanced Gemini AI extraction
        
        Expected payload:
        {
            "conversation_text": "The conversation transcript...",
            "context": {  // Optional additional context
                "previous_interactions": [],
                "lead_source": "phone_call|email|meeting",
                "user_preferences": {}
            },
            "extract_entities": true,  // Optional: whether to extract entities
            "generate_recommendations": true  // Optional: whether to generate recommendations
        }
        """
        try:
            # Validate input
            conversation_text = request.data.get('conversation_text', '').strip()
            if not conversation_text:
                return Response(
                    {
                        "success": False,
                        "error": "conversation_text is required and cannot be empty",
                        "error_code": "MISSING_CONVERSATION_TEXT"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get optional parameters
            context = request.data.get('context', {})
            extract_entities = request.data.get('extract_entities', True)
            generate_recommendations = request.data.get('generate_recommendations', True)
            
            # Initialize AI service
            ai_service = GeminiAIService()
            
            # Extract lead information with context
            extracted_data = ai_service.extract_lead_info(conversation_text, context)
            
            # Add extraction timestamp
            extracted_data['extraction_metadata']['extraction_timestamp'] = timezone.now().isoformat()
            
            # Validate extracted data
            validation_results = ai_service.validate_extracted_data(extracted_data)
            
            # Extract entities if requested
            entities = {}
            if extract_entities:
                entities = ai_service.extract_entities(conversation_text)
            
            # Generate recommendations if requested
            recommendations = {}
            if generate_recommendations:
                recommendations = ai_service.generate_recommendations(extracted_data, context)
            
            # Prepare response data
            response_data = {
                "success": True,
                "analysis_id": None,  # Will be set after saving
                "lead_information": extracted_data,
                "validation": validation_results,
                "entities": entities if extract_entities else None,
                "recommendations": recommendations if generate_recommendations else None,
                "processing_metadata": {
                    "processed_at": timezone.now().isoformat(),
                    "processing_time_ms": None,  # Could be calculated if needed
                    "ai_model": "gemini-1.5-flash",
                    "extraction_version": "2.0"
                }
            }
            
            # Save analysis to database
            analysis = ConversationAnalysis.objects.create(
                user=request.user,
                conversation_text=conversation_text,
                extracted_data={
                    'lead_info': extracted_data,
                    'validation': validation_results,
                    'entities': entities,
                    'recommendations': recommendations,
                    'context': context
                }
            )
            
            response_data["analysis_id"] = str(analysis.id)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error analyzing conversation: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to analyze conversation: {str(e)}",
                    "error_code": "ANALYSIS_FAILED",
                    "timestamp": timezone.now().isoformat()
                },
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


@method_decorator(csrf_exempt, name='dispatch')
class ExtractLeadInfoView(APIView):
    """Dedicated API endpoint for lead information extraction only"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Extract lead information from conversation text without full analysis
        
        Expected payload:
        {
            "conversation_text": "The conversation transcript...",
            "context": {}  // Optional context
        }
        """
        try:
            conversation_text = request.data.get('conversation_text', '').strip()
            if not conversation_text:
                return Response(
                    {
                        "success": False,
                        "error": "conversation_text is required",
                        "error_code": "MISSING_CONVERSATION_TEXT"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            context = request.data.get('context', {})
            ai_service = GeminiAIService()
            
            # Extract lead information
            lead_info = ai_service.extract_lead_info(conversation_text, context)
            lead_info['extraction_metadata']['extraction_timestamp'] = timezone.now().isoformat()
            
            # Validate the data
            validation = ai_service.validate_extracted_data(lead_info)
            
            return Response({
                "success": True,
                "lead_information": lead_info,
                "validation": validation,
                "extracted_at": timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error extracting lead info: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to extract lead information: {str(e)}",
                    "error_code": "EXTRACTION_FAILED"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class ExtractEntitiesView(APIView):
    """API endpoint for entity extraction from text"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Extract named entities from text
        
        Expected payload:
        {
            "text": "Text to extract entities from..."
        }
        """
        try:
            text = request.data.get('text', '').strip()
            if not text:
                return Response(
                    {
                        "success": False,
                        "error": "text is required",
                        "error_code": "MISSING_TEXT"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            ai_service = GeminiAIService()
            entities = ai_service.extract_entities(text)
            
            return Response({
                "success": True,
                "entities": entities,
                "extracted_at": timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to extract entities: {str(e)}",
                    "error_code": "ENTITY_EXTRACTION_FAILED"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class ValidateLeadDataView(APIView):
    """API endpoint for validating lead data"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Validate lead data structure and content
        
        Expected payload:
        {
            "lead_data": {
                // Lead data structure to validate
            }
        }
        """
        try:
            lead_data = request.data.get('lead_data', {})
            if not lead_data:
                return Response(
                    {
                        "success": False,
                        "error": "lead_data is required",
                        "error_code": "MISSING_LEAD_DATA"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            ai_service = GeminiAIService()
            validation_results = ai_service.validate_extracted_data(lead_data)
            
            return Response({
                "success": True,
                "validation": validation_results,
                "validated_at": timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error validating lead data: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to validate lead data: {str(e)}",
                    "error_code": "VALIDATION_FAILED"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConversationHistoryView(APIView):
    """Enhanced API endpoint to retrieve conversation analysis history"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get conversation analysis history for the current user with enhanced formatting"""
        try:
            # Get query parameters
            limit = int(request.query_params.get('limit', 10))
            offset = int(request.query_params.get('offset', 0))
            
            analyses = ConversationAnalysis.objects.filter(
                user=request.user
            ).order_by('-analysis_timestamp')[offset:offset + limit]
            
            history = []
            for analysis in analyses:
                extracted_data = analysis.extracted_data
                lead_info = extracted_data.get('lead_info', {})
                
                history.append({
                    "id": str(analysis.id),
                    "timestamp": analysis.analysis_timestamp.isoformat(),
                    "conversation_preview": (
                        analysis.conversation_text[:100] + "..." 
                        if len(analysis.conversation_text) > 100 
                        else analysis.conversation_text
                    ),
                    "company_name": lead_info.get('company_name'),
                    "contact_name": lead_info.get('contact_details', {}).get('name'),
                    "confidence_score": lead_info.get('extraction_metadata', {}).get('confidence_score', 0),
                    "data_completeness": lead_info.get('extraction_metadata', {}).get('data_completeness', 0),
                    "has_recommendations": bool(extracted_data.get('recommendations')),
                    "validation_status": extracted_data.get('validation', {}).get('is_valid', False)
                })
            
            return Response({
                "success": True,
                "history": history,
                "count": len(history),
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "has_more": len(analyses) == limit
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to retrieve history: {str(e)}",
                    "error_code": "HISTORY_RETRIEVAL_FAILED"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
