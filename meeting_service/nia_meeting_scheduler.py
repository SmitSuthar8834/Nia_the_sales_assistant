import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from .google_meet_service import GoogleMeetService
from .intelligent_meeting_service import IntelligentMeetingService
from .microsoft_teams_service import MicrosoftTeamsService
from .models import MeetingSession, MeetingStatusUpdate

# Import AI service for lead context
try:
    from ai_service.models import AIInsights, Lead
    from ai_service.services import AIAnalysisService

    AI_SERVICE_AVAILABLE = True
except ImportError:
    AI_SERVICE_AVAILABLE = False

User = get_user_model()
logger = logging.getLogger(__name__)


class NIAMeetingType(Enum):
    """Types of NIA meetings"""

    LEAD_CONSULTATION = "lead_consultation"
    SALES_STRATEGY = "sales_strategy"
    OPPORTUNITY_REVIEW = "opportunity_review"
    FOLLOW_UP = "follow_up"
    TRAINING = "training"
    GENERAL_CONSULTATION = "general_consultation"


class NIAMeetingScheduler:
    """Service for scheduling meetings with NIA (Neural Intelligence Assistant)"""

    def __init__(self):
        self.google_service = GoogleMeetService()
        self.teams_service = MicrosoftTeamsService()
        self.intelligent_service = IntelligentMeetingService()

        # NIA meeting configuration
        self.nia_email = getattr(settings, "NIA_EMAIL", "nia@example.com")
        self.nia_name = "NIA (Neural Intelligence Assistant)"
        self.default_meeting_duration = 60  # minutes

        # Meeting templates
        self.meeting_templates = {
            NIAMeetingType.LEAD_CONSULTATION: {
                "duration": 45,
                "agenda_template": "nia_lead_consultation_agenda.txt",
                "preparation_items": [
                    "Review lead information and pain points",
                    "Prepare relevant case studies",
                    "Gather industry insights",
                    "Review conversion strategies",
                ],
            },
            NIAMeetingType.SALES_STRATEGY: {
                "duration": 60,
                "agenda_template": "nia_sales_strategy_agenda.txt",
                "preparation_items": [
                    "Analyze current sales pipeline",
                    "Review performance metrics",
                    "Prepare optimization recommendations",
                    "Gather competitive intelligence",
                ],
            },
            NIAMeetingType.OPPORTUNITY_REVIEW: {
                "duration": 30,
                "agenda_template": "nia_opportunity_review_agenda.txt",
                "preparation_items": [
                    "Review opportunity details",
                    "Analyze deal progression",
                    "Prepare risk assessment",
                    "Identify next steps",
                ],
            },
            NIAMeetingType.FOLLOW_UP: {
                "duration": 30,
                "agenda_template": "nia_follow_up_agenda.txt",
                "preparation_items": [
                    "Review previous meeting outcomes",
                    "Check action item completion",
                    "Prepare progress updates",
                    "Identify new challenges",
                ],
            },
            NIAMeetingType.TRAINING: {
                "duration": 90,
                "agenda_template": "nia_training_agenda.txt",
                "preparation_items": [
                    "Prepare training materials",
                    "Review user skill level",
                    "Customize training content",
                    "Prepare practice scenarios",
                ],
            },
            NIAMeetingType.GENERAL_CONSULTATION: {
                "duration": 45,
                "agenda_template": "nia_general_consultation_agenda.txt",
                "preparation_items": [
                    "Review user context",
                    "Prepare general recommendations",
                    "Gather relevant resources",
                    "Plan discussion topics",
                ],
            },
        }

    def get_available_time_slots(
        self,
        user: User,
        date_range: Tuple[datetime, datetime],
        meeting_type: NIAMeetingType = NIAMeetingType.GENERAL_CONSULTATION,
    ) -> List[Dict]:
        """Get available time slots for NIA meetings"""
        try:
            start_date, end_date = date_range
            template = self.meeting_templates[meeting_type]
            duration = template["duration"]

            # Use intelligent service to find available slots
            availability = self.intelligent_service.analyze_user_availability(
                user, (start_date, end_date)
            )

            # Filter slots based on NIA meeting requirements
            available_slots = []
            for slot in availability.get("available_slots", []):
                # Ensure slot is long enough for the meeting type
                slot_duration = int((slot["end"] - slot["start"]).total_seconds() / 60)
                if slot_duration >= duration:
                    # Adjust slot duration to match meeting type
                    adjusted_end = slot["start"] + timedelta(minutes=duration)

                    available_slots.append(
                        {
                            "start_time": slot["start"],
                            "end_time": adjusted_end,
                            "duration_minutes": duration,
                            "meeting_type": meeting_type.value,
                            "recommended": self._is_optimal_nia_time(slot["start"]),
                            "preparation_time": self._calculate_preparation_time(
                                meeting_type
                            ),
                        }
                    )

            # Sort by recommendation score
            available_slots.sort(
                key=lambda x: (x["recommended"], x["start_time"]), reverse=True
            )
            return available_slots[:10]  # Return top 10 slots

        except Exception as e:
            logger.error(f"Error getting available time slots: {str(e)}")
            return []

    def _is_optimal_nia_time(self, start_time: datetime) -> bool:
        """Determine if a time slot is optimal for NIA meetings"""
        hour = start_time.hour
        day_of_week = start_time.weekday()

        # Prefer business hours (9 AM - 5 PM) on weekdays
        if day_of_week < 5 and 9 <= hour <= 16:
            return True

        return False

    def _calculate_preparation_time(self, meeting_type: NIAMeetingType) -> int:
        """Calculate preparation time needed before meeting (in minutes)"""
        preparation_times = {
            NIAMeetingType.LEAD_CONSULTATION: 15,
            NIAMeetingType.SALES_STRATEGY: 20,
            NIAMeetingType.OPPORTUNITY_REVIEW: 10,
            NIAMeetingType.FOLLOW_UP: 10,
            NIAMeetingType.TRAINING: 30,
            NIAMeetingType.GENERAL_CONSULTATION: 15,
        }
        return preparation_times.get(meeting_type, 15)

    def schedule_nia_meeting(
        self, user: User, meeting_data: Dict
    ) -> Optional[MeetingSession]:
        """Schedule a meeting with NIA"""
        try:
            meeting_type = NIAMeetingType(
                meeting_data.get(
                    "meeting_type", NIAMeetingType.GENERAL_CONSULTATION.value
                )
            )
            start_time = meeting_data["start_time"]
            platform = meeting_data.get(
                "platform", "google_meet"
            )  # Default to Google Meet
            lead_id = meeting_data.get("lead_id")  # Optional lead context

            # Get meeting template
            template = self.meeting_templates[meeting_type]
            duration = template["duration"]
            end_time = start_time + timedelta(minutes=duration)

            # Generate meeting title and description
            title = self._generate_meeting_title(meeting_type, user, lead_id)
            description = self._generate_meeting_description(
                meeting_type, user, lead_id
            )

            # Create meeting based on platform preference
            if platform == "microsoft_teams":
                meeting_session = self.teams_service.create_meeting(
                    user=user,
                    title=title,
                    description=description,
                    start_time=start_time,
                    end_time=end_time,
                    attendee_emails=[self.nia_email],
                )
            else:
                meeting_session = self.google_service.create_meeting(
                    user=user,
                    title=title,
                    description=description,
                    start_time=start_time,
                    end_time=end_time,
                    attendee_emails=[self.nia_email],
                )

            if meeting_session:
                # Add NIA-specific metadata
                MeetingStatusUpdate.objects.create(
                    meeting=meeting_session,
                    update_type=MeetingStatusUpdate.UpdateType.CREATED,
                    description=f"NIA meeting scheduled: {meeting_type.value}",
                    metadata={
                        "nia_meeting_type": meeting_type.value,
                        "lead_id": lead_id,
                        "platform": platform,
                        "preparation_items": template["preparation_items"],
                        "auto_generated_agenda": True,
                    },
                )

                # Schedule preparation reminder
                self._schedule_preparation_reminder(meeting_session, meeting_type)

                # Generate and attach meeting agenda
                agenda = self._generate_meeting_agenda(
                    meeting_session, meeting_type, lead_id
                )

                logger.info(f"Successfully scheduled NIA meeting: {meeting_session.id}")
                return meeting_session

            return None

        except Exception as e:
            logger.error(f"Error scheduling NIA meeting: {str(e)}")
            return None

    def _generate_meeting_title(
        self, meeting_type: NIAMeetingType, user: User, lead_id: str = None
    ) -> str:
        """Generate appropriate meeting title"""
        base_titles = {
            NIAMeetingType.LEAD_CONSULTATION: "NIA Lead Consultation",
            NIAMeetingType.SALES_STRATEGY: "NIA Sales Strategy Session",
            NIAMeetingType.OPPORTUNITY_REVIEW: "NIA Opportunity Review",
            NIAMeetingType.FOLLOW_UP: "NIA Follow-up Meeting",
            NIAMeetingType.TRAINING: "NIA Training Session",
            NIAMeetingType.GENERAL_CONSULTATION: "NIA Consultation",
        }

        title = base_titles.get(meeting_type, "NIA Meeting")

        # Add lead context if available
        if lead_id and AI_SERVICE_AVAILABLE:
            try:
                from ai_service.models import Lead

                lead = Lead.objects.get(id=lead_id, user=user)
                title += f" - {lead.company_name}"
            except:
                pass

        return title

    def _generate_meeting_description(
        self, meeting_type: NIAMeetingType, user: User, lead_id: str = None
    ) -> str:
        """Generate meeting description with context"""
        descriptions = {
            NIAMeetingType.LEAD_CONSULTATION: "Consultation with NIA to discuss lead qualification, conversion strategies, and next steps.",
            NIAMeetingType.SALES_STRATEGY: "Strategic session with NIA to review sales performance and optimize your sales approach.",
            NIAMeetingType.OPPORTUNITY_REVIEW: "Review session with NIA to analyze opportunity progression and identify success factors.",
            NIAMeetingType.FOLLOW_UP: "Follow-up meeting with NIA to review progress and address any new challenges.",
            NIAMeetingType.TRAINING: "Training session with NIA to enhance your sales skills and system knowledge.",
            NIAMeetingType.GENERAL_CONSULTATION: "General consultation with NIA for sales guidance and support.",
        }

        description = descriptions.get(
            meeting_type, "Meeting with NIA for sales assistance."
        )

        # Add lead context if available
        if lead_id and AI_SERVICE_AVAILABLE:
            try:
                from ai_service.models import Lead

                lead = Lead.objects.get(id=lead_id, user=user)
                description += f"\n\nLead Context: {lead.company_name}"
                if lead.pain_points:
                    description += f"\nPain Points: {', '.join(lead.pain_points[:3])}"
            except:
                pass

        return description

    def _generate_meeting_agenda(
        self, meeting: MeetingSession, meeting_type: NIAMeetingType, lead_id: str = None
    ) -> str:
        """Generate intelligent meeting agenda based on context"""
        try:
            template = self.meeting_templates[meeting_type]

            # Base agenda structure
            agenda_items = []

            if meeting_type == NIAMeetingType.LEAD_CONSULTATION:
                agenda_items = [
                    "Welcome and introductions (5 min)",
                    "Lead overview and current status (10 min)",
                    "Pain point analysis and qualification (15 min)",
                    "Conversion strategy recommendations (10 min)",
                    "Next steps and action items (5 min)",
                ]

                # Add lead-specific context
                if lead_id and AI_SERVICE_AVAILABLE:
                    try:
                        from ai_service.models import AIInsights, Lead

                        lead = Lead.objects.get(id=lead_id, user=meeting.organizer)
                        insights = AIInsights.objects.filter(lead=lead).first()

                        if insights:
                            agenda_items.insert(
                                2,
                                f"AI insights review - Lead score: {insights.lead_score}/10 (5 min)",
                            )
                            if insights.recommended_actions:
                                agenda_items.insert(
                                    -1, "Review AI-recommended actions (5 min)"
                                )
                    except:
                        pass

            elif meeting_type == NIAMeetingType.SALES_STRATEGY:
                agenda_items = [
                    "Welcome and current performance review (10 min)",
                    "Pipeline analysis and opportunities (15 min)",
                    "Strategy optimization recommendations (20 min)",
                    "Implementation planning (10 min)",
                    "Q&A and next steps (5 min)",
                ]

            elif meeting_type == NIAMeetingType.OPPORTUNITY_REVIEW:
                agenda_items = [
                    "Opportunity status update (5 min)",
                    "Deal progression analysis (10 min)",
                    "Risk assessment and mitigation (10 min)",
                    "Next steps planning (5 min)",
                ]

            elif meeting_type == NIAMeetingType.FOLLOW_UP:
                agenda_items = [
                    "Previous action items review (10 min)",
                    "Progress updates and challenges (10 min)",
                    "New recommendations (5 min)",
                    "Updated action plan (5 min)",
                ]

            elif meeting_type == NIAMeetingType.TRAINING:
                agenda_items = [
                    "Training objectives and agenda (10 min)",
                    "Core concepts and best practices (30 min)",
                    "Hands-on practice and scenarios (30 min)",
                    "Q&A and additional resources (15 min)",
                    "Next steps and follow-up (5 min)",
                ]

            else:  # GENERAL_CONSULTATION
                agenda_items = [
                    "Welcome and current challenges (10 min)",
                    "Discussion and analysis (20 min)",
                    "Recommendations and guidance (10 min)",
                    "Action items and next steps (5 min)",
                ]

            # Format agenda
            agenda = f"Meeting Agenda - {meeting.title}\n"
            agenda += f"Duration: {template['duration']} minutes\n\n"

            for i, item in enumerate(agenda_items, 1):
                agenda += f"{i}. {item}\n"

            agenda += "\nPreparation Items:\n"
            for item in template["preparation_items"]:
                agenda += f"• {item}\n"

            return agenda

        except Exception as e:
            logger.error(f"Error generating meeting agenda: {str(e)}")
            return "Meeting agenda will be provided before the meeting."

    def _schedule_preparation_reminder(
        self, meeting: MeetingSession, meeting_type: NIAMeetingType
    ):
        """Schedule preparation reminder before meeting"""
        try:
            prep_time = self._calculate_preparation_time(meeting_type)
            reminder_time = meeting.scheduled_start_time - timedelta(minutes=prep_time)

            MeetingStatusUpdate.objects.create(
                meeting=meeting,
                update_type=MeetingStatusUpdate.UpdateType.CREATED,
                description=f"Preparation reminder scheduled for {reminder_time.strftime('%Y-%m-%d %H:%M')}",
                metadata={
                    "reminder_type": "preparation",
                    "reminder_time": reminder_time.isoformat(),
                    "preparation_minutes": prep_time,
                },
            )

        except Exception as e:
            logger.error(f"Error scheduling preparation reminder: {str(e)}")

    def generate_meeting_summary(self, meeting: MeetingSession) -> Dict:
        """Generate post-meeting summary with action items"""
        try:
            # Get meeting metadata
            nia_updates = meeting.status_updates.filter(
                description__icontains="NIA"
            ).first()

            meeting_type = NIAMeetingType.GENERAL_CONSULTATION
            lead_id = None

            if nia_updates and nia_updates.metadata:
                meeting_type = NIAMeetingType(
                    nia_updates.metadata.get("nia_meeting_type", "general_consultation")
                )
                lead_id = nia_updates.metadata.get("lead_id")

            # Generate summary based on meeting type
            summary = {
                "meeting_id": str(meeting.id),
                "meeting_type": meeting_type.value,
                "title": meeting.title,
                "duration_minutes": meeting.actual_duration_minutes
                or meeting.duration_minutes,
                "participants": meeting.participants.count(),
                "status": meeting.status,
                "key_outcomes": self._generate_key_outcomes(
                    meeting, meeting_type, lead_id
                ),
                "action_items": self._generate_action_items(
                    meeting, meeting_type, lead_id
                ),
                "next_steps": self._generate_next_steps(meeting, meeting_type, lead_id),
                "nia_recommendations": self._generate_nia_recommendations(
                    meeting, meeting_type, lead_id
                ),
                "follow_up_required": self._determine_follow_up_needed(
                    meeting, meeting_type
                ),
                "effectiveness_score": self._calculate_meeting_effectiveness(meeting),
                "generated_at": timezone.now().isoformat(),
            }

            # Store summary as meeting update
            MeetingStatusUpdate.objects.create(
                meeting=meeting,
                update_type=MeetingStatusUpdate.UpdateType.CREATED,
                description="Meeting summary generated",
                metadata={"summary_type": "post_meeting", "summary_data": summary},
            )

            return summary

        except Exception as e:
            logger.error(f"Error generating meeting summary: {str(e)}")
            return {}

    def _generate_key_outcomes(
        self, meeting: MeetingSession, meeting_type: NIAMeetingType, lead_id: str = None
    ) -> List[str]:
        """Generate key outcomes based on meeting type"""
        # This would typically integrate with meeting transcription or notes
        # For now, return template-based outcomes

        outcomes_templates = {
            NIAMeetingType.LEAD_CONSULTATION: [
                "Lead qualification completed",
                "Pain points identified and prioritized",
                "Conversion strategy defined",
                "Next engagement steps planned",
            ],
            NIAMeetingType.SALES_STRATEGY: [
                "Current performance analyzed",
                "Optimization opportunities identified",
                "Strategy adjustments recommended",
                "Implementation timeline established",
            ],
            NIAMeetingType.OPPORTUNITY_REVIEW: [
                "Opportunity status assessed",
                "Risk factors identified",
                "Mitigation strategies developed",
                "Progression plan updated",
            ],
        }

        return outcomes_templates.get(
            meeting_type, ["Meeting objectives discussed", "Action items identified"]
        )

    def _generate_action_items(
        self, meeting: MeetingSession, meeting_type: NIAMeetingType, lead_id: str = None
    ) -> List[Dict]:
        """Generate action items based on meeting context"""
        # Template-based action items
        action_templates = {
            NIAMeetingType.LEAD_CONSULTATION: [
                {
                    "task": "Follow up with lead within 24 hours",
                    "owner": "User",
                    "due_date": "tomorrow",
                },
                {
                    "task": "Prepare customized proposal",
                    "owner": "User",
                    "due_date": "3 days",
                },
                {
                    "task": "Schedule product demo",
                    "owner": "User",
                    "due_date": "1 week",
                },
            ],
            NIAMeetingType.SALES_STRATEGY: [
                {
                    "task": "Implement recommended pipeline changes",
                    "owner": "User",
                    "due_date": "1 week",
                },
                {
                    "task": "Update CRM with new strategy",
                    "owner": "User",
                    "due_date": "2 days",
                },
                {
                    "task": "Schedule follow-up strategy review",
                    "owner": "NIA",
                    "due_date": "2 weeks",
                },
            ],
        }

        return action_templates.get(meeting_type, [])

    def _generate_next_steps(
        self, meeting: MeetingSession, meeting_type: NIAMeetingType, lead_id: str = None
    ) -> List[str]:
        """Generate next steps recommendations"""
        next_steps_templates = {
            NIAMeetingType.LEAD_CONSULTATION: [
                "Execute follow-up plan with lead",
                "Monitor lead engagement and response",
                "Schedule opportunity review if lead converts",
            ],
            NIAMeetingType.SALES_STRATEGY: [
                "Implement strategy recommendations",
                "Track performance improvements",
                "Schedule monthly strategy review",
            ],
        }

        return next_steps_templates.get(
            meeting_type, ["Continue with planned activities"]
        )

    def _generate_nia_recommendations(
        self, meeting: MeetingSession, meeting_type: NIAMeetingType, lead_id: str = None
    ) -> List[str]:
        """Generate NIA-specific recommendations"""
        return [
            "Continue regular NIA consultations for optimal results",
            "Leverage AI insights for better decision making",
            "Use NIA meeting templates for consistent outcomes",
        ]

    def _determine_follow_up_needed(
        self, meeting: MeetingSession, meeting_type: NIAMeetingType
    ) -> bool:
        """Determine if follow-up meeting is needed"""
        follow_up_types = [
            NIAMeetingType.LEAD_CONSULTATION,
            NIAMeetingType.SALES_STRATEGY,
            NIAMeetingType.TRAINING,
        ]
        return meeting_type in follow_up_types

    def _calculate_meeting_effectiveness(self, meeting: MeetingSession) -> float:
        """Calculate meeting effectiveness score (0-10)"""
        score = 5.0  # Base score

        # Factor in duration efficiency
        planned_duration = meeting.duration_minutes
        actual_duration = meeting.actual_duration_minutes

        if actual_duration and planned_duration:
            duration_ratio = actual_duration / planned_duration
            if 0.9 <= duration_ratio <= 1.1:  # Within 10% of planned
                score += 1
            elif duration_ratio > 1.5:  # Significantly over time
                score -= 1

        # Factor in on-time start
        if meeting.actual_start_time and meeting.scheduled_start_time:
            delay_minutes = (
                meeting.actual_start_time - meeting.scheduled_start_time
            ).total_seconds() / 60
            if delay_minutes <= 5:
                score += 1
            elif delay_minutes > 15:
                score -= 1

        # Factor in completion
        if meeting.status == MeetingSession.Status.ENDED:
            score += 1
        elif meeting.status == MeetingSession.Status.CANCELLED:
            score -= 3

        # Factor in participant engagement
        participants = meeting.participants.all()
        if participants.count() >= 2:  # User + NIA
            score += 0.5

        return max(0, min(10, score))

    def get_meeting_analytics(
        self, user: User, date_range: Tuple[datetime, datetime] = None
    ) -> Dict:
        """Get analytics for NIA meetings"""
        try:
            if not date_range:
                end_date = timezone.now()
                start_date = end_date - timedelta(days=30)
                date_range = (start_date, end_date)

            start_date, end_date = date_range

            # Get NIA meetings
            nia_meetings = MeetingSession.objects.filter(
                organizer=user,
                scheduled_start_time__gte=start_date,
                scheduled_start_time__lte=end_date,
                status_updates__description__icontains="NIA meeting",
            ).distinct()

            # Calculate analytics
            total_meetings = nia_meetings.count()
            completed_meetings = nia_meetings.filter(
                status=MeetingSession.Status.ENDED
            ).count()
            cancelled_meetings = nia_meetings.filter(
                status=MeetingSession.Status.CANCELLED
            ).count()

            # Meeting type distribution
            type_distribution = {}
            effectiveness_scores = []

            for meeting in nia_meetings:
                # Get meeting type from metadata
                nia_update = meeting.status_updates.filter(
                    description__icontains="NIA meeting"
                ).first()

                if nia_update and nia_update.metadata:
                    meeting_type = nia_update.metadata.get(
                        "nia_meeting_type", "general_consultation"
                    )
                    type_distribution[meeting_type] = (
                        type_distribution.get(meeting_type, 0) + 1
                    )

                # Calculate effectiveness
                effectiveness = self._calculate_meeting_effectiveness(meeting)
                effectiveness_scores.append(effectiveness)

            avg_effectiveness = (
                sum(effectiveness_scores) / len(effectiveness_scores)
                if effectiveness_scores
                else 0
            )

            return {
                "total_meetings": total_meetings,
                "completed_meetings": completed_meetings,
                "cancelled_meetings": cancelled_meetings,
                "completion_rate": (
                    (completed_meetings / total_meetings * 100)
                    if total_meetings > 0
                    else 0
                ),
                "meeting_type_distribution": type_distribution,
                "average_effectiveness_score": round(avg_effectiveness, 2),
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "roi_indicators": {
                    "meetings_per_week": (
                        total_meetings / 4 if total_meetings > 0 else 0
                    ),
                    "avg_effectiveness": avg_effectiveness,
                    "consistency_score": self._calculate_consistency_score(
                        nia_meetings
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Error getting meeting analytics: {str(e)}")
            return {}

    def _calculate_consistency_score(self, meetings) -> float:
        """Calculate consistency score based on regular meeting patterns"""
        if meetings.count() < 2:
            return 0.0

        # Calculate time gaps between meetings
        meeting_dates = [
            m.scheduled_start_time for m in meetings.order_by("scheduled_start_time")
        ]
        gaps = []

        for i in range(1, len(meeting_dates)):
            gap_days = (meeting_dates[i] - meeting_dates[i - 1]).days
            gaps.append(gap_days)

        if not gaps:
            return 0.0

        # Score based on regularity (lower variance = higher score)
        avg_gap = sum(gaps) / len(gaps)
        variance = sum((gap - avg_gap) ** 2 for gap in gaps) / len(gaps)

        # Convert to 0-10 score (lower variance = higher score)
        consistency_score = max(0, 10 - (variance / 10))
        return min(10, consistency_score)
