# Developer Onboarding Guide

Welcome to the NIA Sales Assistant project! This guide will help you get up and running quickly with the codebase.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Git
- Code editor (VS Code recommended)
- Basic Django knowledge

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd nia-sales-assistant

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env
```

Edit `.env` file for development (use SQLite):
```env
# Django Settings
SECRET_KEY=your-development-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,testserver

# Database Settings (SQLite for development)
# Leave DB_NAME empty to use SQLite
# DB_NAME=

# AI Settings (use test keys for development)
GEMINI_API_KEY=test-key-for-development
GEMINI_API_KEY_BACKUP=test-backup-key

# Redis Settings (optional for development)
REDIS_URL=redis://localhost:6379/0
```

### 3. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser account
python manage.py createsuperuser

# Load sample data (optional)
python manage.py loaddata fixtures/sample_data.json
```

### 4. Verify Installation

```bash
# Run system validation
python validation_test.py

# Start development server
python manage.py runserver

# Open browser to http://localhost:8000/admin/
```

## 📁 Project Structure Overview

```
nia_sales_assistant/
├── docs/                    # 📚 Documentation
│   ├── api/                # API specifications
│   ├── implementation/     # Feature documentation
│   ├── setup/             # Setup guides
│   └── ui_testing/        # UI testing specs
├── tests/                  # 🧪 Organized test suite
│   ├── ai_service/        # AI service tests
│   ├── meeting_service/   # Meeting tests
│   ├── voice_service/     # Voice tests
│   └── utils/             # Test utilities
├── scripts/               # 🔧 Utility scripts
├── ai_service/           # 🤖 AI & lead extraction
├── meeting_service/      # 📅 Meeting management
├── voice_service/        # 🎤 Voice processing
├── users/               # 👥 User management
├── admin_config/        # ⚙️ Admin interface
└── nia_sales_assistant/ # 🏠 Django settings
```

## 🧩 Service Architecture

### AI Service (`ai_service/`)
- **Purpose**: Conversation analysis and lead extraction
- **Key Files**:
  - `services.py`: GeminiAIService, DataValidator
  - `models.py`: ConversationAnalysis
  - `views.py`: API endpoints
  - `tests.py`: Comprehensive test suite

### Meeting Service (`meeting_service/`)
- **Purpose**: Meeting scheduling and intelligence
- **Key Files**:
  - `intelligent_meeting_service.py`: AI-powered features
  - `google_meet_service.py`: Google Meet integration
  - `microsoft_teams_service.py`: Teams integration
  - `models.py`: Meeting models

### Voice Service (`voice_service/`)
- **Purpose**: Voice processing and real-time communication
- **Key Files**:
  - `consumers.py`: WebSocket handlers
  - `services.py`: Voice processing
  - `models.py`: Voice session models

## 🛠 Development Workflow

### 1. Understanding Features
Before making changes, review:
- `docs/implementation/` - Feature documentation
- `docs/api/` - API specifications
- `docs/ui_testing/` - UI component details

### 2. Making Changes
1. Create feature branch: `git checkout -b feature/your-feature`
2. Follow Django best practices
3. Write tests for new functionality
4. Update documentation

### 3. Testing Your Changes
```bash
# Run all tests
python manage.py test

# Run specific service tests
python manage.py test ai_service
python manage.py test meeting_service

# Run validation tests
python validation_test.py

# Test specific functionality
python scripts/testing/test_specific_feature.py
```

### 4. Code Quality Guidelines
- Follow PEP 8 style guidelines
- Use meaningful variable names
- Add docstrings to functions and classes
- Keep functions focused and modular
- Write comprehensive tests

## 🧪 Testing Strategy

### Test Organization
- **Unit Tests**: Individual function testing
- **Integration Tests**: Service interaction testing
- **API Tests**: Endpoint functionality testing
- **UI Tests**: Interface component testing

### Running Tests
```bash
# All tests
python manage.py test

# Specific test categories
python manage.py test ai_service.tests.DataValidatorTestCase
python manage.py test meeting_service.tests.MeetingSessionTestCase

# With verbose output
python manage.py test -v 2

# Coverage report (if coverage installed)
coverage run --source='.' manage.py test
coverage report
```

## 🔧 Common Development Tasks

### Creating New Features
```bash
# Create new Django app
python manage.py startapp new_service

# Add to INSTALLED_APPS in settings.py
# Create models, views, URLs
# Write tests
# Update documentation
```

### Database Operations
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset database (development only)
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### API Development
```bash
# Test API endpoints
python scripts/testing/test_api_endpoints.py

# Generate API documentation
python manage.py generateschema --file openapi-schema.yml
```

## 🐛 Debugging Tips

### Common Issues
1. **Import Errors**: Check PYTHONPATH and Django app registration
2. **Database Errors**: Ensure migrations are applied
3. **API Key Errors**: Use test keys for development
4. **Permission Errors**: Check user authentication in tests

### Debugging Tools
```bash
# Django shell
python manage.py shell

# Database shell
python manage.py dbshell

# Check system configuration
python manage.py check

# View SQL queries
python manage.py shell
>>> from django.db import connection
>>> connection.queries
```

## 📚 Learning Resources

### Django Documentation
- [Django Official Docs](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Django Channels](https://channels.readthedocs.io/)

### Project-Specific Resources
- `docs/api/` - API documentation
- `docs/implementation/` - Feature guides
- `docs/ui_testing/` - UI specifications
- Test files - Examples of usage patterns

## 🤝 Getting Help

### Internal Resources
1. Check existing documentation in `docs/`
2. Review test files for usage examples
3. Look at similar implementations in other services

### Code Review Process
1. Create pull request with detailed description
2. Include test results and validation output
3. Update relevant documentation
4. Address review feedback promptly

## 🎯 Next Steps

After completing onboarding:
1. Review the codebase structure
2. Run all tests to ensure everything works
3. Try making a small change and testing it
4. Read through the UI testing documentation
5. Explore the admin interface
6. Start working on your assigned tasks

Welcome to the team! 🚀