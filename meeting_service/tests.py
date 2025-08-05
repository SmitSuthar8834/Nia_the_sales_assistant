from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock

from .models import (
    GoogleMeetCredentials, MeetingSession, MeetingParticipant, 
    MeetingStatusUpdate, MeetingInvitation
)

User = get_user_model()


class GoogleMeetCredentialsTestCase(TestCase):
    """Test cases for GoogleMeetCredentials model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_credentials(self):
        """Test creating Google Meet credentials"""
        credentials = GoogleMeetCredentials.objects.create(
            user=self.user,
            access_token='test_access_token',
            refresh_token='test_refresh_token',
            token_expiry=timezone.now() + timedelta(hours=1),
            scope='https://www.googleapis.com/auth/calendar'
        )
        
        self.assertEqual(credentials.user, self.user)
        self.assertEqual(credentials.access_token, 'test_access_token')
        self.assertFalse(credentials.is_token_expired())
    
    def test_token_expiry_check(self):
        """Test token expiry checking"""
        # Create expired credentials
        expired_credentials = GoogleMeetCredentials.objects.create(
            user=self.user,
            access_token='test_access_token',
            refresh_token='test_refresh_token',
            token_expiry=timezone.now() - timedelta(hours=1),
            scope='https://www.googleapis.com/auth/calendar'
        )
        
        self.assertTrue(expired_credentials.is_token_expired())


class MeetingSessionTestCase(TestCase):
    """Test cases for MeetingSession model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='organizer',
            email='organizer@example.com',
            password='testpass123'
        )
    
    def test_create_meeting_session(self):
        """Test creating a meeting session"""
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        
        meeting = MeetingSession.objects.create(
            organizer=self.user,
            title='Test Meeting',
            description='Test meeting description',
            meeting_type=MeetingSession.MeetingType.GOOGLE_MEET,
            google_meet_url='https://meet.google.com/test-meeting',
            scheduled_start_time=start_time,
            scheduled_end_time=end_time,
            status=MeetingSession.Status.SCHEDULED
        )
        
        self.assertEqual(meeting.organizer, self.user)
        self.assertEqual(meeting.title, 'Test Meeting')
        self.assertEqual(meeting.meeting_type, MeetingSession.MeetingType.GOOGLE_MEET)
        self.assertEqual(meeting.status, MeetingSession.Status.SCHEDULED)
        self.assertEqual(meeting.duration_minutes, 60)
    
    def test_meeting_is_active(self):
        """Test meeting active status checking"""
        now = timezone.now()
        start_time = now - timedelta(minutes=30)
        end_time = now + timedelta(minutes=30)
        
        meeting = MeetingSession.objects.create(
            organizer=self.user,
            title='Active Meeting',
            scheduled_start_time=start_time,
            scheduled_end_time=end_time,
            status=MeetingSession.Status.SCHEDULED
        )
        
        self.assertTrue(meeting.is_active())


class MeetingParticipantTestCase(TestCase):
    """Test cases for MeetingParticipant model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='organizer2',
            email='organizer2@example.com',
            password='testpass123'
        )
        
        self.meeting = MeetingSession.objects.create(
            organizer=self.user,
            title='Test Meeting',
            scheduled_start_time=timezone.now() + timedelta(hours=1),
            scheduled_end_time=timezone.now() + timedelta(hours=2)
        )
    
    def test_create_participant(self):
        """Test creating a meeting participant"""
        participant = MeetingParticipant.objects.create(
            meeting=self.meeting,
            email='participant@example.com',
            name='Test Participant',
            role=MeetingParticipant.ParticipantRole.ATTENDEE,
            status=MeetingParticipant.ParticipantStatus.INVITED
        )
        
        self.assertEqual(participant.meeting, self.meeting)
        self.assertEqual(participant.email, 'participant@example.com')
        self.assertEqual(participant.role, MeetingParticipant.ParticipantRole.ATTENDEE)
        self.assertEqual(participant.status, MeetingParticipant.ParticipantStatus.INVITED)
    
    def test_participation_duration(self):
        """Test participation duration calculation"""
        participant = MeetingParticipant.objects.create(
            meeting=self.meeting,
            email='participant@example.com',
            name='Test Participant',
            joined_at=timezone.now(),
            left_at=timezone.now() + timedelta(minutes=30)
        )
        
        # Duration should be approximately 30 minutes
        self.assertAlmostEqual(participant.participation_duration_minutes, 30, delta=1)


class MeetingStatusUpdateTestCase(TestCase):
    """Test cases for MeetingStatusUpdate model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='organizer3',
            email='organizer3@example.com',
            password='testpass123'
        )
        
        self.meeting = MeetingSession.objects.create(
            organizer=self.user,
            title='Test Meeting',
            scheduled_start_time=timezone.now() + timedelta(hours=1),
            scheduled_end_time=timezone.now() + timedelta(hours=2)
        )
    
    def test_create_status_update(self):
        """Test creating a meeting status update"""
        status_update = MeetingStatusUpdate.objects.create(
            meeting=self.meeting,
            update_type=MeetingStatusUpdate.UpdateType.CREATED,
            description='Meeting created',
            triggered_by=self.user,
            metadata={'test': 'data'}
        )
        
        self.assertEqual(status_update.meeting, self.meeting)
        self.assertEqual(status_update.update_type, MeetingStatusUpdate.UpdateType.CREATED)
        self.assertEqual(status_update.triggered_by, self.user)
        self.assertEqual(status_update.metadata, {'test': 'data'})


