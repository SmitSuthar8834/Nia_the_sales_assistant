#!/usr/bin/env python
"""
Complete Frontend Test Runner
This script provides comprehensive testing for the NIA Sales Assistant frontend interface
"""
import subprocess
import sys
from pathlib import Path

import requests


def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"🧪 {title}")
    print("=" * 60)


def print_step(step, description):
    """Print a formatted step"""
    print(f"\n{step}. {description}")
    print("-" * 40)


def check_django_server():
    """Check if Django server is running"""
    try:
        response = requests.get("http://127.0.0.1:8000", timeout=3)
        return response.status_code == 200
    except:
        return False


def run_django_server():
    """Instructions for running Django server"""
    print("🚀 Django Server Setup")
    print("To run the tests, you need to start the Django server first.")
    print("\nIn a separate terminal window, run:")
    print("  python manage.py runserver")
    print("\nThen press Enter here to continue with the tests...")
    input()


def test_ai_backend():
    """Test the AI backend functionality"""
    print_step("1", "Testing AI Backend")

    try:
        # Run the AI test script
        result = subprocess.run(
            [sys.executable, "test_ai_api.py"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            print("✅ AI Backend tests passed")
            # Show summary from output
            lines = result.stdout.split("\n")
            for line in lines:
                if "Test Results" in line or "✅ PASS" in line or "❌ FAIL" in line:
                    print(f"   {line}")
            return True
        else:
            print("❌ AI Backend tests failed")
            print("Error output:")
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("❌ AI Backend tests timed out")
        return False
    except Exception as e:
        print(f"❌ Error running AI tests: {e}")
        return False


def test_api_endpoints():
    """Test API endpoints"""
    print_step("2", "Testing API Endpoints")

    if not check_django_server():
        print("❌ Django server is not running")
        print("Please start the server with: python manage.py runserver")
        return False

    try:
        result = subprocess.run(
            [sys.executable, "test_frontend_api.py"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if "ALL TESTS PASSED" in result.stdout:
            print("✅ All API endpoint tests passed")
            return True
        else:
            print("❌ Some API endpoint tests failed")
            print("Output:")
            print(result.stdout)
            if result.stderr:
                print("Errors:")
                print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running API tests: {e}")
        return False


def test_frontend_interface():
    """Test frontend interface"""
    print_step("3", "Testing Frontend Interface")

    if not check_django_server():
        print("❌ Django server is not running")
        return False

    try:
        result = subprocess.run(
            [sys.executable, "test_frontend_interface.py"],
            capture_output=True,
            text=True,
            timeout=180,
        )

        if "ALL TESTS PASSED" in result.stdout:
            print("✅ All frontend interface tests passed")
            return True
        else:
            print("❌ Some frontend interface tests failed")
            print("Output:")
            print(result.stdout[-1000:])  # Show last 1000 chars
            return False
    except Exception as e:
        print(f"❌ Error running frontend tests: {e}")
        return False


def manual_test_instructions():
    """Provide manual testing instructions"""
    print_step("4", "Manual Testing Instructions")

    print("📋 Manual Testing Checklist:")
    print("\n1. Open your browser and go to: http://127.0.0.1:8000")
    print("2. Verify the main interface loads with:")
    print("   - NIA header and navigation")
    print("   - Leads, Create Lead, Analytics tabs")
    print("   - Professional styling and layout")

    print("\n3. Test Lead Creation:")
    print("   - Click 'Create Lead' tab")
    print("   - Paste the test conversation (provided below)")
    print("   - Select 'Meeting' as source")
    print("   - Click 'Analyze & Create Lead'")
    print("   - Verify AI analysis results appear")
    print("   - Click 'Create Lead' to save")

    print("\n4. Test Lead List:")
    print("   - Click 'Leads' tab")
    print("   - Verify created lead appears in list")
    print("   - Check lead score badge")
    print("   - Click on lead to view details")

    print("\n5. Test Lead Details:")
    print("   - Verify lead information displays correctly")
    print("   - Check AI insights section")
    print("   - Verify recommendations and action buttons")

    print("\n6. Test Analytics:")
    print("   - Click 'Analytics' tab")
    print("   - Verify statistics display")

    print("\n📝 Test Conversation Text:")
    print("-" * 40)
    print(
        """Sales Rep (Sarah): Good afternoon, Mr. Rodriguez. Thank you for taking the time to meet with me today. I understand from our initial conversation that DataFlow Solutions is experiencing some challenges with your current customer management processes?

Prospect (Miguel Rodriguez - VP of Operations): That's right, Sarah. We're a mid-market logistics company with about 350 employees across five locations. Honestly, we're drowning in spreadsheets and our team is using three different systems that don't talk to each other. But before we go further, I need to be upfront—we just implemented a new ERP system six months ago, and there's some... let's call it "change fatigue" in the organization.

Miguel: Well, our customer retention has dropped 12% over the past year. Our account managers are spending 60% of their time on administrative tasks instead of actually managing relationships. And here's the kicker—last month we lost a $2.3 million contract because three different team members contacted the same client with conflicting information. The client felt we were disorganized and unprofessional."""
    )

    print("\n🌐 Alternative Manual Test:")
    print(f"Open: file://{Path.cwd()}/test_frontend_manual.html")
    print("This provides an interactive test interface")


def generate_test_report(results):
    """Generate a test report"""
    print_header("TEST REPORT")

    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)

    print(f"📊 Test Summary:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Failed: {total_tests - passed_tests}")
    print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")

    print(f"\n📋 Detailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name:.<30} {status}")

    if passed_tests == total_tests:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✨ The NIA Sales Assistant frontend is ready for use!")
        print(f"\n🚀 Next Steps:")
        print(f"   1. Open http://127.0.0.1:8000 in your browser")
        print(f"   2. Test the interface manually using the checklist above")
        print(f"   3. Create leads and verify AI analysis works")
        print(f"   4. Check that all features work as expected")
    else:
        print(f"\n⚠️  Some tests failed. Please check the issues above.")
        print(f"🔧 Common solutions:")
        print(f"   1. Ensure Django server is running: python manage.py runserver")
        print(f"   2. Check Gemini API key is configured in .env")
        print(f"   3. Verify database is set up: python manage.py migrate")
        print(f"   4. Check that all dependencies are installed")


def main():
    """Main test runner"""
    print_header("NIA SALES ASSISTANT FRONTEND TEST SUITE")

    print("This script will test the complete frontend interface including:")
    print("• AI backend functionality")
    print("• API endpoints")
    print("• Frontend interface")
    print("• Manual testing guidance")

    # Check if server is running
    if not check_django_server():
        run_django_server()

    # Run tests
    results = {}

    # Test 1: AI Backend
    results["AI Backend"] = test_ai_backend()

    # Test 2: API Endpoints (only if server is running)
    if check_django_server():
        results["API Endpoints"] = test_api_endpoints()
        results["Frontend Interface"] = test_frontend_interface()
    else:
        print("⚠️  Skipping API and Frontend tests - server not running")
        results["API Endpoints"] = False
        results["Frontend Interface"] = False

    # Manual testing instructions
    manual_test_instructions()

    # Generate report
    generate_test_report(results)


if __name__ == "__main__":
    main()
