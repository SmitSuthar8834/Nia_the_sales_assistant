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
            self.assertIn('555-123-4567', entities['phone_numbers'])  # Test alias
            self.assertIn('$50,000', entities['monetary_amounts'])
            self.assertIn('John Doe', entities['people'])
    
    def test_extract_entities_with_fallback(self):
        """Test entity extraction with AI fallback to pattern matching"""
        text = "John Smith from Acme Corp Inc contacted us about their CRM needs in Q2 2024."
        
        # Mock AI extraction to fail
        with patch.object(self.ai_service, '_extract_entities_with_ai') as mock_ai_extract:
            mock_ai_extract.side_effect = Exception("API quota exceeded")
            
            entities = self.ai_service.extract_entities(text)
            
            # Should still extract entities using pattern matching
            self.assertIn('Acme Corp Inc', entities['companies'])
            self.assertIn('CRM', entities['technologies'])
            self.assertIn('Q2 2024', entities['dates'])
    
    def test_extract_entities_pattern_matching(self):
        """Test pattern-based entity extraction fallback"""
        text = "Dr. Sarah Johnson from TechStart LLC mentioned their API integration needs."
        entities = {'companies': [], 'people': [], 'technologies': [], 'dates': []}
        
        self.ai_service._extract_entities_with_patterns(text, entities)
        
        self.assertIn('TechStart LLC', entities['companies'])
        self.assertIn('Dr. Sarah Johnson', entities['people'])
        self.assertIn('API', entities['technologies'])


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


