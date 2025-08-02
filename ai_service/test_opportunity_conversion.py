"""
Tests for Opportunity Conversion Intelligence functionality (Task 10)

This module tests the AI-powered opportunity conversion intelligence features including:
- Lead-to-opportunity conversion probability analysis
- Deal size and timeline prediction
- Sales stage recommendation functionality
- Risk factor identification and mitigation suggestions
- Historical data analysis for improved predictions
"""

import json
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch, MagicMock

from ai_service.models import Lead, AIInsights, Opportunity, OpportunityIntelligence
from ai_service.services import GeminiAIService
from ai_service.serializers import (
    OpportunitySerializer, OpportunityIntelligenceSerializer,
    OpportunityWithIntelligenceSerializer
)

User = get_user_model()


class OpportunityConversionIntelligenceTestCase(TestCase):
    """Test case for opportunity conversion intelligence functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test lead
        self.lead = Lead.objects.create(
            user=self.user,
            company_name='TechCorp Solutions',
            industry='technology',
            company_size='100-500 employees',
            contact_info={
                'name': 'John Smith',
                'email': 'john.smith@techcorp.com',
                'phone': '+1-555-0123',
                'title': 'CTO',
                'department': 'Technology'
            },
            status='qualified',
            pain_points=['Manual processes', 'Data silos', 'Scalability issues'],
            requirements=['AI automation', 'Data integration', 'Cloud scalability'],
            budget_info='$50,000 - $100,000 approved',
            timeline='Q2 implementation needed',
            decision_makers=['John Smith (CTO)', 'Sarah Johnson (CEO)'],
            urgency_level='high'
        )
        
        # Create AI insights for the lead
        self.ai_insights = AIInsights.objects.create(
            lead=self.lead,
            lead_score=85.0,
            conversion_probability=75.0,
            quality_tier='high',
            opportunity_conversion_score=80.0,
            recommended_for_conversion=True,
            conversion_readiness_factors=[
                'Budget approved',
                'Decision makers identified',
                'Timeline urgency confirmed'
            ],
            estimated_deal_size='$50,000 - $100,000',
            sales_cycle_prediction='3-4 months'
        )
        
        # Create test opportunity
        self.opportunity = Opportunity.objects.create(
            lead=self.lead,
            user=self.user,
            name='TechCorp AI Implementation',
            description='AI-powered automation solution for TechCorp',
            estimated_value=Decimal('75000.00'),
            probability=75.0,
            expected_close_date=date.today() + timedelta(days=90),
            sales_cycle_days=90,
            stage='qualification',
            priority='high'
        )
        
        # Sample lead data for API tests
        self.sample_lead_data = {
            'company_name': 'TechCorp Solutions',
            'industry': 'technology',
            'company_size': '100-500 employees',
            'contact_details': {
                'name': 'John Smith',
                'email': 'john.smith@techcorp.com',
                'title': 'CTO'
            },
            'pain_points': ['Manual processes', 'Data silos'],
            'requirements': ['AI automation', 'Data integration'],
            'budget_info': '$50,000 - $100,000 approved',
            'timeline': 'Q2 implementation needed',
            'urgency_level': 'high'
        }
        
        # Sample opportunity data for API tests
        self.sample_opportunity_data = {
            'name': 'TechCorp AI Implementation',
            'estimated_value': 75000,
            'probability': 75,
            'stage': 'qualification',
            'expected_close_date': (date.today() + timedelta(days=90)).isoformat()
        }


class OpportunityConversionAnalysisTests(OpportunityConversionIntelligenceTestCase):
    """Tests for opportunity conversion analysis functionality"""
    
    @patch('ai_service.services.GeminiAIService._make_api_call')
    def test_analyze_opportunity_conversion_potential(self, mock_api_call):
        """Test lead-to-opportunity conversion probability analysis"""
        # Mock AI response
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "conversion_probability": 75,
            "conversion_confidence": 85,
            "conversion_readiness_score": 80,
            "readiness_factors": [
                "Clear budget authority identified",
                "Specific timeline mentioned",
                "Pain points align with our solution"
            ],
            "blocking_factors": [
                "Decision maker not yet identified"
            ],
            "recommended_for_conversion": True,
            "conversion_timeline": "2-4 weeks",
            "required_actions_before_conversion": [
                "Qualify budget range and approval process",
                "Identify and engage key decision makers"
            ],
            "conversion_triggers": [
                "Budget approval received",
                "Technical requirements confirmed"
            ],
            "risk_factors": [
                "Competitive evaluation in progress"
            ],
            "success_indicators": [
                "Multiple stakeholder engagement",
                "Technical evaluation requested"
            ]
        })
        mock_api_call.return_value = mock_response
        
        # Test the service method
        ai_service = GeminiAIService()
        result = ai_service.analyze_opportunity_conversion_potential(
            self.sample_lead_data,
            {'avg_conversion_rate': 25, 'avg_sales_cycle': '3-6 months'}
        )
        
        # Verify results
        self.assertEqual(result['conversion_probability'], 75)
        self.assertEqual(result['conversion_confidence'], 85)
        self.assertTrue(result['recommended_for_conversion'])
        self.assertIn('Clear budget authority identified', result['readiness_factors'])
        self.assertIn('Budget approval received', result['conversion_triggers'])
        
        # Verify API was called with correct prompt structure
        mock_api_call.assert_called_once()
        call_args = mock_api_call.call_args[0][0]
        self.assertIn('BANT criteria', call_args)
        self.assertIn('conversion readiness', call_args)
    
    def test_opportunity_conversion_analysis_api_endpoint(self):
        """Test the opportunity conversion analysis API endpoint"""
        url = reverse('ai_service:opportunity_conversion_analysis')
        
        with patch('ai_service.services.GeminiAIService.analyze_opportunity_conversion_potential') as mock_analyze:
            mock_analyze.return_value = {
                'conversion_probability': 75,
                'conversion_confidence': 85,
                'recommended_for_conversion': True,
                'readiness_factors': ['Budget approved', 'Timeline confirmed']
            }
            
            # Test successful analysis
            response = self.client.post(url, {
                'lead_data': self.sample_lead_data,
                'historical_data': {'avg_conversion_rate': 25}
            }, content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data['success'])
            self.assertEqual(data['conversion_analysis']['conversion_probability'], 75)
            self.assertTrue(data['conversion_analysis']['recommended_for_conversion'])
    
    def test_conversion_analysis_missing_data(self):
        """Test conversion analysis with missing lead data"""
        url = reverse('ai_service:opportunity_conversion_analysis')
        
        response = self.client.post(url, {}, content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['error_code'], 'MISSING_LEAD_DATA')


class DealSizeTimelinePredictionTests(OpportunityConversionIntelligenceTestCase):
    """Tests for deal size and timeline prediction functionality"""
    
    @patch('ai_service.services.GeminiAIService._make_api_call')
    def test_predict_deal_size_and_timeline(self, mock_api_call):
        """Test deal size range and sales timeline prediction"""
        # Mock AI response
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "deal_size_prediction": {
                "minimum_value": 25000,
                "maximum_value": 75000,
                "most_likely_value": 50000,
                "confidence_level": 75,
                "sizing_rationale": "Based on company size, pain point severity, and industry benchmarks"
            },
            "timeline_prediction": {
                "minimum_days": 60,
                "maximum_days": 180,
                "most_likely_days": 120,
                "confidence_level": 80,
                "timeline_rationale": "Considering decision complexity and typical industry sales cycles"
            },
            "deal_size_factors": [
                "Company size indicates mid-market budget capacity",
                "Multiple pain points suggest comprehensive solution need"
            ],
            "timeline_factors": [
                "Decision maker authority level affects approval speed",
                "Technical evaluation requirements extend timeline"
            ],
            "accelerating_factors": [
                "Urgent business need creates timeline pressure"
            ],
            "risk_factors": [
                "Budget approval process complexity"
            ]
        })
        mock_api_call.return_value = mock_response
        
        # Test the service method
        ai_service = GeminiAIService()
        result = ai_service.predict_deal_size_and_timeline(
            self.sample_lead_data,
            self.sample_opportunity_data
        )
        
        # Verify deal size predictions
        deal_size = result['deal_size_prediction']
        self.assertEqual(deal_size['minimum_value'], 25000)
        self.assertEqual(deal_size['maximum_value'], 75000)
        self.assertEqual(deal_size['most_likely_value'], 50000)
        self.assertEqual(deal_size['confidence_level'], 75)
        
        # Verify timeline predictions
        timeline = result['timeline_prediction']
        self.assertEqual(timeline['minimum_days'], 60)
        self.assertEqual(timeline['maximum_days'], 180)
        self.assertEqual(timeline['most_likely_days'], 120)
        self.assertEqual(timeline['confidence_level'], 80)
        
        # Verify factors are included
        self.assertIn('Company size indicates mid-market budget capacity', result['deal_size_factors'])
        self.assertIn('Urgent business need creates timeline pressure', result['accelerating_factors'])
    
    def test_deal_prediction_validation(self):
        """Test validation of deal size and timeline predictions"""
        ai_service = GeminiAIService()
        
        # Test with invalid data that needs validation
        invalid_data = {
            'deal_size_prediction': {
                'minimum_value': -1000,  # Invalid negative value
                'maximum_value': 10000,
                'most_likely_value': 50000  # Invalid - higher than max
            },
            'timeline_prediction': {
                'minimum_days': -10,  # Invalid negative
                'maximum_days': 30,
                'most_likely_days': 100  # Invalid - higher than max
            }
        }
        
        validated = ai_service._validate_deal_predictions(invalid_data, self.sample_lead_data)
        
        # Check that validation corrected the values
        deal_size = validated['deal_size_prediction']
        self.assertGreaterEqual(deal_size['minimum_value'], 1000)  # Should be corrected to minimum
        self.assertGreaterEqual(deal_size['maximum_value'], deal_size['minimum_value'])
        self.assertLessEqual(deal_size['most_likely_value'], deal_size['maximum_value'])
        
        timeline = validated['timeline_prediction']
        self.assertGreaterEqual(timeline['minimum_days'], 7)  # Should be corrected to minimum
        self.assertGreaterEqual(timeline['maximum_days'], timeline['minimum_days'])
        self.assertLessEqual(timeline['most_likely_days'], timeline['maximum_days'])
    
    def test_deal_size_timeline_prediction_api_endpoint(self):
        """Test the deal size and timeline prediction API endpoint"""
        url = reverse('ai_service:deal_size_timeline_prediction')
        
        with patch('ai_service.services.GeminiAIService.predict_deal_size_and_timeline') as mock_predict:
            mock_predict.return_value = {
                'deal_size_prediction': {
                    'minimum_value': 25000,
                    'maximum_value': 75000,
                    'most_likely_value': 50000,
                    'confidence_level': 75
                },
                'timeline_prediction': {
                    'minimum_days': 60,
                    'maximum_days': 180,
                    'most_likely_days': 120,
                    'confidence_level': 80
                }
            }
            
            response = self.client.post(url, {
                'lead_data': self.sample_lead_data,
                'opportunity_data': self.sample_opportunity_data
            }, content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data['success'])
            self.assertEqual(data['predictions']['deal_size_prediction']['most_likely_value'], 50000)
            self.assertEqual(data['predictions']['timeline_prediction']['most_likely_days'], 120)


class SalesStageRecommendationTests(OpportunityConversionIntelligenceTestCase):
    """Tests for sales stage recommendation functionality"""
    
    @patch('ai_service.services.GeminiAIService._make_api_call')
    def test_recommend_sales_stage(self, mock_api_call):
        """Test sales stage recommendation based on opportunity characteristics"""
        # Mock AI response
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "current_stage_assessment": {
                "recommended_stage": "qualification",
                "stage_confidence": 85,
                "stage_rationale": "Lead shows clear qualification criteria but needs budget confirmation"
            },
            "advancement_analysis": {
                "next_stage": "proposal",
                "advancement_probability": 70,
                "advancement_timeline": "2-3 weeks",
                "advancement_confidence": 75
            },
            "stage_requirements_met": [
                "Initial contact established",
                "Basic needs identified",
                "Pain points confirmed"
            ],
            "stage_requirements_missing": [
                "Budget authority not confirmed",
                "Decision timeline unclear"
            ],
            "advancement_actions": [
                "Schedule budget qualification call",
                "Identify and engage decision makers"
            ],
            "stage_risks": [
                "Budget approval process may be complex"
            ],
            "success_metrics": [
                "Budget range confirmed within 2 weeks"
            ]
        })
        mock_api_call.return_value = mock_response
        
        # Test the service method
        ai_service = GeminiAIService()
        result = ai_service.recommend_sales_stage(
            self.sample_lead_data,
            self.sample_opportunity_data,
            'prospecting'
        )
        
        # Verify stage assessment
        assessment = result['current_stage_assessment']
        self.assertEqual(assessment['recommended_stage'], 'qualification')
        self.assertEqual(assessment['stage_confidence'], 85)
        
        # Verify advancement analysis
        advancement = result['advancement_analysis']
        self.assertEqual(advancement['next_stage'], 'proposal')
        self.assertEqual(advancement['advancement_probability'], 70)
        
        # Verify requirements and actions
        self.assertIn('Initial contact established', result['stage_requirements_met'])
        self.assertIn('Budget authority not confirmed', result['stage_requirements_missing'])
        self.assertIn('Schedule budget qualification call', result['advancement_actions'])
    
    def test_sales_stage_recommendation_api_endpoint(self):
        """Test the sales stage recommendation API endpoint"""
        url = reverse('ai_service:sales_stage_recommendation')
        
        with patch('ai_service.services.GeminiAIService.recommend_sales_stage') as mock_recommend:
            mock_recommend.return_value = {
                'current_stage_assessment': {
                    'recommended_stage': 'qualification',
                    'stage_confidence': 85
                },
                'advancement_analysis': {
                    'next_stage': 'proposal',
                    'advancement_probability': 70
                }
            }
            
            response = self.client.post(url, {
                'lead_data': self.sample_lead_data,
                'opportunity_data': self.sample_opportunity_data,
                'current_stage': 'prospecting'
            }, content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data['success'])
            self.assertEqual(data['stage_recommendations']['current_stage_assessment']['recommended_stage'], 'qualification')


class RiskFactorAnalysisTests(OpportunityConversionIntelligenceTestCase):
    """Tests for risk factor identification and mitigation functionality"""
    
    @patch('ai_service.services.GeminiAIService._make_api_call')
    def test_identify_risk_factors_and_mitigation(self, mock_api_call):
        """Test risk factor identification and mitigation strategy generation"""
        # Mock AI response
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "overall_risk_assessment": {
                "risk_level": "medium",
                "risk_score": 45,
                "confidence": 80,
                "primary_risk_category": "competitive"
            },
            "identified_risks": [
                {
                    "risk_type": "competitive",
                    "risk_description": "Multiple vendor evaluation in progress",
                    "probability": 60,
                    "impact": "high",
                    "risk_score": 75,
                    "indicators": ["Competitor mentions", "Evaluation timeline"]
                },
                {
                    "risk_type": "budget",
                    "risk_description": "Budget approval process unclear",
                    "probability": 40,
                    "impact": "high",
                    "risk_score": 60,
                    "indicators": ["No budget range provided"]
                }
            ],
            "mitigation_strategies": [
                {
                    "risk_type": "competitive",
                    "strategies": [
                        "Emphasize unique differentiators early in process",
                        "Build strong champion relationships"
                    ],
                    "timeline": "immediate",
                    "resources_required": ["Sales engineer", "Reference customers"]
                }
            ],
            "monitoring_recommendations": [
                "Weekly competitive intelligence updates"
            ],
            "early_warning_indicators": [
                "Delayed responses to proposals"
            ]
        })
        mock_api_call.return_value = mock_response
        
        # Test the service method
        ai_service = GeminiAIService()
        result = ai_service.identify_risk_factors_and_mitigation(
            self.sample_lead_data,
            self.sample_opportunity_data,
            {'common_loss_reasons': ['Price', 'Timeline']}
        )
        
        # Verify overall risk assessment
        assessment = result['overall_risk_assessment']
        self.assertEqual(assessment['risk_level'], 'medium')
        self.assertEqual(assessment['risk_score'], 45)
        self.assertEqual(assessment['primary_risk_category'], 'competitive')
        
        # Verify identified risks
        risks = result['identified_risks']
        self.assertEqual(len(risks), 2)
        competitive_risk = next(r for r in risks if r['risk_type'] == 'competitive')
        self.assertEqual(competitive_risk['probability'], 60)
        self.assertEqual(competitive_risk['impact'], 'high')
        
        # Verify mitigation strategies
        strategies = result['mitigation_strategies']
        self.assertEqual(len(strategies), 1)
        competitive_strategy = strategies[0]
        self.assertEqual(competitive_strategy['risk_type'], 'competitive')
        self.assertIn('Emphasize unique differentiators early in process', competitive_strategy['strategies'])
    
    def test_risk_factor_analysis_api_endpoint(self):
        """Test the risk factor analysis API endpoint"""
        url = reverse('ai_service:risk_factor_analysis')
        
        with patch('ai_service.services.GeminiAIService.identify_risk_factors_and_mitigation') as mock_analyze:
            mock_analyze.return_value = {
                'overall_risk_assessment': {
                    'risk_level': 'medium',
                    'risk_score': 45
                },
                'identified_risks': [
                    {
                        'risk_type': 'competitive',
                        'risk_description': 'Multiple vendor evaluation',
                        'probability': 60
                    }
                ]
            }
            
            response = self.client.post(url, {
                'lead_data': self.sample_lead_data,
                'opportunity_data': self.sample_opportunity_data,
                'historical_data': {'common_loss_reasons': ['Price']}
            }, content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data['success'])
            self.assertEqual(data['risk_analysis']['overall_risk_assessment']['risk_level'], 'medium')


class HistoricalPatternAnalysisTests(OpportunityConversionIntelligenceTestCase):
    """Tests for historical data analysis functionality"""
    
    @patch('ai_service.services.GeminiAIService._make_api_call')
    def test_analyze_historical_patterns(self, mock_api_call):
        """Test historical pattern analysis for improved predictions"""
        # Mock AI response
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "similar_leads_analysis": {
                "similar_leads_count": 25,
                "average_conversion_rate": 35,
                "average_deal_size": 45000,
                "average_sales_cycle": 95,
                "success_factors": [
                    "Early technical evaluation",
                    "Executive sponsor engagement"
                ]
            },
            "industry_benchmarks": {
                "industry_conversion_rate": 28,
                "industry_average_deal_size": 52000,
                "industry_sales_cycle": 120,
                "competitive_win_rate": 42
            },
            "predictive_insights": [
                "Leads with similar pain points convert 40% higher than average",
                "Company size indicates 25% higher deal value potential"
            ],
            "optimization_recommendations": [
                "Allocate senior sales engineer for technical evaluation",
                "Schedule executive briefing within first 2 weeks"
            ],
            "success_probability_factors": {
                "positive_indicators": [
                    "Pain point severity matches our strength areas"
                ],
                "negative_indicators": [
                    "Competitive landscape more crowded than average"
                ]
            }
        })
        mock_api_call.return_value = mock_response
        
        # Test the service method
        ai_service = GeminiAIService()
        result = ai_service.analyze_historical_patterns(
            self.sample_lead_data,
            str(self.user.id)
        )
        
        # Verify similar leads analysis
        similar_analysis = result['similar_leads_analysis']
        self.assertEqual(similar_analysis['similar_leads_count'], 25)
        self.assertEqual(similar_analysis['average_conversion_rate'], 35)
        self.assertEqual(similar_analysis['average_deal_size'], 45000)
        
        # Verify industry benchmarks
        benchmarks = result['industry_benchmarks']
        self.assertEqual(benchmarks['industry_conversion_rate'], 28)
        self.assertEqual(benchmarks['competitive_win_rate'], 42)
        
        # Verify insights and recommendations
        self.assertIn('Leads with similar pain points convert 40% higher than average', result['predictive_insights'])
        self.assertIn('Allocate senior sales engineer for technical evaluation', result['optimization_recommendations'])
    
    def test_historical_pattern_analysis_api_endpoint(self):
        """Test the historical pattern analysis API endpoint"""
        url = reverse('ai_service:historical_pattern_analysis')
        
        with patch('ai_service.services.GeminiAIService.analyze_historical_patterns') as mock_analyze:
            mock_analyze.return_value = {
                'similar_leads_analysis': {
                    'similar_leads_count': 25,
                    'average_conversion_rate': 35
                },
                'industry_benchmarks': {
                    'industry_conversion_rate': 28
                }
            }
            
            response = self.client.post(url, {
                'lead_data': self.sample_lead_data,
                'user_id': str(self.user.id)
            }, content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data['success'])
            self.assertEqual(data['historical_analysis']['similar_leads_analysis']['similar_leads_count'], 25)


class OpportunityModelTests(OpportunityConversionIntelligenceTestCase):
    """Tests for Opportunity and OpportunityIntelligence models"""
    
    def test_opportunity_model_creation(self):
        """Test creating an opportunity with all fields"""
        opportunity = Opportunity.objects.create(
            lead=self.lead,
            user=self.user,
            name='Test Opportunity',
            description='Test opportunity description',
            estimated_value=Decimal('50000.00'),
            probability=60.0,
            expected_close_date=date.today() + timedelta(days=60),
            sales_cycle_days=60,
            stage='prospecting',
            priority='medium'
        )
        
        self.assertEqual(opportunity.name, 'Test Opportunity')
        self.assertEqual(opportunity.estimated_value, Decimal('50000.00'))
        self.assertEqual(opportunity.probability, 60.0)
        self.assertEqual(opportunity.stage, 'prospecting')
        self.assertFalse(opportunity.is_high_value)  # Below 50k threshold
        self.assertEqual(opportunity.days_to_close, 60)
    
    def test_opportunity_intelligence_model_creation(self):
        """Test creating opportunity intelligence with all fields"""
        intelligence = OpportunityIntelligence.objects.create(
            opportunity=self.opportunity,
            conversion_probability=75.0,
            conversion_likelihood='high',
            conversion_confidence=85.0,
            predicted_deal_size_min=Decimal('40000.00'),
            predicted_deal_size_max=Decimal('80000.00'),
            predicted_close_date=date.today() + timedelta(days=90),
            sales_cycle_prediction_days=90,
            recommended_stage='qualification',
            next_stage_probability=70.0,
            stage_advancement_timeline='2-3 weeks',
            overall_risk_level='medium',
            risk_factors=['Budget approval complexity', 'Competitive evaluation'],
            risk_mitigation_strategies=['Accelerate decision timeline', 'Provide superior ROI analysis'],
            competitive_threats=['Competitor A', 'In-house solution'],
            competitive_advantages=['Better AI capabilities', 'Faster implementation'],
            win_strategy='Focus on technical superiority and implementation speed',
            similar_deals_count=15,
            historical_win_rate=65.0,
            priority_actions=['Schedule technical demo', 'Engage executive sponsor'],
            next_best_actions=['Qualify budget process', 'Identify additional stakeholders']
        )
        
        self.assertEqual(intelligence.conversion_probability, 75.0)
        self.assertEqual(intelligence.conversion_likelihood, 'high')
        self.assertTrue(intelligence.is_high_probability)
        self.assertFalse(intelligence.needs_attention)  # Risk level is medium, not high
        self.assertEqual(intelligence.similar_deals_count, 15)
        self.assertIn('Budget approval complexity', intelligence.risk_factors)
    
    def test_opportunity_serializers(self):
        """Test opportunity serializers"""
        # Test OpportunitySerializer
        serializer = OpportunitySerializer(self.opportunity)
        data = serializer.data
        
        self.assertEqual(data['name'], 'TechCorp AI Implementation')
        self.assertEqual(data['lead_company_name'], 'TechCorp Solutions')
        self.assertEqual(data['lead_contact_name'], 'John Smith')
        self.assertTrue(data['is_high_value'])  # 75k is above threshold
        
        # Test OpportunityIntelligenceSerializer
        intelligence = OpportunityIntelligence.objects.create(
            opportunity=self.opportunity,
            conversion_probability=75.0,
            conversion_likelihood='high',
            conversion_confidence=85.0,
            predicted_deal_size_min=Decimal('40000.00'),
            predicted_deal_size_max=Decimal('80000.00'),
            predicted_close_date=date.today() + timedelta(days=90),
            sales_cycle_prediction_days=90
        )
        
        intel_serializer = OpportunityIntelligenceSerializer(intelligence)
        intel_data = intel_serializer.data
        
        self.assertEqual(intel_data['conversion_probability'], 75.0)
        self.assertEqual(intel_data['opportunity_name'], 'TechCorp AI Implementation')
        self.assertTrue(intel_data['is_high_probability'])


class ComprehensiveOpportunityIntelligenceTests(OpportunityConversionIntelligenceTestCase):
    """Tests for comprehensive opportunity intelligence functionality"""
    
    def test_comprehensive_opportunity_intelligence_api_endpoint(self):
        """Test the comprehensive opportunity intelligence API endpoint"""
        url = reverse('ai_service:comprehensive_opportunity_intelligence')
        
        with patch('ai_service.services.GeminiAIService.analyze_opportunity_conversion_potential') as mock_conversion, \
             patch('ai_service.services.GeminiAIService.predict_deal_size_and_timeline') as mock_predictions, \
             patch('ai_service.services.GeminiAIService.recommend_sales_stage') as mock_stage, \
             patch('ai_service.services.GeminiAIService.identify_risk_factors_and_mitigation') as mock_risk, \
             patch('ai_service.services.GeminiAIService.analyze_historical_patterns') as mock_historical:
            
            # Mock all service responses
            mock_conversion.return_value = {'conversion_probability': 75, 'recommended_for_conversion': True}
            mock_predictions.return_value = {'deal_size_prediction': {'most_likely_value': 50000}}
            mock_stage.return_value = {'current_stage_assessment': {'recommended_stage': 'qualification'}}
            mock_risk.return_value = {'overall_risk_assessment': {'risk_level': 'medium'}}
            mock_historical.return_value = {'similar_leads_analysis': {'average_conversion_rate': 35}}
            
            response = self.client.post(url, {
                'lead_data': self.sample_lead_data,
                'opportunity_data': self.sample_opportunity_data,
                'include_conversion_analysis': True,
                'include_deal_predictions': True,
                'include_stage_recommendations': True,
                'include_risk_analysis': True,
                'include_historical_patterns': True
            }, content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data['success'])
            
            # Verify all components are included
            self.assertIn('conversion_analysis', data)
            self.assertIn('deal_predictions', data)
            self.assertIn('stage_recommendations', data)
            self.assertIn('risk_analysis', data)
            self.assertIn('historical_analysis', data)
            
            # Verify metadata
            metadata = data['intelligence_metadata']
            components = metadata['components_included']
            self.assertTrue(all(components.values()))  # All components should be True
            self.assertGreater(metadata['overall_confidence'], 0)
    
    def test_selective_intelligence_components(self):
        """Test requesting only specific intelligence components"""
        url = reverse('ai_service:comprehensive_opportunity_intelligence')
        
        with patch('ai_service.services.GeminiAIService.analyze_opportunity_conversion_potential') as mock_conversion:
            mock_conversion.return_value = {'conversion_probability': 75}
            
            response = self.client.post(url, {
                'lead_data': self.sample_lead_data,
                'include_conversion_analysis': True,
                'include_deal_predictions': False,
                'include_stage_recommendations': False,
                'include_risk_analysis': False,
                'include_historical_patterns': False
            }, content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Verify only conversion analysis is included
            self.assertIn('conversion_analysis', data)
            self.assertNotIn('deal_predictions', data)
            self.assertNotIn('stage_recommendations', data)
            self.assertNotIn('risk_analysis', data)
            self.assertNotIn('historical_analysis', data)


class OpportunityConversionAccuracyTests(OpportunityConversionIntelligenceTestCase):
    """Tests for conversion prediction accuracy validation"""
    
    def test_conversion_probability_accuracy_validation(self):
        """Test validation of conversion probability predictions"""
        ai_service = GeminiAIService()
        
        # Test with various probability values
        test_cases = [
            {'conversion_probability': -10, 'expected': 0},  # Negative should be corrected to 0
            {'conversion_probability': 150, 'expected': 100},  # Over 100 should be corrected to 100
            {'conversion_probability': 75, 'expected': 75},  # Valid value should remain unchanged
        ]
        
        for case in test_cases:
            data = {'conversion_probability': case['conversion_probability'], 'conversion_confidence': 80}
            validated = ai_service._validate_conversion_analysis(data, self.sample_lead_data)
            self.assertEqual(validated['conversion_probability'], case['expected'])
    
    def test_deal_size_prediction_accuracy_validation(self):
        """Test validation of deal size prediction accuracy"""
        ai_service = GeminiAIService()
        
        # Test with invalid deal size ranges
        invalid_data = {
            'deal_size_prediction': {
                'minimum_value': 100000,  # Min higher than max
                'maximum_value': 50000,
                'most_likely_value': 75000  # Most likely outside range
            }
        }
        
        validated = ai_service._validate_deal_predictions(invalid_data, self.sample_lead_data)
        deal_size = validated['deal_size_prediction']
        
        # Verify logical consistency
        self.assertLessEqual(deal_size['minimum_value'], deal_size['maximum_value'])
        self.assertGreaterEqual(deal_size['most_likely_value'], deal_size['minimum_value'])
        self.assertLessEqual(deal_size['most_likely_value'], deal_size['maximum_value'])
    
    def test_historical_pattern_accuracy_metrics(self):
        """Test accuracy metrics for historical pattern analysis"""
        ai_service = GeminiAIService()
        
        # Test validation of historical analysis data
        invalid_historical = {
            'similar_leads_analysis': {
                'average_conversion_rate': 150,  # Invalid percentage
                'average_deal_size': -5000,  # Invalid negative
                'average_sales_cycle': -30  # Invalid negative
            }
        }
        
        validated = ai_service._validate_historical_analysis(invalid_historical, self.sample_lead_data)
        analysis = validated['similar_leads_analysis']
        
        # Verify corrections
        self.assertLessEqual(analysis['average_conversion_rate'], 100)
        self.assertGreaterEqual(analysis['average_deal_size'], 1000)
        self.assertGreaterEqual(analysis['average_sales_cycle'], 7)


if __name__ == '__main__':
    pytest.main([__file__])