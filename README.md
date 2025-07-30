# NIA - Neural Intelligence Assistant

NIA is an AI-powered sales assistant that helps sales teams manage leads and opportunities through natural conversation analysis. The system integrates with multiple CRM platforms and uses Google's Gemini AI to provide intelligent suggestions for lead conversion and sales best practices.

## 🚀 Features

- **AI-Powered Conversation Analysis**: Analyze sales conversations and extract structured lead information
- **Intelligent Recommendations**: Get AI-generated sales strategies and next steps
- **CRM Integration**: Support for Creatio and SAP C4C (planned)
- **Lead Management**: Unified interface for managing leads across multiple CRM systems
- **Voice Processing**: Handle voice calls and convert speech to actionable insights (planned)

## 🛠️ Technology Stack

- **Backend**: Django 5.2.4 with Django REST Framework
- **Database**: PostgreSQL with Redis for caching
- **AI**: Google Gemini AI for conversation analysis
- **Message Queue**: Celery with Redis
- **Containerization**: Docker & Docker Compose

## 📋 Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Google Gemini AI API Key

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/SmitSuthar8834/Nia_the_sales_assistant.git
cd Nia_the_sales_assistant
```

### 2. Set Up Environment

Create a `.env` file in the root directory:

```env
# Django Settings
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,testserver

# Database Settings (PostgreSQL)
DB_NAME=nia_sales_assistant
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# Gemini AI Settings
GEMINI_API_KEY=your-gemini-api-key-here

# Redis Settings (for Celery)
REDIS_URL=redis://localhost:6380/0
```

### 3. Start Services

Start PostgreSQL and Redis using Docker:

```bash
docker-compose up -d
```

### 4. Install Dependencies

```bash
pip install django djangorestframework google-generativeai python-decouple psycopg2-binary redis celery
```

### 5. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Start Development Server

```bash
python manage.py runserver
```

## 🧪 Testing

### Test Gemini AI Integration

```bash
python test_gemini.py
```

### Test API Endpoints

```bash
python simple_test.py
```

### Manual API Testing

Test the conversation analysis endpoint:

```bash
curl -u admin:admin -X POST http://127.0.0.1:8000/api/ai/analyze/ \
  -H "Content-Type: application/json" \
  -d '{"conversation_text": "Sales Rep: Hello! Customer: Hi, I am John from ABC Corp. We need a CRM system for our 100-person company."}'
```

## 📚 API Endpoints

- `GET /api/ai/test-connection/` - Test Gemini AI connectivity
- `POST /api/ai/analyze/` - Analyze conversation and extract lead information
- `GET /api/ai/history/` - Get conversation analysis history

## 🏗️ Project Structure

```
nia_sales_assistant/
├── ai_service/          # AI analysis service
├── users/               # User management
├── nia_sales_assistant/ # Django project settings
├── .kiro/              # Kiro IDE specifications
├── docker-compose.yml  # Docker services
├── manage.py           # Django management
└── requirements.txt    # Python dependencies
```

## 🔮 Roadmap

### Phase 1: Core AI Analysis Engine ✅
- [x] Basic Django project setup
- [x] Gemini AI integration
- [x] Lead information extraction
- [x] AI-powered recommendations

### Phase 2: Lead Management (In Progress)
- [ ] Lead model with AI insights
- [ ] Frontend interface
- [ ] Lead scoring and prioritization

### Phase 3: Voice Processing
- [ ] Voice call handling
- [ ] Speech-to-text integration
- [ ] Real-time conversation analysis

### Phase 4: CRM Integration
- [ ] Creatio CRM integration
- [ ] SAP C4C integration
- [ ] Unified CRM management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Gemini AI for powerful conversation analysis
- Django community for the excellent framework
- All contributors who help make NIA better

## 📞 Support

For support, email [your-email@example.com] or create an issue on GitHub.

---

**NIA - Making Sales Smarter with AI** 🤖✨