class GoogleMeetServiceTestCase(TestCase):
    """Test cases for GoogleMeetService (mocked)"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='servicetest',
            email='servicetest@example.com',
            password='testpass123'
        )
    
    def test_credentials_storage(self):
        """Test storing Google Meet credentials"""
        credentials = GoogleMeetCredentials.objects.create(
            user=self.user,
            access_token='test_token',
            refresh_token='test_refresh',
            token_expiry=timezone.now() + timedelta(hours=1),
            scope='calendar'
        )
        
        stored_creds = GoogleMeetCredentials.objects.get(user=self.user)
        self.assertEqual(stored_creds.access_token, 'test_token')
        self.assertEqual(stored_creds.refresh_token, 'test_refresh')
        self.assertFalse(stored_creds.is_token_expired())


# Microsoft Teams Integration Tests

from .models import MicrosoftTeamsCredentials
from .microsoft_teams_service import MicrosoftTeamsService


class MicrosoftTeamsCredentialsTestCase(TestCase):
    """Test cases for MicrosoftTeamsCredentials model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='teamsuser',
            email='teams@example.com',
            password='testpass123'
        )
    
    def test_create_teams_credentials(self):
        """Test creating Microsoft Teams credentials"""
        credentials = MicrosoftTeamsCredentials.objects.create(
            user=self.user,
            access_token='test_teams_access_token',
            refresh_token='test_teams_refresh_token',
            token_expiry=timezone.now() + timedelta(hours=1),
            scope='https://graph.microsoft.com/OnlineMeetings.ReadWrite',
            tenant_id='test-tenant-id'
        )
        
        self.assertEqual(credentials.user, self.user)
        self.assertEqual(credentials.access_token, 'test_teams_access_token')
        self.assertEqual(credentials.tenant_id, 'test-tenant-id')
        self.assertFalse(credentials.is_token_expired())
    
    def test_teams_token_expiry_check(self):
        """Test Teams token expiry checking"""
        # Create expired credentials
        expired_credentials = MicrosoftTeamsCredentials.objects.create(
            user=self.user,
            access_token='test_access_token',
            refresh_token='test_refresh_token',
            token_expiry=timezone.now() - timedelta(hours=1),
            scope='https://graph.microsoft.com/OnlineMeetings.ReadWrite',
            tenant_id='test-tenant-id'
        )
        
        self.assertTrue(expired_credentials.is_token_expired())


class TeamsMeetingSessionTestCase(TestCase):
    """Test cases for Teams MeetingSession model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='teamsorganizer',
            email='teamsorganizer@example.com',
            password='testpass123'
        )
    
    def test_create_teams_meeting_session(self):
        """Test creating a Teams meeting session"""
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        
        meeting = MeetingSession.objects.create(
            organizer=self.user,
            title='Teams Test Meeting',
            description='Teams meeting description',
            meeting_type=MeetingSession.MeetingType.MICROSOFT_TEAMS,
            teams_meeting_url='https://teams.microsoft.com/l/meetup-join/test-meeting',
            teams_meeting_id='test-meeting-id',
            teams_join_url='https://teams.microsoft.com/l/meetup-join/test-meeting',
            teams_conference_id='test-conference-id',
            teams_organizer_id='organizer@example.com',
            scheduled_start_time=start_time,
            scheduled_end_time=end_time,
            status=MeetingSession.Status.SCHEDULED
        )
        
        self.assertEqual(meeting.organizer, self.user)
        self.assertEqual(meeting.title, 'Teams Test Meeting')
        self.assertEqual(meeting.meeting_type, MeetingSession.MeetingType.MICROSOFT_TEAMS)
        self.assertEqual(meeting.teams_meeting_id, 'test-meeting-id')
        self.assertEqual(meeting.teams_conference_id, 'test-conference-id')
        self.assertEqual(meeting.status, MeetingSession.Status.SCHEDULED)
        self.assertEqual(meeting.duration_minutes, 60)


class MicrosoftTeamsServiceTestCase(TestCase):
    """Test cases for MicrosoftTeamsService (mocked)"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='teamsservicetest',
            email='teamsservicetest@example.com',
            password='testpass123'
        )
        
        # Create Teams credentials for the user
        self.teams_credentials = MicrosoftTeamsCredentials.objects.create(
            user=self.user,
            access_token='test_teams_token',
            refresh_token='test_teams_refresh',
            token_expiry=timezone.now() + timedelta(hours=1),
            scope='https://graph.microsoft.com/OnlineMeetings.ReadWrite',
            tenant_id='test-tenant-id'
        )
        
        self.teams_service = MicrosoftTeamsService()
    
    def test_teams_credentials_storage(self):
        """Test storing Microsoft Teams credentials"""
        stored_creds = MicrosoftTeamsCredentials.objects.get(user=self.user)
        self.assertEqual(stored_creds.access_token, 'test_teams_token')
        self.assertEqual(stored_creds.refresh_token, 'test_teams_refresh')
        self.assertEqual(stored_creds.tenant_id, 'test-tenant-id')
        self.assertFalse(stored_creds.is_token_expired())
    
    @patch('meeting_service.microsoft_teams_service.requests.post')
    def test_create_teams_meeting_mock(self, mock_post):
        """Test creating a Teams meeting with mocked API response"""
        # Mock the Graph API response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': 'test-meeting-id',
            'subject': 'Test Teams Meeting',
            'onlineMeeting': {
                'joinUrl': 'https://teams.microsoft.com/l/meetup-join/test-meeting',
                'conferenceId': 'test-conference-id'
            },
            'organizer': {
                'emailAddress': {
                    'address': 'teamsservicetest@example.com'
                }
            }
        }
        mock_post.return_value = mock_response
        
        # Create meeting
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        
        meeting = self.teams_service.create_meeting(
            user=self.user,
            title='Test Teams Meeting',
            description='Test description',
            start_time=start_time,
            end_time=end_time,
            attendee_emails=['attendee@example.com']
        )
        
        # Verify meeting was created
        self.assertIsNotNone(meeting)
        self.assertEqual(meeting.title, 'Test Teams Meeting')
        self.assertEqual(meeting.meeting_type, MeetingSession.MeetingType.MICROSOFT_TEAMS)
        self.assertEqual(meeting.organizer, self.user)
    
    def test_refresh_teams_credentials(self):
        """Test refreshing Teams credentials"""
        # Test with valid credentials
        result = self.teams_service.refresh_user_credentials(self.user)
        self.assertTrue(result)
        
        # Test with expired credentials
        self.teams_credentials.token_expiry = timezone.now() - timedelta(hours=1)
        self.teams_credentials.save()
        
        # This would normally make an API call, but we're testing the logic
        # In a real scenario, this would be mocked
        result = self.teams_service.refresh_user_credentials(self.user)
        # The result depends on the actual MSAL implementation
    
    def test_get_user_teams_meetings(self):
        """Test getting user's Teams meetings"""
        # Create some test meetings
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        
        teams_meeting = MeetingSession.objects.create(
            organizer=self.user,
            title='Teams Meeting',
            meeting_type=MeetingSession.MeetingType.MICROSOFT_TEAMS,
            scheduled_start_time=start_time,
            scheduled_end_time=end_time
        )
        
        google_meeting = MeetingSession.objects.create(
            organizer=self.user,
            title='Google Meeting',
            meeting_type=MeetingSession.MeetingType.GOOGLE_MEET,
            scheduled_start_time=start_time,
            scheduled_end_time=end_time
        )
        
        # Get Teams meetings only
        teams_meetings = self.teams_service.get_user_meetings(self.user)
        
        # Should only return Teams meetings
        self.assertEqual(len(teams_meetings), 1)
        self.assertEqual(teams_meetings[0].meeting_type, MeetingSession.MeetingType.MICROSOFT_TEAMS)
        self.assertEqual(teams_meetings[0].title, 'Teams Meeting')


