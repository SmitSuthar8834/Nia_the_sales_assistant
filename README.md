# NIA Sales Assistant

An AI-powered sales assistant built with Django that helps sales teams convert leads into opportunities using advanced conversation analysis, lead information extraction, meeting management, and voice service capabilities.

## 🚀 Features

### Core AI Services
- **AI-Powered Lead Extraction**: Uses Google Gemini AI to extract comprehensive lead information from sales conversations
- **Entity Recognition**: Automatically identifies emails, phone numbers, company names, and monetary amounts
- **Data Validation**: Comprehensive validation and cleaning of extracted lead data
- **Confidence Scoring**: Algorithmic scoring based on data completeness and quality
- **Sales Recommendations**: AI-generated sales strategies and lead quality scoring

### Meeting Management
- **Intelligent Meeting Scheduling**: AI-powered meeting optimization and conflict detection
- **Multi-Platform Integration**: Google Meet and Microsoft Teams integration
- **Meeting Intelligence**: Pre-meeting preparation and post-meeting analysis
- **Live Meeting Support**: Real-time conversation guidance and suggestions
- **Meeting Outcomes**: Automated summary generation and action item extraction

### Voice Services
- **Real-time Voice Processing**: WebRTC-based voice communication
- **Speech-to-Text**: Conversation transcription and analysis
- **Voice Chat Integration**: Multi-session chat management with file uploads
- **Audio Processing**: Advanced audio handling and storage

### System Features
- **RESTful API**: Professional API endpoints with proper authentication and error handling
- **Multi-tenant Support**: User-based data isolation and management
- **Comprehensive Testing**: 170+ test cases covering all functionality
- **Clean Architecture**: Organized codebase following Django best practices
- **UI Testing Documentation**: Complete specifications for all interface elements

## 🛠 Technology Stack

- **Backend**: Django REST Framework
- **Database**: PostgreSQL (SQLite for development)
- **AI Integration**: Google Gemini AI (gemini-1.5-flash)
- **Authentication**: Django Session Authentication
- **Real-time Communication**: Django Channels with WebSocket support
- **Meeting Integration**: Google Meet API, Microsoft Teams API
- **Voice Processing**: WebRTC, Speech-to-Text APIs
- **Testing**: Django Test Framework with comprehensive coverage
- **Task Queue**: Celery with Redis
- **File Storage**: Django file handling with media storage

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL
- Redis (for Celery)
- Google Gemini AI API Key

## 🔧 Installation

### 1. Clone and Setup

```bash
git clone <repository-url>
cd nia-sales-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy and edit environment file
cp .env.example .env
```

Edit `.env` with your configuration:
```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,testserver

# Database Settings
DB_NAME=nia_sales_assistant
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# AI Settings
GEMINI_API_KEY=your-gemini-api-key

# Redis Settings
REDIS_URL=redis://localhost:6379/0
```

### 3. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 4. Run the Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/ai/`

## 📡 API Endpoints

### AI Service Endpoints (`/api/ai/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analyze/` | POST | Full conversation analysis with lead extraction |
| `/extract-lead/` | POST | Extract lead information only |
| `/extract-entities/` | POST | Extract entities (emails, phones, etc.) |
| `/validate-lead/` | POST | Validate lead data structure |
| `/recommendations/` | POST | Generate sales recommendations |
| `/lead-quality-score/` | POST | Calculate lead quality score |
| `/sales-strategy/` | POST | Generate sales strategy |
| `/industry-insights/` | POST | Get industry-specific insights |
| `/test-connection/` | GET | Test Gemini AI connection |
| `/history/` | GET | Get conversation analysis history |

### Meeting Service Endpoints (`/meeting/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dashboard/` | GET | Meeting dashboard data |
| `/api/unified/meetings/create/` | POST | Create unified meeting |
| `/api/unified/dashboard/` | GET | Unified meeting dashboard |
| `/api/intelligent/availability/` | POST | Analyze user availability |
| `/api/intelligent/recommend-time/` | POST | Recommend meeting times |
| `/api/intelligent/detect-conflicts/` | POST | Detect meeting conflicts |
| `/api/nia/schedule/` | POST | Schedule NIA meeting |
| `/api/nia/analytics/` | GET | Get meeting analytics |
| `/api/calendar/events/` | GET | Get calendar events |
| `/api/calendar/schedule-meeting/` | POST | Schedule meeting with lead |
| `/oauth/google/initiate/` | GET | Initiate Google OAuth |
| `/oauth/teams/initiate/` | GET | Initiate Teams OAuth |