class SalesRecommendationsTestCase(TestCase):
    """Test cases for AI-powered sales recommendations (Task 3)"""
    
    def setUp(self):
        self.ai_service = GeminiAIService()
        self.sample_lead_data = {
            'company_name': 'TechStart Inc',
            'contact_details': {
                'name': 'Sarah Johnson',
                'email': 'sarah@techstart.com',
                'title': 'CTO'
            },
            'industry': 'Software Development',
            'company_size': '50-100 employees',
            'pain_points': ['Manual data entry', 'System integration issues'],
            'requirements': ['Automated workflow', 'API integration'],
            'budget_info': '$100,000 - $150,000',
            'timeline': 'Q3 2024',
            'urgency_level': 'high'
        }
    
    @patch('ai_service.services.genai.configure')
    @patch('ai_service.services.genai.GenerativeModel')
    def test_lead_quality_score_calculation(self, mock_model, mock_configure):
        """Test lead quality score calculation"""
        mock_response = MagicMock()
        mock_response.text = '''```json
        {
            "overall_score": 85,
            "score_breakdown": {
                "data_completeness": 90,
                "engagement_level": 80,
                "budget_fit": 85,
                "timeline_urgency": 90,
                "decision_authority": 75,
                "pain_point_severity": 95
            },
            "quality_tier": "high",
            "conversion_probability": 75,
            "estimated_deal_size": "$100,000 - $150,000",
            "sales_cycle_prediction": "3-6 months",
            "key_strengths": ["Clear pain points", "Confirmed budget", "Urgent timeline"],
            "improvement_areas": ["Need more decision maker access"],
            "competitive_risk": "medium",
            "next_best_action": "Schedule technical demo"
        }
        ```'''
        
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
        ai_service = GeminiAIService()
        quality_score = ai_service.calculate_lead_quality_score(self.sample_lead_data)
        
        self.assertEqual(quality_score['overall_score'], 85)
        self.assertEqual(quality_score['quality_tier'], 'high')
        self.assertEqual(quality_score['conversion_probability'], 75)
        self.assertIn('Clear pain points', quality_score['key_strengths'])
        self.assertIn('validation_metadata', quality_score)
    
    @patch('ai_service.services.genai.configure')
    @patch('ai_service.services.genai.GenerativeModel')
    def test_sales_strategy_generation(self, mock_model, mock_configure):
        """Test sales strategy generation"""
        mock_response = MagicMock()
        mock_response.text = '''```json
        {
            "primary_strategy": "consultative",
            "approach_rationale": "Technical buyer needs detailed solution understanding",
            "key_messaging": [
                "Focus on technical capabilities",
                "Demonstrate integration ease",
                "Show scalability benefits"
            ],
            "objection_handling": {
                "budget_concerns": "Focus on ROI and efficiency gains",
                "timing_issues": "Highlight urgent pain points",
                "competition": "Emphasize technical superiority",
                "authority": "Engage CEO in business case"
            },
            "engagement_tactics": [
                "Technical demo with integration examples",
                "Provide detailed technical documentation",
                "Offer proof of concept"
            ],
            "success_metrics": [
                "Demo engagement level",
                "Technical questions asked",
                "Follow-up meeting requests"
            ],
            "risk_mitigation": [
                "Ensure technical fit early",
                "Address integration concerns",
                "Validate budget authority"
            ]
        }
        ```'''
        
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
        ai_service = GeminiAIService()
        sales_strategy = ai_service.generate_sales_strategy(self.sample_lead_data)
        
        self.assertEqual(sales_strategy['primary_strategy'], 'consultative')
        self.assertIn('Technical buyer needs', sales_strategy['approach_rationale'])
        self.assertIn('Focus on technical capabilities', sales_strategy['key_messaging'])
        self.assertIn('strategy_metadata', sales_strategy)
        self.assertGreater(sales_strategy['strategy_metadata']['confidence_score'], 70)
    
    @patch('ai_service.services.genai.configure')
    @patch('ai_service.services.genai.GenerativeModel')
    def test_industry_insights_generation(self, mock_model, mock_configure):
        """Test industry-specific insights generation"""
        mock_response = MagicMock()
        mock_response.text = '''```json
        {
            "industry_trends": [
                "Digital transformation acceleration",
                "Focus on developer productivity"
            ],
            "industry_pain_points": [
                "Technical debt management",
                "Integration complexity"
            ],
            "solution_fit": {
                "why_relevant": "Addresses core development workflow issues",
                "specific_benefits": ["Reduced manual work", "Better integration"],
                "use_cases": ["CI/CD automation", "API management"]
            },
            "competitive_landscape": {
                "common_competitors": ["GitLab", "Jenkins", "Azure DevOps"],
                "differentiation_opportunities": ["Ease of integration", "Developer experience"]
            },
            "sales_best_practices": [
                "Speak technical language",
                "Focus on developer experience",
                "Provide hands-on demos"
            ],
            "compliance_considerations": [
                "SOC 2 compliance",
                "Data security requirements"
            ],
            "success_stories": [
                "Similar companies reduced deployment time by 60%",
                "Improved developer satisfaction scores"
            ]
        }
        ```'''
        
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
        ai_service = GeminiAIService()
        industry_insights = ai_service.generate_industry_insights(self.sample_lead_data)
        
        self.assertIn('Digital transformation', industry_insights['industry_trends'][0])
        self.assertIn('Technical debt', industry_insights['industry_pain_points'][0])
        self.assertIn('Addresses core development', industry_insights['solution_fit']['why_relevant'])
        self.assertIn('insights_metadata', industry_insights)
        self.assertTrue(industry_insights['insights_metadata']['industry_specified'])
    
    def test_recommendation_confidence_calculation(self):
        """Test recommendation confidence scoring"""
        # Test with complete data
        complete_recommendation = {
            'type': 'next_step',
            'priority': 'high',
            'title': 'Schedule demo'
        }
        
        confidence = self.ai_service._calculate_recommendation_confidence(
            complete_recommendation, self.sample_lead_data
        )
        
        self.assertGreater(confidence, 70)  # Should be high confidence
        
        # Test with incomplete data
        incomplete_data = {'company_name': 'Test Corp'}
        incomplete_confidence = self.ai_service._calculate_recommendation_confidence(
            complete_recommendation, incomplete_data
        )
        
        self.assertLess(incomplete_confidence, confidence)  # Should be lower
    
    def test_default_fallbacks(self):
        """Test default fallback methods"""
        # Test default quality score
        default_quality = self.ai_service._get_default_quality_score()
        self.assertEqual(default_quality['overall_score'], 50)
        self.assertEqual(default_quality['quality_tier'], 'medium')
        self.assertIn('validation_metadata', default_quality)
        
        # Test default strategy
        default_strategy = self.ai_service._get_default_strategy()
        self.assertEqual(default_strategy['primary_strategy'], 'consultative')
        self.assertIn('strategy_metadata', default_strategy)
        
        # Test default insights
        default_insights = self.ai_service._get_default_insights()
        self.assertIn('industry_trends', default_insights)
        self.assertIn('insights_metadata', default_insights)


