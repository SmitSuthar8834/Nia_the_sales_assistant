#!/usr/bin/env python
"""
Simple API test for the AI-powered sales recommendations engine
"""

import requests
import json
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nia_sales_assistant.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

User = get_user_model()

def test_recommendations_api():
    """Test the recommendations API endpoints"""
    print("Testing AI-Powered Sales Recommendations API...")
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Create API client
    client = APIClient()
    client.force_authenticate(user=user)
    
    # Sample lead data
    sample_lead_data = {
        "company_name": "TechCorp Solutions",
        "contact_details": {
            "name": "John Smith",
            "email": "john.smith@techcorp.com",
            "title": "CTO"
        },
        "pain_points": ["Manual processes", "High operational costs"],
        "requirements": ["Automation solution", "Cost reduction"],
        "budget_info": "$50,000 - $100,000",
        "timeline": "Q2 2024",
        "industry": "Technology"
    }
    
    # Test endpoints
    endpoints_to_test = [
        {
            'url': '/api/ai/lead-quality-score/',
            'name': 'Lead Quality Score',
            'data': {'lead_data': sample_lead_data}
        },
        {
            'url': '/api/ai/sales-strategy/',
            'name': 'Sales Strategy',
            'data': {'lead_data': sample_lead_data}
        },
        {
            'url': '/api/ai/industry-insights/',
            'name': 'Industry Insights',
            'data': {'lead_data': sample_lead_data}
        },
        {
            'url': '/api/ai/comprehensive-recommendations/',
            'name': 'Comprehensive Recommendations',
            'data': {
                'lead_data': sample_lead_data,
                'include_quality_score': True,
                'include_sales_strategy': True,
                'include_industry_insights': True,
                'include_next_steps': True
            }
        }
    ]
    
    results = []
    
    for endpoint in endpoints_to_test:
        try:
            print(f"\nTesting {endpoint['name']}...")
            response = client.post(endpoint['url'], endpoint['data'], format='json')
            
            if response.status_code == 200:
                print(f"✓ {endpoint['name']} - Status: {response.status_code}")
                data = response.json()
                if data.get('success'):
                    print(f"  Response contains expected data structure")
                    results.append(True)
                else:
                    print(f"  ✗ Response indicates failure: {data.get('error', 'Unknown error')}")
                    results.append(False)
            else:
                print(f"✗ {endpoint['name']} - Status: {response.status_code}")
                print(f"  Error: {response.content.decode()}")
                results.append(False)
                
        except Exception as e:
            print(f"✗ {endpoint['name']} - Exception: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n{'='*60}")
    print(f"API Test Results: {passed}/{total} endpoints working")
    print(f"{'='*60}")
    
    if passed == total:
        print("🎉 All AI-powered sales recommendations API endpoints are working!")
        return True
    else:
        print("❌ Some API endpoints failed. Check the logs above.")
        return False

if __name__ == "__main__":
    try:
        success = test_recommendations_api()
        exit(0 if success else 1)
    except Exception as e:
        print(f"Error running API tests: {e}")
        import traceback
        traceback.print_exc()
        exit(1)