### Voice Service Endpoints (`/api/voice/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/initiate/` | POST | Initiate voice call |
| `/webrtc/setup/` | POST | Setup WebRTC connection |
| `/end/` | POST | End voice call |
| `/process-audio/` | POST | Process audio data |
| `/generate-speech/` | POST | Generate speech from text |
| `/sessions/` | GET | Get user call sessions |
| `/session/{id}/status/` | GET | Get session status |
| `/session/{id}/summary/` | GET | Get conversation summary |
| `/chat/create/` | POST | Create chat session |
| `/chat/sessions/` | GET | Get chat sessions |
| `/chat/session/{id}/` | GET | Get specific chat session |
| `/chat/session/{id}/upload/` | POST | Upload file to chat |

### Admin Configuration Endpoints (`/admin-config/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/settings/` | GET/POST | System settings management |
| `/api/users/` | GET/POST | User management |
| `/api/templates/` | GET/POST | Template management |
| `/api/integrations/` | GET/POST | Integration settings |

### Example API Usage

#### Analyze Conversation
```python
import requests

response = requests.post('http://localhost:8000/api/ai/analyze/', {
    'conversation_text': '''
    Hi, this is Sarah Johnson from TechStart Inc. I'm the CTO here.
    We're having issues with manual data entry and need an automated solution.
    Our budget is around $100,000 and we need implementation by Q3.
    You can reach me at sarah@techstart.com or 555-987-6543.
    ''',
    'extract_entities': True,
    'generate_recommendations': True
}, headers={'Authorization': 'Session your-session'})

data = response.json()
print(f"Company: {data['lead_information']['company_name']}")
print(f"Contact: {data['lead_information']['contact_details']['name']}")
print(f"Confidence: {data['lead_information']['extraction_metadata']['confidence_score']}%")
```

#### Extract Entities Only
```python
response = requests.post('http://localhost:8000/api/ai/extract-entities/', {
    'text': 'Contact John Doe at john@example.com or call 555-123-4567. Budget is $50,000.'
})

entities = response.json()['entities']
print(f"Emails: {entities['emails']}")
print(f"Phones: {entities['phones']}")
print(f"Money: {entities['monetary_amounts']}")
```

## 🧪 Testing

### Automated Testing

```bash
# Run all tests
python manage.py test

# Run specific service tests
python manage.py test ai_service
python manage.py test meeting_service
python manage.py test voice_service
python manage.py test users

# Run specific test categories
python manage.py test ai_service.tests.DataValidatorTestCase
python manage.py test meeting_service.tests.MeetingSessionTestCase
python manage.py test voice_service.tests

# Run with verbose output
python manage.py test -v 2
```

### Test Coverage

- **170+ comprehensive test cases** across all services
- **AI Service Tests**: Data validation, lead extraction, entity recognition, API endpoints
- **Meeting Service Tests**: Meeting scheduling, intelligence, platform integration
- **Voice Service Tests**: Voice processing, WebSocket communication, chat management
- **User Management Tests**: Authentication, permissions, user workflows
- **Integration Tests**: End-to-end functionality testing

### UI Testing

The project includes comprehensive UI testing documentation in `docs/ui_testing/`:

#### Admin Interface Testing
- **Complete Admin Panel Coverage**: Every button, form field, and link documented
- **User Management Interface**: Create, edit, delete user workflows
- **Meeting Management Interface**: Meeting creation, scheduling, and management
- **AI Service Configuration**: AI settings and service management
- **System Configuration**: Admin settings and system preferences

#### Frontend Interface Testing
- **Login and Authentication**: Login forms, password reset, session management
- **Dashboard Interface**: Main dashboard elements and navigation
- **Meeting Interface**: Meeting creation, joining, and management UI
- **Voice Service Interface**: Voice call initiation and management
- **Responsive Design**: Mobile and desktop interface testing

#### API Integration Testing
- **REST API Endpoints**: All API endpoints with expected responses
- **WebSocket Connections**: Real-time features and live updates
- **Error Handling**: Error states and user feedback
- **Loading States**: Progress indicators and loading animations

#### Interactive Element Testing
- **Form Validation**: All form fields with validation rules and error messages
- **Button States**: Hover, disabled, and loading states for all buttons
- **Modal Dialogs**: Popup behaviors and modal interactions
- **Navigation Elements**: Menu items, breadcrumbs, and routing

### UI Testing Procedures

