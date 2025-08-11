# Test Structure Guide

## Overview

The NIA Sales Assistant test suite has been reorganized into a structured directory layout that groups tests by Django application and functionality. This guide explains how to run and maintain tests in the new structure.

## Directory Structure

```
tests/
├── __init__.py
├── conftest.py                    # Test configuration
├── ai_service/                    # AI service tests
│   ├── __init__.py
│   ├── test_ai_api.py
│   ├── test_ai_guidance_structure.py
│   ├── test_ai_meeting_guidance.py
│   ├── test_ai_question_generation.py
│   ├── test_api_recommendations.py
│   ├── test_gemini_api_integration.py
│   ├── test_lead_extraction.py
│   ├── test_opportunity_conversion_api.py
│   ├── test_opportunity_conversion_functionality.py
│   ├── test_pattern_extraction.py
│   └── test_recommendations_functionality.py
├── meeting_service/               # Meeting service tests
│   ├── __init__.py
│   ├── test_calendar_integration.py
│   ├── test_conversation.py
│   ├── test_dynamic_question_flow.py
│   ├── test_live_meeting_support.py
│   ├── test_meeting_admin.py
│   ├── test_meeting_admin_comprehensive.py
│   ├── test_meeting_admin_implementation.py
│   ├── test_meeting_dashboard.py
│   ├── test_meeting_outcome_logic.py
│   ├── test_meeting_outcome_tracking.py
│   ├── test_pre_meeting_intelligence.py
│   ├── test_question_admin_interface.py
│   ├── test_simple_pre_meeting.py
│   └── test_video_platform_integration.py
├── voice_service/                 # Voice service tests
│   ├── __init__.py
│   ├── test_voice_processing_task7.py
│   └── test_voice_service.py
├── users/                         # User-related tests
│   ├── __init__.py
│   ├── test_create_lead_issue.py
│   └── test_enhanced_lead_interface.py
└── utils/                         # Utility and general tests
    ├── __init__.py
    ├── test_admin_interface.py
    ├── test_dashboard_validation.py
    ├── test_frontend_api.py
    ├── test_frontend_interface.py
    ├── test_helper_functions_standalone.py
    ├── test_helpers.py            # Test utility functions
    └── test_method_exists.py
```

## Running Tests

### Using the Test Runner

A test runner script (`run_tests.py`) is provided in the `scripts/testing/` directory for easy test execution:

```bash
# List all available tests
python scripts/testing/run_tests.py list

# Run all tests
python scripts/testing/run_tests.py all

# Run tests for specific components
python scripts/testing/run_tests.py ai            # AI service tests
python scripts/testing/run_tests.py meeting       # Meeting service tests
python scripts/testing/run_tests.py voice         # Voice service tests
python scripts/testing/run_tests.py users         # User tests
python scripts/testing/run_tests.py utils         # Utility tests
```

### Running Individual Tests

You can run individual test files directly:

```bash
# Run a specific test file
python tests/ai_service/test_ai_api.py
python tests/meeting_service/test_meeting_admin.py
python tests/voice_service/test_voice_service.py
```

### Running Tests by Directory

You can also run all tests in a specific directory:

```bash
# Run all AI service tests
python -m pytest tests/ai_service/

# Run all meeting service tests  
python -m pytest tests/meeting_service/
```

## Test Categories

### AI Service Tests (tests/ai_service/)
- **test_ai_api.py**: Basic AI API connectivity and functionality
- **test_gemini_api_integration.py**: Gemini AI integration tests
- **test_lead_extraction.py**: Lead extraction and processing
- **test_recommendations_functionality.py**: AI recommendation system
- **test_opportunity_conversion_*.py**: Opportunity conversion intelligence

### Meeting Service Tests (tests/meeting_service/)
- **test_meeting_admin*.py**: Admin interface functionality
- **test_calendar_integration.py**: Calendar system integration
- **test_live_meeting_support.py**: Real-time meeting features
- **test_pre_meeting_intelligence.py**: Pre-meeting preparation
- **test_video_platform_integration.py**: Video platform connectivity

### Voice Service Tests (tests/voice_service/)
- **test_voice_service.py**: Core voice processing functionality
- **test_voice_processing_task7.py**: Advanced voice processing features

### User Tests (tests/users/)
- **test_create_lead_issue.py**: Lead creation and management
- **test_enhanced_lead_interface.py**: Enhanced user interface features

### Utility Tests (tests/utils/)
- **test_admin_interface.py**: General admin interface testing
- **test_frontend_*.py**: Frontend interface validation
- **test_helpers.py**: Test utility functions and helpers

## Test Utilities

The `tests/utils/test_helpers.py` file provides common testing utilities:

### BaseTestHelper
- `setup_django()`: Ensure Django is properly configured
- `create_test_user()`: Create test users
- `get_authenticated_client()`: Get authenticated API clients
- `print_test_header()`: Format test output
- `print_test_result()`: Display test results

### Component-Specific Helpers
- **AIServiceTestHelper**: AI service test utilities
- **MeetingServiceTestHelper**: Meeting service test utilities  
- **VoiceServiceTestHelper**: Voice service test utilities

### Usage Example

```python
from tests.utils.test_helpers import BaseTestHelper, AIServiceTestHelper

# Create test user
user = BaseTestHelper.create_test_user()

# Create test lead
lead = AIServiceTestHelper.create_test_lead(user)

# Run test with error handling
result = run_test_with_error_handling(my_test_function, "My Test")
```

## Adding New Tests

When adding new tests:

1. **Choose the appropriate directory** based on the Django app being tested
2. **Follow the naming convention**: `test_*.py`
3. **Include proper imports** and path setup:

```python
#!/usr/bin/env python
"""
Test description
"""
import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nia_sales_assistant.settings')
django.setup()

# Your test imports here
```

4. **Use test helpers** when appropriate to reduce code duplication

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Ensure the path setup is correct in your test file
2. **Django not configured**: Make sure `django.setup()` is called before importing Django models
3. **Database issues**: Tests use the same database as development; consider using test database settings

### Path Issues

If you encounter import issues, verify that your test file includes:

```python
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))
```

The path should go up three levels: `tests/component/test_file.py` → project root.

## Migration from Old Structure

The tests were previously located in the project root directory. They have been moved to:

- Root `test_*.py` files → Appropriate `tests/component/` directories
- Import paths updated to work with new structure
- Test runner created for easy execution
- Test utilities consolidated in `tests/utils/test_helpers.py`

All existing functionality has been preserved while improving organization and maintainability.