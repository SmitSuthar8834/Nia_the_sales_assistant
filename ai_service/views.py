import logging

from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ConversationAnalysis
from .quota_tracker import quota_tracker
from .services import GeminiAIService

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class DebugTestView(APIView):
    """Debug endpoint to test API functionality"""

    permission_classes = []  # No authentication required

    def get(self, request):
        """Simple GET test"""
        return Response(
            {
                "success": True,
                "message": "API is working",
                "timestamp": timezone.now().isoformat(),
            }
        )

    def post(self, request):
        """Test POST with conversation analysis - no database save"""
        try:
            conversation_text = request.data.get(
                "conversation_text",
                "Test conversation with John from Acme Corp about CRM needs.",
            )
            context = request.data.get("context", {})

            # Check if this is a simple test or full analysis
            simple_test = request.data.get("simple_test", False)

            if simple_test:
                # Return a simple mock response for quick testing
                return Response(
                    {
                        "success": True,
                        "message": "Simple test successful",
                        "input": conversation_text,
                        "timestamp": timezone.now().isoformat(),
                    }
                )

            ai_service = GeminiAIService()

            # Extract lead information
            extracted_data = ai_service.extract_lead_info(conversation_text, context)
            extracted_data["extraction_metadata"][
                "extraction_timestamp"
            ] = timezone.now().isoformat()

            # Validate extracted data
            validation_results = ai_service.validate_extracted_data(extracted_data)

            # Extract entities
            entities = ai_service.extract_entities(conversation_text)

            # Generate recommendations
            recommendations = ai_service.generate_recommendations(
                extracted_data, context
            )

            # Return the same structure as the main analyze endpoint
            return Response(
                {
                    "success": True,
                    "analysis_id": None,
                    "lead_information": extracted_data,
                    "validation": validation_results,
                    "entities": entities,
                    "recommendations": recommendations,
                    "processing_metadata": {
                        "processed_at": timezone.now().isoformat(),
                        "processing_time_ms": None,
                        "ai_model": "gemini-1.5-flash",
                        "extraction_version": "2.0",
                    },
                }
            )
        except Exception as e:
            logger.error(f"Debug endpoint error: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": str(e),
                    "timestamp": timezone.now().isoformat(),
                },
                status=500,
            )


class LeadPagination(PageNumberPagination):
    """Custom pagination for lead list views"""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


