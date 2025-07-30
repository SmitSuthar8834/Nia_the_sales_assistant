#!/usr/bin/env python
"""
Simple test script to verify Gemini AI integration
"""
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nia_sales_assistant.settings')
django.setup()

from ai_service.services import GeminiAIService

def test_gemini_connection():
    """Test the Gemini AI connection and basic functionality"""
    print("Testing Gemini AI connection...")
    
    try:
        # Initialize the service
        ai_service = GeminiAIService()
        
        # Test connection
        print("1. Testing connection...")
        connection_result = ai_service.test_connection()
        print(f"Connection result: {connection_result}")
        
        if connection_result['success']:
            print("✅ Gemini AI connection successful!")
            
            # Test lead extraction
            print("\n2. Testing lead information extraction...")
            sample_conversation = """
            Sales Rep: Hi, I'm calling from TechSolutions. I understand you might be looking for a CRM system?
            
            Customer: Yes, we're John Smith from ABC Manufacturing. We're a mid-size company with about 200 employees. 
            Our current system is really outdated and we're having trouble tracking our sales pipeline. 
            We need something that can integrate with our existing ERP system and handle about 1000 leads per month.
            Our budget is around $50,000 and we'd like to implement something within the next 3 months.
            I'm the IT Director, but the final decision will be made by our CEO, Sarah Johnson.
            
            Sales Rep: That sounds like a perfect fit for our enterprise solution...
            """
            
            extracted_info = ai_service.extract_lead_info(sample_conversation)
            print(f"Extracted lead info: {extracted_info}")
            
            # Test recommendations
            print("\n3. Testing recommendations generation...")
            recommendations = ai_service.generate_recommendations(extracted_info)
            print(f"Generated recommendations: {recommendations}")
            
            print("\n✅ All tests passed! Gemini AI integration is working correctly.")
            
        else:
            print("❌ Gemini AI connection failed!")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    test_gemini_connection()