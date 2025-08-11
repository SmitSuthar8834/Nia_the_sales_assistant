"""
Calendar Integration Service for NIA Sales Assistant

This service provides unified calendar integration for Google Calendar and Outlook,
including automatic meeting scheduling, conflict detection, and reminder management.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Microsoft Graph API imports
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from msal import ConfidentialClientApplication

from ai_service.models import Lead
from credentials import get_google_meet_credentials

from .models import GoogleMeetCredentials, Meeting, MicrosoftTeamsCredentials

User = get_user_model()
logger = logging.getLogger(__name__)


class CalendarConflict:
    """Represents a calendar conflict"""

    def __init__(
        self,
        event_id: str,
        title: str,
        start_time: datetime,
        end_time: datetime,
        calendar_type: str,
    ):
        self.event_id = event_id
        self.title = title
        self.start_time = start_time
        self.end_time = end_time
        self.calendar_type = calendar_type

    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "title": self.title,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "calendar_type": self.calendar_type,
        }


class CalendarIntegrationService:
    """Unified calendar integration service for Google Calendar and Outlook"""

    def __init__(self):
        # Google Calendar configuration
        google_creds = get_google_meet_credentials()
        self.google_client_id = google_creds["client_id"]
        self.google_client_secret = google_creds["client_secret"]
        self.google_redirect_uri = settings.GOOGLE_MEET_REDIRECT_URI
        self.google_scopes = settings.GOOGLE_MEET_SCOPES

        # Microsoft Graph configuration
        self.microsoft_client_id = getattr(settings, "MICROSOFT_CLIENT_ID", "")
        self.microsoft_client_secret = getattr(settings, "MICROSOFT_CLIENT_SECRET", "")
        self.microsoft_tenant_id = getattr(settings, "MICROSOFT_TENANT_ID", "common")
        self.microsoft_redirect_uri = getattr(
            settings,
            "MICROSOFT_REDIRECT_URI",
            "http://localhost:8000/meeting/oauth/outlook/callback/",
        )
        self.microsoft_scopes = [
            "https://graph.microsoft.com/Calendars.ReadWrite",
            "https://graph.microsoft.com/User.Read",
            "https://graph.microsoft.com/Mail.Send",
        ]

    # Google Calendar Integration

    def get_google_authorization_url(self, user_id: str) -> str:
        """Generate OAuth authorization URL for Google Calendar"""
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.google_client_id,
                        "client_secret": self.google_client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.google_redirect_uri],
                    }
                },
                scopes=self.google_scopes,
            )
            flow.redirect_uri = self.google_redirect_uri

            authorization_url, state = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                state=f"google_{user_id}",
                prompt="consent",  # Force consent to get refresh token
            )

            logger.info(
                f"Generated Google Calendar authorization URL for user {user_id}"
            )
            return authorization_url

        except Exception as e:
            logger.error(f"Error generating Google authorization URL: {str(e)}")
            raise

    def get_outlook_authorization_url(self, user_id: str) -> str:
        """Generate OAuth authorization URL for Outlook Calendar"""
        try:
            app = ConfidentialClientApplication(
                self.microsoft_client_id,
                authority=f"https://login.microsoftonline.com/{self.microsoft_tenant_id}",
                client_credential=self.microsoft_client_secret,
            )

            auth_url = app.get_authorization_request_url(
                scopes=self.microsoft_scopes,
                state=f"outlook_{user_id}",
                redirect_uri=self.microsoft_redirect_uri,
            )

            logger.info(
                f"Generated Outlook Calendar authorization URL for user {user_id}"
            )
            return auth_url

        except Exception as e:
            logger.error(f"Error generating Outlook authorization URL: {str(e)}")
            raise

    def handle_google_oauth_callback(self, authorization_code: str, state: str) -> bool:
        """Handle Google OAuth callback and store credentials"""
        try:
            # Extract user_id from state
            if not state.startswith("google_"):
                raise ValueError("Invalid state parameter for Google OAuth")

            user_id = state.replace("google_", "")
            user = User.objects.get(id=user_id)

            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.google_client_id,
                        "client_secret": self.google_client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.google_redirect_uri],
                    }
                },
                scopes=self.google_scopes,
            )
            flow.redirect_uri = self.google_redirect_uri

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
                    "scope": " ".join(self.google_scopes),
                },
            )

            if not created:
                google_creds.access_token = credentials.token
                if (
                    credentials.refresh_token
                ):  # Only update if we got a new refresh token
                    google_creds.refresh_token = credentials.refresh_token
                google_creds.token_expiry = credentials.expiry
                google_creds.scope = " ".join(self.google_scopes)
                google_creds.save()

            logger.info(
                f"Successfully stored Google Calendar credentials for user {user_id}"
            )
            return True

        except User.DoesNotExist:
            logger.error(f"User with ID {user_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error handling Google OAuth callback: {str(e)}")
            return False

    def handle_outlook_oauth_callback(
        self, authorization_code: str, state: str
    ) -> bool:
        """Handle Outlook OAuth callback and store credentials"""
        try:
            # Extract user_id from state
            if not state.startswith("outlook_"):
                raise ValueError("Invalid state parameter for Outlook OAuth")

            user_id = state.replace("outlook_", "")
            user = User.objects.get(id=user_id)

            app = ConfidentialClientApplication(
                self.microsoft_client_id,
                authority=f"https://login.microsoftonline.com/{self.microsoft_tenant_id}",
                client_credential=self.microsoft_client_secret,
            )

            # Exchange authorization code for tokens
            result = app.acquire_token_by_authorization_code(
                authorization_code,
                scopes=self.microsoft_scopes,
                redirect_uri=self.microsoft_redirect_uri,
            )

            if "access_token" not in result:
                raise Exception(
                    f"Failed to acquire token: {result.get('error_description', 'Unknown error')}"
                )

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
                    "scope": " ".join(self.microsoft_scopes),
                    "tenant_id": self.microsoft_tenant_id,
                },
            )

            if not created:
                teams_creds.access_token = result["access_token"]
                if result.get("refresh_token"):
                    teams_creds.refresh_token = result["refresh_token"]
                teams_creds.token_expiry = token_expiry
                teams_creds.scope = " ".join(self.microsoft_scopes)
                teams_creds.save()

            logger.info(
                f"Successfully stored Outlook Calendar credentials for user {user_id}"
            )
            return True

        except User.DoesNotExist:
            logger.error(f"User with ID {user_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error handling Outlook OAuth callback: {str(e)}")
            return False

    def refresh_google_credentials(self, user: User) -> bool:
        """Refresh user's Google credentials if needed"""
        try:
            google_creds = GoogleMeetCredentials.objects.get(user=user)

            if google_creds.is_token_expired():
                credentials = Credentials(
                    token=google_creds.access_token,
                    refresh_token=google_creds.refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=self.google_client_id,
                    client_secret=self.google_client_secret,
                    scopes=self.google_scopes,
                )

                # Refresh the token
                credentials.refresh(Request())

                # Update stored credentials
                google_creds.access_token = credentials.token
                google_creds.token_expiry = credentials.expiry
                google_creds.save()

                logger.info(f"Refreshed Google credentials for user {user.id}")

            return True

        except GoogleMeetCredentials.DoesNotExist:
            logger.error(f"No Google Calendar credentials found for user {user.id}")
            return False
        except Exception as e:
            logger.error(f"Error refreshing Google credentials: {str(e)}")
            return False

    def refresh_outlook_credentials(self, user: User) -> bool:
        """Refresh user's Outlook credentials if needed"""
        try:
            teams_creds = MicrosoftTeamsCredentials.objects.get(user=user)

            if teams_creds.is_token_expired() and teams_creds.refresh_token:
                app = ConfidentialClientApplication(
                    self.microsoft_client_id,
                    authority=f"https://login.microsoftonline.com/{self.microsoft_tenant_id}",
                    client_credential=self.microsoft_client_secret,
                )

                result = app.acquire_token_by_refresh_token(
                    teams_creds.refresh_token, scopes=self.microsoft_scopes
                )

                if "access_token" in result:
                    expires_in = result.get("expires_in", 3600)
                    token_expiry = timezone.now() + timedelta(seconds=expires_in)

                    teams_creds.access_token = result["access_token"]
                    teams_creds.token_expiry = token_expiry
                    if result.get("refresh_token"):
                        teams_creds.refresh_token = result["refresh_token"]
                    teams_creds.save()

                    logger.info(f"Refreshed Outlook credentials for user {user.id}")
                    return True
                else:
                    logger.error(
                        f"Failed to refresh Outlook token: {result.get('error_description', 'Unknown error')}"
                    )
                    return False

            return True

        except MicrosoftTeamsCredentials.DoesNotExist:
            logger.error(f"No Outlook Calendar credentials found for user {user.id}")
            return False
        except Exception as e:
            logger.error(f"Error refreshing Outlook credentials: {str(e)}")
            return False

    # Calendar Event Management

    def get_google_calendar_events(
        self, user: User, start_time: datetime, end_time: datetime
    ) -> List[Dict]:
        """Get Google Calendar events for a time range"""
        try:
            if not self.refresh_google_credentials(user):
                return []

            google_creds = GoogleMeetCredentials.objects.get(user=user)
            credentials = Credentials(
                token=google_creds.access_token,
                refresh_token=google_creds.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.google_client_id,
                client_secret=self.google_client_secret,
                scopes=self.google_scopes,
            )

            service = build("calendar", "v3", credentials=credentials)

            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=start_time.isoformat() + "Z",
                    timeMax=end_time.isoformat() + "Z",
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])

            calendar_events = []
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                end = event["end"].get("dateTime", event["end"].get("date"))

                # Parse datetime strings
                if "T" in start:
                    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                else:
                    # All-day event
                    start_dt = datetime.fromisoformat(start + "T00:00:00+00:00")
                    end_dt = datetime.fromisoformat(end + "T23:59:59+00:00")

                calendar_events.append(
                    {
                        "id": event["id"],
                        "title": event.get("summary", "No Title"),
                        "start_time": start_dt,
                        "end_time": end_dt,
                        "calendar_type": "google",
                        "description": event.get("description", ""),
                        "attendees": [
                            att.get("email", "") for att in event.get("attendees", [])
                        ],
                        "location": event.get("location", ""),
                        "status": event.get("status", "confirmed"),
                    }
                )

            logger.info(
                f"Retrieved {len(calendar_events)} Google Calendar events for user {user.id}"
            )
            return calendar_events

        except Exception as e:
            logger.error(f"Error getting Google Calendar events: {str(e)}")
            return []

    def get_outlook_calendar_events(
        self, user: User, start_time: datetime, end_time: datetime
    ) -> List[Dict]:
        """Get Outlook Calendar events for a time range"""
        try:
            if not self.refresh_outlook_credentials(user):
                return []

            teams_creds = MicrosoftTeamsCredentials.objects.get(user=user)

            headers = {
                "Authorization": f"Bearer {teams_creds.access_token}",
                "Content-Type": "application/json",
            }

            # Format times for Microsoft Graph API
            start_str = start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            end_str = end_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

            url = f"https://graph.microsoft.com/v1.0/me/calendar/calendarView"
            params = {
                "startDateTime": start_str,
                "endDateTime": end_str,
                "$orderby": "start/dateTime",
            }

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            events_data = response.json()
            events = events_data.get("value", [])

            calendar_events = []
            for event in events:
                start_dt = datetime.fromisoformat(
                    event["start"]["dateTime"].replace("Z", "+00:00")
                )
                end_dt = datetime.fromisoformat(
                    event["end"]["dateTime"].replace("Z", "+00:00")
                )

                calendar_events.append(
                    {
                        "id": event["id"],
                        "title": event.get("subject", "No Title"),
                        "start_time": start_dt,
                        "end_time": end_dt,
                        "calendar_type": "outlook",
                        "description": event.get("body", {}).get("content", ""),
                        "attendees": [
                            att.get("emailAddress", {}).get("address", "")
                            for att in event.get("attendees", [])
                        ],
                        "location": event.get("location", {}).get("displayName", ""),
                        "status": event.get("showAs", "busy"),
                    }
                )

            logger.info(
                f"Retrieved {len(calendar_events)} Outlook Calendar events for user {user.id}"
            )
            return calendar_events

        except Exception as e:
            logger.error(f"Error getting Outlook Calendar events: {str(e)}")
            return []

    def get_all_calendar_events(
        self, user: User, start_time: datetime, end_time: datetime
    ) -> List[Dict]:
        """Get events from all connected calendars"""
        all_events = []

        # Get Google Calendar events
        google_events = self.get_google_calendar_events(user, start_time, end_time)
        all_events.extend(google_events)

        # Get Outlook Calendar events
        outlook_events = self.get_outlook_calendar_events(user, start_time, end_time)
        all_events.extend(outlook_events)

        # Sort by start time
        all_events.sort(key=lambda x: x["start_time"])

        return all_events

    # Conflict Detection

    def detect_calendar_conflicts(
        self,
        user: User,
        proposed_start: datetime,
        proposed_end: datetime,
        exclude_event_ids: List[str] = None,
    ) -> List[CalendarConflict]:
        """Detect conflicts with existing calendar events"""
        try:
            exclude_event_ids = exclude_event_ids or []
            conflicts = []

            # Get events in the proposed time range (with some buffer)
            buffer_time = timedelta(minutes=15)
            search_start = proposed_start - buffer_time
            search_end = proposed_end + buffer_time

            existing_events = self.get_all_calendar_events(
                user, search_start, search_end
            )

            for event in existing_events:
                # Skip excluded events
                if event["id"] in exclude_event_ids:
                    continue

                # Check for time overlap
                if (
                    event["start_time"] < proposed_end
                    and event["end_time"] > proposed_start
                ):

                    conflict = CalendarConflict(
                        event_id=event["id"],
                        title=event["title"],
                        start_time=event["start_time"],
                        end_time=event["end_time"],
                        calendar_type=event["calendar_type"],
                    )
                    conflicts.append(conflict)

            logger.info(f"Found {len(conflicts)} calendar conflicts for user {user.id}")
            return conflicts

        except Exception as e:
            logger.error(f"Error detecting calendar conflicts: {str(e)}")
            return []

    def find_available_time_slots(
        self,
        user: User,
        duration_minutes: int,
        start_date: datetime,
        end_date: datetime,
        working_hours: Tuple[int, int] = (9, 17),
        exclude_weekends: bool = True,
    ) -> List[Dict]:
        """Find available time slots for scheduling meetings"""
        try:
            available_slots = []

            # Get all existing events in the date range
            existing_events = self.get_all_calendar_events(user, start_date, end_date)

            # Generate potential time slots
            current_date = start_date.date()
            end_date_only = end_date.date()

            while current_date <= end_date_only:
                # Skip weekends if requested
                if exclude_weekends and current_date.weekday() >= 5:
                    current_date += timedelta(days=1)
                    continue

                # Check each hour within working hours
                for hour in range(working_hours[0], working_hours[1]):
                    slot_start = datetime.combine(
                        current_date, datetime.min.time().replace(hour=hour)
                    )
                    slot_start = timezone.make_aware(slot_start)
                    slot_end = slot_start + timedelta(minutes=duration_minutes)

                    # Check if this slot conflicts with existing events
                    conflicts = self.detect_calendar_conflicts(
                        user, slot_start, slot_end
                    )

                    if not conflicts:
                        available_slots.append(
                            {
                                "start_time": slot_start,
                                "end_time": slot_end,
                                "duration_minutes": duration_minutes,
                                "confidence_score": self._calculate_slot_confidence(
                                    slot_start, existing_events, user
                                ),
                            }
                        )

                current_date += timedelta(days=1)

            # Sort by confidence score (best slots first)
            available_slots.sort(key=lambda x: x["confidence_score"], reverse=True)

            logger.info(
                f"Found {len(available_slots)} available time slots for user {user.id}"
            )
            return available_slots[:20]  # Return top 20 slots

        except Exception as e:
            logger.error(f"Error finding available time slots: {str(e)}")
            return []

    def _calculate_slot_confidence(
        self, slot_start: datetime, existing_events: List[Dict], user: User
    ) -> float:
        """Calculate confidence score for a time slot based on user patterns"""
        confidence = 100.0

        # Prefer mid-morning and early afternoon slots
        hour = slot_start.hour
        if 10 <= hour <= 11 or 14 <= hour <= 15:
            confidence += 20
        elif hour == 9 or hour == 16:
            confidence += 10
        elif hour < 9 or hour > 16:
            confidence -= 20

        # Check proximity to other meetings (prefer some buffer time)
        for event in existing_events:
            time_diff = abs((event["start_time"] - slot_start).total_seconds() / 60)
            if time_diff < 30:  # Less than 30 minutes
                confidence -= 30
            elif time_diff < 60:  # Less than 1 hour
                confidence -= 15

        # Prefer Tuesday-Thursday
        weekday = slot_start.weekday()
        if 1 <= weekday <= 3:  # Tuesday to Thursday
            confidence += 10
        elif weekday == 0 or weekday == 4:  # Monday or Friday
            confidence -= 5

        return max(0, min(100, confidence))

    # Meeting Scheduling

    def schedule_meeting_with_conflict_resolution(
        self, user: User, lead: Lead, meeting_data: Dict
    ) -> Tuple[bool, Dict]:
        """Schedule a meeting with automatic conflict resolution"""
        try:
            title = meeting_data.get("title", f"Meeting with {lead.company_name}")
            description = meeting_data.get("description", "")
            duration_minutes = meeting_data.get("duration_minutes", 60)
            preferred_start = meeting_data.get("preferred_start_time")
            attendee_emails = meeting_data.get("attendee_emails", [])

            if preferred_start:
                preferred_start = (
                    datetime.fromisoformat(preferred_start)
                    if isinstance(preferred_start, str)
                    else preferred_start
                )
                preferred_end = preferred_start + timedelta(minutes=duration_minutes)

                # Check for conflicts
                conflicts = self.detect_calendar_conflicts(
                    user, preferred_start, preferred_end
                )

                if not conflicts:
                    # No conflicts, schedule at preferred time
                    return self._create_calendar_meeting(
                        user,
                        title,
                        description,
                        preferred_start,
                        preferred_end,
                        attendee_emails,
                        lead,
                    )
                else:
                    # Find alternative times
                    search_start = preferred_start
                    search_end = preferred_start + timedelta(
                        days=7
                    )  # Search within a week

                    available_slots = self.find_available_time_slots(
                        user, duration_minutes, search_start, search_end
                    )

                    if available_slots:
                        best_slot = available_slots[0]
                        return self._create_calendar_meeting(
                            user,
                            title,
                            description,
                            best_slot["start_time"],
                            best_slot["end_time"],
                            attendee_emails,
                            lead,
                            alternative_time=True,
                            original_conflicts=conflicts,
                        )
                    else:
                        return False, {
                            "error": "No available time slots found",
                            "conflicts": [c.to_dict() for c in conflicts],
                            "suggested_action": "Please choose a different time or date range",
                        }
            else:
                # No preferred time, find best available slot
                search_start = timezone.now() + timedelta(
                    hours=1
                )  # Start from 1 hour from now
                search_end = search_start + timedelta(days=14)  # Search within 2 weeks

                available_slots = self.find_available_time_slots(
                    user, duration_minutes, search_start, search_end
                )

                if available_slots:
                    best_slot = available_slots[0]
                    return self._create_calendar_meeting(
                        user,
                        title,
                        description,
                        best_slot["start_time"],
                        best_slot["end_time"],
                        attendee_emails,
                        lead,
                    )
                else:
                    return False, {
                        "error": "No available time slots found in the next 2 weeks",
                        "suggested_action": "Please check your calendar availability",
                    }

        except Exception as e:
            logger.error(f"Error scheduling meeting with conflict resolution: {str(e)}")
            return False, {"error": str(e)}

    def _create_calendar_meeting(
        self,
        user: User,
        title: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
        attendee_emails: List[str],
        lead: Lead,
        alternative_time: bool = False,
        original_conflicts: List[CalendarConflict] = None,
    ) -> Tuple[bool, Dict]:
        """Create meeting in both Google Calendar and Outlook if available"""
        try:
            results = {}
            meeting_urls = []

            # Try to create in Google Calendar
            google_success = False
            try:
                if self.refresh_google_credentials(user):
                    google_event = self._create_google_calendar_event(
                        user, title, description, start_time, end_time, attendee_emails
                    )
                    if google_event:
                        results["google"] = google_event
                        if google_event.get("hangoutLink"):
                            meeting_urls.append(google_event["hangoutLink"])
                        google_success = True
            except Exception as e:
                logger.warning(f"Failed to create Google Calendar event: {str(e)}")
                results["google_error"] = str(e)

            # Try to create in Outlook Calendar
            outlook_success = False
            try:
                if self.refresh_outlook_credentials(user):
                    outlook_event = self._create_outlook_calendar_event(
                        user, title, description, start_time, end_time, attendee_emails
                    )
                    if outlook_event:
                        results["outlook"] = outlook_event
                        if outlook_event.get("onlineMeeting", {}).get("joinUrl"):
                            meeting_urls.append(
                                outlook_event["onlineMeeting"]["joinUrl"]
                            )
                        outlook_success = True
            except Exception as e:
                logger.warning(f"Failed to create Outlook Calendar event: {str(e)}")
                results["outlook_error"] = str(e)

            if google_success or outlook_success:
                # Create Meeting record in database
                meeting = Meeting.objects.create(
                    lead=lead,
                    title=title,
                    description=description,
                    scheduled_at=start_time,
                    duration_minutes=int((end_time - start_time).total_seconds() / 60),
                    meeting_url=meeting_urls[0] if meeting_urls else "",
                    meeting_platform="google_meet" if google_success else "outlook",
                    participants=attendee_emails,
                    ai_insights={
                        "auto_scheduled": True,
                        "alternative_time_used": alternative_time,
                        "original_conflicts": [
                            c.to_dict() for c in (original_conflicts or [])
                        ],
                        "calendar_integrations": list(results.keys()),
                    },
                )

                results["meeting_id"] = str(meeting.id)
                results["meeting_url"] = meeting_urls[0] if meeting_urls else ""
                results["success"] = True

                logger.info(
                    f"Successfully created meeting {meeting.id} for lead {lead.id}"
                )
                return True, results
            else:
                return False, {
                    "error": "Failed to create meeting in any calendar system",
                    "details": results,
                }

        except Exception as e:
            logger.error(f"Error creating calendar meeting: {str(e)}")
            return False, {"error": str(e)}

    def _create_google_calendar_event(
        self,
        user: User,
        title: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
        attendee_emails: List[str],
    ) -> Optional[Dict]:
        """Create event in Google Calendar"""
        try:
            google_creds = GoogleMeetCredentials.objects.get(user=user)
            credentials = Credentials(
                token=google_creds.access_token,
                refresh_token=google_creds.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.google_client_id,
                client_secret=self.google_client_secret,
                scopes=self.google_scopes,
            )

            service = build("calendar", "v3", credentials=credentials)

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
                "attendees": [{"email": email} for email in attendee_emails],
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "email", "minutes": 24 * 60},  # 1 day before
                        {"method": "email", "minutes": 60},  # 1 hour before
                        {"method": "popup", "minutes": 15},  # 15 minutes before
                    ],
                },
            }

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

            logger.info(f"Created Google Calendar event: {created_event['id']}")
            return created_event

        except Exception as e:
            logger.error(f"Error creating Google Calendar event: {str(e)}")
            return None

    def _create_outlook_calendar_event(
        self,
        user: User,
        title: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
        attendee_emails: List[str],
    ) -> Optional[Dict]:
        """Create event in Outlook Calendar"""
        try:
            teams_creds = MicrosoftTeamsCredentials.objects.get(user=user)

            headers = {
                "Authorization": f"Bearer {teams_creds.access_token}",
                "Content-Type": "application/json",
            }

            event_data = {
                "subject": title,
                "body": {"contentType": "HTML", "content": description},
                "start": {
                    "dateTime": start_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                    "timeZone": "UTC",
                },
                "end": {
                    "dateTime": end_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                    "timeZone": "UTC",
                },
                "attendees": [
                    {
                        "emailAddress": {"address": email, "name": email.split("@")[0]},
                        "type": "required",
                    }
                    for email in attendee_emails
                ],
                "isOnlineMeeting": True,
                "onlineMeetingProvider": "teamsForBusiness",
                "reminderMinutesBeforeStart": 15,
            }

            response = requests.post(
                "https://graph.microsoft.com/v1.0/me/events",
                headers=headers,
                json=event_data,
            )
            response.raise_for_status()

            created_event = response.json()
            logger.info(f"Created Outlook Calendar event: {created_event['id']}")
            return created_event

        except Exception as e:
            logger.error(f"Error creating Outlook Calendar event: {str(e)}")
            return None

    # Meeting Reminders and Preparation

    def schedule_meeting_reminders(
        self, meeting: Meeting, reminder_times: List[int] = None
    ) -> bool:
        """Schedule meeting reminders with preparation materials"""
        try:
            reminder_times = reminder_times or [
                24 * 60,
                60,
                15,
            ]  # 1 day, 1 hour, 15 minutes

            from .pre_meeting_intelligence import PreMeetingIntelligenceService

            intelligence_service = PreMeetingIntelligenceService()

            # Generate preparation materials
            preparation_materials = intelligence_service.generate_meeting_preparation(
                meeting
            )

            # Schedule reminders (this would typically use a task queue like Celery)
            for minutes_before in reminder_times:
                reminder_time = meeting.scheduled_at - timedelta(minutes=minutes_before)

                if reminder_time > timezone.now():
                    # In a real implementation, this would schedule a Celery task
                    self._schedule_reminder_task(
                        meeting, reminder_time, preparation_materials
                    )

            logger.info(
                f"Scheduled {len(reminder_times)} reminders for meeting {meeting.id}"
            )
            return True

        except Exception as e:
            logger.error(f"Error scheduling meeting reminders: {str(e)}")
            return False

    def _schedule_reminder_task(
        self, meeting: Meeting, reminder_time: datetime, preparation_materials: Dict
    ):
        """Schedule a reminder task (placeholder for Celery integration)"""
        # This would typically use Celery to schedule the task
        # For now, we'll just log the scheduled reminder
        logger.info(f"Reminder scheduled for meeting {meeting.id} at {reminder_time}")

        # Store reminder info in meeting AI insights
        if "scheduled_reminders" not in meeting.ai_insights:
            meeting.ai_insights["scheduled_reminders"] = []

        meeting.ai_insights["scheduled_reminders"].append(
            {
                "reminder_time": reminder_time.isoformat(),
                "preparation_materials": preparation_materials,
                "status": "scheduled",
            }
        )
        meeting.save()

    def send_meeting_reminder(self, meeting: Meeting, minutes_before: int) -> bool:
        """Send meeting reminder with preparation materials"""
        try:
            from django.core.mail import send_mail
            from django.template.loader import render_to_string

            # Get lead and user information
            lead = meeting.lead
            user = lead.user if hasattr(lead, "user") else None

            if not user or not user.email:
                logger.warning(f"No user email found for meeting {meeting.id}")
                return False

            # Prepare context for email template
            context = {
                "meeting": meeting,
                "lead": lead,
                "user": user,
                "minutes_before": minutes_before,
                "meeting_url": meeting.meeting_url,
                "preparation_materials": meeting.ai_insights.get(
                    "preparation_materials", {}
                ),
            }

            # Render email content
            subject = f"Meeting Reminder: {meeting.title} in {minutes_before} minutes"
            if minutes_before >= 60:
                hours = minutes_before // 60
                subject = f"Meeting Reminder: {meeting.title} in {hours} hour{'s' if hours > 1 else ''}"
            elif minutes_before >= 1440:
                days = minutes_before // 1440
                subject = (
                    f"Meeting Reminder: {meeting.title} tomorrow"
                    if days == 1
                    else f"Meeting Reminder: {meeting.title} in {days} days"
                )

            # For now, we'll use a simple text email
            # In a real implementation, you'd use HTML templates
            message = f"""
            Hi {user.get_full_name() or user.email},
            
            This is a reminder for your upcoming meeting:
            
            Meeting: {meeting.title}
            Company: {lead.company_name}
            Time: {meeting.scheduled_at.strftime('%Y-%m-%d %H:%M UTC')}
            Duration: {meeting.duration_minutes} minutes
            
            Meeting Link: {meeting.meeting_url}
            
            Preparation Materials:
            - Review lead information and previous conversations
            - Check agenda: {meeting.agenda}
            - Prepare questions based on lead's pain points and requirements
            
            Best regards,
            NIA Sales Assistant
            """

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            logger.info(f"Sent meeting reminder for meeting {meeting.id}")
            return True

        except Exception as e:
            logger.error(f"Error sending meeting reminder: {str(e)}")
            return False

    # Calendar Sync Status

    def get_calendar_sync_status(self, user: User) -> Dict:
        """Get the status of calendar integrations for a user"""
        try:
            status = {
                "google_calendar": {
                    "connected": False,
                    "last_sync": None,
                    "error": None,
                },
                "outlook_calendar": {
                    "connected": False,
                    "last_sync": None,
                    "error": None,
                },
            }

            # Check Google Calendar status
            try:
                google_creds = GoogleMeetCredentials.objects.get(user=user)
                status["google_calendar"][
                    "connected"
                ] = not google_creds.is_token_expired()
                status["google_calendar"][
                    "last_sync"
                ] = google_creds.updated_at.isoformat()

                if google_creds.is_token_expired():
                    status["google_calendar"][
                        "error"
                    ] = "Token expired, re-authentication required"

            except GoogleMeetCredentials.DoesNotExist:
                status["google_calendar"]["error"] = "Not connected"

            # Check Outlook Calendar status
            try:
                teams_creds = MicrosoftTeamsCredentials.objects.get(user=user)
                status["outlook_calendar"][
                    "connected"
                ] = not teams_creds.is_token_expired()
                status["outlook_calendar"][
                    "last_sync"
                ] = teams_creds.updated_at.isoformat()

                if teams_creds.is_token_expired():
                    status["outlook_calendar"][
                        "error"
                    ] = "Token expired, re-authentication required"

            except MicrosoftTeamsCredentials.DoesNotExist:
                status["outlook_calendar"]["error"] = "Not connected"

            return status

        except Exception as e:
            logger.error(f"Error getting calendar sync status: {str(e)}")
            return {
                "google_calendar": {"connected": False, "error": str(e)},
                "outlook_calendar": {"connected": False, "error": str(e)},
            }

    # Utility Methods

    def get_user_timezone(self, user: User) -> str:
        """Get user's timezone (placeholder - would be stored in user profile)"""
        # In a real implementation, this would come from user preferences
        return getattr(user, "timezone", "UTC")

    def format_meeting_invitation(
        self, meeting: Meeting, preparation_materials: Dict = None
    ) -> str:
        """Format meeting invitation with preparation materials"""
        invitation = f"""
        Meeting Invitation: {meeting.title}
        
        Company: {meeting.lead.company_name}
        Date & Time: {meeting.scheduled_at.strftime('%Y-%m-%d %H:%M UTC')}
        Duration: {meeting.duration_minutes} minutes
        
        Meeting Link: {meeting.meeting_url}
        
        Agenda:
        {meeting.agenda}
        
        """

        if preparation_materials:
            invitation += "\nPreparation Materials:\n"
            for key, value in preparation_materials.items():
                invitation += f"- {key}: {value}\n"

        return invitation
