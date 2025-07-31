from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
import json

from .services import GeminiAIService, DataValidator
from .models import ConversationAnalysis

User = get_user_model()


class DataValidatorTestCase(TestCase):
    """Test cases for DataValidator class"""
    
    def setUp(self):
        self.validator = DataValidator()
    
    def test_validate_email_valid(self):
        """Test email validation with valid emails"""
        valid_emails = [
            'test@example.com',
            'user.name@company.co.uk',
            'admin+test@domain.org'
        ]
        for email in valid_emails:
            self.assertTrue(self.validator.validate_email(email))
    
    def test_validate_email_invalid(self):
        """Test email validation with invalid emails"""
        invalid_emails = [
            'invalid-email',
            '@domain.com',
            'user@',
            '',
            None
        ]
        for email in invalid_emails:
            self.assertFalse(self.validator.validate_email(email))
    
    def test_validate_phone_valid(self):
        """Test phone validation with valid phone numbers"""
        valid_phones = [
            '+1-555-123-4567',
            '(555) 123-4567',
            '555.123.4567',
            '5551234567',
            '+44 20 7946 0958'
        ]
        for phone in valid_phones:
            self.assertTrue(self.validator.validate_phone(phone))
    
    def test_validate_phone_invalid(self):
        """Test phone validation with invalid phone numbers"""
        invalid_phones = [
            '123',  # Too short
            '12345678901234567890',  # Too long
            'abc-def-ghij',
            '',
            None
        ]
        for phone in invalid_phones:
            self.assertFalse(self.validator.validate_phone(phone))
    
    def test_clean_company_name(self):
        """Test company name cleaning"""
        self.assertEqual(self.validator.clean_company_name('  Acme Corp  '), 'Acme Corp')
        self.assertIsNone(self.validator.clean_company_name('null'))
        self.assertIsNone(self.validator.clean_company_name('None'))
        self.assertIsNone(self.validator.clean_company_name(''))
    
    def test_validate_lead_data(self):
        """Test comprehensive lead data validation"""
        test_data = {
            'company_name': '  Test Company  ',
            'contact_details': {
                'name': 'John Doe',
                'email': 'john@test.com',
                'phone': '555-123-4567'
            },
            'pain_points': ['Issue 1', '', 'Issue 2', 'Issue 1'],  # Test deduplication
            'requirements': ['Req 1', 'null', 'Req 2']
        }
        
        validated = self.validator.validate_lead_data(test_data)
        
        self.assertEqual(validated['company_name'], 'Test Company')
        self.assertEqual(validated['contact_details']['email'], 'john@test.com')
        self.assertEqual(len(validated['pain_points']), 2)  # Deduplicated
        self.assertNotIn('null', validated['requirements'])


