# NIA Sales Assistant

An AI-powered sales assistant built with Django that helps sales teams convert leads into opportunities using advanced conversation analysis and lead information extraction.

## 🚀 Features

- **AI-Powered Lead Extraction**: Uses Google Gemini AI to extract comprehensive lead information from sales conversations
- **Entity Recognition**: Automatically identifies emails, phone numbers, company names, and monetary amounts
- **Data Validation**: Comprehensive validation and cleaning of extracted lead data
- **Confidence Scoring**: Algorithmic scoring based on data completeness and quality
- **RESTful API**: Professional API endpoints with proper authentication and error handling
- **Multi-tenant Support**: User-based data isolation and management
- **Comprehensive Testing**: 21+ test cases covering all functionality

## 🛠 Technology Stack

- **Backend**: Django REST Framework
- **Database**: PostgreSQL
- **AI Integration**: Google Gemini AI (gemini-1.5-flash)
- **Authentication**: Django Session Authentication
- **Testing**: Django Test Framework with comprehensive coverage
- **Task Queue**: Celery with Redis (configured)

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

### Lead Extraction & Analysis

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ai/analyze/` | POST | Full conversation analysis with lead extraction |
| `/api/ai/extract-lead/` | POST | Extract lead information only |
| `/api/ai/extract-entities/` | POST | Extract entities (emails, phones, etc.) |
| `/api/ai/validate-lead/` | POST | Validate lead data structure |
| `/api/ai/test-connection/` | GET | Test Gemini AI connection |
| `/api/ai/history/` | GET | Get conversation analysis history |

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

### Run Tests

```bash
# Run all tests
python manage.py test ai_service

# Run specific test categories
python manage.py test ai_service.tests.DataValidatorTestCase
python manage.py test ai_service.tests.LeadExtractionAPITestCase
python manage.py test ai_service.tests.GeminiAIServiceTestCase

# Run with verbose output
python manage.py test ai_service -v 2
```

### Test Coverage

- **21 comprehensive test cases**
- **Data validation tests** (email, phone, data cleaning)
- **AI service tests** (extraction, scoring, completeness)
- **API endpoint tests** (all 6 endpoints)
- **Model tests** (database operations)
- **Accuracy tests** (sample conversation scenarios)

### Manual Testing

```bash
# Test core functionality without AI calls
python quick_functionality_test.py

# Test API endpoints
python test_api_endpoints.py

# Test lead extraction with real AI
python test_lead_extraction.py
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
├── ai_service/                    # AI processing and lead extraction
│   ├── models.py                 # ConversationAnalysis model
│   ├── services.py               # GeminiAIService, DataValidator
│   ├── views.py                  # API endpoints (6 endpoints)
│   ├── urls.py                   # URL routing
│   └── tests.py                  # Comprehensive test suite (21 tests)
├── users/                        # User management
│   ├── models.py                 # Custom User model
│   └── ...
├── nia_sales_assistant/          # Django project settings
│   ├── settings.py               # Project configuration
│   ├── urls.py                   # Main URL routing
│   └── ...
├── .kiro/                        # Kiro IDE specifications
├── manage.py                     # Django management script
├── requirements.txt              # Python dependencies
└── README.md                     # This file
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

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add comprehensive tests
5. Ensure all tests pass (`python manage.py test`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎯 Current Status

✅ **Task 2 Complete**: Lead information extraction fully implemented and tested  
🚀 **Production Ready**: Comprehensive testing and validation  
📊 **21/21 Tests Passing**: Full test coverage  
🔧 **Clean Architecture**: Django-only implementation  

Ready for the next development phase!