#!/usr/bin/env python
"""
Test script for lead extraction functionality
"""
import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nia_sales_assistant.settings')
django.setup()

from ai_service.services import GeminiAIService, DataValidator
from django.contrib.auth import get_user_model

def test_lead_extraction():
    """Test the lead extraction functionality"""
    print("Testing Lead Information Extraction...")
    
    # Test conversation
    conversation = """
    Hi, this is Sarah Johnson from TechStart Inc. I'm the CTO here.
    
    We're a software development company with about 75 employees, and we're having some real challenges with our current processes.
    
    Our main issues are manual data entry which is eating up our developers' time, system integration problems where our tools don't talk to each other, and we're worried about scalability as we grow.
    
    We need something that can automate our workflow, has good API integration capabilities, and is cloud-based. Our budget is between $100,000 and $150,000, and we need implementation by Q3 2024.
    
    The decision would involve myself and our CEO, Mike Chen. We've looked at Salesforce and HubSpot but they don't fit our needs.
    
    You can reach me at sarah.johnson@techstart.com or call me at 555-987-6543.
    """
    
    try:
        # Initialize AI service
        ai_service = GeminiAIService()
        
        print("1. Testing AI connection...")
        connection_test = ai_service.test_connection()
        print(f"   Connection: {'✓' if connection_test['success'] else '✗'}")
        
        if not connection_test['success']:
            print(f"   Error: {connection_test['message']}")
            return
        
        print("\n2. Extracting lead information...")
        lead_info = ai_service.extract_lead_info(conversation)
        
        print(f"   Company: {lead_info.get('company_name', 'Not found')}")
        print(f"   Contact: {lead_info.get('contact_details', {}).get('name', 'Not found')}")
        print(f"   Email: {lead_info.get('contact_details', {}).get('email', 'Not found')}")
        print(f"   Phone: {lead_info.get('contact_details', {}).get('phone', 'Not found')}")
        print(f"   Pain Points: {len(lead_info.get('pain_points', []))} identified")
        print(f"   Requirements: {len(lead_info.get('requirements', []))} identified")
        print(f"   Budget: {lead_info.get('budget_info', 'Not mentioned')}")
        print(f"   Timeline: {lead_info.get('timeline', 'Not mentioned')}")
        
        metadata = lead_info.get('extraction_metadata', {})
        print(f"   Confidence Score: {metadata.get('confidence_score', 0):.1f}%")
        print(f"   Data Completeness: {metadata.get('data_completeness', 0):.1f}%")
        
        print("\n3. Validating extracted data...")
        validation = ai_service.validate_extracted_data(lead_info)
        print(f"   Valid: {'✓' if validation['is_valid'] else '✗'}")
        print(f"   Quality Score: {validation['data_quality_score']:.1f}")
        
        if validation['errors']:
            print(f"   Errors: {', '.join(validation['errors'])}")
        if validation['warnings']:
            print(f"   Warnings: {', '.join(validation['warnings'])}")
        
        print("\n4. Testing entity extraction...")
        entities = ai_service.extract_entities(conversation)
        print(f"   Companies: {entities.get('companies', [])}")
        print(f"   People: {entities.get('people', [])}")
        print(f"   Emails: {entities.get('emails', [])}")
        print(f"   Phones: {entities.get('phones', [])}")
        print(f"   Monetary amounts: {entities.get('monetary_amounts', [])}")
        
        print("\n5. Testing data validator...")
        validator = DataValidator()
        
        # Test email validation
        test_emails = ['sarah.johnson@techstart.com', 'invalid-email', 'test@domain.com']
        for email in test_emails:
            is_valid = validator.validate_email(email)
            print(f"   Email '{email}': {'✓' if is_valid else '✗'}")
        
        # Test phone validation
        test_phones = ['555-987-6543', '123', '+1-555-123-4567']
        for phone in test_phones:
            is_valid = validator.validate_phone(phone)
            print(f"   Phone '{phone}': {'✓' if is_valid else '✗'}")
        
        print("\n✅ Lead extraction test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_lead_extraction()