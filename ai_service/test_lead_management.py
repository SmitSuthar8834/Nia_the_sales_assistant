import json
import uuid
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Lead, AIInsights, ConversationAnalysis
from .serializers import LeadSerializer, LeadCreateSerializer, AIInsightsSerializer
from .tasks import analyze_lead_with_ai

User = get_user_model()


class LeadModelTest(TestCase):
    """Test cases for Lead model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_lead_creation(self):
        """Test basic lead creation"""
        lead = Lead.objects.create(
            user=self.user,
            company_name='Test Company',
            contact_info={
                'name': 'John Doe',
                'email': 'john@testcompany.com',
                'phone': '+1234567890'
            },
            status=Lead.Status.NEW,
            pain_points=['High costs', 'Manual processes'],
            requirements=['Automation', 'Cost reduction']
        )
        
        self.assertEqual(lead.company_name, 'Test Company')
        self.assertEqual(lead.contact_name, 'John Doe')
        self.assertEqual(lead.contact_email, 'john@testcompany.com')
        self.assertEqual(lead.contact_phone, '+1234567890')
        self.assertEqual(lead.status, Lead.Status.NEW)
        self.assertEqual(len(lead.pain_points), 2)
        self.assertEqual(len(lead.requirements), 2)
    
    def test_lead_str_representation(self):
        """Test lead string representation"""
        lead = Lead.objects.create(
            user=self.user,
            company_name='Test Company',
            status=Lead.Status.QUALIFIED
        )
        
        self.assertEqual(str(lead), 'Test Company - Qualified')
    
    def test_lead_contact_properties(self):
        """Test lead contact property methods"""
        lead = Lead.objects.create(
            user=self.user,
            company_name='Test Company',
            contact_info={
                'name': 'Jane Smith',
                'email': 'jane@example.com',
                'phone': '+9876543210',
                'title': 'CTO'
            }
        )
        
        self.assertEqual(lead.contact_name, 'Jane Smith')
        self.assertEqual(lead.contact_email, 'jane@example.com')
        self.assertEqual(lead.contact_phone, '+9876543210')


class AIInsightsModelTest(TestCase):
    """Test cases for AIInsights model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.lead = Lead.objects.create(
            user=self.user,
            company_name='Test Company',
            urgency_level=Lead.UrgencyLevel.HIGH
        )
    
    def test_ai_insights_creation(self):
        """Test AI insights creation"""
        insights = AIInsights.objects.create(
            lead=self.lead,
            lead_score=85.5,
            conversion_probability=75.0,
            quality_tier=AIInsights.QualityTier.HIGH,
            recommended_actions=['Schedule demo', 'Send proposal'],
            next_steps=['Follow up call', 'Technical discussion'],
            competitive_risk=AIInsights.CompetitiveRisk.MEDIUM
        )
        
        self.assertEqual(insights.lead_score, 85.5)
        self.assertEqual(insights.conversion_probability, 75.0)
        self.assertEqual(insights.quality_tier, AIInsights.QualityTier.HIGH)
        self.assertEqual(len(insights.recommended_actions), 2)
        self.assertEqual(len(insights.next_steps), 2)
    
    def test_ai_insights_properties(self):
        """Test AI insights property methods"""
        insights = AIInsights.objects.create(
            lead=self.lead,
            lead_score=90.0,
            conversion_probability=80.0,
            competitive_risk=AIInsights.CompetitiveRisk.HIGH
        )
        
        self.assertTrue(insights.is_high_quality)
        self.assertTrue(insights.needs_immediate_attention)
    
    def test_ai_insights_str_representation(self):
        """Test AI insights string representation"""
        insights = AIInsights.objects.create(
            lead=self.lead,
            lead_score=75.0
        )
        
        self.assertEqual(str(insights), 'AI Insights for Test Company (Score: 75.0)')