```bash
# Access UI testing documentation
cd docs/ui_testing/

# Review testing checklists
cat systematic_testing_checklists.md

# Check component specifications
cat ui_component_test_templates.md

# Review user workflows
cat user_workflow_testing.md
```

### Manual Testing Scripts

```bash
# Test core functionality
python validation_test.py

# Test specific services
python scripts/testing/test_ai_service.py
python scripts/testing/test_meeting_service.py
python scripts/testing/test_voice_service.py
```

## 📊 Data Structure

### Lead Information Structure
```json
{
  "company_name": "TechStart Inc",
  "contact_details": {
    "name": "Sarah Johnson",
    "email": "sarah@techstart.com",
    "phone": "555-987-6643",
    "title": "CTO",
    "department": "Technology"
  },
  "pain_points": ["Manual data entry", "System integration issues"],
  "requirements": ["Automated workflow", "API integration"],
  "budget_info": "$100,000 - $150,000",
  "timeline": "Implementation by Q3 2024",
  "decision_makers": ["Sarah Johnson", "Mike Chen (CEO)"],
  "industry": "Software Development",
  "company_size": "50-100 employees",
  "urgency_level": "high",
  "current_solution": "Excel spreadsheets",
  "competitors_mentioned": ["Salesforce", "HubSpot"],
  "extraction_metadata": {
    "confidence_score": 85.0,
    "data_completeness": 70.0,
    "extraction_method": "gemini_ai_enhanced"
  }
}
```

## 🏗 Project Structure

```
nia_sales_assistant/
├── docs/                         # 📚 All project documentation
│   ├── api/                     # API documentation and specifications
│   ├── implementation/          # Implementation summaries and guides
│   ├── setup/                   # Setup and deployment documentation
│   └── ui_testing/              # Complete UI testing specifications
│       ├── admin_interface_testing.md
│       ├── frontend_interface_testing.md
│       ├── api_endpoint_ui_integration.md
│       ├── interactive_element_specifications.md
│       ├── systematic_testing_checklists.md
│       ├── ui_component_test_templates.md
│       └── user_workflow_testing.md
├── tests/                        # 🧪 Organized test suite
│   ├── ai_service/              # AI service tests
│   ├── meeting_service/         # Meeting service tests
│   ├── voice_service/           # Voice service tests
│   ├── users/                   # User management tests
│   └── utils/                   # Test utilities and helpers
├── scripts/                      # 🔧 Utility scripts
│   ├── testing/                 # Testing scripts
│   ├── debugging/               # Debug utilities
│   └── deployment/              # Deployment scripts
├── ai_service/                   # 🤖 AI processing and lead extraction
│   ├── models.py                # ConversationAnalysis model
│   ├── services.py              # GeminiAIService, DataValidator
│   ├── views.py                 # API endpoints
│   ├── urls.py                  # URL routing
│   └── tests.py                 # AI service tests
├── meeting_service/              # 📅 Meeting management and intelligence
│   ├── models.py                # Meeting models
│   ├── services.py              # Meeting services
│   ├── intelligent_meeting_service.py  # AI-powered meeting features
│   ├── google_meet_service.py   # Google Meet integration
│   ├── microsoft_teams_service.py  # Teams integration
│   ├── views.py                 # Meeting API endpoints
│   └── tests.py                 # Meeting service tests
├── voice_service/                # 🎤 Voice processing and communication
│   ├── models.py                # Voice session models
│   ├── services.py              # Voice processing services
│   ├── consumers.py             # WebSocket consumers
│   ├── views.py                 # Voice API endpoints
│   └── tests.py                 # Voice service tests
├── users/                        # 👥 User management
│   ├── models.py                # Custom User model
│   └── tests.py                 # User tests
├── admin_config/                 # ⚙️ Administrative configuration
│   ├── models.py                # Admin configuration models
│   ├── views.py                 # Admin interface views
│   └── tests.py                 # Admin tests
├── nia_sales_assistant/          # 🏠 Django project settings
│   ├── settings.py              # Project configuration
│   ├── urls.py                  # Main URL routing
│   ├── asgi.py                  # ASGI configuration for WebSockets
│   └── wsgi.py                  # WSGI configuration
├── static/                       # 🎨 Static files (CSS, JS, images)
├── templates/                    # 📄 HTML templates
├── media/                        # 📁 User uploaded files
├── .kiro/                        # 🔧 Kiro IDE specifications
├── manage.py                     # Django management script
├── requirements.txt              # Python dependencies
├── docker-compose.yml            # Docker configuration
└── README.md                     # This documentation
```

