"""
Comprehensive tests for AI-powered sales recommendations engine (Task 3)
Tests for lead quality scoring, sales strategy generation, industry insights, and recommendation consistency
"""

import json
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .services import GeminiAIService

User = get_user_model()


class LeadQualityScoringTests(TestCase):
    """Test lead quality scoring functionality"""

    def setUp(self):
        self.ai_service = GeminiAIService()
        self.sample_lead_data = {
            "company_name": "TechCorp Solutions",
            "contact_details": {
                "name": "John Smith",
                "email": "john.smith@techcorp.com",
                "phone": "+1-555-123-4567",
                "title": "CTO",
                "department": "Technology",
            },
            "pain_points": [
                "Manual processes causing delays",
                "Lack of real-time visibility",
                "High operational costs",
            ],
            "requirements": [
                "Automated workflow system",
                "Real-time dashboard",
                "Cost reduction solution",
            ],
            "budget_info": "$50,000 - $100,000",
            "timeline": "Q2 2024 implementation",
            "decision_makers": ["John Smith", "Sarah Johnson (CFO)"],
            "industry": "Technology",
            "company_size": "200-500 employees",
            "urgency_level": "high",
            "current_solution": "Manual Excel-based processes",
        }

    @patch("ai_service.services.genai.GenerativeModel")
    def test_calculate_lead_quality_score_success(self, mock_model):
        """Test successful lead quality score calculation"""
        # Mock AI response
        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "overall_score": 85,
                "score_breakdown": {
                    "data_completeness": 90,
                    "engagement_level": 80,
                    "budget_fit": 85,
                    "timeline_urgency": 90,
                    "decision_authority": 75,
                    "pain_point_severity": 95,
                },
                "quality_tier": "high",
                "conversion_probability": 75,
                "estimated_deal_size": "$75,000",
                "sales_cycle_prediction": "3-4 months",
                "key_strengths": [
                    "Clear pain points identified",
                    "Budget range specified",
                    "Decision maker engaged",
                ],
                "improvement_areas": [
                    "Validate budget authority",
                    "Understand competitive landscape",
                ],
                "competitive_risk": "medium",
                "next_best_action": "Schedule technical demo",
            }
        )

        mock_model.return_value.generate_content.return_value = mock_response

        result = self.ai_service.calculate_lead_quality_score(self.sample_lead_data)

        # Verify structure and content
        self.assertIn("overall_score", result)
        self.assertIn("score_breakdown", result)
        self.assertIn("quality_tier", result)
        self.assertIn("validation_metadata", result)

        # Score might be adjusted by validation, so check it's in reasonable range
        self.assertGreaterEqual(result["overall_score"], 80)
        self.assertLessEqual(result["overall_score"], 100)
        self.assertEqual(result["quality_tier"], "high")
        self.assertIsInstance(result["score_breakdown"], dict)
        self.assertIn("confidence_level", result["validation_metadata"])

    def test_calculate_lead_quality_score_minimal_data(self):
        """Test quality score calculation with minimal lead data"""
        minimal_data = {
            "company_name": "Small Corp",
            "contact_details": {"name": "Jane Doe"},
        }

        with patch("ai_service.services.genai.GenerativeModel") as mock_model:
            # Mock a lower quality response
            mock_response = MagicMock()
            mock_response.text = json.dumps(
                {
                    "overall_score": 35,
                    "score_breakdown": {
                        "data_completeness": 20,
                        "engagement_level": 30,
                        "budget_fit": 40,
                        "timeline_urgency": 30,
                        "decision_authority": 40,
                        "pain_point_severity": 50,
                    },
                    "quality_tier": "low",
                    "conversion_probability": 15,
                    "estimated_deal_size": "Unknown",
                    "sales_cycle_prediction": "Unknown",
                    "key_strengths": ["Company name available"],
                    "improvement_areas": ["Gather more qualification data"],
                    "competitive_risk": "medium",
                    "next_best_action": "Gather more lead qualification data",
                }
            )
            mock_model.return_value.generate_content.return_value = mock_response

            result = self.ai_service.calculate_lead_quality_score(minimal_data)

            # Score should be low but might be adjusted by validation
            self.assertLessEqual(result["overall_score"], 70)
            self.assertIn(
                result["quality_tier"], ["low", "medium"]
            )  # Allow for some variation in AI response

    def test_lead_quality_score_validation(self):
        """Test validation of quality score data"""
        # Test with invalid score (should be clamped)
        invalid_data = {"overall_score": 150}  # Over 100

        with patch("ai_service.services.genai.GenerativeModel") as mock_model:
            mock_response = MagicMock()
            mock_response.text = json.dumps(invalid_data)
            mock_model.return_value.generate_content.return_value = mock_response

            result = self.ai_service.calculate_lead_quality_score(self.sample_lead_data)

            # Score should be clamped to 100
            self.assertLessEqual(result["overall_score"], 100)


