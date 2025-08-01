#!/usr/bin/env python
"""
Simple test script to verify AI API functionality
"""
import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nia_sales_assistant.settings')
django.setup()

from ai_service.services import GeminiAIService
import json

def test_gemini_connection():
    """Test basic Gemini AI connection"""
    print("Testing Gemini AI connection...")
    
    try:
        ai_service = GeminiAIService()
        result = ai_service.test_connection()
        print(f"Connection test result: {json.dumps(result, indent=2)}")
        return result['success']
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False

def test_lead_extraction():
    """Test lead information extraction"""
    print("\nTesting lead information extraction...")
    
    test_conversation = """
    Sales Rep (Sarah): Good afternoon, Mr. Rodriguez. Thank you for taking the time to meet with me today. I understand from our initial conversation that DataFlow Solutions is experiencing some challenges with your current customer management processes?

    Prospect (Miguel Rodriguez - VP of Operations): That's right, Sarah. We're a mid-market logistics company with about 350 employees across five locations. Honestly, we're drowning in spreadsheets and our team is using three different systems that don't talk to each other. But before we go further, I need to be upfront—we just implemented a new ERP system six months ago, and there's some... let's call it "change fatigue" in the organization.

    Sarah: I completely understand that concern, Miguel. Change fatigue is real, and the last thing any organization needs is another disruptive implementation. Can you help me understand what specific pain points are driving you to consider a CRM solution despite the recent ERP rollout?

    Miguel: Well, our customer retention has dropped 12% over the past year. Our account managers are spending 60% of their time on administrative tasks instead of actually managing relationships. And here's the kicker—last month we lost a $2.3 million contract because three different team members contacted the same client with conflicting information. The client felt we were disorganized and unprofessional.

    Sarah: That's a significant loss, and I can see why leadership is concerned. Before we discuss solutions, I'd like to understand your current tech stack better. You mentioned three different systems—can you walk me through what those are and how your team currently manages customer data?

    Miguel: Sure. Sales uses an ancient contact management system called ClientBase Pro—I think it's from 2015. Customer service has their own ticketing system, ServiceMax, and our project managers use a custom-built solution that honestly, nobody fully understands because the developer left the company two years ago. Everything else lives in Excel sheets that get emailed around.

    Sarah: taking notes And how does this connect with your new ERP system?

    Miguel: laughs It doesn't. That's part of the problem. Our CFO, Janet, is adamant that we need everything to integrate with our ERP because it cost us $400K to implement. But our IT director, Tom, says any new system needs to have robust APIs and minimal customization because his team is already stretched thin maintaining what we have.

    Sarah: It sounds like you have multiple stakeholders with different priorities. Beyond Janet and Tom, who else would be involved in evaluating a CRM solution?

    Miguel: Well, there's myself, Janet—our CFO, Tom from IT, Lisa who heads up Customer Service, and Marcus, our VP of Sales. Oh, and our CEO, David, will want to weigh in, especially after that contract loss. He's... particular about ROI calculations and implementation timelines.

    Sarah: That's quite a decision-making committee. In your experience, what's typically the biggest challenge when this group evaluates new technology?

    Miguel: sighs Honestly? We all speak different languages. Marcus wants something that will boost his team's close rates immediately. Lisa needs better customer service workflows. Janet wants detailed financial reporting and cost control. Tom wants something that won't break our infrastructure. And David wants everything for half the price with twice the results.

    Sarah: Those are all valid concerns, and actually, they're not as conflicting as they might seem on the surface. But let me ask you this—if you could wave a magic wand and solve just ONE of these challenges perfectly, which would have the biggest impact on your business?

    Miguel: pauses That's a great question. I think... if we could get a complete view of each customer relationship—who they've talked to, what they've bought, what issues they've had, upcoming opportunities—that would prevent situations like losing that big contract. It would help sales be more effective, customer service more proactive, and give leadership the visibility they need.

    Sarah: That's exactly what a unified customer data platform can provide. But I'm curious—you mentioned the developer who built your custom project management system left. Are you concerned about vendor dependency with a new CRM solution?

    Miguel: Absolutely. We can't afford to be locked into something proprietary again. And frankly, after spending six months implementing the ERP, the idea of another major system rollout makes me nervous. How long do these implementations typically take?

    Sarah: That depends on complexity and scope, but I hear your concern about implementation fatigue. What if we could design a phased approach that delivers quick wins while minimizing disruption? For instance, starting with sales automation for Marcus's team while your customer service continues using ServiceMax until they're ready to transition?

    Miguel: That's interesting. But won't that just create more data silos in the short term?

    Sarah: Not if we choose the right platform. Modern CRMs can integrate with existing systems through APIs, so even during a phased rollout, data flows between systems. Your ERP would remain the system of record for financial data, while the CRM becomes the system of record for customer relationships.

    Miguel: leaning forward Okay, you have my attention. But here's the real test—we have some unique requirements. Our logistics business means we track shipments, delivery windows, and have complex pricing based on routes, fuel costs, and seasonal variations. Can a standard CRM handle that level of customization?

    Sarah: Those are sophisticated requirements, and you're right that not every CRM can handle complex logistics workflows out of the box. However, rather than heavy customization, the best approach is usually finding a platform that's flexible enough to accommodate your business processes without requiring extensive coding. Tell me more about these pricing calculations—are they rule-based or do they require human judgment?

    Miguel: It's a mix. We have base pricing rules, but our senior account managers can adjust based on relationship history, volume commitments, competitive situations. Sometimes a $50K customer gets better pricing than a $200K customer because of strategic value or growth potential.

    Sarah: That's where advanced CRM functionality really shines—business rule engines combined with user permissions and approval workflows. Your system could automate the standard pricing while flagging exceptions for management approval. This would actually speed up your quote process while maintaining control.

    Miguel: Hmm. But what about training? Our sales team ranges from digital natives to people who still print their emails. Will they actually use a new system?

    Sarah: User adoption is critical, and you're smart to think about it upfront. The best CRMs today are designed with user experience in mind—mobile-first, intuitive interfaces, and built-in guided workflows. But beyond the technology, adoption is really about change management and showing clear value to each user type.

    Miguel: checking phone Speaking of users, Marcus just texted me. He's worried that a CRM will slow down his fast-moving sales process and create more administrative burden. How do you address that concern?

    Sarah: Marcus is right to be concerned—a poorly implemented CRM absolutely can slow down sales. But when done right, it should eliminate administrative work, not create it. For example, automated lead routing, email templates, proposal generation, and activity logging. The key is ensuring the system works the way your sales team already works, not forcing them to change successful processes.

    Miguel: That makes sense in theory, but how do we know what "done right" looks like for our specific situation? We're not CRM experts.

    Sarah: Excellent question. That's where a proper discovery and design phase becomes crucial. We'd typically spend 2-3 weeks mapping your current processes, identifying inefficiencies, and designing workflows before any configuration begins. Think of it like architectural blueprints—you wouldn't start building without detailed plans.

    Miguel: nodding Okay, but let's talk numbers. What's the typical investment for something like this, and how do we justify the ROI to David?

    Sarah: Investment varies based on scope and user count, but for an organization your size, you're typically looking at $50K-$150K annually, depending on functionality needs. But let's flip the question—what's the cost of NOT solving this problem? You mentioned losing a $2.3M contract. How many more of those can you afford?

    Miguel: Fair point. And our account managers spending 60% of their time on admin work means we're essentially paying sales salaries for administrative tasks. If we could reduce that to 30%, we'd effectively double their selling capacity without hiring anyone.

    Sarah: Exactly. And think about the compound effect—better customer data leads to more targeted selling, higher close rates, better retention. Many of our clients see 15-25% improvements in sales productivity within the first year.

    Miguel: Those are impressive numbers, but how do we know we'll see similar results? Every vendor promises transformational outcomes.

    Sarah: You're absolutely right to be skeptical. That's why I'd recommend starting with a pilot program—maybe 20-30 users from sales and customer service. We can define specific metrics upfront: lead response time, quote turnaround, customer satisfaction scores, sales cycle length. After 60-90 days, you'll have real data on actual impact.

    Miguel: A pilot approach is interesting. But what happens if the pilot goes well but then the full rollout hits unexpected issues?

    Sarah: That's where phased implementation planning becomes critical. The pilot teaches us about your specific environment, user behavior, and integration challenges. We use those learnings to refine the full rollout plan. It's like running a small-scale dress rehearsal before the main performance.

    Miguel: glancing at watch This has been really helpful, Sarah, but I need to wrap up soon. If we were to move forward, what would the next steps look like?

    Sarah: I'd recommend we schedule a follow-up meeting with your key stakeholders—Marcus, Lisa, Tom, and Janet. We can do a deeper discovery session where each person can voice their specific requirements and concerns. From there, we can design a pilot program that addresses everyone's priorities and gives you concrete data to make a final decision.

    Miguel: That sounds reasonable. But I have to ask—what happens if we go through this whole process and decide the solution isn't right for us?

    Sarah: Then you'll have learned valuable things about your processes and requirements that will help with future decisions. I'd rather walk away from a deal than put you into a solution that doesn't deliver results. My success is measured by client outcomes, not just closed contracts.

    Miguel: standing up I appreciate that honesty, Sarah. Let me talk to David and the team, and I'll get back to you about scheduling that stakeholder meeting. One last question—if you were in my shoes, what would be your biggest concern about moving forward with this?

    Sarah: Honestly? Implementation bandwidth. You've got a lot on your plate with the ERP integration, and adding another major project could strain your team. That's why the phased approach is so important—it has to be manageable alongside your other priorities.

    Miguel: shaking hands That's exactly what I was thinking. Thanks for being straightforward about that. I'll be in touch by early next week.

    Sarah: Perfect. I'll send you a follow-up email with some case studies from similar logistics companies and a framework for that stakeholder meeting. Thank you for your time, Miguel.
    """
    
    try:
        ai_service = GeminiAIService()
        result = ai_service.extract_lead_info(test_conversation)
        print(f"Lead extraction result: {json.dumps(result, indent=2)}")
        return True
    except Exception as e:
        print(f"Lead extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_recommendations():
    """Test recommendations generation"""
    print("\nTesting recommendations generation...")
    
    test_lead_data = {
        "company_name": "DataFlow Solutions",
        "contact_details": {
            "name": "Miguel Rodriguez",
            "email": None,
            "phone": None,
            "title": "VP of Operations"
        },
        "pain_points": [
            "Customer retention dropped 12% over the past year",
            "Account managers spending 60% of time on administrative tasks",
            "Lost $2.3 million contract due to conflicting information",
            "Three different systems that don't talk to each other",
            "Drowning in spreadsheets",
            "Change fatigue from recent ERP implementation"
        ],
        "requirements": [
            "Unified customer data platform",
            "Complete view of customer relationships",
            "Integration with existing ERP system",
            "Phased implementation approach",
            "Complex logistics workflows support",
            "Pricing calculation automation"
        ],
        "budget_info": "$50K-$150K annually",
        "timeline": "Phased approach preferred",
        "industry": "Logistics",
        "company_size": "350 employees across five locations",
        "decision_makers": ["Miguel Rodriguez", "Janet (CFO)", "Tom (IT Director)", "Lisa (Customer Service Head)", "Marcus (VP of Sales)", "David (CEO)"],
        "current_solution": "ClientBase Pro (2015), ServiceMax, custom-built project management system, Excel sheets",
        "urgency_level": "high"
    }
    
    try:
        ai_service = GeminiAIService()
        result = ai_service.generate_recommendations(test_lead_data)
        print(f"Recommendations result: {json.dumps(result, indent=2)}")
        return True
    except Exception as e:
        print(f"Recommendations generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== NIA AI Service Test ===")
    
    # Test connection
    connection_ok = test_gemini_connection()
    
    if connection_ok:
        # Test lead extraction
        extraction_ok = test_lead_extraction()
        
        # Test recommendations
        recommendations_ok = test_recommendations()
        
        print(f"\n=== Test Results ===")
        print(f"Connection: {'✅ PASS' if connection_ok else '❌ FAIL'}")
        print(f"Lead Extraction: {'✅ PASS' if extraction_ok else '❌ FAIL'}")
        print(f"Recommendations: {'✅ PASS' if recommendations_ok else '❌ FAIL'}")
    else:
        print("\n❌ Connection failed - skipping other tests")
        print("\nPlease check:")
        print("1. GEMINI_API_KEY is set correctly in .env file")
        print("2. API key has proper permissions")
        print("3. Internet connection is working")