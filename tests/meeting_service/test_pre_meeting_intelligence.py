#!/usr/bin/env python3
"""
Test script for Pre-Meeting Intelligence functionality
Tests the implementation of the Pre-Meeting Intelligence task
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
from meeting_service.models import Meeting
from meeting_service.pre_meeting_intelligence import PreMeetingIntelligenceService

User = get_user_model()


def create_test_data():
    """Create test data for the pre-meeting intelligence test"""
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
        company_name="TechCorp Solutions",
        defaults={
            "contact_name": "John Smith",
            "contact_email": "john.smith@techcorp.com",
            "contact_phone": "+1-555-0123",
            "industry": "Technology",
            "company_size": "100-500 employees",
            "status": "qualified",
            "pain_points": [
                "Manual processes causing inefficiencies",
                "Lack of real-time visibility into operations",
                "Difficulty scaling current systems",
            ],
            "requirements": [
                "Automated workflow management",
                "Real-time dashboard and reporting",
                "Scalable cloud-based solution",
            ],
            "budget_info": "$50,000 - $100,000 annual budget",
            "timeline": "Implementation needed within 6 months",
            "decision_makers": ["John Smith (CTO)", "Sarah Johnson (CEO)"],
            "urgency_level": "high",
            "current_solution": "Legacy on-premise system",
            "competitors_mentioned": ["Competitor A", "Competitor B"],
        },
    )

    # Create AI insights for the lead
    ai_insights, created = AIInsights.objects.get_or_create(
        lead=lead,
        defaults={
            "lead_score": 85.0,
            "conversion_probability": 75.0,
            "quality_tier": "high",
            "recommended_actions": [
                "Schedule technical demo",
                "Prepare ROI analysis",
                "Connect with decision makers",
            ],
            "key_messaging": [
                "Focus on automation benefits",
                "Highlight scalability advantages",
                "Emphasize quick implementation",
            ],
            "risk_factors": ["Budget approval process", "Competitive evaluation"],
            "opportunities": [
                "Urgent timeline creates buying pressure",
                "Clear pain points align with our solution",
            ],
            "next_best_action": "Schedule product demonstration",
        },
    )

    # Create test meeting
    meeting, created = Meeting.objects.get_or_create(
        lead=lead,
        title="Discovery Call - TechCorp Solutions",
        defaults={
            "description": "Initial discovery call to understand requirements and pain points",
            "meeting_type": "discovery",
            "scheduled_at": timezone.now() + timedelta(days=1),
            "duration_minutes": 60,
            "status": "scheduled",
            "participants": [
                {
                    "name": "John Smith",
                    "email": "john.smith@techcorp.com",
                    "role": "CTO",
                },
                {
                    "name": "Sarah Johnson",
                    "email": "sarah.johnson@techcorp.com",
                    "role": "CEO",
                },
            ],
            "meeting_platform": "Google Meet",
        },
    )

    print(f"Created test data:")
    print(f"- User: {user.username}")
    print(f"- Lead: {lead.company_name}")
    print(f"- Meeting: {meeting.title}")
    print(f"- AI Insights: Score {ai_insights.lead_score}")

    return user, lead, meeting


def test_meeting_agenda_generation():
    """Test AI-powered meeting agenda generation"""
    print("\n=== Testing Meeting Agenda Generation ===")

    user, lead, meeting = create_test_data()
    service = PreMeetingIntelligenceService()

    # Test agenda generation
    print("Generating meeting agenda...")
    result = service.generate_meeting_agenda(meeting)

    print(f"Agenda generation result: {result['success']}")
    if result["success"]:
        print(f"Formatted agenda length: {len(result.get('formatted_agenda', ''))}")
        print(f"Key objectives: {len(result.get('key_objectives', []))}")
        print(
            f"Agenda structure sections: {list(result.get('agenda_structure', {}).keys())}"
        )

        # Print sample agenda
        agenda = result.get("formatted_agenda", "")
        if agenda:
            print("\nSample agenda (first 300 chars):")
            print(agenda[:300] + "..." if len(agenda) > 300 else agenda)
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")

    return result


def test_talking_points_generation():
    """Test AI-powered talking points generation"""
    print("\n=== Testing Talking Points Generation ===")

    user, lead, meeting = create_test_data()
    service = PreMeetingIntelligenceService()

    # Test talking points generation
    print("Generating talking points...")
    result = service.generate_talking_points(meeting)

    print(f"Talking points generation result: {result['success']}")
    if result["success"]:
        print(f"Opening statements: {len(result.get('opening_statements', []))}")
        print(f"Value propositions: {len(result.get('value_propositions', []))}")
        print(
            f"Pain point discussions: {len(result.get('pain_point_discussions', []))}"
        )
        print(f"Solution positioning: {len(result.get('solution_positioning', []))}")

        # Print sample talking points
        if result.get("opening_statements"):
            print(f"\nSample opening statement: {result['opening_statements'][0]}")
        if result.get("value_propositions"):
            print(f"Sample value proposition: {result['value_propositions'][0]}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")

    return result


def test_competitive_analysis():
    """Test AI-powered competitive analysis"""
    print("\n=== Testing Competitive Analysis ===")

    user, lead, meeting = create_test_data()
    service = PreMeetingIntelligenceService()

    # Test competitive analysis
    print("Generating competitive analysis...")
    result = service.generate_competitive_analysis(meeting)

    print(f"Competitive analysis result: {result['success']}")
    if result["success"]:
        print(
            f"Identified competitors: {len(result.get('identified_competitors', []))}"
        )
        print(
            f"Differentiation points: {len(result.get('differentiation_points', []))}"
        )
        print(f"Competitive threats: {len(result.get('competitive_threats', []))}")
        print(
            f"Competitive risk level: {result.get('competitive_risk_level', 'unknown')}"
        )

        # Print sample competitive insights
        if result.get("differentiation_points"):
            print(
                f"\nSample differentiation point: {result['differentiation_points'][0]}"
            )
        if result.get("positioning_strategy"):
            strategy = result["positioning_strategy"]
            print(
                f"Primary positioning message: {strategy.get('primary_message', 'N/A')}"
            )
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")

    return result


def test_comprehensive_preparation_materials():
    """Test comprehensive preparation materials generation"""
    print("\n=== Testing Comprehensive Preparation Materials ===")

    user, lead, meeting = create_test_data()
    service = PreMeetingIntelligenceService()

    # Test comprehensive preparation materials
    print("Generating comprehensive preparation materials...")
    result = service.generate_preparation_materials(meeting)

    print(f"Preparation materials result: {result['success']}")
    if result["success"]:
        print(f"Meeting ID: {result.get('meeting_id')}")
        print(f"Lead company: {result.get('lead_company')}")
        print(f"Meeting type: {result.get('meeting_type')}")

        # Check all components
        components = ["agenda", "talking_points", "competitive_analysis"]
        for component in components:
            comp_result = result.get(component, {})
            print(f"{component.title()} generated: {comp_result.get('success', False)}")

        # Check additional materials
        additional_materials = [
            "preparation_checklist",
            "key_research_points",
            "potential_objections",
            "success_criteria",
            "follow_up_actions",
            "risk_mitigation",
        ]
        for material in additional_materials:
            items = result.get(material, [])
            print(f"{material.replace('_', ' ').title()}: {len(items)} items")

        # Check preparation summary
        summary = result.get("preparation_summary", {})
        print(f"\nPreparation Summary:")
        print(f"- Readiness score: {summary.get('meeting_readiness_score', 0)}")
        print(f"- Key focus areas: {len(summary.get('key_focus_areas', []))}")
        print(
            f"- Preparation time: {summary.get('time_to_prepare_minutes', 0)} minutes"
        )

    else:
        print(f"Error: {result.get('error', 'Unknown error')}")

    return result


def test_meeting_ai_insights_storage():
    """Test that AI insights are properly stored in the meeting"""
    print("\n=== Testing AI Insights Storage ===")

    user, lead, meeting = create_test_data()
    service = PreMeetingIntelligenceService()

    # Generate preparation materials to populate AI insights
    print("Generating materials to test AI insights storage...")
    service.generate_preparation_materials(meeting)

    # Refresh meeting from database
    meeting.refresh_from_db()

    # Check AI insights
    ai_insights = meeting.ai_insights or {}
    print(f"AI insights stored: {bool(ai_insights)}")

    expected_sections = [
        "agenda_generation",
        "talking_points",
        "competitive_analysis",
        "preparation_materials",
    ]

    for section in expected_sections:
        if section in ai_insights:
            section_data = ai_insights[section]
            print(f"- {section}: {bool(section_data)}")
            if "generated_at" in section_data:
                print(f"  Generated at: {section_data['generated_at']}")
        else:
            print(f"- {section}: Missing")

    return ai_insights


def main():
    """Run all pre-meeting intelligence tests"""
    print("🤖 NIA Pre-Meeting Intelligence Test Suite")
    print("=" * 50)

    try:
        # Test individual components
        agenda_result = test_meeting_agenda_generation()
        talking_points_result = test_talking_points_generation()
        competitive_result = test_competitive_analysis()

        # Test comprehensive preparation
        preparation_result = test_comprehensive_preparation_materials()

        # Test AI insights storage
        insights_result = test_meeting_ai_insights_storage()

        # Summary
        print("\n" + "=" * 50)
        print("🎯 TEST SUMMARY")
        print("=" * 50)

        tests = [
            ("Meeting Agenda Generation", agenda_result.get("success", False)),
            ("Talking Points Generation", talking_points_result.get("success", False)),
            ("Competitive Analysis", competitive_result.get("success", False)),
            ("Comprehensive Preparation", preparation_result.get("success", False)),
            ("AI Insights Storage", bool(insights_result)),
        ]

        passed = sum(1 for _, success in tests if success)
        total = len(tests)

        for test_name, success in tests:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")

        print(f"\nResults: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All pre-meeting intelligence tests passed!")
        else:
            print("⚠️  Some tests failed. Check the implementation.")

    except Exception as e:
        print(f"❌ Test suite failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("Starting test execution...")
    main()
    print("Test execution completed.")
