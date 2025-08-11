#!/usr/bin/env python3
"""
Test script for AI Meeting Guidance functionality

This script tests the new AI Meeting Guidance features:
- Real-time objection handling advice
- Closing opportunity identification
- Follow-up action recommendations
- Intervention alerts for struggling meetings
"""

import os
import sys
from pathlib import Path

import django

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))
from datetime import timedelta

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nia_sales_assistant.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone

from ai_service.models import Lead
from meeting_service.live_meeting_support import LiveMeetingSupportService
from meeting_service.models import Meeting

User = get_user_model()


def test_ai_meeting_guidance():
    """Test AI Meeting Guidance functionality"""
    print("🎯 Testing AI Meeting Guidance Functionality")
    print("=" * 60)

    try:
        # Get or create test user
        user, created = User.objects.get_or_create(
            username="test_sales_rep",
            defaults={
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "Sales Rep",
            },
        )
        print(f"✅ Using test user: {user.username}")

        # Get or create test lead
        lead, created = Lead.objects.get_or_create(
            company_name="Test Company Inc",
            defaults={
                "user": user,
                "contact_info": {
                    "name": "John Doe",
                    "email": "john@testcompany.com",
                    "phone": "+1-555-0123",
                    "title": "CTO",
                    "department": "Technology",
                },
                "industry": "Technology",
                "company_size": "50-100",
                "pain_points": ["High operational costs", "Manual processes"],
                "requirements": ["Automation solution", "Cost reduction"],
                "budget_info": "$50,000 - $100,000",
                "timeline": "Q2 2024",
                "decision_makers": ["John Doe (CTO)", "Jane Smith (CFO)"],
            },
        )
        print(f"✅ Using test lead: {lead.company_name}")

        # Create test meeting
        meeting, created = Meeting.objects.get_or_create(
            title="AI Guidance Test Meeting",
            lead=lead,
            defaults={
                "meeting_type": "discovery",
                "scheduled_at": timezone.now() + timedelta(hours=1),
                "agenda": "Test AI meeting guidance features",
                "status": "scheduled",
            },
        )
        print(f"✅ Using test meeting: {meeting.title}")

        # Initialize live meeting service
        live_service = LiveMeetingSupportService()
        print("✅ Initialized LiveMeetingSupportService")

        # Test 1: Start live meeting session
        print("\n📋 Test 1: Starting Live Meeting Session")
        session_result = live_service.start_live_meeting_session(
            str(meeting.id), str(user.id)
        )

        if session_result["success"]:
            print("✅ Live meeting session started successfully")
            session_id = session_result["session_id"]
            print(f"   Session ID: {session_id}")
        else:
            print(f"❌ Failed to start session: {session_result.get('error')}")
            return

        # Test 2: Process conversation with objections
        print("\n🛡️ Test 2: Testing Objection Handling")

        # Simulate conversation with price objection
        objection_turns = [
            (
                "user",
                "So our solution can help reduce your operational costs by up to 40%. The investment for our premium package is $75,000.",
            ),
            (
                "prospect",
                "That seems quite expensive. We're looking at other solutions that cost much less. I'm not sure we can justify that price to our board.",
            ),
            (
                "user",
                "I understand your concern about the investment. Can you tell me more about what budget range you had in mind?",
            ),
            (
                "prospect",
                "We were hoping to stay under $50,000. The other vendors we're looking at are offering similar solutions for around $30,000.",
            ),
        ]

        for speaker, content in objection_turns:
            result = live_service.process_conversation_turn(
                session_id, speaker, content
            )
            if result["success"]:
                print(f"   ✅ Processed {speaker} turn")
            else:
                print(f"   ❌ Failed to process {speaker} turn: {result.get('error')}")

        # Get meeting guidance for objection handling
        from django.core.cache import cache

        session_data = cache.get(session_id)
        if session_data:
            recent_turns = [
                live_service.ConversationTurn(**turn_data)
                for turn_data in session_data["conversation_turns"][-4:]
            ]

            meeting_context = {
                "meeting_type": meeting.meeting_type,
                "lead_info": live_service._get_lead_context(meeting.lead),
            }

            guidance = live_service.generate_meeting_guidance(
                recent_turns, meeting_context
            )

            print(
                f"   📊 Generated {len(guidance.objection_advice)} objection handling advice(s)"
            )
            for i, advice in enumerate(guidance.objection_advice, 1):
                print(
                    f"      {i}. {advice.objection_type.upper()}: {advice.recommended_response[:100]}..."
                )

        # Test 3: Process conversation with buying signals
        print("\n🎯 Test 3: Testing Closing Opportunity Identification")

        closing_turns = [
            (
                "prospect",
                "This solution does sound interesting. If we could make the numbers work, when could we potentially get started?",
            ),
            (
                "user",
                "We could have you up and running within 4-6 weeks of contract signing. What timeline were you hoping for?",
            ),
            (
                "prospect",
                "That timeline works well for us. We need to have something in place before Q3. I'll need to discuss this with our CFO, but I think we can move forward.",
            ),
            (
                "user",
                "That's great to hear! Would it be helpful if I prepared a customized proposal for your review?",
            ),
        ]

        for speaker, content in closing_turns:
            result = live_service.process_conversation_turn(
                session_id, speaker, content
            )
            if result["success"]:
                print(f"   ✅ Processed {speaker} turn")

        # Get updated guidance for closing opportunities
        session_data = cache.get(session_id)
        if session_data:
            recent_turns = [
                live_service.ConversationTurn(**turn_data)
                for turn_data in session_data["conversation_turns"][-4:]
            ]

            guidance = live_service.generate_meeting_guidance(
                recent_turns, meeting_context
            )

            print(
                f"   📊 Generated {len(guidance.closing_opportunities)} closing opportunity(ies)"
            )
            for i, opp in enumerate(guidance.closing_opportunities, 1):
                print(
                    f"      {i}. {opp.opportunity_type.upper()}: {opp.description[:100]}..."
                )
                print(f"         Technique: {opp.recommended_closing_technique}")

        # Test 4: Test follow-up recommendations
        print("\n📋 Test 4: Testing Follow-up Recommendations")

        followup_turns = [
            (
                "prospect",
                "I think we're ready to move to the next step. What do you need from us?",
            ),
            (
                "user",
                "I'll prepare a detailed proposal with the pricing we discussed. I'll also include some case studies from similar companies.",
            ),
            ("prospect", "Perfect. When can we expect to receive that?"),
            (
                "user",
                "I can have that to you by end of week. Should I send it directly to you and copy the CFO?",
            ),
        ]

        for speaker, content in followup_turns:
            result = live_service.process_conversation_turn(
                session_id, speaker, content
            )
            if result["success"]:
                print(f"   ✅ Processed {speaker} turn")

        # Get follow-up recommendations
        session_data = cache.get(session_id)
        if session_data:
            all_turns = [
                live_service.ConversationTurn(**turn_data)
                for turn_data in session_data["conversation_turns"]
            ]

            guidance = live_service.generate_meeting_guidance(
                all_turns, meeting_context
            )

            print(
                f"   📊 Generated {len(guidance.follow_up_recommendations)} follow-up recommendation(s)"
            )
            for i, rec in enumerate(guidance.follow_up_recommendations, 1):
                print(f"      {i}. {rec.action_type.upper()} ({rec.priority} priority)")
                print(f"         {rec.action_description[:100]}...")
                print(f"         Timing: {rec.recommended_timing}")

        # Test 5: Test intervention alerts
        print("\n⚠️ Test 5: Testing Intervention Alerts")

        intervention_turns = [
            (
                "prospect",
                "Actually, I just remembered we're also talking to your main competitor, SalesForce. They're offering a much better deal.",
            ),
            ("user", "I see. Can you tell me more about what they're offering?"),
            (
                "prospect",
                "They're offering a similar solution for about half the price, and they say they can implement it faster.",
            ),
            (
                "prospect",
                "I'm starting to think we should go with them instead. This is getting too complicated and expensive.",
            ),
        ]

        for speaker, content in intervention_turns:
            result = live_service.process_conversation_turn(
                session_id, speaker, content
            )
            if result["success"]:
                print(f"   ✅ Processed {speaker} turn")

        # Get intervention alerts
        session_data = cache.get(session_id)
        if session_data:
            recent_turns = [
                live_service.ConversationTurn(**turn_data)
                for turn_data in session_data["conversation_turns"][-4:]
            ]

            guidance = live_service.generate_meeting_guidance(
                recent_turns, meeting_context
            )

            print(
                f"   📊 Generated {len(guidance.intervention_alerts)} intervention alert(s)"
            )
            for i, alert in enumerate(guidance.intervention_alerts, 1):
                print(
                    f"      {i}. {alert.alert_type.upper()} ({alert.severity} severity)"
                )
                print(f"         {alert.description[:100]}...")
                print(
                    f"         Intervention: {alert.recommended_intervention[:100]}..."
                )

            print(
                f"   📊 Overall Meeting Health: {guidance.overall_meeting_health.upper()}"
            )

        # Test 6: End session and generate summary
        print("\n📝 Test 6: Ending Session and Generating Summary")

        end_result = live_service.end_live_meeting_session(session_id)
        if end_result["success"]:
            print("✅ Live meeting session ended successfully")
            print(
                f"   Total conversation turns: {end_result['total_conversation_turns']}"
            )
            print(
                f"   Meeting duration: {end_result.get('meeting_duration_minutes', 'N/A')} minutes"
            )
        else:
            print(f"❌ Failed to end session: {end_result.get('error')}")

        print("\n🎉 AI Meeting Guidance Test Completed Successfully!")
        print("=" * 60)

        # Summary of features tested
        print("\n📋 Features Tested:")
        print("✅ Real-time objection handling advice")
        print("✅ Closing opportunity identification")
        print("✅ Follow-up action recommendations")
        print("✅ Intervention alerts for struggling meetings")
        print("✅ Overall meeting health assessment")
        print("✅ Live session management")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_ai_meeting_guidance()
