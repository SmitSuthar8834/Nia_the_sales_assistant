#!/usr/bin/env python3
"""
Test script for Meeting Outcome Tracking functionality

This script tests the complete meeting outcome tracking system including:
- Post-meeting summary generation
- Action items extraction and assignment
- Next steps and follow-up scheduling
- Lead scoring updates based on meeting outcomes
"""

import os
import sys
from pathlib import Path

import django

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from datetime import timedelta

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nia_sales_assistant.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone

from ai_service.models import AIInsights, Lead
from meeting_service.meeting_outcome_service import MeetingOutcomeService
from meeting_service.models import Meeting, MeetingQuestion

User = get_user_model()


def create_test_data():
    """Create test data for meeting outcome tracking"""
    print("Creating test data...")

    # Create or get test user
    user, created = User.objects.get_or_create(
        username="test_sales_rep",
        defaults={
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "Sales Rep",
        },
    )

    # Create test lead
    lead, created = Lead.objects.get_or_create(
        user=user,
        company_name="TechCorp Solutions",
        defaults={
            "industry": "Technology",
            "company_size": "100-500 employees",
            "contact_info": {
                "name": "John Smith",
                "email": "john.smith@techcorp.com",
                "phone": "+1-555-0123",
                "title": "CTO",
            },
            "status": Lead.Status.QUALIFIED,
            "pain_points": [
                "Manual data processing is time-consuming",
                "Lack of real-time analytics",
                "Integration challenges with existing systems",
            ],
            "requirements": [
                "Automated data processing solution",
                "Real-time dashboard and reporting",
                "API integration capabilities",
            ],
            "budget_info": "$50,000 - $100,000 annual budget",
            "timeline": "Implementation needed within 3 months",
            "decision_makers": ["John Smith (CTO)", "Sarah Johnson (CEO)"],
            "urgency_level": Lead.UrgencyLevel.HIGH,
        },
    )

    # Create AI insights for the lead
    ai_insights, created = AIInsights.objects.get_or_create(
        lead=lead,
        defaults={
            "lead_score": 75.0,
            "conversion_probability": 65.0,
            "quality_tier": AIInsights.QualityTier.HIGH,
            "opportunity_conversion_score": 70.0,
            "recommended_for_conversion": True,
            "primary_strategy": "Solution-focused approach",
            "confidence_score": 85.0,
            "data_completeness": 80.0,
            "recommended_actions": [
                "Schedule product demonstration",
                "Prepare detailed proposal",
                "Identify technical requirements",
            ],
            "next_steps": [
                "Follow up within 24 hours",
                "Send meeting summary",
                "Schedule technical demo",
            ],
            "risk_factors": [
                "Competitive pressure from existing vendor",
                "Budget approval process may be lengthy",
            ],
            "opportunities": [
                "High urgency level indicates quick decision",
                "Technical decision maker directly involved",
            ],
        },
    )

    # Create completed meeting
    meeting, created = Meeting.objects.get_or_create(
        lead=lead,
        title="Discovery Call - TechCorp Solutions",
        defaults={
            "description": "Initial discovery call to understand requirements and pain points",
            "meeting_type": Meeting.MeetingType.DISCOVERY,
            "scheduled_at": timezone.now() - timedelta(hours=2),
            "duration_minutes": 60,
            "status": Meeting.Status.COMPLETED,
            "started_at": timezone.now() - timedelta(hours=2),
            "ended_at": timezone.now() - timedelta(hours=1),
            "agenda": """
            1. Company introduction and background
            2. Current challenges and pain points
            3. Technical requirements discussion
            4. Budget and timeline exploration
            5. Decision-making process
            6. Next steps and follow-up
            """,
            "participants": [
                "John Smith - CTO",
                "Sarah Johnson - CEO",
                "Mike Davis - IT Director",
            ],
            "ai_insights": {
                "meeting_preparation": {
                    "generated_at": timezone.now().isoformat(),
                    "preparation_materials": "Comprehensive preparation completed",
                }
            },
        },
    )

    # Create meeting questions with responses
    questions_data = [
        {
            "question_text": "What are the main challenges you're facing with your current data processing workflow?",
            "question_type": "pain_points",
            "priority": 9,
            "response": "We spend about 20 hours per week manually processing data from different sources. It's error-prone and prevents our team from focusing on analysis and insights.",
        },
        {
            "question_text": "What's your timeline for implementing a new solution?",
            "question_type": "timeline",
            "priority": 8,
            "response": "We need to have something in place within the next 3 months. Our current system is becoming a major bottleneck.",
        },
        {
            "question_text": "Who else would be involved in the decision-making process?",
            "question_type": "decision_makers",
            "priority": 8,
            "response": "Sarah, our CEO, has final approval. Mike, our IT Director, will handle the technical evaluation. We also need buy-in from the finance team for budget approval.",
        },
        {
            "question_text": "What's your budget range for this type of solution?",
            "question_type": "budget",
            "priority": 7,
            "response": "We've allocated between $50,000 and $100,000 annually for this. We're looking for the best value, not necessarily the cheapest option.",
        },
        {
            "question_text": "Have you evaluated any other solutions or vendors?",
            "question_type": "competition",
            "priority": 6,
            "response": "We looked at DataFlow Pro and Analytics Suite. DataFlow Pro was too complex, and Analytics Suite lacked the integration capabilities we need.",
        },
    ]

    for q_data in questions_data:
        question, created = MeetingQuestion.objects.get_or_create(
            meeting=meeting,
            question_text=q_data["question_text"],
            defaults={
                "question_type": q_data["question_type"],
                "priority": q_data["priority"],
                "priority_level": (
                    MeetingQuestion.Priority.HIGH
                    if q_data["priority"] >= 8
                    else MeetingQuestion.Priority.MEDIUM
                ),
                "ai_generated": True,
                "confidence_score": 85.0,
                "asked_at": timezone.now() - timedelta(minutes=30),
                "response": q_data["response"],
            },
        )

    print(f"✅ Test data created successfully!")
    print(f"   - User: {user.username}")
    print(f"   - Lead: {lead.company_name}")
    print(f"   - Meeting: {meeting.title}")
    print(f"   - Questions: {MeetingQuestion.objects.filter(meeting=meeting).count()}")

    return user, lead, meeting