class SalesStrategyGenerationTests(TestCase):
    """Test sales strategy generation functionality"""

    def setUp(self):
        self.ai_service = GeminiAIService()
        self.sample_lead_data = {
            "company_name": "Enterprise Corp",
            "industry": "Manufacturing",
            "company_size": "1000+ employees",
            "pain_points": ["Inefficient supply chain", "Quality control issues"],
            "budget_info": "$200,000+",
            "urgency_level": "high",
        }

        self.sample_quality_score = {
            "overall_score": 80,
            "quality_tier": "high",
            "conversion_probability": 70,
        }

    @patch("ai_service.services.genai.GenerativeModel")
    def test_generate_sales_strategy_success(self, mock_model):
        """Test successful sales strategy generation"""
        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "primary_strategy": "consultative",
                "approach_rationale": "High-value enterprise client requires consultative approach",
                "key_messaging": [
                    "Focus on ROI and efficiency gains",
                    "Emphasize proven track record with similar companies",
                    "Highlight implementation support",
                ],
                "objection_handling": {
                    "budget_concerns": "Demonstrate clear ROI within 12 months",
                    "timing_issues": "Phased implementation approach",
                    "competition": "Unique integration capabilities",
                    "authority": "Multi-stakeholder presentation approach",
                },
                "engagement_tactics": [
                    "Executive-level presentations",
                    "Proof of concept demonstration",
                    "Reference customer introductions",
                ],
                "success_metrics": [
                    "Stakeholder engagement level",
                    "Technical validation completion",
                    "Budget approval progress",
                ],
                "risk_mitigation": [
                    "Identify all decision makers early",
                    "Understand procurement process",
                    "Plan for competitive evaluation",
                ],
            }
        )

        mock_model.return_value.generate_content.return_value = mock_response

        result = self.ai_service.generate_sales_strategy(
            self.sample_lead_data, self.sample_quality_score
        )

        # Verify structure
        self.assertIn("primary_strategy", result)
        self.assertIn("approach_rationale", result)
        self.assertIn("key_messaging", result)
        self.assertIn("objection_handling", result)
        self.assertIn("strategy_metadata", result)

        # Verify content quality
        self.assertEqual(result["primary_strategy"], "consultative")
        self.assertIsInstance(result["key_messaging"], list)
        self.assertIsInstance(result["objection_handling"], dict)
        self.assertIn("confidence_score", result["strategy_metadata"])

    def test_generate_sales_strategy_different_tiers(self):
        """Test strategy generation for different quality tiers"""
        quality_tiers = ["high", "medium", "low"]

        for tier in quality_tiers:
            quality_score = {
                "quality_tier": tier,
                "overall_score": 80 if tier == "high" else 50,
            }

            with patch("ai_service.services.genai.GenerativeModel") as mock_model:
                mock_response = MagicMock()
                mock_response.text = json.dumps(
                    {
                        "primary_strategy": (
                            "relationship" if tier == "high" else "consultative"
                        ),
                        "approach_rationale": f"Strategy tailored for {tier} quality lead",
                    }
                )
                mock_model.return_value.generate_content.return_value = mock_response

                result = self.ai_service.generate_sales_strategy(
                    self.sample_lead_data, quality_score
                )

                self.assertIn("strategy_metadata", result)
                self.assertEqual(
                    result["strategy_metadata"]["based_on_quality_tier"], tier
                )


