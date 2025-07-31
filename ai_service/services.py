import google.generativeai as genai
from django.conf import settings
import json
import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

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
        """Initialize Gemini AI client with API key"""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.validator = DataValidator()
    
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
            response = self.model.generate_content(prompt)
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
    
    def generate_recommendations(self, lead_data: dict, context: dict = None) -> list:
        """
        Generate AI-powered sales recommendations based on lead data
        
        Args:
            lead_data (dict): Extracted lead information
            context (dict): Additional context information
            
        Returns:
            list: List of recommendations
        """
        context_info = context or {}
        
        prompt = f"""
        Based on the following lead information, provide specific sales recommendations and next steps.
        
        Lead Information:
        {json.dumps(lead_data, indent=2)}
        
        Additional Context:
        {json.dumps(context_info, indent=2)}
        
        Please provide recommendations in the following JSON format:
        {{
            "recommendations": [
                {{
                    "type": "next_step|strategy|approach",
                    "title": "Brief title",
                    "description": "Detailed description",
                    "priority": "high|medium|low",
                    "timeline": "suggested timeline"
                }}
            ],
            "lead_score": "score from 1-100",
            "conversion_probability": "probability percentage",
            "key_insights": ["list of key insights"],
            "risk_factors": ["list of potential risks"],
            "opportunities": ["list of opportunities"]
        }}
        
        Focus on actionable, specific recommendations based on sales best practices.
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up JSON formatting
            if response_text.startswith('```json'):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith('```'):
                response_text = response_text[3:-3].strip()
            
            recommendations_data = json.loads(response_text)
            logger.info(f"Generated recommendations: {recommendations_data}")
            return recommendations_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse recommendations JSON: {e}")
            return self._get_default_recommendations()
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return self._get_default_recommendations()
    
    def test_connection(self) -> dict:
        """
        Test the connection to Gemini AI
        
        Returns:
            dict: Connection test results
        """
        try:
            response = self.model.generate_content("Hello, this is a test message. Please respond with 'Connection successful'.")
            return {
                "success": True,
                "message": "Gemini AI connection successful",
                "response": response.text
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
        
        response = self.model.generate_content(prompt)
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
                    "timeline": "within 2-3 days"
                }
            ],
            "lead_score": 50,
            "conversion_probability": "25%",
            "key_insights": ["More information needed to provide detailed analysis"],
            "risk_factors": ["Limited information available"],
            "opportunities": ["Potential for further qualification"]
        }