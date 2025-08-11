"""
Meeting Outcome Tracking Service

This service handles post-meeting analysis, action item extraction,
follow-up scheduling, and lead scoring updates based on meeting outcomes.
"""

import json
import logging
from datetime import timedelta
from typing import Any, Dict, List

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from ai_service.models import AIInsights
from ai_service.services import GeminiAIService

from .models import Meeting, MeetingQuestion

User = get_user_model()
logger = logging.getLogger(__name__)


class MeetingOutcomeService:
    """Service for tracking and analyzing meeting outcomes"""

    def __init__(self):
        self.ai_service = GeminiAIService()

    def generate_meeting_summary(
        self, meeting: Meeting, regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Generate comprehensive post-meeting summary and key takeaways

        Args:
            meeting: Meeting instance
            regenerate: Whether to regenerate existing summary

        Returns:
            Dict containing summary data and success status
        """
        try:
            # Check if summary already exists and regenerate is False
            if meeting.outcome and not regenerate:
                return {
                    "success": True,
                    "message": "Meeting summary already exists",
                    "summary": meeting.outcome,
                }

            # Gather meeting context
            meeting_context = self._gather_meeting_context(meeting)

            # Generate AI-powered summary
            summary_prompt = self._build_summary_prompt(meeting, meeting_context)

            try:
                response = self.ai_service._make_api_call(summary_prompt)
                response_text = response.text.strip()

                # Parse and structure the summary
                summary_data = self._parse_summary_response(response_text)

            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to generate meeting summary: {str(e)}",
                }

            # Update meeting with summary
            meeting.outcome = summary_data.get("summary", "")

            # Update AI insights with meeting outcomes
            if "ai_insights" not in meeting.ai_insights:
                meeting.ai_insights["ai_insights"] = {}

            meeting.ai_insights["meeting_summary"] = summary_data
            meeting.ai_insights["summary_generated_at"] = timezone.now().isoformat()
            meeting.save()

            logger.info(f"Generated meeting summary for meeting {meeting.id}")

            return {
                "success": True,
                "summary": summary_data,
                "message": "Meeting summary generated successfully",
            }

        except Exception as e:
            logger.error(
                f"Error generating meeting summary for meeting {meeting.id}: {str(e)}"
            )
            return {
                "success": False,
                "error": f"Error generating meeting summary: {str(e)}",
            }

    def extract_action_items(
        self, meeting: Meeting, regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Extract and assign action items from meeting content

        Args:
            meeting: Meeting instance
            regenerate: Whether to regenerate existing action items

        Returns:
            Dict containing action items and success status
        """
        try:
            # Check if action items already exist and regenerate is False
            if meeting.action_items and not regenerate:
                return {
                    "success": True,
                    "message": "Action items already exist",
                    "action_items": meeting.action_items,
                }

            # Gather meeting context for action item extraction
            meeting_context = self._gather_meeting_context(meeting)

            # Generate AI-powered action item extraction
            action_items_prompt = self._build_action_items_prompt(
                meeting, meeting_context
            )

            try:
                response = self.ai_service._make_api_call(action_items_prompt)
                response_text = response.text.strip()

                # Parse and structure action items
                action_items_data = self._parse_action_items_response(response_text)

            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to extract action items: {str(e)}",
                }

            # Update meeting with action items
            meeting.action_items = action_items_data.get("action_items", [])

            # Update AI insights
            if "action_items_analysis" not in meeting.ai_insights:
                meeting.ai_insights["action_items_analysis"] = {}

            meeting.ai_insights["action_items_analysis"] = action_items_data
            meeting.ai_insights["action_items_generated_at"] = (
                timezone.now().isoformat()
            )
            meeting.save()

            logger.info(f"Extracted action items for meeting {meeting.id}")

            return {
                "success": True,
                "action_items": action_items_data,
                "message": "Action items extracted successfully",
            }

        except Exception as e:
            logger.error(
                f"Error extracting action items for meeting {meeting.id}: {str(e)}"
            )
            return {
                "success": False,
                "error": f"Error extracting action items: {str(e)}",
            }

    def schedule_follow_up_actions(self, meeting: Meeting) -> Dict[str, Any]:
        """
        Schedule next steps and follow-up actions based on meeting outcomes

        Args:
            meeting: Meeting instance

        Returns:
            Dict containing follow-up schedule and success status
        """
        try:
            # Gather meeting context and outcomes
            meeting_context = self._gather_meeting_context(meeting)

            # Generate AI-powered follow-up recommendations
            follow_up_prompt = self._build_follow_up_prompt(meeting, meeting_context)

            try:
                response = self.ai_service._make_api_call(follow_up_prompt)
                response_text = response.text.strip()

                # Parse follow-up recommendations
                follow_up_data = self._parse_follow_up_response(response_text)

            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to generate follow-up recommendations: {str(e)}",
                }

            # Update AI insights with follow-up plan
            if "follow_up_plan" not in meeting.ai_insights:
                meeting.ai_insights["follow_up_plan"] = {}

            meeting.ai_insights["follow_up_plan"] = follow_up_data
            meeting.ai_insights["follow_up_generated_at"] = timezone.now().isoformat()
            meeting.save()

            # Create follow-up meetings if recommended
            follow_up_meetings = self._create_follow_up_meetings(
                meeting, follow_up_data
            )

            logger.info(f"Scheduled follow-up actions for meeting {meeting.id}")

            return {
                "success": True,
                "follow_up_plan": follow_up_data,
                "follow_up_meetings": follow_up_meetings,
                "message": "Follow-up actions scheduled successfully",
            }

        except Exception as e:
            logger.error(
                f"Error scheduling follow-up actions for meeting {meeting.id}: {str(e)}"
            )
            return {
                "success": False,
                "error": f"Error scheduling follow-up actions: {str(e)}",
            }

    def update_lead_scoring(self, meeting: Meeting) -> Dict[str, Any]:
        """
        Update lead scoring based on meeting outcomes and insights

        Args:
            meeting: Meeting instance

        Returns:
            Dict containing updated scoring and success status
        """
        try:
            if not meeting.lead:
                return {"success": False, "error": "No lead associated with meeting"}

            # Gather meeting outcomes and context
            meeting_outcomes = self._analyze_meeting_outcomes(meeting)

            # Get or create AI insights for the lead
            ai_insights, created = AIInsights.objects.get_or_create(
                lead=meeting.lead,
                defaults={
                    "lead_score": 0.0,
                    "conversion_probability": 0.0,
                    "confidence_score": 0.0,
                    "data_completeness": 0.0,
                },
            )

            # Calculate updated scores based on meeting outcomes
            updated_scores = self._calculate_updated_scores(
                ai_insights, meeting_outcomes
            )

            # Update AI insights with new scores
            with transaction.atomic():
                ai_insights.lead_score = updated_scores["lead_score"]
                ai_insights.conversion_probability = updated_scores[
                    "conversion_probability"
                ]
                ai_insights.opportunity_conversion_score = updated_scores[
                    "opportunity_conversion_score"
                ]

                # Update quality tier based on new score
                if ai_insights.lead_score >= 80:
                    ai_insights.quality_tier = AIInsights.QualityTier.HIGH
                elif ai_insights.lead_score >= 60:
                    ai_insights.quality_tier = AIInsights.QualityTier.MEDIUM
                else:
                    ai_insights.quality_tier = AIInsights.QualityTier.LOW

                # Update recommendations based on meeting outcomes
                ai_insights.recommended_actions = updated_scores.get(
                    "recommended_actions", []
                )
                ai_insights.next_steps = updated_scores.get("next_steps", [])
                ai_insights.next_best_action = updated_scores.get(
                    "next_best_action", ""
                )

                # Update risk and opportunity analysis
                ai_insights.risk_factors = updated_scores.get("risk_factors", [])
                ai_insights.opportunities = updated_scores.get("opportunities", [])

                # Update conversion readiness
                ai_insights.recommended_for_conversion = updated_scores.get(
                    "recommended_for_conversion", False
                )
                ai_insights.conversion_readiness_factors = updated_scores.get(
                    "conversion_readiness_factors", []
                )

                # Update confidence and completeness
                ai_insights.confidence_score = updated_scores.get(
                    "confidence_score", ai_insights.confidence_score
                )
                ai_insights.data_completeness = updated_scores.get(
                    "data_completeness", ai_insights.data_completeness
                )

                ai_insights.save()

            # Update meeting AI insights with scoring changes
            meeting.ai_insights["lead_scoring_update"] = {
                "previous_scores": {
                    "lead_score": updated_scores.get("previous_lead_score", 0),
                    "conversion_probability": updated_scores.get(
                        "previous_conversion_probability", 0
                    ),
                },
                "updated_scores": {
                    "lead_score": ai_insights.lead_score,
                    "conversion_probability": ai_insights.conversion_probability,
                },
                "score_changes": updated_scores.get("score_changes", {}),
                "meeting_impact": meeting_outcomes,
                "updated_at": timezone.now().isoformat(),
            }
            meeting.save()

            logger.info(
                f"Updated lead scoring for meeting {meeting.id} and lead {meeting.lead.id}"
            )

            return {
                "success": True,
                "updated_scores": {
                    "lead_score": ai_insights.lead_score,
                    "conversion_probability": ai_insights.conversion_probability,
                    "quality_tier": ai_insights.quality_tier,
                    "opportunity_conversion_score": ai_insights.opportunity_conversion_score,
                },
                "score_changes": updated_scores.get("score_changes", {}),
                "meeting_impact": meeting_outcomes,
                "message": "Lead scoring updated successfully",
            }

        except Exception as e:
            logger.error(
                f"Error updating lead scoring for meeting {meeting.id}: {str(e)}"
            )
            return {"success": False, "error": f"Error updating lead scoring: {str(e)}"}

    def process_complete_meeting_outcome(
        self, meeting: Meeting, regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Process complete meeting outcome including all tracking components

        Args:
            meeting: Meeting instance
            regenerate: Whether to regenerate existing data

        Returns:
            Dict containing all outcome processing results
        """
        try:
            results = {
                "meeting_id": str(meeting.id),
                "processing_started_at": timezone.now().isoformat(),
                "components": {},
            }

            # 1. Generate meeting summary
            summary_result = self.generate_meeting_summary(meeting, regenerate)
            results["components"]["summary"] = summary_result

            # 2. Extract action items
            action_items_result = self.extract_action_items(meeting, regenerate)
            results["components"]["action_items"] = action_items_result

            # 3. Schedule follow-up actions
            follow_up_result = self.schedule_follow_up_actions(meeting)
            results["components"]["follow_up"] = follow_up_result

            # 4. Update lead scoring
            scoring_result = self.update_lead_scoring(meeting)
            results["components"]["lead_scoring"] = scoring_result

            # Determine overall success
            all_successful = all(
                component.get("success", False)
                for component in results["components"].values()
            )

            results["overall_success"] = all_successful
            results["processing_completed_at"] = timezone.now().isoformat()

            if all_successful:
                results["message"] = (
                    "All meeting outcome components processed successfully"
                )
            else:
                failed_components = [
                    name
                    for name, component in results["components"].items()
                    if not component.get("success", False)
                ]
                results["message"] = (
                    f'Some components failed: {", ".join(failed_components)}'
                )

            logger.info(f"Processed complete meeting outcome for meeting {meeting.id}")

            return results

        except Exception as e:
            logger.error(
                f"Error processing complete meeting outcome for meeting {meeting.id}: {str(e)}"
            )
            return {
                "overall_success": False,
                "error": f"Error processing meeting outcome: {str(e)}",
                "meeting_id": str(meeting.id),
            }

    # Private helper methods

    def _gather_meeting_context(self, meeting: Meeting) -> Dict[str, Any]:
        """Gather comprehensive meeting context for analysis"""
        context = {
            "meeting_info": {
                "title": meeting.title,
                "description": meeting.description,
                "meeting_type": meeting.meeting_type,
                "duration_minutes": meeting.duration_minutes,
                "actual_duration": meeting.actual_duration_minutes,
                "status": meeting.status,
                "agenda": meeting.agenda,
                "participants": meeting.participants,
            },
            "lead_context": {},
            "questions_asked": [],
            "existing_insights": {},
        }

        # Add lead context if available
        if meeting.lead:
            context["lead_context"] = {
                "company_name": meeting.lead.company_name,
                "industry": meeting.lead.industry,
                "company_size": meeting.lead.company_size,
                "contact_info": meeting.lead.contact_info,
                "status": meeting.lead.status,
                "pain_points": meeting.lead.pain_points,
                "requirements": meeting.lead.requirements,
                "budget_info": meeting.lead.budget_info,
                "timeline": meeting.lead.timeline,
                "decision_makers": meeting.lead.decision_makers,
                "urgency_level": meeting.lead.urgency_level,
            }

            # Add AI insights if available
            if hasattr(meeting.lead, "ai_insights"):
                context["existing_insights"] = {
                    "lead_score": meeting.lead.ai_insights.lead_score,
                    "conversion_probability": meeting.lead.ai_insights.conversion_probability,
                    "quality_tier": meeting.lead.ai_insights.quality_tier,
                    "recommended_actions": meeting.lead.ai_insights.recommended_actions,
                    "risk_factors": meeting.lead.ai_insights.risk_factors,
                    "opportunities": meeting.lead.ai_insights.opportunities,
                }

        # Add questions asked during meeting
        questions = MeetingQuestion.objects.filter(
            meeting=meeting, asked_at__isnull=False
        ).order_by("asked_at")

        for question in questions:
            context["questions_asked"].append(
                {
                    "question_text": question.question_text,
                    "question_type": question.question_type,
                    "response": question.response,
                    "asked_at": (
                        question.asked_at.isoformat() if question.asked_at else None
                    ),
                }
            )

        return context

    def _build_summary_prompt(self, meeting: Meeting, context: Dict[str, Any]) -> str:
        """Build AI prompt for meeting summary generation"""
        return f"""
        As an AI sales assistant, analyze this meeting and generate a comprehensive post-meeting summary.
        
        Meeting Information:
        - Title: {context['meeting_info']['title']}
        - Type: {context['meeting_info']['meeting_type']}
        - Duration: {context['meeting_info']['duration_minutes']} minutes
        - Agenda: {context['meeting_info']['agenda']}
        - Description: {context['meeting_info']['description']}
        
        Lead Context:
        - Company: {context['lead_context'].get('company_name', 'N/A')}
        - Industry: {context['lead_context'].get('industry', 'N/A')}
        - Pain Points: {', '.join(context['lead_context'].get('pain_points', []))}
        - Requirements: {', '.join(context['lead_context'].get('requirements', []))}
        
        Questions Asked and Responses:
        {self._format_questions_for_prompt(context['questions_asked'])}
        
        Please provide a structured meeting summary in JSON format with the following sections:
        {{
            "summary": "Overall meeting summary (2-3 paragraphs)",
            "key_takeaways": ["List of 3-5 key takeaways"],
            "discussion_highlights": ["Important discussion points"],
            "client_feedback": "Summary of client feedback and reactions",
            "pain_points_discussed": ["Pain points that were discussed"],
            "requirements_clarified": ["Requirements that were clarified or identified"],
            "decision_makers_identified": ["Decision makers mentioned or identified"],
            "budget_timeline_info": "Any budget or timeline information discussed",
            "competitive_mentions": ["Any competitors or alternatives mentioned"],
            "objections_raised": ["Any objections or concerns raised"],
            "positive_signals": ["Positive buying signals observed"],
            "meeting_effectiveness": "Assessment of meeting effectiveness (1-10 scale with explanation)",
            "next_meeting_recommendations": "Recommendations for next meeting type and focus"
        }}
        
        Focus on extracting actionable insights that will help with lead qualification and sales progression.
        """

    def _build_action_items_prompt(
        self, meeting: Meeting, context: Dict[str, Any]
    ) -> str:
        """Build AI prompt for action items extraction"""
        return f"""
        As an AI sales assistant, analyze this meeting and extract specific action items and assignments.
        
        Meeting Context:
        - Title: {context['meeting_info']['title']}
        - Type: {context['meeting_info']['meeting_type']}
        - Company: {context['lead_context'].get('company_name', 'N/A')}
        - Participants: {', '.join(context['meeting_info'].get('participants', []))}
        
        Meeting Content:
        - Agenda: {context['meeting_info']['agenda']}
        - Description: {context['meeting_info']['description']}
        - Questions and Responses: {self._format_questions_for_prompt(context['questions_asked'])}
        
        Please extract and structure action items in JSON format:
        {{
            "action_items": [
                {{
                    "id": "unique_id",
                    "description": "Clear description of the action",
                    "assigned_to": "Person responsible (sales rep, client, team member)",
                    "due_date": "Suggested due date (YYYY-MM-DD format)",
                    "priority": "high|medium|low",
                    "category": "follow_up|research|proposal|demo|documentation|internal",
                    "dependencies": ["List of dependencies if any"],
                    "success_criteria": "How to measure completion"
                }}
            ],
            "immediate_actions": ["Actions that need to be done within 24 hours"],
            "follow_up_meetings": [
                {{
                    "type": "demo|proposal|negotiation|closing",
                    "suggested_timeframe": "within X days/weeks",
                    "purpose": "Purpose of the follow-up meeting",
                    "participants": ["Required participants"]
                }}
            ],
            "research_tasks": ["Information that needs to be researched"],
            "internal_coordination": ["Internal team coordination needed"],
            "client_deliverables": ["Items to be delivered to the client"]
        }}
        
        Focus on specific, actionable items with clear ownership and deadlines.
        """

    def _build_follow_up_prompt(self, meeting: Meeting, context: Dict[str, Any]) -> str:
        """Build AI prompt for follow-up scheduling"""
        return f"""
        As an AI sales assistant, analyze this meeting outcome and recommend a comprehensive follow-up strategy.
        
        Meeting Analysis:
        - Type: {context['meeting_info']['meeting_type']}
        - Company: {context['lead_context'].get('company_name', 'N/A')}
        - Current Lead Status: {context['lead_context'].get('status', 'N/A')}
        - Urgency Level: {context['lead_context'].get('urgency_level', 'N/A')}
        
        Current Lead Intelligence:
        - Lead Score: {context['existing_insights'].get('lead_score', 'N/A')}
        - Conversion Probability: {context['existing_insights'].get('conversion_probability', 'N/A')}%
        - Quality Tier: {context['existing_insights'].get('quality_tier', 'N/A')}
        
        Meeting Outcomes:
        - Questions Asked: {len(context['questions_asked'])} questions
        - Key Discussion Points: {self._format_questions_for_prompt(context['questions_asked'])}
        
        Please provide a structured follow-up plan in JSON format:
        {{
            "immediate_follow_up": {{
                "timeframe": "within X hours/days",
                "actions": ["Specific immediate actions"],
                "communication_method": "email|phone|meeting",
                "key_message": "Main message to communicate"
            }},
            "short_term_follow_up": {{
                "timeframe": "within X days/weeks",
                "recommended_meetings": [
                    {{
                        "type": "demo|proposal|technical_review|stakeholder_meeting",
                        "purpose": "Meeting purpose",
                        "duration_minutes": 60,
                        "participants": ["Required participants"],
                        "agenda_items": ["Key agenda items"]
                    }}
                ],
                "deliverables": ["Items to prepare and deliver"]
            }},
            "long_term_strategy": {{
                "sales_cycle_stage": "discovery|qualification|proposal|negotiation|closing",
                "next_milestone": "Next major milestone",
                "success_metrics": ["How to measure progress"],
                "risk_mitigation": ["Strategies to address identified risks"]
            }},
            "automation_triggers": [
                {{
                    "trigger": "time_based|response_based|milestone_based",
                    "condition": "Specific condition",
                    "action": "Automated action to take"
                }}
            ],
            "stakeholder_engagement": {{
                "decision_makers_to_engage": ["Key people to involve"],
                "engagement_strategy": "How to engage them",
                "messaging_approach": "Tailored messaging for each stakeholder"
            }}
        }}
        
        Base recommendations on the meeting outcomes and lead progression needs.
        """

    def _format_questions_for_prompt(self, questions: List[Dict]) -> str:
        """Format questions and responses for AI prompts"""
        if not questions:
            return "No questions were recorded for this meeting."

        formatted = []
        for q in questions:
            formatted.append(
                f"Q: {q['question_text']}\nA: {q.get('response', 'No response recorded')}"
            )

        return "\n\n".join(formatted)

    def _parse_summary_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for meeting summary"""
        try:
            # Try to parse as JSON first
            if response.strip().startswith("{"):
                return json.loads(response)
            else:
                # If not JSON, create structured response
                return {
                    "summary": response,
                    "key_takeaways": [],
                    "discussion_highlights": [],
                    "meeting_effectiveness": "Not assessed",
                }
        except json.JSONDecodeError:
            return {
                "summary": response,
                "key_takeaways": [],
                "discussion_highlights": [],
                "meeting_effectiveness": "Not assessed",
            }

    def _parse_action_items_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for action items"""
        try:
            if response.strip().startswith("{"):
                return json.loads(response)
            else:
                return {
                    "action_items": [],
                    "immediate_actions": [],
                    "follow_up_meetings": [],
                }
        except json.JSONDecodeError:
            return {
                "action_items": [],
                "immediate_actions": [],
                "follow_up_meetings": [],
            }

    def _parse_follow_up_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for follow-up recommendations"""
        try:
            if response.strip().startswith("{"):
                return json.loads(response)
            else:
                return {
                    "immediate_follow_up": {},
                    "short_term_follow_up": {},
                    "long_term_strategy": {},
                }
        except json.JSONDecodeError:
            return {
                "immediate_follow_up": {},
                "short_term_follow_up": {},
                "long_term_strategy": {},
            }

    def _analyze_meeting_outcomes(self, meeting: Meeting) -> Dict[str, Any]:
        """Analyze meeting outcomes for lead scoring updates"""
        outcomes = {
            "meeting_completed": meeting.status == Meeting.Status.COMPLETED,
            "meeting_type": meeting.meeting_type,
            "duration_vs_planned": 0,
            "questions_asked_count": 0,
            "questions_answered_count": 0,
            "engagement_indicators": [],
            "progression_signals": [],
            "risk_indicators": [],
        }

        # Calculate duration variance
        if meeting.actual_duration_minutes and meeting.duration_minutes:
            outcomes["duration_vs_planned"] = (
                meeting.actual_duration_minutes - meeting.duration_minutes
            ) / meeting.duration_minutes

        # Analyze questions and responses
        questions = MeetingQuestion.objects.filter(meeting=meeting)
        outcomes["questions_asked_count"] = questions.filter(
            asked_at__isnull=False
        ).count()
        outcomes["questions_answered_count"] = (
            questions.filter(asked_at__isnull=False, response__isnull=False)
            .exclude(response="")
            .count()
        )

        # Analyze engagement based on question responses
        for question in questions.filter(asked_at__isnull=False):
            if question.response:
                response_length = len(question.response.split())
                if response_length > 20:  # Detailed response
                    outcomes["engagement_indicators"].append("detailed_responses")
                if question.question_type in ["budget", "timeline", "decision_makers"]:
                    outcomes["progression_signals"].append(
                        f"{question.question_type}_discussed"
                    )

        # Check for risk indicators
        if outcomes["questions_asked_count"] > outcomes["questions_answered_count"] * 2:
            outcomes["risk_indicators"].append("low_response_rate")

        if (
            meeting.actual_duration_minutes
            and meeting.actual_duration_minutes < meeting.duration_minutes * 0.5
        ):
            outcomes["risk_indicators"].append("meeting_cut_short")

        return outcomes

    def _calculate_updated_scores(
        self, ai_insights: AIInsights, meeting_outcomes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate updated lead scores based on meeting outcomes"""
        # Store previous scores
        previous_lead_score = ai_insights.lead_score
        previous_conversion_probability = ai_insights.conversion_probability

        # Base score adjustments
        score_adjustments = {
            "meeting_completion": 0,
            "engagement_level": 0,
            "progression_signals": 0,
            "risk_factors": 0,
        }

        # Meeting completion bonus
        if meeting_outcomes["meeting_completed"]:
            score_adjustments["meeting_completion"] = 5

        # Engagement level adjustments
        engagement_score = 0
        if "detailed_responses" in meeting_outcomes["engagement_indicators"]:
            engagement_score += 10

        response_rate = meeting_outcomes["questions_answered_count"] / max(
            meeting_outcomes["questions_asked_count"], 1
        )
        engagement_score += response_rate * 15

        score_adjustments["engagement_level"] = engagement_score

        # Progression signals
        progression_score = len(meeting_outcomes["progression_signals"]) * 8
        score_adjustments["progression_signals"] = progression_score

        # Risk factor penalties
        risk_penalty = len(meeting_outcomes["risk_indicators"]) * -10
        score_adjustments["risk_factors"] = risk_penalty

        # Calculate new scores
        total_adjustment = sum(score_adjustments.values())
        new_lead_score = max(0, min(100, ai_insights.lead_score + total_adjustment))

        # Conversion probability adjustment (more conservative)
        conversion_adjustment = total_adjustment * 0.6
        new_conversion_probability = max(
            0, min(100, ai_insights.conversion_probability + conversion_adjustment)
        )

        # Opportunity conversion score
        opportunity_conversion_score = max(
            0,
            min(100, ai_insights.opportunity_conversion_score + total_adjustment * 0.8),
        )

        # Generate updated recommendations
        updated_recommendations = self._generate_updated_recommendations(
            meeting_outcomes, new_lead_score
        )

        return {
            "previous_lead_score": previous_lead_score,
            "previous_conversion_probability": previous_conversion_probability,
            "lead_score": new_lead_score,
            "conversion_probability": new_conversion_probability,
            "opportunity_conversion_score": opportunity_conversion_score,
            "score_changes": score_adjustments,
            "recommended_actions": updated_recommendations.get(
                "recommended_actions", []
            ),
            "next_steps": updated_recommendations.get("next_steps", []),
            "next_best_action": updated_recommendations.get("next_best_action", ""),
            "risk_factors": updated_recommendations.get("risk_factors", []),
            "opportunities": updated_recommendations.get("opportunities", []),
            "recommended_for_conversion": new_lead_score >= 70
            and new_conversion_probability >= 60,
            "conversion_readiness_factors": updated_recommendations.get(
                "conversion_readiness_factors", []
            ),
            "confidence_score": min(
                100, ai_insights.confidence_score + 5
            ),  # Increase confidence with more data
            "data_completeness": min(
                100, ai_insights.data_completeness + 10
            ),  # More complete after meeting
        }

    def _generate_updated_recommendations(
        self, meeting_outcomes: Dict[str, Any], lead_score: float
    ) -> Dict[str, Any]:
        """Generate updated recommendations based on meeting outcomes"""
        recommendations = {
            "recommended_actions": [],
            "next_steps": [],
            "next_best_action": "",
            "risk_factors": [],
            "opportunities": [],
            "conversion_readiness_factors": [],
        }

        # High-score lead recommendations
        if lead_score >= 80:
            recommendations["recommended_actions"].extend(
                [
                    "Prepare detailed proposal",
                    "Schedule stakeholder presentation",
                    "Conduct technical deep-dive session",
                ]
            )
            recommendations["next_best_action"] = (
                "Schedule proposal presentation with decision makers"
            )
            recommendations["conversion_readiness_factors"].append(
                "High engagement in meeting"
            )

        # Medium-score lead recommendations
        elif lead_score >= 60:
            recommendations["recommended_actions"].extend(
                [
                    "Continue qualification process",
                    "Schedule product demonstration",
                    "Gather additional requirements",
                ]
            )
            recommendations["next_best_action"] = "Schedule product demonstration"

        # Low-score lead recommendations
        else:
            recommendations["recommended_actions"].extend(
                [
                    "Focus on pain point discovery",
                    "Build stronger relationship",
                    "Identify decision makers",
                ]
            )
            recommendations["next_best_action"] = (
                "Schedule discovery call to better understand needs"
            )

        # Add risk factors based on meeting outcomes
        if meeting_outcomes["risk_indicators"]:
            recommendations["risk_factors"].extend(
                [
                    f"Meeting concern: {risk}"
                    for risk in meeting_outcomes["risk_indicators"]
                ]
            )

        # Add opportunities based on progression signals
        if meeting_outcomes["progression_signals"]:
            recommendations["opportunities"].extend(
                [
                    f"Positive signal: {signal}"
                    for signal in meeting_outcomes["progression_signals"]
                ]
            )

        # Generate next steps based on meeting type
        meeting_type = meeting_outcomes.get("meeting_type", "")
        if meeting_type == "discovery":
            recommendations["next_steps"].extend(
                [
                    "Send meeting summary and next steps",
                    "Research specific use cases mentioned",
                    "Prepare customized demo",
                ]
            )
        elif meeting_type == "demo":
            recommendations["next_steps"].extend(
                [
                    "Send demo recording and materials",
                    "Prepare pricing proposal",
                    "Schedule stakeholder meeting",
                ]
            )
        elif meeting_type == "proposal":
            recommendations["next_steps"].extend(
                [
                    "Follow up on proposal feedback",
                    "Address any concerns raised",
                    "Schedule closing meeting",
                ]
            )

        return recommendations

    def _create_follow_up_meetings(
        self, meeting: Meeting, follow_up_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create follow-up meetings based on recommendations"""
        follow_up_meetings = []

        try:
            # Get recommended meetings from follow-up data
            recommended_meetings = follow_up_data.get("short_term_follow_up", {}).get(
                "recommended_meetings", []
            )

            for meeting_rec in recommended_meetings:
                # Calculate suggested date
                timeframe = meeting_rec.get("timeframe", "within 1 week")
                days_ahead = self._parse_timeframe_to_days(timeframe)
                suggested_date = timezone.now() + timedelta(days=days_ahead)

                follow_up_meeting_data = {
                    "title": f"{meeting_rec.get('type', 'Follow-up').title()} - {meeting.lead.company_name}",
                    "meeting_type": meeting_rec.get("type", "follow_up"),
                    "suggested_date": suggested_date.isoformat(),
                    "duration_minutes": meeting_rec.get("duration_minutes", 60),
                    "purpose": meeting_rec.get("purpose", ""),
                    "participants": meeting_rec.get("participants", []),
                    "agenda_items": meeting_rec.get("agenda_items", []),
                }

                follow_up_meetings.append(follow_up_meeting_data)

        except Exception as e:
            logger.error(f"Error creating follow-up meetings: {str(e)}")

        return follow_up_meetings

    def _parse_timeframe_to_days(self, timeframe: str) -> int:
        """Parse timeframe string to number of days"""
        timeframe = timeframe.lower()

        if "hour" in timeframe:
            return 1  # Same day or next day
        elif "day" in timeframe:
            # Extract number of days
            import re

            match = re.search(r"(\d+)", timeframe)
            return int(match.group(1)) if match else 3
        elif "week" in timeframe:
            # Extract number of weeks
            import re

            match = re.search(r"(\d+)", timeframe)
            weeks = int(match.group(1)) if match else 1
            return weeks * 7
        else:
            return 7  # Default to 1 week