class IndustryInsightsTests(TestCase):
    """Test industry-specific insights generation"""

    def setUp(self):
        self.ai_service = GeminiAIService()

    @patch("ai_service.services.genai.GenerativeModel")
    def test_generate_industry_insights_technology(self, mock_model):
        """Test industry insights for technology sector"""
        lead_data = {
            "industry": "Technology",
            "company_size": "100-500 employees",
            "pain_points": ["Scalability issues", "Security concerns"],
        }

        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "industry_trends": [
                    "Cloud-first architecture adoption",
                    "Increased focus on cybersecurity",
                ],
                "industry_pain_points": [
                    "Rapid scaling challenges",
                    "Security compliance requirements",
                ],
                "solution_fit": {
                    "why_relevant": "Addresses core technology scaling needs",
                    "specific_benefits": ["Automated scaling", "Built-in security"],
                    "use_cases": ["DevOps automation", "Security monitoring"],
                },
                "competitive_landscape": {
                    "common_competitors": ["AWS", "Azure", "Google Cloud"],
                    "differentiation_opportunities": ["Specialized industry focus"],
                },
                "sales_best_practices": [
                    "Technical demos are crucial",
                    "Security certifications matter",
                    "ROI calculations should include developer productivity",
                ],
            }
        )

        mock_model.return_value.generate_content.return_value = mock_response

        result = self.ai_service.generate_industry_insights(lead_data)

        # Verify structure
        self.assertIn("industry_trends", result)
        self.assertIn("solution_fit", result)
        self.assertIn("competitive_landscape", result)
        self.assertIn("sales_best_practices", result)
        self.assertIn("insights_metadata", result)

        # Verify content relevance
        self.assertIsInstance(result["industry_trends"], list)
        self.assertIn("why_relevant", result["solution_fit"])
        self.assertTrue(result["insights_metadata"]["industry_specified"])

    @patch("ai_service.services.genai.GenerativeModel")
    def test_generate_industry_insights_no_industry(self, mock_model):
        """Test insights generation when industry is not specified"""
        lead_data = {
            "company_name": "Generic Corp",
            "pain_points": ["Cost reduction needed"],
        }

        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "industry_trends": ["General business efficiency trends"],
                "solution_fit": {"why_relevant": "Universal business benefits"},
            }
        )
        mock_model.return_value.generate_content.return_value = mock_response

        result = self.ai_service.generate_industry_insights(lead_data)

        # Should have lower confidence when industry not specified
        self.assertFalse(result["insights_metadata"]["industry_specified"])
        self.assertLess(result["insights_metadata"]["confidence_score"], 80)


