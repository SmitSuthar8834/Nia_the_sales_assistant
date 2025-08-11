#!/usr/bin/env python
"""
Test configuration for the NIA Sales Assistant test suite
"""
import os
import sys
from pathlib import Path

import django

# Setup Django environment for testing
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nia_sales_assistant.settings")

# Configure Django
django.setup()

# Test configuration settings
TEST_CONFIG = {
    "ai_service": {"test_directory": "tests/ai_service", "test_pattern": "test_*.py"},
    "meeting_service": {
        "test_directory": "tests/meeting_service",
        "test_pattern": "test_*.py",
    },
    "voice_service": {
        "test_directory": "tests/voice_service",
        "test_pattern": "test_*.py",
    },
    "users": {"test_directory": "tests/users", "test_pattern": "test_*.py"},
    "utils": {"test_directory": "tests/utils", "test_pattern": "test_*.py"},
}