class UnifiedMeetingInterfaceTestCase(TestCase):
    """Test cases for unified meeting interface"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='unifieduser',
            email='unified@example.com',
            password='testpass123'
        )
    
    def test_meeting_type_selection(self):
        """Test that meetings can be created with different types"""
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        
        # Create Google Meet meeting
        google_meeting = MeetingSession.objects.create(
            organizer=self.user,
            title='Google Meeting',
            meeting_type=MeetingSession.MeetingType.GOOGLE_MEET,
            google_meet_url='https://meet.google.com/test',
            scheduled_start_time=start_time,
            scheduled_end_time=end_time
        )
        
        # Create Teams meeting
        teams_meeting = MeetingSession.objects.create(
            organizer=self.user,
            title='Teams Meeting',
            meeting_type=MeetingSession.MeetingType.MICROSOFT_TEAMS,
            teams_meeting_url='https://teams.microsoft.com/l/meetup-join/test',
            scheduled_start_time=start_time,
            scheduled_end_time=end_time
        )
        
        # Verify both meetings exist with correct types
        self.assertEqual(google_meeting.meeting_type, MeetingSession.MeetingType.GOOGLE_MEET)
        self.assertEqual(teams_meeting.meeting_type, MeetingSession.MeetingType.MICROSOFT_TEAMS)
        
        # Verify URLs are set correctly
        self.assertTrue(google_meeting.google_meet_url)
        self.assertTrue(teams_meeting.teams_meeting_url)
    
    def test_unified_meeting_dashboard_data(self):
        """Test unified dashboard combines data from both platforms"""
        now = timezone.now()
        
        # Create meetings for today
        google_today = MeetingSession.objects.create(
            organizer=self.user,
            title='Google Today',
            meeting_type=MeetingSession.MeetingType.GOOGLE_MEET,
            scheduled_start_time=now.replace(hour=14, minute=0, second=0, microsecond=0),
            scheduled_end_time=now.replace(hour=15, minute=0, second=0, microsecond=0)
        )
        
        teams_today = MeetingSession.objects.create(
            organizer=self.user,
            title='Teams Today',
            meeting_type=MeetingSession.MeetingType.MICROSOFT_TEAMS,
            scheduled_start_time=now.replace(hour=16, minute=0, second=0, microsecond=0),
            scheduled_end_time=now.replace(hour=17, minute=0, second=0, microsecond=0)
        )
        
        # Create future meetings
        future_google = MeetingSession.objects.create(
            organizer=self.user,
            title='Future Google',
            meeting_type=MeetingSession.MeetingType.GOOGLE_MEET,
            scheduled_start_time=now + timedelta(days=1),
            scheduled_end_time=now + timedelta(days=1, hours=1)
        )
        
        # Get all user meetings
        all_meetings = MeetingSession.objects.filter(organizer=self.user)
        today_meetings = [m for m in all_meetings if m.scheduled_start_time.date() == now.date()]
        future_meetings = [m for m in all_meetings if m.scheduled_start_time > now]
        
        # Verify counts
        self.assertEqual(len(all_meetings), 3)
        self.assertEqual(len(today_meetings), 2)
        self.assertEqual(len(future_meetings), 1)
        
        # Verify meeting types are mixed
        meeting_types = [m.meeting_type for m in all_meetings]
        self.assertIn(MeetingSession.MeetingType.GOOGLE_MEET, meeting_types)
        self.assertIn(MeetingSession.MeetingType.MICROSOFT_TEAMS, meeting_types)


class MeetingIntegrationTestCase(TestCase):
    """Integration tests for meeting functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@example.com',
            password='testpass123'
        )
    
    def test_meeting_participant_workflow(self):
        """Test complete meeting participant workflow"""
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        
        # Create Teams meeting
        meeting = MeetingSession.objects.create(
            organizer=self.user,
            title='Integration Test Meeting',
            meeting_type=MeetingSession.MeetingType.MICROSOFT_TEAMS,
            teams_meeting_url='https://teams.microsoft.com/l/meetup-join/test',
            scheduled_start_time=start_time,
            scheduled_end_time=end_time
        )
        
        # Add participants
        organizer_participant = MeetingParticipant.objects.create(
            meeting=meeting,
            user=self.user,
            email=self.user.email,
            name=self.user.get_full_name() or self.user.email,
            role=MeetingParticipant.ParticipantRole.ORGANIZER,
            status=MeetingParticipant.ParticipantStatus.ACCEPTED
        )
        
        attendee_participant = MeetingParticipant.objects.create(
            meeting=meeting,
            email='attendee@example.com',
            name='Test Attendee',
            role=MeetingParticipant.ParticipantRole.ATTENDEE,
            status=MeetingParticipant.ParticipantStatus.INVITED
        )
        
        # Create status updates
        created_update = MeetingStatusUpdate.objects.create(
            meeting=meeting,
            update_type=MeetingStatusUpdate.UpdateType.CREATED,
            description='Teams meeting created',
            triggered_by=self.user,
            metadata={'teams_meeting_id': 'test-id'}
        )
        
        # Verify the complete workflow
        self.assertEqual(meeting.participants.count(), 2)
        self.assertEqual(meeting.status_updates.count(), 1)
        
        # Verify organizer participant
        self.assertEqual(organizer_participant.role, MeetingParticipant.ParticipantRole.ORGANIZER)
        self.assertEqual(organizer_participant.status, MeetingParticipant.ParticipantStatus.ACCEPTED)
        
        # Verify attendee participant
        self.assertEqual(attendee_participant.role, MeetingParticipant.ParticipantRole.ATTENDEE)
        self.assertEqual(attendee_participant.status, MeetingParticipant.ParticipantStatus.INVITED)
        
        # Verify status update
        self.assertEqual(created_update.update_type, MeetingStatusUpdate.UpdateType.CREATED)
        self.assertEqual(created_update.triggered_by, self.user)
    
    def test_meeting_status_transitions(self):
        """Test meeting status transitions"""
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        
        meeting = MeetingSession.objects.create(
            organizer=self.user,
            title='Status Test Meeting',
            meeting_type=MeetingSession.MeetingType.MICROSOFT_TEAMS,
            scheduled_start_time=start_time,
            scheduled_end_time=end_time,
            status=MeetingSession.Status.SCHEDULED
        )
        
        # Test status transitions
        self.assertEqual(meeting.status, MeetingSession.Status.SCHEDULED)
        
        # Start meeting
        meeting.status = MeetingSession.Status.ACTIVE
        meeting.actual_start_time = timezone.now()
        meeting.save()
        
        MeetingStatusUpdate.objects.create(
            meeting=meeting,
            update_type=MeetingStatusUpdate.UpdateType.STARTED,
            description='Meeting started',
            triggered_by=self.user
        )
        
        self.assertEqual(meeting.status, MeetingSession.Status.ACTIVE)
        self.assertIsNotNone(meeting.actual_start_time)
        
        # End meeting
        meeting.status = MeetingSession.Status.ENDED
        meeting.actual_end_time = timezone.now()
        meeting.save()
        
        MeetingStatusUpdate.objects.create(
            meeting=meeting,
            update_type=MeetingStatusUpdate.UpdateType.ENDED,
            description='Meeting ended',
            triggered_by=self.user
        )
        
        self.assertEqual(meeting.status, MeetingSession.Status.ENDED)
        self.assertIsNotNone(meeting.actual_end_time)
        self.assertEqual(meeting.status_updates.count(), 2)