class GeminiAIServiceTestCase(TestCase):
    """Test cases for GeminiAIService class"""
    
    def setUp(self):
        self.ai_service = GeminiAIService()
    
    @patch('ai_service.services.genai.configure')
    @patch('ai_service.services.genai.GenerativeModel')
    def test_extract_lead_info_success(self, mock_model, mock_configure):
        """Test successful lead information extraction"""
        # Mock AI response
        mock_response = MagicMock()
        mock_response.text = '''```json
        {
            "company_name": "Acme Corp",
            "contact_details": {
                "name": "John Smith",
                "email": "john@acme.com",
                "phone": "555-123-4567"
            },
            "pain_points": ["Slow processes", "High costs"],
            "requirements": ["Automation", "Cost reduction"],
            "budget_info": "$50,000",
            "timeline": "Q2 2024",
            "decision_makers": ["John Smith", "Jane Doe"],
            "industry": "Manufacturing",
            "company_size": "500 employees"
        }
        ```'''
        
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
        # Create fresh service instance with mocked model
        ai_service = GeminiAIService()
        conversation_text = "We spoke with John Smith from Acme Corp about their automation needs..."
        result = ai_service.extract_lead_info(conversation_text)
        
        self.assertEqual(result['company_name'], 'Acme Corp')
        self.assertEqual(result['contact_details']['name'], 'John Smith')
        self.assertIn('Slow processes', result['pain_points'])
        self.assertGreater(result['extraction_metadata']['confidence_score'], 0)
    
    @patch('ai_service.services.genai.configure')
    @patch('ai_service.services.genai.GenerativeModel')
    def test_extract_lead_info_json_error(self, mock_model, mock_configure):
        """Test lead extraction with JSON parsing error"""
        mock_response = MagicMock()
        mock_response.text = "Invalid JSON response"
        
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
        # Create fresh service instance with mocked model
        ai_service = GeminiAIService()
        result = ai_service.extract_lead_info("test conversation")
        
        # Should return default structure
        self.assertIsNone(result['company_name'])
        self.assertEqual(result['extraction_metadata']['extraction_method'], 'default_fallback')
    
    def test_calculate_confidence_score(self):
        """Test confidence score calculation"""
        complete_data = {
            'company_name': 'Test Corp',
            'contact_details': {'name': 'John', 'email': 'john@test.com', 'phone': '555-1234'},
            'pain_points': ['Issue 1'],
            'requirements': ['Req 1'],
            'budget_info': '$10k',
            'timeline': 'Q1',
            'industry': 'Tech',
            'decision_makers': ['John']
        }
        
        score = self.ai_service._calculate_confidence_score(complete_data)
        self.assertGreater(score, 80)  # Should be high for complete data
        
        minimal_data = {'company_name': 'Test Corp'}
        score_minimal = self.ai_service._calculate_confidence_score(minimal_data)
        self.assertEqual(score_minimal, 20)  # Only company name
    
    def test_calculate_data_completeness(self):
        """Test data completeness calculation"""
        complete_data = {
            'company_name': 'Test Corp',
            'contact_details': {'name': 'John'},
            'pain_points': ['Issue'],
            'requirements': ['Req'],
            'budget_info': '$10k',
            'timeline': 'Q1',
            'decision_makers': ['John'],
            'industry': 'Tech',
            'company_size': '100',
            'urgency_level': 'high',
            'current_solution': 'Excel'
        }
        
        completeness = self.ai_service._calculate_data_completeness(complete_data)
        self.assertEqual(completeness, 100.0)
    
    def test_extract_entities(self):
        """Test entity extraction from text"""
        text = "Contact John Doe at john@example.com or call 555-123-4567. Budget is $50,000."
        
        with patch.object(self.ai_service, '_extract_entities_with_ai') as mock_ai_extract:
            mock_ai_extract.return_value = {
                'companies': ['Example Corp'],
                'people': ['John Doe'],
                'technologies': [],
                'dates': []
            }
            
            entities = self.ai_service.extract_entities(text)
            
            self.assertIn('john@example.com', entities['emails'])
            self.assertIn('555-123-4567', entities['phones'])
            self.assertIn('$50,000', entities['monetary_amounts'])
            self.assertIn('John Doe', entities['people'])


