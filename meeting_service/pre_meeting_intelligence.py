"""
Pre-Meeting Intelligence Service - Generates AI-powered meeting preparation materials
"""

import logging
from typing import Any, Dict

from django.utils import timezone

from ai_service.models import Lead
from ai_service.services import GeminiAIService

from .models import Meeting

logger = logging.getLogger(__name__)


class PreMeetingIntelligenceService:
    """Service for generating comprehensive pre-meeting intelligence and preparation materials"""

    def __init__(self):
        self.ai_service = GeminiAIService()

    def generate_meeting_agenda(
        self, meeting: Meeting, regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Generate AI-powered meeting agenda based on lead data and meeting context

        Args:
            meeting (Meeting): The meeting to generate agenda for
            regenerate (bool): Whether to regenerate existing agenda

        Returns:
            dict: Generated agenda with structure and timing
        """
        try:
            # Check if agenda already exists and regenerate is False
            if not regenerate and meeting.agenda and meeting.agenda.strip():
                logger.info(
                    f"Agenda already exists for meeting {meeting.id}, skipping generation"
                )
                return self._format_existing_agenda(meeting)

            # Get lead data for context
            lead_data = self._extract_lead_data(meeting.lead)

            # Prepare meeting context
            meeting_context = {
                "meeting_type": meeting.meeting_type,
                "duration_minutes": meeting.duration_minutes,
                "meeting_status": meeting.status,
                "scheduled_at": (
                    meeting.scheduled_at.isoformat() if meeting.scheduled_at else None
                ),
                "participants": meeting.participants,
                "previous_meetings": self._get_previous_meeting_context(meeting.lead),
                "ai_insights": self._serialize_ai_insights(meeting.lead),
            }

            # Generate agenda using AI service
            logger.info(
                f"Generating agenda for meeting {meeting.id} with lead {meeting.lead.company_name}"
            )
            agenda_data = self._generate_ai_agenda(lead_data, meeting_context)

            # Update meeting with generated agenda
            meeting.agenda = agenda_data.get("formatted_agenda", "")

            # Update AI insights with agenda generation metadata
            current_insights = meeting.ai_insights or {}
            current_insights.update(
                {
                    "agenda_generation": {
                        "generated_at": timezone.now().isoformat(),
                        "agenda_structure": agenda_data.get("agenda_structure", {}),
                        "key_objectives": agenda_data.get("key_objectives", []),
                        "time_allocation": agenda_data.get("time_allocation", {}),
                        "success_metrics": agenda_data.get("success_metrics", []),
                    }
                }
            )
            meeting.ai_insights = current_insights
            meeting.save(update_fields=["agenda", "ai_insights", "updated_at"])

            result = {
                "success": True,
                "agenda_generated": True,
                "formatted_agenda": agenda_data.get("formatted_agenda", ""),
                "agenda_structure": agenda_data.get("agenda_structure", {}),
                "key_objectives": agenda_data.get("key_objectives", []),
                "time_allocation": agenda_data.get("time_allocation", {}),
                "success_metrics": agenda_data.get("success_metrics", []),
                "generation_metadata": agenda_data.get("generation_metadata", {}),
            }

            logger.info(f"Successfully generated agenda for meeting {meeting.id}")
            return result

        except Exception as e:
            logger.error(f"Error generating agenda for meeting {meeting.id}: {e}")
            return {"success": False, "error": str(e), "agenda_generated": False}

    def generate_talking_points(self, meeting: Meeting) -> Dict[str, Any]:
        """
        Generate AI-powered talking points and conversation starters

        Args:
            meeting (Meeting): The meeting to generate talking points for

        Returns:
            dict: Generated talking points organized by category
        """
        try:
            # Get lead data and meeting context
            lead_data = self._extract_lead_data(meeting.lead)
            meeting_context = self._get_meeting_context(meeting)

            # Generate talking points using AI
            logger.info(f"Generating talking points for meeting {meeting.id}")
            talking_points_data = self._generate_ai_talking_points(
                lead_data, meeting_context
            )

            # Update meeting AI insights with talking points
            current_insights = meeting.ai_insights or {}
            current_insights.update(
                {
                    "talking_points": {
                        "generated_at": timezone.now().isoformat(),
                        "opening_statements": talking_points_data.get(
                            "opening_statements", []
                        ),
                        "value_propositions": talking_points_data.get(
                            "value_propositions", []
                        ),
                        "pain_point_discussions": talking_points_data.get(
                            "pain_point_discussions", []
                        ),
                        "solution_positioning": talking_points_data.get(
                            "solution_positioning", []
                        ),
                        "closing_statements": talking_points_data.get(
                            "closing_statements", []
                        ),
                        "conversation_bridges": talking_points_data.get(
                            "conversation_bridges", []
                        ),
                    }
                }
            )
            meeting.ai_insights = current_insights
            meeting.save(update_fields=["ai_insights", "updated_at"])

            result = {
                "success": True,
                "talking_points_generated": True,
                "opening_statements": talking_points_data.get("opening_statements", []),
                "value_propositions": talking_points_data.get("value_propositions", []),
                "pain_point_discussions": talking_points_data.get(
                    "pain_point_discussions", []
                ),
                "solution_positioning": talking_points_data.get(
                    "solution_positioning", []
                ),
                "closing_statements": talking_points_data.get("closing_statements", []),
                "conversation_bridges": talking_points_data.get(
                    "conversation_bridges", []
                ),
                "personalization_notes": talking_points_data.get(
                    "personalization_notes", []
                ),
            }

            logger.info(
                f"Successfully generated talking points for meeting {meeting.id}"
            )
            return result

        except Exception as e:
            logger.error(
                f"Error generating talking points for meeting {meeting.id}: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "talking_points_generated": False,
            }

    def generate_competitive_analysis(self, meeting: Meeting) -> Dict[str, Any]:
        """
        Generate competitive analysis and positioning strategy

        Args:
            meeting (Meeting): The meeting to generate competitive analysis for

        Returns:
            dict: Competitive analysis with positioning recommendations
        """
        try:
            # Get lead data and competitive context
            lead_data = self._extract_lead_data(meeting.lead)
            competitive_context = self._get_competitive_context(meeting.lead)

            # Generate competitive analysis using AI
            logger.info(f"Generating competitive analysis for meeting {meeting.id}")
            competitive_data = self._generate_ai_competitive_analysis(
                lead_data, competitive_context
            )

            # Update meeting AI insights with competitive analysis
            current_insights = meeting.ai_insights or {}
            current_insights.update(
                {
                    "competitive_analysis": {
                        "generated_at": timezone.now().isoformat(),
                        "identified_competitors": competitive_data.get(
                            "identified_competitors", []
                        ),
                        "competitive_landscape": competitive_data.get(
                            "competitive_landscape", {}
                        ),
                        "differentiation_points": competitive_data.get(
                            "differentiation_points", []
                        ),
                        "competitive_threats": competitive_data.get(
                            "competitive_threats", []
                        ),
                        "positioning_strategy": competitive_data.get(
                            "positioning_strategy", {}
                        ),
                        "objection_responses": competitive_data.get(
                            "objection_responses", {}
                        ),
                    }
                }
            )
            meeting.ai_insights = current_insights
            meeting.save(update_fields=["ai_insights", "updated_at"])

            result = {
                "success": True,
                "competitive_analysis_generated": True,
                "identified_competitors": competitive_data.get(
                    "identified_competitors", []
                ),
                "competitive_landscape": competitive_data.get(
                    "competitive_landscape", {}
                ),
                "differentiation_points": competitive_data.get(
                    "differentiation_points", []
                ),
                "competitive_threats": competitive_data.get("competitive_threats", []),
                "positioning_strategy": competitive_data.get(
                    "positioning_strategy", {}
                ),
                "objection_responses": competitive_data.get("objection_responses", {}),
                "competitive_risk_level": competitive_data.get(
                    "competitive_risk_level", "medium"
                ),
            }

            logger.info(
                f"Successfully generated competitive analysis for meeting {meeting.id}"
            )
            return result

        except Exception as e:
            logger.error(
                f"Error generating competitive analysis for meeting {meeting.id}: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "competitive_analysis_generated": False,
            }

    def generate_preparation_materials(
        self, meeting: Meeting, regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Generate comprehensive meeting preparation materials

        Args:
            meeting (Meeting): The meeting to generate preparation materials for
            regenerate (bool): Whether to regenerate existing materials

        Returns:
            dict: Complete preparation package with all materials
        """
        try:
            logger.info(
                f"Generating comprehensive preparation materials for meeting {meeting.id}"
            )

            # Generate all components
            agenda_result = self.generate_meeting_agenda(meeting, regenerate)
            talking_points_result = self.generate_talking_points(meeting)
            competitive_result = self.generate_competitive_analysis(meeting)

            # Generate additional preparation materials
            preparation_data = self._generate_additional_preparation_materials(meeting)

            # Compile comprehensive preparation package
            preparation_package = {
                "success": True,
                "meeting_id": str(meeting.id),
                "lead_company": meeting.lead.company_name,
                "meeting_type": meeting.meeting_type,
                "scheduled_at": (
                    meeting.scheduled_at.isoformat() if meeting.scheduled_at else None
                ),
                "duration_minutes": meeting.duration_minutes,
                "generated_at": timezone.now().isoformat(),
                # Core components
                "agenda": agenda_result,
                "talking_points": talking_points_result,
                "competitive_analysis": competitive_result,
                # Additional materials
                "preparation_checklist": preparation_data.get(
                    "preparation_checklist", []
                ),
                "key_research_points": preparation_data.get("key_research_points", []),
                "potential_objections": preparation_data.get(
                    "potential_objections", []
                ),
                "success_criteria": preparation_data.get("success_criteria", []),
                "follow_up_actions": preparation_data.get("follow_up_actions", []),
                "risk_mitigation": preparation_data.get("risk_mitigation", []),
                # Summary insights
                "preparation_summary": {
                    "meeting_readiness_score": preparation_data.get(
                        "meeting_readiness_score", 0
                    ),
                    "key_focus_areas": preparation_data.get("key_focus_areas", []),
                    "critical_success_factors": preparation_data.get(
                        "critical_success_factors", []
                    ),
                    "recommended_approach": preparation_data.get(
                        "recommended_approach", ""
                    ),
                    "time_to_prepare_minutes": preparation_data.get(
                        "time_to_prepare_minutes", 30
                    ),
                },
            }

            # Update meeting with comprehensive preparation data
            current_insights = meeting.ai_insights or {}
            current_insights.update(
                {
                    "preparation_materials": {
                        "generated_at": timezone.now().isoformat(),
                        "materials_generated": True,
                        "readiness_score": preparation_data.get(
                            "meeting_readiness_score", 0
                        ),
                        "preparation_time_minutes": preparation_data.get(
                            "time_to_prepare_minutes", 30
                        ),
                        "components_generated": [
                            "agenda",
                            "talking_points",
                            "competitive_analysis",
                            "preparation_checklist",
                        ],
                    }
                }
            )
            meeting.ai_insights = current_insights
            meeting.save(update_fields=["ai_insights", "updated_at"])

            logger.info(
                f"Successfully generated comprehensive preparation materials for meeting {meeting.id}"
            )
            return preparation_package

        except Exception as e:
            logger.error(
                f"Error generating preparation materials for meeting {meeting.id}: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "meeting_id": str(meeting.id) if meeting else None,
            }

    def _extract_lead_data(self, lead: Lead) -> Dict[str, Any]:
        """Extract lead data for AI processing"""
        return {
            "company_name": lead.company_name,
            "industry": lead.industry,
            "company_size": lead.company_size,
            "contact_info": lead.contact_info,
            "pain_points": lead.pain_points,
            "requirements": lead.requirements,
            "budget_info": lead.budget_info,
            "timeline": lead.timeline,
            "decision_makers": lead.decision_makers,
            "urgency_level": lead.urgency_level,
            "current_solution": lead.current_solution,
            "competitors_mentioned": lead.competitors_mentioned,
            "status": lead.status,
            "conversation_history": lead.conversation_history,
        }

    def _get_meeting_context(self, meeting: Meeting) -> Dict[str, Any]:
        """Get comprehensive meeting context"""
        return {
            "meeting_type": meeting.meeting_type,
            "duration_minutes": meeting.duration_minutes,
            "meeting_status": meeting.status,
            "scheduled_at": (
                meeting.scheduled_at.isoformat() if meeting.scheduled_at else None
            ),
            "participants": meeting.participants,
            "existing_agenda": meeting.agenda,
            "previous_meetings": self._get_previous_meeting_context(meeting.lead),
            "ai_insights": self._serialize_ai_insights(meeting.lead),
        }

    def _get_previous_meeting_context(self, lead: Lead) -> Dict[str, Any]:
        """Get context from previous meetings with this lead"""
        previous_meetings = Meeting.objects.filter(
            lead=lead, status=Meeting.Status.COMPLETED
        ).order_by("-scheduled_at")[
            :3
        ]  # Last 3 meetings

        context = {
            "previous_meeting_count": previous_meetings.count(),
            "previous_outcomes": [],
            "previous_agendas": [],
            "progression_notes": [],
        }

        for meeting in previous_meetings:
            if meeting.outcome:
                context["previous_outcomes"].append(meeting.outcome)
            if meeting.agenda:
                context["previous_agendas"].append(meeting.agenda)

            # Extract progression insights from AI insights
            if meeting.ai_insights and "meeting_outcome" in meeting.ai_insights:
                context["progression_notes"].append(
                    meeting.ai_insights["meeting_outcome"]
                )

        return context

    def _get_competitive_context(self, lead: Lead) -> Dict[str, Any]:
        """Get competitive context for analysis"""
        return {
            "competitors_mentioned": lead.competitors_mentioned or [],
            "current_solution": lead.current_solution,
            "industry": lead.industry,
            "company_size": lead.company_size,
            "budget_constraints": lead.budget_info,
            "decision_criteria": lead.requirements or [],
        }

    def _serialize_ai_insights(self, lead: Lead) -> Dict[str, Any]:
        """Serialize AI insights for JSON compatibility"""
        try:
            if hasattr(lead, "ai_insights") and lead.ai_insights:
                insights = lead.ai_insights
                return {
                    "lead_score": insights.lead_score,
                    "conversion_probability": insights.conversion_probability,
                    "quality_tier": insights.quality_tier,
                    "recommended_actions": insights.recommended_actions,
                    "key_messaging": insights.key_messaging,
                    "risk_factors": insights.risk_factors,
                    "opportunities": insights.opportunities,
                    "next_best_action": insights.next_best_action,
                }
            return {}
        except Exception as e:
            logger.warning(f"Error serializing AI insights: {e}")
            return {}

    def _generate_ai_agenda(
        self, lead_data: Dict[str, Any], meeting_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI-powered meeting agenda"""
        prompt = f"""
        You are an expert sales meeting strategist. Generate a comprehensive meeting agenda based on the lead information and meeting context provided.
        
        Lead Information: {lead_data}
        Meeting Context: {meeting_context}
        
        Create a structured agenda that includes:
        1. Time allocation for each section
        2. Key objectives for each agenda item
        3. Specific talking points and questions
        4. Success metrics and desired outcomes
        
        Provide the response in this EXACT JSON format:
        {{
            "formatted_agenda": "Complete formatted agenda text with timing",
            "agenda_structure": {{
                "opening": {{
                    "duration_minutes": 5,
                    "objectives": ["build rapport", "set expectations"],
                    "key_points": ["introduction", "agenda overview"]
                }},
                "discovery": {{
                    "duration_minutes": 20,
                    "objectives": ["understand pain points", "qualify needs"],
                    "key_points": ["current challenges", "desired outcomes"]
                }},
                "presentation": {{
                    "duration_minutes": 25,
                    "objectives": ["demonstrate value", "address concerns"],
                    "key_points": ["solution overview", "benefits alignment"]
                }},
                "next_steps": {{
                    "duration_minutes": 10,
                    "objectives": ["define follow-up", "maintain momentum"],
                    "key_points": ["action items", "timeline"]
                }}
            }},
            "key_objectives": ["primary meeting goals"],
            "time_allocation": {{
                "total_minutes": 60,
                "opening_percentage": 8,
                "discovery_percentage": 33,
                "presentation_percentage": 42,
                "next_steps_percentage": 17
            }},
            "success_metrics": ["measurable outcomes to track"],
            "generation_metadata": {{
                "agenda_type": "discovery|demo|proposal|closing",
                "complexity_level": "low|medium|high",
                "customization_level": "standard|customized|highly_customized"
            }}
        }}
        
        Tailor the agenda specifically to this lead's industry, company size, and identified needs.
        """

        try:
            response = self.ai_service._make_api_call(prompt)
            response_text = response.text.strip()
            return self.ai_service._parse_ai_response(response_text)
        except Exception as e:
            logger.error(f"Error generating AI agenda: {e}")
            return self._get_default_agenda()

    def _generate_ai_talking_points(
        self, lead_data: Dict[str, Any], meeting_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI-powered talking points"""
        prompt = f"""
        You are an expert sales conversation strategist. Generate compelling talking points for this sales meeting.
        
        Lead Information: {lead_data}
        Meeting Context: {meeting_context}
        
        Create talking points that are:
        1. Personalized to the lead's specific situation
        2. Focused on their pain points and requirements
        3. Positioned to differentiate our solution
        4. Designed to move the conversation forward
        
        Provide the response in this EXACT JSON format:
        {{
            "opening_statements": [
                "personalized opening statement that builds rapport",
                "agenda setting statement that creates structure"
            ],
            "value_propositions": [
                "primary value proposition aligned with their needs",
                "secondary benefits specific to their industry",
                "quantified benefits where possible"
            ],
            "pain_point_discussions": [
                "empathetic acknowledgment of their challenges",
                "probing questions to deepen understanding",
                "validation of their concerns"
            ],
            "solution_positioning": [
                "how our solution addresses their specific needs",
                "differentiation from competitors they mentioned",
                "proof points and success stories"
            ],
            "closing_statements": [
                "summary of key discussion points",
                "clear next steps and commitments",
                "momentum-building closing"
            ],
            "conversation_bridges": [
                "smooth transitions between topics",
                "ways to redirect if conversation goes off-track",
                "techniques to maintain engagement"
            ],
            "personalization_notes": [
                "specific details to mention about their company",
                "industry-specific terminology to use",
                "cultural or regional considerations"
            ]
        }}
        
        Make all talking points specific to this lead's situation and industry.
        """

        try:
            response = self.ai_service._make_api_call(prompt)
            response_text = response.text.strip()
            return self.ai_service._parse_ai_response(response_text)
        except Exception as e:
            logger.error(f"Error generating AI talking points: {e}")
            return self._get_default_talking_points()

    def _generate_ai_competitive_analysis(
        self, lead_data: Dict[str, Any], competitive_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI-powered competitive analysis"""
        prompt = f"""
        You are an expert competitive intelligence analyst. Generate a comprehensive competitive analysis for this sales meeting.
        
        Lead Information: {lead_data}
        Competitive Context: {competitive_context}
        
        Analyze the competitive landscape and provide strategic positioning recommendations.
        
        Provide the response in this EXACT JSON format:
        {{
            "identified_competitors": [
                {{
                    "name": "competitor name",
                    "market_position": "leader|challenger|niche",
                    "strengths": ["key strengths"],
                    "weaknesses": ["key weaknesses"],
                    "likely_approach": "how they would position against us"
                }}
            ],
            "competitive_landscape": {{
                "market_maturity": "emerging|growing|mature",
                "competitive_intensity": "low|medium|high",
                "key_differentiators": ["what matters most in this market"],
                "buyer_priorities": ["what buyers care about most"]
            }},
            "differentiation_points": [
                "our unique advantages vs competitors",
                "specific features/benefits they can't match",
                "proof points that support our differentiation"
            ],
            "competitive_threats": [
                "potential objections competitors might raise",
                "areas where we might be vulnerable",
                "competitive moves to watch for"
            ],
            "positioning_strategy": {{
                "primary_message": "main positioning statement",
                "supporting_points": ["key supporting arguments"],
                "proof_points": ["evidence to support our position"],
                "competitive_response": "how to handle competitive comparisons"
            }},
            "objection_responses": {{
                "price_objections": "how to handle price comparisons",
                "feature_objections": "how to handle feature gaps",
                "vendor_objections": "how to handle vendor concerns",
                "timing_objections": "how to handle timing concerns"
            }},
            "competitive_risk_level": "low|medium|high"
        }}
        
        Focus on actionable insights that will help win this specific deal.
        """

        try:
            response = self.ai_service._make_api_call(prompt)
            response_text = response.text.strip()
            return self.ai_service._parse_ai_response(response_text)
        except Exception as e:
            logger.error(f"Error generating AI competitive analysis: {e}")
            return self._get_default_competitive_analysis()

    def _generate_additional_preparation_materials(
        self, meeting: Meeting
    ) -> Dict[str, Any]:
        """Generate additional preparation materials"""
        lead_data = self._extract_lead_data(meeting.lead)
        meeting_context = self._get_meeting_context(meeting)

        prompt = f"""
        You are an expert sales preparation coach. Generate comprehensive preparation materials for this sales meeting.
        
        Lead Information: {lead_data}
        Meeting Context: {meeting_context}
        
        Create practical preparation materials that will ensure meeting success.
        
        Provide the response in this EXACT JSON format:
        {{
            "preparation_checklist": [
                "specific preparation tasks to complete before the meeting",
                "research items to review",
                "materials to prepare or bring"
            ],
            "key_research_points": [
                "important facts about their company to know",
                "industry trends that might be relevant",
                "recent news or developments to mention"
            ],
            "potential_objections": [
                "likely objections they might raise",
                "concerns they might have",
                "hesitations to address proactively"
            ],
            "success_criteria": [
                "specific outcomes that would make this meeting successful",
                "measurable goals to achieve",
                "progress indicators to track"
            ],
            "follow_up_actions": [
                "potential next steps to propose",
                "follow-up materials to offer",
                "commitments to be prepared to make"
            ],
            "risk_mitigation": [
                "potential risks and how to avoid them",
                "backup plans if things don't go as expected",
                "ways to recover from difficult moments"
            ],
            "meeting_readiness_score": 85,
            "key_focus_areas": [
                "most important areas to focus on during the meeting"
            ],
            "critical_success_factors": [
                "factors that will determine meeting success"
            ],
            "recommended_approach": "overall recommended approach for this meeting",
            "time_to_prepare_minutes": 30
        }}
        
        Make all recommendations specific and actionable for this particular meeting.
        """

        try:
            response = self.ai_service._make_api_call(prompt)
            response_text = response.text.strip()
            return self.ai_service._parse_ai_response(response_text)
        except Exception as e:
            logger.error(f"Error generating additional preparation materials: {e}")
            return self._get_default_preparation_materials()

    def _format_existing_agenda(self, meeting: Meeting) -> Dict[str, Any]:
        """Format existing agenda for return"""
        return {
            "success": True,
            "agenda_generated": True,
            "formatted_agenda": meeting.agenda,
            "existing_agenda": True,
            "generation_metadata": {
                "source": "existing",
                "last_updated": meeting.updated_at.isoformat(),
            },
        }

    def _get_default_agenda(self) -> Dict[str, Any]:
        """Get default agenda structure when AI generation fails"""
        return {
            "formatted_agenda": """
MEETING AGENDA

1. Opening & Introductions (5 minutes)
   - Welcome and introductions
   - Agenda overview and objectives

2. Discovery & Needs Assessment (20 minutes)
   - Current situation and challenges
   - Requirements and priorities
   - Success criteria

3. Solution Presentation (25 minutes)
   - Solution overview
   - Benefits and value proposition
   - Addressing specific needs

4. Next Steps & Follow-up (10 minutes)
   - Summary of key points
   - Action items and timeline
   - Schedule follow-up
            """.strip(),
            "agenda_structure": {
                "opening": {
                    "duration_minutes": 5,
                    "objectives": ["introductions", "set expectations"],
                },
                "discovery": {
                    "duration_minutes": 20,
                    "objectives": ["understand needs", "qualify requirements"],
                },
                "presentation": {
                    "duration_minutes": 25,
                    "objectives": ["demonstrate value", "address concerns"],
                },
                "next_steps": {
                    "duration_minutes": 10,
                    "objectives": ["define follow-up", "maintain momentum"],
                },
            },
            "key_objectives": [
                "understand needs",
                "demonstrate value",
                "advance opportunity",
            ],
            "time_allocation": {
                "total_minutes": 60,
                "opening_percentage": 8,
                "discovery_percentage": 33,
                "presentation_percentage": 42,
                "next_steps_percentage": 17,
            },
            "success_metrics": [
                "clear next steps defined",
                "stakeholder engagement",
                "needs qualification",
            ],
            "generation_metadata": {
                "agenda_type": "standard",
                "complexity_level": "medium",
                "customization_level": "standard",
            },
        }

    def _get_default_talking_points(self) -> Dict[str, Any]:
        """Get default talking points when AI generation fails"""
        return {
            "opening_statements": [
                "Thank you for taking the time to meet with us today",
                "I'd like to start by understanding your current situation and challenges",
            ],
            "value_propositions": [
                "Our solution helps organizations improve efficiency and reduce costs",
                "We've helped similar companies achieve measurable results",
            ],
            "pain_point_discussions": [
                "I understand you're facing some challenges in this area",
                "Can you tell me more about how this impacts your business?",
            ],
            "solution_positioning": [
                "Based on what you've shared, our solution can address these specific needs",
                "Here's how we've helped other companies in similar situations",
            ],
            "closing_statements": [
                "Let me summarize what we've discussed today",
                "What would you like to see as our next step?",
            ],
            "conversation_bridges": [
                "That's a great point, let me build on that",
                "Speaking of that, I'd like to show you how we address this",
            ],
            "personalization_notes": [
                "Research the company's recent news and developments",
                "Understand their industry-specific challenges",
            ],
        }

    def _get_default_competitive_analysis(self) -> Dict[str, Any]:
        """Get default competitive analysis when AI generation fails"""
        return {
            "identified_competitors": [],
            "competitive_landscape": {
                "market_maturity": "growing",
                "competitive_intensity": "medium",
                "key_differentiators": ["quality", "service", "innovation"],
                "buyer_priorities": ["value", "reliability", "support"],
            },
            "differentiation_points": [
                "Superior customer service and support",
                "Proven track record of success",
                "Innovative approach to solving problems",
            ],
            "competitive_threats": [
                "Price-based competition",
                "Feature comparison challenges",
                "Vendor relationship concerns",
            ],
            "positioning_strategy": {
                "primary_message": "We deliver superior value through innovation and service",
                "supporting_points": [
                    "proven results",
                    "customer satisfaction",
                    "industry expertise",
                ],
                "proof_points": ["case studies", "testimonials", "awards"],
                "competitive_response": "Focus on total value and long-term partnership",
            },
            "objection_responses": {
                "price_objections": "Focus on total cost of ownership and ROI",
                "feature_objections": "Emphasize unique capabilities and benefits",
                "vendor_objections": "Highlight stability, support, and partnership approach",
                "timing_objections": "Create urgency through compelling events",
            },
            "competitive_risk_level": "medium",
        }

    def _get_default_preparation_materials(self) -> Dict[str, Any]:
        """Get default preparation materials when AI generation fails"""
        return {
            "preparation_checklist": [
                "Review lead information and conversation history",
                "Prepare relevant case studies and materials",
                "Test technology and presentation materials",
                "Confirm meeting logistics and attendees",
            ],
            "key_research_points": [
                "Company background and recent news",
                "Industry trends and challenges",
                "Key stakeholders and decision makers",
            ],
            "potential_objections": [
                "Budget constraints",
                "Timing concerns",
                "Competitive alternatives",
                "Implementation complexity",
            ],
            "success_criteria": [
                "Clear understanding of needs and requirements",
                "Stakeholder engagement and interest",
                "Defined next steps and timeline",
            ],
            "follow_up_actions": [
                "Send meeting summary and next steps",
                "Provide requested information or materials",
                "Schedule follow-up meeting or demo",
            ],
            "risk_mitigation": [
                "Prepare for technical questions",
                "Have backup materials ready",
                "Plan for different meeting scenarios",
            ],
            "meeting_readiness_score": 75,
            "key_focus_areas": [
                "Understanding customer needs",
                "Demonstrating value proposition",
                "Building relationships",
            ],
            "critical_success_factors": [
                "Active listening and engagement",
                "Clear value demonstration",
                "Strong follow-up plan",
            ],
            "recommended_approach": "Focus on discovery and relationship building",
            "time_to_prepare_minutes": 30,
        }
