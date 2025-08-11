import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from credentials import get_google_meet_credentials

from .models import (
    GoogleMeetCredentials,
    MeetingParticipant,
    MeetingSession,
    MeetingStatusUpdate,
)

User = get_user_model()
logger = logging.getLogger(__name__)


class GoogleMeetService:
    """Service for managing Google Meet integration"""

    def __init__(self):
        google_creds = get_google_meet_credentials()
        self.client_id = google_creds["web"]["client_id"]
        self.client_secret = google_creds["web"]["client_secret"]
        self.redirect_uri = settings.GOOGLE_MEET_REDIRECT_URI
        self.scopes = settings.GOOGLE_MEET_SCOPES

    def get_authorization_url(self, user_id: str) -> str:
        """Generate OAuth authorization URL for Google Meet"""
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri],
                    }
                },
                scopes=self.scopes,
            )
            flow.redirect_uri = self.redirect_uri

            authorization_url, state = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                state=user_id,  # Pass user_id as state parameter
            )

            logger.info(f"Generated authorization URL for user {user_id}")
            return authorization_url

        except Exception as e:
            logger.error(f"Error generating authorization URL: {str(e)}")
            raise

    def handle_oauth_callback(self, authorization_code: str, state: str) -> bool:
        """Handle OAuth callback and store credentials"""
        try:
            user_id = state
            user = User.objects.get(id=user_id)

            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri],
                    }
                },
                scopes=self.scopes,
            )
            flow.redirect_uri = self.redirect_uri

            # Exchange authorization code for tokens
            flow.fetch_token(code=authorization_code)
            credentials = flow.credentials

            # Store or update credentials
            google_creds, created = GoogleMeetCredentials.objects.get_or_create(
                user=user,
                defaults={
                    "access_token": credentials.token,
                    "refresh_token": credentials.refresh_token,
                    "token_expiry": credentials.expiry,
                    "scope": " ".join(self.scopes),
                },
            )

            if not created:
                # Update existing credentials
                google_creds.access_token = credentials.token
                google_creds.refresh_token = credentials.refresh_token
                google_creds.token_expiry = credentials.expiry
                google_creds.scope = " ".join(self.scopes)
                google_creds.save()

            logger.info(
                f"Successfully stored Google Meet credentials for user {user_id}"
            )
            return True

        except User.DoesNotExist:
            logger.error(f"User with ID {user_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error handling OAuth callback: {str(e)}")
            return False

    def refresh_user_credentials(self, user: User) -> bool:
        """Refresh user's Google credentials if needed"""
        try:
            google_creds = GoogleMeetCredentials.objects.get(user=user)

            if google_creds.is_token_expired():
                credentials = Credentials(
                    token=google_creds.access_token,
                    refresh_token=google_creds.refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    scopes=self.scopes,
                )

                # Refresh the token
                credentials.refresh(Request())

                # Update stored credentials
                google_creds.access_token = credentials.token
                google_creds.token_expiry = credentials.expiry
                google_creds.save()

                logger.info(f"Refreshed credentials for user {user.id}")
                return True

            return True

        except GoogleMeetCredentials.DoesNotExist:
            logger.error(f"No Google Meet credentials found for user {user.id}")
            return False
        except Exception as e:
            logger.error(f"Error refreshing credentials: {str(e)}")
            return False

    def create_meeting(
        self,
        user: User,
        title: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
        attendee_emails: List[str] = None,
    ) -> Optional[MeetingSession]:
        """Create a Google Meet meeting"""
        try:
            # Ensure user has valid credentials
            if not self.refresh_user_credentials(user):
                raise Exception("Invalid or missing Google credentials")

            google_creds = GoogleMeetCredentials.objects.get(user=user)
            credentials = Credentials(
                token=google_creds.access_token,
                refresh_token=google_creds.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=self.scopes,
            )

            # Build Calendar API service
            service = build("calendar", "v3", credentials=credentials)

            # Create calendar event with Google Meet
            event = {
                "summary": title,
                "description": description,
                "start": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": "UTC",
                },
                "end": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": "UTC",
                },
                "conferenceData": {
                    "createRequest": {
                        "requestId": str(uuid.uuid4()),
                        "conferenceSolutionKey": {"type": "hangoutsMeet"},
                    }
                },
                "attendees": [{"email": email} for email in (attendee_emails or [])],
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "email", "minutes": 24 * 60},
                        {"method": "popup", "minutes": 10},
                    ],
                },
            }

            # Create the event
            created_event = (
                service.events()
                .insert(
                    calendarId="primary",
                    body=event,
                    conferenceDataVersion=1,
                    sendUpdates="all",
                )
                .execute()
            )

            # Extract Google Meet details
            meet_url = ""
            meet_space_id = ""
            if "conferenceData" in created_event:
                conference_data = created_event["conferenceData"]
                if "entryPoints" in conference_data:
                    for entry_point in conference_data["entryPoints"]:
                        if entry_point["entryPointType"] == "video":
                            meet_url = entry_point["uri"]
                            break
                if "conferenceId" in conference_data:
                    meet_space_id = conference_data["conferenceId"]

            # Create MeetingSession record
            meeting_session = MeetingSession.objects.create(
                organizer=user,
                title=title,
                description=description,
                meeting_type=MeetingSession.MeetingType.GOOGLE_MEET,
                google_meet_url=meet_url,
                google_calendar_event_id=created_event["id"],
                google_meet_space_id=meet_space_id,
                scheduled_start_time=start_time,
                scheduled_end_time=end_time,
                status=MeetingSession.Status.SCHEDULED,
            )

            # Create participant records
            if attendee_emails:
                for email in attendee_emails:
                    participant = MeetingParticipant.objects.create(
                        meeting=meeting_session,
                        email=email,
                        name=email.split("@")[0],  # Use email prefix as default name
                        role=MeetingParticipant.ParticipantRole.ATTENDEE,
                        status=MeetingParticipant.ParticipantStatus.INVITED,
                    )

            # Add organizer as participant
            MeetingParticipant.objects.create(
                meeting=meeting_session,
                user=user,
                email=user.email,
                name=user.get_full_name() or user.email,
                role=MeetingParticipant.ParticipantRole.ORGANIZER,
                status=MeetingParticipant.ParticipantStatus.ACCEPTED,
            )

            # Create status update
            MeetingStatusUpdate.objects.create(
                meeting=meeting_session,
                update_type=MeetingStatusUpdate.UpdateType.CREATED,
                description=f"Meeting '{title}' created with Google Meet",
                triggered_by=user,
                metadata={
                    "google_event_id": created_event["id"],
                    "meet_url": meet_url,
                    "attendee_count": len(attendee_emails) if attendee_emails else 0,
                },
            )

            logger.info(
                f"Successfully created Google Meet meeting: {meeting_session.id}"
            )
            return meeting_session

        except Exception as e:
            logger.error(f"Error creating Google Meet meeting: {str(e)}")
            return None

    def update_meeting_status(
        self, meeting_session: MeetingSession, new_status: str, user: User = None
    ) -> bool:
        """Update meeting status and create status update record"""
        try:
            old_status = meeting_session.status
            meeting_session.status = new_status

            # Update timing based on status
            now = timezone.now()
            if (
                new_status == MeetingSession.Status.ACTIVE
                and not meeting_session.actual_start_time
            ):
                meeting_session.actual_start_time = now
            elif (
                new_status == MeetingSession.Status.ENDED
                and not meeting_session.actual_end_time
            ):
                meeting_session.actual_end_time = now

            meeting_session.save()

            # Create status update record
            update_type_map = {
                MeetingSession.Status.ACTIVE: MeetingStatusUpdate.UpdateType.STARTED,
                MeetingSession.Status.ENDED: MeetingStatusUpdate.UpdateType.ENDED,
                MeetingSession.Status.CANCELLED: MeetingStatusUpdate.UpdateType.CANCELLED,
            }

            update_type = update_type_map.get(
                new_status, MeetingStatusUpdate.UpdateType.CREATED
            )

            MeetingStatusUpdate.objects.create(
                meeting=meeting_session,
                update_type=update_type,
                description=f"Meeting status changed from {old_status} to {new_status}",
                triggered_by=user,
                metadata={"old_status": old_status, "new_status": new_status},
            )

            logger.info(f"Updated meeting {meeting_session.id} status to {new_status}")
            return True

        except Exception as e:
            logger.error(f"Error updating meeting status: {str(e)}")
            return False

    def get_user_meetings(self, user: User, status: str = None) -> List[MeetingSession]:
        """Get meetings for a user, optionally filtered by status"""
        try:
            queryset = MeetingSession.objects.filter(
                models.Q(organizer=user) | models.Q(participants__user=user)
            ).distinct()

            if status:
                queryset = queryset.filter(status=status)

            return list(queryset.order_by("-scheduled_start_time"))

        except Exception as e:
            logger.error(f"Error getting user meetings: {str(e)}")
            return []

    def get_meeting_recordings(
        self, meeting_session: MeetingSession, user: User
    ) -> List[Dict]:
        """Get recordings for a Google Meet meeting"""
        try:
            # Ensure user has valid credentials
            if not self.refresh_user_credentials(user):
                raise Exception("Invalid or missing Google credentials")

            google_creds = GoogleMeetCredentials.objects.get(user=user)
            credentials = Credentials(
                token=google_creds.access_token,
                refresh_token=google_creds.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=self.scopes,
            )

            # Build Drive API service to access recordings
            drive_service = build("drive", "v3", credentials=credentials)

            # Search for recordings related to this meeting
            # Google Meet recordings are typically stored in Google Drive
            query = f"name contains '{meeting_session.title}' and mimeType='video/mp4'"

            results = (
                drive_service.files()
                .list(
                    q=query,
                    fields="files(id, name, webViewLink, createdTime, size, mimeType)",
                )
                .execute()
            )

            recordings = []
            for file in results.get("files", []):
                recordings.append(
                    {
                        "id": file["id"],
                        "name": file["name"],
                        "url": file["webViewLink"],
                        "created_time": file["createdTime"],
                        "size": file.get("size", 0),
                        "mime_type": file["mimeType"],
                    }
                )

            logger.info(
                f"Found {len(recordings)} recordings for meeting {meeting_session.id}"
            )
            return recordings

        except Exception as e:
            logger.error(f"Error getting Google Meet recordings: {str(e)}")
            return []

    def get_meeting_transcripts(
        self, meeting_session: MeetingSession, user: User
    ) -> List[Dict]:
        """Get transcripts for a Google Meet meeting"""
        try:
            # Ensure user has valid credentials
            if not self.refresh_user_credentials(user):
                raise Exception("Invalid or missing Google credentials")

            google_creds = GoogleMeetCredentials.objects.get(user=user)
            credentials = Credentials(
                token=google_creds.access_token,
                refresh_token=google_creds.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=self.scopes,
            )

            # Build Drive API service to access transcripts
            drive_service = build("drive", "v3", credentials=credentials)

            # Search for transcripts related to this meeting
            # Google Meet transcripts are typically stored as Google Docs
            query = f"name contains '{meeting_session.title}' and name contains 'transcript'"

            results = (
                drive_service.files()
                .list(
                    q=query,
                    fields="files(id, name, webViewLink, createdTime, mimeType)",
                )
                .execute()
            )

            transcripts = []
            for file in results.get("files", []):
                # Get document content if it's a Google Doc
                content = ""
                if file["mimeType"] == "application/vnd.google-apps.document":
                    try:
                        docs_service = build("docs", "v1", credentials=credentials)
                        doc = (
                            docs_service.documents()
                            .get(documentId=file["id"])
                            .execute()
                        )
                        content = self._extract_text_from_doc(doc)
                    except Exception as e:
                        logger.warning(
                            f"Could not extract content from document {file['id']}: {str(e)}"
                        )

                transcripts.append(
                    {
                        "id": file["id"],
                        "name": file["name"],
                        "url": file["webViewLink"],
                        "created_time": file["createdTime"],
                        "mime_type": file["mimeType"],
                        "content": content,
                    }
                )

            logger.info(
                f"Found {len(transcripts)} transcripts for meeting {meeting_session.id}"
            )
            return transcripts

        except Exception as e:
            logger.error(f"Error getting Google Meet transcripts: {str(e)}")
            return []

    def _extract_text_from_doc(self, doc: Dict) -> str:
        """Extract text content from Google Docs document"""
        try:
            content = doc.get("body", {}).get("content", [])
            text_parts = []

            for element in content:
                if "paragraph" in element:
                    paragraph = element["paragraph"]
                    if "elements" in paragraph:
                        for elem in paragraph["elements"]:
                            if "textRun" in elem:
                                text_parts.append(elem["textRun"]["content"])

            return "".join(text_parts)

        except Exception as e:
            logger.error(f"Error extracting text from document: {str(e)}")
            return ""

    def create_meeting_with_agenda(
        self,
        user: User,
        title: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
        attendee_emails: List[str] = None,
        agenda_items: List[str] = None,
    ) -> Optional[MeetingSession]:
        """Create a Google Meet meeting with a structured agenda"""
        try:
            # Build agenda content
            agenda_content = description or ""
            if agenda_items:
                agenda_content += "\n\n📋 Meeting Agenda:\n"
                for i, item in enumerate(agenda_items, 1):
                    agenda_content += f"{i}. {item}\n"

            # Create the meeting with enhanced description
            meeting_session = self.create_meeting(
                user=user,
                title=title,
                description=agenda_content,
                start_time=start_time,
                end_time=end_time,
                attendee_emails=attendee_emails,
            )

            if meeting_session:
                # Store agenda items in meeting metadata
                meeting_session.ai_insights = meeting_session.ai_insights or {}
                meeting_session.ai_insights["agenda_items"] = agenda_items or []
                meeting_session.save()

                logger.info(
                    f"Created Google Meet meeting with agenda: {meeting_session.id}"
                )

            return meeting_session

        except Exception as e:
            logger.error(f"Error creating Google Meet meeting with agenda: {str(e)}")
            return None

    def generate_meeting_link(self, meeting_session: MeetingSession) -> Optional[str]:
        """Generate or retrieve the meeting link for sharing"""
        try:
            if meeting_session.google_meet_url:
                return meeting_session.google_meet_url

            # If no URL is stored, try to retrieve it from Google Calendar
            if meeting_session.google_calendar_event_id:
                user = meeting_session.organizer

                if not self.refresh_user_credentials(user):
                    raise Exception("Invalid or missing Google credentials")

                google_creds = GoogleMeetCredentials.objects.get(user=user)
                credentials = Credentials(
                    token=google_creds.access_token,
                    refresh_token=google_creds.refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    scopes=self.scopes,
                )

                # Build Calendar API service
                service = build("calendar", "v3", credentials=credentials)

                # Get the event details
                event = (
                    service.events()
                    .get(
                        calendarId="primary",
                        eventId=meeting_session.google_calendar_event_id,
                    )
                    .execute()
                )

                # Extract Google Meet URL
                if "conferenceData" in event:
                    conference_data = event["conferenceData"]
                    if "entryPoints" in conference_data:
                        for entry_point in conference_data["entryPoints"]:
                            if entry_point["entryPointType"] == "video":
                                meeting_url = entry_point["uri"]

                                # Update the meeting session with the URL
                                meeting_session.google_meet_url = meeting_url
                                meeting_session.save()

                                return meeting_url

            logger.warning(f"No Google Meet URL found for meeting {meeting_session.id}")
            return None

        except Exception as e:
            logger.error(f"Error generating Google Meet link: {str(e)}")
            return None

    def share_meeting_link(
        self,
        meeting_session: MeetingSession,
        recipient_emails: List[str],
        custom_message: str = None,
    ) -> bool:
        """Share meeting link via email"""
        try:
            meeting_url = self.generate_meeting_link(meeting_session)
            if not meeting_url:
                logger.error(
                    f"No meeting URL available for sharing: {meeting_session.id}"
                )
                return False

            user = meeting_session.organizer

            if not self.refresh_user_credentials(user):
                raise Exception("Invalid or missing Google credentials")

            google_creds = GoogleMeetCredentials.objects.get(user=user)
            credentials = Credentials(
                token=google_creds.access_token,
                refresh_token=google_creds.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=self.scopes,
            )

            # Build Gmail API service
            gmail_service = build("gmail", "v1", credentials=credentials)

            # Prepare email content
            subject = f"Meeting Invitation: {meeting_session.title}"

            body = (
                custom_message
                or f"""
You're invited to join our meeting:

📅 Meeting: {meeting_session.title}
🕐 Time: {meeting_session.scheduled_start_time.strftime('%Y-%m-%d %H:%M UTC')}
⏱️ Duration: {meeting_session.duration_minutes} minutes

🔗 Join the meeting: {meeting_url}

{meeting_session.description or ''}

Best regards,
{user.get_full_name() or user.email}
            """
            )

            # Send email to each recipient
            success_count = 0
            for email in recipient_emails:
                try:
                    message = {
                        "raw": self._create_email_message(
                            sender=user.email, to=email, subject=subject, body=body
                        )
                    }

                    gmail_service.users().messages().send(
                        userId="me", body=message
                    ).execute()

                    success_count += 1
                    logger.info(f"Sent meeting link to {email}")

                except Exception as e:
                    logger.error(f"Failed to send meeting link to {email}: {str(e)}")

            logger.info(
                f"Successfully shared meeting link to {success_count}/{len(recipient_emails)} recipients"
            )
            return success_count > 0

        except Exception as e:
            logger.error(f"Error sharing Google Meet link: {str(e)}")
            return False

    def _create_email_message(
        self, sender: str, to: str, subject: str, body: str
    ) -> str:
        """Create email message in the required format"""
        import base64
        from email.mime.text import MIMEText

        message = MIMEText(body)
        message["to"] = to
        message["from"] = sender
        message["subject"] = subject

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return raw_message

    def delete_meeting(self, meeting_session: MeetingSession, user: User) -> bool:
        """Delete a Google Meet meeting"""
        try:
            # Only organizer can delete
            if meeting_session.organizer != user:
                logger.error(
                    f"User {user.id} not authorized to delete meeting {meeting_session.id}"
                )
                return False

            # Ensure user has valid credentials
            if not self.refresh_user_credentials(user):
                raise Exception("Invalid or missing Google credentials")

            google_creds = GoogleMeetCredentials.objects.get(user=user)
            credentials = Credentials(
                token=google_creds.access_token,
                refresh_token=google_creds.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=self.scopes,
            )

            # Build Calendar API service
            service = build("calendar", "v3", credentials=credentials)

            # Delete the calendar event
            if meeting_session.google_calendar_event_id:
                service.events().delete(
                    calendarId="primary",
                    eventId=meeting_session.google_calendar_event_id,
                    sendUpdates="all",
                ).execute()

            # Update meeting status to cancelled
            self.update_meeting_status(
                meeting_session, MeetingSession.Status.CANCELLED, user
            )

            logger.info(
                f"Successfully deleted Google Meet meeting: {meeting_session.id}"
            )
            return True

        except Exception as e:
            logger.error(f"Error deleting Google Meet meeting: {str(e)}")
            return False
