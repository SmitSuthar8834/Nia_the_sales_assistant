#!/usr/bin/env python
"""
Test utilities and helper functions for the NIA Sales Assistant test suite
"""
import os
import sys
from pathlib import Path

import django

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nia_sales_assistant.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

User = get_user_model()


class BaseTestHelper:
    """Base class for test helpers with common functionality"""

    @staticmethod
    def setup_django():
        """Ensure Django is properly configured for testing"""
        if not django.conf.settings.configured:
            django.setup()

    @staticmethod
    def create_test_user(
        username="testuser", email="test@example.com", password="testpass123"
    ):
        """Create a test user for testing purposes"""
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "first_name": "Test", "last_name": "User"},
        )
        if created:
            user.set_password(password)
            user.save()
        return user

    @staticmethod
    def get_authenticated_client(user=None):
        """Get an authenticated API client for testing"""
        if user is None:
            user = BaseTestHelper.create_test_user()

        client = APIClient()
        client.force_authenticate(user=user)
        return client

    @staticmethod
    def print_test_header(test_name):
        """Print a formatted test header"""
        print(f"\n🧪 {test_name}")
        print("=" * (len(test_name) + 3))

    @staticmethod
    def print_test_result(test_name, success, message=""):
        """Print formatted test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")


class AIServiceTestHelper(BaseTestHelper):
    """Helper functions specific to AI service testing"""

    @staticmethod
    def create_test_lead(user=None):
        """Create a test lead for AI service testing"""
        from ai_service.models import Lead

        if user is None:
            user = BaseTestHelper.create_test_user()

        lead = Lead.objects.create(
            name="Test Lead",
            email="testlead@example.com",
            phone="123-456-7890",
            company="Test Company",
            created_by=user,
        )
        return lead


class MeetingServiceTestHelper(BaseTestHelper):
    """Helper functions specific to meeting service testing"""

    @staticmethod
    def create_test_meeting(user=None, title="Test Meeting"):
        """Create a test meeting for meeting service testing"""
        from meeting_service.models import Meeting

        if user is None:
            user = BaseTestHelper.create_test_user()

        meeting = Meeting.objects.create(
            title=title,
            description="Test meeting description",
            scheduled_time=timezone.now() + timezone.timedelta(hours=1),
            created_by=user,
        )
        return meeting


class VoiceServiceTestHelper(BaseTestHelper):
    """Helper functions specific to voice service testing"""

    @staticmethod
    def create_test_call_session(user=None):
        """Create a test call session for voice service testing"""
        from voice_service.models import CallSession

        if user is None:
            user = BaseTestHelper.create_test_user()

        session = CallSession.objects.create(
            user=user, session_id="test_session_123", status="active"
        )
        return session


def run_test_with_error_handling(test_function, test_name):
    """Run a test function with proper error handling and reporting"""
    try:
        BaseTestHelper.print_test_header(test_name)
        result = test_function()
        BaseTestHelper.print_test_result(test_name, True, "Test completed successfully")
        return result
    except Exception as e:
        BaseTestHelper.print_test_result(test_name, False, f"Error: {str(e)}")
        import traceback

        print(f"   Traceback: {traceback.format_exc()}")
        return None
