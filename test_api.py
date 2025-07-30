#!/usr/bin/env python
"""
API Testing Script for NIA Sales Assistant
Tests all the AI service endpoints
"""
import requests
import json
from requests.auth import HTTPBasicAuth

# Configuration
BASE_URL = "http://127.0.0.1:8000"
USERNAME = "admin"
PASSWORD = "admin"  # The password we set during superuser creation

def test_api_endpoints():
    """Test all API endpoints"""
    print("🚀 Testing NIA Sales Assistant API Endpoints")
    print("=" * 50)
    
    # Create a session for authentication
    session = requests.Session()
    
    # Test 1: Login and get session
    print("\n1. Testing Authentication...")
    login_url = f"{BASE_URL}/admin/login/"
    
    # Get CSRF token first
    response = session.get(login_url)
    if response.status_code == 200:
        print("✅ Server is accessible")
    else:
        print("❌ Server is not accessible")
        return
    
    # Test 2: Test Gemini Connection
    print("\n2. Testing Gemini AI Connection...")
    test_connection_url = f"{BASE_URL}/api/ai/test-connection/"
    
    try:
        response = session.get(test_connection_url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Gemini AI connection test successful!")
            print(f"Response: {result}")
        else:
            print(f"❌ Connection test failed: {response.text}")
    except Exception as e:
        print(f"❌ Error testing connection: {e}")
    
    # Test 3: Test Conversation Analysis
    print("\n3. Testing Conversation Analysis...")
    analyze_url = f"{BASE_URL}/api/ai/analyze/"
    
    sample_conversation = """
    Sales Rep: Hi, I'm calling from TechSolutions. I understand you might be looking for a CRM system?
    
    Customer: Yes, I'm Mike Johnson from XYZ Corp. We're a growing startup with about 50 employees. 
    Our current spreadsheet-based system is becoming unmanageable. We need something that can help us 
    track leads better and automate our sales process. We're looking at a budget of around $20,000 
    and want to implement something within the next 2 months. I'm the founder, so I make the final decisions.
    
    Sales Rep: That sounds perfect for our small business solution. Let me tell you about our features...
    """
    
    payload = {
        "conversation_text": sample_conversation
    }
    
    try:
        response = session.post(
            analyze_url, 
            json=payload,
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Conversation analysis successful!")
            print(f"Analysis ID: {result.get('analysis_id')}")
            print(f"Lead Info: {json.dumps(result.get('lead_info'), indent=2)}")
            print(f"Recommendations: {len(result.get('recommendations', {}).get('recommendations', []))} recommendations generated")
        else:
            print(f"❌ Analysis failed: {response.text}")
    except Exception as e:
        print(f"❌ Error analyzing conversation: {e}")
    
    # Test 4: Test Conversation History
    print("\n4. Testing Conversation History...")
    history_url = f"{BASE_URL}/api/ai/history/"
    
    try:
        response = session.get(history_url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ History retrieval successful!")
            print(f"Number of conversations: {result.get('count', 0)}")
        else:
            print(f"❌ History retrieval failed: {response.text}")
    except Exception as e:
        print(f"❌ Error retrieving history: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 API Testing Complete!")

def test_with_curl_commands():
    """Generate curl commands for manual testing"""
    print("\n📋 Manual Testing with cURL Commands:")
    print("=" * 50)
    
    print("\n1. Test Gemini Connection:")
    print(f"curl -u {USERNAME}:{PASSWORD} -X GET {BASE_URL}/api/ai/test-connection/")
    
    print("\n2. Test Conversation Analysis:")
    print(f"""curl -u {USERNAME}:{PASSWORD} -X POST {BASE_URL}/api/ai/analyze/ \\
  -H "Content-Type: application/json" \\
  -d '{{"conversation_text": "Sales Rep: Hello! Customer: Hi, I am John from ABC Corp. We need a CRM system for our 100-person company."}}'""")
    
    print("\n3. Test Conversation History:")
    print(f"curl -u {USERNAME}:{PASSWORD} -X GET {BASE_URL}/api/ai/history/")

if __name__ == "__main__":
    test_api_endpoints()
    test_with_curl_commands()