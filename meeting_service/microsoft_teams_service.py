import logging
from datetime import datetime, timedelta
from typing import List, Optional

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from msal import ConfidentialClientApplication

from .models import (
    MeetingParticipant,
    MeetingSession,
    MeetingStatusUpdate,
    MicrosoftTeamsCredentials,
)

User = get_user_model()
logger = logging.getLogger(__name__)


class MicrosoftTeamsService:
    """Service for managing Microsoft Teams integration"""

    def __init__(self):
        # These would typically come from Django settings
        self.client_id = getattr(settings, "MICROSOFT_CLIENT_ID", "")
        self.client_secret = getattr(settings, "MICROSOFT_CLIENT_SECRET", "")
        self.tenant_id = getattr(settings, "MICROSOFT_TENANT_ID", "common")
        self.redirect_uri = getattr(
            settings,
            "MICROSOFT_REDIRECT_URI",
            "http://localhost:8000/api/meetings/teams/callback/",
        )
        self.scopes = getattr(
            settings,
            "MICROSOFT_SCOPES",
            [
                "https://graph.microsoft.com/OnlineMeetings.ReadWrite",
                "https://graph.microsoft.com/Calendars.ReadWrite",
                "https://graph.microsoft.com/User.Read",
                "https://graph.microsoft.com/Team.ReadBasic.All",
                "https://graph.microsoft.com/Channel.ReadBasic.All",
            ],
        )

        # Initialize MSAL app
        self.msal_app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
        )

    def get_authorization_url(self, user_id: str) -> str:
        """Generate OAuth authorization URL for Microsoft Teams"""
        try:
            auth_url = self.msal_app.get_authorization_request_url(
                scopes=self.scopes,
                redirect_uri=self.redirect_uri,
                state=user_id,  # Pass user_id as state parameter
            )

            logger.info(
                f"Generated Microsoft Teams authorization URL for user {user_id}"
            )
            return auth_url

        except Exception as e:
            logger.error(
                f"Error generating Microsoft Teams authorization URL: {str(e)}"
            )
            raise

    def handle_oauth_callback(self, authorization_code: str, state: str) -> bool:
        """Handle OAuth callback and store credentials"""
        try:
            user_id = state
            user = User.objects.get(id=user_id)

            # Exchange authorization code for tokens
            result = self.msal_app.acquire_token_by_authorization_code(
                code=authorization_code,
                scopes=self.scopes,
                redirect_uri=self.redirect_uri,
            )

            if "error" in result:
                logger.error(
                    f"Error in OAuth callback: {result.get('error_description', result['error'])}"
                )
                return False

            # Calculate token expiry
            expires_in = result.get("expires_in", 3600)
            token_expiry = timezone.now() + timedelta(seconds=expires_in)

            # Store or update credentials
            teams_creds, created = MicrosoftTeamsCredentials.objects.get_or_create(
                user=user,
                defaults={
                    "access_token": result["access_token"],
                    "refresh_token": result.get("refresh_token", ""),
                    "token_expiry": token_expiry,
                    "scope": " ".join(self.scopes),
                    "tenant_id": self.tenant_id,
                },
            )

            if not created:
                # Update existing credentials
                teams_creds.access_token = result["access_token"]
                teams_creds.refresh_token = result.get(
                    "refresh_token", teams_creds.refresh_token
                )
                teams_creds.token_expiry = token_expiry
                teams_creds.scope = " ".join(self.scopes)
                teams_creds.save()

            logger.info(
                f"Successfully stored Microsoft Teams credentials for user {user_id}"
            )
            return True

        except User.DoesNotExist:
            logger.error(f"User with ID {user_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error handling Microsoft Teams OAuth callback: {str(e)}")
            return False

    def refresh_user_credentials(self, user: User) -> bool:
        """Refresh user's Microsoft Teams credentials if needed"""
        try:
            teams_creds = MicrosoftTeamsCredentials.objects.get(user=user)

            if teams_creds.is_token_expired():
                # Refresh the token using MSAL
                result = self.msal_app.acquire_token_silent(
                    scopes=self.scopes, account=None  # MSAL will find the account
                )

                if not result or "error" in result:
                    # Try refresh token if silent acquisition fails
                    if teams_creds.refresh_token:
                        result = self.msal_app.acquire_token_by_refresh_token(
                            refresh_token=teams_creds.refresh_token, scopes=self.scopes
                        )

                if result and "access_token" in result:
                    # Update stored credentials
                    expires_in = result.get("expires_in", 3600)
                    teams_creds.access_token = result["access_token"]
                    teams_creds.token_expiry = timezone.now() + timedelta(
                        seconds=expires_in
                    )
                    if "refresh_token" in result:
                        teams_creds.refresh_token = result["refresh_token"]
                    teams_creds.save()

                    logger.info(
                        f"Refreshed Microsoft Teams credentials for user {user.id}"
                    )
                    return True
                else:
                    logger.error(
                        f"Failed to refresh Microsoft Teams credentials for user {user.id}"
                    )
                    return False

            return True

        except MicrosoftTeamsCredentials.DoesNotExist:
            logger.error(f"No Microsoft Teams credentials found for user {user.id}")
            return False
        except Exception as e:
            logger.error(f"Error refreshing Microsoft Teams credentials: {str(e)}")
            return False

    def _make_graph_request(
        self, user: User, method: str, endpoint: str, data: dict = None
    ) -> Optional[dict]:
        """Make authenticated request to Microsoft Graph API"""
        try:
            if not self.refresh_user_credentials(user):
                raise Exception("Invalid or missing Microsoft Teams credentials")

            teams_creds = MicrosoftTeamsCredentials.objects.get(user=user)

            headers = {
                "Authorization": f"Bearer {teams_creds.access_token}",
                "Content-Type": "application/json",
            }

            url = f"https://graph.microsoft.com/v1.0{endpoint}"

            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            if response.status_code in [200, 201, 202, 204]:
                return response.json() if response.content else {}
            else:
                logger.error(
                    f"Graph API request failed: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Error making Graph API request: {str(e)}")
            return None

    def create_meeting(
        self,
        user: User,
        title: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
        attendee_emails: List[str] = None,
    ) -> Optional[MeetingSession]:
        """Create a Microsoft Teams meeting"""
        try:
            # Prepare meeting data for Microsoft Graph API
            meeting_data = {
                "subject": title,
                "body": {"contentType": "HTML", "content": description or ""},
                "start": {"dateTime": start_time.isoformat(), "timeZone": "UTC"},
                "end": {"dateTime": end_time.isoformat(), "timeZone": "UTC"},
                "isOnlineMeeting": True,
                "onlineMeetingProvider": "teamsForBusiness",
            }

            # Add attendees if provided
            if attendee_emails:
                meeting_data["attendees"] = [
                    {
                        "emailAddress": {"address": email, "name": email.split("@")[0]},
                        "type": "required",
                    }
                    for email in attendee_emails
                ]

            # Create the meeting via Graph API
            result = self._make_graph_request(user, "POST", "/me/events", meeting_data)

            if not result:
                logger.error("Failed to create Teams meeting via Graph API")
                return None

            # Extract Teams meeting details
            teams_meeting_url = ""
            teams_join_url = ""
            teams_conference_id = ""

            if "onlineMeeting" in result:
                online_meeting = result["onlineMeeting"]
                teams_meeting_url = online_meeting.get("joinUrl", "")
                teams_join_url = online_meeting.get("joinUrl", "")
                teams_conference_id = online_meeting.get("conferenceId", "")

            # Create MeetingSession record
            meeting_session = MeetingSession.objects.create(
                organizer=user,
                title=title,
                description=description,
                meeting_type=MeetingSession.MeetingType.MICROSOFT_TEAMS,
                teams_meeting_url=teams_meeting_url,
                teams_meeting_id=result.get("id", ""),
                teams_join_url=teams_join_url,
                teams_conference_id=teams_conference_id,
                teams_organizer_id=result.get("organizer", {})
                .get("emailAddress", {})
                .get("address", ""),
                scheduled_start_time=start_time,
                scheduled_end_time=end_time,
                status=MeetingSession.Status.SCHEDULED,
            )

            # Create participant records
            if attendee_emails:
                for email in attendee_emails:
                    MeetingParticipant.objects.create(
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
                description=f"Meeting '{title}' created with Microsoft Teams",
                triggered_by=user,
                metadata={
                    "teams_meeting_id": result.get("id", ""),
                    "teams_join_url": teams_join_url,
                    "attendee_count": len(attendee_emails) if attendee_emails else 0,
                },
            )

            logger.info(
                f"Successfully created Microsoft Teams meeting: {meeting_session.id}"
            )
            return meeting_session

        except Exception as e:
            logger.error(f"Error creating Microsoft Teams meeting: {str(e)}")
            return None

    def get_user_teams(self, user: User) -> List[dict]:
        """Get Teams that the user is a member of"""
        try:
            result = self._make_graph_request(user, "GET", "/me/joinedTeams")

            if result and "value" in result:
                return result["value"]

            return []

        except Exception as e:
            logger.error(f"Error getting user teams: {str(e)}")
            return []

    def get_team_channels(self, user: User, team_id: str) -> List[dict]:
        """Get channels for a specific team"""
        try:
            result = self._make_graph_request(user, "GET", f"/teams/{team_id}/channels")

            if result and "value" in result:
                return result["value"]

            return []

        except Exception as e:
            logger.error(f"Error getting team channels: {str(e)}")
            return []

    def send_channel_message(
        self, user: User, team_id: str, channel_id: str, message: str
    ) -> bool:
        """Send a message to a Teams channel"""
        try:
            message_data = {"body": {"contentType": "html", "content": message}}

            result = self._make_graph_request(
                user,
                "POST",
                f"/teams/{team_id}/channels/{channel_id}/messages",
                message_data,
            )

            return result is not None

        except Exception as e:
            logger.error(f"Error sending channel message: {str(e)}")
            return False

    def get_meeting_recordings(self, user: User, meeting_id: str) -> List[dict]:
        """Get recordings for a specific meeting"""
        try:
            # Get recordings from Microsoft Graph API
            # First try to get recordings from the online meeting
            result = self._make_graph_request(
                user, "GET", f"/me/onlineMeetings/{meeting_id}/recordings"
            )

            recordings = []
            if result and "value" in result:
                recordings.extend(result["value"])

            # Also check for recordings in OneDrive/SharePoint
            # Teams recordings are often stored in the organizer's OneDrive
            drive_result = self._make_graph_request(
                user, "GET", f"/me/drive/root/search(q='{meeting_id}')"
            )

            if drive_result and "value" in drive_result:
                for item in drive_result["value"]:
                    if item.get("file", {}).get("mimeType", "").startswith("video/"):
                        recordings.append(
                            {
                                "id": item["id"],
                                "name": item["name"],
                                "webUrl": item["webUrl"],
                                "downloadUrl": item.get(
                                    "@microsoft.graph.downloadUrl", ""
                                ),
                                "createdDateTime": item["createdDateTime"],
                                "size": item.get("size", 0),
                                "mimeType": item.get("file", {}).get("mimeType", ""),
                                "source": "onedrive",
                            }
                        )

            logger.info(
                f"Found {len(recordings)} recordings for Teams meeting {meeting_id}"
            )
            return recordings

        except Exception as e:
            logger.error(f"Error getting Teams meeting recordings: {str(e)}")
            return []

    def get_meeting_transcripts(self, user: User, meeting_id: str) -> List[dict]:
        """Get transcripts for a specific meeting"""
        try:
            # Get transcripts from Microsoft Graph API
            result = self._make_graph_request(
                user, "GET", f"/me/onlineMeetings/{meeting_id}/transcripts"
            )

            transcripts = []
            if result and "value" in result:
                for transcript in result["value"]:
                    # Get transcript content
                    content_result = self._make_graph_request(
                        user,
                        "GET",
                        f'/me/onlineMeetings/{meeting_id}/transcripts/{transcript["id"]}/content',
                    )

                    transcript_data = {
                        "id": transcript["id"],
                        "createdDateTime": transcript["createdDateTime"],
                        "meetingId": transcript.get("meetingId", meeting_id),
                        "content": content_result if content_result else "",
                        "source": "teams_api",
                    }
                    transcripts.append(transcript_data)

            # Also search for transcript files in OneDrive/SharePoint
            drive_result = self._make_graph_request(
                user, "GET", f"/me/drive/root/search(q='transcript {meeting_id}')"
            )

            if drive_result and "value" in drive_result:
                for item in drive_result["value"]:
                    if (
                        item["name"].lower().endswith(".vtt")
                        or item["name"].lower().endswith(".txt")
                        or "transcript" in item["name"].lower()
                    ):

                        # Get file content
                        content = ""
                        try:
                            content_result = self._make_graph_request(
                                user, "GET", f"/me/drive/items/{item['id']}/content"
                            )
                            if content_result:
                                content = str(content_result)
                        except Exception as e:
                            logger.warning(
                                f"Could not get content for transcript file {item['id']}: {str(e)}"
                            )

                        transcripts.append(
                            {
                                "id": item["id"],
                                "name": item["name"],
                                "webUrl": item["webUrl"],
                                "createdDateTime": item["createdDateTime"],
                                "content": content,
                                "source": "onedrive",
                            }
                        )

            logger.info(
                f"Found {len(transcripts)} transcripts for Teams meeting {meeting_id}"
            )
            return transcripts

        except Exception as e:
            logger.error(f"Error getting Teams meeting transcripts: {str(e)}")
            return []

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
                description=f"Teams meeting status changed from {old_status} to {new_status}",
                triggered_by=user,
                metadata={"old_status": old_status, "new_status": new_status},
            )

            logger.info(
                f"Updated Teams meeting {meeting_session.id} status to {new_status}"
            )
            return True

        except Exception as e:
            logger.error(f"Error updating Teams meeting status: {str(e)}")
            return False

    def delete_meeting(self, meeting_session: MeetingSession, user: User) -> bool:
        """Delete a Microsoft Teams meeting"""
        try:
            # Only organizer can delete
            if meeting_session.organizer != user:
                logger.error(
                    f"User {user.id} not authorized to delete meeting {meeting_session.id}"
                )
                return False

            # Delete the meeting via Graph API
            if meeting_session.teams_meeting_id:
                result = self._make_graph_request(
                    user, "DELETE", f"/me/events/{meeting_session.teams_meeting_id}"
                )

                if result is None:
                    logger.warning(
                        f"Failed to delete Teams meeting via API, but updating local status"
                    )

            # Update meeting status to cancelled
            self.update_meeting_status(
                meeting_session, MeetingSession.Status.CANCELLED, user
            )

            logger.info(
                f"Successfully deleted Microsoft Teams meeting: {meeting_session.id}"
            )
            return True

        except Exception as e:
            logger.error(f"Error deleting Microsoft Teams meeting: {str(e)}")
            return False

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
        """Create a Microsoft Teams meeting with a structured agenda"""
        try:
            # Build agenda content
            agenda_content = description or ""
            if agenda_items:
                agenda_content += "<br><br><strong>📋 Meeting Agenda:</strong><br><ol>"
                for item in agenda_items:
                    agenda_content += f"<li>{item}</li>"
                agenda_content += "</ol>"

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

                logger.info(f"Created Teams meeting with agenda: {meeting_session.id}")

            return meeting_session

        except Exception as e:
            logger.error(f"Error creating Teams meeting with agenda: {str(e)}")
            return None

    def generate_meeting_link(self, meeting_session: MeetingSession) -> Optional[str]:
        """Generate or retrieve the meeting link for sharing"""
        try:
            if meeting_session.teams_join_url:
                return meeting_session.teams_join_url
            elif meeting_session.teams_meeting_url:
                return meeting_session.teams_meeting_url

            # If no URL is stored, try to retrieve it from Microsoft Graph
            if meeting_session.teams_meeting_id:
                user = meeting_session.organizer

                result = self._make_graph_request(
                    user, "GET", f"/me/events/{meeting_session.teams_meeting_id}"
                )

                if result and "onlineMeeting" in result:
                    online_meeting = result["onlineMeeting"]
                    meeting_url = online_meeting.get("joinUrl", "")

                    if meeting_url:
                        # Update the meeting session with the URL
                        meeting_session.teams_join_url = meeting_url
                        meeting_session.teams_meeting_url = meeting_url
                        meeting_session.save()

                        return meeting_url

            logger.warning(
                f"No Teams meeting URL found for meeting {meeting_session.id}"
            )
            return None

        except Exception as e:
            logger.error(f"Error generating Teams meeting link: {str(e)}")
            return None

    def share_meeting_link(
        self,
        meeting_session: MeetingSession,
        recipient_emails: List[str],
        custom_message: str = None,
    ) -> bool:
        """Share meeting link via email using Microsoft Graph"""
        try:
            meeting_url = self.generate_meeting_link(meeting_session)
            if not meeting_url:
                logger.error(
                    f"No meeting URL available for sharing: {meeting_session.id}"
                )
                return False

            user = meeting_session.organizer

            # Prepare email content
            subject = f"Meeting Invitation: {meeting_session.title}"

            body_content = (
                custom_message
                or f"""
<p>You're invited to join our meeting:</p>

<p><strong>📅 Meeting:</strong> {meeting_session.title}<br>
<strong>🕐 Time:</strong> {meeting_session.scheduled_start_time.strftime('%Y-%m-%d %H:%M UTC')}<br>
<strong>⏱️ Duration:</strong> {meeting_session.duration_minutes} minutes</p>

<p><strong>🔗 <a href="{meeting_url}">Join the meeting</a></strong></p>

<p>{meeting_session.description or ''}</p>

<p>Best regards,<br>
{user.get_full_name() or user.email}</p>
            """
            )

            # Send email to each recipient
            success_count = 0
            for email in recipient_emails:
                try:
                    email_data = {
                        "message": {
                            "subject": subject,
                            "body": {"contentType": "HTML", "content": body_content},
                            "toRecipients": [{"emailAddress": {"address": email}}],
                        },
                        "saveToSentItems": "true",
                    }

                    result = self._make_graph_request(
                        user, "POST", "/me/sendMail", email_data
                    )

                    if result is not None:
                        success_count += 1
                        logger.info(f"Sent Teams meeting link to {email}")
                    else:
                        logger.error(f"Failed to send Teams meeting link to {email}")

                except Exception as e:
                    logger.error(
                        f"Failed to send Teams meeting link to {email}: {str(e)}"
                    )

            logger.info(
                f"Successfully shared Teams meeting link to {success_count}/{len(recipient_emails)} recipients"
            )
            return success_count > 0

        except Exception as e:
            logger.error(f"Error sharing Teams meeting link: {str(e)}")
            return False

    def enable_meeting_recording(
        self, meeting_session: MeetingSession, user: User
    ) -> bool:
        """Enable recording for a Teams meeting"""
        try:
            if meeting_session.teams_meeting_id:
                # Update meeting to enable recording
                meeting_data = {"allowRecording": True, "recordAutomatically": True}

                result = self._make_graph_request(
                    user,
                    "PATCH",
                    f"/me/events/{meeting_session.teams_meeting_id}",
                    meeting_data,
                )

                if result:
                    meeting_session.recording_enabled = True
                    meeting_session.save()

                    logger.info(
                        f"Enabled recording for Teams meeting {meeting_session.id}"
                    )
                    return True

            return False

        except Exception as e:
            logger.error(f"Error enabling Teams meeting recording: {str(e)}")
            return False

    def get_user_meetings(self, user: User, status: str = None) -> List[MeetingSession]:
        """Get Teams meetings for a user, optionally filtered by status"""
        try:
            queryset = MeetingSession.objects.filter(
                models.Q(organizer=user) | models.Q(participants__user=user),
                meeting_type=MeetingSession.MeetingType.MICROSOFT_TEAMS,
            ).distinct()

            if status:
                queryset = queryset.filter(status=status)

            return list(queryset.order_by("-scheduled_start_time"))

        except Exception as e:
            logger.error(f"Error getting user Teams meetings: {str(e)}")
            return []
