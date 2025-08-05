import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .models import GoogleMeetCredentials, MeetingSession, MeetingParticipant, MeetingStatusUpdate
from credentials import get_google_meet_credentials

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
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.scopes
            )
            flow.redirect_uri = self.redirect_uri
            
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=user_id  # Pass user_id as state parameter
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
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.scopes
            )
            flow.redirect_uri = self.redirect_uri
            
            # Exchange authorization code for tokens
            flow.fetch_token(code=authorization_code)
            credentials = flow.credentials
            
            # Store or update credentials
            google_creds, created = GoogleMeetCredentials.objects.get_or_create(
                user=user,
                defaults={
                    'access_token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_expiry': credentials.expiry,
                    'scope': ' '.join(self.scopes)
                }
            )
            
            if not created:
                # Update existing credentials
                google_creds.access_token = credentials.token
                google_creds.refresh_token = credentials.refresh_token
                google_creds.token_expiry = credentials.expiry
                google_creds.scope = ' '.join(self.scopes)
                google_creds.save()
            
            logger.info(f"Successfully stored Google Meet credentials for user {user_id}")
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
                    scopes=self.scopes
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
    
    def create_meeting(self, user: User, title: str, description: str, 
                      start_time: datetime, end_time: datetime, 
                      attendee_emails: List[str] = None) -> Optional[MeetingSession]:
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
                scopes=self.scopes
            )
            
            # Build Calendar API service
            service = build('calendar', 'v3', credentials=credentials)
            
            # Create calendar event with Google Meet
            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'conferenceData': {
                    'createRequest': {
                        'requestId': str(uuid.uuid4()),
                        'conferenceSolutionKey': {
                            'type': 'hangoutsMeet'
                        }
                    }
                },
                'attendees': [{'email': email} for email in (attendee_emails or [])],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 10},
                    ],
                },
            }
            
            # Create the event
            created_event = service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1,
                sendUpdates='all'
            ).execute()
            
            # Extract Google Meet details
            meet_url = ""
            meet_space_id = ""
            if 'conferenceData' in created_event:
                conference_data = created_event['conferenceData']
                if 'entryPoints' in conference_data:
                    for entry_point in conference_data['entryPoints']:
                        if entry_point['entryPointType'] == 'video':
                            meet_url = entry_point['uri']
                            break
                if 'conferenceId' in conference_data:
                    meet_space_id = conference_data['conferenceId']
            
            # Create MeetingSession record
            meeting_session = MeetingSession.objects.create(
                organizer=user,
                title=title,
                description=description,
                meeting_type=MeetingSession.MeetingType.GOOGLE_MEET,
                google_meet_url=meet_url,
                google_calendar_event_id=created_event['id'],
                google_meet_space_id=meet_space_id,
                scheduled_start_time=start_time,
                scheduled_end_time=end_time,
                status=MeetingSession.Status.SCHEDULED
            )
            
            # Create participant records
            if attendee_emails:
                for email in attendee_emails:
                    participant = MeetingParticipant.objects.create(
                        meeting=meeting_session,
                        email=email,
                        name=email.split('@')[0],  # Use email prefix as default name
                        role=MeetingParticipant.ParticipantRole.ATTENDEE,
                        status=MeetingParticipant.ParticipantStatus.INVITED
                    )
            
            # Add organizer as participant
            MeetingParticipant.objects.create(
                meeting=meeting_session,
                user=user,
                email=user.email,
                name=user.get_full_name() or user.email,
                role=MeetingParticipant.ParticipantRole.ORGANIZER,
                status=MeetingParticipant.ParticipantStatus.ACCEPTED
            )
            
            # Create status update
            MeetingStatusUpdate.objects.create(
                meeting=meeting_session,
                update_type=MeetingStatusUpdate.UpdateType.CREATED,
                description=f"Meeting '{title}' created with Google Meet",
                triggered_by=user,
                metadata={
                    'google_event_id': created_event['id'],
                    'meet_url': meet_url,
                    'attendee_count': len(attendee_emails) if attendee_emails else 0
                }
            )
            
            logger.info(f"Successfully created Google Meet meeting: {meeting_session.id}")
            return meeting_session
            
        except Exception as e:
            logger.error(f"Error creating Google Meet meeting: {str(e)}")
            return None
    
    def update_meeting_status(self, meeting_session: MeetingSession, 
                            new_status: str, user: User = None) -> bool:
        """Update meeting status and create status update record"""
        try:
            old_status = meeting_session.status
            meeting_session.status = new_status
            
            # Update timing based on status
            now = timezone.now()
            if new_status == MeetingSession.Status.ACTIVE and not meeting_session.actual_start_time:
                meeting_session.actual_start_time = now
            elif new_status == MeetingSession.Status.ENDED and not meeting_session.actual_end_time:
                meeting_session.actual_end_time = now
            
            meeting_session.save()
            
            # Create status update record
            update_type_map = {
                MeetingSession.Status.ACTIVE: MeetingStatusUpdate.UpdateType.STARTED,
                MeetingSession.Status.ENDED: MeetingStatusUpdate.UpdateType.ENDED,
                MeetingSession.Status.CANCELLED: MeetingStatusUpdate.UpdateType.CANCELLED,
            }
            
            update_type = update_type_map.get(new_status, MeetingStatusUpdate.UpdateType.CREATED)
            
            MeetingStatusUpdate.objects.create(
                meeting=meeting_session,
                update_type=update_type,
                description=f"Meeting status changed from {old_status} to {new_status}",
                triggered_by=user,
                metadata={'old_status': old_status, 'new_status': new_status}
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
                models.Q(organizer=user) | 
                models.Q(participants__user=user)
            ).distinct()
            
            if status:
                queryset = queryset.filter(status=status)
            
            return list(queryset.order_by('-scheduled_start_time'))
            
        except Exception as e:
            logger.error(f"Error getting user meetings: {str(e)}")
            return []
    
    def delete_meeting(self, meeting_session: MeetingSession, user: User) -> bool:
        """Delete a Google Meet meeting"""
        try:
            # Only organizer can delete
            if meeting_session.organizer != user:
                logger.error(f"User {user.id} not authorized to delete meeting {meeting_session.id}")
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
                scopes=self.scopes
            )
            
            # Build Calendar API service
            service = build('calendar', 'v3', credentials=credentials)
            
            # Delete the calendar event
            if meeting_session.google_calendar_event_id:
                service.events().delete(
                    calendarId='primary',
                    eventId=meeting_session.google_calendar_event_id,
                    sendUpdates='all'
                ).execute()
            
            # Update meeting status to cancelled
            self.update_meeting_status(meeting_session, MeetingSession.Status.CANCELLED, user)
            
            logger.info(f"Successfully deleted Google Meet meeting: {meeting_session.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting Google Meet meeting: {str(e)}")
            return False