#!/usr/bin/env python
"""
Test script to verify the Meeting Actions in Lead Admin implementation
"""

import os
import sys
from pathlib import Path

import django

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))


# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nia_sales_assistant.settings")
django.setup()
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model

from ai_service.admin import LeadAdmin
from ai_service.models import Lead
from meeting_service.models import Meeting

User = get_user_model()


def test_lead_admin_meeting_actions():
    """Test that the Lead Admin has meeting action buttons"""
    print("Testing Lead Admin Meeting Actions Implementation...")

    # Get or create test user
    user, created = User.objects.get_or_create(
        username="testuser",
        defaults={"email": "test@example.com", "is_staff": True, "is_superuser": True},
    )
    if created:
        user.set_password("testpass123")
        user.save()

    # Create test lead
    lead = Lead.objects.create(
        user=user,
        company_name="Test Company",
        industry="Technology",
        status="new",
        contact_info={
            "name": "John Doe",
            "email": "john@testcompany.com",
            "phone": "+1234567890",
        },
        pain_points=["Slow processes", "High costs"],
        requirements=["Automation", "Cost reduction"],
        budget_info="$50,000 - $100,000",
        timeline="Q1 2024",
    )

    # Test LeadAdmin methods
    admin_site = AdminSite()
    lead_admin = LeadAdmin(Lead, admin_site)

    # Test lead_actions method
    print("✓ Testing lead_actions method...")
    actions_html = lead_admin.lead_actions(lead)
    assert (
        "quickScheduleMeeting" in actions_html
    ), "Quick schedule meeting button not found"
    assert "scheduleMeeting" in actions_html, "Schedule meeting button not found"
    assert "📅" in actions_html, "Meeting emoji not found in actions"
    print("  ✓ Lead actions contain meeting buttons")

    # Test meeting_scheduling_widget method
    print("✓ Testing meeting_scheduling_widget method...")
    widget_html = lead_admin.meeting_scheduling_widget(lead)
    assert "meeting-scheduling-widget" in widget_html, "Meeting widget class not found"
    assert "Schedule New Meeting" in widget_html, "Schedule button not found in widget"
    assert (
        "Auto-Populated Meeting Details" in widget_html
    ), "Auto-populated section not found"
    assert (
        "AI Meeting Recommendations" in widget_html
    ), "AI recommendations section not found"
    assert lead.company_name in widget_html, "Company name not auto-populated"
    print("  ✓ Meeting scheduling widget contains all required sections")

    # Test that widget shows lead context
    assert lead.contact_info["name"] in widget_html, "Contact name not shown in widget"
    assert lead.industry in widget_html, "Industry not shown in widget"
    assert ", ".join(lead.pain_points) in widget_html, "Pain points not shown in widget"
    print("  ✓ Widget auto-populates lead data correctly")

    # Create a test meeting and verify it shows in widget
    meeting = Meeting.objects.create(
        lead=lead,
        title=f"Meeting with {lead.company_name}",
        meeting_type="discovery",
        scheduled_at="2024-12-10 10:00:00+00:00",
        duration_minutes=60,
        status="scheduled",
    )

    widget_html_with_meeting = lead_admin.meeting_scheduling_widget(lead)
    assert meeting.title in widget_html_with_meeting, "Meeting not shown in widget"
    assert (
        "Recent Meetings" in widget_html_with_meeting
    ), "Recent meetings section not found"
    print("  ✓ Widget displays existing meetings")

    print("\n✅ All Lead Admin Meeting Actions tests passed!")

    # Test admin URLs exist
    print("\n✓ Testing admin URL patterns...")
    from meeting_service import urls

    # Check that admin action URLs are defined
    url_patterns = [str(pattern.pattern) for pattern in urls.urlpatterns]
    admin_urls = [url for url in url_patterns if "admin/meeting_service/meeting" in url]

    assert (
        len(admin_urls) >= 4
    ), f"Expected at least 4 admin URLs, found {len(admin_urls)}"
    print(f"  ✓ Found {len(admin_urls)} admin action URLs")

    # Test that static files exist
    print("\n✓ Testing static files...")
    import os

    js_files = [
        "static/admin/js/meeting_actions.js",
        "static/admin/js/lead_meeting_actions.js",
    ]

    css_files = [
        "static/admin/css/meeting_admin.css",
        "static/admin/css/lead_meeting_widget.css",
    ]

    for js_file in js_files:
        assert os.path.exists(js_file), f"JavaScript file {js_file} not found"
        print(f"  ✓ {js_file} exists")

    for css_file in css_files:
        assert os.path.exists(css_file), f"CSS file {css_file} not found"
        print(f"  ✓ {css_file} exists")

    print("\n✅ All static files exist!")

    # Test JavaScript functions exist
    print("\n✓ Testing JavaScript functions...")

    with open("static/admin/js/lead_meeting_actions.js", "r") as f:
        js_content = f.read()

    required_functions = [
        "scheduleMeeting",
        "quickScheduleMeeting",
        "generateMeetingAgenda",
        "createMeetingModal",
        "populateMeetingForm",
        "submitMeetingForm",
    ]

    for func in required_functions:
        assert (
            f"function {func}" in js_content
        ), f"Function {func} not found in JavaScript"
        print(f"  ✓ {func} function exists")

    print("\n✅ All JavaScript functions exist!")

    # Clean up
    meeting.delete()
    lead.delete()
    # Don't delete user as it might be used elsewhere

    print(
        "\n🎉 All tests passed! Meeting Actions in Lead Admin implementation is working correctly!"
    )

    return True


def test_meeting_admin_views():
    """Test that the meeting admin action views work"""
    print("\n✓ Testing Meeting Admin Action Views...")

    # Test that views are importable
    from meeting_service.views import (
        cancel_meeting_admin,
        complete_meeting_admin,
        create_meeting_admin,
        start_meeting_admin,
    )

    print("  ✓ All admin action views are importable")

    # Test view decorators
    assert hasattr(
        start_meeting_admin, "__wrapped__"
    ), "start_meeting_admin not properly decorated"
    assert hasattr(
        complete_meeting_admin, "__wrapped__"
    ), "complete_meeting_admin not properly decorated"
    assert hasattr(
        cancel_meeting_admin, "__wrapped__"
    ), "cancel_meeting_admin not properly decorated"
    assert hasattr(
        create_meeting_admin, "__wrapped__"
    ), "create_meeting_admin not properly decorated"

    print("  ✓ All views have proper decorators")

    print("\n✅ Meeting Admin Action Views tests passed!")


if __name__ == "__main__":
    try:
        test_lead_admin_meeting_actions()
        test_meeting_admin_views()
        print("\n🎉 ALL TESTS PASSED! Implementation is complete and working!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
