# Design Document

## Overview

The codebase cleanup design focuses on reorganizing the NIA Sales Assistant project structure to follow Django best practices, improve maintainability, and reduce clutter. The cleanup will be performed systematically to ensure no functionality is lost while significantly improving code organization.

## Architecture

### Current Structure Issues
- 40+ files in project root directory
- Test files scattered throughout the project
- Documentation files mixed with code
- Temporary and debug files committed to repository
- Inconsistent naming conventions

### Target Structure
```
nia_sales_assistant/
├── docs/                          # All documentation
│   ├── api/                       # API documentation
│   ├── implementation/            # Implementation summaries
│   └── setup/                     # Setup and deployment guides
├── tests/                         # All test files
│   ├── ai_service/               # AI service tests
│   ├── meeting_service/          # Meeting service tests
│   ├── voice_service/            # Voice service tests
│   ├── users/                    # User tests
│   └── utils/                    # Test utilities
├── scripts/                      # Utility scripts
├── config/                       # Configuration files
├── [Django apps remain as-is]
├── manage.py
├── requirements.txt
├── README.md
├── .env.example
└── docker-compose.yml
```

## Components and Interfaces

### 1. File Organization Component
**Purpose:** Systematically move and organize files into appropriate directories

**Key Operations:**
- Create new directory structure
- Move documentation files to docs/
- Move test files to tests/
- Move utility scripts to scripts/
- Remove temporary/debug files

### 2. Documentation Consolidation Component
**Purpose:** Merge and organize documentation for better accessibility

**Key Operations:**
- Consolidate implementation summaries
- Create comprehensive API documentation
- Organize setup and deployment guides
- Create navigation index

### 3. Test Organization Component
**Purpose:** Restructure test files for better maintainability

**Key Operations:**
- Group tests by Django application
- Create test utilities module
- Standardize test naming conventions
- Create test runner configurations

### 4. Code Optimization Component
**Purpose:** Clean up Python code for better quality

**Key Operations:**
- Remove unused imports
- Fix code formatting inconsistencies
- Optimize database queries where needed
- Remove dead code

## Data Models

### File Mapping Structure
```python
FILE_MOVES = {
    'documentation': {
        'source_pattern': '*.md',
        'destination': 'docs/',
        'exclude': ['README.md']
    },
    'tests': {
        'source_pattern': 'test_*.py',
        'destination': 'tests/',
        'organize_by': 'component'
    },
    'scripts': {
        'source_pattern': ['debug_*.py', 'run_*.py', 'restart_*.py'],
        'destination': 'scripts/'
    }
}
```

### Cleanup Configuration
```python
CLEANUP_CONFIG = {
    'remove_files': [
        'debug_*.py',
        'simple_test.py',
        'quick_functionality_test.py'
    ],
    'preserve_files': [
        'manage.py',
        'requirements.txt',
        'README.md',
        '.env.example',
        'docker-compose.yml'
    ]
}
```

## Error Handling

### File Operation Errors
- **Missing Files:** Log warnings for files that cannot be found
- **Permission Errors:** Provide clear error messages for file access issues
- **Dependency Conflicts:** Check for import dependencies before moving files

### Backup Strategy
- Create backup of current structure before cleanup
- Implement rollback mechanism for critical errors
- Validate functionality after each cleanup phase

## Testing Strategy

### Pre-Cleanup Validation
1. Run all existing tests to establish baseline
2. Document current test coverage
3. Identify critical functionality dependencies

### Post-Cleanup Validation
1. Verify all tests still pass after reorganization
2. Check that all imports resolve correctly
3. Validate that Django applications start properly
4. Test API endpoints functionality

### Cleanup Testing Phases
1. **Phase 1:** Documentation organization (low risk)
2. **Phase 2:** Test file organization (medium risk)
3. **Phase 3:** Script and utility organization (medium risk)
4. **Phase 4:** Code optimization (high risk - requires thorough testing)

## Implementation Phases

### Phase 1: Documentation Cleanup (Safe)
- Create docs/ directory structure
- Move all .md files except README.md
- Consolidate implementation summaries
- Create documentation index

### Phase 2: Test Organization (Medium Risk)
- Create tests/ directory structure
- Move all test_*.py files
- Update import paths in test files
- Create test configuration files

### Phase 3: Script Organization (Medium Risk)
- Create scripts/ directory
- Move utility and debug scripts
- Update any references to moved scripts
- Clean up temporary files

### Phase 4: Code Optimization (High Risk)
- Remove unused imports across all Python files
- Fix formatting inconsistencies
- Optimize database queries
- Remove dead code and commented sections

## UI Testing Documentation Structure

### Admin Interface Components
```
admin_ui_specs/
├── dashboard/
│   ├── buttons.md              # Every button with click actions
│   ├── navigation.md           # Menu items and routing
│   └── widgets.md              # Dashboard widgets behavior
├── forms/
│   ├── user_forms.md           # User creation/edit forms
│   ├── meeting_forms.md        # Meeting management forms
│   └── ai_service_forms.md     # AI service configuration forms
└── api_endpoints/
    ├── rest_api.md             # All REST endpoints with UI integration
    └── websocket.md            # Real-time features testing
```

### Frontend Interface Components
```
frontend_ui_specs/
├── pages/
│   ├── login.md                # Login page elements
│   ├── dashboard.md            # Main dashboard UI
│   ├── meetings.md             # Meeting interface
│   └── voice_service.md        # Voice service UI
├── components/
│   ├── buttons.md              # All button types and states
│   ├── forms.md                # Form components and validation
│   └── modals.md               # Modal dialogs and popups
└── interactions/
    ├── click_actions.md        # All clickable elements
    ├── form_submissions.md     # Form submission behaviors
    └── real_time_updates.md    # Live updates and notifications
```

## Success Metrics

### Quantitative Metrics
- Reduce root directory files from 40+ to <10
- Organize 20+ test files into structured directories
- Consolidate 15+ documentation files
- Remove 10+ temporary/debug files
- Document 100+ UI elements with expected behaviors
- Create test specifications for 50+ interactive components

### Qualitative Metrics
- Improved developer onboarding experience
- Easier navigation of project structure
- Better separation of concerns
- Cleaner git history going forward
- Comprehensive UI testing coverage
- Clear documentation for every user interaction

## Risk Mitigation

### High-Risk Operations
- Moving files with complex import dependencies
- Removing files that might be referenced elsewhere
- Modifying core Django application structure

### Mitigation Strategies
- Create comprehensive backup before starting
- Implement changes in small, testable increments
- Validate functionality after each phase
- Maintain detailed log of all changes made