def test_meeting_summary_generation(meeting):
    """Test meeting summary generation"""
    print("\n🔍 Testing Meeting Summary Generation...")

    outcome_service = MeetingOutcomeService()
    result = outcome_service.generate_meeting_summary(meeting, regenerate=True)

    if result.get("success"):
        print("✅ Meeting summary generated successfully!")
        summary_data = result.get("summary", {})

        print(f"   - Summary: {summary_data.get('summary', 'N/A')[:100]}...")
        print(f"   - Key Takeaways: {len(summary_data.get('key_takeaways', []))} items")
        print(
            f"   - Discussion Highlights: {len(summary_data.get('discussion_highlights', []))} items"
        )
        print(
            f"   - Meeting Effectiveness: {summary_data.get('meeting_effectiveness', 'N/A')}"
        )

        # Verify meeting was updated
        meeting.refresh_from_db()
        if meeting.outcome:
            print("✅ Meeting outcome field updated successfully")
        else:
            print("❌ Meeting outcome field not updated")

    else:
        print(f"❌ Meeting summary generation failed: {result.get('error')}")

    return result


def test_action_items_extraction(meeting):
    """Test action items extraction"""
    print("\n📋 Testing Action Items Extraction...")

    outcome_service = MeetingOutcomeService()
    result = outcome_service.extract_action_items(meeting, regenerate=True)

    if result.get("success"):
        print("✅ Action items extracted successfully!")
        action_items_data = result.get("action_items", {})

        action_items = action_items_data.get("action_items", [])
        print(f"   - Action Items: {len(action_items)} items")

        for i, item in enumerate(action_items[:3], 1):  # Show first 3 items
            print(f"     {i}. {item.get('description', 'N/A')[:60]}...")
            print(f"        Assigned to: {item.get('assigned_to', 'N/A')}")
            print(f"        Priority: {item.get('priority', 'N/A')}")

        immediate_actions = action_items_data.get("immediate_actions", [])
        print(f"   - Immediate Actions: {len(immediate_actions)} items")

        follow_up_meetings = action_items_data.get("follow_up_meetings", [])
        print(f"   - Follow-up Meetings: {len(follow_up_meetings)} suggested")

        # Verify meeting was updated
        meeting.refresh_from_db()
        if meeting.action_items:
            print("✅ Meeting action_items field updated successfully")
        else:
            print("❌ Meeting action_items field not updated")

    else:
        print(f"❌ Action items extraction failed: {result.get('error')}")

    return result


