#!/usr/bin/env python
"""
API Test script for Opportunity Conversion Intelligence endpoints (Task 10)

This script tests the API endpoints for opportunity conversion intelligence.
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

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nia_sales_assistant.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

User = get_user_model()


def test_opportunity_conversion_api_endpoints():
    """Test all opportunity conversion intelligence API endpoints"""
    print("Testing Opportunity Conversion Intelligence API Endpoints...")

    client = Client()

    # Sample test data
    lead_data = {
        "company_name": "API Test Corp",
        "industry": "technology",
        "company_size": "100-500 employees",
        "contact_details": {
            "name": "John Smith",
            "email": "john@apitest.com",
            "title": "CTO",
        },
        "pain_points": ["Manual processes", "Data silos"],
        "requirements": ["AI automation", "Data integration"],
        "budget_info": "$50,000 - $100,000 approved",
        "timeline": "Q2 implementation needed",
        "urgency_level": "high",
    }

    opportunity_data = {
        "name": "API Test AI Implementation",
        "estimated_value": 75000,
        "probability": 75,
        "stage": "qualification",
        "expected_close_date": "2024-06-01",
    }

    # Test endpoints with mocked AI responses
    endpoints_to_test = [
        {
            "name": "Opportunity Conversion Analysis",
            "url": "ai_service:opportunity_conversion_analysis",
            "payload": {
                "lead_data": lead_data,
                "historical_data": {"avg_conversion_rate": 25},
            },
            "mock_response": {
                "conversion_probability": 75,
                "conversion_confidence": 85,
                "recommended_for_conversion": True,
                "readiness_factors": ["Budget approved", "Timeline confirmed"],
            },
        },
        {
            "name": "Deal Size Timeline Prediction",
            "url": "ai_service:deal_size_timeline_prediction",
            "payload": {"lead_data": lead_data, "opportunity_data": opportunity_data},
            "mock_response": {
                "deal_size_prediction": {
                    "minimum_value": 25000,
                    "maximum_value": 75000,
                    "most_likely_value": 50000,
                    "confidence_level": 75,
                },
                "timeline_prediction": {
                    "minimum_days": 60,
                    "maximum_days": 180,
                    "most_likely_days": 120,
                    "confidence_level": 80,
                },
            },
        },
        {
            "name": "Sales Stage Recommendation",
            "url": "ai_service:sales_stage_recommendation",
            "payload": {
                "lead_data": lead_data,
                "opportunity_data": opportunity_data,
                "current_stage": "prospecting",
            },
            "mock_response": {
                "current_stage_assessment": {
                    "recommended_stage": "qualification",
                    "stage_confidence": 85,
                },
                "advancement_analysis": {
                    "next_stage": "proposal",
                    "advancement_probability": 70,
                },
            },
        },
        {
            "name": "Risk Factor Analysis",
            "url": "ai_service:risk_factor_analysis",
            "payload": {
                "lead_data": lead_data,
                "opportunity_data": opportunity_data,
                "historical_data": {"common_loss_reasons": ["Price"]},
            },
            "mock_response": {
                "overall_risk_assessment": {"risk_level": "medium", "risk_score": 45},
                "identified_risks": [
                    {
                        "risk_type": "competitive",
                        "risk_description": "Multiple vendor evaluation",
                        "probability": 60,
                    }
                ],
            },
        },
        {
            "name": "Historical Pattern Analysis",
            "url": "ai_service:historical_pattern_analysis",
            "payload": {"lead_data": lead_data, "user_id": "test-user-id"},
            "mock_response": {
                "similar_leads_analysis": {
                    "similar_leads_count": 25,
                    "average_conversion_rate": 35,
                },
                "industry_benchmarks": {"industry_conversion_rate": 28},
            },
        },
    ]

    results = []

    for endpoint in endpoints_to_test:
        try:
            print(f"\nTesting {endpoint['name']}...")

            # Mock the AI service method based on endpoint
            if "conversion_analysis" in endpoint["url"]:
                mock_path = "ai_service.services.GeminiAIService.analyze_opportunity_conversion_potential"
            elif "deal_size_timeline" in endpoint["url"]:
                mock_path = (
                    "ai_service.services.GeminiAIService.predict_deal_size_and_timeline"
                )
            elif "sales_stage" in endpoint["url"]:
                mock_path = "ai_service.services.GeminiAIService.recommend_sales_stage"
            elif "risk_factor" in endpoint["url"]:
                mock_path = "ai_service.services.GeminiAIService.identify_risk_factors_and_mitigation"
            elif "historical_pattern" in endpoint["url"]:
                mock_path = (
                    "ai_service.services.GeminiAIService.analyze_historical_patterns"
                )
            else:
                mock_path = "ai_service.services.GeminiAIService._make_api_call"

            with patch(mock_path) as mock_method:
                mock_method.return_value = endpoint["mock_response"]

                url = reverse(endpoint["url"])
                response = client.post(
                    url,
                    data=json.dumps(endpoint["payload"]),
                    content_type="application/json",
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        print(f"✓ {endpoint['name']}: SUCCESS")
                        print(f"  Response keys: {list(data.keys())}")
                        results.append(True)
                    else:
                        print(f"✗ {endpoint['name']}: API returned success=False")
                        print(f"  Error: {data.get('error', 'Unknown error')}")
                        results.append(False)
                else:
                    print(f"✗ {endpoint['name']}: HTTP {response.status_code}")
                    print(f"  Response: {response.content.decode()}")
                    results.append(False)

        except Exception as e:
            print(f"✗ {endpoint['name']}: Exception - {e}")
            results.append(False)

    return results


def test_comprehensive_opportunity_intelligence_endpoint():
    """Test the comprehensive opportunity intelligence endpoint"""
    print("\nTesting Comprehensive Opportunity Intelligence Endpoint...")

    client = Client()

    lead_data = {
        "company_name": "Comprehensive Test Corp",
        "industry": "technology",
        "pain_points": ["Manual processes"],
        "requirements": ["AI automation"],
    }

    opportunity_data = {
        "name": "Comprehensive Test Opportunity",
        "stage": "qualification",
    }

    payload = {
        "lead_data": lead_data,
        "opportunity_data": opportunity_data,
        "include_conversion_analysis": True,
        "include_deal_predictions": True,
        "include_stage_recommendations": True,
        "include_risk_analysis": True,
        "include_historical_patterns": True,
    }

    # Mock all the service methods
    mocks = {
        "ai_service.services.GeminiAIService.analyze_opportunity_conversion_potential": {
            "conversion_probability": 75,
            "recommended_for_conversion": True,
        },
        "ai_service.services.GeminiAIService.predict_deal_size_and_timeline": {
            "deal_size_prediction": {"most_likely_value": 50000}
        },
        "ai_service.services.GeminiAIService.recommend_sales_stage": {
            "current_stage_assessment": {"recommended_stage": "qualification"}
        },
        "ai_service.services.GeminiAIService.identify_risk_factors_and_mitigation": {
            "overall_risk_assessment": {"risk_level": "medium"}
        },
        "ai_service.services.GeminiAIService.analyze_historical_patterns": {
            "similar_leads_analysis": {"average_conversion_rate": 35}
        },
    }

    try:
        with patch.multiple(
            "ai_service.services.GeminiAIService",
            **{
                method.split(".")[-1]: MagicMock(return_value=response)
                for method, response in mocks.items()
            },
        ):
            url = reverse("ai_service:comprehensive_opportunity_intelligence")
            response = client.post(
                url, data=json.dumps(payload), content_type="application/json"
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print("✓ Comprehensive Opportunity Intelligence: SUCCESS")
                    print(
                        f"  Components included: {list(data.get('intelligence_metadata', {}).get('components_included', {}).keys())}"
                    )
                    return True
                else:
                    print(
                        f"✗ Comprehensive Opportunity Intelligence: API returned success=False"
                    )
                    print(f"  Error: {data.get('error', 'Unknown error')}")
                    return False
            else:
                print(
                    f"✗ Comprehensive Opportunity Intelligence: HTTP {response.status_code}"
                )
                print(f"  Response: {response.content.decode()}")
                return False

    except Exception as e:
        print(f"✗ Comprehensive Opportunity Intelligence: Exception - {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all API tests"""
    print("=" * 70)
    print("OPPORTUNITY CONVERSION INTELLIGENCE API ENDPOINT TESTS")
    print("=" * 70)

    # Test individual endpoints
    endpoint_results = test_opportunity_conversion_api_endpoints()

    # Test comprehensive endpoint
    comprehensive_result = test_comprehensive_opportunity_intelligence_endpoint()

    # Summary
    print("\n" + "=" * 70)
    print("API TEST SUMMARY")
    print("=" * 70)

    total_endpoints = len(endpoint_results)
    passed_endpoints = sum(endpoint_results)
    comprehensive_passed = 1 if comprehensive_result else 0

    total_tests = total_endpoints + 1
    total_passed = passed_endpoints + comprehensive_passed

    print(f"Individual endpoints: {passed_endpoints}/{total_endpoints}")
    print(f"Comprehensive endpoint: {comprehensive_passed}/1")
    print(f"Total API tests passed: {total_passed}/{total_tests}")

    if total_passed == total_tests:
        print("✓ All opportunity conversion intelligence API tests PASSED!")
        print("\nAPI endpoints successfully implemented:")
        print("- /api/ai/opportunity-conversion-analysis/")
        print("- /api/ai/deal-size-timeline-prediction/")
        print("- /api/ai/sales-stage-recommendation/")
        print("- /api/ai/risk-factor-analysis/")
        print("- /api/ai/historical-pattern-analysis/")
        print("- /api/ai/comprehensive-opportunity-intelligence/")
    else:
        print("✗ Some API tests FAILED. Check the output above for details.")

    return total_passed == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