@method_decorator(csrf_exempt, name="dispatch")
class AnalyzeConversationView(APIView):
    """Enhanced API endpoint to analyze conversation text and extract lead information"""

    permission_classes = []  # Temporarily disable authentication for testing

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
            conversation_text = request.data.get("conversation_text", "").strip()
            if not conversation_text:
                return Response(
                    {
                        "success": False,
                        "error": "conversation_text is required and cannot be empty",
                        "error_code": "MISSING_CONVERSATION_TEXT",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get optional parameters
            context = request.data.get("context", {})
            extract_entities = request.data.get("extract_entities", True)
            generate_recommendations = request.data.get(
                "generate_recommendations", True
            )

            # Initialize AI service
            ai_service = GeminiAIService()

            # Extract lead information with context
            extracted_data = ai_service.extract_lead_info(conversation_text, context)

            # Add extraction timestamp
            extracted_data["extraction_metadata"][
                "extraction_timestamp"
            ] = timezone.now().isoformat()

            # Validate extracted data
            validation_results = ai_service.validate_extracted_data(extracted_data)

            # Extract entities if requested
            entities = {}
            if extract_entities:
                entities = ai_service.extract_entities(conversation_text)

            # Generate recommendations if requested
            recommendations = {}
            if generate_recommendations:
                recommendations = ai_service.generate_recommendations(
                    extracted_data, context
                )

            # Prepare response data
            response_data = {
                "success": True,
                "analysis_id": None,  # Will be set after saving
                "lead_information": extracted_data,
                "validation": validation_results,
                "entities": entities if extract_entities else None,
                "recommendations": (
                    recommendations if generate_recommendations else None
                ),
                "processing_metadata": {
                    "processed_at": timezone.now().isoformat(),
                    "processing_time_ms": None,  # Could be calculated if needed
                    "ai_model": "gemini-1.5-flash",
                    "extraction_version": "2.0",
                },
            }

            # Save analysis to database (only if user is authenticated)
            analysis_id = None
            if hasattr(request, "user") and request.user.is_authenticated:
                try:
                    analysis = ConversationAnalysis.objects.create(
                        user=request.user,
                        conversation_text=conversation_text,
                        extracted_data={
                            "lead_info": extracted_data,
                            "validation": validation_results,
                            "entities": entities,
                            "recommendations": recommendations,
                            "context": context,
                        },
                    )
                    analysis_id = str(analysis.id)
                except Exception as e:
                    logger.warning(f"Failed to save analysis to database: {e}")
            else:
                # For testing without authentication, skip database save
                logger.info("Skipping database save - no authenticated user")

            response_data["analysis_id"] = analysis_id

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error analyzing conversation: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to analyze conversation: {str(e)}",
                    "error_code": "ANALYSIS_FAILED",
                    "timestamp": timezone.now().isoformat(),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
class TestGeminiConnectionView(APIView):
    """API endpoint to test Gemini AI connection"""

    permission_classes = []  # Temporarily disable authentication for testing

    def get(self, request):
        """Test the connection to Gemini AI"""
        try:
            ai_service = GeminiAIService()
            result = ai_service.test_connection()

            if result["success"]:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        except Exception as e:
            logger.error(f"Error testing Gemini connection: {e}")
            return Response(
                {"error": f"Connection test failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
class GeminiQuotaStatusView(APIView):
    """API endpoint to check Gemini API quota status"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current Gemini API quota usage and status"""
        try:
            # Get current usage statistics
            usage = quota_tracker.get_current_usage()
            status_info = quota_tracker.get_quota_status()

            return Response(
                {
                    "success": True,
                    "quota_status": {
                        "healthy": status_info["healthy"],
                        "warnings": status_info["warnings"],
                        "errors": status_info["errors"],
                        "usage": usage,
                        "recommendations": [],
                    },
                    "timestamp": timezone.now().isoformat(),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error checking quota status: {e}")
            return Response(
                {
                    "success": False,
                    "error": f"Failed to check quota status: {str(e)}",
                    "error_code": "QUOTA_CHECK_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        """Reset quota counters (admin only)"""
        try:
            # Check if user has admin permissions (you can customize this)
            if not request.user.is_staff:
                return Response(
                    {"error": "Admin permissions required"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            quota_type = request.data.get("quota_type", "all")
            quota_tracker.reset_quota(quota_type)

            return Response(
                {
                    "success": True,
                    "message": f"Quota counters reset: {quota_type}",
                    "timestamp": timezone.now().isoformat(),
                }
            )

        except Exception as e:
            logger.error(f"Error resetting quota: {e}")
            return Response(
                {"error": f"Failed to reset quota: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
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
            conversation_text = request.data.get("conversation_text", "").strip()
            if not conversation_text:
                return Response(
                    {
                        "success": False,
                        "error": "conversation_text is required",
                        "error_code": "MISSING_CONVERSATION_TEXT",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            context = request.data.get("context", {})
            ai_service = GeminiAIService()

            # Extract lead information
            lead_info = ai_service.extract_lead_info(conversation_text, context)
            lead_info["extraction_metadata"][
                "extraction_timestamp"
            ] = timezone.now().isoformat()

            # Validate the data
            validation = ai_service.validate_extracted_data(lead_info)

            return Response(
                {
                    "success": True,
                    "lead_information": lead_info,
                    "validation": validation,
                    "extracted_at": timezone.now().isoformat(),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error extracting lead info: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to extract lead information: {str(e)}",
                    "error_code": "EXTRACTION_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
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
            text = request.data.get("text", "").strip()
            if not text:
                return Response(
                    {
                        "success": False,
                        "error": "text is required",
                        "error_code": "MISSING_TEXT",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            ai_service = GeminiAIService()
            entities = ai_service.extract_entities(text)

            return Response(
                {
                    "success": True,
                    "entities": entities,
                    "extracted_at": timezone.now().isoformat(),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error extracting entities: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to extract entities: {str(e)}",
                    "error_code": "ENTITY_EXTRACTION_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
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
            lead_data = request.data.get("lead_data", {})
            if not lead_data:
                return Response(
                    {
                        "success": False,
                        "error": "lead_data is required",
                        "error_code": "MISSING_LEAD_DATA",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            ai_service = GeminiAIService()
            validation_results = ai_service.validate_extracted_data(lead_data)

            return Response(
                {
                    "success": True,
                    "validation": validation_results,
                    "validated_at": timezone.now().isoformat(),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error validating lead data: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to validate lead data: {str(e)}",
                    "error_code": "VALIDATION_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
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
            lead_data = request.data.get("lead_data", {})
            if not lead_data:
                return Response(
                    {
                        "success": False,
                        "error": "lead_data is required",
                        "error_code": "MISSING_LEAD_DATA",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            ai_service = GeminiAIService()
            quality_score = ai_service.calculate_lead_quality_score(lead_data)

            # Add timestamp
            quality_score["validation_metadata"][
                "last_calculated"
            ] = timezone.now().isoformat()

            return Response(
                {
                    "success": True,
                    "quality_score": quality_score,
                    "calculated_at": timezone.now().isoformat(),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error calculating lead quality score: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to calculate lead quality score: {str(e)}",
                    "error_code": "QUALITY_SCORE_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
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
            lead_data = request.data.get("lead_data", {})
            if not lead_data:
                return Response(
                    {
                        "success": False,
                        "error": "lead_data is required",
                        "error_code": "MISSING_LEAD_DATA",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            quality_score = request.data.get("quality_score")

            ai_service = GeminiAIService()
            sales_strategy = ai_service.generate_sales_strategy(
                lead_data, quality_score
            )

            # Add timestamp
            sales_strategy["strategy_metadata"][
                "last_generated"
            ] = timezone.now().isoformat()

            return Response(
                {
                    "success": True,
                    "sales_strategy": sales_strategy,
                    "generated_at": timezone.now().isoformat(),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error generating sales strategy: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to generate sales strategy: {str(e)}",
                    "error_code": "SALES_STRATEGY_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
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
            lead_data = request.data.get("lead_data", {})
            if not lead_data:
                return Response(
                    {
                        "success": False,
                        "error": "lead_data is required",
                        "error_code": "MISSING_LEAD_DATA",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            ai_service = GeminiAIService()
            industry_insights = ai_service.generate_industry_insights(lead_data)

            # Add timestamp
            industry_insights["insights_metadata"][
                "last_generated"
            ] = timezone.now().isoformat()

            return Response(
                {
                    "success": True,
                    "industry_insights": industry_insights,
                    "generated_at": timezone.now().isoformat(),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error generating industry insights: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to generate industry insights: {str(e)}",
                    "error_code": "INDUSTRY_INSIGHTS_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ConversationHistoryView(APIView):
    """Enhanced API endpoint to retrieve conversation analysis history"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get conversation analysis history for the current user with enhanced formatting"""
        try:
            # Get query parameters
            limit = int(request.query_params.get("limit", 10))
            offset = int(request.query_params.get("offset", 0))

            analyses = ConversationAnalysis.objects.filter(user=request.user).order_by(
                "-analysis_timestamp"
            )[offset : offset + limit]

            history = []
            for analysis in analyses:
                extracted_data = analysis.extracted_data
                lead_info = extracted_data.get("lead_info", {})

                history.append(
                    {
                        "id": str(analysis.id),
                        "timestamp": analysis.analysis_timestamp.isoformat(),
                        "conversation_preview": (
                            analysis.conversation_text[:100] + "..."
                            if len(analysis.conversation_text) > 100
                            else analysis.conversation_text
                        ),
                        "company_name": lead_info.get("company_name"),
                        "contact_name": lead_info.get("contact_details", {}).get(
                            "name"
                        ),
                        "confidence_score": lead_info.get(
                            "extraction_metadata", {}
                        ).get("confidence_score", 0),
                        "data_completeness": lead_info.get(
                            "extraction_metadata", {}
                        ).get("data_completeness", 0),
                        "has_recommendations": bool(
                            extracted_data.get("recommendations")
                        ),
                        "validation_status": extracted_data.get("validation", {}).get(
                            "is_valid", False
                        ),
                    }
                )

            return Response(
                {
                    "success": True,
                    "history": history,
                    "count": len(history),
                    "pagination": {
                        "limit": limit,
                        "offset": offset,
                        "has_more": len(analyses) == limit,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to retrieve history: {str(e)}",
                    "error_code": "HISTORY_RETRIEVAL_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
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
            lead_data = request.data.get("lead_data", {})
            if not lead_data:
                return Response(
                    {
                        "success": False,
                        "error": "lead_data is required",
                        "error_code": "MISSING_LEAD_DATA",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            ai_service = GeminiAIService()
            quality_score = ai_service.calculate_lead_quality_score(lead_data)

            # Add timestamp
            quality_score["validation_metadata"][
                "last_calculated"
            ] = timezone.now().isoformat()

            return Response(
                {
                    "success": True,
                    "quality_score": quality_score,
                    "calculated_at": timezone.now().isoformat(),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error calculating lead quality score: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to calculate lead quality score: {str(e)}",
                    "error_code": "QUALITY_SCORE_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
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
            lead_data = request.data.get("lead_data", {})
            if not lead_data:
                return Response(
                    {
                        "success": False,
                        "error": "lead_data is required",
                        "error_code": "MISSING_LEAD_DATA",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            quality_score = request.data.get("quality_score")

            ai_service = GeminiAIService()
            sales_strategy = ai_service.generate_sales_strategy(
                lead_data, quality_score
            )

            # Add timestamp
            sales_strategy["strategy_metadata"][
                "last_generated"
            ] = timezone.now().isoformat()

            return Response(
                {
                    "success": True,
                    "sales_strategy": sales_strategy,
                    "generated_at": timezone.now().isoformat(),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error generating sales strategy: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to generate sales strategy: {str(e)}",
                    "error_code": "SALES_STRATEGY_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
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
            lead_data = request.data.get("lead_data", {})
            if not lead_data:
                return Response(
                    {
                        "success": False,
                        "error": "lead_data is required",
                        "error_code": "MISSING_LEAD_DATA",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            ai_service = GeminiAIService()
            industry_insights = ai_service.generate_industry_insights(lead_data)

            # Add timestamp
            industry_insights["insights_metadata"][
                "last_generated"
            ] = timezone.now().isoformat()

            return Response(
                {
                    "success": True,
                    "industry_insights": industry_insights,
                    "generated_at": timezone.now().isoformat(),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error generating industry insights: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to generate industry insights: {str(e)}",
                    "error_code": "INDUSTRY_INSIGHTS_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
class ComprehensiveRecommendationsView(APIView):
    """API endpoint for generating comprehensive sales recommendations with all components"""

    permission_classes = []  # Temporarily disable authentication for testing

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
            lead_data = request.data.get("lead_data", {})
            if not lead_data:
                return Response(
                    {
                        "success": False,
                        "error": "lead_data is required",
                        "error_code": "MISSING_LEAD_DATA",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get optional flags
            include_quality_score = request.data.get("include_quality_score", True)
            include_sales_strategy = request.data.get("include_sales_strategy", True)
            include_industry_insights = request.data.get(
                "include_industry_insights", True
            )
            include_next_steps = request.data.get("include_next_steps", True)

            ai_service = GeminiAIService()

            # Initialize response structure
            comprehensive_recommendations = {
                "success": True,
                "lead_analysis": {
                    "lead_data": lead_data,
                    "analysis_timestamp": timezone.now().isoformat(),
                },
            }

            # Generate quality score if requested
            quality_score = None
            if include_quality_score:
                quality_score = ai_service.calculate_lead_quality_score(lead_data)
                quality_score["validation_metadata"][
                    "last_calculated"
                ] = timezone.now().isoformat()
                comprehensive_recommendations["quality_score"] = quality_score

            # Generate sales strategy if requested
            if include_sales_strategy:
                sales_strategy = ai_service.generate_sales_strategy(
                    lead_data, quality_score
                )
                sales_strategy["strategy_metadata"][
                    "last_generated"
                ] = timezone.now().isoformat()
                comprehensive_recommendations["sales_strategy"] = sales_strategy

            # Generate industry insights if requested
            if include_industry_insights:
                industry_insights = ai_service.generate_industry_insights(lead_data)
                industry_insights["insights_metadata"][
                    "last_generated"
                ] = timezone.now().isoformat()
                comprehensive_recommendations["industry_insights"] = industry_insights

            # Generate next steps and recommendations if requested
            if include_next_steps:
                context = {
                    "quality_score": quality_score,
                    "user_preferences": request.data.get("user_preferences", {}),
                }
                recommendations = ai_service.generate_recommendations(
                    lead_data, context
                )
                comprehensive_recommendations["recommendations"] = recommendations

            # Add overall analysis metadata
            comprehensive_recommendations["analysis_metadata"] = {
                "components_included": {
                    "quality_score": include_quality_score,
                    "sales_strategy": include_sales_strategy,
                    "industry_insights": include_industry_insights,
                    "next_steps": include_next_steps,
                },
                "overall_confidence": self._calculate_overall_analysis_confidence(
                    comprehensive_recommendations
                ),
                "processing_time": None,  # Could be calculated if needed
                "ai_model": "gemini-1.5-flash",
                "analysis_version": "1.0",
            }

            return Response(comprehensive_recommendations, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(
                f"Error generating comprehensive recommendations: {e}", exc_info=True
            )
            return Response(
                {
                    "success": False,
                    "error": f"Failed to generate comprehensive recommendations: {str(e)}",
                    "error_code": "COMPREHENSIVE_RECOMMENDATIONS_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _calculate_overall_analysis_confidence(self, analysis: dict) -> float:
        """Calculate overall confidence score for the comprehensive analysis"""
        confidence_scores = []

        # Collect confidence scores from different components
        if "quality_score" in analysis:
            quality_meta = analysis["quality_score"].get("validation_metadata", {})
            confidence_scores.append(quality_meta.get("confidence_level", 50))

        if "sales_strategy" in analysis:
            strategy_meta = analysis["sales_strategy"].get("strategy_metadata", {})
            confidence_scores.append(strategy_meta.get("confidence_score", 50))

        if "industry_insights" in analysis:
            insights_meta = analysis["industry_insights"].get("insights_metadata", {})
            confidence_scores.append(insights_meta.get("confidence_score", 50))

        if "recommendations" in analysis:
            rec_confidence = analysis["recommendations"].get(
                "recommendation_confidence", 50
            )
            confidence_scores.append(rec_confidence)

        # Calculate average confidence if we have scores, otherwise return default
        if confidence_scores:
            return sum(confidence_scores) / len(confidence_scores)
        else:
            return 60.0  # Default confidence


@method_decorator(csrf_exempt, name="dispatch")
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
            lead_data = request.data.get("lead_data", {})
            if not lead_data:
                return Response(
                    {
                        "success": False,
                        "error": "lead_data is required",
                        "error_code": "MISSING_LEAD_DATA",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            current_stage = request.data.get("current_stage", "prospecting")
            priority_focus = request.data.get("priority_focus", "quality")
            constraints = request.data.get("constraints", {})

            ai_service = GeminiAIService()

            # Enhanced context for next steps generation
            context = {
                "current_stage": current_stage,
                "priority_focus": priority_focus,
                "constraints": constraints,
                "user_preferences": request.data.get("user_preferences", {}),
            }

            # Generate targeted recommendations
            recommendations = ai_service.generate_recommendations(lead_data, context)

            return Response(
                {
                    "success": True,
                    "recommendations": recommendations,
                    "context_applied": context,
                    "generated_at": timezone.now().isoformat(),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(
                f"Error generating next steps recommendations: {e}", exc_info=True
            )
            return Response(
                {
                    "success": False,
                    "error": f"Failed to generate next steps: {str(e)}",
                    "error_code": "NEXT_STEPS_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# Lead Management Views with AI Integration

from django.db import models
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination

from .models import AIInsights, Lead
from .serializers import (
    AIInsightsSerializer,
    LeadCreateSerializer,
    LeadListSerializer,
    LeadSerializer,
    LeadUpdateSerializer,
)
from .tasks import refresh_lead_insights


class LeadPagination(PageNumberPagination):
    """Custom pagination for leads"""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class LeadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing leads with AI insights integration

    Provides CRUD operations for leads with automatic AI analysis
    """

    permission_classes = []  # Temporarily disable authentication for testing
    pagination_class = LeadPagination

    def get_queryset(self):
        """Get leads for the authenticated user with optional filtering"""
        # For testing without authentication, get all leads or create a test user
        if hasattr(self.request, "user") and self.request.user.is_authenticated:
            queryset = Lead.objects.filter(user=self.request.user).select_related(
                "ai_insights"
            )
        else:
            # For testing, return all leads
            queryset = Lead.objects.all().select_related("ai_insights")

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by quality tier
        quality_filter = self.request.query_params.get("quality_tier")
        if quality_filter:
            queryset = queryset.filter(ai_insights__quality_tier=quality_filter)

        # Search by company name or contact name
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(company_name__icontains=search)
                | Q(contact_info__name__icontains=search)
                | Q(contact_info__email__icontains=search)
            )

        # Filter by urgency level
        urgency_filter = self.request.query_params.get("urgency")
        if urgency_filter:
            queryset = queryset.filter(urgency_level=urgency_filter)

        # Order by creation date (newest first) or lead score
        ordering = self.request.query_params.get("ordering", "-created_at")
        if ordering == "lead_score":
            queryset = queryset.order_by("-ai_insights__lead_score", "-created_at")
        elif ordering == "-lead_score":
            queryset = queryset.order_by("ai_insights__lead_score", "-created_at")
        else:
            queryset = queryset.order_by(ordering)

        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == "create":
            return LeadCreateSerializer
        elif self.action == "update" or self.action == "partial_update":
            return LeadUpdateSerializer
        elif self.action == "list":
            return LeadListSerializer
        else:
            return LeadSerializer

    def create(self, request, *args, **kwargs):
        """Create a new lead with optional AI analysis"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lead = serializer.save()

        # Return full lead data with AI insights placeholder
        response_serializer = LeadSerializer(lead)

        return Response(
            {
                "status": "success",
                "message": "Lead created successfully",
                "lead": response_serializer.data,
                "ai_analysis_triggered": bool(request.data.get("conversation_text")),
            },
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        """Update a lead with optional AI re-analysis"""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        lead = serializer.save()

        # Return full lead data
        response_serializer = LeadSerializer(lead)

        return Response(
            {
                "status": "success",
                "message": "Lead updated successfully",
                "lead": response_serializer.data,
                "ai_analysis_triggered": request.data.get("trigger_ai_analysis", False),
            }
        )

    @action(detail=True, methods=["post"])
    def refresh_insights(self, request, pk=None):
        """Refresh AI insights for a specific lead"""
        lead = self.get_object()

        if not lead.conversation_history:
            return Response(
                {"error": "No conversation history available for AI analysis"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Trigger AI analysis
        task = refresh_lead_insights.delay(str(lead.id))

        return Response(
            {
                "status": "success",
                "message": "AI insights refresh triggered",
                "task_id": task.id,
            }
        )

    @action(detail=True, methods=["get"])
    def insights(self, request, pk=None):
        """Get detailed AI insights for a specific lead"""
        lead = self.get_object()

        try:
            insights = lead.ai_insights
            serializer = AIInsightsSerializer(insights)
            return Response({"status": "success", "insights": serializer.data})
        except AIInsights.DoesNotExist:
            return Response(
                {
                    "status": "not_found",
                    "message": "No AI insights available for this lead",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["get"])
    def high_priority(self, request):
        """Get high-priority leads that need immediate attention"""
        queryset = (
            self.get_queryset()
            .filter(
                Q(ai_insights__quality_tier="high")
                | Q(urgency_level="high")
                | Q(ai_insights__conversion_probability__gte=70)
                | Q(ai_insights__competitive_risk="high")
            )
            .order_by("-ai_insights__lead_score", "-created_at")
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = LeadListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = LeadListSerializer(queryset, many=True)
        return Response({"status": "success", "high_priority_leads": serializer.data})

    @action(detail=False, methods=["post"])
    def bulk_refresh_insights(self, request):
        """Refresh AI insights for multiple leads"""
        lead_ids = request.data.get("lead_ids", [])

        if not lead_ids:
            return Response(
                {"error": "lead_ids list is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify all leads belong to the user
        user_leads = self.get_queryset().filter(id__in=lead_ids)
        valid_lead_ids = [str(lead.id) for lead in user_leads]

        if len(valid_lead_ids) != len(lead_ids):
            return Response(
                {"error": "Some lead IDs are invalid or do not belong to you"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Trigger bulk refresh
        from .tasks import bulk_refresh_insights

        task = bulk_refresh_insights.delay(valid_lead_ids)

        return Response(
            {
                "status": "success",
                "message": f"AI insights refresh triggered for {len(valid_lead_ids)} leads",
                "task_id": task.id,
                "lead_count": len(valid_lead_ids),
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class LeadAnalyticsView(APIView):
    """API endpoint for lead analytics and insights"""

    permission_classes = []  # Temporarily disable authentication for testing

    def get(self, request):
        """
        Get analytics and insights about user's leads
        """
        try:
            # Handle case where there's no authenticated user
            if hasattr(request, "user") and request.user.is_authenticated:
                user_leads = Lead.objects.filter(user=request.user).select_related(
                    "ai_insights"
                )
            else:
                # For testing, get all leads
                user_leads = Lead.objects.all().select_related("ai_insights")

            # Basic statistics
            total_leads = user_leads.count()
            leads_with_insights = user_leads.filter(ai_insights__isnull=False).count()

            # Status distribution
            status_distribution = {}
            for status_choice in Lead.Status.choices:
                status_distribution[status_choice[0]] = user_leads.filter(
                    status=status_choice[0]
                ).count()

            # Quality tier distribution
            quality_distribution = {}
            for quality_choice in AIInsights.QualityTier.choices:
                quality_distribution[quality_choice[0]] = user_leads.filter(
                    ai_insights__quality_tier=quality_choice[0]
                ).count()

            # Average lead score
            if hasattr(request, "user") and request.user.is_authenticated:
                insights_queryset = AIInsights.objects.filter(lead__user=request.user)
            else:
                # For testing, get all insights
                insights_queryset = AIInsights.objects.all()

            avg_lead_score = (
                insights_queryset.aggregate(avg_score=models.Avg("lead_score"))[
                    "avg_score"
                ]
                or 0
            )

            # High priority leads count
            high_priority_count = user_leads.filter(
                Q(ai_insights__quality_tier="high")
                | Q(urgency_level="high")
                | Q(ai_insights__conversion_probability__gte=70)
            ).count()

            return Response(
                {
                    "status": "success",
                    "analytics": {
                        "total_leads": total_leads,
                        "leads_with_insights": leads_with_insights,
                        "insights_coverage": (
                            (leads_with_insights / total_leads * 100)
                            if total_leads > 0
                            else 0
                        ),
                        "status_distribution": status_distribution,
                        "quality_distribution": quality_distribution,
                        "average_lead_score": round(avg_lead_score, 2),
                        "high_priority_count": high_priority_count,
                    },
                }
            )

        except Exception as e:
            logger.error(f"Error generating lead analytics: {e}")
            return Response(
                {"error": "Failed to generate analytics", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# Opportunity Conversion Intelligence Views


@method_decorator(csrf_exempt, name="dispatch")
class OpportunityConversionAnalysisView(APIView):
    """API endpoint for analyzing lead-to-opportunity conversion potential"""

    permission_classes = []  # Temporarily disable authentication for testing

    def post(self, request):
        """
        Analyze lead's potential for conversion to opportunity

        Expected payload:
        {
            "lead_data": {
                // Lead information to analyze
            },
            "historical_data": {
                // Optional historical conversion data
            }
        }
        """
        try:
            lead_data = request.data.get("lead_data", {})
            if not lead_data:
                return Response(
                    {
                        "success": False,
                        "error": "lead_data is required",
                        "error_code": "MISSING_LEAD_DATA",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            historical_data = request.data.get("historical_data", {})

            ai_service = GeminiAIService()
            conversion_analysis = ai_service.analyze_opportunity_conversion_potential(
                lead_data, historical_data
            )

            return Response(
                {
                    "success": True,
                    "conversion_analysis": conversion_analysis,
                    "analyzed_at": timezone.now().isoformat(),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(
                f"Error analyzing opportunity conversion potential: {e}", exc_info=True
            )
            return Response(
                {
                    "success": False,
                    "error": f"Failed to analyze conversion potential: {str(e)}",
                    "error_code": "CONVERSION_ANALYSIS_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
class DealSizeTimelinePredictionView(APIView):
    """API endpoint for predicting deal size and timeline"""

    permission_classes = []  # Temporarily disable authentication for testing

    def post(self, request):
        """
        Predict deal size range and sales timeline

        Expected payload:
        {
            "lead_data": {
                // Lead information
            },
            "opportunity_data": {
                // Optional existing opportunity data
            }
        }
        """
        try:
            lead_data = request.data.get("lead_data", {})
            if not lead_data:
                return Response(
                    {
                        "success": False,
                        "error": "lead_data is required",
                        "error_code": "MISSING_LEAD_DATA",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            opportunity_data = request.data.get("opportunity_data", {})

            ai_service = GeminiAIService()
            predictions = ai_service.predict_deal_size_and_timeline(
                lead_data, opportunity_data
            )

            return Response(
                {
                    "success": True,
                    "predictions": predictions,
                    "predicted_at": timezone.now().isoformat(),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error predicting deal size and timeline: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to predict deal size and timeline: {str(e)}",
                    "error_code": "PREDICTION_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
class SalesStageRecommendationView(APIView):
    """API endpoint for recommending sales stage and advancement strategy"""

    permission_classes = []  # Temporarily disable authentication for testing

    def post(self, request):
        """
        Recommend appropriate sales stage and advancement strategy

        Expected payload:
        {
            "lead_data": {
                // Original lead information
            },
            "opportunity_data": {
                // Current opportunity data
            },
            "current_stage": "prospecting|qualification|proposal|negotiation"
        }
        """
        try:
            lead_data = request.data.get("lead_data", {})
            opportunity_data = request.data.get("opportunity_data", {})

            if not lead_data or not opportunity_data:
                return Response(
                    {
                        "success": False,
                        "error": "Both lead_data and opportunity_data are required",
                        "error_code": "MISSING_DATA",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            current_stage = request.data.get("current_stage")

            ai_service = GeminiAIService()
            stage_recommendations = ai_service.recommend_sales_stage(
                lead_data, opportunity_data, current_stage
            )

            return Response(
                {
                    "success": True,
                    "stage_recommendations": stage_recommendations,
                    "recommended_at": timezone.now().isoformat(),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error recommending sales stage: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to recommend sales stage: {str(e)}",
                    "error_code": "STAGE_RECOMMENDATION_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
class RiskFactorAnalysisView(APIView):
    """API endpoint for identifying risk factors and mitigation strategies"""

    permission_classes = []  # Temporarily disable authentication for testing

    def post(self, request):
        """
        Identify potential risk factors and suggest mitigation strategies

        Expected payload:
        {
            "lead_data": {
                // Lead information
            },
            "opportunity_data": {
                // Opportunity details
            },
            "historical_data": {
                // Optional historical risk patterns
            }
        }
        """
        try:
            lead_data = request.data.get("lead_data", {})
            opportunity_data = request.data.get("opportunity_data", {})

            if not lead_data or not opportunity_data:
                return Response(
                    {
                        "success": False,
                        "error": "Both lead_data and opportunity_data are required",
                        "error_code": "MISSING_DATA",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            historical_data = request.data.get("historical_data", {})

            ai_service = GeminiAIService()
            risk_analysis = ai_service.identify_risk_factors_and_mitigation(
                lead_data, opportunity_data, historical_data
            )

            return Response(
                {
                    "success": True,
                    "risk_analysis": risk_analysis,
                    "analyzed_at": timezone.now().isoformat(),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error analyzing risk factors: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to analyze risk factors: {str(e)}",
                    "error_code": "RISK_ANALYSIS_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
class HistoricalPatternAnalysisView(APIView):
    """API endpoint for analyzing historical patterns to improve predictions"""

    permission_classes = []  # Temporarily disable authentication for testing

    def post(self, request):
        """
        Analyze historical data patterns for improved predictions

        Expected payload:
        {
            "lead_data": {
                // Current lead data for comparison
            },
            "user_id": "optional_user_id_for_personalized_analysis"
        }
        """
        try:
            lead_data = request.data.get("lead_data", {})
            if not lead_data:
                return Response(
                    {
                        "success": False,
                        "error": "lead_data is required",
                        "error_code": "MISSING_LEAD_DATA",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user_id = request.data.get("user_id")

            ai_service = GeminiAIService()
            historical_analysis = ai_service.analyze_historical_patterns(
                lead_data, user_id
            )

            return Response(
                {
                    "success": True,
                    "historical_analysis": historical_analysis,
                    "analyzed_at": timezone.now().isoformat(),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error analyzing historical patterns: {e}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": f"Failed to analyze historical patterns: {str(e)}",
                    "error_code": "HISTORICAL_ANALYSIS_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
class ComprehensiveOpportunityIntelligenceView(APIView):
    """API endpoint for comprehensive opportunity conversion intelligence analysis"""

    permission_classes = []  # Temporarily disable authentication for testing

    def post(self, request):
        """
        Generate comprehensive opportunity conversion intelligence

        Expected payload:
        {
            "lead_data": {
                // Lead information
            },
            "opportunity_data": {
                // Optional opportunity data if already exists
            },
            "include_conversion_analysis": true,
            "include_deal_predictions": true,
            "include_stage_recommendations": true,
            "include_risk_analysis": true,
            "include_historical_patterns": true
        }
        """
        try:
            lead_data = request.data.get("lead_data", {})
            if not lead_data:
                return Response(
                    {
                        "success": False,
                        "error": "lead_data is required",
                        "error_code": "MISSING_LEAD_DATA",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            opportunity_data = request.data.get("opportunity_data", {})

            # Get optional flags
            include_conversion = request.data.get("include_conversion_analysis", True)
            include_predictions = request.data.get("include_deal_predictions", True)
            include_stage_recs = request.data.get("include_stage_recommendations", True)
            include_risk = request.data.get("include_risk_analysis", True)
            include_historical = request.data.get("include_historical_patterns", True)

            ai_service = GeminiAIService()

            # Initialize comprehensive intelligence response
            intelligence = {
                "success": True,
                "lead_data": lead_data,
                "opportunity_data": opportunity_data,
                "analysis_timestamp": timezone.now().isoformat(),
            }

            # Generate conversion analysis if requested
            if include_conversion:
                historical_data = request.data.get("historical_data", {})
                conversion_analysis = (
                    ai_service.analyze_opportunity_conversion_potential(
                        lead_data, historical_data
                    )
                )
                intelligence["conversion_analysis"] = conversion_analysis

            # Generate deal predictions if requested
            if include_predictions:
                predictions = ai_service.predict_deal_size_and_timeline(
                    lead_data, opportunity_data
                )
                intelligence["deal_predictions"] = predictions

            # Generate stage recommendations if requested and opportunity data exists
            if include_stage_recs and opportunity_data:
                current_stage = opportunity_data.get("stage")
                stage_recommendations = ai_service.recommend_sales_stage(
                    lead_data, opportunity_data, current_stage
                )
                intelligence["stage_recommendations"] = stage_recommendations

            # Generate risk analysis if requested and opportunity data exists
            if include_risk and opportunity_data:
                historical_data = request.data.get("historical_data", {})
                risk_analysis = ai_service.identify_risk_factors_and_mitigation(
                    lead_data, opportunity_data, historical_data
                )
                intelligence["risk_analysis"] = risk_analysis

            # Generate historical pattern analysis if requested
            if include_historical:
                user_id = request.data.get("user_id")
                historical_analysis = ai_service.analyze_historical_patterns(
                    lead_data, user_id
                )
                intelligence["historical_analysis"] = historical_analysis

            # Add overall intelligence metadata
            intelligence["intelligence_metadata"] = {
                "components_included": {
                    "conversion_analysis": include_conversion,
                    "deal_predictions": include_predictions,
                    "stage_recommendations": include_stage_recs,
                    "risk_analysis": include_risk,
                    "historical_patterns": include_historical,
                },
                "overall_confidence": self._calculate_intelligence_confidence(
                    intelligence
                ),
                "ai_model": "gemini-1.5-flash",
                "analysis_version": "1.0",
            }

            return Response(intelligence, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(
                f"Error generating comprehensive opportunity intelligence: {e}",
                exc_info=True,
            )
            return Response(
                {
                    "success": False,
                    "error": f"Failed to generate opportunity intelligence: {str(e)}",
                    "error_code": "OPPORTUNITY_INTELLIGENCE_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _calculate_intelligence_confidence(self, intelligence: dict) -> float:
        """Calculate overall confidence score for the opportunity intelligence"""
        confidence_scores = []

        # Collect confidence scores from different components
        if "conversion_analysis" in intelligence:
            conversion_confidence = intelligence["conversion_analysis"].get(
                "conversion_confidence", 50
            )
            confidence_scores.append(conversion_confidence)

        if "deal_predictions" in intelligence:
            deal_confidence = (
                intelligence["deal_predictions"]
                .get("deal_size_prediction", {})
                .get("confidence_level", 50)
            )
            timeline_confidence = (
                intelligence["deal_predictions"]
                .get("timeline_prediction", {})
                .get("confidence_level", 50)
            )
            confidence_scores.extend([deal_confidence, timeline_confidence])

        if "stage_recommendations" in intelligence:
            stage_confidence = (
                intelligence["stage_recommendations"]
                .get("advancement_analysis", {})
                .get("advancement_confidence", 50)
            )
            confidence_scores.append(stage_confidence)

        if "risk_analysis" in intelligence:
            risk_confidence = (
                intelligence["risk_analysis"]
                .get("overall_risk_assessment", {})
                .get("confidence", 50)
            )
            confidence_scores.append(risk_confidence)

        # Calculate average confidence if we have scores, otherwise return default
        if confidence_scores:
            return sum(confidence_scores) / len(confidence_scores)
        else:
            return 65.0  # Default confidence for opportunity intelligence