def test_follow_up_scheduling(meeting):
    """Test follow-up scheduling"""
    print("\n📅 Testing Follow-up Scheduling...")

    outcome_service = MeetingOutcomeService()
    result = outcome_service.schedule_follow_up_actions(meeting)

    if result.get("success"):
        print("✅ Follow-up actions scheduled successfully!")
        follow_up_plan = result.get("follow_up_plan", {})

        immediate_follow_up = follow_up_plan.get("immediate_follow_up", {})
        print(
            f"   - Immediate Follow-up: {immediate_follow_up.get('timeframe', 'N/A')}"
        )
        print(f"     Actions: {len(immediate_follow_up.get('actions', []))} items")

        short_term_follow_up = follow_up_plan.get("short_term_follow_up", {})
        recommended_meetings = short_term_follow_up.get("recommended_meetings", [])
        print(
            f"   - Short-term Follow-up: {len(recommended_meetings)} meetings recommended"
        )

        for i, meeting_rec in enumerate(recommended_meetings[:2], 1):  # Show first 2
            print(
                f"     {i}. {meeting_rec.get('type', 'N/A')} - {meeting_rec.get('purpose', 'N/A')[:50]}..."
            )

        long_term_strategy = follow_up_plan.get("long_term_strategy", {})
        print(
            f"   - Long-term Strategy: {long_term_strategy.get('sales_cycle_stage', 'N/A')}"
        )
        print(f"     Next Milestone: {long_term_strategy.get('next_milestone', 'N/A')}")

        follow_up_meetings = result.get("follow_up_meetings", [])
        print(f"   - Follow-up Meetings Created: {len(follow_up_meetings)} meetings")

        # Verify meeting AI insights were updated
        meeting.refresh_from_db()
        if "follow_up_plan" in meeting.ai_insights:
            print("✅ Meeting AI insights updated with follow-up plan")
        else:
            print("❌ Meeting AI insights not updated with follow-up plan")

    else:
        print(f"❌ Follow-up scheduling failed: {result.get('error')}")

    return result


def test_lead_scoring_update(meeting):
    """Test lead scoring updates"""
    print("\n📊 Testing Lead Scoring Update...")

    # Get initial scores
    if hasattr(meeting.lead, "ai_insights"):
        initial_lead_score = meeting.lead.ai_insights.lead_score
        initial_conversion_prob = meeting.lead.ai_insights.conversion_probability
        print(
            f"   Initial Scores - Lead: {initial_lead_score}, Conversion: {initial_conversion_prob}%"
        )
    else:
        print("   No initial AI insights found")
        initial_lead_score = 0
        initial_conversion_prob = 0

    outcome_service = MeetingOutcomeService()
    result = outcome_service.update_lead_scoring(meeting)

    if result.get("success"):
        print("✅ Lead scoring updated successfully!")
        updated_scores = result.get("updated_scores", {})

        new_lead_score = updated_scores.get("lead_score", 0)
        new_conversion_prob = updated_scores.get("conversion_probability", 0)
        quality_tier = updated_scores.get("quality_tier", "N/A")

        print(
            f"   Updated Scores - Lead: {new_lead_score}, Conversion: {new_conversion_prob}%"
        )
        print(f"   Quality Tier: {quality_tier}")

        score_changes = result.get("score_changes", {})
        print("   Score Changes:")
        for component, change in score_changes.items():
            if change != 0:
                print(f"     - {component}: {change:+.1f}")

        meeting_impact = result.get("meeting_impact", {})
        print(f"   Meeting Impact:")
        print(
            f"     - Questions Asked: {meeting_impact.get('questions_asked_count', 0)}"
        )
        print(
            f"     - Questions Answered: {meeting_impact.get('questions_answered_count', 0)}"
        )
        print(
            f"     - Engagement Indicators: {len(meeting_impact.get('engagement_indicators', []))}"
        )
        print(
            f"     - Progression Signals: {len(meeting_impact.get('progression_signals', []))}"
        )

        # Verify AI insights were updated
        meeting.lead.refresh_from_db()
        if hasattr(meeting.lead, "ai_insights"):
            print("✅ Lead AI insights updated successfully")
        else:
            print("❌ Lead AI insights not found after update")

    else:
        print(f"❌ Lead scoring update failed: {result.get('error')}")

    return result


