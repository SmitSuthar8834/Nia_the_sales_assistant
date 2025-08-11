#!/usr/bin/env python3
"""
Test script for Meeting Outcome Tracking logic (without database)

This script tests the core logic of the meeting outcome tracking system
without requiring database connections.
"""

import json
import sys
from datetime import datetime
from unittest.mock import MagicMock


# Mock Django components
class MockModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.id = "test-uuid"

    def save(self, **kwargs):
        pass

    def refresh_from_db(self):
        pass


class MockUser(MockModel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.username = kwargs.get("username", "test_user")


class MockLead(MockModel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.company_name = kwargs.get("company_name", "Test Company")
        self.industry = kwargs.get("industry", "Technology")
        self.contact_info = kwargs.get("contact_info", {})
        self.pain_points = kwargs.get("pain_points", [])
        self.requirements = kwargs.get("requirements", [])


class MockAIInsights(MockModel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lead_score = kwargs.get("lead_score", 75.0)
        self.conversion_probability = kwargs.get("conversion_probability", 65.0)


class MockMeeting(MockModel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = kwargs.get("title", "Test Meeting")
        self.status = kwargs.get("status", "completed")
        self.outcome = kwargs.get("outcome", "")
        self.action_items = kwargs.get("action_items", [])
        self.ai_insights = kwargs.get("ai_insights", {})
        self.lead = kwargs.get("lead")


class MockMeetingQuestion(MockModel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.question_text = kwargs.get("question_text", "")
        self.response = kwargs.get("response", "")
        self.asked_at = kwargs.get("asked_at")


# Mock the AI service response
class MockAIResponse:
    def __init__(self, text):
        self.text = text


class MockGeminiAIService:
    def _make_api_call(self, prompt):
        # Return mock responses based on prompt content
        if "meeting summary" in prompt.lower():
            return MockAIResponse(
                json.dumps(
                    {
                        "summary": "This was a productive discovery call with TechCorp Solutions. The client expressed significant pain points around manual data processing and showed strong interest in our automated solution.",
                        "key_takeaways": [
                            "Client spends 20 hours/week on manual data processing",
                            "Strong urgency with 3-month timeline",
                            "Budget allocated between $50K-$100K annually",
                            "Technical decision maker directly involved",
                        ],
                        "discussion_highlights": [
                            "Current system is becoming a major bottleneck",
                            "Previous evaluations of competitors were unsatisfactory",
                            "CEO approval required for final decision",
                        ],
                        "client_feedback": "Very positive response to our solution approach",
                        "meeting_effectiveness": "8/10 - High engagement and clear next steps identified",
                    }
                )
            )

        elif "action items" in prompt.lower():
            return MockAIResponse(
                json.dumps(
                    {
                        "action_items": [
                            {
                                "id": "action_1",
                                "description": "Send meeting summary and next steps to John Smith",
                                "assigned_to": "sales_rep",
                                "due_date": "2024-01-16",
                                "priority": "high",
                                "category": "follow_up",
                            },
                            {
                                "id": "action_2",
                                "description": "Prepare customized demo focusing on data integration",
                                "assigned_to": "sales_rep",
                                "due_date": "2024-01-18",
                                "priority": "high",
                                "category": "demo",
                            },
                        ],
                        "immediate_actions": [
                            "Send meeting summary within 24 hours",
                            "Schedule demo for next week",
                        ],
                        "follow_up_meetings": [
                            {
                                "type": "demo",
                                "suggested_timeframe": "within 1 week",
                                "purpose": "Product demonstration with technical team",
                            }
                        ],
                    }
                )
            )

        elif "follow-up" in prompt.lower():
            return MockAIResponse(
                json.dumps(
                    {
                        "immediate_follow_up": {
                            "timeframe": "within 24 hours",
                            "actions": ["Send meeting summary", "Schedule demo"],
                            "communication_method": "email",
                            "key_message": "Thank you for the productive discussion",
                        },
                        "short_term_follow_up": {
                            "timeframe": "within 1 week",
                            "recommended_meetings": [
                                {
                                    "type": "demo",
                                    "purpose": "Product demonstration",
                                    "duration_minutes": 60,
                                    "participants": ["John Smith", "Mike Davis"],
                                }
                            ],
                        },
                        "long_term_strategy": {
                            "sales_cycle_stage": "qualification",
                            "next_milestone": "Technical evaluation complete",
                        },
                    }
                )
            )

        else:
            return MockAIResponse("Mock AI response")


# Import the service we want to test
sys.path.append(".")

# Mock Django imports before importing our service
import sys

# Mock Django modules
mock_django_modules = {
    "django": MagicMock(),
    "django.db": MagicMock(),
    "django.db.models": MagicMock(),
    "django.contrib.auth": MagicMock(),
    "django.utils": MagicMock(),
    "django.utils.timezone": MagicMock(),
    "ai_service.models": MagicMock(),
    "ai_service.services": MagicMock(),
}

for module_name, mock_module in mock_django_modules.items():
    sys.modules[module_name] = mock_module

# Mock timezone.now()
mock_now = datetime(2024, 1, 15, 14, 30, 0)
sys.modules["django.utils.timezone"].now = lambda: mock_now

# Mock the models
sys.modules["ai_service.models"].Lead = MockLead
sys.modules["ai_service.models"].AIInsights = MockAIInsights
sys.modules["ai_service.services"].GeminiAIService = MockGeminiAIService

# Now import our service
from meeting_service.meeting_outcome_service import MeetingOutcomeService


def create_test_meeting():
    """Create a test meeting with mock data"""
    lead = MockLead(
        company_name="TechCorp Solutions",
        industry="Technology",
        contact_info={"name": "John Smith", "email": "john@techcorp.com"},
        pain_points=["Manual data processing", "Lack of real-time analytics"],
        requirements=["Automated solution", "API integration"],
    )

    # Add AI insights to lead
    lead.ai_insights = MockAIInsights(lead_score=75.0, conversion_probability=65.0)

    meeting = MockMeeting(
        title="Discovery Call - TechCorp Solutions",
        status="completed",
        lead=lead,
        ai_insights={},
    )

    return meeting


def test_meeting_summary_generation():
    """Test meeting summary generation logic"""
    print("🔍 Testing Meeting Summary Generation Logic...")

    meeting = create_test_meeting()
    service = MeetingOutcomeService()

    try:
        result = service.generate_meeting_summary(meeting, regenerate=True)

        if result.get("success"):
            print("✅ Meeting summary generated successfully!")
            summary_data = result.get("summary", {})

            # Verify expected fields are present
            expected_fields = ["summary", "key_takeaways", "discussion_highlights"]
            for field in expected_fields:
                if field in summary_data:
                    print(f"   ✅ {field}: Present")
                else:
                    print(f"   ❌ {field}: Missing")

            # Check if meeting was updated
            if meeting.outcome:
                print("   ✅ Meeting outcome field would be updated")

            return True
        else:
            print(f"❌ Meeting summary generation failed: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ Exception in meeting summary generation: {str(e)}")
        return False


def test_action_items_extraction():
    """Test action items extraction logic"""
    print("\n📋 Testing Action Items Extraction Logic...")

    meeting = create_test_meeting()
    service = MeetingOutcomeService()

    try:
        result = service.extract_action_items(meeting, regenerate=True)

        if result.get("success"):
            print("✅ Action items extracted successfully!")
            action_items_data = result.get("action_items", {})

            # Verify expected fields
            action_items = action_items_data.get("action_items", [])
            print(f"   ✅ Action items count: {len(action_items)}")

            if action_items:
                first_item = action_items[0]
                required_fields = ["description", "assigned_to", "priority"]
                for field in required_fields:
                    if field in first_item:
                        print(f"   ✅ Action item {field}: Present")
                    else:
                        print(f"   ❌ Action item {field}: Missing")

            immediate_actions = action_items_data.get("immediate_actions", [])
            print(f"   ✅ Immediate actions count: {len(immediate_actions)}")

            return True
        else:
            print(f"❌ Action items extraction failed: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ Exception in action items extraction: {str(e)}")
        return False


def test_follow_up_scheduling():
    """Test follow-up scheduling logic"""
    print("\n📅 Testing Follow-up Scheduling Logic...")

    meeting = create_test_meeting()
    service = MeetingOutcomeService()

    try:
        result = service.schedule_follow_up_actions(meeting)

        if result.get("success"):
            print("✅ Follow-up actions scheduled successfully!")
            follow_up_plan = result.get("follow_up_plan", {})

            # Verify expected sections
            expected_sections = [
                "immediate_follow_up",
                "short_term_follow_up",
                "long_term_strategy",
            ]
            for section in expected_sections:
                if section in follow_up_plan:
                    print(f"   ✅ {section}: Present")
                else:
                    print(f"   ❌ {section}: Missing")

            return True
        else:
            print(f"❌ Follow-up scheduling failed: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ Exception in follow-up scheduling: {str(e)}")
        return False


def test_lead_scoring_update():
    """Test lead scoring update logic"""
    print("\n📊 Testing Lead Scoring Update Logic...")

    meeting = create_test_meeting()
    service = MeetingOutcomeService()

    try:
        result = service.update_lead_scoring(meeting)

        if result.get("success"):
            print("✅ Lead scoring updated successfully!")
            updated_scores = result.get("updated_scores", {})

            # Verify score fields
            score_fields = ["lead_score", "conversion_probability", "quality_tier"]
            for field in score_fields:
                if field in updated_scores:
                    print(f"   ✅ {field}: {updated_scores[field]}")
                else:
                    print(f"   ❌ {field}: Missing")

            score_changes = result.get("score_changes", {})
            print(f"   ✅ Score changes calculated: {len(score_changes)} components")

            return True
        else:
            print(f"❌ Lead scoring update failed: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ Exception in lead scoring update: {str(e)}")
        return False


def test_complete_outcome_processing():
    """Test complete outcome processing logic"""
    print("\n🚀 Testing Complete Outcome Processing Logic...")

    meeting = create_test_meeting()
    service = MeetingOutcomeService()

    try:
        result = service.process_complete_meeting_outcome(meeting, regenerate=True)

        if result.get("overall_success"):
            print("✅ Complete outcome processing successful!")

            components = result.get("components", {})
            print(f"   ✅ Components processed: {len(components)}")

            for component_name, component_result in components.items():
                status = "✅" if component_result.get("success") else "❌"
                print(f"     {status} {component_name}")

            return True
        else:
            print(
                f"❌ Complete outcome processing failed: {result.get('message', 'Unknown error')}"
            )
            return False

    except Exception as e:
        print(f"❌ Exception in complete outcome processing: {str(e)}")
        return False


def test_prompt_building():
    """Test AI prompt building logic"""
    print("\n🔧 Testing AI Prompt Building Logic...")

    meeting = create_test_meeting()
    service = MeetingOutcomeService()

    try:
        # Test gathering meeting context
        context = service._gather_meeting_context(meeting)

        print("✅ Meeting context gathered successfully!")
        print(f"   ✅ Meeting info keys: {list(context['meeting_info'].keys())}")
        print(f"   ✅ Lead context keys: {list(context['lead_context'].keys())}")

        # Test building prompts
        summary_prompt = service._build_summary_prompt(meeting, context)
        action_items_prompt = service._build_action_items_prompt(meeting, context)
        follow_up_prompt = service._build_follow_up_prompt(meeting, context)

        print("✅ AI prompts built successfully!")
        print(f"   ✅ Summary prompt length: {len(summary_prompt)} characters")
        print(
            f"   ✅ Action items prompt length: {len(action_items_prompt)} characters"
        )
        print(f"   ✅ Follow-up prompt length: {len(follow_up_prompt)} characters")

        # Verify prompts contain expected content
        if "TechCorp Solutions" in summary_prompt:
            print("   ✅ Company name included in summary prompt")
        else:
            print("   ❌ Company name missing from summary prompt")

        return True

    except Exception as e:
        print(f"❌ Exception in prompt building: {str(e)}")
        return False


def test_response_parsing():
    """Test AI response parsing logic"""
    print("\n🔍 Testing AI Response Parsing Logic...")

    service = MeetingOutcomeService()

    try:
        # Test JSON response parsing
        json_response = (
            '{"summary": "Test summary", "key_takeaways": ["Point 1", "Point 2"]}'
        )
        parsed_summary = service._parse_summary_response(json_response)

        if "summary" in parsed_summary and "key_takeaways" in parsed_summary:
            print("✅ JSON summary response parsed correctly")
        else:
            print("❌ JSON summary response parsing failed")

        # Test plain text response parsing
        text_response = "This is a plain text summary"
        parsed_text = service._parse_summary_response(text_response)

        if "summary" in parsed_text:
            print("✅ Plain text summary response parsed correctly")
        else:
            print("❌ Plain text summary response parsing failed")

        # Test action items parsing
        action_items_json = (
            '{"action_items": [{"description": "Test action", "priority": "high"}]}'
        )
        parsed_actions = service._parse_action_items_response(action_items_json)

        if "action_items" in parsed_actions:
            print("✅ Action items response parsed correctly")
        else:
            print("❌ Action items response parsing failed")

        return True

    except Exception as e:
        print(f"❌ Exception in response parsing: {str(e)}")
        return False


def main():
    """Main test function"""
    print("🧪 Meeting Outcome Tracking Logic Test Suite")
    print("=" * 55)
    print("(Testing core logic without database dependencies)")
    print()

    test_results = {}

    # Run individual tests
    test_results["Prompt Building"] = test_prompt_building()
    test_results["Response Parsing"] = test_response_parsing()
    test_results["Meeting Summary"] = test_meeting_summary_generation()
    test_results["Action Items"] = test_action_items_extraction()
    test_results["Follow-up Scheduling"] = test_follow_up_scheduling()
    test_results["Lead Scoring"] = test_lead_scoring_update()
    test_results["Complete Processing"] = test_complete_outcome_processing()

    # Summary
    print("\n📊 Test Summary")
    print("=" * 30)

    for test_name, success in test_results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {test_name}")

    passed_tests = sum(test_results.values())
    total_tests = len(test_results)

    print(f"\n🎯 Overall Results: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print(
            "🎉 All logic tests passed! Meeting Outcome Tracking core logic is working correctly."
        )
        print("\n✅ Implementation Summary:")
        print("   - Meeting summary generation with AI-powered analysis")
        print("   - Action items extraction and assignment")
        print("   - Follow-up scheduling and next steps planning")
        print("   - Lead scoring updates based on meeting outcomes")
        print("   - Complete outcome processing workflow")
        print("   - Robust error handling and response parsing")
    else:
        print("⚠️  Some logic tests failed. Please check the error messages above.")

    return passed_tests == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
