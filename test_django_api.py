#!/usr/bin/env python
"""
Django API Testing Script for NIA Sales Assistant
Uses Django's test client to test API endpoints
"""
import os
import django
import json
from django.test import Client
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nia_sales_assistant.settings')
django.setup()

User = get_user_model()

def test_api_with_django_client():
    """Test API endpoints using Django's test client"""
    print("🚀 Testing NIA Sales Assistant API with Django Client")
    print("=" * 60)
    
    # Create test client
    client = Client()
    
    # Get or create test user
    try:
        user = User.objects.get(username='admin')
        print(f"✅ Using existing user: {user.username}")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        print(f"✅ Created test user: {user.username}")
    
    # Login the user
    client.force_login(user)
    print("✅ User logged in successfully")
    
    # Test 1: Test Gemini Connection
    print("\n1. Testing Gemini AI Connection...")
    response = client.get('/api/ai/test-connection/')
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Gemini AI connection test successful!")
        print(f"Response: {result}")
    else:
        print(f"❌ Connection test failed")
        print(f"Response: {response.content.decode()}")
    
    # Test 2: Test Conversation Analysis
    print("\n2. Testing Conversation Analysis...")
    
    sample_conversation = """
    Sales Rep: Hi, I'm calling from TechSolutions. I understand you might be looking for a CRM system?
    
    Customer: Yes, I'm Sarah Wilson from GreenTech Industries. We're a mid-size company with about 150 employees. 
    Our current system is really outdated and we're losing track of our leads. We need something that can 
    integrate with our existing tools and handle our growing customer base. Our budget is around $30,000 
    and we'd like to have something in place within the next 4 months. I'm the Operations Manager, 
    but our CTO David Chen will also be involved in the decision.
    
    Sales Rep: That sounds like a perfect fit for our enterprise solution...
    """
    
    payload = {
        "conversation_text": sample_conversation
    }
    
    response = client.post(
        '/api/ai/analyze/',
        data=json.dumps(payload),
        content_type='application/json'
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Conversation analysis successful!")
        print(f"Analysis ID: {result.get('analysis_id')}")
        
        lead_info = result.get('lead_info', {})
        print(f"\n📊 Extracted Lead Information:")
        print(f"  Company: {lead_info.get('company_name')}")
        print(f"  Contact: {lead_info.get('contact_details', {}).get('name')}")
        print(f"  Industry: {lead_info.get('industry')}")
        print(f"  Budget: {lead_info.get('budget_info')}")
        print(f"  Timeline: {lead_info.get('timeline')}")
        print(f"  Pain Points: {lead_info.get('pain_points')}")
        print(f"  Requirements: {lead_info.get('requirements')}")
        
        recommendations = result.get('recommendations', {})
        print(f"\n🎯 AI Recommendations:")
        print(f"  Lead Score: {recommendations.get('lead_score')}")
        print(f"  Conversion Probability: {recommendations.get('conversion_probability')}")
        print(f"  Number of Recommendations: {len(recommendations.get('recommendations', []))}")
        
        # Show first few recommendations
        for i, rec in enumerate(recommendations.get('recommendations', [])[:3]):
            print(f"  {i+1}. {rec.get('title')} ({rec.get('priority')} priority)")
            
    else:
        print(f"❌ Analysis failed")
        print(f"Response: {response.content.decode()}")
    
    # Test 3: Test Conversation History
    print("\n3. Testing Conversation History...")
    response = client.get('/api/ai/history/')
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ History retrieval successful!")
        print(f"Number of conversations: {result.get('count', 0)}")
        
        if result.get('count', 0) > 0:
            print("📝 Recent conversations:")
            for i, conv in enumerate(result.get('history', [])[:3]):
                print(f"  {i+1}. {conv.get('timestamp')} - {conv.get('conversation_preview')}")
    else:
        print(f"❌ History retrieval failed")
        print(f"Response: {response.content.decode()}")
    
    print("\n" + "=" * 60)
    print("🎉 Django API Testing Complete!")
    
    # Test 4: Test with invalid data
    print("\n4. Testing Error Handling...")
    response = client.post(
        '/api/ai/analyze/',
        data=json.dumps({"conversation_text": ""}),
        content_type='application/json'
    )
    
    print(f"Empty conversation test - Status Code: {response.status_code}")
    if response.status_code == 400:
        print("✅ Error handling working correctly")
    else:
        print("❌ Error handling not working as expected")

if __name__ == "__main__":
    test_api_with_django_client()