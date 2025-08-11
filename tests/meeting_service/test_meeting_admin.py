#!/usr/bin/env python
"""
Test script for Meeting Admin Interface
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

from meeting_service.models import Meeting


def test_meeting_admin():
    """Test the meeting admin interface functionality"""
    print("🧪 Testing Meeting Admin Interface")
    print("=" * 50)

    # Get test data
    meeting = Meeting.objects.first()
    if not meeting:
        print("❌ No test meeting found. Please run the setup first.")
        return

    print(f"✅ Found test meeting: {meeting.title}")
    print(f"   - Lead: {meeting.lead.company_name}")
    print(f"   - Status: {meeting.get_status_display()}")
    print(f"   - Scheduled: {meeting.scheduled_at}")
    print(f"   - Type: {meeting.get_meeting_type_display()}")

    # Test lead context
    print(f"\n📋 Lead Context:")
    print(f"   - Company: {meeting.lead.company_name}")
    print(f"   - Contact: {meeting.lead.contact_name}")
    print(f"   - Email: {meeting.lead.contact_email}")
    print(f"   - Status: {meeting.lead.get_status_display()}")
    print(f"   - Industry: {meeting.lead.industry or 'Not specified'}")

    # Test AI insights
    print(f"\n🤖 AI Insights:")
    try:
        insights = meeting.lead.ai_insights
        print(f"   - Lead Score: {insights.lead_score}/100")
        print(f"   - Conversion Probability: {insights.conversion_probability}%")
        print(f"   - Quality Tier: {insights.get_quality_tier_display()}")
        print(f"   - Next Best Action: {insights.next_best_action}")
        print(f"   - Recommended Actions: {', '.join(insights.recommended_actions)}")
        print(f"   - Key Messaging: {', '.join(insights.key_messaging)}")
    except Exception as e:
        print(f"   - Error loading AI insights: {e}")

    # Test meeting properties
    print(f"\n⏰ Meeting Properties:")
    print(f"   - Is Upcoming: {meeting.is_upcoming}")
    print(f"   - Is Overdue: {meeting.is_overdue}")
    print(f"   - Duration: {meeting.duration_minutes} minutes")

    # Test meeting actions
    print(f"\n🎬 Available Actions:")
    if meeting.status == Meeting.Status.SCHEDULED:
        print("   - ▶️ Start Meeting")
        print("   - ❌ Cancel Meeting")
    elif meeting.status == Meeting.Status.IN_PROGRESS:
        print("   - ✅ Complete Meeting")
    else:
        print("   - 👁️ View Only")

    print(f"\n✅ Meeting Admin Interface Test Complete!")
    print(f"   Meeting ID: {meeting.id}")
    print(f"   Admin URL: /admin/meeting_service/meeting/{meeting.id}/change/")


if __name__ == "__main__":
    test_meeting_admin()