class LeadExtractionAPITestCase(APITestCase):
    """Test cases for lead extraction API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    @patch('ai_service.views.GeminiAIService')
    def test_analyze_conversation_success(self, mock_service):
        """Test successful conversation analysis"""
        # Mock service response
        mock_instance = mock_service.return_value
        mock_instance.extract_lead_info.return_value = {
            'company_name': 'Test Corp',
            'contact_details': {'name': 'John Doe'},
            'pain_points': ['Issue 1'],
            'requirements': ['Req 1'],
            'extraction_metadata': {
                'confidence_score': 85.0,
                'data_completeness': 70.0,
                'extraction_method': 'gemini_ai_enhanced'
            }
        }
        mock_instance.validate_extracted_data.return_value = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'data_quality_score': 85.0
        }
        mock_instance.extract_entities.return_value = {'companies': ['Test Corp']}
        mock_instance.generate_recommendations.return_value = {
            'recommendations': [{'title': 'Follow up'}]
        }
        
        url = reverse('ai_service:analyze_conversation')
        data = {
            'conversation_text': 'Test conversation with John from Test Corp',
            'extract_entities': True,
            'generate_recommendations': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['lead_information']['company_name'], 'Test Corp')
        self.assertIsNotNone(response.data['analysis_id'])
    
    def test_analyze_conversation_missing_text(self):
        """Test conversation analysis with missing text"""
        url = reverse('ai_service:analyze_conversation')
        data = {'conversation_text': ''}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error_code'], 'MISSING_CONVERSATION_TEXT')
    
    @patch('ai_service.views.GeminiAIService')
    def test_extract_lead_info_endpoint(self, mock_service):
        """Test dedicated lead extraction endpoint"""
        mock_instance = mock_service.return_value
        mock_instance.extract_lead_info.return_value = {
            'company_name': 'Test Corp',
            'extraction_metadata': {'confidence_score': 75.0}
        }
        mock_instance.validate_extracted_data.return_value = {
            'is_valid': True,
            'data_quality_score': 75.0
        }
        
        url = reverse('ai_service:extract_lead_info')
        data = {'conversation_text': 'Test conversation'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['lead_information']['company_name'], 'Test Corp')
    
    @patch('ai_service.views.GeminiAIService')
    def test_extract_entities_endpoint(self, mock_service):
        """Test entity extraction endpoint"""
        mock_instance = mock_service.return_value
        mock_instance.extract_entities.return_value = {
            'companies': ['Test Corp'],
            'people': ['John Doe'],
            'emails': ['john@test.com']
        }
        
        url = reverse('ai_service:extract_entities')
        data = {'text': 'John Doe from Test Corp, email: john@test.com'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('Test Corp', response.data['entities']['companies'])
    
    @patch('ai_service.views.GeminiAIService')
    def test_validate_lead_data_endpoint(self, mock_service):
        """Test lead data validation endpoint"""
        mock_instance = mock_service.return_value
        mock_instance.validate_extracted_data.return_value = {
            'is_valid': True,
            'errors': [],
            'warnings': ['Low completeness'],
            'data_quality_score': 60.0
        }
        
        url = reverse('ai_service:validate_lead_data')
        data = {
            'lead_data': {
                'company_name': 'Test Corp',
                'contact_details': {'name': 'John'}
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertTrue(response.data['validation']['is_valid'])
    
    def test_conversation_history_endpoint(self):
        """Test conversation history retrieval"""
        # Create test analysis
        ConversationAnalysis.objects.create(
            user=self.user,
            conversation_text='Test conversation',
            extracted_data={
                'lead_info': {
                    'company_name': 'Test Corp',
                    'contact_details': {'name': 'John'},
                    'extraction_metadata': {'confidence_score': 80.0}
                }
            }
        )
        
        url = reverse('ai_service:conversation_history')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['history']), 1)
        self.assertEqual(response.data['history'][0]['company_name'], 'Test Corp')


class ConversationAnalysisModelTestCase(TestCase):
    """Test cases for ConversationAnalysis model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_conversation_analysis(self):
        """Test creating a conversation analysis record"""
        analysis = ConversationAnalysis.objects.create(
            user=self.user,
            conversation_text='Test conversation',
            extracted_data={'test': 'data'}
        )
        
        self.assertEqual(analysis.user, self.user)
        self.assertEqual(analysis.conversation_text, 'Test conversation')
        self.assertEqual(analysis.extracted_data['test'], 'data')
        self.assertIsNotNone(analysis.analysis_timestamp)
    
    def test_conversation_analysis_ordering(self):
        """Test that analyses are ordered by timestamp descending"""
        import time
        
        analysis1 = ConversationAnalysis.objects.create(
            user=self.user,
            conversation_text='First conversation',
            extracted_data={}
        )
        
        # Small delay to ensure different timestamps
        time.sleep(0.01)
        
        analysis2 = ConversationAnalysis.objects.create(
            user=self.user,
            conversation_text='Second conversation',
            extracted_data={}
        )
        
        analyses = ConversationAnalysis.objects.all()
        self.assertEqual(analyses[0], analysis2)  # Most recent first
        self.assertEqual(analyses[1], analysis1)