# Intelligent Meeting Service Tests

from .intelligent_meeting_service import IntelligentMeetingService


class IntelligentMeetingServiceTestCase(TestCase):
    """Test cases for IntelligentMeetingService"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='intelligentuser',
            email='intelligent@example.com',
            password='testpass123'
        )
        
        self.intelligent_service = IntelligentMeetingService()
        
        # Create some test meetings for analysis
        now = timezone.now()
        
        # Meeting today at 10 AM
        self.meeting_today = MeetingSession.objects.create(
            organizer=self.user,
            title='Today Meeting',
            scheduled_start_time=now.replace(hour=10, minute=0, second=0, microsecond=0),
            scheduled_end_time=now.replace(hour=11, minute=0, second=0, microsecond=0),
            actual_start_time=now.replace(hour=10, minute=5, second=0, microsecond=0),
            actual_end_time=now.replace(hour=11, minute=10, second=0, microsecond=0),
            status=MeetingSession.Status.ENDED
        )
        
        # Meeting tomorrow at 2 PM
        tomorrow = now + timedelta(days=1)
        self.meeting_tomorrow = MeetingSession.objects.create(
            organizer=self.user,
            title='Tomorrow Meeting',
            scheduled_start_time=tomorrow.replace(hour=14, minute=0, second=0, microsecond=0),
            scheduled_end_time=tomorrow.replace(hour=15, minute=0, second=0, microsecond=0),
            status=MeetingSession.Status.SCHEDULED
        )
        
        # Meeting next week (for availability analysis)
        next_week = now + timedelta(days=7)
        self.meeting_next_week = MeetingSession.objects.create(
            organizer=self.user,
            title='Next Week Meeting',
            scheduled_start_time=next_week.replace(hour=9, minute=0, second=0, microsecond=0),
            scheduled_end_time=next_week.replace(hour=10, minute=0, second=0, microsecond=0),
            status=MeetingSession.Status.SCHEDULED
        )
    
    def test_analyze_user_availability(self):
        """Test user availability analysis"""
        start_date = timezone.now()
        end_date = start_date + timedelta(days=7)
        
        availability = self.intelligent_service.analyze_user_availability(
            self.user, (start_date, end_date)
        )
        
        # Check that analysis returns expected structure
        self.assertIn('total_meetings', availability)
        self.assertIn('avg_daily_meetings', availability)
        self.assertIn('available_slots', availability)
        self.assertIn('meeting_load', availability)
        
        # Should find at least 2 meetings in the range
        self.assertGreaterEqual(availability['total_meetings'], 2)
        
        # Should have some available slots
        self.assertIsInstance(availability['available_slots'], list)
    
    def test_recommend_meeting_time(self):
        """Test meeting time recommendations"""
        recommendations = self.intelligent_service.recommend_meeting_time(
            self.user, duration_minutes=60
        )
        
        # Should return a list of recommendations
        self.assertIsInstance(recommendations, list)
        
        # Each recommendation should have required fields
        if recommendations:
            rec = recommendations[0]
            self.assertIn('start_time', rec)
            self.assertIn('end_time', rec)
            self.assertIn('score', rec)
            self.assertIn('reason', rec)
            
            # Score should be a number
            self.assertIsInstance(rec['score'], (int, float))
    
    def test_detect_meeting_conflicts(self):
        """Test meeting conflict detection"""
        # Create a proposed meeting that conflicts with tomorrow's meeting
        tomorrow = timezone.now() + timedelta(days=1)
        proposed_meeting = {
            'start_time': tomorrow.replace(hour=13, minute=30, second=0, microsecond=0),
            'end_time': tomorrow.replace(hour=14, minute=30, second=0, microsecond=0)
        }
        
        conflicts = self.intelligent_service.detect_meeting_conflicts(
            self.user, proposed_meeting
        )
        
        # Should detect conflict with tomorrow's meeting
        self.assertGreater(len(conflicts), 0)
        
        # Check conflict details
        conflict = conflicts[0]
        self.assertIn('meeting_id', conflict)
        self.assertIn('title', conflict)
        self.assertIn('overlap_minutes', conflict)
        self.assertGreater(conflict['overlap_minutes'], 0)
    
    def test_suggest_reschedule_options(self):
        """Test reschedule suggestions"""
        alternatives = self.intelligent_service.suggest_reschedule_options(
            self.user, self.meeting_tomorrow
        )
        
        # Should return alternative times
        self.assertIsInstance(alternatives, list)
        
        # Each alternative should have required fields
        if alternatives:
            alt = alternatives[0]
            self.assertIn('start_time', alt)
            self.assertIn('end_time', alt)
            self.assertIn('score', alt)
            self.assertIn('reason', alt)
            self.assertIn('time_difference_hours', alt)
    
    def test_schedule_post_meeting_followup(self):
        """Test post-meeting follow-up scheduling"""
        success = self.intelligent_service.schedule_post_meeting_follow_up(
            self.meeting_today
        )
        
        # Should successfully schedule follow-up
        self.assertTrue(success)
        
        # Should create a status update
        follow_up_updates = self.meeting_today.status_updates.filter(
            description__icontains='follow-up'
        )
        self.assertGreater(follow_up_updates.count(), 0)
        
        # Check metadata
        follow_up = follow_up_updates.first()
        self.assertIn('follow_up_time', follow_up.metadata)
        self.assertIn('follow_up_type', follow_up.metadata)
        self.assertEqual(follow_up.metadata['follow_up_type'], 'post_meeting')
    
    def test_analyze_meeting_patterns(self):
        """Test meeting pattern analysis"""
        patterns = self.intelligent_service.analyze_meeting_patterns(
            self.user, days_back=30
        )
        
        # Check that analysis returns expected structure
        self.assertIn('total_meetings', patterns)
        self.assertIn('avg_duration', patterns)
        self.assertIn('most_productive_hours', patterns)
        self.assertIn('meeting_frequency_by_day', patterns)
        self.assertIn('recommendations', patterns)
        
        # Should find our test meetings
        self.assertGreaterEqual(patterns['total_meetings'], 3)
        
        # Recommendations should be a list
        self.assertIsInstance(patterns['recommendations'], list)
    
    def test_calculate_meeting_productivity_score(self):
        """Test meeting productivity score calculation"""
        # Test with a well-structured meeting
        score = self.intelligent_service._calculate_meeting_productivity_score(
            self.meeting_today
        )
        
        # Score should be between 0 and 10
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 10)
        
        # Should be a float
        self.assertIsInstance(score, float)
    
    def test_calculate_overlap_minutes(self):
        """Test overlap calculation between time periods"""
        start1 = timezone.now()
        end1 = start1 + timedelta(hours=1)
        
        # Overlapping period
        start2 = start1 + timedelta(minutes=30)
        end2 = start2 + timedelta(hours=1)
        
        overlap = self.intelligent_service._calculate_overlap_minutes(
            start1, end1, start2, end2
        )
        
        # Should have 30 minutes overlap
        self.assertEqual(overlap, 30)
        
        # Non-overlapping periods
        start3 = end1 + timedelta(minutes=10)
        end3 = start3 + timedelta(hours=1)
        
        no_overlap = self.intelligent_service._calculate_overlap_minutes(
            start1, end1, start3, end3
        )
        
        # Should have no overlap
        self.assertEqual(no_overlap, 0)
    
    def test_get_calendar_sync_status(self):
        """Test calendar sync status retrieval"""
        sync_status = self.intelligent_service.get_calendar_sync_status(self.user)
        
        # Should return expected structure
        self.assertIn('google_calendar', sync_status)
        self.assertIn('outlook_calendar', sync_status)
        self.assertIn('teams_calendar', sync_status)
        
        # Should be boolean values
        self.assertIsInstance(sync_status['google_calendar'], bool)
        self.assertIsInstance(sync_status['outlook_calendar'], bool)
        self.assertIsInstance(sync_status['teams_calendar'], bool)
    
    def test_find_available_slots(self):
        """Test finding available time slots"""
        start_date = timezone.now()
        end_date = start_date + timedelta(days=2)
        
        # Get existing meetings
        existing_meetings = list(MeetingSession.objects.filter(organizer=self.user))
        
        # Find available slots
        available_slots = self.intelligent_service._find_available_slots(
            self.user, start_date, end_date, existing_meetings
        )
        
        # Should return a list of slots
        self.assertIsInstance(available_slots, list)
        
        # Each slot should have required fields
        if available_slots:
            slot = available_slots[0]
            self.assertIn('start', slot)
            self.assertIn('end', slot)
            self.assertIn('duration_minutes', slot)
            
            # Start should be before end
            self.assertLess(slot['start'], slot['end'])
    
    def test_generate_recommendation_reason(self):
        """Test recommendation reason generation"""
        slot = {
            'start': timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        }
        peak_hours = [10, 14, 16]
        daily_count = 1
        
        reason = self.intelligent_service._generate_recommendation_reason(
            slot, peak_hours, daily_count
        )
        
        # Should return a string
        self.assertIsInstance(reason, str)
        self.assertGreater(len(reason), 0)
        
        # Should mention peak hours since 10 AM is in peak_hours
        self.assertIn('typical meeting hours', reason)


class IntelligentMeetingIntegrationTestCase(TestCase):
    """Integration tests for intelligent meeting functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='integrationintelligent',
            email='integrationintelligent@example.com',
            password='testpass123'
        )
        
        self.intelligent_service = IntelligentMeetingService()
    
    def test_end_to_end_meeting_optimization(self):
        """Test complete meeting optimization workflow"""
        now = timezone.now()
        
        # Create a busy schedule
        for i in range(5):
            start_time = now + timedelta(days=i, hours=10)
            end_time = start_time + timedelta(hours=1)
            
            MeetingSession.objects.create(
                organizer=self.user,
                title=f'Busy Meeting {i+1}',
                scheduled_start_time=start_time,
                scheduled_end_time=end_time,
                status=MeetingSession.Status.SCHEDULED
            )
        
        # Analyze patterns
        patterns = self.intelligent_service.analyze_meeting_patterns(self.user, 30)
        
        # Should detect high meeting frequency
        self.assertGreaterEqual(patterns['total_meetings'], 5)
        
        # Get recommendations
        recommendations = self.intelligent_service.recommend_meeting_time(self.user, 60)
        
        # Should provide alternatives
        self.assertIsInstance(recommendations, list)
        
        # Analyze availability
        start_date = now
        end_date = now + timedelta(days=7)
        availability = self.intelligent_service.analyze_user_availability(
            self.user, (start_date, end_date)
        )
        
        # Should show heavy meeting load
        self.assertEqual(availability['meeting_load'], 'heavy')
    
    def test_conflict_resolution_workflow(self):
        """Test complete conflict resolution workflow"""
        now = timezone.now()
        
        # Create existing meeting
        existing_meeting = MeetingSession.objects.create(
            organizer=self.user,
            title='Existing Meeting',
            scheduled_start_time=now + timedelta(hours=2),
            scheduled_end_time=now + timedelta(hours=3),
            status=MeetingSession.Status.SCHEDULED
        )
        
        # Propose conflicting meeting
        proposed_meeting = {
            'start_time': now + timedelta(hours=1, minutes=30),
            'end_time': now + timedelta(hours=2, minutes=30)
        }
        
        # Detect conflicts
        conflicts = self.intelligent_service.detect_meeting_conflicts(
            self.user, proposed_meeting
        )
        
        # Should detect the conflict
        self.assertGreater(len(conflicts), 0)
        
        # Get reschedule options
        alternatives = self.intelligent_service.suggest_reschedule_options(
            self.user, existing_meeting
        )
        
        # Should provide alternatives
        self.assertIsInstance(alternatives, list)
        
        # Alternatives should not conflict with the proposed meeting
        for alt in alternatives:
            alt_conflicts = self.intelligent_service.detect_meeting_conflicts(
                self.user, {
                    'start_time': alt['start_time'],
                    'end_time': alt['end_time']
                }
            )
            # Should have fewer or no conflicts
            self.assertLessEqual(len(alt_conflicts), len(conflicts))

