"""
Live Meeting Support Service for NIA Sales Assistant

This service provides real-time conversation analysis, question suggestions,
sentiment analysis, and key moment identification during active meetings.
"""

import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from django.core.cache import cache
from django.utils import timezone

from ai_service.models import Lead
from ai_service.services import GeminiAIService

from .models import Meeting

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation"""

    timestamp: datetime
    speaker: str  # 'user' or 'prospect'
    content: str
    duration_seconds: Optional[float] = None
    confidence_score: Optional[float] = None


@dataclass
class SentimentAnalysis:
    """Sentiment analysis results for conversation segments"""

    overall_sentiment: str  # 'positive', 'neutral', 'negative'
    sentiment_score: float  # -1.0 to 1.0
    engagement_level: str  # 'high', 'medium', 'low'
    engagement_score: float  # 0.0 to 100.0
    emotional_indicators: List[str]
    confidence_level: float  # 0.0 to 100.0


@dataclass
class KeyMoment:
    """Represents a key moment identified in the conversation"""

    timestamp: datetime
    moment_type: str  # 'buying_signal', 'objection', 'pain_point', 'decision_maker', 'budget_mention', 'timeline_mention'
    description: str
    importance_score: float  # 0.0 to 100.0
    context: str
    suggested_response: Optional[str] = None
    follow_up_actions: List[str] = None


@dataclass
class QuestionSuggestion:
    """AI-generated question suggestion based on conversation flow"""

    question_text: str
    question_type: str  # 'discovery', 'budget', 'timeline', 'decision_makers', 'pain_points', 'closing'
    priority_score: float  # 0.0 to 100.0
    rationale: str
    timing_suggestion: str  # 'immediate', 'after_current_topic', 'later_in_meeting'
    expected_outcome: str
    follow_up_questions: List[str] = None


@dataclass
class ObjectionHandlingAdvice:
    """AI-generated advice for handling objections"""

    objection_type: (
        str  # 'price', 'timing', 'authority', 'need', 'trust', 'competition'
    )
    objection_text: str
    recommended_response: str
    alternative_approaches: List[str]
    confidence_score: float  # 0.0 to 100.0
    urgency_level: str  # 'low', 'medium', 'high', 'critical'
    follow_up_questions: List[str] = None


@dataclass
class ClosingOpportunity:
    """Identified opportunity to close the deal"""

    opportunity_type: (
        str  # 'buying_signal', 'urgency', 'budget_confirmed', 'decision_maker_present'
    )
    description: str
    recommended_closing_technique: str
    closing_questions: List[str]
    confidence_score: float  # 0.0 to 100.0
    timing_recommendation: str  # 'immediate', 'within_5_minutes', 'end_of_meeting'
    risk_factors: List[str] = None


@dataclass
class FollowUpRecommendation:
    """AI-generated follow-up action recommendations"""

    action_type: str  # 'email', 'call', 'meeting', 'proposal', 'demo', 'reference'
    priority: str  # 'high', 'medium', 'low'
    recommended_timing: str  # 'immediate', 'same_day', 'within_24h', 'within_week'
    action_description: str
    rationale: str
    success_probability: float  # 0.0 to 100.0
    required_resources: List[str] = None


@dataclass
class InterventionAlert:
    """Alert for meetings that need intervention"""

    alert_type: str  # 'disengagement', 'strong_objection', 'competitor_mention', 'budget_concern', 'timeline_issue'
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    recommended_intervention: str
    immediate_actions: List[str]
    confidence_score: float  # 0.0 to 100.0
    triggered_at: datetime


@dataclass
class MeetingGuidance:
    """Complete AI meeting guidance package"""

    objection_advice: List[ObjectionHandlingAdvice]
    closing_opportunities: List[ClosingOpportunity]
    follow_up_recommendations: List[FollowUpRecommendation]
    intervention_alerts: List[InterventionAlert]
    overall_meeting_health: str  # 'excellent', 'good', 'concerning', 'critical'
    guidance_timestamp: datetime


@dataclass
class LiveAnalysisResult:
    """Complete real-time analysis result"""

    conversation_turns: List[ConversationTurn]
    sentiment_analysis: SentimentAnalysis
    key_moments: List[KeyMoment]
    question_suggestions: List[QuestionSuggestion]
    meeting_guidance: MeetingGuidance
    meeting_progress: Dict[str, Any]
    analysis_timestamp: datetime
    confidence_score: float


class LiveMeetingSupportService:
    """
    Service for providing real-time meeting support including conversation analysis,
    sentiment tracking, key moment identification, and intelligent question suggestions.
    """

    def __init__(self):
        self.ai_service = GeminiAIService()
        self.conversation_buffer = []
        self.analysis_cache_timeout = 30  # seconds
        self.min_analysis_interval = 10  # seconds between analyses

    def start_live_meeting_session(
        self, meeting_id: str, user_id: str
    ) -> Dict[str, Any]:
        """
        Initialize a live meeting session for real-time analysis

        Args:
            meeting_id: UUID of the meeting
            user_id: ID of the user conducting the meeting

        Returns:
            dict: Session initialization result
        """
        try:
            meeting = Meeting.objects.get(id=meeting_id)

            # Mark meeting as in progress
            meeting.mark_as_started()

            # Initialize session cache
            session_key = f"live_meeting_{meeting_id}"
            session_data = {
                "meeting_id": meeting_id,
                "user_id": user_id,
                "start_time": timezone.now().isoformat(),
                "conversation_turns": [],
                "last_analysis_time": None,
                "key_moments": [],
                "sentiment_history": [],
                "question_suggestions": [],
            }

            cache.set(session_key, session_data, timeout=3600)  # 1 hour timeout

            # Get initial meeting context and questions
            initial_questions = self._generate_initial_questions(meeting)

            logger.info(f"Started live meeting session for meeting {meeting_id}")

            return {
                "success": True,
                "session_id": session_key,
                "meeting_title": meeting.title,
                "lead_company": meeting.lead.company_name,
                "initial_questions": initial_questions,
                "meeting_context": {
                    "meeting_type": meeting.meeting_type,
                    "lead_info": self._get_lead_context(meeting.lead),
                    "ai_insights": self._get_ai_insights_context(meeting.lead),
                },
            }

        except Meeting.DoesNotExist:
            logger.error(f"Meeting {meeting_id} not found")
            return {"success": False, "error": "Meeting not found"}
        except Exception as e:
            logger.error(f"Error starting live meeting session: {e}")
            return {"success": False, "error": str(e)}

    def process_conversation_turn(
        self,
        session_id: str,
        speaker: str,
        content: str,
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Process a new conversation turn and provide real-time analysis

        Args:
            session_id: Live meeting session ID
            speaker: 'user' or 'prospect'
            content: Spoken content
            timestamp: When this was spoken (defaults to now)

        Returns:
            dict: Real-time analysis results
        """
        try:
            # Get session data
            session_data = cache.get(session_id)
            if not session_data:
                return {"success": False, "error": "Session not found or expired"}

            # Create conversation turn
            turn_timestamp = timestamp or timezone.now()
            conversation_turn = ConversationTurn(
                timestamp=turn_timestamp,
                speaker=speaker,
                content=content,
                confidence_score=self._calculate_transcription_confidence(content),
            )

            # Add to session conversation history
            session_data["conversation_turns"].append(asdict(conversation_turn))

            # Check if we should perform analysis
            should_analyze = self._should_perform_analysis(session_data, content)

            analysis_result = None
            if should_analyze:
                # Perform real-time analysis
                analysis_result = self._perform_live_analysis(
                    session_data, conversation_turn
                )
                session_data["last_analysis_time"] = turn_timestamp.isoformat()

            # Update session cache
            cache.set(session_id, session_data, timeout=3600)

            response = {
                "success": True,
                "conversation_turn": asdict(conversation_turn),
                "analysis_performed": should_analyze,
            }

            if analysis_result:
                response.update(
                    {
                        "sentiment_analysis": asdict(
                            analysis_result.sentiment_analysis
                        ),
                        "key_moments": [
                            asdict(moment) for moment in analysis_result.key_moments
                        ],
                        "question_suggestions": [
                            asdict(q) for q in analysis_result.question_suggestions
                        ],
                        "meeting_progress": analysis_result.meeting_progress,
                    }
                )

            return response

        except Exception as e:
            logger.error(f"Error processing conversation turn: {e}")
            return {"success": False, "error": str(e)}

    def get_real_time_suggestions(self, session_id: str) -> Dict[str, Any]:
        """
        Get current real-time suggestions for the meeting

        Args:
            session_id: Live meeting session ID

        Returns:
            dict: Current suggestions and analysis
        """
        try:
            session_data = cache.get(session_id)
            if not session_data:
                return {"success": False, "error": "Session not found or expired"}

            # Get recent conversation context
            recent_turns = session_data["conversation_turns"][-10:]  # Last 10 turns

            if not recent_turns:
                return {
                    "success": True,
                    "suggestions": [],
                    "sentiment": None,
                    "key_moments": [],
                }

            # Perform fresh analysis on recent conversation
            conversation_text = self._build_conversation_context(recent_turns)

            # Generate current suggestions
            suggestions = self._generate_contextual_suggestions(
                conversation_text, session_data["meeting_id"]
            )

            # Get current sentiment
            sentiment = self._analyze_current_sentiment(recent_turns)

            # Get recent key moments
            recent_moments = session_data.get("key_moments", [])[-5:]  # Last 5 moments

            return {
                "success": True,
                "suggestions": suggestions,
                "sentiment": sentiment,
                "key_moments": recent_moments,
                "conversation_summary": self._generate_conversation_summary(
                    recent_turns
                ),
            }

        except Exception as e:
            logger.error(f"Error getting real-time suggestions: {e}")
            return {"success": False, "error": str(e)}

    def identify_key_moments(
        self,
        conversation_turns: List[ConversationTurn],
        meeting_context: Dict[str, Any],
    ) -> List[KeyMoment]:
        """
        Identify key moments in the conversation using AI analysis

        Args:
            conversation_turns: Recent conversation turns
            meeting_context: Meeting and lead context

        Returns:
            List[KeyMoment]: Identified key moments
        """
        try:
            # Build conversation text for analysis
            conversation_text = "\n".join(
                [f"{turn.speaker}: {turn.content}" for turn in conversation_turns]
            )

            # Create AI prompt for key moment identification
            prompt = f"""
            Analyze this sales meeting conversation and identify key moments that are important for the sales process.
            
            Meeting Context:
            - Meeting Type: {meeting_context.get('meeting_type', 'discovery')}
            - Company: {meeting_context.get('company_name', 'Unknown')}
            - Industry: {meeting_context.get('industry', 'Unknown')}
            
            Conversation:
            {conversation_text}
            
            Identify key moments and classify them as:
            - buying_signal: Expressions of interest, positive feedback, or purchase intent
            - objection: Concerns, hesitations, or pushback
            - pain_point: Business challenges or problems mentioned
            - decision_maker: References to decision makers or approval processes
            - budget_mention: Budget discussions, financial constraints, or investment capacity
            - timeline_mention: Timeline discussions, urgency, or project deadlines
            - competitive_mention: References to competitors or alternative solutions
            - requirement_clarification: Specific needs or requirements discussed
            
            Return analysis in this JSON format:
            {{
                "key_moments": [
                    {{
                        "moment_type": "buying_signal|objection|pain_point|decision_maker|budget_mention|timeline_mention|competitive_mention|requirement_clarification",
                        "description": "brief description of what happened",
                        "importance_score": 85,
                        "context": "relevant conversation excerpt",
                        "suggested_response": "recommended response or follow-up",
                        "follow_up_actions": ["specific actions to take"]
                    }}
                ]
            }}
            """

            response = self.ai_service._make_api_call(prompt)
            analysis_data = self.ai_service._parse_ai_response(response.text.strip())

            key_moments = []
            for moment_data in analysis_data.get("key_moments", []):
                key_moment = KeyMoment(
                    timestamp=timezone.now(),
                    moment_type=moment_data.get("moment_type", "unknown"),
                    description=moment_data.get("description", ""),
                    importance_score=float(moment_data.get("importance_score", 50)),
                    context=moment_data.get("context", ""),
                    suggested_response=moment_data.get("suggested_response"),
                    follow_up_actions=moment_data.get("follow_up_actions", []),
                )
                key_moments.append(key_moment)

            return key_moments

        except Exception as e:
            logger.error(f"Error identifying key moments: {e}")
            return []

    def analyze_conversation_sentiment(
        self, conversation_turns: List[ConversationTurn]
    ) -> SentimentAnalysis:
        """
        Analyze sentiment and engagement level of the conversation

        Args:
            conversation_turns: Recent conversation turns to analyze

        Returns:
            SentimentAnalysis: Sentiment analysis results
        """
        try:
            # Build conversation text
            conversation_text = "\n".join(
                [f"{turn.speaker}: {turn.content}" for turn in conversation_turns]
            )

            # Create AI prompt for sentiment analysis
            prompt = f"""
            Analyze the sentiment and engagement level in this sales meeting conversation.
            Focus on the prospect's responses and overall conversation dynamics.
            
            Conversation:
            {conversation_text}
            
            Analyze and return results in this JSON format:
            {{
                "overall_sentiment": "positive|neutral|negative",
                "sentiment_score": 0.7,
                "engagement_level": "high|medium|low",
                "engagement_score": 85,
                "emotional_indicators": [
                    "specific phrases or behaviors indicating emotion/engagement"
                ],
                "confidence_level": 90,
                "analysis_notes": "brief explanation of the sentiment assessment"
            }}
            
            Consider:
            - Positive language, enthusiasm, questions, and active participation
            - Negative language, hesitation, objections, or disengagement
            - Length and depth of responses
            - Use of specific business terms or detailed explanations
            - Questions asked by the prospect
            """

            response = self.ai_service._make_api_call(prompt)
            analysis_data = self.ai_service._parse_ai_response(response.text.strip())

            sentiment_analysis = SentimentAnalysis(
                overall_sentiment=analysis_data.get("overall_sentiment", "neutral"),
                sentiment_score=float(analysis_data.get("sentiment_score", 0.0)),
                engagement_level=analysis_data.get("engagement_level", "medium"),
                engagement_score=float(analysis_data.get("engagement_score", 50.0)),
                emotional_indicators=analysis_data.get("emotional_indicators", []),
                confidence_level=float(analysis_data.get("confidence_level", 50.0)),
            )

            return sentiment_analysis

        except Exception as e:
            logger.error(f"Error analyzing conversation sentiment: {e}")
            return SentimentAnalysis(
                overall_sentiment="neutral",
                sentiment_score=0.0,
                engagement_level="medium",
                engagement_score=50.0,
                emotional_indicators=[],
                confidence_level=0.0,
            )

    def generate_next_question_suggestions(
        self,
        conversation_turns: List[ConversationTurn],
        meeting_context: Dict[str, Any],
    ) -> List[QuestionSuggestion]:
        """
        Generate intelligent next question suggestions based on conversation flow

        Args:
            conversation_turns: Recent conversation history
            meeting_context: Meeting and lead context

        Returns:
            List[QuestionSuggestion]: Prioritized question suggestions
        """
        try:
            # Build conversation context
            conversation_text = "\n".join(
                [
                    f"{turn.speaker}: {turn.content}"
                    for turn in conversation_turns[-8:]  # Last 8 turns
                ]
            )

            # Get lead context
            lead_info = meeting_context.get("lead_info", {})

            # Create AI prompt for question generation
            prompt = f"""
            Based on this sales meeting conversation flow, suggest the next best questions to ask.
            Consider what information is still needed and what topics should be explored deeper.
            
            Meeting Context:
            - Meeting Type: {meeting_context.get('meeting_type', 'discovery')}
            - Company: {lead_info.get('company_name', 'Unknown')}
            - Industry: {lead_info.get('industry', 'Unknown')}
            - Known Pain Points: {', '.join(lead_info.get('pain_points', []))}
            - Known Requirements: {', '.join(lead_info.get('requirements', []))}
            
            Recent Conversation:
            {conversation_text}
            
            Generate 3-5 strategic next questions that will:
            1. Build on the current conversation topic
            2. Uncover missing qualification information
            3. Move the sales process forward
            4. Address any concerns or objections raised
            5. Identify decision makers and budget authority
            
            Return suggestions in this JSON format:
            {{
                "question_suggestions": [
                    {{
                        "question_text": "specific question to ask",
                        "question_type": "discovery|budget|timeline|decision_makers|pain_points|requirements|closing|objection_handling",
                        "priority_score": 90,
                        "rationale": "why this question is important now",
                        "timing_suggestion": "immediate|after_current_topic|later_in_meeting",
                        "expected_outcome": "what we hope to learn or achieve",
                        "follow_up_questions": ["potential follow-up questions based on response"]
                    }}
                ]
            }}
            
            Prioritize questions that address gaps in our qualification or build on positive momentum.
            """

            response = self.ai_service._make_api_call(prompt)
            analysis_data = self.ai_service._parse_ai_response(response.text.strip())

            question_suggestions = []
            for q_data in analysis_data.get("question_suggestions", []):
                suggestion = QuestionSuggestion(
                    question_text=q_data.get("question_text", ""),
                    question_type=q_data.get("question_type", "discovery"),
                    priority_score=float(q_data.get("priority_score", 50)),
                    rationale=q_data.get("rationale", ""),
                    timing_suggestion=q_data.get("timing_suggestion", "immediate"),
                    expected_outcome=q_data.get("expected_outcome", ""),
                    follow_up_questions=q_data.get("follow_up_questions", []),
                )
                question_suggestions.append(suggestion)

            # Sort by priority score
            question_suggestions.sort(key=lambda x: x.priority_score, reverse=True)

            return question_suggestions

        except Exception as e:
            logger.error(f"Error generating question suggestions: {e}")
            return []

    def generate_meeting_guidance(
        self,
        conversation_turns: List[ConversationTurn],
        meeting_context: Dict[str, Any],
    ) -> MeetingGuidance:
        """
        Generate comprehensive AI meeting guidance including objection handling,
        closing opportunities, follow-up recommendations, and intervention alerts

        Args:
            conversation_turns: Recent conversation history
            meeting_context: Meeting and lead context

        Returns:
            MeetingGuidance: Complete guidance package
        """
        try:
            # Build conversation context
            conversation_text = "\n".join(
                [f"{turn.speaker}: {turn.content}" for turn in conversation_turns]
            )

            # Get lead context
            lead_info = meeting_context.get("lead_info", {})

            # Create comprehensive AI prompt for meeting guidance
            prompt = f"""
            Analyze this sales meeting conversation and provide comprehensive AI guidance.
            
            Meeting Context:
            - Meeting Type: {meeting_context.get('meeting_type', 'discovery')}
            - Company: {lead_info.get('company_name', 'Unknown')}
            - Industry: {lead_info.get('industry', 'Unknown')}
            - Known Pain Points: {', '.join(lead_info.get('pain_points', []))}
            - Budget Info: {lead_info.get('budget_info', 'Unknown')}
            - Timeline: {lead_info.get('timeline', 'Unknown')}
            - Decision Makers: {', '.join(lead_info.get('decision_makers', []))}
            
            Recent Conversation:
            {conversation_text}
            
            Provide comprehensive meeting guidance in this JSON format:
            {{
                "objection_handling": [
                    {{
                        "objection_type": "price|timing|authority|need|trust|competition",
                        "objection_text": "specific objection mentioned",
                        "recommended_response": "how to respond to this objection",
                        "alternative_approaches": ["alternative response strategies"],
                        "confidence_score": 85,
                        "urgency_level": "low|medium|high|critical",
                        "follow_up_questions": ["questions to ask after handling objection"]
                    }}
                ],
                "closing_opportunities": [
                    {{
                        "opportunity_type": "buying_signal|urgency|budget_confirmed|decision_maker_present",
                        "description": "why this is a closing opportunity",
                        "recommended_closing_technique": "assumptive|alternative|urgency|summary",
                        "closing_questions": ["specific closing questions to ask"],
                        "confidence_score": 90,
                        "timing_recommendation": "immediate|within_5_minutes|end_of_meeting",
                        "risk_factors": ["potential risks to consider"]
                    }}
                ],
                "follow_up_recommendations": [
                    {{
                        "action_type": "email|call|meeting|proposal|demo|reference",
                        "priority": "high|medium|low",
                        "recommended_timing": "immediate|same_day|within_24h|within_week",
                        "action_description": "specific action to take",
                        "rationale": "why this action is recommended",
                        "success_probability": 75,
                        "required_resources": ["what resources are needed"]
                    }}
                ],
                "intervention_alerts": [
                    {{
                        "alert_type": "disengagement|strong_objection|competitor_mention|budget_concern|timeline_issue",
                        "severity": "low|medium|high|critical",
                        "description": "what is concerning",
                        "recommended_intervention": "immediate action to take",
                        "immediate_actions": ["specific steps to take now"],
                        "confidence_score": 80
                    }}
                ],
                "overall_meeting_health": "excellent|good|concerning|critical"
            }}
            
            Focus on:
            1. Identifying and addressing objections with proven sales techniques
            2. Recognizing closing opportunities and providing specific closing approaches
            3. Recommending strategic follow-up actions based on conversation outcomes
            4. Alerting to situations requiring immediate intervention
            5. Assessing overall meeting health and momentum
            """

            response = self.ai_service._make_api_call(prompt)
            analysis_data = self.ai_service._parse_ai_response(response.text.strip())

            # Parse objection handling advice
            objection_advice = []
            for obj_data in analysis_data.get("objection_handling", []):
                advice = ObjectionHandlingAdvice(
                    objection_type=obj_data.get("objection_type", "unknown"),
                    objection_text=obj_data.get("objection_text", ""),
                    recommended_response=obj_data.get("recommended_response", ""),
                    alternative_approaches=obj_data.get("alternative_approaches", []),
                    confidence_score=float(obj_data.get("confidence_score", 50)),
                    urgency_level=obj_data.get("urgency_level", "medium"),
                    follow_up_questions=obj_data.get("follow_up_questions", []),
                )
                objection_advice.append(advice)

            # Parse closing opportunities
            closing_opportunities = []
            for close_data in analysis_data.get("closing_opportunities", []):
                opportunity = ClosingOpportunity(
                    opportunity_type=close_data.get(
                        "opportunity_type", "buying_signal"
                    ),
                    description=close_data.get("description", ""),
                    recommended_closing_technique=close_data.get(
                        "recommended_closing_technique", "assumptive"
                    ),
                    closing_questions=close_data.get("closing_questions", []),
                    confidence_score=float(close_data.get("confidence_score", 50)),
                    timing_recommendation=close_data.get(
                        "timing_recommendation", "immediate"
                    ),
                    risk_factors=close_data.get("risk_factors", []),
                )
                closing_opportunities.append(opportunity)

            # Parse follow-up recommendations
            follow_up_recommendations = []
            for followup_data in analysis_data.get("follow_up_recommendations", []):
                recommendation = FollowUpRecommendation(
                    action_type=followup_data.get("action_type", "email"),
                    priority=followup_data.get("priority", "medium"),
                    recommended_timing=followup_data.get(
                        "recommended_timing", "within_24h"
                    ),
                    action_description=followup_data.get("action_description", ""),
                    rationale=followup_data.get("rationale", ""),
                    success_probability=float(
                        followup_data.get("success_probability", 50)
                    ),
                    required_resources=followup_data.get("required_resources", []),
                )
                follow_up_recommendations.append(recommendation)

            # Parse intervention alerts
            intervention_alerts = []
            for alert_data in analysis_data.get("intervention_alerts", []):
                alert = InterventionAlert(
                    alert_type=alert_data.get("alert_type", "unknown"),
                    severity=alert_data.get("severity", "medium"),
                    description=alert_data.get("description", ""),
                    recommended_intervention=alert_data.get(
                        "recommended_intervention", ""
                    ),
                    immediate_actions=alert_data.get("immediate_actions", []),
                    confidence_score=float(alert_data.get("confidence_score", 50)),
                    triggered_at=timezone.now(),
                )
                intervention_alerts.append(alert)

            # Create meeting guidance
            meeting_guidance = MeetingGuidance(
                objection_advice=objection_advice,
                closing_opportunities=closing_opportunities,
                follow_up_recommendations=follow_up_recommendations,
                intervention_alerts=intervention_alerts,
                overall_meeting_health=analysis_data.get(
                    "overall_meeting_health", "good"
                ),
                guidance_timestamp=timezone.now(),
            )

            return meeting_guidance

        except Exception as e:
            logger.error(f"Error generating meeting guidance: {e}")
            return MeetingGuidance(
                objection_advice=[],
                closing_opportunities=[],
                follow_up_recommendations=[],
                intervention_alerts=[],
                overall_meeting_health="unknown",
                guidance_timestamp=timezone.now(),
            )

    def generate_meeting_guidance(
        self,
        conversation_turns: List[ConversationTurn],
        meeting_context: Dict[str, Any],
    ) -> MeetingGuidance:
        """
        Generate comprehensive AI meeting guidance including objection handling,
        closing opportunities, follow-up recommendations, and intervention alerts

        Args:
            conversation_turns: Recent conversation history
            meeting_context: Meeting and lead context

        Returns:
            MeetingGuidance: Complete guidance package
        """
        try:
            # Build conversation context
            conversation_text = "\n".join(
                [f"{turn.speaker}: {turn.content}" for turn in conversation_turns]
            )

            # Get lead context
            lead_info = meeting_context.get("lead_info", {})

            # Create comprehensive AI prompt for meeting guidance
            prompt = f"""
            Analyze this sales meeting conversation and provide comprehensive AI guidance.
            
            Meeting Context:
            - Meeting Type: {meeting_context.get('meeting_type', 'discovery')}
            - Company: {lead_info.get('company_name', 'Unknown')}
            - Industry: {lead_info.get('industry', 'Unknown')}
            - Known Pain Points: {', '.join(lead_info.get('pain_points', []))}
            - Budget Info: {lead_info.get('budget_info', 'Unknown')}
            - Timeline: {lead_info.get('timeline', 'Unknown')}
            - Decision Makers: {', '.join(lead_info.get('decision_makers', []))}
            
            Recent Conversation:
            {conversation_text}
            
            Provide comprehensive meeting guidance in this JSON format:
            {{
                "objection_handling": [
                    {{
                        "objection_type": "price|timing|authority|need|trust|competition",
                        "objection_text": "specific objection mentioned",
                        "recommended_response": "how to respond to this objection",
                        "alternative_approaches": ["alternative response strategies"],
                        "confidence_score": 85,
                        "urgency_level": "low|medium|high|critical",
                        "follow_up_questions": ["questions to ask after handling objection"]
                    }}
                ],
                "closing_opportunities": [
                    {{
                        "opportunity_type": "buying_signal|urgency|budget_confirmed|decision_maker_present",
                        "description": "why this is a closing opportunity",
                        "recommended_closing_technique": "assumptive|alternative|urgency|summary",
                        "closing_questions": ["specific closing questions to ask"],
                        "confidence_score": 90,
                        "timing_recommendation": "immediate|within_5_minutes|end_of_meeting",
                        "risk_factors": ["potential risks to consider"]
                    }}
                ],
                "follow_up_recommendations": [
                    {{
                        "action_type": "email|call|meeting|proposal|demo|reference",
                        "priority": "high|medium|low",
                        "recommended_timing": "immediate|same_day|within_24h|within_week",
                        "action_description": "specific action to take",
                        "rationale": "why this action is recommended",
                        "success_probability": 75,
                        "required_resources": ["what resources are needed"]
                    }}
                ],
                "intervention_alerts": [
                    {{
                        "alert_type": "disengagement|strong_objection|competitor_mention|budget_concern|timeline_issue",
                        "severity": "low|medium|high|critical",
                        "description": "what is concerning",
                        "recommended_intervention": "immediate action to take",
                        "immediate_actions": ["specific steps to take now"],
                        "confidence_score": 80
                    }}
                ],
                "overall_meeting_health": "excellent|good|concerning|critical"
            }}
            
            Focus on:
            1. Identifying and addressing objections with proven sales techniques
            2. Recognizing closing opportunities and providing specific closing approaches
            3. Recommending strategic follow-up actions based on conversation outcomes
            4. Alerting to situations requiring immediate intervention
            5. Assessing overall meeting health and momentum
            """

            response = self.ai_service._make_api_call(prompt)
            analysis_data = self.ai_service._parse_ai_response(response.text.strip())

            # Parse objection handling advice
            objection_advice = []
            for obj_data in analysis_data.get("objection_handling", []):
                advice = ObjectionHandlingAdvice(
                    objection_type=obj_data.get("objection_type", "unknown"),
                    objection_text=obj_data.get("objection_text", ""),
                    recommended_response=obj_data.get("recommended_response", ""),
                    alternative_approaches=obj_data.get("alternative_approaches", []),
                    confidence_score=float(obj_data.get("confidence_score", 50)),
                    urgency_level=obj_data.get("urgency_level", "medium"),
                    follow_up_questions=obj_data.get("follow_up_questions", []),
                )
                objection_advice.append(advice)

            # Parse closing opportunities
            closing_opportunities = []
            for close_data in analysis_data.get("closing_opportunities", []):
                opportunity = ClosingOpportunity(
                    opportunity_type=close_data.get(
                        "opportunity_type", "buying_signal"
                    ),
                    description=close_data.get("description", ""),
                    recommended_closing_technique=close_data.get(
                        "recommended_closing_technique", "assumptive"
                    ),
                    closing_questions=close_data.get("closing_questions", []),
                    confidence_score=float(close_data.get("confidence_score", 50)),
                    timing_recommendation=close_data.get(
                        "timing_recommendation", "immediate"
                    ),
                    risk_factors=close_data.get("risk_factors", []),
                )
                closing_opportunities.append(opportunity)

            # Parse follow-up recommendations
            follow_up_recommendations = []
            for followup_data in analysis_data.get("follow_up_recommendations", []):
                recommendation = FollowUpRecommendation(
                    action_type=followup_data.get("action_type", "email"),
                    priority=followup_data.get("priority", "medium"),
                    recommended_timing=followup_data.get(
                        "recommended_timing", "within_24h"
                    ),
                    action_description=followup_data.get("action_description", ""),
                    rationale=followup_data.get("rationale", ""),
                    success_probability=float(
                        followup_data.get("success_probability", 50)
                    ),
                    required_resources=followup_data.get("required_resources", []),
                )
                follow_up_recommendations.append(recommendation)

            # Parse intervention alerts
            intervention_alerts = []
            for alert_data in analysis_data.get("intervention_alerts", []):
                alert = InterventionAlert(
                    alert_type=alert_data.get("alert_type", "unknown"),
                    severity=alert_data.get("severity", "medium"),
                    description=alert_data.get("description", ""),
                    recommended_intervention=alert_data.get(
                        "recommended_intervention", ""
                    ),
                    immediate_actions=alert_data.get("immediate_actions", []),
                    confidence_score=float(alert_data.get("confidence_score", 50)),
                    triggered_at=timezone.now(),
                )
                intervention_alerts.append(alert)

            # Create meeting guidance
            meeting_guidance = MeetingGuidance(
                objection_advice=objection_advice,
                closing_opportunities=closing_opportunities,
                follow_up_recommendations=follow_up_recommendations,
                intervention_alerts=intervention_alerts,
                overall_meeting_health=analysis_data.get(
                    "overall_meeting_health", "good"
                ),
                guidance_timestamp=timezone.now(),
            )

            return meeting_guidance

        except Exception as e:
            logger.error(f"Error generating meeting guidance: {e}")
            return MeetingGuidance(
                objection_advice=[],
                closing_opportunities=[],
                follow_up_recommendations=[],
                intervention_alerts=[],
                overall_meeting_health="unknown",
                guidance_timestamp=timezone.now(),
            )

    def end_live_meeting_session(self, session_id: str) -> Dict[str, Any]:
        """
        End the live meeting session and generate final summary

        Args:
            session_id: Live meeting session ID

        Returns:
            dict: Final meeting summary and analysis
        """
        try:
            session_data = cache.get(session_id)
            if not session_data:
                return {"success": False, "error": "Session not found or expired"}

            meeting_id = session_data["meeting_id"]
            meeting = Meeting.objects.get(id=meeting_id)

            # Mark meeting as completed
            meeting.mark_as_completed()

            # Generate final meeting summary
            conversation_turns = [
                ConversationTurn(**turn_data)
                for turn_data in session_data["conversation_turns"]
            ]

            final_summary = self._generate_final_meeting_summary(
                conversation_turns,
                session_data.get("key_moments", []),
                session_data.get("sentiment_history", []),
            )

            # Update meeting with AI insights
            meeting.ai_insights = final_summary
            meeting.save()

            # Clean up session cache
            cache.delete(session_id)

            logger.info(f"Ended live meeting session for meeting {meeting_id}")

            return {
                "success": True,
                "meeting_id": meeting_id,
                "final_summary": final_summary,
                "total_conversation_turns": len(conversation_turns),
                "meeting_duration_minutes": meeting.actual_duration_minutes,
            }

        except Exception as e:
            logger.error(f"Error ending live meeting session: {e}")
            return {"success": False, "error": str(e)}

    # Private helper methods

    def _generate_initial_questions(self, meeting: Meeting) -> List[Dict[str, Any]]:
        """Generate initial questions for the meeting start"""
        try:
            # Get existing meeting questions or generate new ones
            existing_questions = meeting.questions.filter(priority__gte=7).order_by(
                "-priority", "sequence_order"
            )[:5]

            if existing_questions:
                return [
                    {
                        "question_text": q.question_text,
                        "question_type": q.question_type,
                        "priority": q.priority,
                        "rationale": f"Pre-planned {q.get_question_type_display().lower()} question",
                    }
                    for q in existing_questions
                ]

            # Generate initial questions using AI
            lead_context = {
                "company_name": meeting.lead.company_name,
                "industry": meeting.lead.industry,
                "pain_points": meeting.lead.pain_points,
                "requirements": meeting.lead.requirements,
                "meeting_type": meeting.meeting_type,
            }

            questions_data = self.ai_service.generate_meeting_questions(
                lead_context, {"meeting_type": meeting.meeting_type}
            )

            # Extract top priority questions
            initial_questions = []
            for category in [
                "discovery_questions",
                "pain_point_questions",
                "budget_questions",
            ]:
                category_questions = questions_data.get(category, [])
                for q in category_questions[:2]:  # Top 2 from each category
                    initial_questions.append(
                        {
                            "question_text": q.get("question", ""),
                            "question_type": category.replace("_questions", ""),
                            "priority": q.get("priority", 5),
                            "rationale": q.get("rationale", ""),
                        }
                    )

            return sorted(initial_questions, key=lambda x: x["priority"], reverse=True)[
                :5
            ]

        except Exception as e:
            logger.error(f"Error generating initial questions: {e}")
            return []

    def _get_lead_context(self, lead: Lead) -> Dict[str, Any]:
        """Get lead context for meeting analysis"""
        return {
            "company_name": lead.company_name,
            "industry": lead.industry,
            "company_size": lead.company_size,
            "pain_points": lead.pain_points,
            "requirements": lead.requirements,
            "budget_info": lead.budget_info,
            "timeline": lead.timeline,
            "decision_makers": lead.decision_makers,
            "current_solution": lead.current_solution,
            "competitors_mentioned": lead.competitors_mentioned,
        }

    def _get_ai_insights_context(self, lead: Lead) -> Dict[str, Any]:
        """Get AI insights context for meeting analysis"""
        try:
            ai_insights = lead.ai_insights
            return {
                "lead_score": ai_insights.lead_score,
                "conversion_probability": ai_insights.conversion_probability,
                "quality_tier": ai_insights.quality_tier,
                "key_strengths": ai_insights.key_strengths,
                "improvement_areas": ai_insights.improvement_areas,
                "recommended_actions": ai_insights.recommended_actions,
            }
        except:
            return {}

    def generate_meeting_guidance(
        self,
        conversation_turns: List[ConversationTurn],
        meeting_context: Dict[str, Any],
    ) -> MeetingGuidance:
        """
        Generate comprehensive AI meeting guidance including objection handling,
        closing opportunities, follow-up recommendations, and intervention alerts

        Args:
            conversation_turns: Recent conversation history
            meeting_context: Meeting and lead context

        Returns:
            MeetingGuidance: Complete guidance package
        """
        try:
            # Build conversation context
            conversation_text = "\n".join(
                [f"{turn.speaker}: {turn.content}" for turn in conversation_turns]
            )

            # Get lead context
            lead_info = meeting_context.get("lead_info", {})

            # Create comprehensive AI prompt for meeting guidance
            prompt = f"""
            Analyze this sales meeting conversation and provide comprehensive AI guidance.
            
            Meeting Context:
            - Meeting Type: {meeting_context.get('meeting_type', 'discovery')}
            - Company: {lead_info.get('company_name', 'Unknown')}
            - Industry: {lead_info.get('industry', 'Unknown')}
            - Known Pain Points: {', '.join(lead_info.get('pain_points', []))}
            - Budget Info: {lead_info.get('budget_info', 'Unknown')}
            - Timeline: {lead_info.get('timeline', 'Unknown')}
            - Decision Makers: {', '.join(lead_info.get('decision_makers', []))}
            
            Recent Conversation:
            {conversation_text}
            
            Provide comprehensive meeting guidance in this JSON format:
            {{
                "objection_handling": [
                    {{
                        "objection_type": "price|timing|authority|need|trust|competition",
                        "objection_text": "specific objection mentioned",
                        "recommended_response": "how to respond to this objection",
                        "alternative_approaches": ["alternative response strategies"],
                        "confidence_score": 85,
                        "urgency_level": "low|medium|high|critical",
                        "follow_up_questions": ["questions to ask after handling objection"]
                    }}
                ],
                "closing_opportunities": [
                    {{
                        "opportunity_type": "buying_signal|urgency|budget_confirmed|decision_maker_present",
                        "description": "why this is a closing opportunity",
                        "recommended_closing_technique": "assumptive|alternative|urgency|summary",
                        "closing_questions": ["specific closing questions to ask"],
                        "confidence_score": 90,
                        "timing_recommendation": "immediate|within_5_minutes|end_of_meeting",
                        "risk_factors": ["potential risks to consider"]
                    }}
                ],
                "follow_up_recommendations": [
                    {{
                        "action_type": "email|call|meeting|proposal|demo|reference",
                        "priority": "high|medium|low",
                        "recommended_timing": "immediate|same_day|within_24h|within_week",
                        "action_description": "specific action to take",
                        "rationale": "why this action is recommended",
                        "success_probability": 75,
                        "required_resources": ["what resources are needed"]
                    }}
                ],
                "intervention_alerts": [
                    {{
                        "alert_type": "disengagement|strong_objection|competitor_mention|budget_concern|timeline_issue",
                        "severity": "low|medium|high|critical",
                        "description": "what is concerning",
                        "recommended_intervention": "immediate action to take",
                        "immediate_actions": ["specific steps to take now"],
                        "confidence_score": 80
                    }}
                ],
                "overall_meeting_health": "excellent|good|concerning|critical"
            }}
            
            Focus on:
            1. Identifying and addressing objections with proven sales techniques
            2. Recognizing closing opportunities and providing specific closing approaches
            3. Recommending strategic follow-up actions based on conversation outcomes
            4. Alerting to situations requiring immediate intervention
            5. Assessing overall meeting health and momentum
            """

            response = self.ai_service._make_api_call(prompt)
            analysis_data = self.ai_service._parse_ai_response(response.text.strip())

            # Parse objection handling advice
            objection_advice = []
            for obj_data in analysis_data.get("objection_handling", []):
                advice = ObjectionHandlingAdvice(
                    objection_type=obj_data.get("objection_type", "unknown"),
                    objection_text=obj_data.get("objection_text", ""),
                    recommended_response=obj_data.get("recommended_response", ""),
                    alternative_approaches=obj_data.get("alternative_approaches", []),
                    confidence_score=float(obj_data.get("confidence_score", 50)),
                    urgency_level=obj_data.get("urgency_level", "medium"),
                    follow_up_questions=obj_data.get("follow_up_questions", []),
                )
                objection_advice.append(advice)

            # Parse closing opportunities
            closing_opportunities = []
            for close_data in analysis_data.get("closing_opportunities", []):
                opportunity = ClosingOpportunity(
                    opportunity_type=close_data.get(
                        "opportunity_type", "buying_signal"
                    ),
                    description=close_data.get("description", ""),
                    recommended_closing_technique=close_data.get(
                        "recommended_closing_technique", "assumptive"
                    ),
                    closing_questions=close_data.get("closing_questions", []),
                    confidence_score=float(close_data.get("confidence_score", 50)),
                    timing_recommendation=close_data.get(
                        "timing_recommendation", "immediate"
                    ),
                    risk_factors=close_data.get("risk_factors", []),
                )
                closing_opportunities.append(opportunity)

            # Parse follow-up recommendations
            follow_up_recommendations = []
            for followup_data in analysis_data.get("follow_up_recommendations", []):
                recommendation = FollowUpRecommendation(
                    action_type=followup_data.get("action_type", "email"),
                    priority=followup_data.get("priority", "medium"),
                    recommended_timing=followup_data.get(
                        "recommended_timing", "within_24h"
                    ),
                    action_description=followup_data.get("action_description", ""),
                    rationale=followup_data.get("rationale", ""),
                    success_probability=float(
                        followup_data.get("success_probability", 50)
                    ),
                    required_resources=followup_data.get("required_resources", []),
                )
                follow_up_recommendations.append(recommendation)

            # Parse intervention alerts
            intervention_alerts = []
            for alert_data in analysis_data.get("intervention_alerts", []):
                alert = InterventionAlert(
                    alert_type=alert_data.get("alert_type", "unknown"),
                    severity=alert_data.get("severity", "medium"),
                    description=alert_data.get("description", ""),
                    recommended_intervention=alert_data.get(
                        "recommended_intervention", ""
                    ),
                    immediate_actions=alert_data.get("immediate_actions", []),
                    confidence_score=float(alert_data.get("confidence_score", 50)),
                    triggered_at=timezone.now(),
                )
                intervention_alerts.append(alert)

            # Create meeting guidance
            meeting_guidance = MeetingGuidance(
                objection_advice=objection_advice,
                closing_opportunities=closing_opportunities,
                follow_up_recommendations=follow_up_recommendations,
                intervention_alerts=intervention_alerts,
                overall_meeting_health=analysis_data.get(
                    "overall_meeting_health", "good"
                ),
                guidance_timestamp=timezone.now(),
            )

            return meeting_guidance

        except Exception as e:
            logger.error(f"Error generating meeting guidance: {e}")
            return MeetingGuidance(
                objection_advice=[],
                closing_opportunities=[],
                follow_up_recommendations=[],
                intervention_alerts=[],
                overall_meeting_health="unknown",
                guidance_timestamp=timezone.now(),
            )

    def _should_perform_analysis(
        self, session_data: Dict[str, Any], content: str
    ) -> bool:
        """Determine if we should perform real-time analysis"""
        # Check minimum interval
        last_analysis = session_data.get("last_analysis_time")
        if last_analysis:
            last_time = datetime.fromisoformat(last_analysis.replace("Z", "+00:00"))
            if (
                timezone.now() - last_time
            ).total_seconds() < self.min_analysis_interval:
                return False

        # Check content significance
        significant_keywords = [
            "budget",
            "cost",
            "price",
            "decision",
            "approve",
            "timeline",
            "when",
            "problem",
            "challenge",
            "issue",
            "need",
            "require",
            "solution",
            "competitor",
            "alternative",
            "currently",
            "using",
            "interested",
            "concerned",
            "worried",
            "hesitant",
            "excited",
            "impressed",
        ]

        content_lower = content.lower()
        has_significant_content = any(
            keyword in content_lower for keyword in significant_keywords
        )

        # Analyze if content is significant or enough turns have passed
        turn_count = len(session_data.get("conversation_turns", []))
        return has_significant_content or turn_count % 5 == 0  # Every 5 turns minimum

    def _perform_live_analysis(
        self, session_data: Dict[str, Any], current_turn: ConversationTurn
    ) -> LiveAnalysisResult:
        """Perform comprehensive live analysis"""
        try:
            # Get meeting context
            meeting_id = session_data["meeting_id"]
            meeting = Meeting.objects.get(id=meeting_id)
            meeting_context = {
                "meeting_type": meeting.meeting_type,
                "lead_info": self._get_lead_context(meeting.lead),
                "ai_insights": self._get_ai_insights_context(meeting.lead),
            }

            # Get recent conversation turns
            conversation_turns = [
                ConversationTurn(**turn_data)
                for turn_data in session_data["conversation_turns"][
                    -10:
                ]  # Last 10 turns
            ]

            # Perform various analyses
            sentiment_analysis = self.analyze_conversation_sentiment(conversation_turns)
            key_moments = self.identify_key_moments(conversation_turns, meeting_context)
            question_suggestions = self.generate_next_question_suggestions(
                conversation_turns, meeting_context
            )
            meeting_guidance = self.generate_meeting_guidance(
                conversation_turns, meeting_context
            )
            meeting_progress = self._calculate_meeting_progress(
                conversation_turns, meeting_context
            )

            # Update session data with new analysis
            session_data["key_moments"].extend(
                [asdict(moment) for moment in key_moments]
            )
            session_data["sentiment_history"].append(asdict(sentiment_analysis))
            session_data["question_suggestions"] = [
                asdict(q) for q in question_suggestions
            ]

            # Create comprehensive analysis result
            analysis_result = LiveAnalysisResult(
                conversation_turns=conversation_turns,
                sentiment_analysis=sentiment_analysis,
                key_moments=key_moments,
                question_suggestions=question_suggestions,
                meeting_guidance=meeting_guidance,
                meeting_progress=meeting_progress,
                analysis_timestamp=timezone.now(),
                confidence_score=self._calculate_analysis_confidence(
                    sentiment_analysis, key_moments, question_suggestions
                ),
            )

            return analysis_result

        except Exception as e:
            logger.error(f"Error performing live analysis: {e}")
            # Return empty analysis result
            return LiveAnalysisResult(
                conversation_turns=[],
                sentiment_analysis=SentimentAnalysis(
                    overall_sentiment="neutral",
                    sentiment_score=0.0,
                    engagement_level="medium",
                    engagement_score=50.0,
                    emotional_indicators=[],
                    confidence_level=0.0,
                ),
                key_moments=[],
                question_suggestions=[],
                meeting_guidance=MeetingGuidance(
                    objection_advice=[],
                    closing_opportunities=[],
                    follow_up_recommendations=[],
                    intervention_alerts=[],
                    overall_meeting_health="unknown",
                    guidance_timestamp=timezone.now(),
                ),
                meeting_progress={
                    "progress_percentage": 0,
                    "meeting_stage": "discovery",
                },
                analysis_timestamp=timezone.now(),
                confidence_score=0.0,
            )

    def _calculate_analysis_confidence(
        self,
        sentiment_analysis: SentimentAnalysis,
        key_moments: List[KeyMoment],
        question_suggestions: List[QuestionSuggestion],
    ) -> float:
        """Calculate overall confidence score for the analysis"""
        try:
            # Weight different analysis components
            sentiment_confidence = sentiment_analysis.confidence_level
            moments_confidence = sum(
                moment.importance_score for moment in key_moments
            ) / max(len(key_moments), 1)
            questions_confidence = sum(
                q.priority_score for q in question_suggestions
            ) / max(len(question_suggestions), 1)

            # Calculate weighted average
            overall_confidence = (
                sentiment_confidence * 0.3
                + moments_confidence * 0.4
                + questions_confidence * 0.3
            )

            return min(overall_confidence, 100.0)

        except Exception as e:
            logger.error(f"Error calculating analysis confidence: {e}")
            return 50.0
        try:
            # Get recent conversation turns
            recent_turns = [
                ConversationTurn(**turn_data)
                for turn_data in session_data["conversation_turns"][-10:]
            ]

            # Get meeting context
            meeting = Meeting.objects.get(id=session_data["meeting_id"])
            meeting_context = {
                "meeting_type": meeting.meeting_type,
                "company_name": meeting.lead.company_name,
                "industry": meeting.lead.industry,
                "lead_info": self._get_lead_context(meeting.lead),
            }

            # Perform analyses
            sentiment_analysis = self.analyze_conversation_sentiment(recent_turns)
            key_moments = self.identify_key_moments(recent_turns, meeting_context)
            question_suggestions = self.generate_next_question_suggestions(
                recent_turns, meeting_context
            )

            # Calculate meeting progress
            meeting_progress = self._calculate_meeting_progress(
                recent_turns, meeting_context
            )

            # Update session data with new insights
            session_data["key_moments"].extend(
                [asdict(moment) for moment in key_moments]
            )
            session_data["sentiment_history"].append(asdict(sentiment_analysis))
            session_data["question_suggestions"] = [
                asdict(q) for q in question_suggestions
            ]

            return LiveAnalysisResult(
                conversation_turns=recent_turns,
                sentiment_analysis=sentiment_analysis,
                key_moments=key_moments,
                question_suggestions=question_suggestions,
                meeting_progress=meeting_progress,
                analysis_timestamp=timezone.now(),
                confidence_score=sentiment_analysis.confidence_level,
            )

        except Exception as e:
            logger.error(f"Error performing live analysis: {e}")
            raise

    def _calculate_transcription_confidence(self, content: str) -> float:
        """Calculate confidence score for transcribed content"""
        # Simple heuristic based on content characteristics
        if not content or len(content.strip()) < 3:
            return 0.0

        # Check for common transcription issues
        issues = 0
        if "[inaudible]" in content.lower():
            issues += 1
        if "..." in content:
            issues += 1
        if len(content.split()) < 3:
            issues += 1

        base_confidence = 90.0
        confidence = max(base_confidence - (issues * 20), 10.0)

        return confidence

    def _build_conversation_context(self, turns: List[Dict[str, Any]]) -> str:
        """Build conversation context string from turns"""
        return "\n".join([f"{turn['speaker']}: {turn['content']}" for turn in turns])

    def _generate_contextual_suggestions(
        self, conversation_text: str, meeting_id: str
    ) -> List[Dict[str, Any]]:
        """Generate contextual suggestions based on current conversation"""
        try:
            meeting = Meeting.objects.get(id=meeting_id)
            conversation_turns = [
                ConversationTurn(
                    timestamp=timezone.now(), speaker="mixed", content=conversation_text
                )
            ]

            meeting_context = {
                "meeting_type": meeting.meeting_type,
                "company_name": meeting.lead.company_name,
                "industry": meeting.lead.industry,
                "lead_info": self._get_lead_context(meeting.lead),
            }

            suggestions = self.generate_next_question_suggestions(
                conversation_turns, meeting_context
            )
            return [asdict(suggestion) for suggestion in suggestions]

        except Exception as e:
            logger.error(f"Error generating contextual suggestions: {e}")
            return []

    def _analyze_current_sentiment(
        self, recent_turns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze current sentiment from recent turns"""
        try:
            turns = [ConversationTurn(**turn_data) for turn_data in recent_turns]
            sentiment = self.analyze_conversation_sentiment(turns)
            return asdict(sentiment)
        except Exception as e:
            logger.error(f"Error analyzing current sentiment: {e}")
            return {}

    def _generate_conversation_summary(self, recent_turns: List[Dict[str, Any]]) -> str:
        """Generate a brief summary of recent conversation"""
        if not recent_turns:
            return "No recent conversation to summarize."

        conversation_text = self._build_conversation_context(recent_turns)

        try:
            prompt = f"""
            Provide a brief 2-3 sentence summary of this recent sales meeting conversation:
            
            {conversation_text}
            
            Focus on:
            - Key topics discussed
            - Any important information revealed
            - Current conversation direction
            """

            response = self.ai_service._make_api_call(prompt)
            return response.text.strip()

        except Exception as e:
            logger.error(f"Error generating conversation summary: {e}")
            return "Unable to generate conversation summary."

    def _calculate_meeting_progress(
        self,
        conversation_turns: List[ConversationTurn],
        meeting_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calculate meeting progress and qualification status"""
        try:
            # Define qualification areas
            qualification_areas = {
                "pain_points_identified": False,
                "budget_discussed": False,
                "timeline_established": False,
                "decision_makers_identified": False,
                "requirements_clarified": False,
                "next_steps_defined": False,
            }

            # Analyze conversation for qualification progress
            conversation_text = "\n".join(
                [f"{turn.speaker}: {turn.content}" for turn in conversation_turns]
            )

            # Simple keyword-based progress tracking
            progress_keywords = {
                "pain_points_identified": [
                    "problem",
                    "challenge",
                    "issue",
                    "difficulty",
                    "pain",
                ],
                "budget_discussed": ["budget", "cost", "price", "investment", "spend"],
                "timeline_established": [
                    "timeline",
                    "when",
                    "deadline",
                    "schedule",
                    "urgency",
                ],
                "decision_makers_identified": [
                    "decision",
                    "approve",
                    "boss",
                    "manager",
                    "team",
                ],
                "requirements_clarified": [
                    "need",
                    "require",
                    "must have",
                    "feature",
                    "functionality",
                ],
                "next_steps_defined": [
                    "next",
                    "follow up",
                    "schedule",
                    "meeting",
                    "demo",
                ],
            }

            conversation_lower = conversation_text.lower()
            for area, keywords in progress_keywords.items():
                qualification_areas[area] = any(
                    keyword in conversation_lower for keyword in keywords
                )

            # Calculate overall progress percentage
            completed_areas = sum(
                1 for completed in qualification_areas.values() if completed
            )
            progress_percentage = (completed_areas / len(qualification_areas)) * 100

            return {
                "qualification_areas": qualification_areas,
                "progress_percentage": progress_percentage,
                "completed_areas": completed_areas,
                "total_areas": len(qualification_areas),
                "meeting_stage": self._determine_meeting_stage(progress_percentage),
            }

        except Exception as e:
            logger.error(f"Error calculating meeting progress: {e}")
            return {"progress_percentage": 0, "meeting_stage": "discovery"}

    def _determine_meeting_stage(self, progress_percentage: float) -> str:
        """Determine current meeting stage based on progress"""
        if progress_percentage < 25:
            return "opening"
        elif progress_percentage < 50:
            return "discovery"
        elif progress_percentage < 75:
            return "qualification"
        else:
            return "closing"

    def _generate_final_meeting_summary(
        self,
        conversation_turns: List[ConversationTurn],
        key_moments: List[Dict[str, Any]],
        sentiment_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate comprehensive final meeting summary"""
        try:
            # Build full conversation text
            full_conversation = "\n".join(
                [f"{turn.speaker}: {turn.content}" for turn in conversation_turns]
            )

            # Create comprehensive summary prompt
            prompt = f"""
            Generate a comprehensive summary of this sales meeting based on the conversation and analysis data.
            
            Full Conversation:
            {full_conversation}
            
            Key Moments Identified: {len(key_moments)}
            Sentiment Analysis Points: {len(sentiment_history)}
            
            Provide a detailed summary in this JSON format:
            {{
                "meeting_summary": "comprehensive 3-4 sentence summary of the meeting",
                "key_outcomes": [
                    "important outcomes and decisions from the meeting"
                ],
                "information_gathered": {{
                    "pain_points": ["pain points discussed"],
                    "requirements": ["requirements identified"],
                    "budget_info": "budget information discussed or null",
                    "timeline": "timeline information or null",
                    "decision_makers": ["decision makers mentioned"],
                    "competitors": ["competitors mentioned"]
                }},
                "next_steps": [
                    "specific next steps and follow-up actions"
                ],
                "overall_sentiment": "positive|neutral|negative",
                "meeting_effectiveness": "high|medium|low",
                "conversion_probability": 75,
                "recommendations": [
                    "strategic recommendations for follow-up"
                ]
            }}
            """

            response = self.ai_service._make_api_call(prompt)
            summary_data = self.ai_service._parse_ai_response(response.text.strip())

            return summary_data

        except Exception as e:
            logger.error(f"Error generating final meeting summary: {e}")
            return {
                "meeting_summary": "Meeting completed with conversation analysis.",
                "key_outcomes": [],
                "next_steps": [],
                "overall_sentiment": "neutral",
                "meeting_effectiveness": "medium",
                "conversion_probability": 50,
            }