## 🔒 Security Features

- **Authentication Required**: All endpoints require user authentication
- **Input Validation**: Comprehensive input sanitization and validation
- **Data Validation**: Email/phone format validation with regex
- **Error Handling**: Secure error messages without data leakage
- **SQL Injection Protection**: Django ORM provides built-in protection

## 🚀 Production Deployment

### Environment Setup
```bash
# Production settings
DEBUG=False
ALLOWED_HOSTS=your-domain.com
SECRET_KEY=your-production-secret-key

# Use production database
DB_HOST=your-production-db-host
DB_PASSWORD=your-secure-password

# Use production Redis
REDIS_URL=redis://your-production-redis:6379/0
```

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d
```

## 📈 Performance & Monitoring

- **Response Time**: Fast response for validation/entity extraction
- **Error Handling**: Graceful fallbacks for AI failures
- **Data Persistence**: Efficient PostgreSQL storage
- **Logging**: Comprehensive logging for debugging and monitoring

## 👨‍💻 Developer Onboarding Guide

### Quick Start for New Developers

1. **Environment Setup**
   ```bash
   # Clone repository
   git clone <repository-url>
   cd nia-sales-assistant
   
   # Setup virtual environment
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Configuration**
   ```bash
   # Copy environment file
   cp .env.example .env
   
   # Edit .env with your settings (use SQLite for development)
   # Remove DB_NAME to use SQLite instead of PostgreSQL
   ```

3. **Database Setup**
   ```bash
   # Run migrations
   python manage.py migrate
   
   # Create superuser
   python manage.py createsuperuser
   
   # Load sample data (optional)
   python manage.py loaddata fixtures/sample_data.json
   ```

4. **Verify Installation**
   ```bash
   # Run validation tests
   python validation_test.py
   
   # Start development server
   python manage.py runserver
   
   # Access admin interface
   # http://localhost:8000/admin/
   ```

### Development Workflow

1. **Understanding the Codebase**
   - Review `docs/implementation/` for feature documentation
   - Check `docs/api/` for API specifications
   - Read `docs/ui_testing/` for UI component details

2. **Making Changes**
   - Follow Django best practices
   - Write tests for new functionality
   - Update documentation as needed
   - Use the organized project structure

3. **Testing Your Changes**
   ```bash
   # Run relevant tests
   python manage.py test ai_service
   python manage.py test meeting_service
   python manage.py test voice_service
   
   # Run UI validation
   python validation_test.py
   
   # Test specific functionality
   python scripts/testing/test_specific_feature.py
   ```

4. **Code Quality**
   - Follow PEP 8 style guidelines
   - Use meaningful variable and function names
   - Add docstrings to functions and classes
   - Keep functions focused and modular

### Project Architecture Understanding

- **AI Service**: Handles conversation analysis and lead extraction
- **Meeting Service**: Manages meeting scheduling and intelligence
- **Voice Service**: Processes voice communication and chat
- **Admin Config**: Provides administrative interfaces
- **Users**: Manages user authentication and permissions

### Common Development Tasks

```bash
# Create new Django app
python manage.py startapp new_service

# Create migrations
python manage.py makemigrations

# Run specific tests
python manage.py test app_name.tests.TestClassName

# Collect static files
python manage.py collectstatic

# Create superuser
python manage.py createsuperuser
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow the developer onboarding guide above
4. Make your changes following project conventions
5. Add comprehensive tests for new functionality
6. Update relevant documentation
7. Ensure all tests pass (`python manage.py test`)
8. Run validation tests (`python validation_test.py`)
9. Commit your changes (`git commit -m 'Add amazing feature'`)
10. Push to the branch (`git push origin feature/amazing-feature`)
11. Open a Pull Request with detailed description

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎯 Current Status

✅ **Codebase Cleanup Complete**: Organized project structure with clean architecture  
✅ **AI Services**: Lead extraction, entity recognition, and sales recommendations  
✅ **Meeting Management**: Intelligent scheduling with Google Meet/Teams integration  
✅ **Voice Services**: Real-time voice processing and chat management  
✅ **Comprehensive Testing**: 170+ tests across all services  
✅ **UI Testing Documentation**: Complete specifications for all interface elements  
✅ **Developer Ready**: Full onboarding guide and documentation  

🚀 **Production Ready**: Clean, tested, and well-documented codebase ready for deployment!