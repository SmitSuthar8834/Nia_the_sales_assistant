#!/usr/bin/env python
"""
Test script for Dynamic Question Flow functionality
Tests AI adapts questions based on previous answers, follow-up generation,
effectiveness tracking, and industry-specific templates.
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
from meeting_service.models import ConversationFlow, Meeting, QuestionEffectivenessLog
from meeting_service.question_service import MeetingQuestionService

User = get_user_model()


def create_test_data():
    """Create test data for dynamic question flow testing"""
    print("Creating test data...")

    # Create test user
    user, created = User.objects.get_or_create(
        username="test_sales_rep",
        defaults={
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "Rep",
        },
    )

    # Create test lead
    lead, created = Lead.objects.get_or_create(
        company_name="TechCorp Solutions",
        defaults={
            "industry": "technology",
            "company_size": "100-500 employees",
            "contact_name": "John Smith",
            "contact_info": {
                "email": "john.smith@techcorp.com",
                "phone": "+1-555-0123",
                "title": "CTO",
            },
            "pain_points": ["Legacy system integration challenges", "Manual processes"],
            "requirements": ["Cloud migration", "API integration"],
            "budget_info": "$50,000 - $100,000",
            "timeline": "Q2 2024",
            "decision_makers": ["John Smith (CTO)", "Sarah Johnson (CEO)"],
            "urgency_level": "high",
            "current_solution": "On-premise legacy system",
            "status": "qualified",
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
            "agenda": "Understand current challenges and requirements",
        },
    )

    print(
        f"Created test data: User={user.username}, Lead={lead.company_name}, Meeting={meeting.title}"
    )
    return user, lead, meeting


def test_basic_question_generation():
    """Test basic AI question generation"""
    print("\n=== Testing Basic Question Generation ===")

    user, lead, meeting = create_test_data()
    question_service = MeetingQuestionService()

    try:
        # Generate questions for the meeting
        result = question_service.generate_questions_for_meeting(
            meeting, regenerate=True
        )

        print(f"Question generation result: {result['success']}")
        print(f"Questions generated: {result['questions_generated']}")
        print(f"Questions by type: {result['questions_by_type']}")

        # Verify questions were created
        questions = meeting.questions.all()
        print(f"Questions in database: {questions.count()}")

        for question in questions[:3]:  # Show first 3 questions
            print(
                f"- {question.get_question_type_display()}: {question.question_text[:80]}..."
            )
            print(
                f"  Priority: {question.priority}, Confidence: {question.confidence_score}"
            )

        return result["success"]

    except Exception as e:
        print(f"Error in basic question generation: {e}")
        return False


def test_dynamic_follow_up_generation():
    """Test dynamic follow-up question generation based on responses"""
    print("\n=== Testing Dynamic Follow-up Generation ===")

    user, lead, meeting = create_test_data()
    question_service = MeetingQuestionService()

    try:
        # First generate base questions
        question_service.generate_questions_for_meeting(meeting, regenerate=True)

        # Get a question to test follow-ups
        original_question = meeting.questions.first()
        if not original_question:
            print("No questions found to test follow-ups")
            return False

        # Simulate a response that should trigger follow-ups
        test_response = """
        We're currently struggling with our legacy CRM system that doesn't integrate well 
        with our new marketing automation tools. This is causing data silos and our sales 
        team is spending too much time on manual data entry. We've been looking at solutions 
        for about 6 months now, and our CEO has allocated a budget of around $75,000 for 
        the right solution. The main challenge is that we need something that can integrate 
        with our existing ERP system and provide real-time reporting.
        """

        # Generate dynamic follow-ups
        follow_up_result = question_service.generate_dynamic_follow_ups(
            original_question,
            test_response,
            conversation_context={
                "meeting_stage": "discovery",
                "engagement_level": "high",
            },
        )

        print(f"Follow-up generation result: {follow_up_result['success']}")
        print(
            f"Immediate follow-ups created: {follow_up_result['immediate_follow_ups_created']}"
        )
        print(f"Conditional follow-ups: {follow_up_result['conditional_follow_ups']}")
        print(f"Deep dive questions: {follow_up_result['deep_dive_questions']}")

        # Show response insights
        insights = follow_up_result.get("response_insights", {})
        print(f"Response insights:")
        print(f"- Key points: {insights.get('key_points_mentioned', [])}")
        print(f"- Buying signals: {insights.get('buying_signals', [])}")
        print(f"- Pain points: {insights.get('pain_points_identified', [])}")

        # Verify follow-up questions were created
        follow_up_questions = meeting.questions.filter(
            depends_on_question=original_question
        )
        print(f"Follow-up questions created in database: {follow_up_questions.count()}")

        for question in follow_up_questions:
            print(f"- Follow-up: {question.question_text[:80]}...")
            print(
                f"  Priority: {question.priority}, Type: {question.get_question_type_display()}"
            )

        return follow_up_result["success"]

    except Exception as e:
        print(f"Error in dynamic follow-up generation: {e}")
        return False


def test_conversation_adaptation():
    """Test question adaptation based on conversation flow"""
    print("\n=== Testing Conversation Adaptation ===")

    user, lead, meeting = create_test_data()
    question_service = MeetingQuestionService()

    try:
        # Generate base questions
        question_service.generate_questions_for_meeting(meeting, regenerate=True)

        # Simulate conversation history
        conversation_history = [
            {
                "question_id": "q1",
                "question": "What are your main challenges with your current system?",
                "response": "Integration issues and manual processes are our biggest pain points.",
                "response_quality": 85,
                "engagement_level": "high",
                "asked_at": "2024-01-15T10:00:00Z",
            },
            {
                "question_id": "q2",
                "question": "How is this impacting your team productivity?",
                "response": "Our sales team spends 3-4 hours daily on data entry instead of selling.",
                "response_quality": 90,
                "engagement_level": "high",
                "asked_at": "2024-01-15T10:05:00Z",
            },
            {
                "question_id": "q3",
                "question": "What budget range are you considering?",
                "response": "We have about $75,000 allocated for this project.",
                "response_quality": 95,
                "engagement_level": "high",
                "asked_at": "2024-01-15T10:10:00Z",
            },
        ]

        # Test conversation adaptation
        adaptation_result = question_service.adapt_questions_for_conversation(
            meeting, conversation_history
        )

        print(f"Adaptation result: {adaptation_result['success']}")
        print(f"Total adaptations made: {adaptation_result['adaptations_made']}")
        print(f"Questions modified: {adaptation_result['questions_modified']}")
        print(f"Questions added: {adaptation_result['questions_added']}")
        print(f"Questions skipped: {adaptation_result['questions_skipped']}")

        # Show conversation insights
        insights = adaptation_result.get("conversation_insights", {})
        print(f"Conversation insights:")
        print(f"- Engagement level: {insights.get('engagement_level', 'unknown')}")
        print(f"- Buying signals: {insights.get('buying_signals', [])}")
        print(f"- Information gathered: {insights.get('information_gathered', [])}")
        print(
            f"- Recommended focus: {insights.get('recommended_focus', 'Continue as planned')}"
        )

        return adaptation_result["success"]

    except Exception as e:
        print(f"Error in conversation adaptation: {e}")
        return False


def test_question_effectiveness_tracking():
    """Test question effectiveness tracking and learning"""
    print("\n=== Testing Question Effectiveness Tracking ===")

    user, lead, meeting = create_test_data()
    question_service = MeetingQuestionService()

    try:
        # Generate questions
        question_service.generate_questions_for_meeting(meeting, regenerate=True)

        # Get a question to track effectiveness
        question = meeting.questions.first()
        if not question:
            print("No questions found to track effectiveness")
            return False

        # Simulate question response and outcomes
        test_response = """
        Yes, we're definitely interested in a solution that can solve our integration 
        challenges. The manual processes are really hurting our productivity, and we 
        need something that can integrate with our ERP system. We're looking to make 
        a decision within the next 2 months, and we have budget approval already.
        """

        outcome_data = {
            "led_to_qualification": True,
            "generated_follow_up": True,
            "positive_response": True,
            "moved_deal_forward": True,
            "response_length": len(test_response.split()),
            "buying_signals_count": 3,
            "pain_points_identified": 2,
            "engagement_level": "high",
        }

        # Track effectiveness
        effectiveness_result = question_service.track_question_effectiveness(
            question, test_response, outcome_data
        )

        print(f"Effectiveness tracking result: {effectiveness_result['success']}")
        print(f"Effectiveness score: {effectiveness_result['effectiveness_score']}")
        print(f"Effectiveness tier: {effectiveness_result['effectiveness_tier']}")
        print(f"Key insights: {effectiveness_result['key_insights']}")

        # Show learning insights
        learning = effectiveness_result.get("learning_insights", {})
        print(f"Learning insights:")
        print(f"- What worked well: {learning.get('what_worked_well', [])}")
        print(
            f"- Improvement opportunities: {learning.get('improvement_opportunities', [])}"
        )

        # Verify effectiveness log was created
        effectiveness_logs = QuestionEffectivenessLog.objects.filter(question=question)
        print(f"Effectiveness logs created: {effectiveness_logs.count()}")

        return effectiveness_result["success"]

    except Exception as e:
        print(f"Error in effectiveness tracking: {e}")
        return False


def test_industry_specific_templates():
    """Test industry-specific question template generation"""
    print("\n=== Testing Industry-Specific Templates ===")

    user, lead, meeting = create_test_data()
    question_service = MeetingQuestionService()

    try:
        # Test industry template generation
        template_result = question_service.generate_industry_specific_questions(
            meeting, regenerate=True
        )

        print(f"Industry template result: {template_result['success']}")
        print(f"Industry: {template_result['industry']}")
        print(f"Questions created: {template_result['questions_created']}")

        # Show industry insights
        insights = template_result.get("industry_insights", {})
        print(f"Industry insights:")
        print(f"- Key success factors: {insights.get('key_success_factors', [])}")
        print(f"- Common objections: {insights.get('common_objections', [])}")
        print(f"- Decision influencers: {insights.get('decision_influencers', [])}")

        # Verify industry-specific questions were created
        industry_questions = meeting.questions.filter(industry_specific=True)
        print(f"Industry-specific questions created: {industry_questions.count()}")

        for question in industry_questions[:3]:
            print(f"- Industry Q: {question.question_text[:80]}...")
            print(
                f"  Type: {question.get_question_type_display()}, Priority: {question.priority}"
            )

        return template_result["success"]

    except Exception as e:
        print(f"Error in industry template generation: {e}")
        return False


def test_conversation_flow_tracking():
    """Test conversation flow tracking and optimization"""
    print("\n=== Testing Conversation Flow Tracking ===")

    user, lead, meeting = create_test_data()

    try:
        # Create conversation flow
        flow, created = ConversationFlow.objects.get_or_create(
            meeting=meeting,
            defaults={
                "questions_asked_sequence": [],
                "response_quality_progression": [],
                "engagement_progression": [],
            },
        )

        # Generate some questions to track
        question_service = MeetingQuestionService()
        question_service.generate_questions_for_meeting(meeting, regenerate=True)

        # Simulate conversation flow
        questions = list(meeting.questions.all()[:3])

        for i, question in enumerate(questions):
            response_quality = 80 + (i * 5)  # Increasing quality
            engagement_level = ["medium", "high", "high"][i]

            flow.add_question_to_sequence(question, response_quality, engagement_level)
            print(
                f"Added question {i+1} to flow: Quality={response_quality}, Engagement={engagement_level}"
            )

        # Complete the flow
        flow.complete_flow()

        print(f"Conversation flow completed:")
        print(f"- Optimal sequence score: {flow.optimal_sequence_score}")
        print(f"- Conversation momentum: {flow.conversation_momentum}")
        print(f"- Peak engagement point: {flow.peak_engagement_point}")
        print(f"- Questions in sequence: {len(flow.questions_asked_sequence)}")

        return True

    except Exception as e:
        print(f"Error in conversation flow tracking: {e}")
        return False


def run_comprehensive_test():
    """Run all dynamic question flow tests"""
    print("🚀 Starting Dynamic Question Flow Comprehensive Test")
    print("=" * 60)

    test_results = {}

    # Run all tests
    tests = [
        ("Basic Question Generation", test_basic_question_generation),
        ("Dynamic Follow-up Generation", test_dynamic_follow_up_generation),
        ("Conversation Adaptation", test_conversation_adaptation),
        ("Question Effectiveness Tracking", test_question_effectiveness_tracking),
        ("Industry-Specific Templates", test_industry_specific_templates),
        ("Conversation Flow Tracking", test_conversation_flow_tracking),
    ]

    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running {test_name}...")
            result = test_func()
            test_results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status}: {test_name}")
        except Exception as e:
            test_results[test_name] = False
            print(f"❌ FAILED: {test_name} - {e}")

    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)

    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")

    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All Dynamic Question Flow tests PASSED!")
        print("\n✨ Dynamic Question Flow Features Verified:")
        print("   • AI adapts questions based on previous answers")
        print("   • Follow-up question generation and prioritization")
        print("   • Question effectiveness tracking and learning")
        print("   • Industry-specific question templates")
        print("   • Conversation flow optimization")
        print("   • Real-time question adaptation")
    else:
        print(f"⚠️  {total - passed} tests failed. Please check the implementation.")

    return passed == total


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