class RecommendationConsistencyTests(TestCase):
    """Test consistency and quality of recommendations"""

    def setUp(self):
        self.ai_service = GeminiAIService()
        self.consistent_lead_data = {
            "company_name": "Consistent Corp",
            "industry": "Healthcare",
            "pain_points": ["Compliance challenges", "Data security"],
            "budget_info": "$100,000",
            "urgency_level": "medium",
        }

    @patch("ai_service.services.genai.GenerativeModel")
    def test_recommendation_confidence_scoring(self, mock_model):
        """Test that recommendations include proper confidence scoring"""
        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "recommendations": [
                    {
                        "type": "next_step",
                        "title": "Schedule compliance review",
                        "priority": "high",
                        "timeline": "1 week",
                    }
                ],
                "lead_score": 75,
            }
        )

        mock_model.return_value.generate_content.return_value = mock_response

        result = self.ai_service.generate_recommendations(self.consistent_lead_data)

        # Check confidence scoring
        self.assertIn("recommendation_confidence", result)
        self.assertIsInstance(result["recommendation_confidence"], (int, float))
        self.assertGreaterEqual(result["recommendation_confidence"], 0)
        self.assertLessEqual(result["recommendation_confidence"], 100)

        # Check individual recommendation confidence
        if "recommendations" in result:
            for rec in result["recommendations"]:
                self.assertIn("confidence_score", rec)

    def test_recommendation_ranking_consistency(self):
        """Test that recommendations are properly ranked by priority and confidence"""
        with patch("ai_service.services.genai.GenerativeModel") as mock_model:
            mock_response = MagicMock()
            mock_response.text = json.dumps(
                {
                    "recommendations": [
                        {
                            "type": "follow_up",
                            "priority": "low",
                            "title": "Low priority item",
                        },
                        {
                            "type": "next_step",
                            "priority": "high",
                            "title": "High priority item",
                        },
                        {
                            "type": "strategy",
                            "priority": "medium",
                            "title": "Medium priority item",
                        },
                    ]
                }
            )
            mock_model.return_value.generate_content.return_value = mock_response

            result = self.ai_service.generate_recommendations(self.consistent_lead_data)

            if "recommendations" in result and len(result["recommendations"]) > 1:
                # Check that high priority items come first
                priorities = [
                    rec.get("priority", "low") for rec in result["recommendations"]
                ]
                priority_values = {"high": 3, "medium": 2, "low": 1}
                priority_scores = [priority_values.get(p, 1) for p in priorities]

                # Should be sorted in descending order (high to low priority)
                self.assertEqual(priority_scores, sorted(priority_scores, reverse=True))


