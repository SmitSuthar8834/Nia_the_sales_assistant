#!/usr/bin/env python
"""
Simple test script to verify the AI-powered sales recommendations engine functionality
This script tests the core functionality without relying on external API calls
"""

import os
import sys
from pathlib import Path

import django

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

import json
from unittest.mock import MagicMock, patch

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nia_sales_assistant.settings")
django.setup()

from ai_service.services import GeminiAIService


def test_lead_quality_scoring():
    """Test lead quality scoring functionality"""
    print("Testing Lead Quality Scoring...")

    ai_service = GeminiAIService()

    sample_lead_data = {
        "company_name": "TechCorp Solutions",
        "contact_details": {
            "name": "John Smith",
            "email": "john.smith@techcorp.com",
            "phone": "+1-555-123-4567",
            "title": "CTO",
        },
        "pain_points": ["Manual processes", "High costs"],
        "requirements": ["Automation", "Cost reduction"],
        "budget_info": "$50,000 - $100,000",
        "timeline": "Q2 2024",
        "industry": "Technology",
    }

    # Mock the AI response
    with patch("ai_service.services.genai.GenerativeModel") as mock_model:
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
                "key_strengths": ["Clear pain points", "Budget specified"],
                "improvement_areas": ["Validate budget authority"],
                "competitive_risk": "medium",
                "next_best_action": "Schedule technical demo",
            }
        )
        mock_model.return_value.generate_content.return_value = mock_response

        result = ai_service.calculate_lead_quality_score(sample_lead_data)

        # Verify results
        assert "overall_score" in result
        assert "quality_tier" in result
        assert "validation_metadata" in result
        assert result["overall_score"] >= 80

        print("✓ Lead quality scoring working correctly")
        return True


def test_sales_strategy_generation():
    """Test sales strategy generation functionality"""
    print("Testing Sales Strategy Generation...")

    ai_service = GeminiAIService()

    sample_lead_data = {
        "company_name": "Enterprise Corp",
        "industry": "Manufacturing",
        "company_size": "1000+ employees",
        "pain_points": ["Supply chain inefficiency"],
        "budget_info": "$200,000+",
    }

    quality_score = {"overall_score": 80, "quality_tier": "high"}

    # Mock the AI response
    with patch("ai_service.services.genai.GenerativeModel") as mock_model:
        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "primary_strategy": "consultative",
                "approach_rationale": "High-value enterprise client requires consultative approach",
                "key_messaging": ["Focus on ROI", "Proven track record"],
                "objection_handling": {
                    "budget_concerns": "Demonstrate clear ROI",
                    "timing_issues": "Phased implementation",
                },
                "engagement_tactics": ["Executive presentations", "Proof of concept"],
                "success_metrics": ["Stakeholder engagement", "Technical validation"],
                "risk_mitigation": [
                    "Identify decision makers",
                    "Understand procurement",
                ],
            }
        )
        mock_model.return_value.generate_content.return_value = mock_response

        result = ai_service.generate_sales_strategy(sample_lead_data, quality_score)

        # Verify results
        assert "primary_strategy" in result
        assert "key_messaging" in result
        assert "strategy_metadata" in result
        assert isinstance(result["key_messaging"], list)

        print("✓ Sales strategy generation working correctly")
        return True


