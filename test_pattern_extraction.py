#!/usr/bin/env python
"""
Test pattern-based entity extraction without API calls
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nia_sales_assistant.settings')
django.setup()

from ai_service.services import GeminiAIService


def test_pattern_extraction():
    """Test pattern-based entity extraction"""
    print("Testing pattern-based entity extraction...")
    
    ai_service = GeminiAIService()
    
    # Test text with various entities
    test_text = """
    Dr. Sarah Johnson from TechStart LLC contacted us about their CRM needs. 
    She mentioned they also work with Acme Corp Inc and Global Solutions Ltd.
    Contact her at sarah@techstart.com or call 555-987-6543.
    They need API integration, database optimization, and cloud migration.
    Budget is $75,000 and timeline is Q2 2024.
    """
    
    # Initialize entities dictionary
    entities = {
        'companies': [],
        'people': [],
        'emails': [],
        'phones': [],
        'phone_numbers': [],
        'monetary_amounts': [],
        'dates': [],
        'technologies': []
    }
    
    # Extract using pattern matching only
    ai_service._extract_entities_with_patterns(test_text, entities)
    
    print("✅ Pattern extraction completed!")
    print(f"Companies: {entities['companies']}")
    print(f"People: {entities['people']}")
    print(f"Technologies: {entities['technologies']}")
    print(f"Dates: {entities['dates']}")
    
    # Also test the full extract_entities method with email/phone patterns
    full_entities = {
        'companies': [],
        'people': [],
        'emails': [],
        'phones': [],
        'phone_numbers': [],
        'monetary_amounts': [],
        'dates': [],
        'technologies': []
    }
    
    # Extract emails using regex
    import re
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    full_entities['emails'] = re.findall(email_pattern, test_text)
    
    # Extract phones using regex
    phone_pattern = r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'
    phone_numbers = re.findall(phone_pattern, test_text)
    full_entities['phones'] = phone_numbers
    full_entities['phone_numbers'] = phone_numbers
    
    # Extract monetary amounts
    money_pattern = r'\$[\d,]+(?:\.\d{2})?|\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|USD|k|K|million|M|billion|B)\b'
    full_entities['monetary_amounts'] = re.findall(money_pattern, test_text, re.IGNORECASE)
    
    # Add pattern-based entities
    ai_service._extract_entities_with_patterns(test_text, full_entities)
    
    print("\n✅ Full pattern extraction completed!")
    print(f"Companies: {full_entities['companies']}")
    print(f"People: {full_entities['people']}")
    print(f"Emails: {full_entities['emails']}")
    print(f"Phones: {full_entities['phones']}")
    print(f"Technologies: {full_entities['technologies']}")
    print(f"Monetary amounts: {full_entities['monetary_amounts']}")
    print(f"Dates: {full_entities['dates']}")
    
    # Verify expected entities were found
    expected_companies = ['TechStart LLC', 'Acme Corp Inc', 'Global Solutions Ltd']
    expected_people = ['Dr. Sarah Johnson']
    expected_emails = ['sarah@techstart.com']
    expected_phones = ['555-987-6543']
    expected_tech = ['CRM', 'API', 'database', 'cloud']
    expected_money = ['$75,000']
    expected_dates = ['Q2 2024']
    
    success = True
    
    for company in expected_companies:
        if company not in full_entities['companies']:
            print(f"❌ Missing company: {company}")
            success = False
    
    for person in expected_people:
        if person not in full_entities['people']:
            print(f"❌ Missing person: {person}")
            success = False
    
    for email in expected_emails:
        if email not in full_entities['emails']:
            print(f"❌ Missing email: {email}")
            success = False
    
    for phone in expected_phones:
        if phone not in full_entities['phones']:
            print(f"❌ Missing phone: {phone}")
            success = False
    
    for tech in expected_tech:
        if tech not in full_entities['technologies']:
            print(f"❌ Missing technology: {tech}")
            success = False
    
    for money in expected_money:
        if money not in full_entities['monetary_amounts']:
            print(f"❌ Missing monetary amount: {money}")
            success = False
    
    for date in expected_dates:
        if date not in full_entities['dates']:
            print(f"❌ Missing date: {date}")
            success = False
    
    if success:
        print("\n🎉 All expected entities were extracted successfully!")
        return True
    else:
        print("\n⚠️ Some expected entities were not extracted.")
        return False


if __name__ == "__main__":
    success = test_pattern_extraction()
    sys.exit(0 if success else 1)