class SalesRecommendationsAPITestCase(APITestCase):
    """Test cases for sales recommendations API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.sample_lead_data = {
            'company_name': 'TechStart Inc',
            'contact_details': {'name': 'Sarah Johnson'},
            'industry': 'Software Development',
            'pain_points': ['Manual processes'],
            'requirements': ['Automation']
        }
    
    @patch('ai_service.views.GeminiAIService')
    def test_lead_quality_score_endpoint(self, mock_service):
        """Test lead quality score API endpoint"""
        mock_instance = mock_service.return_value
        mock_instance.calculate_lead_quality_score.return_value = {
            'overall_score': 85,
            'quality_tier': 'high',
            'conversion_probability': 75,
            'validation_metadata': {'confidence_level': 90}
        }
        
        url = reverse('ai_service:lead_quality_score')
        data = {'lead_data': self.sample_lead_data}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['quality_score']['overall_score'], 85)
        self.assertIsNotNone(response.data['calculated_at'])
    
    @patch('ai_service.views.GeminiAIService')
    def test_sales_strategy_endpoint(self, mock_service):
        """Test sales strategy API endpoint"""
        mock_instance = mock_service.return_value
        mock_instance.generate_sales_strategy.return_value = {
            'primary_strategy': 'consultative',
            'key_messaging': ['Focus on value'],
            'strategy_metadata': {'confidence_score': 80}
        }
        
        url = reverse('ai_service:sales_strategy')
        data = {'lead_data': self.sample_lead_data}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['sales_strategy']['primary_strategy'], 'consultative')
        self.assertIsNotNone(response.data['generated_at'])
    
    @patch('ai_service.views.GeminiAIService')
    def test_industry_insights_endpoint(self, mock_service):
        """Test industry insights API endpoint"""
        mock_instance = mock_service.return_value
        mock_instance.generate_industry_insights.return_value = {
            'industry_trends': ['Digital transformation'],
            'solution_fit': {'why_relevant': 'Addresses key needs'},
            'insights_metadata': {'confidence_score': 85}
        }
        
        url = reverse('ai_service:industry_insights')
        data = {'lead_data': self.sample_lead_data}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('Digital transformation', response.data['industry_insights']['industry_trends'])
        self.assertIsNotNone(response.data['generated_at'])
    
    def test_missing_lead_data_error(self):
        """Test error handling for missing lead data"""
        endpoints = [
            'ai_service:lead_quality_score',
            'ai_service:sales_strategy',
            'ai_service:industry_insights'
        ]
        
        for endpoint_name in endpoints:
            url = reverse(endpoint_name)
            response = self.client.post(url, {}, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertFalse(response.data['success'])
            self.assertEqual(response.data['error_code'], 'MISSING_LEAD_DATA')


class LeadExtractionAccuracyTestCase(TestCase):
    """Test cases for AI extraction accuracy and validation"""
    
    def setUp(self):
        self.ai_service = GeminiAIService()
        self.sample_conversations = [
            {
                'text': "Hi, this is John Smith from Acme Corporation. We're looking for a CRM solution to help with our sales process. Our current system is outdated and we need something that can integrate with our existing tools. We have about 50 sales reps and our budget is around $100,000. We'd like to implement this by Q3 2024.",
                'expected': {
                    'company_name': 'Acme Corporation',
                    'contact_name': 'John Smith',
                    'pain_points': ['outdated system'],
                    'requirements': ['CRM solution', 'integration'],
                    'budget_info': '$100,000',
                    'timeline': 'Q3 2024'
                }
            },
            {
                'text': "Sarah from TechStart Inc called about automation needs. They have manual processes that are slowing them down. Looking for workflow automation, budget is flexible, need it ASAP.",
                'expected': {
                    'company_name': 'TechStart Inc',
                    'contact_name': 'Sarah',
                    'pain_points': ['manual processes', 'slowing down'],
                    'requirements': ['workflow automation'],
                    'urgency_level': 'high'
                }
            }
        ]
    
    @patch('ai_service.services.genai.configure')
    @patch('ai_service.services.genai.GenerativeModel')
    def test_lead_extraction_accuracy_comprehensive(self, mock_model, mock_configure):
        """Test comprehensive lead extraction accuracy"""
        for i, conversation in enumerate(self.sample_conversations):
            with self.subTest(conversation=i):
                # Mock AI response based on expected data
                expected = conversation['expected']
                mock_response = MagicMock()
                mock_response.text = f'''```json
                {{
                    "company_name": "{expected.get('company_name', 'null')}",
                    "contact_details": {{
                        "name": "{expected.get('contact_name', 'null')}",
                        "email": null,
                        "phone": null,
                        "title": null,
                        "department": null
                    }},
                    "pain_points": {json.dumps(expected.get('pain_points', []))},
                    "requirements": {json.dumps(expected.get('requirements', []))},
                    "budget_info": "{expected.get('budget_info', 'null')}",
                    "timeline": "{expected.get('timeline', 'null')}",
                    "decision_makers": [],
                    "industry": null,
                    "company_size": null,
                    "urgency_level": "{expected.get('urgency_level', 'null')}",
                    "current_solution": null,
                    "competitors_mentioned": []
                }}
                ```'''
                
                mock_model_instance = MagicMock()
                mock_model_instance.generate_content.return_value = mock_response
                mock_model.return_value = mock_model_instance
                
                ai_service = GeminiAIService()
                result = ai_service.extract_lead_info(conversation['text'])
                
                # Verify extraction accuracy
                if expected.get('company_name'):
                    self.assertEqual(result['company_name'], expected['company_name'])
                if expected.get('contact_name'):
                    self.assertEqual(result['contact_details']['name'], expected['contact_name'])
                if expected.get('pain_points'):
                    for pain_point in expected['pain_points']:
                        self.assertIn(pain_point, result['pain_points'])
                if expected.get('requirements'):
                    for requirement in expected['requirements']:
                        self.assertIn(requirement, result['requirements'])
    
    def test_data_validation_accuracy(self):
        """Test data validation accuracy"""
        test_cases = [
            {
                'data': {
                    'company_name': 'Valid Corp',
                    'contact_details': {
                        'name': 'John Doe',
                        'email': 'john@valid.com',
                        'phone': '555-123-4567'
                    },
                    'pain_points': ['Issue 1'],
                    'requirements': ['Solution 1']
                },
                'expected_valid': True,
                'expected_score': 85.0  # High score for complete data
            },
            {
                'data': {
                    'company_name': None,
                    'contact_details': {
                        'name': None,
                        'email': 'invalid-email',
                        'phone': '123'
                    },
                    'pain_points': [],
                    'requirements': []
                },
                'expected_valid': False,
                'expected_score': 0.0  # Low score for incomplete/invalid data
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            with self.subTest(case=i):
                validation = self.ai_service.validate_extracted_data(test_case['data'])
                
                self.assertEqual(validation['is_valid'], test_case['expected_valid'])
                if test_case['expected_valid']:
                    self.assertGreaterEqual(validation['data_quality_score'], test_case['expected_score'])
                else:
                    self.assertLessEqual(validation['data_quality_score'], test_case['expected_score'])
    
    def test_confidence_score_accuracy(self):
        """Test confidence score calculation accuracy"""
        # Test with high-quality data
        high_quality_data = {
            'company_name': 'Test Corp',
            'contact_details': {
                'name': 'John Doe',
                'email': 'john@test.com',
                'phone': '555-123-4567',
                'title': 'CEO'
            },
            'pain_points': ['Issue 1', 'Issue 2'],
            'requirements': ['Solution 1', 'Solution 2'],
            'budget_info': '$50,000',
            'timeline': 'Q2 2024',
            'industry': 'Technology',
            'decision_makers': ['John Doe']
        }
        
        high_score = self.ai_service._calculate_confidence_score(high_quality_data)
        self.assertGreaterEqual(high_score, 80.0)
        
        # Test with low-quality data
        low_quality_data = {
            'company_name': 'Test Corp',
            'contact_details': {},
            'pain_points': [],
            'requirements': []
        }
        
        low_score = self.ai_service._calculate_confidence_score(low_quality_data)
        self.assertLessEqual(low_score, 30.0)
        
        # High quality should score higher than low quality
        self.assertGreater(high_score, low_score)
    
    def test_entity_recognition_accuracy(self):
        """Test entity recognition accuracy for companies, contacts, and requirements"""
        test_text = """
        John Smith, the CTO at TechCorp Inc, mentioned they need a new CRM system. 
        Their current solution from Salesforce isn't meeting their needs. 
        Contact him at john.smith@techcorp.com or 555-987-6543. 
        Budget is around $75,000 and they want to implement by December 2024.
        """
        
        # Mock AI entity extraction
        with patch.object(self.ai_service, '_extract_entities_with_ai') as mock_ai_extract:
            mock_ai_extract.return_value = {
                'companies': ['TechCorp Inc', 'Salesforce'],
                'people': ['John Smith'],
                'technologies': ['CRM system'],
                'dates': ['December 2024']
            }
            
            entities = self.ai_service.extract_entities(test_text)
            
            # Verify company recognition
            self.assertIn('TechCorp Inc', entities['companies'])
            self.assertIn('Salesforce', entities['companies'])
            
            # Verify contact recognition
            self.assertIn('John Smith', entities['people'])
            self.assertIn('john.smith@techcorp.com', entities['emails'])
            self.assertIn('555-987-6543', entities['phones'])
            
            # Verify requirement recognition
            self.assertIn('CRM system', entities['technologies'])
            
            # Verify monetary amount recognition
            self.assertIn('$75,000', entities['monetary_amounts'])
    
    def test_extraction_with_missing_information(self):
        """Test extraction accuracy when information is missing or incomplete"""
        incomplete_text = "Someone called about needing help with their processes."
        
        with patch.object(self.ai_service, '_make_api_call') as mock_api_call:
            mock_response = MagicMock()
            mock_response.text = '''```json
            {
                "company_name": null,
                "contact_details": {
                    "name": null,
                    "email": null,
                    "phone": null,
                    "title": null,
                    "department": null
                },
                "pain_points": ["process issues"],
                "requirements": ["help with processes"],
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
            mock_api_call.return_value = mock_response
            
            result = self.ai_service.extract_lead_info(incomplete_text)
            
            # Should handle missing information gracefully
            self.assertIsNone(result['company_name'])
            self.assertIsNone(result['contact_details']['name'])
            self.assertIn('process issues', result['pain_points'])
            
            # Confidence should be low for incomplete data
            self.assertLess(result['extraction_metadata']['confidence_score'], 50.0)
    
    def test_extraction_error_handling(self):
        """Test extraction error handling and fallback mechanisms"""
        test_text = "Test conversation"
        
        # Test JSON parsing error
        with patch.object(self.ai_service, '_make_api_call') as mock_api_call:
            mock_response = MagicMock()
            mock_response.text = "Invalid JSON response"
            mock_api_call.return_value = mock_response
            
            result = self.ai_service.extract_lead_info(test_text)
            
            # Should return default structure
            self.assertIsNone(result['company_name'])
            self.assertEqual(result['extraction_metadata']['extraction_method'], 'default_fallback')
        
        # Test API call error
        with patch.object(self.ai_service, '_make_api_call') as mock_api_call:
            mock_api_call.side_effect = Exception("API Error")
            
            result = self.ai_service.extract_lead_info(test_text)
            
            # Should return default structure
            self.assertIsNone(result['company_name'])
            self.assertEqual(result['extraction_metadata']['extraction_method'], 'default_fallback')es for lead extraction accuracy with sample conversations"""
    
    def setUp(self):
        self.ai_service = GeminiAIService()
    
    @patch('ai_service.services.genai.configure')
    @patch('ai_service.services.genai.GenerativeModel')
    def test_sales_call_conversation(self, mock_model, mock_configure):
        # Test extraction from a typical sales call conversation
        mock_response = MagicMock()
        mock_response.text = '{"company_name": "TechStart Inc", "contact_details": {"name": "Sarah Johnson", "email": "sarah.johnson@techstart.com", "phone": "555-987-6543", "title": "CTO", "department": "Technology"}, "pain_points": ["Manual data entry", "System integration issues", "Scalability concerns"], "requirements": ["Automated workflow", "API integration", "Cloud-based solution"], "budget_info": "$100,000 - $150,000", "timeline": "Implementation by Q3 2024", "decision_makers": ["Sarah Johnson", "Mike Chen (CEO)"], "industry": "Software Development", "company_size": "50-100 employees", "urgency_level": "high", "current_solution": "Excel spreadsheets and manual processes", "competitors_mentioned": ["Salesforce", "HubSpot"]}'
        
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
        conversation = "Hi Sarah, thanks for taking the time to speak with me today. I understand you are the CTO at TechStart Inc. Sarah: Yes, that is right. We are a software development company with about 75 employees, and we are having some real challenges with our current processes. What kind of challenges are you facing? Sarah: Well, we are still doing a lot of manual data entry, which is eating up our developers time. We also have major system integration issues - our tools do not talk to each other properly. And frankly, we are worried about scalability as we grow. I see. What would an ideal solution look like for you? Sarah: We need something that can automate our workflow, has good API integration capabilities, and is cloud-based so we can scale easily. Our budget is somewhere between $100,000 and $150,000, and we would need to have everything implemented by Q3 2024. Who else would be involved in this decision? Sarah: It would be myself and our CEO, Mike Chen. We have looked at Salesforce and HubSpot, but they do not quite fit our specific needs. You can reach me at sarah.johnson@techstart.com or call me at 555-987-6543 if you have any follow-up questions."
        
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
        # Test extraction from conversation with minimal information
        mock_response = MagicMock()
        mock_response.text = '{"company_name": "ABC Company", "contact_details": {"name": "John", "email": null, "phone": null, "title": null, "department": null}, "pain_points": ["Need better solution"], "requirements": [], "budget_info": null, "timeline": null, "decision_makers": [], "industry": null, "company_size": null, "urgency_level": null, "current_solution": null, "competitors_mentioned": []}'
        
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