class LeadExtractionAccuracyTestCase(TestCase):
    """Test cases for lead extraction accuracy with sample conversations"""
    
    def setUp(self):
        self.ai_service = GeminiAIService()
    
    @patch('ai_service.services.genai.configure')
    @patch('ai_service.services.genai.GenerativeModel')
    def test_sales_call_conversation(self, mock_model, mock_configure):
        """Test extraction from a typical sales call conversation"""
        mock_response = MagicMock()
        mock_response.text = '''```json
        {
            "company_name": "TechStart Inc",
            "contact_details": {
                "name": "Sarah Johnson",
                "email": "sarah.johnson@techstart.com",
                "phone": "555-987-6543",
                "title": "CTO",
                "department": "Technology"
            },
            "pain_points": ["Manual data entry", "System integration issues", "Scalability concerns"],
            "requirements": ["Automated workflow", "API integration", "Cloud-based solution"],
            "budget_info": "$100,000 - $150,000",
            "timeline": "Implementation by Q3 2024",
            "decision_makers": ["Sarah Johnson", "Mike Chen (CEO)"],
            "industry": "Software Development",
            "company_size": "50-100 employees",
            "urgency_level": "high",
            "current_solution": "Excel spreadsheets and manual processes",
            "competitors_mentioned": ["Salesforce", "HubSpot"]
        }
        ```'''
        
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
        conversation = """
        Hi Sarah, thanks for taking the time to speak with me today. I understand you're the CTO at TechStart Inc.
        
        Sarah: Yes, that's right. We're a software development company with about 75 employees, and we're having some real challenges with our current processes.
        
        What kind of challenges are you facing?
        
        Sarah: Well, we're still doing a lot of manual data entry, which is eating up our developers' time. We also have major system integration issues - our tools don't talk to each other properly. And frankly, we're worried about scalability as we grow.
        
        I see. What would an ideal solution look like for you?
        
        Sarah: We need something that can automate our workflow, has good API integration capabilities, and is cloud-based so we can scale easily. Our budget is somewhere between $100,000 and $150,000, and we'd need to have everything implemented by Q3 2024.
        
        Who else would be involved in this decision?
        
        Sarah: It would be myself and our CEO, Mike Chen. We've looked at Salesforce and HubSpot, but they don't quite fit our specific needs.
        
        You can reach me at sarah.johnson@techstart.com or call me at 555-987-6543 if you have any follow-up questions.
        """
        
        # Create fresh service instance with mocked model
        ai_service = GeminiAIService()
        result = ai_service.extract_lead_info(conversation)
        
        # Verify key information was extracted correctly
        self.assertEqual(result['company_name'], 'TechStart Inc')
        self.assertEqual(result['contact_details']['name'], 'Sarah Johnson')
        self.assertEqual(result['contact_details']['email'], 'sarah.johnson@techstart.com')
        self.assertIn('Manual data entry', result['pain_points'])
        self.assertIn('Automated workflow', result['requirements'])
        self.assertIn('Sarah Johnson', result['decision_makers'])
        self.assertEqual(result['urgency_level'], 'high')
    
    @patch('ai_service.services.genai.configure')
    @patch('ai_service.services.genai.GenerativeModel')
    def test_minimal_information_conversation(self, mock_model, mock_configure):
        """Test extraction from conversation with minimal information"""
        mock_response = MagicMock()
        mock_response.text = '''```json
        {
            "company_name": "ABC Company",
            "contact_details": {
                "name": "John",
                "email": null,
                "phone": null,
                "title": null,
                "department": null
            },
            "pain_points": ["Need better solution"],
            "requirements": [],
            "budget_info": null,
            "timeline": null,
            "decision_makers": [],
            "industry": null,
            "company_size": null,
            "urgency_level": null,
            "current_solution": null,
            "competitors_mentioned": []
        }
        ```'''
        
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
        conversation = "Hi, this is John from ABC Company. We need a better solution for our business."
        
        # Create fresh service instance with mocked model
        ai_service = GeminiAIService()
        result = ai_service.extract_lead_info(conversation)
        
        # Should extract basic information
        self.assertEqual(result['company_name'], 'ABC Company')
        self.assertEqual(result['contact_details']['name'], 'John')
        
        # Confidence should be lower for minimal data
        confidence = result['extraction_metadata']['confidence_score']
        self.assertLessEqual(confidence, 50)  # Should be low confidence
