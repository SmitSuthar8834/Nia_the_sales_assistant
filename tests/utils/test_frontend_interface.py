#!/usr/bin/env python
"""
Frontend Interface Test Script
Tests the complete frontend interface functionality including API endpoints
"""
import os
import sys
from pathlib import Path

import django
import requests

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nia_sales_assistant.settings")
django.setup()

# Test configuration
BASE_URL = "http://127.0.0.1:8000"
API_BASE_URL = f"{BASE_URL}/api/ai"

# Test conversation data
TEST_CONVERSATION = """
Sales Rep (Sarah): Good afternoon, Mr. Rodriguez. Thank you for taking the time to meet with me today. I understand from our initial conversation that DataFlow Solutions is experiencing some challenges with your current customer management processes?

Prospect (Miguel Rodriguez - VP of Operations): That's right, Sarah. We're a mid-market logistics company with about 350 employees across five locations. Honestly, we're drowning in spreadsheets and our team is using three different systems that don't talk to each other. But before we go further, I need to be upfront—we just implemented a new ERP system six months ago, and there's some... let's call it "change fatigue" in the organization.

Sarah: I completely understand that concern, Miguel. Change fatigue is real, and the last thing any organization needs is another disruptive implementation. Can you help me understand what specific pain points are driving you to consider a CRM solution despite the recent ERP rollout?

Miguel: Well, our customer retention has dropped 12% over the past year. Our account managers are spending 60% of their time on administrative tasks instead of actually managing relationships. And here's the kicker—last month we lost a $2.3 million contract because three different team members contacted the same client with conflicting information. The client felt we were disorganized and unprofessional.
"""


def test_server_running():
    """Test if Django server is running"""
    print("🔍 Testing if Django server is running...")
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Django server is running")
            return True
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Server is not running: {e}")
        print("💡 Please run: python manage.py runserver")
        return False


def test_frontend_loads():
    """Test if the main frontend page loads"""
    print("\n🔍 Testing frontend page load...")
    try:
        response = requests.get(BASE_URL, timeout=10)
        if response.status_code == 200:
            content = response.text
            # Check for key elements
            checks = [
                ("NIA - Neural Intelligence Assistant", "Page title"),
                ("Lead Management", "Lead management section"),
                ("Create New Lead", "Create lead button"),
                ("main.css", "CSS file reference"),
                ("api.js", "API JavaScript file"),
                ("ui.js", "UI JavaScript file"),
                ("main.js", "Main JavaScript file"),
            ]

            all_passed = True
            for check_text, description in checks:
                if check_text in content:
                    print(f"  ✅ {description} found")
                else:
                    print(f"  ❌ {description} missing")
                    all_passed = False

            if all_passed:
                print("✅ Frontend page loads correctly with all required elements")
                return True
            else:
                print("❌ Frontend page missing some elements")
                return False
        else:
            print(f"❌ Frontend page failed to load: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error loading frontend: {e}")
        return False


