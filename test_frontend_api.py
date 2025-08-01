#!/usr/bin/env python
"""
Frontend API Test Script
Quick test script to verify API endpoints are working for the frontend
"""
import requests
import json
import time

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_BASE_URL = f"{BASE_URL}/api/ai"

# Test data
TEST_CONVERSATION = """
Sales Rep: Good afternoon, Mr. Rodriguez. I understand DataFlow Solutions is experiencing challenges with customer management?

Miguel Rodriguez (VP Operations): That's right. We're a logistics company with 350 employees across five locations. We're drowning in spreadsheets and using three different systems that don't talk to each other. Our customer retention dropped 12% and we lost a $2.3 million contract due to conflicting information.

Sales Rep: That's a significant challenge. What specific pain points are driving you to consider a CRM solution?

Miguel: Our account managers spend 60% of their time on admin tasks instead of managing relationships. We need a unified view of customer data and better integration with our new ERP system.
"""

def quick_api_test():
    """Run a quick test of all API endpoints"""
    print("🚀 Quick Frontend API Test")
    print("=" * 50)
    
    tests = []
    
    # Test 1: Server connectivity
    print("1. Testing server connectivity...")
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code == 200:
            print("   ✅ Server is running")
            tests.append(("Server", True))
        else:
            print(f"   ❌ Server returned {response.status_code}")
            tests.append(("Server", False))
    except Exception as e:
        print(f"   ❌ Server connection failed: {e}")
        tests.append(("Server", False))
        return tests
    
    # Test 2: Debug endpoint
    print("\n2. Testing debug endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/debug-test/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("   ✅ Debug endpoint working")
                tests.append(("Debug API", True))
            else:
                print("   ❌ Debug endpoint returned success=false")
                tests.append(("Debug API", False))
        else:
            print(f"   ❌ Debug endpoint failed: {response.status_code}")
            tests.append(("Debug API", False))
    except Exception as e:
        print(f"   ❌ Debug endpoint error: {e}")
        tests.append(("Debug API", False))
    
    # Test 3: Conversation analysis
    print("\n3. Testing conversation analysis...")
    try:
        payload = {
            "conversation_text": TEST_CONVERSATION,
            "context": {"source": "meeting", "urgency": "high"}
        }
        response = requests.post(
            f"{API_BASE_URL}/analyze/",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('lead_information'):
                lead_info = data['lead_information']
                print(f"   ✅ Analysis working - Company: {lead_info.get('company_name', 'N/A')}")
                print(f"      Contact: {lead_info.get('contact_details', {}).get('name', 'N/A')}")
                print(f"      Pain points: {len(lead_info.get('pain_points', []))}")
                print(f"      Confidence: {lead_info.get('extraction_metadata', {}).get('confidence_score', 'N/A')}%")
                tests.append(("Analysis", True))
            else:
                print("   ❌ Analysis returned invalid data")
                tests.append(("Analysis", False))
        else:
            print(f"   ❌ Analysis failed: {response.status_code}")
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    error_data = response.json()
                    print(f"      Error: {error_data.get('error', 'Unknown')}")
                except:
                    pass
            tests.append(("Analysis", False))
    except Exception as e:
        print(f"   ❌ Analysis error: {e}")
        tests.append(("Analysis", False))
    
    # Test 4: Lead management
    print("\n4. Testing lead management...")
    try:
        # Get existing leads
        response = requests.get(f"{API_BASE_URL}/leads/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            lead_count = len(data.get('results', []))
            print(f"   ✅ Lead retrieval working - Found {lead_count} leads")
            
            # Try creating a lead
            lead_data = {
                "company_name": f"Test Company {int(time.time())}",
                "contact_info": {
                    "name": "Test Contact",
                    "email": "test@example.com"
                },
                "source": "api_test",
                "pain_points": ["Test pain point"],
                "requirements": ["Test requirement"]
            }
            
            create_response = requests.post(
                f"{API_BASE_URL}/leads/",
                json=lead_data,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            
            if create_response.status_code == 201:
                create_data = create_response.json()
                print(f"   ✅ Lead creation working - ID: {create_data.get('lead', {}).get('id', 'N/A')}")
                tests.append(("Lead Management", True))
            else:
                print(f"   ⚠️  Lead retrieval works but creation failed: {create_response.status_code}")
                tests.append(("Lead Management", False))
        else:
            print(f"   ❌ Lead management failed: {response.status_code}")
            tests.append(("Lead Management", False))
    except Exception as e:
        print(f"   ❌ Lead management error: {e}")
        tests.append(("Lead Management", False))
    
    # Test 5: AI Recommendations
    print("\n5. Testing AI recommendations...")
    try:
        rec_data = {
            "lead_data": {
                "company_name": "DataFlow Solutions",
                "contact_details": {"name": "Miguel Rodriguez", "title": "VP Operations"},
                "pain_points": ["Customer retention issues", "Admin burden"],
                "requirements": ["CRM integration", "Process automation"],
                "budget_info": "$100K",
                "industry": "Logistics"
            }
        }
        
        response = requests.post(
            f"{API_BASE_URL}/comprehensive-recommendations/",
            json=rec_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('recommendations'):
                rec = data['recommendations']
                print(f"   ✅ Recommendations working")
                print(f"      Quality Score: {rec.get('quality_score', 'N/A')}")
                print(f"      Conversion Probability: {rec.get('conversion_probability', 'N/A')}%")
                print(f"      Next Steps: {len(rec.get('next_steps', []))}")
                tests.append(("Recommendations", True))
            else:
                print("   ❌ Recommendations returned invalid data")
                tests.append(("Recommendations", False))
        else:
            print(f"   ❌ Recommendations failed: {response.status_code}")
            tests.append(("Recommendations", False))
    except Exception as e:
        print(f"   ❌ Recommendations error: {e}")
        tests.append(("Recommendations", False))
    
    # Test 6: Analytics
    print("\n6. Testing analytics...")
    try:
        response = requests.get(f"{API_BASE_URL}/analytics/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Analytics working")
            print(f"      Total Leads: {data.get('total_leads', 0)}")
            print(f"      High Quality: {data.get('high_quality_leads', 0)}")
            print(f"      Avg Score: {data.get('average_lead_score', 'N/A')}")
            tests.append(("Analytics", True))
        else:
            print(f"   ❌ Analytics failed: {response.status_code}")
            tests.append(("Analytics", False))
    except Exception as e:
        print(f"   ❌ Analytics error: {e}")
        tests.append(("Analytics", False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<20} {status}")
    
    print("-" * 50)
    print(f"Total: {passed}/{total} ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✨ Frontend API is ready for use!")
        print(f"\n🌐 Open your browser to: {BASE_URL}")
        print("📝 Use the manual test page: test_frontend_manual.html")
    else:
        print(f"\n⚠️  {total-passed} tests failed")
        print("🔧 Check the Django server and API configuration")
    
    return tests

if __name__ == "__main__":
    quick_api_test()