#!/usr/bin/env python
"""
Test script to verify the admin interface for dynamic question flow
"""

import os
import sys
from pathlib import Path

import django

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))


# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nia_sales_assistant.settings")
django.setup()

from django.contrib.admin.sites import site

from meeting_service.admin import (
    ConversationFlowAdmin,
    MeetingAdmin,
    MeetingQuestionAdmin,
    QuestionEffectivenessLogAdmin,
    QuestionTemplateAdmin,
)
from meeting_service.models import (
    ConversationFlow,
    Meeting,
    MeetingQuestion,
    QuestionEffectivenessLog,
    QuestionTemplate,
)


def test_admin_registration():
    """Test that all models are properly registered in admin"""
    print("🔍 Testing Admin Registration...")

    # Check if models are registered
    registered_models = [model for model, admin_class in site._registry.items()]

    models_to_check = [
        Meeting,
        MeetingQuestion,
        QuestionTemplate,
        QuestionEffectivenessLog,
        ConversationFlow,
    ]

    for model in models_to_check:
        if model in registered_models:
            admin_class = site._registry[model]
            print(
                f"✅ {model.__name__} is registered with {admin_class.__class__.__name__}"
            )
        else:
            print(f"❌ {model.__name__} is NOT registered in admin")
            return False

    return True


def test_admin_list_displays():
    """Test that admin list displays are properly configured"""
    print("\n🔍 Testing Admin List Displays...")

    admin_configs = [
        (MeetingAdmin, "Meeting"),
        (MeetingQuestionAdmin, "MeetingQuestion"),
        (QuestionTemplateAdmin, "QuestionTemplate"),
        (QuestionEffectivenessLogAdmin, "QuestionEffectivenessLog"),
        (ConversationFlowAdmin, "ConversationFlow"),
    ]

    for admin_class, model_name in admin_configs:
        try:
            list_display = getattr(admin_class, "list_display", [])
            list_filter = getattr(admin_class, "list_filter", [])
            search_fields = getattr(admin_class, "search_fields", [])

            print(f"✅ {model_name}Admin:")
            print(f"   - List display fields: {len(list_display)}")
            print(f"   - List filters: {len(list_filter)}")
            print(f"   - Search fields: {len(search_fields)}")

        except Exception as e:
            print(f"❌ Error testing {model_name}Admin: {e}")
            return False

    return True


def test_admin_methods():
    """Test that custom admin methods exist and are callable"""
    print("\n🔍 Testing Admin Custom Methods...")

    # Test MeetingAdmin methods
    meeting_admin = MeetingAdmin(Meeting, site)
    methods_to_test = [
        "lead_company_display",
        "status_display",
        "meeting_actions",
        "lead_context_display",
        "ai_insights_display",
    ]

    for method_name in methods_to_test:
        if hasattr(meeting_admin, method_name):
            method = getattr(meeting_admin, method_name)
            if callable(method):
                print(f"✅ MeetingAdmin.{method_name} is callable")
            else:
                print(f"❌ MeetingAdmin.{method_name} is not callable")
                return False
        else:
            print(f"❌ MeetingAdmin.{method_name} does not exist")
            return False

    # Test MeetingQuestionAdmin methods
    question_admin = MeetingQuestionAdmin(MeetingQuestion, site)
    question_methods = [
        "question_preview",
        "meeting_title",
        "priority_display",
        "asked_status",
        "question_actions",
    ]

    for method_name in question_methods:
        if hasattr(question_admin, method_name):
            method = getattr(question_admin, method_name)
            if callable(method):
                print(f"✅ MeetingQuestionAdmin.{method_name} is callable")
            else:
                print(f"❌ MeetingQuestionAdmin.{method_name} is not callable")
                return False
        else:
            print(f"❌ MeetingQuestionAdmin.{method_name} does not exist")
            return False

    return True


def test_admin_fieldsets():
    """Test that admin fieldsets are properly configured"""
    print("\n🔍 Testing Admin Fieldsets...")

    admin_configs = [
        (MeetingAdmin, "Meeting"),
        (MeetingQuestionAdmin, "MeetingQuestion"),
        (QuestionTemplateAdmin, "QuestionTemplate"),
        (QuestionEffectivenessLogAdmin, "QuestionEffectivenessLog"),
        (ConversationFlowAdmin, "ConversationFlow"),
    ]

    for admin_class, model_name in admin_configs:
        try:
            fieldsets = getattr(admin_class, "fieldsets", None)
            if fieldsets:
                print(f"✅ {model_name}Admin has {len(fieldsets)} fieldsets configured")
                for i, (name, options) in enumerate(fieldsets):
                    fields_count = len(options.get("fields", []))
                    print(f"   - {name}: {fields_count} fields")
            else:
                print(f"⚠️  {model_name}Admin has no fieldsets (using default)")

        except Exception as e:
            print(f"❌ Error testing {model_name}Admin fieldsets: {e}")
            return False

    return True


def run_admin_tests():
    """Run all admin interface tests"""
    print("🚀 Starting Admin Interface Tests")
    print("=" * 50)

    test_results = {}

    tests = [
        ("Admin Registration", test_admin_registration),
        ("Admin List Displays", test_admin_list_displays),
        ("Admin Custom Methods", test_admin_methods),
        ("Admin Fieldsets", test_admin_fieldsets),
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
    print("\n" + "=" * 50)
    print("📊 ADMIN TEST SUMMARY")
    print("=" * 50)

    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)

    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")

    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All Admin Interface tests PASSED!")
        print("\n✨ Admin Features Available:")
        print("   • Enhanced Meeting admin with AI insights")
        print("   • Dynamic Question management interface")
        print("   • Question Template management")
        print("   • Question Effectiveness tracking")
        print("   • Conversation Flow monitoring")
        print("   • Visual indicators and action buttons")
    else:
        print(
            f"⚠️  {total - passed} tests failed. Please check the admin configuration."
        )

    return passed == total


if __name__ == "__main__":
    success = run_admin_tests()
    sys.exit(0 if success else 1)