class APIEndpointTests(APITestCase):
    """Test API endpoints for sales recommendations"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        self.sample_lead_data = {
            "company_name": "API Test Corp",
            "contact_details": {"name": "Test Contact"},
            "industry": "Technology",
            "pain_points": ["API integration challenges"],
        }

    @patch("ai_service.services.genai.GenerativeModel")
    def test_lead_quality_score_endpoint(self, mock_model):
        """Test lead quality score API endpoint"""
        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "overall_score": 70,
                "quality_tier": "medium",
                "conversion_probability": 45,
            }
        )
        mock_model.return_value.generate_content.return_value = mock_response

        url = reverse("ai_service:lead_quality_score")
        data = {"lead_data": self.sample_lead_data}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("quality_score", response.data)
        self.assertIn("overall_score", response.data["quality_score"])

    @patch("ai_service.services.genai.GenerativeModel")
    def test_sales_strategy_endpoint(self, mock_model):
        """Test sales strategy API endpoint"""
        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "primary_strategy": "consultative",
                "key_messaging": ["Focus on technical benefits"],
            }
        )
        mock_model.return_value.generate_content.return_value = mock_response

        url = reverse("ai_service:sales_strategy")
        data = {"lead_data": self.sample_lead_data}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("sales_strategy", response.data)

    @patch("ai_service.services.genai.GenerativeModel")
    def test_industry_insights_endpoint(self, mock_model):
        """Test industry insights API endpoint"""
        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "industry_trends": ["Tech trend 1", "Tech trend 2"],
                "sales_best_practices": ["Practice 1", "Practice 2"],
            }
        )
        mock_model.return_value.generate_content.return_value = mock_response

        url = reverse("ai_service:industry_insights")
        data = {"lead_data": self.sample_lead_data}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("industry_insights", response.data)

    @patch("ai_service.services.genai.GenerativeModel")
    def test_comprehensive_recommendations_endpoint(self, mock_model):
        """Test comprehensive recommendations API endpoint"""
        # Mock multiple AI responses for different components
        mock_responses = [
            json.dumps({"overall_score": 75, "quality_tier": "high"}),  # Quality score
            json.dumps({"primary_strategy": "relationship"}),  # Sales strategy
            json.dumps({"industry_trends": ["Trend 1"]}),  # Industry insights
            json.dumps({"recommendations": [{"type": "next_step"}]}),  # Recommendations
        ]

        mock_model.return_value.generate_content.side_effect = [
            MagicMock(text=response) for response in mock_responses
        ]

        url = reverse("ai_service:comprehensive_recommendations")
        data = {
            "lead_data": self.sample_lead_data,
            "include_quality_score": True,
            "include_sales_strategy": True,
            "include_industry_insights": True,
            "include_next_steps": True,
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("quality_score", response.data)
        self.assertIn("sales_strategy", response.data)
        self.assertIn("industry_insights", response.data)
        self.assertIn("recommendations", response.data)
        self.assertIn("analysis_metadata", response.data)

    def test_missing_lead_data_error(self):
        """Test error handling when lead_data is missing"""
        url = reverse("ai_service:lead_quality_score")
        data = {}  # Missing lead_data

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error_code"], "MISSING_LEAD_DATA")

    def test_authentication_required(self):
        """Test that authentication is required for all endpoints"""
        self.client.force_authenticate(user=None)  # Remove authentication

        endpoints = [
            "ai_service:lead_quality_score",
            "ai_service:sales_strategy",
            "ai_service:industry_insights",
            "ai_service:comprehensive_recommendations",
        ]

        for endpoint in endpoints:
            url = reverse(endpoint)
            data = {"lead_data": self.sample_lead_data}

            response = self.client.post(url, data, format="json")
            self.assertIn(
                response.status_code,
                [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
            )


class RecommendationQualityTests(TestCase):
    """Test the quality and consistency of AI recommendations"""

    def setUp(self):
        self.ai_service = GeminiAIService()

    def test_recommendation_structure_validation(self):
        """Test that recommendations follow expected structure"""
        sample_data = {
            "company_name": "Structure Test Corp",
            "pain_points": ["Test pain point"],
        }

        with patch("ai_service.services.genai.GenerativeModel") as mock_model:
            mock_response = MagicMock()
            mock_response.text = json.dumps(
                {
                    "recommendations": [
                        {
                            "type": "next_step",
                            "title": "Test recommendation",
                            "description": "Test description",
                            "priority": "high",
                            "timeline": "1 week",
                            "effort_level": "medium",
                            "expected_outcome": "Test outcome",
                            "success_metrics": "Test metrics",
                        }
                    ]
                }
            )
            mock_model.return_value.generate_content.return_value = mock_response

            result = self.ai_service.generate_recommendations(sample_data)

            # Validate recommendation structure
            self.assertIn("recommendations", result)
            if result["recommendations"]:
                rec = result["recommendations"][0]
                required_fields = [
                    "type",
                    "title",
                    "description",
                    "priority",
                    "timeline",
                ]
                for field in required_fields:
                    self.assertIn(field, rec, f"Missing required field: {field}")

    def test_confidence_score_ranges(self):
        """Test that confidence scores are within valid ranges"""
        sample_data = {"company_name": "Confidence Test Corp"}

        with patch("ai_service.services.genai.GenerativeModel") as mock_model:
            mock_response = MagicMock()
            mock_response.text = json.dumps({"recommendations": []})
            mock_model.return_value.generate_content.return_value = mock_response

            result = self.ai_service.generate_recommendations(sample_data)

            # Check confidence score range
            confidence = result.get("recommendation_confidence", 0)
            self.assertGreaterEqual(confidence, 0)
            self.assertLessEqual(confidence, 100)
            self.assertIsInstance(confidence, (int, float))


# Tests can be run with: python manage.py test ai_service.test_recommendations
