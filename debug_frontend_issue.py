#!/usr/bin/env python
"""
Debug script to identify the frontend blank results issue
"""
import requests
import json

def test_api_response():
    """Test what the API actually returns"""
    print("🔍 Debugging Frontend Blank Results Issue")
    print("=" * 50)
    
    # Test conversation
    test_conversation = "I spoke with John Smith from Acme Corp. They need a CRM system and have a budget of $50,000."
    
    print("1. Testing API endpoint directly...")
    try:
        response = requests.post(
            'http://127.0.0.1:8000/api/ai/analyze/',
            json={
                'conversation_text': test_conversation,
                'context': {'source': 'meeting', 'urgency': 'high'},
                'extract_entities': True,
                'generate_recommendations': True
            },
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ API Response Structure:")
            print(json.dumps(data, indent=2))
            
            print("\n🔍 Key Analysis:")
            print(f"- Has 'success' field: {'success' in data}")
            print(f"- Success value: {data.get('success')}")
            print(f"- Has 'lead_information': {'lead_information' in data}")
            print(f"- Has 'lead_info': {'lead_info' in data}")
            
            if 'lead_information' in data:
                lead_info = data['lead_information']
                print(f"- Company name: {lead_info.get('company_name')}")
                print(f"- Contact details: {lead_info.get('contact_details')}")
                print(f"- Pain points count: {len(lead_info.get('pain_points', []))}")
                print(f"- Requirements count: {len(lead_info.get('requirements', []))}")
            
            print("\n📋 Frontend Expectations vs Reality:")
            print("Frontend expects:")
            print("- analysis.lead_info or analysis.lead_information")
            print("- analysis.pain_points")
            print("- analysis.requirements")
            print("- analysis.quality_score")
            
            print("\nAPI actually returns:")
            for key in data.keys():
                print(f"- {key}: {type(data[key])}")
                
        else:
            print(f"\n❌ API Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error text: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Django server is not running")
        print("Please start the server with: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🔧 SOLUTION:")
    print("The frontend JavaScript needs to match the actual API response structure.")
    print("Check the browser console (F12) when testing to see the actual response.")
    
    return True

if __name__ == "__main__":
    test_api_response()