#!/usr/bin/env python
"""
Test script for API endpoints
"""
import os
import sys
import django
import json
from django.test import Client
from django.contrib.auth import get_user_model

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nia_sales_assistant.settings')
django.setup()

def test_api_endpoints():
    """Test the API endpoints"""
    print("Testing API Endpoints...")
    
    # Create test user
    User = get_user_model()
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Create client and login
    client = Client()
    client.force_login(user)
    
    print("1. Testing entity extraction endpoint...")
    response = client.post('/api/ai/extract-entities/', {
        'text': 'Contact John Doe at john@example.com or call 555-123-4567. Budget is $50,000.'
    }, content_type='application/json')
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Status: {response.status_code}")
        print(f"   ✓ Success: {data.get('success', False)}")
        entities = data.get('entities', {})
        print(f"   ✓ Emails found: {entities.get('emails', [])}")
        print(f"   ✓ Phones found: {entities.get('phones', [])}")
        print(f"   ✓ Money amounts: {entities.get('monetary_amounts', [])}")
    else:
        print(f"   ✗ Failed with status: {response.status_code}")
        print(f"   ✗ Response: {response.content}")
    
    print("\n2. Testing lead data validation endpoint...")
    test_lead_data = {
        'lead_data': {
            'company_name': 'Test Corp',
            'contact_details': {
                'name': 'John Doe',
                'email': 'john@test.com',
                'phone': '555-123-4567'
            },
            'pain_points': ['Issue 1', 'Issue 2'],
            'requirements': ['Req 1']
        }
    }
    
    response = client.post('/api/ai/validate-lead/', 
                          json.dumps(test_lead_data), 
                          content_type='application/json')
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Status: {response.status_code}")
        print(f"   ✓ Success: {data.get('success', False)}")
        validation = data.get('validation', {})
        print(f"   ✓ Valid: {validation.get('is_valid', False)}")
        print(f"   ✓ Quality Score: {validation.get('data_quality_score', 0)}")
    else:
        print(f"   ✗ Failed with status: {response.status_code}")
        print(f"   ✗ Response: {response.content}")
    
    print("\n3. Testing conversation history endpoint...")
    response = client.get('/api/ai/history/')
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Status: {response.status_code}")
        print(f"   ✓ Success: {data.get('success', False)}")
        print(f"   ✓ History count: {data.get('count', 0)}")
    else:
        print(f"   ✗ Failed with status: {response.status_code}")
        print(f"   ✗ Response: {response.content}")
    
    print("\n4. Testing Gemini connection endpoint...")
    response = client.get('/api/ai/test-connection/')
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Status: {response.status_code}")
        print(f"   ✓ Success: {data.get('success', False)}")
        print(f"   ✓ Message: {data.get('message', 'No message')}")
    else:
        print(f"   ✗ Failed with status: {response.status_code}")
        print(f"   ✗ Response: {response.content}")
    
    print("\n✅ API endpoint tests completed!")

if __name__ == "__main__":
    test_api_endpoints()