def test_complete_outcome_processing(meeting):
    """Test complete outcome processing"""
    print("\n🚀 Testing Complete Outcome Processing...")

    outcome_service = MeetingOutcomeService()
    result = outcome_service.process_complete_meeting_outcome(meeting, regenerate=True)

    if result.get("overall_success"):
        print("✅ Complete outcome processing successful!")

        components = result.get("components", {})
        print(f"   Components Processed: {len(components)}")

        for component_name, component_result in components.items():
            status = "✅" if component_result.get("success") else "❌"
            print(
                f"     {status} {component_name}: {component_result.get('message', 'N/A')}"
            )

        processing_time = result.get("processing_completed_at", "") - result.get(
            "processing_started_at", ""
        )
        print(
            f"   Processing Time: Started at {result.get('processing_started_at', 'N/A')}"
        )
        print(
            f"                   Completed at {result.get('processing_completed_at', 'N/A')}"
        )

    else:
        print(
            f"❌ Complete outcome processing failed: {result.get('message', 'Unknown error')}"
        )

        # Show component-specific errors
        components = result.get("components", {})
        for component_name, component_result in components.items():
            if not component_result.get("success"):
                print(
                    f"   ❌ {component_name}: {component_result.get('error', 'Unknown error')}"
                )

    return result


def test_outcome_status_check(meeting):
    """Test outcome status checking"""
    print("\n🔍 Testing Outcome Status Check...")

    # Refresh meeting data
    meeting.refresh_from_db()

    # Check what components have been processed
    components_status = {
        "summary": bool(meeting.outcome),
        "action_items": bool(meeting.action_items),
        "follow_up_plan": "follow_up_plan" in meeting.ai_insights,
        "lead_scoring": "lead_scoring_update" in meeting.ai_insights,
    }

    print("   Component Status:")
    for component, completed in components_status.items():
        status = "✅" if completed else "❌"
        print(f"     {status} {component}: {'Completed' if completed else 'Pending'}")

    completed_count = sum(components_status.values())
    total_count = len(components_status)
    completion_percentage = (completed_count / total_count) * 100

    print(
        f"   Overall Completion: {completed_count}/{total_count} ({completion_percentage:.1f}%)"
    )

    if completion_percentage == 100:
        print("✅ All outcome components have been processed!")
    else:
        pending_components = [
            name for name, completed in components_status.items() if not completed
        ]
        print(f"⏳ Pending components: {', '.join(pending_components)}")

    return components_status


def main():
    """Main test function"""
    print("🧪 Meeting Outcome Tracking Test Suite")
    print("=" * 50)

    try:
        # Create test data
        user, lead, meeting = create_test_data()

        # Test individual components
        summary_result = test_meeting_summary_generation(meeting)
        action_items_result = test_action_items_extraction(meeting)
        follow_up_result = test_follow_up_scheduling(meeting)
        scoring_result = test_lead_scoring_update(meeting)

        # Test complete processing
        complete_result = test_complete_outcome_processing(meeting)

        # Check final status
        final_status = test_outcome_status_check(meeting)

        # Summary
        print("\n📊 Test Summary")
        print("=" * 30)

        test_results = {
            "Meeting Summary": summary_result.get("success", False),
            "Action Items": action_items_result.get("success", False),
            "Follow-up Scheduling": follow_up_result.get("success", False),
            "Lead Scoring": scoring_result.get("success", False),
            "Complete Processing": complete_result.get("overall_success", False),
        }

        for test_name, success in test_results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {status} {test_name}")

        passed_tests = sum(test_results.values())
        total_tests = len(test_results)

        print(f"\n🎯 Overall Results: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            print("🎉 All tests passed! Meeting Outcome Tracking is working correctly.")
        else:
            print("⚠️  Some tests failed. Please check the error messages above.")

        # Show final meeting state
        print(f"\n📋 Final Meeting State:")
        print(f"   - Meeting ID: {meeting.id}")
        print(f"   - Status: {meeting.status}")
        print(f"   - Has Summary: {'Yes' if meeting.outcome else 'No'}")
        print(f"   - Has Action Items: {'Yes' if meeting.action_items else 'No'}")
        print(f"   - AI Insights Keys: {list(meeting.ai_insights.keys())}")

        if hasattr(meeting.lead, "ai_insights"):
            ai_insights = meeting.lead.ai_insights
            print(f"   - Lead Score: {ai_insights.lead_score}")
            print(f"   - Conversion Probability: {ai_insights.conversion_probability}%")
            print(f"   - Quality Tier: {ai_insights.quality_tier}")

    except Exception as e:
        print(f"❌ Test suite failed with error: {str(e)}")
        import traceback

        traceback.print_exc()
        return False

    return passed_tests == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
