import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from .google_meet_service import GoogleMeetService
from .microsoft_teams_service import MicrosoftTeamsService
from .models import (
    GoogleMeetCredentials,
    MeetingSession,
    MeetingStatusUpdate,
    MicrosoftTeamsCredentials,
)

User = get_user_model()
logger = logging.getLogger(__name__)


class IntelligentMeetingService:
    """Service for intelligent meeting management, scheduling, and follow-up"""

    def __init__(self):
        self.google_service = GoogleMeetService()
        self.teams_service = MicrosoftTeamsService()

        # Configuration for intelligent scheduling
        self.max_daily_meetings = 3
        self.min_meeting_gap_minutes = 15
        self.preferred_meeting_hours = (9, 17)  # 9 AM to 5 PM
        self.post_meeting_delay_minutes = 30
        self.late_meeting_threshold_minutes = 15

    def analyze_user_availability(
        self, user: User, date_range: Tuple[datetime, datetime]
    ) -> Dict:
        """Analyze user's meeting patterns and availability"""
        try:
            start_date, end_date = date_range

            # Get user's meetings in the date range
            meetings = MeetingSession.objects.filter(
                Q(organizer=user) | Q(participants__user=user),
                scheduled_start_time__gte=start_date,
                scheduled_start_time__lte=end_date,
            ).distinct()

            # Analyze meeting patterns
            daily_counts = defaultdict(int)
            hourly_distribution = defaultdict(int)
            duration_stats = []

            for meeting in meetings:
                # Daily meeting count
                date_key = meeting.scheduled_start_time.date()
                daily_counts[date_key] += 1

                # Hourly distribution
                hour_key = meeting.scheduled_start_time.hour
                hourly_distribution[hour_key] += 1

                # Duration statistics
                if meeting.duration_minutes > 0:
                    duration_stats.append(meeting.duration_minutes)

            # Calculate statistics
            avg_daily_meetings = sum(daily_counts.values()) / max(len(daily_counts), 1)
            peak_hours = sorted(
                hourly_distribution.items(), key=lambda x: x[1], reverse=True
            )[:3]
            avg_duration = (
                sum(duration_stats) / max(len(duration_stats), 1)
                if duration_stats
                else 60
            )

            # Find available time slots
            available_slots = self._find_available_slots(
                user, start_date, end_date, meetings
            )

            return {
                "total_meetings": len(meetings),
                "avg_daily_meetings": round(avg_daily_meetings, 2),
                "peak_hours": [hour for hour, count in peak_hours],
                "avg_duration_minutes": round(avg_duration, 2),
                "daily_counts": dict(daily_counts),
                "available_slots": available_slots,
                "meeting_load": self._calculate_meeting_load(daily_counts),
            }

        except Exception as e:
            logger.error(f"Error analyzing user availability: {str(e)}")
            return {}

    def _find_available_slots(
        self,
        user: User,
        start_date: datetime,
        end_date: datetime,
        existing_meetings: List[MeetingSession],
    ) -> List[Dict]:
        """Find available time slots for meetings"""
        available_slots = []

        # Create a list of busy time periods
        busy_periods = []
        for meeting in existing_meetings:
            busy_periods.append(
                {
                    "start": meeting.scheduled_start_time,
                    "end": meeting.scheduled_end_time,
                }
            )

        # Sort busy periods by start time
        busy_periods.sort(key=lambda x: x["start"])

        # Find gaps between meetings
        current_time = start_date.replace(
            hour=self.preferred_meeting_hours[0], minute=0, second=0, microsecond=0
        )
        end_time = end_date.replace(
            hour=self.preferred_meeting_hours[1], minute=0, second=0, microsecond=0
        )

        while current_time < end_time:
            # Check if current time is during business hours
            if (
                self.preferred_meeting_hours[0]
                <= current_time.hour
                < self.preferred_meeting_hours[1]
            ):
                # Check if this slot conflicts with existing meetings
                slot_end = current_time + timedelta(hours=1)  # Default 1-hour slot

                is_available = True
                for busy_period in busy_periods:
                    if (
                        current_time < busy_period["end"]
                        and slot_end > busy_period["start"]
                    ):
                        is_available = False
                        break

                if is_available:
                    available_slots.append(
                        {"start": current_time, "end": slot_end, "duration_minutes": 60}
                    )

            current_time += timedelta(minutes=30)  # Check every 30 minutes

        return available_slots[:10]  # Return top 10 available slots

    def _calculate_meeting_load(self, daily_counts: Dict) -> str:
        """Calculate meeting load level"""
        if not daily_counts:
            return "light"

        avg_daily = sum(daily_counts.values()) / len(daily_counts)

        if avg_daily <= 1:
            return "light"
        elif avg_daily <= 3:
            return "moderate"
        else:
            return "heavy"

    def recommend_meeting_time(
        self, user: User, duration_minutes: int = 60, preferred_date: datetime = None
    ) -> List[Dict]:
        """Recommend optimal meeting times based on user patterns"""
        try:
            # Default to next 7 days if no preferred date
            if not preferred_date:
                preferred_date = timezone.now()

            start_range = preferred_date
            end_range = preferred_date + timedelta(days=7)

            # Analyze user availability
            availability = self.analyze_user_availability(
                user, (start_range, end_range)
            )

            # Get user's peak hours for better recommendations
            peak_hours = availability.get("peak_hours", [10, 14, 16])

            recommendations = []

            # Generate recommendations based on available slots and peak hours
            for slot in availability.get("available_slots", []):
                slot_hour = slot["start"].hour

                # Score the slot based on various factors
                score = 0

                # Prefer peak hours
                if slot_hour in peak_hours:
                    score += 30

                # Prefer business hours
                if (
                    self.preferred_meeting_hours[0]
                    <= slot_hour
                    < self.preferred_meeting_hours[1]
                ):
                    score += 20

                # Prefer not too early or too late
                if 10 <= slot_hour <= 15:
                    score += 15

                # Check if it's not overloading the day
                date_key = slot["start"].date()
                daily_count = availability.get("daily_counts", {}).get(date_key, 0)
                if daily_count < self.max_daily_meetings:
                    score += 25
                else:
                    score -= 20

                recommendations.append(
                    {
                        "start_time": slot["start"],
                        "end_time": slot["start"] + timedelta(minutes=duration_minutes),
                        "score": score,
                        "reason": self._generate_recommendation_reason(
                            slot, peak_hours, daily_count
                        ),
                    }
                )

            # Sort by score and return top recommendations
            recommendations.sort(key=lambda x: x["score"], reverse=True)
            return recommendations[:5]

        except Exception as e:
            logger.error(f"Error recommending meeting time: {str(e)}")
            return []

    def _generate_recommendation_reason(
        self, slot: Dict, peak_hours: List[int], daily_count: int
    ) -> str:
        """Generate human-readable reason for recommendation"""
        reasons = []

        slot_hour = slot["start"].hour

        if slot_hour in peak_hours:
            reasons.append("matches your typical meeting hours")

        if 10 <= slot_hour <= 15:
            reasons.append("optimal time for productivity")

        if daily_count < 2:
            reasons.append("light meeting day")
        elif daily_count < self.max_daily_meetings:
            reasons.append("manageable meeting load")

        if not reasons:
            reasons.append("available time slot")

        return ", ".join(reasons)

    def detect_meeting_conflicts(
        self, user: User, proposed_meeting: Dict
    ) -> List[Dict]:
        """Detect conflicts with existing meetings"""
        try:
            start_time = proposed_meeting["start_time"]
            end_time = proposed_meeting["end_time"]

            # Find overlapping meetings
            conflicts = MeetingSession.objects.filter(
                Q(organizer=user) | Q(participants__user=user),
                scheduled_start_time__lt=end_time,
                scheduled_end_time__gt=start_time,
                status__in=[
                    MeetingSession.Status.SCHEDULED,
                    MeetingSession.Status.ACTIVE,
                ],
            ).distinct()

            conflict_details = []
            for conflict in conflicts:
                conflict_details.append(
                    {
                        "meeting_id": str(conflict.id),
                        "title": conflict.title,
                        "start_time": conflict.scheduled_start_time,
                        "end_time": conflict.scheduled_end_time,
                        "meeting_type": conflict.meeting_type,
                        "overlap_minutes": self._calculate_overlap_minutes(
                            start_time,
                            end_time,
                            conflict.scheduled_start_time,
                            conflict.scheduled_end_time,
                        ),
                    }
                )

            return conflict_details

        except Exception as e:
            logger.error(f"Error detecting meeting conflicts: {str(e)}")
            return []

    def _calculate_overlap_minutes(
        self, start1: datetime, end1: datetime, start2: datetime, end2: datetime
    ) -> int:
        """Calculate overlap between two time periods in minutes"""
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)

        if overlap_start < overlap_end:
            return int((overlap_end - overlap_start).total_seconds() / 60)
        return 0

    def suggest_reschedule_options(
        self, user: User, conflicted_meeting: MeetingSession
    ) -> List[Dict]:
        """Suggest alternative times for a conflicted meeting"""
        try:
            # Get meeting duration
            duration = conflicted_meeting.duration_minutes or 60

            # Look for alternatives in the next 14 days
            start_range = timezone.now()
            end_range = start_range + timedelta(days=14)

            # Get recommendations
            recommendations = self.recommend_meeting_time(user, duration)

            # Filter out times that are too close to the original time
            original_time = conflicted_meeting.scheduled_start_time
            filtered_recommendations = []

            for rec in recommendations:
                time_diff = abs(
                    (rec["start_time"] - original_time).total_seconds() / 3600
                )
                if time_diff >= 1:  # At least 1 hour difference
                    filtered_recommendations.append(
                        {
                            "start_time": rec["start_time"],
                            "end_time": rec["end_time"],
                            "score": rec["score"],
                            "reason": rec["reason"],
                            "time_difference_hours": round(time_diff, 1),
                        }
                    )

            return filtered_recommendations[:3]  # Top 3 alternatives

        except Exception as e:
            logger.error(f"Error suggesting reschedule options: {str(e)}")
            return []

    def schedule_post_meeting_follow_up(self, meeting: MeetingSession) -> bool:
        """Schedule intelligent follow-up actions after a meeting"""
        try:
            # Calculate follow-up time (30 minutes after meeting ends)
            follow_up_time = meeting.scheduled_end_time + timedelta(
                minutes=self.post_meeting_delay_minutes
            )

            # Check if meeting ran late
            actual_end = meeting.actual_end_time or meeting.scheduled_end_time
            if actual_end > meeting.scheduled_end_time:
                late_minutes = int(
                    (actual_end - meeting.scheduled_end_time).total_seconds() / 60
                )
                if late_minutes > self.late_meeting_threshold_minutes:
                    # Adjust follow-up time for late meetings
                    follow_up_time = actual_end + timedelta(
                        minutes=self.post_meeting_delay_minutes
                    )

            # Create follow-up status update
            MeetingStatusUpdate.objects.create(
                meeting=meeting,
                update_type=MeetingStatusUpdate.UpdateType.CREATED,  # Using existing type
                description=f"Follow-up scheduled for {follow_up_time.strftime('%Y-%m-%d %H:%M')}",
                metadata={
                    "follow_up_time": follow_up_time.isoformat(),
                    "follow_up_type": "post_meeting",
                    "late_minutes": late_minutes if "late_minutes" in locals() else 0,
                },
            )

            logger.info(
                f"Scheduled follow-up for meeting {meeting.id} at {follow_up_time}"
            )
            return True

        except Exception as e:
            logger.error(f"Error scheduling post-meeting follow-up: {str(e)}")
            return False

    def analyze_meeting_patterns(self, user: User, days_back: int = 30) -> Dict:
        """Analyze user's meeting patterns for optimization"""
        try:
            # Get meetings from the last N days
            start_date = timezone.now() - timedelta(days=days_back)
            end_date = timezone.now()

            meetings = MeetingSession.objects.filter(
                Q(organizer=user) | Q(participants__user=user),
                scheduled_start_time__gte=start_date,
                scheduled_start_time__lte=end_date,
            ).distinct()

            # Analyze patterns
            patterns = {
                "total_meetings": meetings.count(),
                "avg_duration": 0,
                "most_productive_hours": [],
                "meeting_frequency_by_day": defaultdict(int),
                "late_meetings_count": 0,
                "cancelled_meetings_count": 0,
                "meeting_types_distribution": defaultdict(int),
            }

            durations = []
            hourly_productivity = defaultdict(list)

            for meeting in meetings:
                # Duration analysis
                if meeting.duration_minutes:
                    durations.append(meeting.duration_minutes)

                # Day of week analysis
                day_name = meeting.scheduled_start_time.strftime("%A")
                patterns["meeting_frequency_by_day"][day_name] += 1

                # Hour analysis with productivity score
                hour = meeting.scheduled_start_time.hour
                productivity_score = self._calculate_meeting_productivity_score(meeting)
                hourly_productivity[hour].append(productivity_score)

                # Late meetings
                if meeting.actual_start_time and meeting.scheduled_start_time:
                    delay_minutes = (
                        meeting.actual_start_time - meeting.scheduled_start_time
                    ).total_seconds() / 60
                    if delay_minutes > self.late_meeting_threshold_minutes:
                        patterns["late_meetings_count"] += 1

                # Cancelled meetings
                if meeting.status == MeetingSession.Status.CANCELLED:
                    patterns["cancelled_meetings_count"] += 1

                # Meeting type distribution
                patterns["meeting_types_distribution"][meeting.meeting_type] += 1

            # Calculate averages and insights
            if durations:
                patterns["avg_duration"] = round(sum(durations) / len(durations), 2)

            # Find most productive hours
            productive_hours = []
            for hour, scores in hourly_productivity.items():
                if scores:
                    avg_score = sum(scores) / len(scores)
                    productive_hours.append((hour, avg_score))

            productive_hours.sort(key=lambda x: x[1], reverse=True)
            patterns["most_productive_hours"] = [
                hour for hour, score in productive_hours[:3]
            ]

            # Generate recommendations
            patterns["recommendations"] = self._generate_pattern_recommendations(
                patterns
            )

            return patterns

        except Exception as e:
            logger.error(f"Error analyzing meeting patterns: {str(e)}")
            return {}

    def _calculate_meeting_productivity_score(self, meeting: MeetingSession) -> float:
        """Calculate a productivity score for a meeting based on various factors"""
        score = 5.0  # Base score

        # Factor in meeting duration (optimal around 30-60 minutes)
        duration = meeting.duration_minutes or 60
        if 30 <= duration <= 60:
            score += 2
        elif duration > 120:
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

        # Factor in completion status
        if meeting.status == MeetingSession.Status.ENDED:
            score += 1
        elif meeting.status == MeetingSession.Status.CANCELLED:
            score -= 2

        # Factor in participant engagement (based on participation duration)
        participants = meeting.participants.all()
        if participants:
            engagement_scores = []
            for participant in participants:
                if participant.participation_duration_minutes > 0:
                    engagement_ratio = (
                        participant.participation_duration_minutes / duration
                    )
                    engagement_scores.append(min(engagement_ratio, 1.0))

            if engagement_scores:
                avg_engagement = sum(engagement_scores) / len(engagement_scores)
                score += avg_engagement * 2

        return max(0, min(10, score))  # Clamp between 0 and 10

    def _generate_pattern_recommendations(self, patterns: Dict) -> List[str]:
        """Generate recommendations based on meeting patterns"""
        recommendations = []

        # Duration recommendations
        avg_duration = patterns.get("avg_duration", 60)
        if avg_duration > 90:
            recommendations.append(
                "Consider shorter meetings - your average is longer than optimal"
            )
        elif avg_duration < 30:
            recommendations.append(
                "Your meetings might benefit from slightly longer durations for better outcomes"
            )

        # Frequency recommendations
        total_meetings = patterns.get("total_meetings", 0)
        if total_meetings > 60:  # More than 2 per day on average
            recommendations.append(
                "High meeting frequency detected - consider consolidating or declining some meetings"
            )

        # Late meetings
        late_count = patterns.get("late_meetings_count", 0)
        if late_count > total_meetings * 0.2:  # More than 20% late
            recommendations.append(
                "Consider adding buffer time between meetings to reduce delays"
            )

        # Productive hours
        productive_hours = patterns.get("most_productive_hours", [])
        if productive_hours:
            hours_str = ", ".join([f"{h}:00" for h in productive_hours])
            recommendations.append(
                f"Schedule important meetings during your most productive hours: {hours_str}"
            )

        # Meeting type balance
        types_dist = patterns.get("meeting_types_distribution", {})
        if len(types_dist) == 1:
            recommendations.append(
                "Consider diversifying meeting platforms for different types of interactions"
            )

        return recommendations

    def get_calendar_sync_status(self, user: User) -> Dict:
        """Get the status of calendar integrations for the user"""
        try:
            status = {
                "google_calendar": False,
                "outlook_calendar": False,
                "teams_calendar": False,
                "last_sync": None,
                "sync_errors": [],
            }

            # Check Google Calendar integration
            try:
                google_creds = GoogleMeetCredentials.objects.get(user=user)
                status["google_calendar"] = not google_creds.is_token_expired()
            except GoogleMeetCredentials.DoesNotExist:
                pass

            # Check Teams/Outlook integration
            try:
                teams_creds = MicrosoftTeamsCredentials.objects.get(user=user)
                status["teams_calendar"] = not teams_creds.is_token_expired()
                status["outlook_calendar"] = status[
                    "teams_calendar"
                ]  # Same credentials
            except MicrosoftTeamsCredentials.DoesNotExist:
                pass

            # Get last sync time from most recent meeting
            last_meeting = (
                MeetingSession.objects.filter(
                    Q(organizer=user) | Q(participants__user=user)
                )
                .order_by("-updated_at")
                .first()
            )

            if last_meeting:
                status["last_sync"] = last_meeting.updated_at

            return status

        except Exception as e:
            logger.error(f"Error getting calendar sync status: {str(e)}")
            return {"error": str(e)}