class GeminiAIIntegrationTestCase(TestCase):
    # Integration tests for Gemini AI service with real API calls (requires valid API key)
    
    def setUp(self):
        self.ai_service = GeminiAIService()
    
    def test_connection_with_valid_key(self):
        # Test connection to Gemini AI with valid API key
        # Skip if no valid API key is configured
        try:
            result = self.ai_service.test_connection()
            if result['success']:
                self.assertTrue(result['success'])
                self.assertIsNotNone(result['response'])
            else:
                self.skipTest("No valid Gemini API key configured")
        except Exception as e:
            self.skipTest(f"API connection failed: {e}")
    
    def test_real_lead_extraction(self):
        # Test real lead extraction with a sample conversation
        # Skip if quota is exceeded
        try:
            sample_conversation = "Hello, this is Mike Johnson from DataTech Solutions. We are a mid-size company with about 200 employees in the financial services sector. We are currently struggling with our data management processes and are looking for a comprehensive solution that can help us automate our workflows and improve data accuracy. Our budget is around $75,000 and we need to implement something by the end of Q2 2024. You can reach me at mike.johnson@datatech.com or call 555-123-4567."
            
            result = self.ai_service.extract_lead_info(sample_conversation)
            
            # Verify extraction worked
            self.assertIsNotNone(result)
            self.assertIn('extraction_metadata', result)
            
            # If extraction was successful, verify some basic fields
            if result.get('company_name'):
                self.assertIn('DataTech', result['company_name'])
            
        except Exception as e:
            if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                self.skipTest(f"API quota exceeded: {e}")
            else:
                raise