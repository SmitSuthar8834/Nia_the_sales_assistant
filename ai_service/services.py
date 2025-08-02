import google.generativeai as genai
from django.conf import settings
import json
import logging
import re
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from .quota_tracker import quota_tracker
from .ai_context_guidelines import (
    SALES_CONTEXT, AI_GUIDELINES, PROMPT_TEMPLATES,
    get_context_for_industry, get_confidence_guidelines,
    get_objection_handling_strategies, get_recommendation_guidelines,
    build_context_prompt
)
from .ai_config import (
    get_company_config, get_sales_methodology, get_ai_behavior_config,
    get_industry_config, get_scoring_config
)

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
        # Get industry-specific context
        industry = lead_data.get('industry', 'technology')
        industry_context = get_context_for_industry(industry)
        confidence_guidelines = get_confidence_guidelines()
        
        # Build context-aware prompt
        base_prompt = build_context_prompt('lead_quality_score', {
            'industry': industry,
            'company_size': lead_data.get('company_size', 'Unknown'),
            'typical_sales_cycle': industry_context.get('typical_sales_cycle', '3-6 months')
        })
        
        prompt = f"""
        {base_prompt}
        
        Lead Data to Analyze: {json.dumps(lead_data, indent=2)}
        
        Industry Context:
        - Common pain points: {', '.join(industry_context.get('common_pain_points', []))}
        - Typical decision makers: {', '.join(industry_context.get('decision_makers', []))}
        - Sales approach: {industry_context.get('sales_approach', 'Consultative')}
        - Typical sales cycle: {industry_context.get('typical_sales_cycle', '3-6 months')}
        
        Confidence Scoring Guidelines:
        High confidence indicators: {', '.join(confidence_guidelines['high_confidence_indicators'])}
        Medium confidence indicators: {', '.join(confidence_guidelines['medium_confidence_indicators'])}
        Low confidence indicators: {', '.join(confidence_guidelines['low_confidence_indicators'])}
        
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
        
        Base your analysis on our company's strengths and the specific industry context provided.
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
        
        # Get industry-specific context and objection handling strategies
        industry = lead_data.get('industry', 'technology')
        industry_context = get_context_for_industry(industry)
        objection_strategies = get_objection_handling_strategies()
        
        # Build context-aware prompt
        base_prompt = build_context_prompt('sales_strategy', {
            'industry': industry,
            'quality_tier': quality_info.get('quality_tier', 'medium'),
            'company_size': lead_data.get('company_size', 'Unknown')
        })
        
        prompt = f"""
        {base_prompt}
        
        Lead Data: {json.dumps(lead_data, indent=2)}
        Quality Assessment: {json.dumps(quality_info, indent=2)}
        
        Industry-Specific Context:
        - Key messaging themes: {', '.join(industry_context.get('key_messaging', []))}
        - Decision makers: {', '.join(industry_context.get('decision_makers', []))}
        - Sales approach: {industry_context.get('sales_approach', 'Consultative')}
        - Common pain points: {', '.join(industry_context.get('common_pain_points', []))}
        
        Objection Handling Strategies:
        Budget concerns: {', '.join(objection_strategies['budget_concerns']['strategies'])}
        Timing concerns: {', '.join(objection_strategies['timing_concerns']['strategies'])}
        Authority concerns: {', '.join(objection_strategies['authority_concerns']['strategies'])}
        Competition concerns: {', '.join(objection_strategies['competition_concerns']['strategies'])}
        
        Provide strategy in this EXACT JSON format:
        {{
            "primary_strategy": "consultative|solution|relationship|competitive",
            "approach_rationale": "why this strategy fits this lead based on our methodology",
            "key_messaging": [
                "primary value proposition aligned with our differentiators",
                "secondary benefits specific to their industry",
                "differentiation points vs competitors"
            ],
            "objection_handling": {{
                "budget_concerns": "specific approach based on our proven strategies",
                "timing_issues": "how to create urgency and compelling events",
                "competition": "how to differentiate using our unique advantages",
                "authority": "how to reach and influence decision makers"
            }},
            "engagement_tactics": [
                "specific tactics for this lead type and industry",
                "communication preferences and channels",
                "meeting/demo strategies that work for this industry"
            ],
            "success_metrics": [
                "how to measure progress through our sales stages",
                "key milestones and conversion indicators"
            ],
            "risk_mitigation": [
                "potential risks specific to this industry and lead type",
                "proactive strategies to avoid common pitfalls"
            ]
        }}
        
        Align strategy with our consultative selling methodology and company strengths.
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
        
        # Get comprehensive industry context
        industry_context = get_context_for_industry(industry)
        
        # Build context-aware prompt
        base_prompt = build_context_prompt('industry_insights', {
            'industry': industry,
            'company_size': company_size,
            'target_market': SALES_CONTEXT['company_profile']['target_market']
        })
        
        prompt = f"""
        {base_prompt}
        
        Industry: {industry}
        Company Size: {company_size}
        Lead Context: {json.dumps(lead_data, indent=2)}
        
        Our Company Strengths for This Industry:
        {chr(10).join(f"- {advantage}" for advantage in SALES_CONTEXT['company_profile']['competitive_advantages'])}
        
        Industry Knowledge Base:
        - Common pain points: {', '.join(industry_context.get('common_pain_points', []))}
        - Typical decision makers: {', '.join(industry_context.get('decision_makers', []))}
        - Recommended sales approach: {industry_context.get('sales_approach', 'Consultative')}
        - Typical sales cycle: {industry_context.get('typical_sales_cycle', '3-6 months')}
        - Key messaging themes: {', '.join(industry_context.get('key_messaging', []))}
        
        Provide insights in this EXACT JSON format:
        {{
            "industry_trends": [
                "current trends affecting {industry}",
                "market challenges and digital transformation opportunities"
            ],
            "industry_pain_points": [
                "common pain points specific to {industry}",
                "business challenges our solution addresses"
            ],
            "solution_fit": {{
                "why_relevant": "why our AI-powered sales solution fits {industry}",
                "specific_benefits": ["benefits aligned with our competitive advantages"],
                "use_cases": ["relevant use cases showcasing our strengths"]
            }},
            "competitive_landscape": {{
                "common_competitors": ["typical competitors in {industry} sales tech space"],
                "differentiation_opportunities": ["how our unique advantages create competitive edge"]
            }},
            "sales_best_practices": [
                "industry-specific sales approaches that work for {industry}",
                "communication preferences and decision-making patterns",
                "proven strategies for {company_size} companies"
            ],
            "compliance_considerations": [
                "regulatory or compliance factors relevant to {industry}",
                "data privacy and security requirements"
            ],
            "success_stories": [
                "relevant case studies or success patterns for similar companies",
                "ROI examples and implementation timelines"
            ]
        }}
        
        Focus on actionable insights that leverage our company's strengths and address specific {industry} needs.
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
        """Build comprehensive recommendations prompt with context guidelines"""
        industry = lead_data.get('industry', 'technology')
        industry_context = get_context_for_industry(industry)
        recommendation_guidelines = get_recommendation_guidelines()
        
        # Build context-aware prompt
        base_prompt = build_context_prompt('recommendations', {
            'industry': industry,
            'company_size': lead_data.get('company_size', 'Unknown'),
            'urgency_level': lead_data.get('urgency_level', 'medium')
        })
        
        return f"""
        {base_prompt}
        
        Lead Information:
        {json.dumps(lead_data, indent=2)}
        
        Additional Context:
        {json.dumps(context, indent=2)}
        
        Industry-Specific Guidelines:
        - Decision makers: {', '.join(industry_context.get('decision_makers', []))}
        - Sales approach: {industry_context.get('sales_approach', 'Consultative')}
        - Typical sales cycle: {industry_context.get('typical_sales_cycle', '3-6 months')}
        
        Recommendation Framework:
        Immediate actions: {', '.join(recommendation_guidelines['next_steps']['immediate_actions'])}
        Short-term actions: {', '.join(recommendation_guidelines['next_steps']['short_term_actions'])}
        High priority focus: {', '.join(recommendation_guidelines['priority_matrix']['high_priority'])}
        
        Our Company Differentiators to Emphasize:
        {chr(10).join(f"- {advantage}" for advantage in SALES_CONTEXT['company_profile']['competitive_advantages'])}
        
        Provide recommendations in this EXACT JSON format:
        {{
            "recommendations": [
                {{
                    "type": "next_step|strategy|approach|follow_up",
                    "title": "Brief actionable title aligned with our methodology",
                    "description": "Detailed description with specific actions leveraging our strengths",
                    "priority": "high|medium|low",
                    "timeline": "immediate|1-3 days|1 week|2-4 weeks",
                    "effort_level": "low|medium|high",
                    "expected_outcome": "what this should achieve for our sales process",
                    "success_metrics": "how to measure success using our KPIs"
                }}
            ],
            "lead_score": 85,
            "conversion_probability": 65,
            "estimated_close_timeline": "based on industry typical cycle",
            "key_insights": [
                "important insights about this lead's fit with our solution",
                "opportunities to leverage our competitive advantages",
                "potential challenges and how to address them"
            ],
            "risk_factors": [
                "potential risks specific to this industry and lead type",
                "competitive threats and mitigation strategies",
                "internal challenges and resource requirements"
            ],
            "opportunities": [
                "specific opportunities to showcase our differentiators",
                "upsell/cross-sell potential based on our product suite",
                "expansion possibilities and strategic partnerships"
            ],
            "next_best_actions": [
                "top 3 immediate actions prioritized by our sales methodology",
                "actions that advance through our defined sales stages"
            ]
        }}
        
        Align all recommendations with our consultative selling approach and company strengths.
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
            'phone_numbers': [],  # Alias for phones for backward compatibility
            'monetary_amounts': [],
            'dates': [],
            'technologies': []
        }
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        entities['emails'] = re.findall(email_pattern, text)
        
        # Phone pattern (various formats)
        phone_pattern = r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'
        phone_numbers = re.findall(phone_pattern, text)
        entities['phones'] = phone_numbers
        entities['phone_numbers'] = phone_numbers  # Alias for backward compatibility
        
        # Monetary amounts
        money_pattern = r'\$[\d,]+(?:\.\d{2})?|\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|USD|k|K|million|M|billion|B)\b'
        entities['monetary_amounts'] = re.findall(money_pattern, text, re.IGNORECASE)
        
        # Use AI for more complex entity extraction (with fallback for quota issues)
        ai_extraction_successful = False
        try:
            ai_entities = self._extract_entities_with_ai(text)
            for entity_type, values in ai_entities.items():
                if entity_type in entities:
                    entities[entity_type].extend(values)
                    # Remove duplicates
                    entities[entity_type] = list(set(entities[entity_type]))
            ai_extraction_successful = True
        except Exception as e:
            logger.warning(f"AI entity extraction failed, using pattern matching only: {e}")
        
        # Always run pattern matching as fallback or supplement
        self._extract_entities_with_patterns(text, entities)
        
        # Ensure all keys have unique values and remove empty strings
        for key in entities:
            entities[key] = list(set([item for item in entities[key] if item and item.strip()]))
        
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
    
    def _extract_entities_with_patterns(self, text: str, entities: Dict[str, List[str]]) -> None:
        """Fallback pattern-based entity extraction when AI is unavailable"""
        # Basic company patterns - look for company suffixes and extract the company name
        company_suffixes = ['Corp', 'Corporation', 'Inc', 'Incorporated', 'LLC', 'Ltd', 'Limited', 'Company', 'Co']
        
        # Find all potential company mentions
        for suffix in company_suffixes:
            # Pattern to find "Word Word Suffix" format
            pattern = rf'\b([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*)\s+{re.escape(suffix)}\.?\b'
            matches = re.findall(pattern, text)
            for match in matches:
                # Clean up and validate the company name
                company_name = f"{match.strip()} {suffix}"
                if len(company_name.split()) <= 4:  # Reasonable company name length
                    entities['companies'].append(company_name)
        
        # Basic person name patterns (Title + Name)
        name_pattern = r'\b(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Prof\.?)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        people = re.findall(name_pattern, text)
        entities['people'].extend(people)
        
        # Common technology terms
        tech_keywords = ['CRM', 'ERP', 'API', 'SaaS', 'cloud', 'software', 'platform', 'system', 'database', 'analytics']
        for keyword in tech_keywords:
            if keyword.lower() in text.lower():
                entities['technologies'].append(keyword)
        
        # Basic date patterns
        date_pattern = r'\b(?:Q[1-4]\s+\d{4}|\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}|January|February|March|April|May|June|July|August|September|October|November|December)\b'
        dates = re.findall(date_pattern, text, re.IGNORECASE)
        entities['dates'].extend(dates)
        
        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))
    
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
    
    def analyze_opportunity_conversion_potential(self, lead_data: dict, historical_data: dict = None) -> dict:
        """
        Analyze lead-to-opportunity conversion probability and readiness
        
        Args:
            lead_data (dict): Lead information to analyze
            historical_data (dict): Historical conversion data for context
            
        Returns:
            dict: Comprehensive conversion analysis with probability and recommendations
        """
        historical_context = historical_data or {}
        
        # Build context-aware prompt for conversion analysis
        prompt = f"""
        You are an expert sales conversion analyst. Analyze this lead's potential for conversion to a sales opportunity.
        
        ANALYSIS FRAMEWORK:
        1. Evaluate conversion readiness based on BANT criteria (Budget, Authority, Need, Timeline)
        2. Assess engagement level and buying signals
        3. Consider competitive landscape and urgency factors
        4. Analyze data completeness and qualification level
        
        Lead Data: {json.dumps(lead_data, indent=2)}
        
        Historical Context:
        - Average conversion rate: {historical_context.get('avg_conversion_rate', 25)}%
        - Typical sales cycle: {historical_context.get('avg_sales_cycle', '3-6 months')}
        - Similar industry conversion rate: {historical_context.get('industry_conversion_rate', 30)}%
        
        Provide analysis in this EXACT JSON format:
        {{
            "conversion_probability": 75,
            "conversion_confidence": 85,
            "conversion_readiness_score": 80,
            "readiness_factors": [
                "Clear budget authority identified",
                "Specific timeline mentioned",
                "Pain points align with our solution"
            ],
            "blocking_factors": [
                "Decision maker not yet identified",
                "Budget approval process unclear"
            ],
            "recommended_for_conversion": true,
            "conversion_timeline": "2-4 weeks",
            "required_actions_before_conversion": [
                "Qualify budget range and approval process",
                "Identify and engage key decision makers",
                "Conduct needs assessment call"
            ],
            "conversion_triggers": [
                "Budget approval received",
                "Technical requirements confirmed",
                "Timeline urgency increases"
            ],
            "risk_factors": [
                "Competitive evaluation in progress",
                "Budget cycle timing uncertainty"
            ],
            "success_indicators": [
                "Multiple stakeholder engagement",
                "Technical evaluation requested",
                "Reference requests made"
            ]
        }}
        
        Base your analysis on proven sales conversion methodologies and the specific lead characteristics provided.
        """
        
        try:
            response = self._make_api_call(prompt)
            response_text = response.text.strip()
            
            conversion_data = self._parse_ai_response(response_text)
            
            # Validate and enhance conversion analysis
            validated_conversion = self._validate_conversion_analysis(conversion_data, lead_data)
            
            logger.info(f"Analyzed opportunity conversion potential: {validated_conversion}")
            return validated_conversion
            
        except Exception as e:
            logger.error(f"Error analyzing opportunity conversion potential: {e}")
            return self._get_default_conversion_analysis()
    
    def predict_deal_size_and_timeline(self, lead_data: dict, opportunity_data: dict = None) -> dict:
        """
        Predict deal size range and sales timeline based on lead characteristics
        
        Args:
            lead_data (dict): Lead information
            opportunity_data (dict): Optional existing opportunity data
            
        Returns:
            dict: Deal size and timeline predictions with confidence intervals
        """
        opportunity_context = opportunity_data or {}
        industry = lead_data.get('industry', 'technology')
        company_size = lead_data.get('company_size', 'Unknown')
        
        # Get industry-specific context for deal sizing
        industry_context = get_context_for_industry(industry)
        
        prompt = f"""
        You are an expert sales forecasting analyst. Predict the deal size and sales timeline for this opportunity.
        
        PREDICTION FRAMEWORK:
        1. Analyze company size, industry, and budget indicators
        2. Consider pain point severity and solution scope
        3. Factor in competitive landscape and urgency
        4. Apply industry benchmarks and historical patterns
        
        Lead Information: {json.dumps(lead_data, indent=2)}
        Opportunity Context: {json.dumps(opportunity_context, indent=2)}
        
        Industry Benchmarks:
        - Industry: {industry}
        - Typical deal size range: {industry_context.get('typical_deal_size', '$25K-$100K')}
        - Average sales cycle: {industry_context.get('typical_sales_cycle', '3-6 months')}
        - Decision complexity: {industry_context.get('decision_complexity', 'Medium')}
        
        Company Size Context:
        - Size indicator: {company_size}
        - Budget implications: Consider enterprise vs SMB budget patterns
        
        Provide predictions in this EXACT JSON format:
        {{
            "deal_size_prediction": {{
                "minimum_value": 25000,
                "maximum_value": 75000,
                "most_likely_value": 50000,
                "confidence_level": 75,
                "sizing_rationale": "Based on company size, pain point severity, and industry benchmarks"
            }},
            "timeline_prediction": {{
                "minimum_days": 60,
                "maximum_days": 180,
                "most_likely_days": 120,
                "confidence_level": 80,
                "timeline_rationale": "Considering decision complexity and typical industry sales cycles"
            }},
            "deal_size_factors": [
                "Company size indicates mid-market budget capacity",
                "Multiple pain points suggest comprehensive solution need",
                "Industry standards support premium pricing"
            ],
            "timeline_factors": [
                "Decision maker authority level affects approval speed",
                "Technical evaluation requirements extend timeline",
                "Budget cycle timing influences close date"
            ],
            "accelerating_factors": [
                "Urgent business need creates timeline pressure",
                "Existing vendor contract expiration",
                "Regulatory compliance deadline"
            ],
            "risk_factors": [
                "Budget approval process complexity",
                "Multiple stakeholder consensus required",
                "Competitive evaluation timeline"
            ],
            "benchmarking_data": {{
                "industry_average_deal_size": 45000,
                "industry_average_sales_cycle": 105,
                "similar_company_patterns": "Mid-market companies typically close 30% faster with clear ROI"
            }}
        }}
        
        Base predictions on realistic market conditions and proven sales patterns.
        """
        
        try:
            response = self._make_api_call(prompt)
            response_text = response.text.strip()
            
            prediction_data = self._parse_ai_response(response_text)
            
            # Validate and enhance predictions
            validated_predictions = self._validate_deal_predictions(prediction_data, lead_data)
            
            logger.info(f"Predicted deal size and timeline: {validated_predictions}")
            return validated_predictions
            
        except Exception as e:
            logger.error(f"Error predicting deal size and timeline: {e}")
            return self._get_default_deal_predictions()
    
    def recommend_sales_stage(self, lead_data: dict, opportunity_data: dict, current_stage: str = None) -> dict:
        """
        Recommend appropriate sales stage based on opportunity characteristics and progress
        
        Args:
            lead_data (dict): Original lead information
            opportunity_data (dict): Current opportunity data
            current_stage (str): Current sales stage
            
        Returns:
            dict: Stage recommendations with advancement probability and timeline
        """
        current_stage = current_stage or opportunity_data.get('stage', 'prospecting')
        
        # Define sales stage progression framework
        stage_framework = {
            'prospecting': {
                'next_stage': 'qualification',
                'requirements': ['Initial contact made', 'Basic need identified', 'Contact information confirmed']
            },
            'qualification': {
                'next_stage': 'proposal',
                'requirements': ['BANT criteria assessed', 'Decision makers identified', 'Budget range confirmed']
            },
            'proposal': {
                'next_stage': 'negotiation',
                'requirements': ['Formal proposal submitted', 'Technical requirements confirmed', 'Pricing discussed']
            },
            'negotiation': {
                'next_stage': 'closed_won',
                'requirements': ['Terms negotiated', 'Contract reviewed', 'Final approvals pending']
            }
        }
        
        prompt = f"""
        You are an expert sales stage analyst. Recommend the appropriate sales stage and advancement strategy.
        
        STAGE ANALYSIS FRAMEWORK:
        1. Evaluate current qualification level against stage requirements
        2. Assess readiness for stage advancement
        3. Identify gaps that need addressing
        4. Predict advancement probability and timeline
        
        Current Stage: {current_stage}
        Lead Data: {json.dumps(lead_data, indent=2)}
        Opportunity Data: {json.dumps(opportunity_data, indent=2)}
        
        Stage Framework: {json.dumps(stage_framework, indent=2)}
        
        Provide recommendations in this EXACT JSON format:
        {{
            "current_stage_assessment": {{
                "recommended_stage": "qualification",
                "stage_confidence": 85,
                "stage_rationale": "Lead shows clear qualification criteria but needs budget confirmation"
            }},
            "advancement_analysis": {{
                "next_stage": "proposal",
                "advancement_probability": 70,
                "advancement_timeline": "2-3 weeks",
                "advancement_confidence": 75
            }},
            "stage_requirements_met": [
                "Initial contact established",
                "Basic needs identified",
                "Pain points confirmed"
            ],
            "stage_requirements_missing": [
                "Budget authority not confirmed",
                "Decision timeline unclear",
                "Technical requirements not detailed"
            ],
            "advancement_actions": [
                "Schedule budget qualification call",
                "Identify and engage decision makers",
                "Conduct technical needs assessment"
            ],
            "stage_risks": [
                "Budget approval process may be complex",
                "Multiple stakeholders not yet engaged",
                "Competitive evaluation possible"
            ],
            "success_metrics": [
                "Budget range confirmed within 2 weeks",
                "Decision maker meeting scheduled",
                "Technical requirements documented"
            ],
            "fallback_strategies": [
                "If budget unclear, focus on ROI demonstration",
                "If decision makers unavailable, work through champion",
                "If timeline uncertain, create urgency through limited-time offers"
            ]
        }}
        
        Base recommendations on proven sales methodology and realistic progression timelines.
        """
        
        try:
            response = self._make_api_call(prompt)
            response_text = response.text.strip()
            
            stage_data = self._parse_ai_response(response_text)
            
            # Validate and enhance stage recommendations
            validated_stage = self._validate_stage_recommendations(stage_data, opportunity_data)
            
            logger.info(f"Recommended sales stage: {validated_stage}")
            return validated_stage
            
        except Exception as e:
            logger.error(f"Error recommending sales stage: {e}")
            return self._get_default_stage_recommendations()
    
    def identify_risk_factors_and_mitigation(self, lead_data: dict, opportunity_data: dict, historical_data: dict = None) -> dict:
        """
        Identify potential risk factors and suggest mitigation strategies
        
        Args:
            lead_data (dict): Lead information
            opportunity_data (dict): Opportunity details
            historical_data (dict): Historical risk patterns
            
        Returns:
            dict: Risk analysis with mitigation strategies and monitoring recommendations
        """
        historical_context = historical_data or {}
        
        prompt = f"""
        You are an expert sales risk analyst. Identify potential risks and provide mitigation strategies for this opportunity.
        
        RISK ANALYSIS FRAMEWORK:
        1. Competitive risks and market threats
        2. Internal capability and resource risks
        3. Customer-side risks (budget, authority, timeline)
        4. Technical and implementation risks
        5. Relationship and communication risks
        
        Lead Data: {json.dumps(lead_data, indent=2)}
        Opportunity Data: {json.dumps(opportunity_data, indent=2)}
        
        Historical Risk Patterns:
        - Common loss reasons: {historical_context.get('common_loss_reasons', ['Price', 'Timeline', 'Features'])}
        - Risk indicators: {historical_context.get('risk_indicators', ['Long sales cycles', 'Multiple vendors', 'Budget delays'])}
        
        Provide analysis in this EXACT JSON format:
        {{
            "overall_risk_assessment": {{
                "risk_level": "medium",
                "risk_score": 45,
                "confidence": 80,
                "primary_risk_category": "competitive"
            }},
            "identified_risks": [
                {{
                    "risk_type": "competitive",
                    "risk_description": "Multiple vendor evaluation in progress",
                    "probability": 60,
                    "impact": "high",
                    "risk_score": 75,
                    "indicators": ["Competitor mentions", "Evaluation timeline", "Feature comparisons"]
                }},
                {{
                    "risk_type": "budget",
                    "risk_description": "Budget approval process unclear",
                    "probability": 40,
                    "impact": "high",
                    "risk_score": 60,
                    "indicators": ["No budget range provided", "Multiple approvers mentioned"]
                }}
            ],
            "mitigation_strategies": [
                {{
                    "risk_type": "competitive",
                    "strategies": [
                        "Emphasize unique differentiators early in process",
                        "Build strong champion relationships",
                        "Provide superior proof of concept"
                    ],
                    "timeline": "immediate",
                    "resources_required": ["Sales engineer", "Reference customers", "Executive sponsor"]
                }},
                {{
                    "risk_type": "budget",
                    "strategies": [
                        "Conduct thorough budget qualification",
                        "Provide ROI analysis and business case",
                        "Identify budget approval process and timeline"
                    ],
                    "timeline": "within 2 weeks",
                    "resources_required": ["Financial analyst", "ROI calculator", "Executive presentation"]
                }}
            ],
            "monitoring_recommendations": [
                "Weekly competitive intelligence updates",
                "Budget approval milestone tracking",
                "Stakeholder engagement frequency monitoring"
            ],
            "early_warning_indicators": [
                "Delayed responses to proposals",
                "Reduced stakeholder engagement",
                "New competitor mentions",
                "Budget cycle changes"
            ],
            "contingency_plans": [
                "If competitive threat increases: Accelerate decision timeline",
                "If budget issues arise: Explore phased implementation",
                "If timeline delays: Maintain engagement with value-add activities"
            ]
        }}
        
        Focus on actionable risks with specific mitigation strategies and clear monitoring criteria.
        """
        
        try:
            response = self._make_api_call(prompt)
            response_text = response.text.strip()
            
            risk_data = self._parse_ai_response(response_text)
            
            # Validate and enhance risk analysis
            validated_risks = self._validate_risk_analysis(risk_data, opportunity_data)
            
            logger.info(f"Identified risks and mitigation strategies: {validated_risks}")
            return validated_risks
            
        except Exception as e:
            logger.error(f"Error identifying risk factors: {e}")
            return self._get_default_risk_analysis()
    
    def analyze_historical_patterns(self, lead_data: dict, user_id: str = None) -> dict:
        """
        Analyze historical data patterns to improve predictions
        
        Args:
            lead_data (dict): Current lead data for comparison
            user_id (str): User ID for personalized historical analysis
            
        Returns:
            dict: Historical pattern analysis with benchmarks and insights
        """
        # This would typically query historical data from the database
        # For now, we'll simulate with AI analysis of provided patterns
        
        prompt = f"""
        You are an expert sales data analyst. Analyze historical patterns to provide insights for this lead.
        
        HISTORICAL ANALYSIS FRAMEWORK:
        1. Similar lead characteristics and outcomes
        2. Industry-specific conversion patterns
        3. Seasonal and timing factors
        4. Sales methodology effectiveness
        5. Resource allocation optimization
        
        Current Lead Profile: {json.dumps(lead_data, indent=2)}
        
        Analyze patterns and provide insights in this EXACT JSON format:
        {{
            "similar_leads_analysis": {{
                "similar_leads_count": 25,
                "average_conversion_rate": 35,
                "average_deal_size": 45000,
                "average_sales_cycle": 95,
                "success_factors": [
                    "Early technical evaluation",
                    "Executive sponsor engagement",
                    "Clear ROI demonstration"
                ]
            }},
            "industry_benchmarks": {{
                "industry_conversion_rate": 28,
                "industry_average_deal_size": 52000,
                "industry_sales_cycle": 120,
                "competitive_win_rate": 42,
                "seasonal_patterns": "Q4 budget flush increases close rates by 15%"
            }},
            "predictive_insights": [
                "Leads with similar pain points convert 40% higher than average",
                "Company size indicates 25% higher deal value potential",
                "Industry timing suggests 20% faster sales cycle possible"
            ],
            "optimization_recommendations": [
                "Allocate senior sales engineer for technical evaluation",
                "Schedule executive briefing within first 2 weeks",
                "Prepare industry-specific ROI calculator"
            ],
            "success_probability_factors": {{
                "positive_indicators": [
                    "Pain point severity matches our strength areas",
                    "Company growth stage aligns with expansion needs",
                    "Budget cycle timing favorable"
                ],
                "negative_indicators": [
                    "Competitive landscape more crowded than average",
                    "Decision complexity higher than typical"
                ],
                "neutral_factors": [
                    "Geographic location shows average performance",
                    "Contact seniority level typical for industry"
                ]
            }},
            "resource_allocation_guidance": {{
                "recommended_investment_level": "high",
                "key_resources_needed": ["Senior AE", "Sales engineer", "Executive sponsor"],
                "timeline_priorities": ["Technical proof within 3 weeks", "Executive meeting within 4 weeks"],
                "success_metrics": ["Technical approval", "Budget confirmation", "Timeline agreement"]
            }}
        }}
        
        Base analysis on realistic historical patterns and proven sales methodologies.
        """
        
        try:
            response = self._make_api_call(prompt)
            response_text = response.text.strip()
            
            historical_data = self._parse_ai_response(response_text)
            
            # Validate and enhance historical analysis
            validated_historical = self._validate_historical_analysis(historical_data, lead_data)
            
            logger.info(f"Analyzed historical patterns: {validated_historical}")
            return validated_historical
            
        except Exception as e:
            logger.error(f"Error analyzing historical patterns: {e}")
            return self._get_default_historical_analysis()
    
    # Validation and default methods for opportunity conversion intelligence
    
    def _validate_conversion_analysis(self, data: dict, lead_data: dict) -> dict:
        """Validate and enhance conversion analysis data"""
        validated = data.copy()
        
        # Ensure probability is within valid range
        validated['conversion_probability'] = max(0, min(100, validated.get('conversion_probability', 50)))
        validated['conversion_confidence'] = max(0, min(100, validated.get('conversion_confidence', 70)))
        
        # Ensure required fields exist
        validated.setdefault('readiness_factors', [])
        validated.setdefault('blocking_factors', [])
        validated.setdefault('required_actions_before_conversion', [])
        
        # Set default conversion recommendation based on probability
        if 'recommended_for_conversion' not in validated:
            validated['recommended_for_conversion'] = validated['conversion_probability'] >= 60
        
        return validated
    
    def _validate_deal_predictions(self, data: dict, lead_data: dict) -> dict:
        """Validate and enhance deal prediction data"""
        validated = data.copy()
        
        # Validate deal size prediction structure
        if 'deal_size_prediction' in validated:
            deal_size = validated['deal_size_prediction']
            deal_size['minimum_value'] = max(1000, deal_size.get('minimum_value', 10000))
            deal_size['maximum_value'] = max(deal_size['minimum_value'], deal_size.get('maximum_value', 50000))
            deal_size['most_likely_value'] = max(deal_size['minimum_value'], 
                                               min(deal_size['maximum_value'], 
                                                   deal_size.get('most_likely_value', 25000)))
        
        # Validate timeline prediction structure
        if 'timeline_prediction' in validated:
            timeline = validated['timeline_prediction']
            timeline['minimum_days'] = max(7, timeline.get('minimum_days', 30))
            timeline['maximum_days'] = max(timeline['minimum_days'], timeline.get('maximum_days', 180))
            timeline['most_likely_days'] = max(timeline['minimum_days'],
                                             min(timeline['maximum_days'],
                                                 timeline.get('most_likely_days', 90)))
        
        return validated
    
    def _validate_stage_recommendations(self, data: dict, opportunity_data: dict) -> dict:
        """Validate and enhance stage recommendation data"""
        validated = data.copy()
        
        # Ensure advancement probability is valid
        if 'advancement_analysis' in validated:
            advancement = validated['advancement_analysis']
            advancement['advancement_probability'] = max(0, min(100, advancement.get('advancement_probability', 50)))
        
        # Ensure required lists exist
        validated.setdefault('stage_requirements_met', [])
        validated.setdefault('stage_requirements_missing', [])
        validated.setdefault('advancement_actions', [])
        
        return validated
    
    def _validate_risk_analysis(self, data: dict, opportunity_data: dict) -> dict:
        """Validate and enhance risk analysis data"""
        validated = data.copy()
        
        # Ensure risk score is valid
        if 'overall_risk_assessment' in validated:
            risk_assessment = validated['overall_risk_assessment']
            risk_assessment['risk_score'] = max(0, min(100, risk_assessment.get('risk_score', 50)))
        
        # Ensure required structures exist
        validated.setdefault('identified_risks', [])
        validated.setdefault('mitigation_strategies', [])
        validated.setdefault('monitoring_recommendations', [])
        
        return validated
    
    def _validate_historical_analysis(self, data: dict, lead_data: dict) -> dict:
        """Validate and enhance historical analysis data"""
        validated = data.copy()
        
        # Ensure similar leads analysis has valid numbers
        if 'similar_leads_analysis' in validated:
            similar = validated['similar_leads_analysis']
            similar['average_conversion_rate'] = max(0, min(100, similar.get('average_conversion_rate', 25)))
            similar['average_deal_size'] = max(1000, similar.get('average_deal_size', 25000))
            similar['average_sales_cycle'] = max(7, similar.get('average_sales_cycle', 90))
        
        return validated
    
    # Default fallback methods
    
    def _get_default_conversion_analysis(self) -> dict:
        """Return default conversion analysis when generation fails"""
        return {
            "conversion_probability": 50.0,
            "conversion_confidence": 60.0,
            "conversion_readiness_score": 50.0,
            "readiness_factors": ["Basic lead information captured"],
            "blocking_factors": ["Needs further qualification"],
            "recommended_for_conversion": False,
            "conversion_timeline": "4-6 weeks",
            "required_actions_before_conversion": [
                "Qualify budget and authority",
                "Confirm timeline and urgency",
                "Identify decision makers"
            ],
            "conversion_triggers": ["Budget confirmation", "Timeline urgency"],
            "risk_factors": ["Incomplete qualification"],
            "success_indicators": ["Stakeholder engagement"]
        }
    
    def _get_default_deal_predictions(self) -> dict:
        """Return default deal predictions when generation fails"""
        return {
            "deal_size_prediction": {
                "minimum_value": 10000,
                "maximum_value": 50000,
                "most_likely_value": 25000,
                "confidence_level": 60,
                "sizing_rationale": "Based on typical industry patterns"
            },
            "timeline_prediction": {
                "minimum_days": 60,
                "maximum_days": 180,
                "most_likely_days": 120,
                "confidence_level": 65,
                "timeline_rationale": "Standard sales cycle for similar opportunities"
            },
            "deal_size_factors": ["Company size assessment needed"],
            "timeline_factors": ["Decision process complexity unknown"],
            "accelerating_factors": ["Urgency indicators"],
            "risk_factors": ["Competitive evaluation possible"]
        }
    
    def _get_default_stage_recommendations(self) -> dict:
        """Return default stage recommendations when generation fails"""
        return {
            "current_stage_assessment": {
                "recommended_stage": "qualification",
                "stage_confidence": 60,
                "stage_rationale": "Needs further qualification"
            },
            "advancement_analysis": {
                "next_stage": "proposal",
                "advancement_probability": 50,
                "advancement_timeline": "3-4 weeks",
                "advancement_confidence": 60
            },
            "stage_requirements_met": ["Initial contact established"],
            "stage_requirements_missing": ["Budget qualification needed"],
            "advancement_actions": ["Schedule qualification call"],
            "stage_risks": ["Incomplete information"],
            "success_metrics": ["Information gathering progress"]
        }
    
    def _get_default_risk_analysis(self) -> dict:
        """Return default risk analysis when generation fails"""
        return {
            "overall_risk_assessment": {
                "risk_level": "medium",
                "risk_score": 50,
                "confidence": 60,
                "primary_risk_category": "qualification"
            },
            "identified_risks": [{
                "risk_type": "qualification",
                "risk_description": "Incomplete lead qualification",
                "probability": 60,
                "impact": "medium",
                "risk_score": 50,
                "indicators": ["Limited information available"]
            }],
            "mitigation_strategies": [{
                "risk_type": "qualification",
                "strategies": ["Conduct thorough discovery call"],
                "timeline": "within 1 week",
                "resources_required": ["Sales representative time"]
            }],
            "monitoring_recommendations": ["Track qualification progress"],
            "early_warning_indicators": ["Delayed responses"],
            "contingency_plans": ["Alternative qualification approaches"]
        }
    
    def _get_default_historical_analysis(self) -> dict:
        """Return default historical analysis when generation fails"""
        return {
            "similar_leads_analysis": {
                "similar_leads_count": 10,
                "average_conversion_rate": 25,
                "average_deal_size": 25000,
                "average_sales_cycle": 90,
                "success_factors": ["Proper qualification", "Stakeholder engagement"]
            },
            "industry_benchmarks": {
                "industry_conversion_rate": 25,
                "industry_average_deal_size": 30000,
                "industry_sales_cycle": 120,
                "competitive_win_rate": 35
            },
            "predictive_insights": ["Standard industry patterns apply"],
            "optimization_recommendations": ["Follow standard sales process"],
            "success_probability_factors": {
                "positive_indicators": ["Lead shows interest"],
                "negative_indicators": ["Limited information available"],
                "neutral_factors": ["Standard industry characteristics"]
            }
        }