class LeadSerializerTest(TestCase):
    """Test cases for Lead serializers"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.lead_data = {
            'company_name': 'Test Company',
            'industry': 'Technology',
            'contact_info': {
                'name': 'John Doe',
                'email': 'john@testcompany.com',
                'phone': '+1234567890'
            },
            'pain_points': ['High costs', 'Manual processes'],
            'requirements': ['Automation', 'Integration']
        }
    
    def test_lead_serializer_validation(self):
        """Test lead serializer validation"""
        serializer = LeadSerializer(data=self.lead_data)
        self.assertTrue(serializer.is_valid())
    
    def test_lead_serializer_invalid_contact_info(self):
        """Test lead serializer with invalid contact info"""
        invalid_data = self.lead_data.copy()
        invalid_data['contact_info'] = {
            'name': 'John Doe',
            'email': 'invalid-email'  # Invalid email format
        }
        
        serializer = LeadSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('contact_info', serializer.errors)
    
    def test_lead_create_serializer(self):
        """Test lead create serializer with conversation text"""
        create_data = self.lead_data.copy()
        create_data['conversation_text'] = 'Customer mentioned they need automation solutions...'
        
        serializer = LeadCreateSerializer(data=create_data)
        self.assertTrue(serializer.is_valid())


class LeadAPITest(APITestCase):
    """Test cases for Lead API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.lead_data = {
            'company_name': 'Test Company',
            'industry': 'Technology',
            'contact_info': {
                'name': 'John Doe',
                'email': 'john@testcompany.com',
                'phone': '+1234567890'
            },
            'pain_points': ['High costs', 'Manual processes'],
            'requirements': ['Automation', 'Integration'],
            'status': 'new'
        }
    
    def test_create_lead(self):
        """Test creating a new lead"""
        url = reverse('ai_service:lead-list')
        response = self.client.post(url, self.lead_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('lead', response.data)
        
        # Verify lead was created in database
        lead = Lead.objects.get(company_name='Test Company')
        self.assertEqual(lead.user, self.user)
        self.assertEqual(lead.contact_name, 'John Doe')
    
    @patch('ai_service.tasks.analyze_lead_with_ai.delay')
    def test_create_lead_with_conversation_text(self, mock_analyze):
        """Test creating a lead with conversation text triggers AI analysis"""
        create_data = self.lead_data.copy()
        create_data['conversation_text'] = 'Customer mentioned they need automation solutions...'
        
        url = reverse('ai_service:lead-list')
        response = self.client.post(url, create_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['ai_analysis_triggered'])
        
        # Verify AI analysis task was triggered
        mock_analyze.assert_called_once()
    
    def test_list_leads(self):
        """Test listing leads"""
        # Create test leads
        Lead.objects.create(
            user=self.user,
            company_name='Company A',
            status=Lead.Status.NEW
        )
        Lead.objects.create(
            user=self.user,
            company_name='Company B',
            status=Lead.Status.QUALIFIED
        )
        
        url = reverse('ai_service:lead-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_filter_leads_by_status(self):
        """Test filtering leads by status"""
        Lead.objects.create(
            user=self.user,
            company_name='Company A',
            status=Lead.Status.NEW
        )
        Lead.objects.create(
            user=self.user,
            company_name='Company B',
            status=Lead.Status.QUALIFIED
        )
        
        url = reverse('ai_service:lead-list')
        response = self.client.get(url, {'status': 'new'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['company_name'], 'Company A')
    
    def test_search_leads(self):
        """Test searching leads by company name"""
        Lead.objects.create(
            user=self.user,
            company_name='Tech Solutions Inc',
            status=Lead.Status.NEW
        )
        Lead.objects.create(
            user=self.user,
            company_name='Marketing Agency',
            status=Lead.Status.NEW
        )
        
        url = reverse('ai_service:lead-list')
        response = self.client.get(url, {'search': 'Tech'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['company_name'], 'Tech Solutions Inc')
    
    def test_get_lead_detail(self):
        """Test getting lead detail"""
        lead = Lead.objects.create(
            user=self.user,
            company_name='Test Company',
            contact_info={'name': 'John Doe', 'email': 'john@test.com'}
        )
        
        url = reverse('ai_service:lead-detail', kwargs={'pk': lead.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['company_name'], 'Test Company')
        self.assertEqual(response.data['contact_name'], 'John Doe')
    
    def test_update_lead(self):
        """Test updating a lead"""
        lead = Lead.objects.create(
            user=self.user,
            company_name='Test Company',
            status=Lead.Status.NEW
        )
        
        update_data = {
            'status': 'qualified',
            'industry': 'Healthcare'
        }
        
        url = reverse('ai_service:lead-detail', kwargs={'pk': lead.id})
        response = self.client.patch(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        
        # Verify lead was updated
        lead.refresh_from_db()
        self.assertEqual(lead.status, Lead.Status.QUALIFIED)
        self.assertEqual(lead.industry, 'Healthcare')
    
    def test_delete_lead(self):
        """Test deleting a lead"""
        lead = Lead.objects.create(
            user=self.user,
            company_name='Test Company'
        )
        
        url = reverse('ai_service:lead-detail', kwargs={'pk': lead.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify lead was deleted
        self.assertFalse(Lead.objects.filter(id=lead.id).exists())
    
    def test_get_lead_insights(self):
        """Test getting AI insights for a lead"""
        lead = Lead.objects.create(
            user=self.user,
            company_name='Test Company'
        )
        insights = AIInsights.objects.create(
            lead=lead,
            lead_score=85.0,
            conversion_probability=70.0,
            recommended_actions=['Schedule demo', 'Send proposal']
        )
        
        url = reverse('ai_service:lead-insights', kwargs={'pk': lead.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['insights']['lead_score'], 85.0)
        self.assertEqual(len(response.data['insights']['recommended_actions']), 2)
    
    def test_get_lead_insights_not_found(self):
        """Test getting insights for lead without AI insights"""
        lead = Lead.objects.create(
            user=self.user,
            company_name='Test Company'
        )
        
        url = reverse('ai_service:lead-insights', kwargs={'pk': lead.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['status'], 'not_found')
    
    @patch('ai_service.tasks.refresh_lead_insights.delay')
    def test_refresh_lead_insights(self, mock_refresh):
        """Test refreshing AI insights for a lead"""
        lead = Lead.objects.create(
            user=self.user,
            company_name='Test Company',
            conversation_history='Customer mentioned they need automation...'
        )
        
        mock_refresh.return_value = MagicMock(id='task-123')
        
        url = reverse('ai_service:lead-refresh-insights', kwargs={'pk': lead.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['task_id'], 'task-123')
        
        mock_refresh.assert_called_once_with(str(lead.id))
    
    def test_refresh_insights_no_conversation(self):
        """Test refreshing insights for lead without conversation history"""
        lead = Lead.objects.create(
            user=self.user,
            company_name='Test Company'
        )
        
        url = reverse('ai_service:lead-refresh-insights', kwargs={'pk': lead.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('No conversation history', response.data['error'])
    
    def test_get_high_priority_leads(self):
        """Test getting high priority leads"""
        # Create regular lead
        regular_lead = Lead.objects.create(
            user=self.user,
            company_name='Regular Company',
            urgency_level=Lead.UrgencyLevel.LOW
        )
        AIInsights.objects.create(
            lead=regular_lead,
            lead_score=50.0,
            quality_tier=AIInsights.QualityTier.MEDIUM
        )
        
        # Create high priority lead
        priority_lead = Lead.objects.create(
            user=self.user,
            company_name='Priority Company',
            urgency_level=Lead.UrgencyLevel.HIGH
        )
        AIInsights.objects.create(
            lead=priority_lead,
            lead_score=90.0,
            quality_tier=AIInsights.QualityTier.HIGH
        )
        
        url = reverse('ai_service:lead-high-priority')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['company_name'], 'Priority Company')
    
    def test_lead_analytics(self):
        """Test lead analytics endpoint"""
        # Create test leads with different statuses and insights
        lead1 = Lead.objects.create(
            user=self.user,
            company_name='Company A',
            status=Lead.Status.NEW,
            urgency_level=Lead.UrgencyLevel.HIGH
        )
        AIInsights.objects.create(
            lead=lead1,
            lead_score=85.0,
            quality_tier=AIInsights.QualityTier.HIGH
        )
        
        lead2 = Lead.objects.create(
            user=self.user,
            company_name='Company B',
            status=Lead.Status.QUALIFIED
        )
        AIInsights.objects.create(
            lead=lead2,
            lead_score=60.0,
            quality_tier=AIInsights.QualityTier.MEDIUM
        )
        
        url = reverse('ai_service:lead_analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        
        analytics = response.data['analytics']
        self.assertEqual(analytics['total_leads'], 2)
        self.assertEqual(analytics['leads_with_insights'], 2)
        self.assertEqual(analytics['insights_coverage'], 100.0)
        self.assertEqual(analytics['high_priority_count'], 1)
        self.assertEqual(analytics['status_distribution']['new'], 1)
        self.assertEqual(analytics['status_distribution']['qualified'], 1)


class LeadTaskTest(TestCase):
    """Test cases for lead-related Celery tasks"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.lead = Lead.objects.create(
            user=self.user,
            company_name='Test Company',
            conversation_history='Customer mentioned they need automation solutions for their manufacturing process...'
        )
    
    @patch('ai_service.tasks.GeminiAIService')
    def test_analyze_lead_with_ai_success(self, mock_ai_service):
        """Test successful AI analysis of lead"""
        # Mock AI service responses
        mock_service = mock_ai_service.return_value
        mock_service.extract_lead_info.return_value = {
            'company_name': 'Test Company',
            'industry': 'Manufacturing',
            'pain_points': ['Manual processes', 'High costs'],
            'requirements': ['Automation', 'Cost reduction']
        }
        mock_service.calculate_lead_quality_score.return_value = {
            'overall_score': 85.0,
            'conversion_probability': 75.0,
            'quality_tier': 'high'
        }
        mock_service.generate_recommendations.return_value = {
            'recommendations': ['Schedule demo', 'Send proposal'],
            'next_best_actions': ['Follow up call']
        }
        mock_service.generate_sales_strategy.return_value = {
            'primary_strategy': 'consultative_selling'
        }
        mock_service.generate_industry_insights.return_value = {
            'industry_trends': ['Digital transformation']
        }
        
        # Execute task
        result = analyze_lead_with_ai(str(self.lead.id))
        
        # Verify result
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['lead_id'], str(self.lead.id))
        
        # Verify AI insights were created
        self.assertTrue(AIInsights.objects.filter(lead=self.lead).exists())
        insights = AIInsights.objects.get(lead=self.lead)
        self.assertEqual(insights.lead_score, 85.0)
        self.assertEqual(insights.conversion_probability, 75.0)
    
    def test_analyze_lead_with_ai_no_conversation(self):
        """Test AI analysis with no conversation text"""
        lead_no_conversation = Lead.objects.create(
            user=self.user,
            company_name='No Conversation Company'
        )
        
        result = analyze_lead_with_ai(str(lead_no_conversation.id))
        
        self.assertEqual(result['status'], 'skipped')
        self.assertEqual(result['reason'], 'No conversation text available')
    
    def test_analyze_lead_with_ai_lead_not_found(self):
        """Test AI analysis with non-existent lead"""
        fake_lead_id = str(uuid.uuid4())
        
        result = analyze_lead_with_ai(fake_lead_id)
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error'], 'Lead not found')