def test_industry_insights():
    """Test industry-specific insights generation"""
    print("Testing Industry Insights Generation...")

    ai_service = GeminiAIService()

    sample_lead_data = {
        "industry": "Healthcare",
        "company_size": "500-1000 employees",
        "pain_points": ["Compliance challenges", "Data security"],
    }

    # Mock the AI response
    with patch("ai_service.services.genai.GenerativeModel") as mock_model:
        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "industry_trends": [
                    "Digital health transformation",
                    "Regulatory compliance focus",
                ],
                "industry_pain_points": ["HIPAA compliance", "Data integration"],
                "solution_fit": {
                    "why_relevant": "Addresses healthcare-specific needs",
                    "specific_benefits": ["HIPAA compliance", "Secure data handling"],
                    "use_cases": ["Patient data management", "Compliance reporting"],
                },
                "competitive_landscape": {
                    "common_competitors": ["Epic", "Cerner"],
                    "differentiation_opportunities": ["Specialized healthcare focus"],
                },
                "sales_best_practices": [
                    "Understand regulatory requirements",
                    "Focus on patient outcomes",
                ],
            }
        )
        mock_model.return_value.generate_content.return_value = mock_response

        result = ai_service.generate_industry_insights(sample_lead_data)

        # Verify results
        assert "industry_trends" in result
        assert "solution_fit" in result
        assert "insights_metadata" in result
        assert isinstance(result["industry_trends"], list)

        print("✓ Industry insights generation working correctly")
        return True


def test_comprehensive_recommendations():
    """Test comprehensive recommendations generation"""
    print("Testing Comprehensive Recommendations...")

    ai_service = GeminiAIService()

    sample_lead_data = {
        "company_name": "Test Corp",
        "industry": "Technology",
        "pain_points": ["Scalability issues"],
        "requirements": ["Cloud solution"],
    }

    # Mock the AI response
    with patch("ai_service.services.genai.GenerativeModel") as mock_model:
        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "recommendations": [
                    {
                        "type": "next_step",
                        "title": "Schedule technical demo",
                        "description": "Demonstrate scalability features",
                        "priority": "high",
                        "timeline": "1 week",
                        "effort_level": "medium",
                        "expected_outcome": "Technical validation",
                        "success_metrics": "Demo acceptance",
                    }
                ],
                "lead_score": 75,
                "conversion_probability": 60,
                "key_insights": ["Strong technical interest"],
                "next_best_actions": ["Schedule demo", "Prepare technical materials"],
            }
        )
        mock_model.return_value.generate_content.return_value = mock_response

        result = ai_service.generate_recommendations(sample_lead_data)

        # Verify results
        assert "recommendations" in result
        assert "recommendation_confidence" in result
        assert isinstance(result["recommendations"], list)

        if result["recommendations"]:
            rec = result["recommendations"][0]
            assert "confidence_score" in rec
            assert "type" in rec
            assert "priority" in rec

        print("✓ Comprehensive recommendations working correctly")
        return True


def test_confidence_scoring():
    """Test confidence scoring and ranking functionality"""
    print("Testing Confidence Scoring and Ranking...")

    ai_service = GeminiAIService()

    # Test data completeness calculation
    complete_data = {
        "company_name": "Complete Corp",
        "contact_details": {"name": "John Doe", "email": "john@complete.com"},
        "pain_points": ["Issue 1", "Issue 2"],
        "requirements": ["Req 1", "Req 2"],
        "budget_info": "$100k",
        "timeline": "Q2",
        "industry": "Tech",
    }

    incomplete_data = {"company_name": "Incomplete Corp"}

    complete_score = ai_service._calculate_data_completeness(complete_data)
    incomplete_score = ai_service._calculate_data_completeness(incomplete_data)

    assert complete_score > incomplete_score
    assert 0 <= complete_score <= 100
    assert 0 <= incomplete_score <= 100

    print("✓ Confidence scoring working correctly")
    return True


def main():
    """Run all functionality tests"""
    print("=" * 60)
    print("AI-Powered Sales Recommendations Engine - Functionality Test")
    print("=" * 60)

    tests = [
        test_lead_quality_scoring,
        test_sales_strategy_generation,
        test_industry_insights,
        test_comprehensive_recommendations,
        test_confidence_scoring,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
                print(f"✗ {test.__name__} failed")
        except Exception as e:
            failed += 1
            print(f"✗ {test.__name__} failed with error: {e}")

    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print(
            "🎉 All AI-powered sales recommendations functionality is working correctly!"
        )
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error running tests: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
