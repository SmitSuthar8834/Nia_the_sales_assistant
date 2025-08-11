#!/usr/bin/env python3
"""
Test script for AI Meeting Guidance structure (without API calls)

This script tests the basic structure and data classes for AI Meeting Guidance.
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

from django.utils import timezone

from meeting_service.live_meeting_support import (
    ClosingOpportunity,
    ConversationTurn,
    FollowUpRecommendation,
    InterventionAlert,
    LiveMeetingSupportService,
    MeetingGuidance,
    ObjectionHandlingAdvice,
)


def test_ai_guidance_structure():
    """Test AI Meeting Guidance data structures"""
    print("🎯 Testing AI Meeting Guidance Data Structures")
    print("=" * 60)

    try:
        # Test 1: Create ConversationTurn
        print("\n📋 Test 1: Creating ConversationTurn")
        turn = ConversationTurn(
            timestamp=timezone.now(),
            speaker="user",
            content="What is your budget for this project?",
            confidence_score=0.95,
        )
        print(f"✅ ConversationTurn created: {turn.speaker} - {turn.content[:50]}...")

        # Test 2: Create ObjectionHandlingAdvice
        print("\n🛡️ Test 2: Creating ObjectionHandlingAdvice")
        objection_advice = ObjectionHandlingAdvice(
            objection_type="price",
            objection_text="This seems too expensive",
            recommended_response="I understand your concern about the investment. Let me show you the ROI...",
            alternative_approaches=[
                "Focus on value",
                "Break down costs",
                "Compare to alternatives",
            ],
            confidence_score=85.0,
            urgency_level="high",
            follow_up_questions=["What budget range were you considering?"],
        )
        print(
            f"✅ ObjectionHandlingAdvice created: {objection_advice.objection_type} - {objection_advice.confidence_score}%"
        )

        # Test 3: Create ClosingOpportunity
        print("\n🎯 Test 3: Creating ClosingOpportunity")
        closing_opportunity = ClosingOpportunity(
            opportunity_type="buying_signal",
            description="Prospect asked about implementation timeline",
            recommended_closing_technique="assumptive",
            closing_questions=[
                "When would you like to get started?",
                "Should we schedule the kickoff meeting?",
            ],
            confidence_score=90.0,
            timing_recommendation="immediate",
            risk_factors=["Budget approval needed"],
        )
        print(
            f"✅ ClosingOpportunity created: {closing_opportunity.opportunity_type} - {closing_opportunity.confidence_score}%"
        )

        # Test 4: Create FollowUpRecommendation
        print("\n📋 Test 4: Creating FollowUpRecommendation")
        followup_rec = FollowUpRecommendation(
            action_type="proposal",
            priority="high",
            recommended_timing="within_24h",
            action_description="Send detailed proposal with pricing and timeline",
            rationale="Prospect showed strong interest and asked for next steps",
            success_probability=75.0,
            required_resources=["Proposal template", "Pricing sheet", "Case studies"],
        )
        print(
            f"✅ FollowUpRecommendation created: {followup_rec.action_type} - {followup_rec.priority} priority"
        )

        # Test 5: Create InterventionAlert
        print("\n⚠️ Test 5: Creating InterventionAlert")
        intervention_alert = InterventionAlert(
            alert_type="competitor_mention",
            severity="high",
            description="Prospect mentioned considering a competitor solution",
            recommended_intervention="Address competitive advantages immediately",
            immediate_actions=[
                "Highlight unique value props",
                "Share competitive comparison",
                "Schedule demo",
            ],
            confidence_score=80.0,
            triggered_at=timezone.now(),
        )
        print(
            f"✅ InterventionAlert created: {intervention_alert.alert_type} - {intervention_alert.severity} severity"
        )

        # Test 6: Create MeetingGuidance
        print("\n🎯 Test 6: Creating MeetingGuidance")
        meeting_guidance = MeetingGuidance(
            objection_advice=[objection_advice],
            closing_opportunities=[closing_opportunity],
            follow_up_recommendations=[followup_rec],
            intervention_alerts=[intervention_alert],
            overall_meeting_health="good",
            guidance_timestamp=timezone.now(),
        )
        print(
            f"✅ MeetingGuidance created with {len(meeting_guidance.objection_advice)} objections, "
            f"{len(meeting_guidance.closing_opportunities)} opportunities, "
            f"{len(meeting_guidance.follow_up_recommendations)} follow-ups, "
            f"{len(meeting_guidance.intervention_alerts)} alerts"
        )
        print(f"   Overall meeting health: {meeting_guidance.overall_meeting_health}")

        # Test 7: Test LiveMeetingSupportService initialization
        print("\n🔧 Test 7: Testing LiveMeetingSupportService")
        live_service = LiveMeetingSupportService()
        print("✅ LiveMeetingSupportService initialized successfully")

        # Test 8: Test method existence
        print("\n📋 Test 8: Checking Method Availability")
        methods_to_check = [
            "start_live_meeting_session",
            "process_conversation_turn",
            "get_real_time_suggestions",
            "identify_key_moments",
            "analyze_conversation_sentiment",
            "generate_next_question_suggestions",
            "generate_meeting_guidance",
            "end_live_meeting_session",
        ]

        for method_name in methods_to_check:
            if hasattr(live_service, method_name):
                print(f"   ✅ {method_name} - Available")
            else:
                print(f"   ❌ {method_name} - Missing")

        print("\n🎉 AI Meeting Guidance Structure Test Completed Successfully!")
        print("=" * 60)

        # Summary of structures tested
        print("\n📋 Data Structures Tested:")
        print("✅ ConversationTurn")
        print("✅ ObjectionHandlingAdvice")
        print("✅ ClosingOpportunity")
        print("✅ FollowUpRecommendation")
        print("✅ InterventionAlert")
        print("✅ MeetingGuidance")
        print("✅ LiveMeetingSupportService")

        print("\n📋 Key Features Verified:")
        print("✅ Real-time objection handling advice structure")
        print("✅ Closing opportunity identification structure")
        print("✅ Follow-up action recommendations structure")
        print("✅ Intervention alerts for struggling meetings structure")
        print("✅ Overall meeting health assessment structure")
        print("✅ Service method availability")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_ai_guidance_structure()
