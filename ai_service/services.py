import google.generativeai as genai
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)


class GeminiAIService:
    """Service class for interacting with Google Gemini AI"""
    
    def __init__(self):
        """Initialize Gemini AI client with API key"""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def extract_lead_info(self, conversation_text: str) -> dict:
        """
        Extract structured lead information from conversation transcript
        
        Args:
            conversation_text (str): The conversation transcript
            
        Returns:
            dict: Extracted lead information
        """
        prompt = f"""
        Analyze the following sales conversation and extract key lead information.
        Return the information in JSON format with the following structure:
        {{
            "company_name": "extracted company name or null",
            "contact_details": {{
                "name": "contact person name or null",
                "email": "email address or null",
                "phone": "phone number or null"
            }},
            "pain_points": ["list of identified pain points"],
            "requirements": ["list of identified requirements"],
            "budget_info": "budget information or null",
            "timeline": "timeline information or null",
            "decision_makers": ["list of decision makers mentioned"],
            "industry": "industry or sector or null",
            "company_size": "company size information or null"
        }}
        
        Conversation:
        {conversation_text}
        
        Please analyze carefully and extract only information that is explicitly mentioned or can be reasonably inferred.
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Try to find JSON in the response
            if response_text.startswith('```json'):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith('```'):
                response_text = response_text[3:-3].strip()
            
            extracted_data = json.loads(response_text)
            logger.info(f"Successfully extracted lead info: {extracted_data}")
            return extracted_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini response: {e}")
            return self._get_default_lead_structure()
        except Exception as e:
            logger.error(f"Error extracting lead info: {e}")
            return self._get_default_lead_structure()
    
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
    
    def _get_default_lead_structure(self) -> dict:
        """Return default lead structure when extraction fails"""
        return {
            "company_name": None,
            "contact_details": {
                "name": None,
                "email": None,
                "phone": None
            },
            "pain_points": [],
            "requirements": [],
            "budget_info": None,
            "timeline": None,
            "decision_makers": [],
            "industry": None,
            "company_size": None
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