def test_static_files():
    """Test if static files are accessible"""
    print("\n🔍 Testing static files accessibility...")
    static_files = [
        "/static/css/main.css",
        "/static/js/api.js",
        "/static/js/ui.js",
        "/static/js/main.js",
    ]

    all_passed = True
    for file_path in static_files:
        try:
            response = requests.get(BASE_URL + file_path, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ {file_path} accessible")
            else:
                print(f"  ❌ {file_path} not accessible ({response.status_code})")
                all_passed = False
        except Exception as e:
            print(f"  ❌ {file_path} error: {e}")
            all_passed = False

    return all_passed


def test_api_endpoints():
    """Test API endpoints functionality"""
    print("\n🔍 Testing API endpoints...")

    # Test debug endpoint
    try:
        response = requests.get(f"{API_BASE_URL}/debug-test/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("  ✅ Debug endpoint working")
            else:
                print("  ❌ Debug endpoint returned success=false")
                return False
        else:
            print(f"  ❌ Debug endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Debug endpoint error: {e}")
        return False

    # Test conversation analysis endpoint
    try:
        payload = {
            "conversation_text": TEST_CONVERSATION,
            "context": {"source": "meeting", "urgency": "high"},
        }
        response = requests.post(
            f"{API_BASE_URL}/analyze/",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("lead_information"):
                print("  ✅ Conversation analysis endpoint working")
                print(
                    f"    - Extracted company: {data['lead_information'].get('company_name', 'N/A')}"
                )
                print(
                    f"    - Contact: {data['lead_information'].get('contact_details', {}).get('name', 'N/A')}"
                )
                print(
                    f"    - Pain points: {len(data['lead_information'].get('pain_points', []))}"
                )
            else:
                print("  ❌ Analysis endpoint returned invalid data")
                return False
        else:
            print(f"  ❌ Analysis endpoint failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"    Error: {error_data}")
            except:
                print(f"    Response: {response.text[:200]}...")
            return False
    except Exception as e:
        print(f"  ❌ Analysis endpoint error: {e}")
        return False

    # Test leads endpoint
    try:
        response = requests.get(f"{API_BASE_URL}/leads/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(
                f"  ✅ Leads endpoint working (found {len(data.get('results', []))} leads)"
            )
        else:
            print(f"  ❌ Leads endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Leads endpoint error: {e}")
        return False

    # Test analytics endpoint
    try:
        response = requests.get(f"{API_BASE_URL}/analytics/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Analytics endpoint working")
            print(f"    - Total leads: {data.get('total_leads', 0)}")
        else:
            print(f"  ❌ Analytics endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Analytics endpoint error: {e}")
        return False

    return True


def test_lead_creation_workflow():
    """Test the complete lead creation workflow"""
    print("\n🔍 Testing lead creation workflow...")

    try:
        # Create a lead using the API
        lead_data = {
            "company_name": "Test Company Inc",
            "contact_info": {
                "name": "John Test",
                "email": "john@testcompany.com",
                "phone": "555-0123",
            },
            "source": "meeting",
            "conversation_text": TEST_CONVERSATION,
            "pain_points": ["Data silos", "Manual processes"],
            "requirements": ["CRM integration", "Automation"],
        }

        response = requests.post(
            f"{API_BASE_URL}/leads/",
            json=lead_data,
            headers={"Content-Type": "application/json"},
            timeout=15,
        )

        if response.status_code == 201:
            data = response.json()
            lead_id = data["lead"]["id"]
            print(f"  ✅ Lead created successfully (ID: {lead_id})")

            # Test retrieving the created lead
            response = requests.get(f"{API_BASE_URL}/leads/{lead_id}/", timeout=10)
            if response.status_code == 200:
                lead_data = response.json()
                print(f"  ✅ Lead retrieval working")
                print(f"    - Company: {lead_data.get('company_name')}")
                print(f"    - Contact: {lead_data.get('contact_name')}")
                return True
            else:
                print(f"  ❌ Lead retrieval failed: {response.status_code}")
                return False
        else:
            print(f"  ❌ Lead creation failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"    Error: {error_data}")
            except:
                print(f"    Response: {response.text[:200]}...")
            return False

    except Exception as e:
        print(f"  ❌ Lead creation workflow error: {e}")
        return False


def test_comprehensive_recommendations():
    """Test comprehensive recommendations endpoint"""
    print("\n🔍 Testing comprehensive recommendations...")

    try:
        lead_data = {
            "company_name": "DataFlow Solutions",
            "contact_details": {
                "name": "Miguel Rodriguez",
                "title": "VP of Operations",
            },
            "pain_points": [
                "Customer retention dropped 12%",
                "Lost $2.3M contract",
                "Account managers spending 60% time on admin",
            ],
            "requirements": [
                "Unified customer data platform",
                "ERP integration",
                "Phased implementation",
            ],
            "budget_info": "$50K-$150K annually",
            "industry": "Logistics",
            "company_size": "350 employees",
        }

        response = requests.post(
            f"{API_BASE_URL}/comprehensive-recommendations/",
            json={"lead_data": lead_data},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                recommendations = data.get("recommendations", {})
                print("  ✅ Comprehensive recommendations working")
                print(
                    f"    - Quality score: {recommendations.get('quality_score', 'N/A')}"
                )
                print(
                    f"    - Conversion probability: {recommendations.get('conversion_probability', 'N/A')}"
                )
                print(f"    - Next steps: {len(recommendations.get('next_steps', []))}")
                return True
            else:
                print("  ❌ Recommendations returned success=false")
                return False
        else:
            print(f"  ❌ Recommendations endpoint failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"    Error: {error_data}")
            except:
                print(f"    Response: {response.text[:200]}...")
            return False

    except Exception as e:
        print(f"  ❌ Recommendations error: {e}")
        return False


def run_all_tests():
    """Run all frontend interface tests"""
    print("=" * 60)
    print("🧪 FRONTEND INTERFACE TEST SUITE")
    print("=" * 60)

    tests = [
        ("Server Running", test_server_running),
        ("Frontend Loads", test_frontend_loads),
        ("Static Files", test_static_files),
        ("API Endpoints", test_api_endpoints),
        ("Lead Creation", test_lead_creation_workflow),
        ("AI Recommendations", test_comprehensive_recommendations),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1

    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Frontend interface is working correctly.")
        print("\n💡 Next steps:")
        print("   1. Open http://127.0.0.1:8000 in your browser")
        print("   2. Test the lead creation form with conversation text")
        print("   3. Verify AI analysis results display properly")
        print("   4. Check lead list and detail views")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please check the issues above.")
        print("\n🔧 Common fixes:")
        print("   1. Make sure Django server is running: python manage.py runserver")
        print("   2. Check that all static files are properly configured")
        print("   3. Verify API endpoints are accessible")
        print("   4. Ensure Gemini API key is configured correctly")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
