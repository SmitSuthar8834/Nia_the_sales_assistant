#!/usr/bin/env python
"""
Test script to debug the create lead button issue
"""
import requests
import json

def test_analysis_response():
    """Test what the analysis API actually returns"""
    print("🔍 Testing Analysis API Response Structure")
    print("=" * 50)
    
    test_conversation = """
    I spoke with Miguel Rodriguez from DataFlow Solutions. They're a logistics company 
    with 350 employees. They lost a $2.3 million contract due to poor customer management.
    Miguel is the VP of Operations and they need a CRM system.
    """
    
    try:
        # Test the analysis endpoint
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
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n✅ Analysis Response Structure:")
            print("Top-level keys:", list(data.keys()))
            
            # Check what the frontend expects vs what we get
            print("\n🔍 Frontend Expectations vs Reality:")
            
            # Check for lead information
            if 'lead_information' in data:
                print("✅ Has 'lead_information'")
                lead_info = data['lead_information']
                print(f"   - company_name: {lead_info.get('company_name')}")
                print(f"   - contact_details: {lead_info.get('contact_details')}")
                print(f"   - pain_points: {len(lead_info.get('pain_points', []))} items")
                print(f"   - requirements: {len(lead_info.get('requirements', []))} items")
            else:
                print("❌ Missing 'lead_information'")
            
            if 'lead_info' in data:
                print("✅ Has 'lead_info'")
            else:
                print("❌ Missing 'lead_info'")
            
            # Check for direct pain_points and requirements
            if 'pain_points' in data:
                print(f"✅ Has direct 'pain_points': {len(data['pain_points'])} items")
            else:
                print("❌ Missing direct 'pain_points'")
                
            if 'requirements' in data:
                print(f"✅ Has direct 'requirements': {len(data['requirements'])} items")
            else:
                print("❌ Missing direct 'requirements'")
            
            # Show the structure that would work for lead creation
            print("\n📋 Data Structure for Lead Creation:")
            if 'lead_information' in data:
                lead_info = data['lead_information']
                lead_data = {
                    'company_name': lead_info.get('company_name', 'Unknown'),
                    'contact_info': {
                        'name': lead_info.get('contact_details', {}).get('name', ''),
                        'email': lead_info.get('contact_details', {}).get('email', ''),
                        'phone': lead_info.get('contact_details', {}).get('phone', '')
                    },
                    'pain_points': lead_info.get('pain_points', []),
                    'requirements': lead_info.get('requirements', []),
                    'industry': lead_info.get('industry', ''),
                    'company_size': lead_info.get('company_size', ''),
                    'budget_info': lead_info.get('budget_info', ''),
                    'timeline': lead_info.get('timeline', ''),
                    'urgency_level': lead_info.get('urgency_level', 'medium')
                }
                print(json.dumps(lead_data, indent=2))
                
                # Test lead creation
                print("\n🧪 Testing Lead Creation...")
                create_response = requests.post(
                    'http://127.0.0.1:8000/api/ai/leads/',
                    json=lead_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=15
                )
                
                print(f"Create Lead Status: {create_response.status_code}")
                if create_response.status_code == 201:
                    create_data = create_response.json()
                    print("✅ Lead created successfully!")
                    print(f"Lead ID: {create_data.get('lead', {}).get('id')}")
                else:
                    print("❌ Lead creation failed")
                    try:
                        error_data = create_response.json()
                        print(f"Error: {json.dumps(error_data, indent=2)}")
                    except:
                        print(f"Error text: {create_response.text}")
            
        else:
            print(f"❌ Analysis failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error text: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Django server is not running")
        print("Please start the server with: python manage.py runserver")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_analysis_response()