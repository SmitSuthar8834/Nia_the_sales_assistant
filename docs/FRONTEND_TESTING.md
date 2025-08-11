# NIA Sales Assistant - Frontend Testing Guide

This guide provides comprehensive instructions for testing the NIA Sales Assistant frontend interface.

## 🚀 Quick Start

### 1. Start the Django Server
```bash
python manage.py runserver
```

### 2. Run Automated Tests
```bash
# Run all tests
python scripts/testing/run_frontend_tests.py

# Or run individual test scripts
python test_ai_api.py           # Test AI backend
python test_frontend_api.py     # Test API endpoints
python test_frontend_interface.py  # Test complete interface
```

### 3. Manual Testing
- Open browser to: http://127.0.0.1:8000
- Or open: `test_frontend_manual.html` for interactive testing

## 📋 Test Coverage

### ✅ Automated Tests

**AI Backend Tests (`test_ai_api.py`)**
- Gemini AI connection
- Lead information extraction
- AI recommendations generation
- Data validation and processing

**API Endpoint Tests (`test_frontend_api.py`)**
- Server connectivity
- Debug endpoints
- Conversation analysis API
- Lead management CRUD
- AI recommendations API
- Analytics endpoints

**Frontend Interface Tests (`test_frontend_interface.py`)**
- Page loading and rendering
- Static file accessibility
- JavaScript functionality
- Complete workflow testing

### 🖱️ Manual Tests

**Interface Navigation**
- [ ] Main page loads correctly
- [ ] Navigation between tabs works
- [ ] Responsive design on different screen sizes

**Lead Creation Workflow**
- [ ] Create Lead form displays properly
- [ ] Conversation text input works
- [ ] AI analysis processes and displays results
- [ ] Lead creation completes successfully

**Lead Management**
- [ ] Lead list displays with scores
- [ ] Lead detail view shows complete information
- [ ] AI insights section renders properly
- [ ] Action buttons are functional

**Analytics Dashboard**
- [ ] Statistics display correctly
- [ ] Data updates in real-time

## 🧪 Test Data

### Sample Conversation for Testing
```
Sales Rep (Sarah): Good afternoon, Mr. Rodriguez. Thank you for taking the time to meet with me today. I understand from our initial conversation that DataFlow Solutions is experiencing some challenges with your current customer management processes?

Prospect (Miguel Rodriguez - VP of Operations): That's right, Sarah. We're a mid-market logistics company with about 350 employees across five locations. Honestly, we're drowning in spreadsheets and our team is using three different systems that don't talk to each other. But before we go further, I need to be upfront—we just implemented a new ERP system six months ago, and there's some... let's call it "change fatigue" in the organization.

Miguel: Well, our customer retention has dropped 12% over the past year. Our account managers are spending 60% of their time on administrative tasks instead of actually managing relationships. And here's the kicker—last month we lost a $2.3 million contract because three different team members contacted the same client with conflicting information. The client felt we were disorganized and unprofessional.
```

### Expected AI Analysis Results
- **Company**: DataFlow Solutions
- **Contact**: Miguel Rodriguez (VP of Operations)
- **Industry**: Logistics
- **Company Size**: 350 employees across 5 locations
- **Pain Points**: Customer retention drop, admin burden, lost contract
- **Requirements**: Unified customer data, ERP integration
- **Quality Score**: 80+ (high confidence)

## 🔧 Troubleshooting

### Common Issues

**Server Not Starting**
```bash
# Check if port 8000 is in use
netstat -an | findstr :8000

# Try different port
python manage.py runserver 8001
```

**API Endpoints Failing**
- Verify Gemini API key in `.env` file
- Check database migrations: `python manage.py migrate`
- Ensure authentication is disabled for testing

**Frontend Not Loading**
- Check static files configuration in `settings.py`
- Verify template directory is configured
- Clear browser cache

**AI Analysis Returns Empty Results**
- Verify Gemini API key is valid
- Check internet connection
- Review API quota limits

### Debug Mode

Enable debug logging by adding to Django settings:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'ai_service': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## 📊 Test Results Interpretation

### Success Criteria
- ✅ All automated tests pass (100% success rate)
- ✅ Manual interface testing completes without errors
- ✅ AI analysis produces accurate results
- ✅ Lead creation workflow functions end-to-end

### Performance Benchmarks
- Page load time: < 2 seconds
- AI analysis time: < 30 seconds
- API response time: < 5 seconds
- Lead creation: < 10 seconds

## 🎯 Test Scenarios

### Scenario 1: New User Experience
1. Open application for first time
2. Navigate through all sections
3. Create first lead with conversation analysis
4. Verify results and recommendations

### Scenario 2: Complex Sales Conversation
1. Use multi-stakeholder conversation
2. Verify extraction of multiple decision makers
3. Check comprehensive pain points identification
4. Validate detailed requirements analysis

### Scenario 3: Lead Management Workflow
1. Create multiple leads
2. View lead list with different filters
3. Access lead details and insights
4. Execute recommended actions

### Scenario 4: Analytics and Reporting
1. Generate leads with different quality scores
2. View analytics dashboard
3. Verify statistics accuracy
4. Check data visualization

## 📝 Reporting Issues

When reporting issues, please include:
- Test script output
- Browser console errors (F12)
- Django server logs
- Steps to reproduce
- Expected vs actual behavior

## 🚀 Next Steps

After successful testing:
1. Deploy to staging environment
2. Conduct user acceptance testing
3. Performance optimization
4. Security review
5. Production deployment

---

**Note**: This testing suite verifies the complete frontend interface implementation for Task 5 of the AI Sales Assistant project.