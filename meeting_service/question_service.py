"""
Meeting Question Service - Handles AI-generated questions for meetings
"""

import logging
from typing import Any, Dict, List

from django.utils import timezone

from ai_service.models import Lead
from ai_service.services import GeminiAIService

from .models import Meeting, MeetingQuestion

logger = logging.getLogger(__name__)


class MeetingQuestionService:
    """Service for generating and managing AI-powered meeting questions"""

    def __init__(self):
        self.ai_service = GeminiAIService()

    def generate_questions_for_meeting(
        self, meeting: Meeting, regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Generate AI-powered questions for a specific meeting

        Args:
            meeting (Meeting): The meeting to generate questions for
            regenerate (bool): Whether to regenerate existing questions

        Returns:
            dict: Generated questions with metadata
        """
        try:
            # Check if questions already exist and regenerate is False
            if not regenerate and meeting.questions.exists():
                logger.info(
                    f"Questions already exist for meeting {meeting.id}, skipping generation"
                )
                return self._format_existing_questions(meeting)

            # Get lead data for context
            lead_data = self._extract_lead_data(meeting.lead)

            # Prepare meeting context
            meeting_context = {
                "meeting_type": meeting.meeting_type,
                "meeting_status": meeting.status,
                "agenda": meeting.agenda,
                "previous_meetings": self._get_previous_meeting_context(meeting.lead),
                "ai_insights": self._serialize_ai_insights(meeting.lead),
            }

            # Generate questions using AI service
            logger.info(
                f"Generating questions for meeting {meeting.id} with lead {meeting.lead.company_name}"
            )
            questions_data = self.ai_service.generate_meeting_questions(
                lead_data, meeting_context
            )

            # Clear existing questions if regenerating
            if regenerate:
                meeting.questions.all().delete()
                logger.info(f"Cleared existing questions for meeting {meeting.id}")

            # Create MeetingQuestion objects
            created_questions = self._create_meeting_questions(meeting, questions_data)

            # Update meeting AI insights with question generation metadata
            self._update_meeting_insights(meeting, questions_data, created_questions)

            result = {
                "success": True,
                "questions_generated": len(created_questions),
                "questions_by_type": self._group_questions_by_type(created_questions),
                "generation_metadata": questions_data.get("question_strategy", {}),
                "created_questions": [
                    self._serialize_question(q) for q in created_questions
                ],
            }

            logger.info(
                f"Successfully generated {len(created_questions)} questions for meeting {meeting.id}"
            )
            return result

        except Exception as e:
            logger.error(f"Error generating questions for meeting {meeting.id}: {e}")
            return {"success": False, "error": str(e), "questions_generated": 0}

    def get_prioritized_questions(
        self, meeting: Meeting, limit: int = None
    ) -> List[MeetingQuestion]:
        """
        Get questions for a meeting ordered by priority and sequence

        Args:
            meeting (Meeting): The meeting to get questions for
            limit (int): Optional limit on number of questions

        Returns:
            list: Prioritized list of MeetingQuestion objects
        """
        questions = meeting.questions.filter(ai_generated=True).order_by(
            "-priority", "sequence_order", "question_type"
        )

        if limit:
            questions = questions[:limit]

        return list(questions)

    def get_questions_by_type(
        self, meeting: Meeting, question_type: str
    ) -> List[MeetingQuestion]:
        """
        Get questions of a specific type for a meeting

        Args:
            meeting (Meeting): The meeting to get questions for
            question_type (str): The type of questions to retrieve

        Returns:
            list: List of MeetingQuestion objects of the specified type
        """
        return list(
            meeting.questions.filter(
                question_type=question_type, ai_generated=True
            ).order_by("-priority", "sequence_order")
        )

    def get_conversion_focused_questions(
        self, meeting: Meeting
    ) -> List[MeetingQuestion]:
        """
        Get questions that are focused on conversion (budget, timeline, decision makers, closing)

        Args:
            meeting (Meeting): The meeting to get questions for

        Returns:
            list: List of conversion-focused MeetingQuestion objects
        """
        conversion_types = [
            MeetingQuestion.QuestionType.BUDGET,
            MeetingQuestion.QuestionType.TIMELINE,
            MeetingQuestion.QuestionType.DECISION_MAKERS,
            MeetingQuestion.QuestionType.CLOSING,
        ]

        return list(
            meeting.questions.filter(
                question_type__in=conversion_types, ai_generated=True
            ).order_by("-priority", "sequence_order")
        )

    def mark_question_asked(
        self, question: MeetingQuestion, response: str = "", response_quality: str = ""
    ) -> bool:
        """
        Mark a question as asked and record the response

        Args:
            question (MeetingQuestion): The question that was asked
            response (str): The response received
            response_quality (str): Quality assessment of the response

        Returns:
            bool: Success status
        """
        try:
            question.mark_as_asked(response)
            if response_quality:
                question.response_quality = response_quality
                question.save(update_fields=["response_quality", "updated_at"])

            # Generate follow-up questions if needed
            if question.triggers_follow_up and response:
                self._generate_follow_up_questions(question, response)

            logger.info(f"Marked question {question.id} as asked")
            return True

        except Exception as e:
            logger.error(f"Error marking question {question.id} as asked: {e}")
            return False

    def update_question_effectiveness(
        self, question: MeetingQuestion, outcome_data: Dict[str, Any]
    ) -> bool:
        """
        Update the effectiveness score of a question based on outcomes

        Args:
            question (MeetingQuestion): The question to update
            outcome_data (dict): Data about the question's effectiveness

        Returns:
            bool: Success status
        """
        try:
            question.calculate_effectiveness(outcome_data)
            logger.info(f"Updated effectiveness for question {question.id}")
            return True

        except Exception as e:
            logger.error(f"Error updating question effectiveness {question.id}: {e}")
            return False

    def _extract_lead_data(self, lead: Lead) -> Dict[str, Any]:
        """Extract lead data for AI question generation"""
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
            "previous_questions_asked": [],
        }

        for meeting in previous_meetings:
            if meeting.outcome:
                context["previous_outcomes"].append(meeting.outcome)

            # Get questions that were asked in previous meetings
            asked_questions = meeting.questions.filter(asked_at__isnull=False)
            for question in asked_questions:
                context["previous_questions_asked"].append(
                    {
                        "type": question.question_type,
                        "question": question.question_text,
                        "response": question.response,
                    }
                )

        return context

    def _serialize_ai_insights(self, lead: Lead) -> Dict[str, Any]:
        """Serialize AI insights for JSON compatibility"""
        try:
            if hasattr(lead, "ai_insights") and lead.ai_insights:
                insights = lead.ai_insights
                return {
                    "lead_score": insights.lead_score,
                    "conversion_probability": insights.conversion_probability,
                    "quality_tier": insights.quality_tier,
                    "opportunity_conversion_score": insights.opportunity_conversion_score,
                    "recommended_for_conversion": insights.recommended_for_conversion,
                    "estimated_deal_size": insights.estimated_deal_size,
                    "sales_cycle_prediction": insights.sales_cycle_prediction,
                    "primary_strategy": insights.primary_strategy,
                    "competitive_risk": insights.competitive_risk,
                    "next_best_action": insights.next_best_action,
                    "recommended_actions": insights.recommended_actions,
                    "key_messaging": insights.key_messaging,
                    "risk_factors": insights.risk_factors,
                    "opportunities": insights.opportunities,
                }
            return {}
        except Exception as e:
            logger.warning(f"Error serializing AI insights: {e}")
            return {}

    def _create_meeting_questions(
        self, meeting: Meeting, questions_data: Dict[str, Any]
    ) -> List[MeetingQuestion]:
        """Create MeetingQuestion objects from AI-generated data"""
        created_questions = []
        sequence_counter = 1

        # Question type mapping
        type_mapping = {
            "discovery_questions": MeetingQuestion.QuestionType.DISCOVERY,
            "budget_questions": MeetingQuestion.QuestionType.BUDGET,
            "timeline_questions": MeetingQuestion.QuestionType.TIMELINE,
            "decision_maker_questions": MeetingQuestion.QuestionType.DECISION_MAKERS,
            "pain_point_questions": MeetingQuestion.QuestionType.PAIN_POINTS,
            "requirements_questions": MeetingQuestion.QuestionType.REQUIREMENTS,
            "competitive_questions": MeetingQuestion.QuestionType.COMPETITION,
            "closing_questions": MeetingQuestion.QuestionType.CLOSING,
        }

        for category, question_type in type_mapping.items():
            questions_list = questions_data.get(category, [])

            for question_data in questions_list:
                try:
                    # Determine priority level based on numeric priority
                    priority_num = question_data.get("priority", 5)
                    if priority_num >= 8:
                        priority_level = MeetingQuestion.Priority.HIGH
                    elif priority_num >= 6:
                        priority_level = MeetingQuestion.Priority.MEDIUM
                    else:
                        priority_level = MeetingQuestion.Priority.LOW

                    question = MeetingQuestion.objects.create(
                        meeting=meeting,
                        question_text=question_data.get("question", ""),
                        question_type=question_type,
                        priority=priority_num,
                        priority_level=priority_level,
                        ai_generated=True,
                        generation_context={
                            "rationale": question_data.get("rationale", ""),
                            "expected_insights": question_data.get(
                                "expected_insights", []
                            ),
                            "follow_up_triggers": question_data.get(
                                "follow_up_triggers", []
                            ),
                            "category": category,
                        },
                        confidence_score=question_data.get("confidence_score", 70.0),
                        industry_specific=question_data.get("industry_specific", False),
                        triggers_follow_up=bool(
                            question_data.get("follow_up_triggers")
                        ),
                        sequence_order=sequence_counter,
                    )

                    created_questions.append(question)
                    sequence_counter += 1

                except Exception as e:
                    logger.error(
                        f"Error creating question from data {question_data}: {e}"
                    )
                    continue

        return created_questions

    def _update_meeting_insights(
        self,
        meeting: Meeting,
        questions_data: Dict[str, Any],
        created_questions: List[MeetingQuestion],
    ):
        """Update meeting AI insights with question generation data"""
        try:
            current_insights = meeting.ai_insights or {}

            current_insights.update(
                {
                    "question_generation": {
                        "generated_at": timezone.now().isoformat(),
                        "total_questions": len(created_questions),
                        "questions_by_type": self._group_questions_by_type(
                            created_questions
                        ),
                        "strategy": questions_data.get("question_strategy", {}),
                        "high_priority_questions": len(
                            [q for q in created_questions if q.is_high_priority]
                        ),
                        "conversion_focused_questions": len(
                            [q for q in created_questions if q.is_conversion_focused]
                        ),
                    }
                }
            )

            meeting.ai_insights = current_insights
            meeting.save(update_fields=["ai_insights", "updated_at"])

        except Exception as e:
            logger.error(f"Error updating meeting insights: {e}")

    def _group_questions_by_type(
        self, questions: List[MeetingQuestion]
    ) -> Dict[str, int]:
        """Group questions by type and return counts"""
        type_counts = {}
        for question in questions:
            question_type = question.get_question_type_display()
            type_counts[question_type] = type_counts.get(question_type, 0) + 1
        return type_counts

    def _format_existing_questions(self, meeting: Meeting) -> Dict[str, Any]:
        """Format existing questions for return"""
        questions = list(meeting.questions.all())

        return {
            "success": True,
            "questions_generated": len(questions),
            "questions_by_type": self._group_questions_by_type(questions),
            "existing_questions": True,
            "created_questions": [self._serialize_question(q) for q in questions],
        }

    def _serialize_question(self, question: MeetingQuestion) -> Dict[str, Any]:
        """Serialize a MeetingQuestion object for API response"""
        return {
            "id": str(question.id),
            "question_text": question.question_text,
            "question_type": question.question_type,
            "question_type_display": question.get_question_type_display(),
            "priority": question.priority,
            "priority_level": question.priority_level,
            "confidence_score": question.confidence_score,
            "industry_specific": question.industry_specific,
            "conversion_focused": question.is_conversion_focused,
            "sequence_order": question.sequence_order,
            "asked_at": question.asked_at.isoformat() if question.asked_at else None,
            "response": question.response,
            "generation_context": question.generation_context,
            "created_at": question.created_at.isoformat(),
        }

    def generate_dynamic_follow_ups(
        self,
        original_question: MeetingQuestion,
        response: str,
        conversation_context: dict = None,
    ) -> Dict[str, Any]:
        """
        Generate dynamic AI-powered follow-up questions based on response

        Args:
            original_question (MeetingQuestion): The original question that was asked
            response (str): The response received from the prospect
            conversation_context (dict): Additional conversation context

        Returns:
            dict: Generated follow-up questions with prioritization
        """
        try:
            # Prepare question data for AI service
            question_data = {
                "id": str(original_question.id),
                "question": original_question.question_text,
                "question_type": original_question.question_type,
                "priority": original_question.priority,
                "rationale": original_question.generation_context.get("rationale", ""),
            }

            # Get lead data
            lead_data = self._extract_lead_data(original_question.meeting.lead)

            # Generate dynamic follow-ups using AI service
            follow_ups = self.ai_service.generate_dynamic_follow_up_questions(
                question_data, response, lead_data, conversation_context
            )

            # Create new MeetingQuestion objects for immediate follow-ups
            created_follow_ups = self._create_follow_up_questions(
                original_question, follow_ups.get("immediate_follow_ups", [])
            )

            # Store all follow-up data in the original question
            self._store_follow_up_data(original_question, follow_ups, response)

            result = {
                "success": True,
                "immediate_follow_ups_created": len(created_follow_ups),
                "conditional_follow_ups": len(
                    follow_ups.get("conditional_follow_ups", [])
                ),
                "deep_dive_questions": len(follow_ups.get("deep_dive_questions", [])),
                "response_insights": follow_ups.get("response_insights", {}),
                "created_questions": [
                    self._serialize_question(q) for q in created_follow_ups
                ],
            }

            logger.info(
                f"Generated dynamic follow-ups for question {original_question.id}: {result}"
            )
            return result

        except Exception as e:
            logger.error(f"Error generating dynamic follow-ups: {e}")
            return {
                "success": False,
                "error": str(e),
                "immediate_follow_ups_created": 0,
            }

    def adapt_questions_for_conversation(
        self, meeting: Meeting, conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Adapt remaining questions based on conversation flow and responses

        Args:
            meeting (Meeting): The meeting to adapt questions for
            conversation_history (list): History of questions and responses

        Returns:
            dict: Adapted questions with new priorities and recommendations
        """
        try:
            # Get remaining questions (not yet asked)
            remaining_questions = list(meeting.questions.filter(asked_at__isnull=True))

            if not remaining_questions:
                logger.info(f"No remaining questions to adapt for meeting {meeting.id}")
                return {
                    "success": True,
                    "adaptations_made": 0,
                    "message": "No remaining questions to adapt",
                }

            # Prepare questions data for AI service
            questions_data = [
                {
                    "id": str(q.id),
                    "question": q.question_text,
                    "question_type": q.question_type,
                    "priority": q.priority,
                    "sequence_order": q.sequence_order,
                    "asked_at": None,
                }
                for q in remaining_questions
            ]

            # Get lead data
            lead_data = self._extract_lead_data(meeting.lead)

            # Generate adaptations using AI service
            adaptations = self.ai_service.adapt_questions_based_on_conversation(
                questions_data, conversation_history, lead_data
            )

            # Apply adaptations to questions
            adaptation_results = self._apply_question_adaptations(
                meeting, adaptations, remaining_questions
            )

            # Update meeting insights with adaptation data
            self._update_meeting_adaptation_insights(
                meeting, adaptations, adaptation_results
            )

            result = {
                "success": True,
                "adaptations_made": adaptation_results["total_adaptations"],
                "questions_modified": adaptation_results["questions_modified"],
                "questions_added": adaptation_results["questions_added"],
                "questions_skipped": adaptation_results["questions_skipped"],
                "conversation_insights": adaptations.get("conversation_insights", {}),
                "recommended_sequence": adaptations.get("recommended_sequence", []),
            }

            logger.info(f"Adapted questions for meeting {meeting.id}: {result}")
            return result

        except Exception as e:
            logger.error(f"Error adapting questions for conversation: {e}")
            return {"success": False, "error": str(e), "adaptations_made": 0}

    def track_question_effectiveness(
        self, question: MeetingQuestion, response: str, outcome_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Track and analyze question effectiveness for learning and improvement

        Args:
            question (MeetingQuestion): The question to analyze
            response (str): The response received
            outcome_data (dict): Data about the question's effectiveness

        Returns:
            dict: Effectiveness analysis and learning insights
        """
        try:
            # Prepare question data for AI service
            question_data = {
                "id": str(question.id),
                "question": question.question_text,
                "question_type": question.question_type,
                "priority": question.priority,
                "rationale": question.generation_context.get("rationale", ""),
                "confidence_score": question.confidence_score,
            }

            # Generate effectiveness analysis using AI service
            effectiveness = self.ai_service.track_question_effectiveness(
                question_data, response, outcome_data
            )

            # Update question with effectiveness data
            self._update_question_effectiveness(question, effectiveness)

            # Store learning insights for future question generation
            self._store_learning_insights(question, effectiveness)

            result = {
                "success": True,
                "effectiveness_score": effectiveness.get("effectiveness_score", 0),
                "effectiveness_tier": effectiveness.get("effectiveness_tier", "medium"),
                "key_insights": effectiveness.get("key_insights_gained", []),
                "learning_insights": effectiveness.get("learning_insights", {}),
                "recommendations": effectiveness.get("recommendations", {}),
            }

            logger.info(f"Tracked effectiveness for question {question.id}: {result}")
            return result

        except Exception as e:
            logger.error(f"Error tracking question effectiveness: {e}")
            return {"success": False, "error": str(e), "effectiveness_score": 0}

    def generate_industry_specific_questions(
        self, meeting: Meeting, regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Generate industry-specific question templates and apply them to the meeting

        Args:
            meeting (Meeting): The meeting to generate questions for
            regenerate (bool): Whether to regenerate existing questions

        Returns:
            dict: Generated industry-specific questions
        """
        try:
            lead = meeting.lead
            industry = lead.industry or "technology"
            company_size = lead.company_size

            # Generate industry-specific templates
            templates = self.ai_service.generate_industry_question_templates(
                industry, company_size
            )

            # Apply templates to create meeting questions
            created_questions = self._apply_industry_templates(
                meeting, templates, regenerate
            )

            # Update meeting insights with industry-specific data
            self._update_meeting_industry_insights(
                meeting, templates, created_questions
            )

            result = {
                "success": True,
                "industry": industry,
                "templates_generated": len(
                    templates.get("discovery_meeting", {}).get(
                        "pain_point_questions", []
                    )
                ),
                "questions_created": len(created_questions),
                "industry_insights": templates.get("industry_insights", {}),
                "created_questions": [
                    self._serialize_question(q) for q in created_questions
                ],
            }

            logger.info(
                f"Generated industry-specific questions for meeting {meeting.id}: {result}"
            )
            return result

        except Exception as e:
            logger.error(f"Error generating industry-specific questions: {e}")
            return {"success": False, "error": str(e), "questions_created": 0}

    def _create_follow_up_questions(
        self, original_question: MeetingQuestion, follow_up_data: List[Dict[str, Any]]
    ) -> List[MeetingQuestion]:
        """Create MeetingQuestion objects from follow-up data"""
        created_questions = []

        for follow_up in follow_up_data:
            try:
                # Determine priority level
                priority_num = follow_up.get("priority", 5)
                if priority_num >= 8:
                    priority_level = MeetingQuestion.Priority.HIGH
                elif priority_num >= 6:
                    priority_level = MeetingQuestion.Priority.MEDIUM
                else:
                    priority_level = MeetingQuestion.Priority.LOW

                # Map question type
                question_type = self._map_question_type(
                    follow_up.get("question_type", "discovery")
                )

                question = MeetingQuestion.objects.create(
                    meeting=original_question.meeting,
                    question_text=follow_up.get("question", ""),
                    question_type=question_type,
                    priority=priority_num,
                    priority_level=priority_level,
                    ai_generated=True,
                    generation_context={
                        "rationale": follow_up.get("rationale", ""),
                        "response_trigger": follow_up.get("response_trigger", ""),
                        "expected_outcome": follow_up.get("expected_outcome", ""),
                        "original_question_id": str(original_question.id),
                        "generation_type": "dynamic_follow_up",
                    },
                    confidence_score=follow_up.get("confidence_score", 75.0),
                    triggers_follow_up=True,
                    depends_on_question=original_question,
                    sequence_order=original_question.sequence_order + 1,
                )

                created_questions.append(question)

            except Exception as e:
                logger.error(f"Error creating follow-up question: {e}")
                continue

        return created_questions

    def _store_follow_up_data(
        self,
        original_question: MeetingQuestion,
        follow_ups: Dict[str, Any],
        response: str,
    ):
        """Store follow-up data in the original question"""
        try:
            current_follow_ups = original_question.follow_up_questions or []

            new_follow_up_entry = {
                "generated_at": timezone.now().isoformat(),
                "response": response,
                "immediate_follow_ups": follow_ups.get("immediate_follow_ups", []),
                "conditional_follow_ups": follow_ups.get("conditional_follow_ups", []),
                "deep_dive_questions": follow_ups.get("deep_dive_questions", []),
                "response_insights": follow_ups.get("response_insights", {}),
            }

            current_follow_ups.append(new_follow_up_entry)
            original_question.follow_up_questions = current_follow_ups
            original_question.save(update_fields=["follow_up_questions", "updated_at"])

        except Exception as e:
            logger.error(f"Error storing follow-up data: {e}")

    def _apply_question_adaptations(
        self,
        meeting: Meeting,
        adaptations: Dict[str, Any],
        remaining_questions: List[MeetingQuestion],
    ) -> Dict[str, Any]:
        """Apply question adaptations to the meeting questions"""
        results = {
            "total_adaptations": 0,
            "questions_modified": 0,
            "questions_added": 0,
            "questions_skipped": 0,
        }

        try:
            # Create a mapping of question IDs for easy lookup
            question_map = {str(q.id): q for q in remaining_questions}

            # Apply adapted questions
            for adapted in adaptations.get("adapted_questions", []):
                question_id = adapted.get("original_question_id")
                if question_id in question_map:
                    question = question_map[question_id]
                    question.question_text = adapted.get(
                        "adapted_question", question.question_text
                    )
                    question.priority = adapted.get("new_priority", question.priority)

                    # Update generation context with adaptation info
                    context = question.generation_context or {}
                    context["adaptation"] = {
                        "adapted_at": timezone.now().isoformat(),
                        "adaptation_reason": adapted.get("adaptation_reason", ""),
                        "timing_recommendation": adapted.get(
                            "timing_recommendation", ""
                        ),
                    }
                    question.generation_context = context
                    question.save()

                    results["questions_modified"] += 1
                    results["total_adaptations"] += 1

            # Create new questions
            for new_question in adaptations.get("new_questions", []):
                try:
                    question_type = self._map_question_type(
                        new_question.get("question_type", "discovery")
                    )
                    priority_num = new_question.get("priority", 5)

                    if priority_num >= 8:
                        priority_level = MeetingQuestion.Priority.HIGH
                    elif priority_num >= 6:
                        priority_level = MeetingQuestion.Priority.MEDIUM
                    else:
                        priority_level = MeetingQuestion.Priority.LOW

                    MeetingQuestion.objects.create(
                        meeting=meeting,
                        question_text=new_question.get("question", ""),
                        question_type=question_type,
                        priority=priority_num,
                        priority_level=priority_level,
                        ai_generated=True,
                        generation_context={
                            "rationale": new_question.get("rationale", ""),
                            "conversation_trigger": new_question.get(
                                "conversation_trigger", ""
                            ),
                            "generation_type": "conversation_adaptation",
                        },
                        confidence_score=75.0,
                        sequence_order=max(
                            [q.sequence_order for q in remaining_questions], default=0
                        )
                        + 1,
                    )

                    results["questions_added"] += 1
                    results["total_adaptations"] += 1

                except Exception as e:
                    logger.error(f"Error creating new adapted question: {e}")

            # Mark questions to skip
            for skip_item in adaptations.get("questions_to_skip", []):
                question_id = skip_item.get("question_id")
                if question_id in question_map:
                    question = question_map[question_id]

                    # Update generation context with skip info
                    context = question.generation_context or {}
                    context["skipped"] = {
                        "skipped_at": timezone.now().isoformat(),
                        "skip_reason": skip_item.get("skip_reason", ""),
                        "conversation_based": True,
                    }
                    question.generation_context = context
                    question.save()

                    results["questions_skipped"] += 1
                    results["total_adaptations"] += 1

        except Exception as e:
            logger.error(f"Error applying question adaptations: {e}")

        return results

    def _update_question_effectiveness(
        self, question: MeetingQuestion, effectiveness: Dict[str, Any]
    ):
        """Update question with effectiveness data"""
        try:
            question.effectiveness_score = effectiveness.get("effectiveness_score", 0)

            # Update generation context with effectiveness data
            context = question.generation_context or {}
            context["effectiveness_analysis"] = {
                "analyzed_at": timezone.now().isoformat(),
                "effectiveness_tier": effectiveness.get("effectiveness_tier", "medium"),
                "key_insights": effectiveness.get("key_insights_gained", []),
                "performance_breakdown": effectiveness.get(
                    "effectiveness_breakdown", {}
                ),
                "learning_insights": effectiveness.get("learning_insights", {}),
            }
            question.generation_context = context
            question.save()

        except Exception as e:
            logger.error(f"Error updating question effectiveness: {e}")

    def _store_learning_insights(
        self, question: MeetingQuestion, effectiveness: Dict[str, Any]
    ):
        """Store learning insights for future question generation improvement"""
        try:
            # This could be enhanced to store insights in a separate learning database
            # For now, we'll log the insights for future analysis
            learning_data = {
                "question_id": str(question.id),
                "question_type": question.question_type,
                "industry": question.meeting.lead.industry,
                "effectiveness_score": effectiveness.get("effectiveness_score", 0),
                "what_worked_well": effectiveness.get("learning_insights", {}).get(
                    "what_worked_well", []
                ),
                "improvement_opportunities": effectiveness.get(
                    "learning_insights", {}
                ).get("improvement_opportunities", []),
                "context_factors": effectiveness.get("learning_insights", {}).get(
                    "context_factors", []
                ),
            }

            logger.info(f"Learning insights for question improvement: {learning_data}")

        except Exception as e:
            logger.error(f"Error storing learning insights: {e}")

    def _apply_industry_templates(
        self, meeting: Meeting, templates: Dict[str, Any], regenerate: bool = False
    ) -> List[MeetingQuestion]:
        """Apply industry-specific templates to create meeting questions"""
        created_questions = []

        if not regenerate and meeting.questions.exists():
            logger.info(
                f"Questions already exist for meeting {meeting.id}, skipping template application"
            )
            return created_questions

        if regenerate:
            meeting.questions.all().delete()

        try:
            meeting_type = meeting.meeting_type.lower()
            template_key = f"{meeting_type}_meeting"

            if template_key not in templates:
                template_key = "discovery_meeting"  # Default fallback

            meeting_templates = templates.get(template_key, {})
            sequence_counter = 1

            # Process each question category in the template
            for category, questions_list in meeting_templates.items():
                if not isinstance(questions_list, list):
                    continue

                question_type = self._map_category_to_question_type(category)

                for template_data in questions_list:
                    try:
                        # Extract variables and create question text
                        question_text = self._populate_template_variables(
                            template_data.get("template", ""), meeting.lead
                        )

                        priority_num = template_data.get("priority", 7)
                        if priority_num >= 8:
                            priority_level = MeetingQuestion.Priority.HIGH
                        elif priority_num >= 6:
                            priority_level = MeetingQuestion.Priority.MEDIUM
                        else:
                            priority_level = MeetingQuestion.Priority.LOW

                        question = MeetingQuestion.objects.create(
                            meeting=meeting,
                            question_text=question_text,
                            question_type=question_type,
                            priority=priority_num,
                            priority_level=priority_level,
                            ai_generated=True,
                            generation_context={
                                "rationale": template_data.get("rationale", ""),
                                "expected_responses": template_data.get(
                                    "expected_responses", []
                                ),
                                "follow_up_triggers": template_data.get(
                                    "follow_up_triggers", []
                                ),
                                "template_category": category,
                                "generation_type": "industry_template",
                                "industry": meeting.lead.industry,
                            },
                            confidence_score=85.0,  # Higher confidence for industry-specific templates
                            industry_specific=True,
                            triggers_follow_up=bool(
                                template_data.get("follow_up_triggers")
                            ),
                            sequence_order=sequence_counter,
                        )

                        created_questions.append(question)
                        sequence_counter += 1

                    except Exception as e:
                        logger.error(
                            f"Error creating question from template {template_data}: {e}"
                        )
                        continue

        except Exception as e:
            logger.error(f"Error applying industry templates: {e}")

        return created_questions

    def _map_question_type(self, type_string: str) -> str:
        """Map question type string to MeetingQuestion.QuestionType"""
        type_mapping = {
            "discovery": MeetingQuestion.QuestionType.DISCOVERY,
            "budget": MeetingQuestion.QuestionType.BUDGET,
            "timeline": MeetingQuestion.QuestionType.TIMELINE,
            "decision_makers": MeetingQuestion.QuestionType.DECISION_MAKERS,
            "pain_points": MeetingQuestion.QuestionType.PAIN_POINTS,
            "requirements": MeetingQuestion.QuestionType.REQUIREMENTS,
            "competition": MeetingQuestion.QuestionType.COMPETITION,
            "closing": MeetingQuestion.QuestionType.CLOSING,
            "current_solution": MeetingQuestion.QuestionType.CURRENT_SOLUTION,
            "objection_handling": MeetingQuestion.QuestionType.OBJECTION_HANDLING,
        }

        return type_mapping.get(
            type_string.lower(), MeetingQuestion.QuestionType.DISCOVERY
        )

    def _map_category_to_question_type(self, category: str) -> str:
        """Map template category to question type"""
        category_mapping = {
            "pain_point_questions": MeetingQuestion.QuestionType.PAIN_POINTS,
            "current_state_questions": MeetingQuestion.QuestionType.CURRENT_SOLUTION,
            "stakeholder_questions": MeetingQuestion.QuestionType.DECISION_MAKERS,
            "requirements_questions": MeetingQuestion.QuestionType.REQUIREMENTS,
            "integration_questions": MeetingQuestion.QuestionType.REQUIREMENTS,
            "budget_questions": MeetingQuestion.QuestionType.BUDGET,
            "timeline_questions": MeetingQuestion.QuestionType.TIMELINE,
            "decision_process_questions": MeetingQuestion.QuestionType.DECISION_MAKERS,
            "objection_handling_questions": MeetingQuestion.QuestionType.OBJECTION_HANDLING,
        }

        return category_mapping.get(category, MeetingQuestion.QuestionType.DISCOVERY)

    def _populate_template_variables(self, template: str, lead) -> str:
        """Populate template variables with lead data"""
        try:
            # Simple variable substitution - could be enhanced with more sophisticated templating
            populated = template

            # Replace common variables
            if hasattr(lead, "company_name") and lead.company_name:
                populated = populated.replace("{company_name}", lead.company_name)
            if hasattr(lead, "industry") and lead.industry:
                populated = populated.replace("{industry}", lead.industry)
            if hasattr(lead, "company_size") and lead.company_size:
                populated = populated.replace("{company_size}", lead.company_size)

            # Remove any remaining template variables
            import re

            populated = re.sub(r"\{[^}]+\}", "[specific details]", populated)

            return populated

        except Exception as e:
            logger.error(f"Error populating template variables: {e}")
            return template

    def _update_meeting_adaptation_insights(
        self, meeting: Meeting, adaptations: Dict[str, Any], results: Dict[str, Any]
    ):
        """Update meeting insights with adaptation data"""
        try:
            current_insights = meeting.ai_insights or {}

            current_insights["question_adaptation"] = {
                "adapted_at": timezone.now().isoformat(),
                "total_adaptations": results["total_adaptations"],
                "questions_modified": results["questions_modified"],
                "questions_added": results["questions_added"],
                "questions_skipped": results["questions_skipped"],
                "conversation_insights": adaptations.get("conversation_insights", {}),
                "adaptation_confidence": adaptations.get("adaptation_metadata", {}).get(
                    "adaptation_confidence", 75.0
                ),
            }

            meeting.ai_insights = current_insights
            meeting.save(update_fields=["ai_insights", "updated_at"])

        except Exception as e:
            logger.error(f"Error updating meeting adaptation insights: {e}")

    def _update_meeting_industry_insights(
        self,
        meeting: Meeting,
        templates: Dict[str, Any],
        created_questions: List[MeetingQuestion],
    ):
        """Update meeting insights with industry-specific data"""
        try:
            current_insights = meeting.ai_insights or {}

            current_insights["industry_specialization"] = {
                "generated_at": timezone.now().isoformat(),
                "industry": meeting.lead.industry,
                "questions_created": len(created_questions),
                "industry_insights": templates.get("industry_insights", {}),
                "template_metadata": templates.get("template_metadata", {}),
                "specialization_confidence": 85.0,
            }

            meeting.ai_insights = current_insights
            meeting.save(update_fields=["ai_insights", "updated_at"])

        except Exception as e:
            logger.error(f"Error updating meeting industry insights: {e}")

    def _generate_follow_up_questions(
        self, original_question: MeetingQuestion, response: str
    ):
        """Legacy method - now redirects to dynamic follow-up generation"""
        try:
            result = self.generate_dynamic_follow_ups(original_question, response)
            logger.info(f"Generated follow-ups using dynamic system: {result}")

        except Exception as e:
            logger.error(f"Error generating follow-up questions: {e}")
