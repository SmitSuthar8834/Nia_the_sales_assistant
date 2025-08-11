#!/usr/bin/env python3
"""
Simple test to check if the generate_meeting_guidance method exists
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


def test_method_exists():
    """Test if the generate_meeting_guidance method exists"""
    try:
        from meeting_service.live_meeting_support import LiveMeetingSupportService

        service = LiveMeetingSupportService()

        # Check if method exists
        if hasattr(service, "generate_meeting_guidance"):
            print("✅ generate_meeting_guidance method exists")

            # Check if it's callable
            if callable(getattr(service, "generate_meeting_guidance")):
                print("✅ generate_meeting_guidance method is callable")
            else:
                print("❌ generate_meeting_guidance method is not callable")
        else:
            print("❌ generate_meeting_guidance method does not exist")

        # List all methods
        print("\nAll methods in LiveMeetingSupportService:")
        for attr_name in dir(service):
            if not attr_name.startswith("_") and callable(getattr(service, attr_name)):
                print(f"  - {attr_name}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_method_exists()
