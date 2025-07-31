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


@method_decorator(csrf_exempt, name='dispatch')
class LeadQualityScoreView(APIView):
    """API endpoint for calculating lead quality score"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Calculate comprehensive lead quality score
        
        Expected payload:
        {
            "lead_data": {
                // Lead information to analyze
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
            quality_score = ai_service.calculate_lead_quality_score(lead_data)
            
            # Add timestamp
            quality_score['validation_metadata']['last_calculated'] = timezone.now().isoformat()
            
            return Response({
                "success": True,
                "quality_score": quality_score,
                "calculated_at": timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error calculating lead quality score: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to calculate lead quality score: {str(e)}",
                    "error_code": "QUALITY_SCORE_FAILED"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class SalesStrategyView(APIView):
    """API endpoint for generating sales strategy recommendations"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Generate tailored sales strategy recommendations
        
        Expected payload:
        {
            "lead_data": {
                // Lead information
            },
            "quality_score": {
                // Optional pre-calculated quality score
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
            
            quality_score = request.data.get('quality_score')
            
            ai_service = GeminiAIService()
            sales_strategy = ai_service.generate_sales_strategy(lead_data, quality_score)
            
            # Add timestamp
            sales_strategy['strategy_metadata']['last_generated'] = timezone.now().isoformat()
            
            return Response({
                "success": True,
                "sales_strategy": sales_strategy,
                "generated_at": timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating sales strategy: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to generate sales strategy: {str(e)}",
                    "error_code": "SALES_STRATEGY_FAILED"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class IndustryInsightsView(APIView):
    """API endpoint for generating industry-specific insights"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Generate industry-specific insights and best practices
        
        Expected payload:
        {
            "lead_data": {
                // Lead information with industry context
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
            industry_insights = ai_service.generate_industry_insights(lead_data)
            
            # Add timestamp
            industry_insights['insights_metadata']['last_generated'] = timezone.now().isoformat()
            
            return Response({
                "success": True,
                "industry_insights": industry_insights,
                "generated_at": timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating industry insights: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to generate industry insights: {str(e)}",
                    "error_code": "INDUSTRY_INSIGHTS_FAILED"
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

@method_decorator(csrf_exempt, name='dispatch')
class LeadQualityScoreView(APIView):
    """API endpoint for calculating lead quality score"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Calculate comprehensive lead quality score
        
        Expected payload:
        {
            "lead_data": {
                // Lead information to analyze
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
            quality_score = ai_service.calculate_lead_quality_score(lead_data)
            
            # Add timestamp
            quality_score['validation_metadata']['last_calculated'] = timezone.now().isoformat()
            
            return Response({
                "success": True,
                "quality_score": quality_score,
                "calculated_at": timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error calculating lead quality score: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to calculate lead quality score: {str(e)}",
                    "error_code": "QUALITY_SCORE_FAILED"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class SalesStrategyView(APIView):
    """API endpoint for generating sales strategy recommendations"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Generate tailored sales strategy recommendations
        
        Expected payload:
        {
            "lead_data": {
                // Lead information
            },
            "quality_score": {
                // Optional pre-calculated quality score
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
            
            quality_score = request.data.get('quality_score')
            
            ai_service = GeminiAIService()
            sales_strategy = ai_service.generate_sales_strategy(lead_data, quality_score)
            
            # Add timestamp
            sales_strategy['strategy_metadata']['last_generated'] = timezone.now().isoformat()
            
            return Response({
                "success": True,
                "sales_strategy": sales_strategy,
                "generated_at": timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating sales strategy: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to generate sales strategy: {str(e)}",
                    "error_code": "SALES_STRATEGY_FAILED"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class IndustryInsightsView(APIView):
    """API endpoint for generating industry-specific insights"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Generate industry-specific insights and best practices
        
        Expected payload:
        {
            "lead_data": {
                // Lead information with industry context
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
            industry_insights = ai_service.generate_industry_insights(lead_data)
            
            # Add timestamp
            industry_insights['insights_metadata']['last_generated'] = timezone.now().isoformat()
            
            return Response({
                "success": True,
                "industry_insights": industry_insights,
                "generated_at": timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating industry insights: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to generate industry insights: {str(e)}",
                    "error_code": "INDUSTRY_INSIGHTS_FAILED"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@m
ethod_decorator(csrf_exempt, name='dispatch')
class ComprehensiveRecommendationsView(APIView):
    """API endpoint for generating comprehensive sales recommendations with all components"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Generate comprehensive sales recommendations including quality score, strategy, and insights
        
        Expected payload:
        {
            "lead_data": {
                // Lead information to analyze
            },
            "include_quality_score": true,
            "include_sales_strategy": true,
            "include_industry_insights": true,
            "include_next_steps": true
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
            
            # Get optional flags
            include_quality_score = request.data.get('include_quality_score', True)
            include_sales_strategy = request.data.get('include_sales_strategy', True)
            include_industry_insights = request.data.get('include_industry_insights', True)
            include_next_steps = request.data.get('include_next_steps', True)
            
            ai_service = GeminiAIService()
            
            # Initialize response structure
            comprehensive_recommendations = {
                "success": True,
                "lead_analysis": {
                    "lead_data": lead_data,
                    "analysis_timestamp": timezone.now().isoformat()
                }
            }
            
            # Generate quality score if requested
            quality_score = None
            if include_quality_score:
                quality_score = ai_service.calculate_lead_quality_score(lead_data)
                quality_score['validation_metadata']['last_calculated'] = timezone.now().isoformat()
                comprehensive_recommendations['quality_score'] = quality_score
            
            # Generate sales strategy if requested
            if include_sales_strategy:
                sales_strategy = ai_service.generate_sales_strategy(lead_data, quality_score)
                sales_strategy['strategy_metadata']['last_generated'] = timezone.now().isoformat()
                comprehensive_recommendations['sales_strategy'] = sales_strategy
            
            # Generate industry insights if requested
            if include_industry_insights:
                industry_insights = ai_service.generate_industry_insights(lead_data)
                industry_insights['insights_metadata']['last_generated'] = timezone.now().isoformat()
                comprehensive_recommendations['industry_insights'] = industry_insights
            
            # Generate next steps and recommendations if requested
            if include_next_steps:
                context = {
                    'quality_score': quality_score,
                    'user_preferences': request.data.get('user_preferences', {})
                }
                recommendations = ai_service.generate_recommendations(lead_data, context)
                comprehensive_recommendations['recommendations'] = recommendations
            
            # Add overall analysis metadata
            comprehensive_recommendations['analysis_metadata'] = {
                "components_included": {
                    "quality_score": include_quality_score,
                    "sales_strategy": include_sales_strategy,
                    "industry_insights": include_industry_insights,
                    "next_steps": include_next_steps
                },
                "overall_confidence": self._calculate_overall_analysis_confidence(comprehensive_recommendations),
                "processing_time": None,  # Could be calculated if needed
                "ai_model": "gemini-1.5-flash",
                "analysis_version": "1.0"
            }
            
            return Response(comprehensive_recommendations, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating comprehensive recommendations: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to generate comprehensive recommendations: {str(e)}",
                    "error_code": "COMPREHENSIVE_RECOMMENDATIONS_FAILED"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _calculate_overall_analysis_confidence(self, analysis: dict) -> float:
        """Calculate overall confidence score for the comprehensive analysis"""
        confidence_scores = []
        
        # Collect confidence scores from different components
        if 'quality_score' in analysis:
            quality_meta = analysis['quality_score'].get('validation_metadata', {})
            confidence_scores.append(quality_meta.get('confidence_level', 50))
        
        if 'sales_strategy' in analysis:
            strategy_meta = analysis['sales_strategy'].get('strategy_metadata', {})
            confidence_scores.append(strategy_meta.get('confidence_score', 50))
        
        if 'industry_insights' in analysis:
            insights_meta = analysis['industry_insights'].get('insights_metadata', {})
            confidence_scores.append(insights_meta.get('confidence_score', 50))
        
        if 'recommendations' in analysis:
            rec_confidence = analysis['recommendations'].get('recommendation_confidence', 50)
            confidence_scores.append(rec_confidence)
        
        # Calculate average confidence if we have scores, otherwise return default
        if confidence_scores:
            return sum(confidence_scores) / len(confidence_scores)
        else:
            return 60.0  # Default confidence


@method_decorator(csrf_exempt, name='dispatch')
class NextStepsRecommendationsView(APIView):
    """API endpoint specifically for generating next steps and action recommendations"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Generate specific next steps and action recommendations
        
        Expected payload:
        {
            "lead_data": {
                // Lead information
            },
            "current_stage": "prospecting|qualification|proposal|negotiation",
            "priority_focus": "speed|quality|relationship|competitive",
            "constraints": {
                "timeline": "urgent|normal|flexible",
                "resources": "limited|normal|extensive"
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
            
            current_stage = request.data.get('current_stage', 'prospecting')
            priority_focus = request.data.get('priority_focus', 'quality')
            constraints = request.data.get('constraints', {})
            
            ai_service = GeminiAIService()
            
            # Enhanced context for next steps generation
            context = {
                'current_stage': current_stage,
                'priority_focus': priority_focus,
                'constraints': constraints,
                'user_preferences': request.data.get('user_preferences', {})
            }
            
            # Generate targeted recommendations
            recommendations = ai_service.generate_recommendations(lead_data, context)
            
            return Response({
                "success": True,
                "recommendations": recommendations,
                "context_applied": context,
                "generated_at": timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating next steps recommendations: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to generate next steps: {str(e)}",
                    "error_code": "NEXT_STEPS_FAILED"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )