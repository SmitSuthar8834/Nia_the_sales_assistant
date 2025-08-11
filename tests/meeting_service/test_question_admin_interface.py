#!/usr/bin/env python
"""
Test script for Question Admin Interface functionality
"""

import os
import sys
from pathlib import Path

import django

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from django.contrib.auth import get_user_model
from django.test import Client

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nia_sales_assistant.settings")
django.setup()

from ai_service.models import Lead
from meeting_service.models import Meeting, MeetingQuestion, QuestionTemplate

User = get_user_model()


def test_question_admin_interface():
    """Test the question admin interface functionality"""

    print("🧪 Testing Question Admin Interface...")

    # Create test user
    try:
        admin_user = User.objects.create_superuser(
            username="testadmin", email="admin@test.com", password="testpass123"
        )
        print("✅ Created test admin user")
    except Exception as e:
        print(f"⚠️ Admin user might already exist: {e}")
        admin_user = User.objects.get(username="testadmin")

    # Create test lead
    try:
        test_lead = Lead.objects.create(
            user=admin_user,
            company_name="Test Company",
            contact_info={
                "name": "John Doe",
                "email": "john@testcompany.com",
                "phone": "+1-555-0123",
                "title": "CTO",
            },
            industry="Technology",
            status="new",
        )
        print("✅ Created test lead")
    except Exception as e:
        print(f"⚠️ Test lead creation failed: {e}")
        return False

    # Create test meeting
    try:
        from datetime import timedelta

        from django.utils import timezone

        test_meeting = Meeting.objects.create(
            lead=test_lead,
            title="Test Discovery Meeting",
            meeting_type="discovery",
            scheduled_at=timezone.now() + timedelta(days=1),
            status="scheduled",
        )
        print("✅ Created test meeting")
    except Exception as e:
        print(f"⚠️ Test meeting creation failed: {e}")
        return False

    # Create test question template
    try:
        test_template = QuestionTemplate.objects.create(
            name="Test Discovery Template",
            industry="Technology",
            template_type="discovery",
            question_category="pain_points",
            question_template="What are your main challenges with {current_solution}?",
            variables=["current_solution"],
            rationale="This question helps identify pain points in current solutions",
            priority=8,
            confidence_score=85.0,
            is_active=True,
        )
        print("✅ Created test question template")
    except Exception as e:
        print(f"⚠️ Test template creation failed: {e}")
        return False

    # Create test meeting question
    try:
        test_question = MeetingQuestion.objects.create(
            meeting=test_meeting,
            question_text="What are your main challenges with your current CRM system?",
            question_type="pain_points",
            priority=8,
            ai_generated=True,
            confidence_score=85.0,
            generation_context={
                "template_id": str(test_template.id),
                "rationale": "Identify pain points in current CRM solution",
                "expected_insights": ["Integration issues", "User adoption challenges"],
                "follow_up_triggers": ["If mentions integration", "If mentions cost"],
            },
        )
        print("✅ Created test meeting question")
    except Exception as e:
        print(f"⚠️ Test question creation failed: {e}")
        return False

    # Test admin URLs
    client = Client()

    try:
        # Login as admin
        login_success = client.login(username="testadmin", password="testpass123")
        if not login_success:
            print("❌ Failed to login as admin")
            return False
        print("✅ Successfully logged in as admin")

        # Test question template admin list
        response = client.get("/admin/meeting_service/questiontemplate/")
        if response.status_code == 200:
            print("✅ Question template admin list accessible")
        else:
            print(f"❌ Question template admin list failed: {response.status_code}")
            return False

        # Test meeting question admin list
        response = client.get("/admin/meeting_service/meetingquestion/")
        if response.status_code == 200:
            print("✅ Meeting question admin list accessible")
        else:
            print(f"❌ Meeting question admin list failed: {response.status_code}")
            return False

        # Test meeting admin list
        response = client.get("/admin/meeting_service/meeting/")
        if response.status_code == 200:
            print("✅ Meeting admin list accessible")
        else:
            print(f"❌ Meeting admin list failed: {response.status_code}")
            return False

        # Test question template detail view
        response = client.get(
            f"/admin/meeting_service/questiontemplate/{test_template.id}/change/"
        )
        if response.status_code == 200:
            print("✅ Question template detail view accessible")
        else:
            print(f"❌ Question template detail view failed: {response.status_code}")
            return False

        # Test meeting question detail view
        response = client.get(
            f"/admin/meeting_service/meetingquestion/{test_question.id}/change/"
        )
        if response.status_code == 200:
            print("✅ Meeting question detail view accessible")
        else:
            print(f"❌ Meeting question detail view failed: {response.status_code}")
            return False

        print("🎉 All admin interface tests passed!")
        return True

    except Exception as e:
        print(f"❌ Admin interface test failed: {e}")
        return False

    finally:
        # Cleanup test data
        try:
            test_question.delete()
            test_template.delete()
            test_meeting.delete()
            test_lead.delete()
            print("🧹 Cleaned up test data")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")


def test_static_files():
    """Test that static files are properly configured"""

    print("\n📁 Testing Static Files...")

    static_files = [
        "static/admin/css/question_template_admin.css",
        "static/admin/css/meeting_question_admin.css",
        "static/admin/js/question_template_actions.js",
        "static/admin/js/meeting_question_actions.js",
    ]

    all_exist = True
    for file_path in static_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False

    return all_exist


def test_template_files():
    """Test that template files are properly configured"""

    print("\n📄 Testing Template Files...")

    template_files = [
        "templates/admin/meeting_service/questiontemplate/test_template.html",
        "templates/admin/meeting_service/questiontemplate/analytics.html",
    ]

    all_exist = True
    for file_path in template_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False

    return all_exist


def main():
    """Run all tests"""

    print("🚀 Starting Question Admin Interface Tests\n")

    # Test static files
    static_ok = test_static_files()

    # Test template files
    template_ok = test_template_files()

    # Test admin interface
    admin_ok = test_question_admin_interface()

    print(f"\n📊 Test Results:")
    print(f"Static Files: {'✅ PASS' if static_ok else '❌ FAIL'}")
    print(f"Template Files: {'✅ PASS' if template_ok else '❌ FAIL'}")
    print(f"Admin Interface: {'✅ PASS' if admin_ok else '❌ FAIL'}")

    if static_ok and template_ok and admin_ok:
        print("\n🎉 All tests passed! Question Admin Interface is ready.")
        return True
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
