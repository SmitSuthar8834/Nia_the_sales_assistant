#!/usr/bin/env python
"""
Test script for AI Question Generation functionality
"""

import os
import sys
from pathlib import Path

import django

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from datetime import timedelta

from django.utils import timezone

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nia_sales_assistant.settings")
django.setup()

from django.contrib.auth import get_user_model

from ai_service.models import AIInsights, Lead
from meeting_service.models import Meeting, MeetingQuestion
from meeting_service.question_service import MeetingQuestionService

User = get_user_model()


def test_ai_question_generation():
    """Test the AI question generation functionality"""
    print("🤖 Testing AI Question Generation for Meetings")
    print("=" * 60)

    try:
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username="test_sales_rep",
            defaults={
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "Sales Rep",
            },
        )
        print(f"✅ Using test user: {user.username}")

        # Create a test lead with comprehensive data
        lead_data = {
            "company_name": "TechCorp Solutions",
            "industry": "technology",
            "company_size": "100-500 employees",
            "contact_info": {
                "name": "John Smith",
                "email": "john.smith@techcorp.com",
                "phone": "+1-555-0123",
                "title": "VP of Sales",
                "department": "Sales",
            },
            "pain_points": [
                "Manual lead qualification process",
                "Lack of sales conversation insights",
                "Poor CRM data quality",
                "Inconsistent follow-up processes",
            ],
            "requirements": [
                "AI-powered conversation analysis",
                "Automated lead scoring",
                "CRM integration",
                "Real-time sales recommendations",
            ],
            "budget_info": "$50,000 - $100,000 annual budget",
            "timeline": "Need solution implemented within 3 months",
            "decision_makers": [
                "John Smith (VP Sales)",
                "Sarah Johnson (CTO)",
                "Mike Davis (CEO)",
            ],
            "urgency_level": "high",
            "current_solution": "Using basic CRM with manual processes",
            "competitors_mentioned": ["Salesforce", "HubSpot"],
            "status": "qualified",
        }

        # Create or update the test lead
        lead, created = Lead.objects.update_or_create(
            user=user, company_name=lead_data["company_name"], defaults=lead_data
        )
        print(
            f"✅ {'Created' if created else 'Updated'} test lead: {lead.company_name}"
        )

        # Create AI insights for the lead
        ai_insights, created = AIInsights.objects.update_or_create(
            lead=lead,
            defaults={
                "lead_score": 85.0,
                "conversion_probability": 72.0,
                "quality_tier": "high",
                "opportunity_conversion_score": 78.0,
                "recommended_for_conversion": True,
                "estimated_deal_size": "$75,000",
                "sales_cycle_prediction": "3-4 months",
                "primary_strategy": "consultative",
                "competitive_risk": "medium",
                "next_best_action": "Schedule discovery call to understand current pain points",
                "recommended_actions": [
                    "Conduct detailed needs assessment",
                    "Demonstrate AI conversation analysis features",
                    "Provide ROI calculator and case studies",
                    "Schedule technical demo with CTO",
                ],
                "key_messaging": [
                    "AI-powered sales intelligence",
                    "Automated lead qualification",
                    "Seamless CRM integration",
                    "Proven ROI in similar companies",
                ],
                "risk_factors": [
                    "Competitive evaluation in progress",
                    "Budget approval process unclear",
                ],
                "opportunities": [
                    "High urgency and clear timeline",
                    "Strong technical requirements match",
                    "Multiple decision makers engaged",
                ],
            },
        )
        print(f"✅ {'Created' if created else 'Updated'} AI insights for lead")

        # Create a test meeting
        meeting_data = {
            "title": "Discovery Call - TechCorp Solutions",
            "description": "Initial discovery call to understand business challenges and requirements",
            "meeting_type": "discovery",
            "scheduled_at": timezone.now() + timedelta(days=1),
            "duration_minutes": 60,
            "status": "scheduled",
            "agenda": "Understand current sales process, identify pain points, discuss solution fit",
            "meeting_platform": "Google Meet",
            "participants": [
                {
                    "name": "John Smith",
                    "email": "john.smith@techcorp.com",
                    "role": "VP Sales",
                },
                {
                    "name": "Sarah Johnson",
                    "email": "sarah.johnson@techcorp.com",
                    "role": "CTO",
                },
            ],
        }

        meeting, created = Meeting.objects.update_or_create(
            lead=lead, title=meeting_data["title"], defaults=meeting_data
        )
        print(f"✅ {'Created' if created else 'Updated'} test meeting: {meeting.title}")

        # Initialize the question service
        question_service = MeetingQuestionService()
        print("✅ Initialized MeetingQuestionService")

        # Generate questions for the meeting
        print("\n🔄 Generating AI-powered questions for the meeting...")
        result = question_service.generate_questions_for_meeting(
            meeting, regenerate=True
        )

        if result["success"]:
            print(
                f"✅ Successfully generated {result['questions_generated']} questions"
            )
            print(f"📊 Questions by type: {result['questions_by_type']}")

            # Display generated questions
            print("\n📝 Generated Questions:")
            print("-" * 40)

            questions = question_service.get_prioritized_questions(meeting)
            for i, question in enumerate(questions[:10], 1):  # Show top 10 questions
                print(
                    f"\n{i}. [{question.get_question_type_display()}] Priority: {question.priority}"
                )
                print(f"   Question: {question.question_text}")
                print(f"   Confidence: {question.confidence_score}%")
                print(
                    f"   Industry Specific: {'Yes' if question.industry_specific else 'No'}"
                )
                print(
                    f"   Conversion Focused: {'Yes' if question.is_conversion_focused else 'No'}"
                )

                if question.generation_context.get("rationale"):
                    print(f"   Rationale: {question.generation_context['rationale']}")

            # Test getting conversion-focused questions
            conversion_questions = question_service.get_conversion_focused_questions(
                meeting
            )
            print(f"\n🎯 Conversion-focused questions: {len(conversion_questions)}")

            # Test getting questions by type
            discovery_questions = question_service.get_questions_by_type(
                meeting, "discovery"
            )
            budget_questions = question_service.get_questions_by_type(meeting, "budget")
            print(f"🔍 Discovery questions: {len(discovery_questions)}")
            print(f"💰 Budget questions: {len(budget_questions)}")

            # Test marking a question as asked
            if questions:
                test_question = questions[0]
                success = question_service.mark_question_asked(
                    test_question,
                    "We're currently using a basic CRM but struggling with lead qualification and follow-up consistency.",
                    "detailed",
                )
                if success:
                    print(
                        f"✅ Successfully marked question as asked: {test_question.question_text[:50]}..."
                    )

                # Test effectiveness update
                success = question_service.update_question_effectiveness(
                    test_question,
                    {
                        "led_to_qualification": True,
                        "generated_follow_up": True,
                        "positive_response": True,
                        "moved_deal_forward": True,
                    },
                )
                if success:
                    print(
                        f"✅ Updated question effectiveness score: {test_question.effectiveness_score}"
                    )

            print(f"\n📈 Generation Strategy:")
            strategy = result.get("generation_metadata", {})
            if strategy:
                print(f"   Total Questions: {strategy.get('total_questions', 0)}")
                print(f"   High Priority: {strategy.get('high_priority_count', 0)}")
                print(
                    f"   Estimated Duration: {strategy.get('meeting_duration_estimate', {}).get('recommended_duration', 0)} minutes"
                )
                print(
                    f"   Key Objectives: {', '.join(strategy.get('key_objectives', []))}"
                )

        else:
            print(
                f"❌ Failed to generate questions: {result.get('error', 'Unknown error')}"
            )
            return False

        print("\n" + "=" * 60)
        print("✅ AI Question Generation test completed successfully!")
        print(f"📊 Total questions in database: {MeetingQuestion.objects.count()}")
        print(f"🎯 Questions for this meeting: {meeting.questions.count()}")

        return True

    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_question_admin_display():
    """Test the admin display functionality"""
    print("\n🔧 Testing Admin Display Functionality")
    print("-" * 40)

    try:
        # Get a sample meeting with questions
        meeting = Meeting.objects.filter(questions__isnull=False).first()
        if not meeting:
            print("❌ No meetings with questions found")
            return False

        print(f"✅ Testing with meeting: {meeting.title}")

        # Test question display methods
        questions = meeting.questions.all()[:3]  # Test with first 3 questions

        for question in questions:
            print(f"\n📝 Question: {question.question_text[:50]}...")
            print(f"   Type: {question.get_question_type_display()}")
            print(
                f"   Priority: {question.priority} ({question.get_priority_level_display()})"
            )
            print(f"   Confidence: {question.confidence_score}%")
            print(f"   Asked: {'Yes' if question.asked_at else 'No'}")
            print(
                f"   Conversion Focused: {'Yes' if question.is_conversion_focused else 'No'}"
            )
            print(
                f"   Industry Specific: {'Yes' if question.industry_specific else 'No'}"
            )

        print("✅ Admin display test completed")
        return True

    except Exception as e:
        print(f"❌ Error testing admin display: {str(e)}")
        return False


if __name__ == "__main__":
    print("🚀 Starting AI Question Generation Tests")
    print("=" * 60)

    # Run the main test
    success = test_ai_question_generation()

    if success:
        # Run admin display test
        test_question_admin_display()

        print("\n🎉 All tests completed successfully!")
        print("\n💡 Next steps:")
        print("   1. Check the Django admin to see the generated questions")
        print("   2. Navigate to /admin/meeting_service/meetingquestion/")
        print("   3. View the meeting admin to see questions inline")
        print("   4. Test the question generation in a real meeting scenario")
    else:
        print("\n❌ Tests failed. Please check the error messages above.")
        sys.exit(1)
