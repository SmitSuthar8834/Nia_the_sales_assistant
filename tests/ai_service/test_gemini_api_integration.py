#!/usr/bin/env python
"""
Simple test script to verify Gemini AI integration works.
This script tests the core functionality without using Django's test framework.
"""

import os
import sys
from pathlib import Path

import django

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nia_sales_assistant.settings")
django.setup()

from ai_service.services import GeminiAIService


def test_gemini_connection():
    """Test basic Gemini AI connection"""
    print("Testing Gemini AI connection...")

    try:
        ai_service = GeminiAIService()
        result = ai_service.test_connection()

        if result["success"]:
            print("✅ Gemini AI connection successful!")
            print(f"Response: {result['message']}")
            return True
        else:
            print("❌ Gemini AI connection failed!")
            print(f"Error: {result['message']}")
            return False

    except Exception as e:
        print(f"❌ Connection test failed with exception: {e}")
        return False


def test_lead_extraction():
    """Test lead information extraction"""
    print("\nTesting lead information extraction...")

    sample_conversation = """
    Hi, this is John Smith from Acme Corporation. We're a manufacturing company 
    with about 200 employees. We're currently struggling with our manual data entry 
    processes and need a solution that can help automate our workflows. 
    Our budget is around $50,000 and we need to implement something by Q2 2024.
    You can reach me at john.smith@acme.com or call 555-123-4567.
    """

    try:
        ai_service = GeminiAIService()
        result = ai_service.extract_lead_info(sample_conversation)

        print("✅ Lead extraction completed!")
        print(f"Company: {result.get('company_name', 'Not extracted')}")
        print(
            f"Contact: {result.get('contact_details', {}).get('name', 'Not extracted')}"
        )
        print(
            f"Email: {result.get('contact_details', {}).get('email', 'Not extracted')}"
        )
        print(f"Budget: {result.get('budget_info', 'Not extracted')}")
        print(f"Timeline: {result.get('timeline', 'Not extracted')}")
        print(
            f"Confidence Score: {result.get('extraction_metadata', {}).get('confidence_score', 0)}"
        )
        print(
            f"Data Completeness: {result.get('extraction_metadata', {}).get('data_completeness', 0)}%"
        )

        return True

    except Exception as e:
        print(f"❌ Lead extraction failed: {e}")
        return False


def test_entity_extraction():
    """Test entity extraction"""
    print("\nTesting entity extraction...")

    sample_text = """
    Contact Sarah Johnson at sarah@techcorp.com or call 555-987-6543. 
    She works at TechCorp Inc and mentioned they need CRM integration. 
    Budget is $75,000 and timeline is Q3 2024.
    """

    try:
        ai_service = GeminiAIService()
        entities = ai_service.extract_entities(sample_text)

        print("✅ Entity extraction completed!")
        print(f"Companies: {entities.get('companies', [])}")
        print(f"People: {entities.get('people', [])}")
        print(f"Emails: {entities.get('emails', [])}")
        print(f"Phones: {entities.get('phones', [])}")
        print(f"Technologies: {entities.get('technologies', [])}")
        print(f"Monetary amounts: {entities.get('monetary_amounts', [])}")

        return True

    except Exception as e:
        print(f"❌ Entity extraction failed: {e}")
        return False


def test_data_validation():
    """Test data validation"""
    print("\nTesting data validation...")

    sample_data = {
        "company_name": "Test Corp",
        "contact_details": {
            "name": "John Doe",
            "email": "john@test.com",
            "phone": "555-123-4567",
        },
        "pain_points": ["Manual processes"],
        "requirements": ["Automation"],
        "budget_info": "$50,000",
    }

    try:
        ai_service = GeminiAIService()
        validation = ai_service.validate_extracted_data(sample_data)

        print("✅ Data validation completed!")
        print(f"Is Valid: {validation.get('is_valid', False)}")
        print(f"Errors: {validation.get('errors', [])}")
        print(f"Warnings: {validation.get('warnings', [])}")
        print(f"Quality Score: {validation.get('data_quality_score', 0)}")

        return True

    except Exception as e:
        print(f"❌ Data validation failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 Starting Gemini AI Integration Tests")
    print("=" * 50)

    tests = [
        test_gemini_connection,
        test_lead_extraction,
        test_entity_extraction,
        test_data_validation,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print("-" * 30)

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Gemini AI integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
