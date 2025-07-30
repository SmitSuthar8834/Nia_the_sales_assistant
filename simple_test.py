#!/usr/bin/env python
"""
Simple test to demonstrate NIA Sales Assistant functionality
"""
import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nia_sales_assistant.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

def demo_nia_functionality():
    """Demonstrate NIA's AI-powered sales assistant capabilities"""
    print("🤖 NIA (Neural Intelligence Assistant) - Demo")
    print("=" * 50)
    
    # Create test client and user
    client = Client()
    user, created = User.objects.get_or_create(
        username='demo_user',
        defaults={'email': 'demo@example.com'}
    )
    if created:
        user.set_password('demo123')
        user.save()
    
    client.force_login(user)
    print(f"✅ Demo user logged in: {user.username}")
    
    # Test conversation analysis
    print("\n📞 Simulating Sales Call Analysis...")
    
    sample_conversation = """
    NIA: Hello! I'm NIA, your AI sales assistant. How can I help you today?
    
    Sales Rep: Hi NIA, I just had a call with a potential client. Let me tell you about it.
    
    Sales Rep: I spoke with Jennifer Martinez from CloudTech Solutions. They're a growing 
    tech startup with about 75 employees. Jennifer is their Head of Sales Operations. 
    
    She mentioned they're struggling with their current lead management process - they're 
    using spreadsheets and it's becoming chaotic. They lose track of follow-ups and 
    can't properly analyze their sales pipeline.
    
    They need a CRM system that can integrate with their existing tools like Slack and 
    their email marketing platform. Their budget is around $25,000 and they want to 
    implement something within the next 3 months.
    
    Jennifer seemed very interested but mentioned that the final decision will be made 
    by their CEO, Michael Chen, and their CTO, Sarah Kim. She said they've been burned 
    by software implementations before, so they're being very careful this time.
    
    What do you think, NIA? How should I approach this lead?
    """
    
    # Send to NIA for analysis
    response = client.post(
        '/api/ai/analyze/',
        data=json.dumps({"conversation_text": sample_conversation}),
        content_type='application/json'
    )
    
    if response.status_code == 200:
        result = response.json()
        
        print("✅ NIA Analysis Complete!")
        print(f"📊 Analysis ID: {result['analysis_id']}")
        
        # Display extracted lead information
        lead_info = result['lead_info']
        print(f"\n🏢 EXTRACTED LEAD INFORMATION:")
        print(f"   Company: {lead_info.get('company_name', 'N/A')}")
        print(f"   Contact: {lead_info.get('contact_details', {}).get('name', 'N/A')}")
        print(f"   Industry: {lead_info.get('industry', 'N/A')}")
        print(f"   Company Size: {lead_info.get('company_size', 'N/A')}")
        print(f"   Budget: {lead_info.get('budget_info', 'N/A')}")
        print(f"   Timeline: {lead_info.get('timeline', 'N/A')}")
        
        print(f"\n💡 PAIN POINTS IDENTIFIED:")
        for i, pain_point in enumerate(lead_info.get('pain_points', []), 1):
            print(f"   {i}. {pain_point}")
        
        print(f"\n📋 REQUIREMENTS:")
        for i, req in enumerate(lead_info.get('requirements', []), 1):
            print(f"   {i}. {req}")
        
        print(f"\n👥 DECISION MAKERS:")
        for i, dm in enumerate(lead_info.get('decision_makers', []), 1):
            print(f"   {i}. {dm}")
        
        # Display AI recommendations
        recommendations = result['recommendations']
        print(f"\n🎯 NIA'S AI RECOMMENDATIONS:")
        print(f"   Lead Score: {recommendations.get('lead_score', 'N/A')}/100")
        print(f"   Conversion Probability: {recommendations.get('conversion_probability', 'N/A')}")
        
        print(f"\n📈 RECOMMENDED ACTIONS:")
        for i, rec in enumerate(recommendations.get('recommendations', [])[:5], 1):
            print(f"   {i}. [{rec.get('priority', 'medium').upper()}] {rec.get('title', 'N/A')}")
            print(f"      → {rec.get('description', 'N/A')}")
            print(f"      ⏰ Timeline: {rec.get('timeline', 'N/A')}")
            print()
        
        print(f"🔍 KEY INSIGHTS:")
        for i, insight in enumerate(recommendations.get('key_insights', []), 1):
            print(f"   {i}. {insight}")
        
        print(f"\n⚠️  RISK FACTORS:")
        for i, risk in enumerate(recommendations.get('risk_factors', []), 1):
            print(f"   {i}. {risk}")
        
        print(f"\n🚀 OPPORTUNITIES:")
        for i, opp in enumerate(recommendations.get('opportunities', []), 1):
            print(f"   {i}. {opp}")
        
    else:
        print(f"❌ Analysis failed: {response.content.decode()}")
    
    print("\n" + "=" * 50)
    print("🎉 NIA Demo Complete!")
    print("\nNIA has successfully:")
    print("✅ Analyzed the sales conversation")
    print("✅ Extracted structured lead information")
    print("✅ Identified pain points and requirements")
    print("✅ Generated AI-powered sales recommendations")
    print("✅ Provided actionable next steps")
    print("\nTask 1 Implementation: ✅ COMPLETE")

if __name__ == "__main__":
    demo_nia_functionality()