# NIA Meeting Scheduler Tests

from .nia_meeting_scheduler import NIAMeetingScheduler, NIAMeetingType


class NIAMeetingSchedulerTestCase(TestCase):
    """Test cases for NIAMeetingScheduler"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='niauser',
            email='niauser@example.com',
            password='testpass123'
        )
        
        self.nia_scheduler = NIAMeetingScheduler()
    
    def test_get_available_time_slots(self):
        """Test getting available time slots for NIA meetings"""
        start_date = timezone.now()
        end_date = start_date + timedelta(days=7)
        
        available_slots = self.nia_scheduler.get_available_time_slots(
            self.user, (start_date, end_date), NIAMeetingType.LEAD_CONSULTATION
        )
        
        # Should return a list of available slots
        self.assertIsInstance(available_slots, list)
        
        # Each slot should have required fields
        if available_slots:
            slot = available_slots[0]
            self.assertIn('start_time', slot)
            self.assertIn('end_time', slot)
            self.assertIn('duration_minutes', slot)
            self.assertIn('meeting_type', slot)
            self.assertIn('recommended', slot)
            self.assertIn('preparation_time', slot)
            
            # Duration should match meeting type
            self.assertEqual(slot['duration_minutes'], 45)  # Lead consultation duration
            self.assertEqual(slot['meeting_type'], 'lead_consultation')
    
    def test_schedule_nia_meeting(self):
        """Test scheduling a NIA meeting"""
        start_time = timezone.now() + timedelta(hours=2)
        
        meeting_data = {
            'start_time': start_time,
            'meeting_type': NIAMeetingType.GENERAL_CONSULTATION.value,
            'platform': 'google_meet'
        }
        
        # Mock the Google Meet service to avoid actual API calls
        with patch.object(self.nia_scheduler.google_service, 'create_meeting') as mock_create:
            mock_meeting = MeetingSession.objects.create(
                organizer=self.user,
                title='NIA Consultation',
                scheduled_start_time=start_time,
                scheduled_end_time=start_time + timedelta(minutes=45),
                meeting_type=MeetingSession.MeetingType.GOOGLE_MEET
            )
            mock_create.return_value = mock_meeting
            
            meeting_session = self.nia_scheduler.schedule_nia_meeting(self.user, meeting_data)
            
            # Should successfully create meeting
            self.assertIsNotNone(meeting_session)
            self.assertEqual(meeting_session.organizer, self.user)
            self.assertIn('NIA', meeting_session.title)
            
            # Should create NIA-specific status update
            nia_updates = meeting_session.status_updates.filter(
                description__icontains='NIA meeting'
            )
            self.assertGreater(nia_updates.count(), 0)
            
            # Check metadata
            nia_update = nia_updates.first()
            self.assertIn('nia_meeting_type', nia_update.metadata)
            self.assertEqual(nia_update.metadata['nia_meeting_type'], 'general_consultation')
    
    def test_generate_meeting_title(self):
        """Test meeting title generation"""
        title = self.nia_scheduler._generate_meeting_title(
            NIAMeetingType.LEAD_CONSULTATION, self.user
        )
        
        self.assertIn('NIA', title)
        self.assertIn('Lead Consultation', title)
    
    def test_generate_meeting_description(self):
        """Test meeting description generation"""
        description = self.nia_scheduler._generate_meeting_description(
            NIAMeetingType.SALES_STRATEGY, self.user
        )
        
        self.assertIn('NIA', description)
        self.assertIn('sales', description.lower())
        self.assertGreater(len(description), 20)
    
    def test_generate_meeting_agenda(self):
        """Test meeting agenda generation"""
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(minutes=45)
        
        meeting = MeetingSession.objects.create(
            organizer=self.user,
            title='NIA Lead Consultation',
            scheduled_start_time=start_time,
            scheduled_end_time=end_time
        )
        
        agenda = self.nia_scheduler._generate_meeting_agenda(
            meeting, NIAMeetingType.LEAD_CONSULTATION
        )
        
        # Should contain agenda structure
        self.assertIn('Meeting Agenda', agenda)
        self.assertIn('Duration:', agenda)
        self.assertIn('Preparation Items:', agenda)
        
        # Should contain lead consultation specific items
        self.assertIn('Lead overview', agenda)
        self.assertIn('Pain point', agenda)
    
    def test_calculate_preparation_time(self):
        """Test preparation time calculation"""
        # Different meeting types should have different preparation times
        lead_prep = self.nia_scheduler._calculate_preparation_time(NIAMeetingType.LEAD_CONSULTATION)
        training_prep = self.nia_scheduler._calculate_preparation_time(NIAMeetingType.TRAINING)
        
        self.assertIsInstance(lead_prep, int)
        self.assertIsInstance(training_prep, int)
        self.assertGreater(training_prep, lead_prep)  # Training should need more prep
    
    def test_is_optimal_nia_time(self):
        """Test optimal time detection"""
        # Business hours on weekday should be optimal
        weekday_business = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        while weekday_business.weekday() >= 5:  # Ensure it's a weekday
            weekday_business += timedelta(days=1)
        
        self.assertTrue(self.nia_scheduler._is_optimal_nia_time(weekday_business))
        
        # Evening should not be optimal
        evening = weekday_business.replace(hour=20)
        self.assertFalse(self.nia_scheduler._is_optimal_nia_time(evening))
    
    def test_generate_meeting_summary(self):
        """Test meeting summary generation"""
        start_time = timezone.now() - timedelta(hours=2)
        end_time = start_time + timedelta(minutes=45)
        
        meeting = MeetingSession.objects.create(
            organizer=self.user,
            title='NIA Lead Consultation',
            scheduled_start_time=start_time,
            scheduled_end_time=end_time,
            actual_start_time=start_time,
            actual_end_time=end_time,
            status=MeetingSession.Status.ENDED
        )
        
        # Add NIA metadata
        MeetingStatusUpdate.objects.create(
            meeting=meeting,
            update_type=MeetingStatusUpdate.UpdateType.CREATED,
            description='NIA meeting scheduled: lead_consultation',
            metadata={
                'nia_meeting_type': 'lead_consultation',
                'platform': 'google_meet'
            }
        )
        
        summary = self.nia_scheduler.generate_meeting_summary(meeting)
        
        # Should contain required summary fields
        self.assertIn('meeting_id', summary)
        self.assertIn('meeting_type', summary)
        self.assertIn('key_outcomes', summary)
        self.assertIn('action_items', summary)
        self.assertIn('next_steps', summary)
        self.assertIn('nia_recommendations', summary)
        self.assertIn('effectiveness_score', summary)
        
        # Meeting type should be correct
        self.assertEqual(summary['meeting_type'], 'lead_consultation')
        
        # Should have effectiveness score
        self.assertIsInstance(summary['effectiveness_score'], (int, float))
        self.assertGreaterEqual(summary['effectiveness_score'], 0)
        self.assertLessEqual(summary['effectiveness_score'], 10)
    
    def test_calculate_meeting_effectiveness(self):
        """Test meeting effectiveness calculation"""
        start_time = timezone.now() - timedelta(hours=1)
        end_time = start_time + timedelta(minutes=60)
        
        # Create a well-executed meeting
        good_meeting = MeetingSession.objects.create(
            organizer=self.user,
            title='Good NIA Meeting',
            scheduled_start_time=start_time,
            scheduled_end_time=end_time,
            actual_start_time=start_time,  # On time
            actual_end_time=end_time,  # On schedule
            status=MeetingSession.Status.ENDED
        )
        
        effectiveness = self.nia_scheduler._calculate_meeting_effectiveness(good_meeting)
        
        # Should be a reasonable score
        self.assertIsInstance(effectiveness, float)
        self.assertGreaterEqual(effectiveness, 0)
        self.assertLessEqual(effectiveness, 10)
        self.assertGreater(effectiveness, 5)  # Should be above average
    
    def test_get_meeting_analytics(self):
        """Test meeting analytics generation"""
        # Create some test NIA meetings
        now = timezone.now()
        
        for i in range(3):
            start_time = now - timedelta(days=i*7, hours=2)
            end_time = start_time + timedelta(minutes=45)
            
            meeting = MeetingSession.objects.create(
                organizer=self.user,
                title=f'NIA Meeting {i+1}',
                scheduled_start_time=start_time,
                scheduled_end_time=end_time,
                actual_start_time=start_time,
                actual_end_time=end_time,
                status=MeetingSession.Status.ENDED
            )
            
            # Add NIA metadata
            MeetingStatusUpdate.objects.create(
                meeting=meeting,
                update_type=MeetingStatusUpdate.UpdateType.CREATED,
                description='NIA meeting scheduled: general_consultation',
                metadata={'nia_meeting_type': 'general_consultation'}
            )
        
        analytics = self.nia_scheduler.get_meeting_analytics(self.user)
        
        # Should contain analytics structure
        self.assertIn('total_meetings', analytics)
        self.assertIn('completed_meetings', analytics)
        self.assertIn('completion_rate', analytics)
        self.assertIn('meeting_type_distribution', analytics)
        self.assertIn('average_effectiveness_score', analytics)
        self.assertIn('roi_indicators', analytics)
        
        # Should find our test meetings
        self.assertGreaterEqual(analytics['total_meetings'], 3)
        self.assertGreaterEqual(analytics['completed_meetings'], 3)
        
        # Should have type distribution
        self.assertIn('general_consultation', analytics['meeting_type_distribution'])
    
    def test_meeting_templates(self):
        """Test meeting templates configuration"""
        # All meeting types should have templates
        for meeting_type in NIAMeetingType:
            self.assertIn(meeting_type, self.nia_scheduler.meeting_templates)
            
            template = self.nia_scheduler.meeting_templates[meeting_type]
            
            # Each template should have required fields
            self.assertIn('duration', template)
            self.assertIn('agenda_template', template)
            self.assertIn('preparation_items', template)
            
            # Duration should be reasonable
            self.assertGreater(template['duration'], 0)
            self.assertLessEqual(template['duration'], 120)
            
            # Should have preparation items
            self.assertIsInstance(template['preparation_items'], list)
            self.assertGreater(len(template['preparation_items']), 0)


class NIAMeetingIntegrationTestCase(TestCase):
    """Integration tests for NIA meeting functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='niaintegration',
            email='niaintegration@example.com',
            password='testpass123'
        )
        
        self.nia_scheduler = NIAMeetingScheduler()
    
    def test_complete_nia_meeting_workflow(self):
        """Test complete NIA meeting workflow from scheduling to summary"""
        # Step 1: Get available slots
        start_date = timezone.now()
        end_date = start_date + timedelta(days=7)
        
        available_slots = self.nia_scheduler.get_available_time_slots(
            self.user, (start_date, end_date), NIAMeetingType.LEAD_CONSULTATION
        )
        
        self.assertGreater(len(available_slots), 0)
        
        # Step 2: Schedule meeting
        slot = available_slots[0]
        meeting_data = {
            'start_time': slot['start_time'],
            'meeting_type': NIAMeetingType.LEAD_CONSULTATION.value,
            'platform': 'google_meet'
        }
        
        # Mock the meeting creation
        with patch.object(self.nia_scheduler.google_service, 'create_meeting') as mock_create:
            mock_meeting = MeetingSession.objects.create(
                organizer=self.user,
                title='NIA Lead Consultation',
                scheduled_start_time=slot['start_time'],
                scheduled_end_time=slot['end_time'],
                meeting_type=MeetingSession.MeetingType.GOOGLE_MEET,
                status=MeetingSession.Status.SCHEDULED
            )
            mock_create.return_value = mock_meeting
            
            meeting_session = self.nia_scheduler.schedule_nia_meeting(self.user, meeting_data)
            
            self.assertIsNotNone(meeting_session)
            
            # Step 3: Simulate meeting completion
            meeting_session.status = MeetingSession.Status.ENDED
            meeting_session.actual_start_time = meeting_session.scheduled_start_time
            meeting_session.actual_end_time = meeting_session.scheduled_end_time
            meeting_session.save()
            
            # Step 4: Generate summary
            summary = self.nia_scheduler.generate_meeting_summary(meeting_session)
            
            self.assertIn('meeting_id', summary)
            self.assertIn('key_outcomes', summary)
            self.assertIn('action_items', summary)
            
            # Step 5: Get analytics
            analytics = self.nia_scheduler.get_meeting_analytics(self.user)
            
            self.assertGreaterEqual(analytics['total_meetings'], 1)
            self.assertGreaterEqual(analytics['completed_meetings'], 1)
    
    def test_nia_meeting_with_lead_context(self):
        """Test NIA meeting with lead context integration"""
        # This test would require AI service integration
        # For now, test the basic functionality without lead context
        
        meeting_data = {
            'start_time': timezone.now() + timedelta(hours=2),
            'meeting_type': NIAMeetingType.LEAD_CONSULTATION.value,
            'platform': 'google_meet',
            'lead_id': 'test-lead-id'  # This would be a real lead ID in practice
        }
        
        # Mock the meeting creation
        with patch.object(self.nia_scheduler.google_service, 'create_meeting') as mock_create:
            mock_meeting = MeetingSession.objects.create(
                organizer=self.user,
                title='NIA Lead Consultation',
                scheduled_start_time=meeting_data['start_time'],
                scheduled_end_time=meeting_data['start_time'] + timedelta(minutes=45),
                meeting_type=MeetingSession.MeetingType.GOOGLE_MEET
            )
            mock_create.return_value = mock_meeting
            
            meeting_session = self.nia_scheduler.schedule_nia_meeting(self.user, meeting_data)
            
            self.assertIsNotNone(meeting_session)
            
            # Check that lead context was stored in metadata
            nia_updates = meeting_session.status_updates.filter(
                description__icontains='NIA meeting'
            )
            self.assertGreater(nia_updates.count(), 0)
            
            nia_update = nia_updates.first()
            self.assertEqual(nia_update.metadata.get('lead_id'), 'test-lead-id')