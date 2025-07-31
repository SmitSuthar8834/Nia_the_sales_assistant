import google.generativeai as genai
from django.conf import settings
import json
import logging
import re
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from .quota_tracker import quota_tracker

logger = logging.getLogger(__name__)


@dataclass
class ContactDetails:
    """Structured contact information"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None


@dataclass
class LeadInformation:
    """Structured lead information extracted from conversation"""
    company_name: Optional[str] = None
    contact_details: ContactDetails = None
    pain_points: List[str] = None
    requirements: List[str] = None
    budget_info: Optional[str] = None
    timeline: Optional[str] = None
    decision_makers: List[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    urgency_level: Optional[str] = None
    current_solution: Optional[str] = None
    competitors_mentioned: List[str] = None
    
    def __post_init__(self):
        if self.contact_details is None:
            self.contact_details = ContactDetails()
        if self.pain_points is None:
            self.pain_points = []
        if self.requirements is None:
            self.requirements = []
        if self.decision_makers is None:
            self.decision_makers = []
        if self.competitors_mentioned is None:
            self.competitors_mentioned = []


class DataValidator:
    """Validates and cleans extracted lead data"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        if not email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format"""
        if not phone:
            return False
        # Remove common formatting characters
        cleaned = re.sub(r'[^\d+]', '', phone)
        # Check if it's a reasonable phone number length
        return 7 <= len(cleaned) <= 15
    
    @staticmethod
    def clean_company_name(company_name: str) -> Optional[str]:
        """Clean and validate company name"""
        if not company_name or company_name.lower() in ['null', 'none', 'n/a']:
            return None
        return company_name.strip()
    
    @staticmethod
    def validate_lead_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean extracted lead data"""
        validated_data = data.copy()
        
        # Validate company name
        if 'company_name' in validated_data:
            validated_data['company_name'] = DataValidator.clean_company_name(
                validated_data['company_name']
            )
        
        # Validate contact details
        if 'contact_details' in validated_data and validated_data['contact_details']:
            contact = validated_data['contact_details']
            
            # Validate email
            if 'email' in contact and contact['email']:
                if not DataValidator.validate_email(contact['email']):
                    contact['email'] = None
            
            # Validate phone
            if 'phone' in contact and contact['phone']:
                if not DataValidator.validate_phone(contact['phone']):
                    contact['phone'] = None
        
        # Clean lists - remove empty strings and duplicates
        for list_field in ['pain_points', 'requirements', 'decision_makers', 'competitors_mentioned']:
            if list_field in validated_data and isinstance(validated_data[list_field], list):
                validated_data[list_field] = list(set([
                    item.strip() for item in validated_data[list_field] 
                    if item and item.strip() and item.lower() not in ['null', 'none', 'n/a']
                ]))
        
        return validated_data


class GeminiAIService:
    """Enhanced service class for interacting with Google Gemini AI"""
    
    def __init__(self):
        """Initialize Gemini AI client with API key rotation support"""
        self.api_keys = settings.GEMINI_API_KEYS
        self.current_key_index = 0
        self.model = None
        self.validator = DataValidator()
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Gemini client with the current API key"""
        try:
            current_key = self.api_keys[self.current_key_index]
            genai.configure(api_key=current_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client with key index {self.current_key_index}: {e}")
            raise
    
    def _rotate_api_key(self):
        """Rotate to the next API key if quota is exceeded"""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            logger.info(f"Rotating to API key index {self.current_key_index}")
            self._initialize_client()
            return True
        return False
    
    def _make_api_call(self, prompt: str, max_retries: int = 2):
        """Make API call with quota tracking and automatic key rotation"""
        estimated_tokens = quota_tracker.estimate_tokens(prompt)
        
        for attempt in range(max_retries + 1):
            try:
                # Check quota before making request
                quota_check = quota_tracker.can_make_request(estimated_tokens)
                
                if not quota_check['can_request']:
                    logger.warning(f"Quota limit reached: {quota_check['reason']}")
                    
                    # Try rotating to next API key
                    if self._rotate_api_key():
                        logger.info(f"Rotated to new API key, retrying (attempt {attempt + 1})")
                        continue
                    else:
                        # No more keys to try, check if we should wait
                        wait_time = quota_check.get('wait_seconds', 60)
                        if wait_time < 300 and attempt < max_retries:  # Only wait if less than 5 minutes
                            logger.info(f"Waiting {wait_time} seconds for quota reset")
                            time.sleep(wait_time)
                            continue
                        else:
                            raise Exception(f"Quota exceeded: {quota_check['reason']}. Wait time: {wait_time} seconds")
                
                # Make the API call
                response = self.model.generate_content(prompt)
                
                # Record successful request
                actual_tokens = len(response.text) // 3 if hasattr(response, 'text') and response.text else estimated_tokens
                quota_tracker.record_request(actual_tokens)
                
                return response
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check for quota-related errors
                if 'quota' in error_msg or 'rate limit' in error_msg or 'resource_exhausted' in error_msg:
                    logger.warning(f"API quota exceeded for key index {self.current_key_index}: {e}")
                    
                    # Try rotating API key
                    if attempt < max_retries and self._rotate_api_key():
                        logger.info(f"Retrying with new API key (attempt {attempt + 1})")
                        continue
                    else:
                        logger.error("All API keys exhausted or max retries reached")
                        raise Exception("All Gemini API keys have exceeded their quota limits")
                else:
                    # For other errors, retry with exponential backoff
                    if attempt < max_retries:
                        wait_time = 2 ** attempt
                        logger.warning(f"API call failed (attempt {attempt + 1}), retrying in {wait_time} seconds: {e}")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Non-quota API error: {e}")
                        raise
        
        raise Exception("Max retries exceeded for API call")
    
    def extract_lead_info(self, conversation_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Enhanced lead information extraction from conversation transcript
        
        Args:
            conversation_text (str): The conversation transcript
            context (dict): Additional context for better extraction
            
        Returns:
            dict: Validated and structured lead information
        """
        context = context or {}
        
        # Enhanced prompt with better structure and instructions
        prompt = self._build_extraction_prompt(conversation_text, context)
        
        try:
            response = self._make_api_call(prompt)
            response_text = response.text.strip()
            
            # Clean and parse JSON response
            extracted_data = self._parse_ai_response(response_text)
            
            # Validate and clean the extracted data
            validated_data = self.validator.validate_lead_data(extracted_data)
            
            # Add extraction metadata
            validated_data['extraction_metadata'] = {
                'extraction_timestamp': None,  # Will be set by the view
                'confidence_score': self._calculate_confidence_score(validated_data),
                'data_completeness': self._calculate_data_completeness(validated_data),
                'extraction_method': 'gemini_ai_enhanced'
            }
            
            logger.info(f"Successfully extracted and validated lead info: {validated_data}")
            return validated_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini response: {e}")
            return self._get_default_lead_structure()
        except Exception as e:
            logger.error(f"Error extracting lead info: {e}")
            return self._get_default_lead_structure()
    
    def _build_extraction_prompt(self, conversation_text: str, context: Dict[str, Any]) -> str:
        """Build enhanced extraction prompt with context"""
        base_prompt = f"""
        You are an expert sales conversation analyst. Analyze the following sales conversation and extract comprehensive lead information.
        
        IMPORTANT INSTRUCTIONS:
        1. Extract only information that is explicitly mentioned or can be reasonably inferred
        2. Use null for missing information, don't make assumptions
        3. Be precise with contact details - validate email and phone formats
        4. Identify pain points as specific business challenges mentioned
        5. Requirements should be specific needs or solutions requested
        6. Pay attention to urgency indicators and decision-making authority
        
        Return the information in this EXACT JSON structure:
        {{
            "company_name": "extracted company name or null",
            "contact_details": {{
                "name": "contact person full name or null",
                "email": "valid email address or null",
                "phone": "phone number or null",
                "title": "job title or role or null",
                "department": "department or division or null"
            }},
            "pain_points": ["specific business challenges or problems mentioned"],
            "requirements": ["specific needs, solutions, or features requested"],
            "budget_info": "budget range, constraints, or approval process mentioned or null",
            "timeline": "project timeline, deadlines, or urgency mentioned or null",
            "decision_makers": ["names or roles of people involved in decision making"],
            "industry": "business sector or industry or null",
            "company_size": "number of employees, revenue, or size indicators or null",
            "urgency_level": "high|medium|low or null based on timeline and language used",
            "current_solution": "existing tools, vendors, or solutions mentioned or null",
            "competitors_mentioned": ["competitor names or alternative solutions discussed"]
        }}
        """
        
        if context:
            base_prompt += f"\n\nAdditional Context:\n{json.dumps(context, indent=2)}\n"
        
        base_prompt += f"\n\nConversation to analyze:\n{conversation_text}\n\nProvide the JSON response:"
        
        return base_prompt
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse and clean AI response to extract JSON"""
        # Remove markdown formatting
        if response_text.startswith('```json'):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith('```'):
            response_text = response_text[3:-3].strip()
        
        # Try to find JSON in the response if it's mixed with other text
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group()
        
        return json.loads(response_text)
    
    def _calculate_confidence_score(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score based on data completeness and quality"""
        score = 0.0
        max_score = 100.0
        
        # Company name (20 points)
        if data.get('company_name'):
            score += 20
        
        # Contact details (30 points total)
        contact = data.get('contact_details', {})
        if contact.get('name'):
            score += 10
        if contact.get('email'):
            score += 10
        if contact.get('phone'):
            score += 10
        
        # Pain points and requirements (30 points total)
        if data.get('pain_points'):
            score += 15
        if data.get('requirements'):
            score += 15
        
        # Additional details (20 points total)
        additional_fields = ['budget_info', 'timeline', 'industry', 'decision_makers']
        for field in additional_fields:
            if data.get(field):
                score += 5
        
        return min(score, max_score)
    
    def _calculate_data_completeness(self, data: Dict[str, Any]) -> float:
        """Calculate data completeness percentage"""
        total_fields = 11  # Total number of main fields
        filled_fields = 0
        
        main_fields = [
            'company_name', 'contact_details', 'pain_points', 'requirements',
            'budget_info', 'timeline', 'decision_makers', 'industry',
            'company_size', 'urgency_level', 'current_solution'
        ]
        
        for field in main_fields:
            if field == 'contact_details':
                contact = data.get(field, {})
                if any(contact.get(k) for k in ['name', 'email', 'phone']):
                    filled_fields += 1
            elif field in ['pain_points', 'requirements', 'decision_makers']:
                if data.get(field) and len(data[field]) > 0:
                    filled_fields += 1
            else:
                if data.get(field):
                    filled_fields += 1
        
        return (filled_fields / total_fields) * 100
    
    def generate_recommendations(self, lead_data: dict, context: dict = None) -> dict:
        """
        Generate comprehensive AI-powered sales recommendations based on lead data
        
        Args:
            lead_data (dict): Extracted lead information
            context (dict): Additional context information
            
        Returns:
            dict: Comprehensive recommendations with scoring and insights
        """
        context_info = context or {}
        
        # Enhanced prompt for comprehensive recommendations
        prompt = self._build_recommendations_prompt(lead_data, context_info)
        
        try:
            response = self._make_api_call(prompt)
            response_text = response.text.strip()
            
            # Clean up JSON formatting
            recommendations_data = self._parse_ai_response(response_text)
            
            # Add confidence scoring and ranking
            enhanced_recommendations = self._enhance_recommendations(recommendations_data, lead_data)
            
            logger.info(f"Generated enhanced recommendations: {enhanced_recommendations}")
            return enhanced_recommendations
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse recommendations JSON: {e}")
            return self._get_default_recommendations()
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return self._get_default_recommendations()
    
    def calculate_lead_quality_score(self, lead_data: dict) -> dict:
        """
        Calculate comprehensive lead quality score using AI analysis
        
        Args:
            lead_data (dict): Lead information to analyze
            
        Returns:
            dict: Lead quality analysis with score and breakdown
        """
        prompt = f"""
        Analyze this lead and provide a comprehensive quality assessment:
        
        Lead Data: {json.dumps(lead_data, indent=2)}
        
        Provide analysis in this EXACT JSON format:
        {{
            "overall_score": 85,
            "score_breakdown": {{
                "data_completeness": 90,
                "engagement_level": 80,
                "budget_fit": 85,
                "timeline_urgency": 75,
                "decision_authority": 70,
                "pain_point_severity": 95
            }},
            "quality_tier": "high|medium|low",
            "conversion_probability": 65,
            "estimated_deal_size": "$50,000 - $100,000",
            "sales_cycle_prediction": "3-6 months",
            "key_strengths": ["specific strengths identified"],
            "improvement_areas": ["areas that need more qualification"],
            "competitive_risk": "high|medium|low",
            "next_best_action": "specific recommended next step"
        }}
        
        Base scoring on: data completeness, engagement signals, budget indicators, 
        timeline urgency, decision-making authority, and pain point severity.
        """
        
        try:
            response = self._make_api_call(prompt)
            response_text = response.text.strip()
            
            quality_data = self._parse_ai_response(response_text)
            
            # Validate and enhance the quality score
            validated_quality = self._validate_quality_score(quality_data, lead_data)
            
            logger.info(f"Calculated lead quality score: {validated_quality}")
            return validated_quality
            
        except Exception as e:
            logger.error(f"Error calculating lead quality score: {e}")
            return self._get_default_quality_score()
    
    def generate_sales_strategy(self, lead_data: dict, quality_score: dict = None) -> dict:
        """
        Generate tailored sales strategy based on lead characteristics
        
        Args:
            lead_data (dict): Lead information
            quality_score (dict): Optional pre-calculated quality score
            
        Returns:
            dict: Comprehensive sales strategy recommendations
        """
        quality_info = quality_score or self.calculate_lead_quality_score(lead_data)
        
        prompt = f"""
        Create a tailored sales strategy for this lead:
        
        Lead Data: {json.dumps(lead_data, indent=2)}
        Quality Assessment: {json.dumps(quality_info, indent=2)}
        
        Provide strategy in this EXACT JSON format:
        {{
            "primary_strategy": "consultative|solution|relationship|competitive",
            "approach_rationale": "why this strategy fits this lead",
            "key_messaging": [
                "primary value proposition",
                "secondary benefits",
                "differentiation points"
            ],
            "objection_handling": {{
                "budget_concerns": "how to address budget objections",
                "timing_issues": "how to handle timing concerns",
                "competition": "how to differentiate from competitors",
                "authority": "how to reach decision makers"
            }},
            "engagement_tactics": [
                "specific tactics for this lead type",
                "communication preferences",
                "meeting/demo strategies"
            ],
            "success_metrics": [
                "how to measure progress",
                "key milestones to track"
            ],
            "risk_mitigation": [
                "potential risks and how to avoid them"
            ]
        }}
        
        Tailor strategy to the lead's industry, company size, pain points, and quality tier.
        """
        
        try:
            response = self._make_api_call(prompt)
            response_text = response.text.strip()
            
            strategy_data = self._parse_ai_response(response_text)
            
            # Add strategy confidence and ranking
            enhanced_strategy = self._enhance_strategy(strategy_data, lead_data, quality_info)
            
            logger.info(f"Generated sales strategy: {enhanced_strategy}")
            return enhanced_strategy
            
        except Exception as e:
            logger.error(f"Error generating sales strategy: {e}")
            return self._get_default_strategy()
    
    def generate_industry_insights(self, lead_data: dict) -> dict:
        """
        Generate industry-specific insights and best practices
        
        Args:
            lead_data (dict): Lead information with industry context
            
        Returns:
            dict: Industry-specific insights and recommendations
        """
        industry = lead_data.get('industry', 'General Business')
        company_size = lead_data.get('company_size', 'Unknown')
        
        prompt = f"""
        Provide industry-specific insights and best practices for this lead:
        
        Industry: {industry}
        Company Size: {company_size}
        Lead Context: {json.dumps(lead_data, indent=2)}
        
        Provide insights in this EXACT JSON format:
        {{
            "industry_trends": [
                "current trends affecting this industry",
                "market challenges and opportunities"
            ],
            "industry_pain_points": [
                "common pain points in this industry",
                "typical business challenges"
            ],
            "solution_fit": {{
                "why_relevant": "why our solution fits this industry",
                "specific_benefits": ["industry-specific benefits"],
                "use_cases": ["relevant use cases for this industry"]
            }},
            "competitive_landscape": {{
                "common_competitors": ["typical competitors in this space"],
                "differentiation_opportunities": ["how to stand out"]
            }},
            "sales_best_practices": [
                "industry-specific sales approaches",
                "communication preferences",
                "decision-making patterns"
            ],
            "compliance_considerations": [
                "regulatory or compliance factors to consider"
            ],
            "success_stories": [
                "relevant case studies or success patterns"
            ]
        }}
        
        Focus on actionable insights specific to {industry} companies of size {company_size}.
        """
        
        try:
            response = self._make_api_call(prompt)
            response_text = response.text.strip()
            
            insights_data = self._parse_ai_response(response_text)
            
            # Add confidence scoring for insights
            enhanced_insights = self._enhance_insights(insights_data, lead_data)
            
            logger.info(f"Generated industry insights: {enhanced_insights}")
            return enhanced_insights
            
        except Exception as e:
            logger.error(f"Error generating industry insights: {e}")
            return self._get_default_insights()
    
    def _build_recommendations_prompt(self, lead_data: dict, context: dict) -> str:
        """Build comprehensive recommendations prompt"""
        return f"""
        You are an expert sales strategist. Analyze this lead and provide comprehensive recommendations.
        
        Lead Information:
        {json.dumps(lead_data, indent=2)}
        
        Additional Context:
        {json.dumps(context, indent=2)}
        
        Provide recommendations in this EXACT JSON format:
        {{
            "recommendations": [
                {{
                    "type": "next_step|strategy|approach|follow_up",
                    "title": "Brief actionable title",
                    "description": "Detailed description with specific actions",
                    "priority": "high|medium|low",
                    "timeline": "immediate|1-3 days|1 week|2-4 weeks",
                    "effort_level": "low|medium|high",
                    "expected_outcome": "what this should achieve",
                    "success_metrics": "how to measure success"
                }}
            ],
            "lead_score": 85,
            "conversion_probability": 65,
            "estimated_close_timeline": "3-6 months",
            "key_insights": [
                "important insights about this lead",
                "opportunities identified",
                "potential challenges"
            ],
            "risk_factors": [
                "potential risks that could derail the deal",
                "competitive threats",
                "internal challenges"
            ],
            "opportunities": [
                "specific opportunities to pursue",
                "upsell/cross-sell potential",
                "expansion possibilities"
            ],
            "next_best_actions": [
                "top 3 immediate actions to take",
                "prioritized by impact and urgency"
            ]
        }}
        
        Focus on specific, actionable recommendations based on the lead's characteristics.
        """
    
    def _enhance_recommendations(self, recommendations: dict, lead_data: dict) -> dict:
        """Enhance recommendations with confidence scoring and ranking"""
        enhanced = recommendations.copy()
        
        # Add confidence scoring for each recommendation
        if 'recommendations' in enhanced:
            for rec in enhanced['recommendations']:
                rec['confidence_score'] = self._calculate_recommendation_confidence(rec, lead_data)
            
            # Sort recommendations by priority and confidence
            enhanced['recommendations'] = sorted(
                enhanced['recommendations'],
                key=lambda x: (
                    {'high': 3, 'medium': 2, 'low': 1}.get(x.get('priority', 'low'), 1),
                    x.get('confidence_score', 0)
                ),
                reverse=True
            )
        
        # Add overall recommendation confidence
        enhanced['recommendation_confidence'] = self._calculate_overall_confidence(enhanced, lead_data)
        
        return enhanced
    
    def _calculate_recommendation_confidence(self, recommendation: dict, lead_data: dict) -> float:
        """Calculate confidence score for individual recommendation"""
        confidence = 50.0  # Base confidence
        
        # Increase confidence based on data completeness
        completeness = self._calculate_data_completeness(lead_data)
        confidence += (completeness / 100) * 20
        
        # Adjust based on recommendation type
        rec_type = recommendation.get('type', '')
        if rec_type == 'next_step':
            confidence += 15  # Next steps are usually high confidence
        elif rec_type == 'strategy':
            confidence += 10  # Strategy recommendations are medium-high confidence
        
        # Adjust based on priority
        priority = recommendation.get('priority', 'low')
        if priority == 'high':
            confidence += 10
        elif priority == 'medium':
            confidence += 5
        
        return min(confidence, 100.0)
    
    def _calculate_overall_confidence(self, recommendations: dict, lead_data: dict) -> float:
        """Calculate overall confidence in the recommendation set"""
        base_confidence = 60.0
        
        # Factor in lead score if available
        lead_score = recommendations.get('lead_score', 50)
        base_confidence += (lead_score - 50) * 0.4
        
        # Factor in data completeness
        completeness = self._calculate_data_completeness(lead_data)
        base_confidence += (completeness / 100) * 20
        
        return min(base_confidence, 100.0)
    
    def _validate_quality_score(self, quality_data: dict, lead_data: dict) -> dict:
        """Validate and enhance quality score data"""
        validated = quality_data.copy()
        
        # Ensure score is within valid range
        if 'overall_score' in validated:
            validated['overall_score'] = max(0, min(100, validated['overall_score']))
        
        # Add validation metadata
        validated['validation_metadata'] = {
            'data_points_used': len([k for k, v in lead_data.items() if v]),
            'confidence_level': self._calculate_data_completeness(lead_data),
            'last_calculated': None  # Will be set by the view
        }
        
        return validated
    
    def _enhance_strategy(self, strategy: dict, lead_data: dict, quality_info: dict) -> dict:
        """Enhance strategy with additional metadata"""
        enhanced = strategy.copy()
        
        enhanced['strategy_metadata'] = {
            'based_on_quality_tier': quality_info.get('quality_tier', 'medium'),
            'confidence_score': self._calculate_strategy_confidence(strategy, lead_data),
            'last_generated': None  # Will be set by the view
        }
        
        return enhanced
    
    def _calculate_strategy_confidence(self, strategy: dict, lead_data: dict) -> float:
        """Calculate confidence in the generated strategy"""
        confidence = 70.0  # Base confidence for strategies
        
        # Increase confidence based on data completeness
        completeness = self._calculate_data_completeness(lead_data)
        confidence += (completeness / 100) * 20
        
        # Increase confidence if industry is specified
        if lead_data.get('industry'):
            confidence += 10
        
        return min(confidence, 100.0)
    
    def _enhance_insights(self, insights: dict, lead_data: dict) -> dict:
        """Enhance industry insights with metadata"""
        enhanced = insights.copy()
        
        enhanced['insights_metadata'] = {
            'industry_specified': bool(lead_data.get('industry')),
            'confidence_score': self._calculate_insights_confidence(insights, lead_data),
            'last_generated': None  # Will be set by the view
        }
        
        return enhanced
    
    def _calculate_insights_confidence(self, insights: dict, lead_data: dict) -> float:
        """Calculate confidence in industry insights"""
        confidence = 60.0  # Base confidence
        
        # Higher confidence if industry is clearly specified
        if lead_data.get('industry') and lead_data['industry'] != 'Unknown':
            confidence += 25
        
        # Higher confidence if company size is known
        if lead_data.get('company_size'):
            confidence += 15
        
        return min(confidence, 100.0)
    
    def _get_default_quality_score(self) -> dict:
        """Return default quality score when calculation fails"""
        return {
            "overall_score": 50,
            "score_breakdown": {
                "data_completeness": 30,
                "engagement_level": 50,
                "budget_fit": 50,
                "timeline_urgency": 50,
                "decision_authority": 50,
                "pain_point_severity": 50
            },
            "quality_tier": "medium",
            "conversion_probability": 25,
            "estimated_deal_size": "Unknown",
            "sales_cycle_prediction": "Unknown",
            "key_strengths": ["More information needed"],
            "improvement_areas": ["Gather more lead qualification data"],
            "competitive_risk": "medium",
            "next_best_action": "Schedule discovery call to gather more information",
            "validation_metadata": {
                "data_points_used": 0,
                "confidence_level": 0,
                "last_calculated": None
            }
        }
    
    def _get_default_strategy(self) -> dict:
        """Return default sales strategy when generation fails"""
        return {
            "primary_strategy": "consultative",
            "approach_rationale": "Insufficient data for specific strategy - using consultative approach",
            "key_messaging": [
                "Focus on understanding customer needs",
                "Demonstrate value through discovery",
                "Build trust through expertise"
            ],
            "objection_handling": {
                "budget_concerns": "Focus on ROI and value demonstration",
                "timing_issues": "Understand urgency drivers and create compelling events",
                "competition": "Differentiate through unique value proposition",
                "authority": "Identify and engage key decision makers"
            },
            "engagement_tactics": [
                "Schedule discovery calls",
                "Provide relevant case studies",
                "Offer value-added insights"
            ],
            "success_metrics": [
                "Meeting acceptance rate",
                "Engagement level in conversations",
                "Progression through sales stages"
            ],
            "risk_mitigation": [
                "Qualify budget and authority early",
                "Understand competitive landscape",
                "Maintain regular communication"
            ],
            "strategy_metadata": {
                "based_on_quality_tier": "medium",
                "confidence_score": 40.0,
                "last_generated": None
            }
        }
    
    def _get_default_insights(self) -> dict:
        """Return default industry insights when generation fails"""
        return {
            "industry_trends": [
                "Digital transformation continues across industries",
                "Focus on operational efficiency and cost reduction"
            ],
            "industry_pain_points": [
                "Manual processes and inefficiencies",
                "Data silos and integration challenges"
            ],
            "solution_fit": {
                "why_relevant": "Most businesses need improved efficiency and automation",
                "specific_benefits": ["Reduced manual work", "Better data insights"],
                "use_cases": ["Process automation", "Data integration"]
            },
            "competitive_landscape": {
                "common_competitors": ["Various solution providers in the market"],
                "differentiation_opportunities": ["Focus on specific customer needs"]
            },
            "sales_best_practices": [
                "Focus on business outcomes",
                "Demonstrate clear ROI",
                "Provide proof of concept opportunities"
            ],
            "compliance_considerations": [
                "Standard data privacy and security requirements"
            ],
            "success_stories": [
                "Similar companies have seen efficiency improvements",
                "ROI typically achieved within 6-12 months"
            ],
            "insights_metadata": {
                "industry_specified": False,
                "confidence_score": 30.0,
                "last_generated": None
            }
        }
    
    def test_connection(self) -> dict:
        """
        Test the connection to Gemini AI
        
        Returns:
            dict: Connection test results
        """
        try:
            response = self._make_api_call("Hello, this is a test message. Please respond with 'Connection successful'.")
            return {
                "success": True,
                "message": "Gemini AI connection successful",
                "response": response.text,
                "current_api_key_index": self.current_key_index
            }
        except Exception as e:
            logger.error(f"Gemini AI connection test failed: {e}")
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "response": None
            }
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from text using pattern matching and AI
        
        Args:
            text (str): Text to extract entities from
            
        Returns:
            dict: Dictionary of entity types and their values
        """
        entities = {
            'companies': [],
            'people': [],
            'emails': [],
            'phones': [],
            'monetary_amounts': [],
            'dates': [],
            'technologies': []
        }
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        entities['emails'] = re.findall(email_pattern, text)
        
        # Phone pattern (various formats)
        phone_pattern = r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'
        entities['phones'] = re.findall(phone_pattern, text)
        
        # Monetary amounts
        money_pattern = r'\$[\d,]+(?:\.\d{2})?|\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|USD|k|K|million|M|billion|B)\b'
        entities['monetary_amounts'] = re.findall(money_pattern, text, re.IGNORECASE)
        
        # Use AI for more complex entity extraction
        try:
            ai_entities = self._extract_entities_with_ai(text)
            for entity_type, values in ai_entities.items():
                if entity_type in entities:
                    entities[entity_type].extend(values)
                    # Remove duplicates
                    entities[entity_type] = list(set(entities[entity_type]))
        except Exception as e:
            logger.warning(f"AI entity extraction failed: {e}")
        
        return entities
    
    def _extract_entities_with_ai(self, text: str) -> Dict[str, List[str]]:
        """Use AI to extract complex entities"""
        prompt = f"""
        Extract named entities from the following text. Return as JSON:
        {{
            "companies": ["company names mentioned"],
            "people": ["person names mentioned"],
            "technologies": ["software, tools, or technologies mentioned"],
            "dates": ["dates or time references mentioned"]
        }}
        
        Text: {text}
        """
        
        response = self._make_api_call(prompt)
        response_text = response.text.strip()
        
        if response_text.startswith('```json'):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith('```'):
            response_text = response_text[3:-3].strip()
        
        return json.loads(response_text)
    
    def validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive validation of extracted lead data
        
        Args:
            data (dict): Raw extracted data
            
        Returns:
            dict: Validated data with validation results
        """
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'data_quality_score': 0.0
        }
        
        # Validate required fields
        if not data.get('company_name') and not data.get('contact_details', {}).get('name'):
            validation_results['errors'].append("Either company name or contact name is required")
            validation_results['is_valid'] = False
        
        # Validate contact details
        contact = data.get('contact_details', {})
        if contact.get('email') and not self.validator.validate_email(contact['email']):
            validation_results['errors'].append(f"Invalid email format: {contact['email']}")
            validation_results['is_valid'] = False
        
        if contact.get('phone') and not self.validator.validate_phone(contact['phone']):
            validation_results['warnings'].append(f"Phone number format may be invalid: {contact['phone']}")
        
        # Check data completeness
        completeness = self._calculate_data_completeness(data)
        if completeness < 30:
            validation_results['warnings'].append("Low data completeness - consider gathering more information")
        
        validation_results['data_quality_score'] = self._calculate_confidence_score(data)
        
        return validation_results
    
    def _get_default_lead_structure(self) -> Dict[str, Any]:
        """Return enhanced default lead structure when extraction fails"""
        return {
            "company_name": None,
            "contact_details": {
                "name": None,
                "email": None,
                "phone": None,
                "title": None,
                "department": None
            },
            "pain_points": [],
            "requirements": [],
            "budget_info": None,
            "timeline": None,
            "decision_makers": [],
            "industry": None,
            "company_size": None,
            "urgency_level": None,
            "current_solution": None,
            "competitors_mentioned": [],
            "extraction_metadata": {
                "extraction_timestamp": None,
                "confidence_score": 0.0,
                "data_completeness": 0.0,
                "extraction_method": 'default_fallback'
            }
        }
    
    def _get_default_recommendations(self) -> dict:
        """Return default recommendations when generation fails"""
        return {
            "recommendations": [
                {
                    "type": "next_step",
                    "title": "Follow up with prospect",
                    "description": "Schedule a follow-up call to gather more information",
                    "priority": "medium",
                    "timeline": "1-3 days",
                    "effort_level": "low",
                    "expected_outcome": "Gather more lead qualification data",
                    "success_metrics": "Obtain contact details and pain points",
                    "confidence_score": 70.0
                }
            ],
            "lead_score": 50,
            "conversion_probability": 25,
            "estimated_close_timeline": "Unknown",
            "key_insights": ["More information needed to provide detailed analysis"],
            "risk_factors": ["Limited information available"],
            "opportunities": ["Potential for further qualification"],
            "next_best_actions": [
                "Schedule discovery call",
                "Send follow-up email",
                "Research company background"
            ],
            "recommendation_confidence": 60.0
        }
    
    def _get_default_strategy(self) -> dict:
        """Return default sales strategy when generation fails"""
        return {
            "primary_strategy": "consultative",
            "approach_rationale": "Insufficient data requires consultative approach to gather information",
            "key_messaging": [
                "Focus on understanding business challenges",
                "Demonstrate expertise through questions",
                "Build trust through active listening"
            ],
            "objection_handling": {
                "budget_concerns": "Focus on ROI and value demonstration",
                "timing_issues": "Understand urgency drivers and create compelling timeline",
                "competition": "Differentiate through unique value proposition",
                "authority": "Identify and engage decision makers early"
            },
            "engagement_tactics": [
                "Ask open-ended discovery questions",
                "Share relevant case studies",
                "Provide educational content"
            ],
            "success_metrics": [
                "Number of pain points identified",
                "Decision maker engagement level",
                "Meeting progression rate"
            ],
            "risk_mitigation": [
                "Qualify budget early",
                "Identify all stakeholders",
                "Understand decision process"
            ],
            "strategy_metadata": {
                "based_on_quality_tier": "medium",
                "confidence_score": 60.0,
                "last_generated": None
            }
        }
    
    def _get_default_insights(self) -> dict:
        """Return default industry insights when generation fails"""
        return {
            "industry_trends": [
                "Digital transformation continues across industries",
                "Cost optimization remains a priority"
            ],
            "industry_pain_points": [
                "Operational efficiency challenges",
                "Technology integration issues"
            ],
            "solution_fit": {
                "why_relevant": "General business solutions apply across industries",
                "specific_benefits": ["Improved efficiency", "Cost reduction"],
                "use_cases": ["Process automation", "Data management"]
            },
            "competitive_landscape": {
                "common_competitors": ["Industry-standard solutions"],
                "differentiation_opportunities": ["Customization", "Support quality"]
            },
            "sales_best_practices": [
                "Focus on business outcomes",
                "Demonstrate clear ROI",
                "Build relationships with key stakeholders"
            ],
            "compliance_considerations": [
                "Data privacy regulations",
                "Industry-specific compliance requirements"
            ],
            "success_stories": [
                "Similar companies have achieved efficiency gains",
                "ROI typically realized within 6-12 months"
            ],
            "insights_metadata": {
                "industry_specified": False,
                "confidence_score": 50.0,
                "last_generated": None
            }
        }
    
    def test_connection(self) -> dict:
        """Test connection to Gemini AI service"""
        try:
            # Simple test prompt
            test_prompt = "Respond with 'Connection successful' if you can read this message."
            response = self._make_api_call(test_prompt)
            
            if response and response.text:
                return {
                    "success": True,
                    "message": "Gemini AI connection successful",
                    "model": "gemini-1.5-flash",
                    "response": response.text.strip()
                }
            else:
                return {
                    "success": False,
                    "message": "No response from Gemini AI",
                    "error": "Empty response"
                }
                
        except Exception as e:
            logger.error(f"Gemini AI connection test failed: {e}")
            return {
                "success": False,
                "message": "Gemini AI connection failed",
                "error": str(e)
            }
    
    def extract_entities(self, text: str) -> dict:
        """Extract named entities from text using Gemini AI"""
        prompt = f"""
        Extract named entities from the following text and categorize them:
        
        Text: {text}
        
        Return the entities in this JSON format:
        {{
            "people": ["person names"],
            "organizations": ["company/organization names"],
            "locations": ["places, cities, countries"],
            "products": ["product or service names"],
            "technologies": ["technology or software names"],
            "dates": ["dates and time references"],
            "money": ["monetary amounts"],
            "phone_numbers": ["phone numbers"],
            "emails": ["email addresses"]
        }}
        """
        
        try:
            response = self._make_api_call(prompt)
            response_text = response.text.strip()
            
            entities = self._parse_ai_response(response_text)
            
            # Clean and validate entities
            cleaned_entities = {}
            for category, items in entities.items():
                if isinstance(items, list):
                    cleaned_entities[category] = [
                        item.strip() for item in items 
                        if item and item.strip()
                    ]
                else:
                    cleaned_entities[category] = []
            
            return cleaned_entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {
                "people": [],
                "organizations": [],
                "locations": [],
                "products": [],
                "technologies": [],
                "dates": [],
                "money": [],
                "phone_numbers": [],
                "emails": []
            }
    
    def validate_extracted_data(self, data: dict) -> dict:
        """Validate extracted lead data and return validation results"""
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'data_quality_score': 0.0
        }
        
        # Validate required fields
        if not data.get('company_name') and not data.get('contact_details', {}).get('name'):
            validation_results['errors'].append("Either company name or contact name is required")
            validation_results['is_valid'] = False
        
        # Validate contact details
        contact = data.get('contact_details', {})
        if contact.get('email') and not self.validator.validate_email(contact['email']):
            validation_results['errors'].append(f"Invalid email format: {contact['email']}")
            validation_results['is_valid'] = False
        
        if contact.get('phone') and not self.validator.validate_phone(contact['phone']):
            validation_results['warnings'].append(f"Phone number format may be invalid: {contact['phone']}")
        
        # Check data completeness
        completeness = self._calculate_data_completeness(data)
        if completeness < 30:
            validation_results['warnings'].append("Low data completeness - consider gathering more information")
        
        validation_results['data_quality_score'] = self._calculate_confidence_score(data)
        
        return validation_results 
   
    def _generate_contextual_next_steps(self, lead_data: dict, context: dict) -> dict:
        """Generate contextual next steps based on lead data and current context"""
        current_stage = context.get('current_stage', 'prospecting')
        priority_focus = context.get('priority_focus', 'quality')
        constraints = context.get('constraints', {})
        
        prompt = f"""
        Generate specific next steps for this sales lead based on the current context:
        
        Lead Data: {json.dumps(lead_data, indent=2)}
        Current Stage: {current_stage}
        Priority Focus: {priority_focus}
        Constraints: {json.dumps(constraints, indent=2)}
        
        Provide next steps in this EXACT JSON format:
        {{
            "immediate_actions": [
                {{
                    "action": "specific action to take",
                    "timeline": "when to complete this",
                    "priority": "high|medium|low",
                    "effort": "low|medium|high",
                    "expected_outcome": "what this should achieve"
                }}
            ],
            "follow_up_sequence": [
                {{
                    "step": 1,
                    "action": "first follow-up action",
                    "timing": "when to do this",
                    "method": "email|phone|meeting|demo"
                }}
            ],
            "preparation_tasks": [
                "research tasks",
                "materials to prepare",
                "stakeholders to identify"
            ],
            "success_metrics": [
                "how to measure progress",
                "key indicators of success"
            ],
            "contingency_plans": [
                "what to do if primary approach fails",
                "alternative strategies"
            ]
        }}
        
        Tailor recommendations to the {current_stage} stage with {priority_focus} focus.
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            next_steps = self._parse_ai_response(response_text)
            
            # Add confidence scoring
            next_steps['confidence_score'] = self._calculate_next_steps_confidence(next_steps, lead_data, context)
            next_steps['generated_at'] = None  # Will be set by the view
            
            return next_steps
            
        except Exception as e:
            logger.error(f"Error generating contextual next steps: {e}")
            return self._get_default_next_steps()
    
    def _calculate_next_steps_confidence(self, next_steps: dict, lead_data: dict, context: dict) -> float:
        """Calculate confidence score for next steps recommendations"""
        confidence = 60.0  # Base confidence
        
        # Increase confidence based on data completeness
        completeness = self._calculate_data_completeness(lead_data)
        confidence += (completeness / 100) * 20
        
        # Increase confidence if stage is specified
        if context.get('current_stage') and context['current_stage'] != 'unknown':
            confidence += 10
        
        # Increase confidence if constraints are provided
        if context.get('constraints'):
            confidence += 10
        
        return min(confidence, 100.0)
    
    def _get_default_next_steps(self) -> dict:
        """Return default next steps when generation fails"""
        return {
            "immediate_actions": [
                {
                    "action": "Schedule follow-up call with prospect",
                    "timeline": "within 2-3 business days",
                    "priority": "high",
                    "effort": "low",
                    "expected_outcome": "Maintain engagement and gather more information"
                }
            ],
            "follow_up_sequence": [
                {
                    "step": 1,
                    "action": "Send personalized follow-up email",
                    "timing": "within 24 hours",
                    "method": "email"
                },
                {
                    "step": 2,
                    "action": "Make follow-up phone call",
                    "timing": "2-3 days after email",
                    "method": "phone"
                }
            ],
            "preparation_tasks": [
                "Research company background and recent news",
                "Prepare relevant case studies",
                "Identify key stakeholders"
            ],
            "success_metrics": [
                "Response rate to follow-up communications",
                "Meeting acceptance rate",
                "Information gathered per interaction"
            ],
            "contingency_plans": [
                "If no response, try different communication channel",
                "If not interested, ask for referrals",
                "If timing is bad, schedule future follow-up"
            ],
            "confidence_score": 50.0,
            "generated_at": None
        }