"""
Unified Video Platform Service for Google Meet and Microsoft Teams Integration

This service provides a unified interface for video platform operations including:
- Meeting creation with agenda
- Recording and transcript access
- Meeting link generation and sharing
- Automated meeting management
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from django.contrib.auth import get_user_model
from django.utils import timezone

from .google_meet_service import GoogleMeetService
from .microsoft_teams_service import MicrosoftTeamsService
from .models import GoogleMeetCredentials, MeetingSession, MicrosoftTeamsCredentials

User = get_user_model()
logger = logging.getLogger(__name__)


class VideoPlatformService:
    """Unified service for video platform operations"""

    def __init__(self):
        self.google_service = GoogleMeetService()
        self.teams_service = MicrosoftTeamsService()

    def get_user_preferred_platform(self, user: User) -> str:
        """Determine user's preferred video platform based on available credentials"""
        try:
            # Check for Google Meet credentials
            google_available = False
            try:
                google_creds = GoogleMeetCredentials.objects.get(user=user)
                google_available = not google_creds.is_token_expired()
            except GoogleMeetCredentials.DoesNotExist:
                pass

            # Check for Teams credentials
            teams_available = False
            try:
                teams_creds = MicrosoftTeamsCredentials.objects.get(user=user)
                teams_available = not teams_creds.is_token_expired()
            except MicrosoftTeamsCredentials.DoesNotExist:
                pass

            # Return preferred platform based on availability
            if teams_available and google_available:
                # If both available, prefer Teams (more enterprise features)
                return "microsoft_teams"
            elif teams_available:
                return "microsoft_teams"
            elif google_available:
                return "google_meet"
            else:
                return "none"

        except Exception as e:
            logger.error(
                f"Error determining preferred platform for user {user.id}: {str(e)}"
            )
            return "none"

    def create_meeting_with_agenda(
        self,
        user: User,
        title: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
        attendee_emails: List[str] = None,
        agenda_items: List[str] = None,
        platform: str = None,
    ) -> Optional[MeetingSession]:
        """Create a meeting with agenda on the specified or preferred platform"""
        try:
            # Determine platform to use
            if not platform:
                platform = self.get_user_preferred_platform(user)

            if platform == "none":
                logger.error(
                    f"No video platform credentials available for user {user.id}"
                )
                return None

            # Create meeting on the appropriate platform
            if platform == "microsoft_teams":
                meeting_session = self.teams_service.create_meeting_with_agenda(
                    user=user,
                    title=title,
                    description=description,
                    start_time=start_time,
                    end_time=end_time,
                    attendee_emails=attendee_emails,
                    agenda_items=agenda_items,
                )
            elif platform == "google_meet":
                meeting_session = self.google_service.create_meeting_with_agenda(
                    user=user,
                    title=title,
                    description=description,
                    start_time=start_time,
                    end_time=end_time,
                    attendee_emails=attendee_emails,
                    agenda_items=agenda_items,
                )
            else:
                logger.error(f"Unsupported platform: {platform}")
                return None

            if meeting_session:
                logger.info(
                    f"Created meeting with agenda on {platform}: {meeting_session.id}"
                )

            return meeting_session

        except Exception as e:
            logger.error(f"Error creating meeting with agenda: {str(e)}")
            return None

    def get_meeting_recordings(self, meeting_session: MeetingSession) -> List[Dict]:
        """Get recordings for a meeting regardless of platform"""
        try:
            user = meeting_session.organizer

            if meeting_session.meeting_type == MeetingSession.MeetingType.GOOGLE_MEET:
                return self.google_service.get_meeting_recordings(meeting_session, user)
            elif (
                meeting_session.meeting_type
                == MeetingSession.MeetingType.MICROSOFT_TEAMS
            ):
                return self.teams_service.get_meeting_recordings(
                    user, meeting_session.teams_meeting_id
                )
            else:
                logger.error(
                    f"Unsupported meeting type: {meeting_session.meeting_type}"
                )
                return []

        except Exception as e:
            logger.error(f"Error getting meeting recordings: {str(e)}")
            return []

    def get_meeting_transcripts(self, meeting_session: MeetingSession) -> List[Dict]:
        """Get transcripts for a meeting regardless of platform"""
        try:
            user = meeting_session.organizer

            if meeting_session.meeting_type == MeetingSession.MeetingType.GOOGLE_MEET:
                return self.google_service.get_meeting_transcripts(
                    meeting_session, user
                )
            elif (
                meeting_session.meeting_type
                == MeetingSession.MeetingType.MICROSOFT_TEAMS
            ):
                return self.teams_service.get_meeting_transcripts(
                    user, meeting_session.teams_meeting_id
                )
            else:
                logger.error(
                    f"Unsupported meeting type: {meeting_session.meeting_type}"
                )
                return []

        except Exception as e:
            logger.error(f"Error getting meeting transcripts: {str(e)}")
            return []

    def generate_meeting_link(self, meeting_session: MeetingSession) -> Optional[str]:
        """Generate or retrieve meeting link regardless of platform"""
        try:
            if meeting_session.meeting_type == MeetingSession.MeetingType.GOOGLE_MEET:
                return self.google_service.generate_meeting_link(meeting_session)
            elif (
                meeting_session.meeting_type
                == MeetingSession.MeetingType.MICROSOFT_TEAMS
            ):
                return self.teams_service.generate_meeting_link(meeting_session)
            else:
                logger.error(
                    f"Unsupported meeting type: {meeting_session.meeting_type}"
                )
                return None

        except Exception as e:
            logger.error(f"Error generating meeting link: {str(e)}")
            return None

    def share_meeting_link(
        self,
        meeting_session: MeetingSession,
        recipient_emails: List[str],
        custom_message: str = None,
    ) -> bool:
        """Share meeting link via email regardless of platform"""
        try:
            if meeting_session.meeting_type == MeetingSession.MeetingType.GOOGLE_MEET:
                return self.google_service.share_meeting_link(
                    meeting_session, recipient_emails, custom_message
                )
            elif (
                meeting_session.meeting_type
                == MeetingSession.MeetingType.MICROSOFT_TEAMS
            ):
                return self.teams_service.share_meeting_link(
                    meeting_session, recipient_emails, custom_message
                )
            else:
                logger.error(
                    f"Unsupported meeting type: {meeting_session.meeting_type}"
                )
                return False

        except Exception as e:
            logger.error(f"Error sharing meeting link: {str(e)}")
            return False

    def enable_meeting_recording(self, meeting_session: MeetingSession) -> bool:
        """Enable recording for a meeting regardless of platform"""
        try:
            user = meeting_session.organizer

            if meeting_session.meeting_type == MeetingSession.MeetingType.GOOGLE_MEET:
                # Google Meet recording is typically enabled by default if user has permission
                meeting_session.recording_enabled = True
                meeting_session.save()
                logger.info(
                    f"Recording enabled for Google Meet meeting {meeting_session.id}"
                )
                return True
            elif (
                meeting_session.meeting_type
                == MeetingSession.MeetingType.MICROSOFT_TEAMS
            ):
                return self.teams_service.enable_meeting_recording(
                    meeting_session, user
                )
            else:
                logger.error(
                    f"Unsupported meeting type: {meeting_session.meeting_type}"
                )
                return False

        except Exception as e:
            logger.error(f"Error enabling meeting recording: {str(e)}")
            return False

    def get_platform_capabilities(self, user: User) -> Dict[str, Dict]:
        """Get capabilities for each available platform"""
        try:
            capabilities = {
                "google_meet": {
                    "available": False,
                    "features": {
                        "meeting_creation": True,
                        "agenda_support": True,
                        "recording_access": True,
                        "transcript_access": True,
                        "link_sharing": True,
                        "email_integration": True,
                    },
                },
                "microsoft_teams": {
                    "available": False,
                    "features": {
                        "meeting_creation": True,
                        "agenda_support": True,
                        "recording_access": True,
                        "transcript_access": True,
                        "link_sharing": True,
                        "email_integration": True,
                        "channel_integration": True,
                        "recording_control": True,
                    },
                },
            }

            # Check Google Meet availability
            try:
                google_creds = GoogleMeetCredentials.objects.get(user=user)
                capabilities["google_meet"][
                    "available"
                ] = not google_creds.is_token_expired()
            except GoogleMeetCredentials.DoesNotExist:
                pass

            # Check Teams availability
            try:
                teams_creds = MicrosoftTeamsCredentials.objects.get(user=user)
                capabilities["microsoft_teams"][
                    "available"
                ] = not teams_creds.is_token_expired()
            except MicrosoftTeamsCredentials.DoesNotExist:
                pass

            return capabilities

        except Exception as e:
            logger.error(f"Error getting platform capabilities: {str(e)}")
            return {}

    def create_automated_meeting(
        self,
        user: User,
        lead_data: Dict,
        meeting_type: str = "discovery",
        platform: str = None,
    ) -> Optional[MeetingSession]:
        """Create an automated meeting with AI-generated agenda based on lead data"""
        try:
            from .pre_meeting_intelligence import PreMeetingIntelligenceService

            # Generate meeting details using AI
            intelligence_service = PreMeetingIntelligenceService()

            # Generate agenda based on lead data and meeting type
            agenda_items = self._generate_meeting_agenda(lead_data, meeting_type)

            # Generate meeting title and description
            title = self._generate_meeting_title(lead_data, meeting_type)
            description = self._generate_meeting_description(lead_data, meeting_type)

            # Set meeting timing (default to 1 hour from now + 1 day)
            start_time = timezone.now() + timezone.timedelta(days=1)
            end_time = start_time + timezone.timedelta(hours=1)

            # Extract attendee emails from lead data
            attendee_emails = []
            if "contact_email" in lead_data:
                attendee_emails.append(lead_data["contact_email"])
            if "additional_contacts" in lead_data:
                for contact in lead_data["additional_contacts"]:
                    if "email" in contact:
                        attendee_emails.append(contact["email"])

            # Create the meeting
            meeting_session = self.create_meeting_with_agenda(
                user=user,
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                attendee_emails=attendee_emails,
                agenda_items=agenda_items,
                platform=platform,
            )

            if meeting_session:
                # Store lead context in meeting metadata
                meeting_session.ai_insights = meeting_session.ai_insights or {}
                meeting_session.ai_insights["lead_data"] = lead_data
                meeting_session.ai_insights["meeting_type"] = meeting_type
                meeting_session.ai_insights["automated"] = True
                meeting_session.save()

                logger.info(f"Created automated meeting for lead: {meeting_session.id}")

            return meeting_session

        except Exception as e:
            logger.error(f"Error creating automated meeting: {str(e)}")
            return None

    def _generate_meeting_agenda(self, lead_data: Dict, meeting_type: str) -> List[str]:
        """Generate meeting agenda based on lead data and meeting type"""
        try:
            agenda_templates = {
                "discovery": [
                    "Introductions and company overview",
                    "Understanding current challenges and pain points",
                    "Exploring business requirements and goals",
                    "Discussing timeline and decision-making process",
                    "Next steps and follow-up actions",
                ],
                "demo": [
                    "Brief recap of previous discussions",
                    "Product demonstration focused on key requirements",
                    "Q&A session and technical questions",
                    "Pricing and implementation discussion",
                    "Next steps and proposal timeline",
                ],
                "proposal": [
                    "Proposal presentation and walkthrough",
                    "Addressing questions and concerns",
                    "Implementation timeline and milestones",
                    "Contract terms and pricing discussion",
                    "Decision timeline and next steps",
                ],
                "closing": [
                    "Final questions and clarifications",
                    "Contract review and terms finalization",
                    "Implementation planning and kickoff",
                    "Success metrics and expectations",
                    "Signing and onboarding next steps",
                ],
            }

            base_agenda = agenda_templates.get(
                meeting_type, agenda_templates["discovery"]
            )

            # Customize agenda based on lead data
            if "industry" in lead_data:
                base_agenda.insert(
                    1, f"Industry-specific challenges in {lead_data['industry']}"
                )

            if "pain_points" in lead_data and lead_data["pain_points"]:
                base_agenda.insert(
                    -1,
                    f"Addressing specific concerns: {', '.join(lead_data['pain_points'][:2])}",
                )

            return base_agenda

        except Exception as e:
            logger.error(f"Error generating meeting agenda: {str(e)}")
            return ["Meeting discussion", "Q&A", "Next steps"]

    def _generate_meeting_title(self, lead_data: Dict, meeting_type: str) -> str:
        """Generate meeting title based on lead data and meeting type"""
        try:
            company_name = lead_data.get("company_name", "Prospect")

            title_templates = {
                "discovery": f"Discovery Call - {company_name}",
                "demo": f"Product Demo - {company_name}",
                "proposal": f"Proposal Presentation - {company_name}",
                "closing": f"Contract Discussion - {company_name}",
                "follow_up": f"Follow-up Meeting - {company_name}",
            }

            return title_templates.get(meeting_type, f"Meeting with {company_name}")

        except Exception as e:
            logger.error(f"Error generating meeting title: {str(e)}")
            return "Sales Meeting"

    def _generate_meeting_description(self, lead_data: Dict, meeting_type: str) -> str:
        """Generate meeting description based on lead data and meeting type"""
        try:
            company_name = lead_data.get("company_name", "the prospect")
            industry = lead_data.get("industry", "")

            description = f"Meeting with {company_name}"
            if industry:
                description += f" ({industry})"

            if meeting_type == "discovery":
                description += " to understand their business needs and challenges."
            elif meeting_type == "demo":
                description += (
                    " to demonstrate our solution and address their requirements."
                )
            elif meeting_type == "proposal":
                description += " to present our proposal and discuss implementation."
            elif meeting_type == "closing":
                description += " to finalize the agreement and next steps."

            if "pain_points" in lead_data and lead_data["pain_points"]:
                description += (
                    f"\n\nKey topics to address: {', '.join(lead_data['pain_points'])}"
                )

            return description

        except Exception as e:
            logger.error(f"Error generating meeting description: {str(e)}")
            return "Sales meeting discussion"

    def get_meeting_analytics(self, user: User, days_back: int = 30) -> Dict:
        """Get analytics for video platform usage"""
        try:
            from datetime import timedelta

            from django.db.models import Count, Q

            start_date = timezone.now() - timedelta(days=days_back)

            # Get meeting statistics
            meetings = MeetingSession.objects.filter(
                organizer=user, created_at__gte=start_date
            )

            analytics = {
                "total_meetings": meetings.count(),
                "google_meet_meetings": meetings.filter(
                    meeting_type=MeetingSession.MeetingType.GOOGLE_MEET
                ).count(),
                "teams_meetings": meetings.filter(
                    meeting_type=MeetingSession.MeetingType.MICROSOFT_TEAMS
                ).count(),
                "meetings_with_recordings": meetings.filter(
                    recording_enabled=True
                ).count(),
                "completed_meetings": meetings.filter(
                    status=MeetingSession.Status.ENDED
                ).count(),
                "cancelled_meetings": meetings.filter(
                    status=MeetingSession.Status.CANCELLED
                ).count(),
                "platform_distribution": {
                    "google_meet": meetings.filter(
                        meeting_type=MeetingSession.MeetingType.GOOGLE_MEET
                    ).count(),
                    "microsoft_teams": meetings.filter(
                        meeting_type=MeetingSession.MeetingType.MICROSOFT_TEAMS
                    ).count(),
                },
            }

            return analytics

        except Exception as e:
            logger.error(f"Error getting meeting analytics: {str(e)}")
            return {}
