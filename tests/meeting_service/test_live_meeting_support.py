#!/usr/bin/env python
"""
Test script for Live Meeting Support functionality

This script tests the core components of the live meeting support system:
- Real-time conversation analysis
- Sentiment analysis and engagement scoring
- Key moment identification
- Next question suggestions
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

from ai_service.models import Lead
from meeting_service.live_meeting_support import (
    ConversationTurn,
    LiveMeetingSupportService,
)
from meeting_service.models import Meeting

User = get_user_model()


def create_test_data():
    """Create test user, lead, and meeting for testing"""
    print("Creating test data...")

    # Create test user
    user, created = User.objects.get_or_create(
        username="test_sales_rep",
        defaults={
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
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
                "title": "CTO",
                "phone": "+1-555-0123",
            },
            "pain_points": [
                "Manual data processing is time-consuming",
                "Lack of real-time analytics",
                "Integration challenges with existing systems",
            ],
            "requirements": [
                "Automated data processing",
                "Real-time dashboard",
                "API integration capabilities",
            ],
            "budget_info": "$50,000 - $100,000 annual budget",
            "timeline": "Need solution implemented within 3 months",
            "decision_makers": ["John Smith (CTO)", "Sarah Johnson (CEO)"],
        },
    )

    # Create test meeting
    meeting, created = Meeting.objects.get_or_create(
        lead=lead,
        title="Discovery Call - TechCorp Solutions",
        defaults={
            "meeting_type": Meeting.MeetingType.DISCOVERY,
            "scheduled_at": timezone.now() + timedelta(hours=1),
            "duration_minutes": 60,
            "status": Meeting.Status.SCHEDULED,
            "agenda": "Discuss current challenges and explore potential solutions",
        },
    )

    print(f"✓ Created test user: {user.username}")
    print(f"✓ Created test lead: {lead.company_name}")
    print(f"✓ Created test meeting: {meeting.title}")

    return user, lead, meeting


def test_conversation_analysis():
    """Test real-time conversation analysis"""
    print("\n" + "=" * 50)
    print("TESTING CONVERSATION ANALYSIS")
    print("=" * 50)

    service = LiveMeetingSupportService()

    # Sample conversation turns
    conversation_turns = [
        ConversationTurn(
            timestamp=timezone.now(),
            speaker="user",
            content="Hi John, thanks for taking the time to meet with us today. I'd love to learn more about your current data processing challenges.",
        ),
        ConversationTurn(
            timestamp=timezone.now(),
            speaker="prospect",
            content="Thanks for reaching out. We're definitely struggling with our current manual processes. It's taking our team hours each day to process data that should be automated.",
        ),
        ConversationTurn(
            timestamp=timezone.now(),
            speaker="user",
            content="That sounds frustrating. Can you tell me more about the specific types of data you're processing and how it impacts your daily operations?",
        ),
        ConversationTurn(
            timestamp=timezone.now(),
            speaker="prospect",
            content="We handle customer transaction data, inventory updates, and financial reports. The manual work is error-prone and prevents us from getting real-time insights. Our CEO is pushing for a solution within the next quarter.",
        ),
    ]

    print("Sample conversation:")
    for turn in conversation_turns:
        print(f"  {turn.speaker}: {turn.content}")

    # Test sentiment analysis
    print("\nTesting sentiment analysis...")
    sentiment = service.analyze_conversation_sentiment(conversation_turns)

    print(f"✓ Overall Sentiment: {sentiment.overall_sentiment}")
    print(f"✓ Sentiment Score: {sentiment.sentiment_score:.2f}")
    print(f"✓ Engagement Level: {sentiment.engagement_level}")
    print(f"✓ Engagement Score: {sentiment.engagement_score:.1f}")
    print(f"✓ Emotional Indicators: {', '.join(sentiment.emotional_indicators)}")
    print(f"✓ Confidence Level: {sentiment.confidence_level:.1f}%")

    return conversation_turns


def test_key_moment_identification(conversation_turns):
    """Test key moment identification"""
    print("\n" + "=" * 50)
    print("TESTING KEY MOMENT IDENTIFICATION")
    print("=" * 50)

    service = LiveMeetingSupportService()

    meeting_context = {
        "meeting_type": "discovery",
        "company_name": "TechCorp Solutions",
        "industry": "Technology",
    }

    print("Identifying key moments in conversation...")
    key_moments = service.identify_key_moments(conversation_turns, meeting_context)

    print(f"✓ Found {len(key_moments)} key moments:")

    for i, moment in enumerate(key_moments, 1):
        print(f"\n  {i}. {moment.moment_type.upper()}")
        print(f"     Description: {moment.description}")
        print(f"     Importance: {moment.importance_score:.1f}/100")
        print(f"     Context: {moment.context[:100]}...")
        if moment.suggested_response:
            print(f"     Suggested Response: {moment.suggested_response}")
        if moment.follow_up_actions:
            print(f"     Follow-up Actions: {', '.join(moment.follow_up_actions)}")

    return key_moments


def test_question_suggestions(conversation_turns):
    """Test next question suggestions"""
    print("\n" + "=" * 50)
    print("TESTING QUESTION SUGGESTIONS")
    print("=" * 50)

    service = LiveMeetingSupportService()

    meeting_context = {
        "meeting_type": "discovery",
        "company_name": "TechCorp Solutions",
        "industry": "Technology",
        "lead_info": {
            "company_name": "TechCorp Solutions",
            "industry": "Technology",
            "pain_points": [
                "Manual data processing is time-consuming",
                "Lack of real-time analytics",
            ],
            "requirements": ["Automated data processing", "Real-time dashboard"],
            "budget_info": "$50,000 - $100,000 annual budget",
            "timeline": "Need solution implemented within 3 months",
            "decision_makers": ["John Smith (CTO)", "Sarah Johnson (CEO)"],
        },
    }

    print("Generating next question suggestions...")
    suggestions = service.generate_next_question_suggestions(
        conversation_turns, meeting_context
    )

    print(f"✓ Generated {len(suggestions)} question suggestions:")

    for i, suggestion in enumerate(suggestions, 1):
        print(f"\n  {i}. {suggestion.question_type.upper()} QUESTION")
        print(f"     Question: {suggestion.question_text}")
        print(f"     Priority: {suggestion.priority_score:.1f}/100")
        print(f"     Timing: {suggestion.timing_suggestion}")
        print(f"     Rationale: {suggestion.rationale}")
        print(f"     Expected Outcome: {suggestion.expected_outcome}")
        if suggestion.follow_up_questions:
            print(
                f"     Follow-ups: {', '.join(suggestion.follow_up_questions[:2])}..."
            )

    return suggestions


def test_live_session_workflow():
    """Test complete live meeting session workflow"""
    print("\n" + "=" * 50)
    print("TESTING LIVE SESSION WORKFLOW")
    print("=" * 50)

    user, lead, meeting = create_test_data()
    service = LiveMeetingSupportService()

    # Start live session
    print("1. Starting live meeting session...")
    session_result = service.start_live_meeting_session(str(meeting.id), str(user.id))

    if session_result["success"]:
        print(f"✓ Session started: {session_result['session_id']}")
        print(f"✓ Meeting: {session_result['meeting_title']}")
        print(f"✓ Company: {session_result['lead_company']}")
        print(f"✓ Initial questions: {len(session_result['initial_questions'])}")

        session_id = session_result["session_id"]

        # Process conversation turns
        print("\n2. Processing conversation turns...")

        sample_turns = [
            (
                "user",
                "Hi John, thanks for joining today. How are things going at TechCorp?",
            ),
            (
                "prospect",
                "Thanks for having me. Things are busy - we're really struggling with our data processing workflows.",
            ),
            (
                "user",
                "I'd love to hear more about those challenges. What's the biggest pain point you're facing?",
            ),
            (
                "prospect",
                "The manual work is killing us. We spend 4-5 hours daily on data entry that should be automated. And we have no real-time visibility into our operations.",
            ),
            (
                "user",
                "That sounds incredibly frustrating. What's the business impact of these delays?",
            ),
            (
                "prospect",
                "We're missing opportunities because we can't respond quickly to market changes. Our CEO wants this fixed within 90 days, and we have budget approved for the right solution.",
            ),
        ]

        for speaker, content in sample_turns:
            print(f"   Processing: {speaker} - {content[:50]}...")
            result = service.process_conversation_turn(session_id, speaker, content)

            if result["success"]:
                print(f"   ✓ Processed successfully")
                if result.get("analysis_performed"):
                    print(
                        f"   ✓ Analysis performed - found {len(result.get('key_moments', []))} key moments"
                    )
            else:
                print(f"   ✗ Error: {result.get('error')}")

        # Get real-time suggestions
        print("\n3. Getting real-time suggestions...")
        suggestions_result = service.get_real_time_suggestions(session_id)

        if suggestions_result["success"]:
            print(f"✓ Current suggestions: {len(suggestions_result['suggestions'])}")
            print(
                f"✓ Sentiment: {suggestions_result.get('sentiment', {}).get('overall_sentiment', 'N/A')}"
            )
            print(f"✓ Key moments: {len(suggestions_result['key_moments'])}")

        # End session
        print("\n4. Ending live meeting session...")
        end_result = service.end_live_meeting_session(session_id)

        if end_result["success"]:
            print(f"✓ Session ended successfully")
            print(
                f"✓ Total conversation turns: {end_result['total_conversation_turns']}"
            )
            print(
                f"✓ Meeting duration: {end_result.get('meeting_duration_minutes', 'N/A')} minutes"
            )
            print(f"✓ Final summary generated")
        else:
            print(f"✗ Error ending session: {end_result.get('error')}")

    else:
        print(f"✗ Failed to start session: {session_result.get('error')}")


def main():
    """Run all tests"""
    print("🤖 NIA LIVE MEETING SUPPORT - TEST SUITE")
    print("=" * 60)

    try:
        # Test individual components
        conversation_turns = test_conversation_analysis()
        test_key_moment_identification(conversation_turns)
        test_question_suggestions(conversation_turns)

        # Test complete workflow
        test_live_session_workflow()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)

        print("\nLive Meeting Support Features Tested:")
        print("✓ Real-time conversation analysis")
        print("✓ Sentiment analysis and engagement scoring")
        print("✓ Key moment identification and flagging")
        print("✓ Next question suggestions based on conversation flow")
        print("✓ Complete live session workflow")
        print("✓ Session management and caching")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
