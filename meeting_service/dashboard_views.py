from datetime import timedelta
from typing import Any, Dict, List

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Avg
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from .models import Meeting, MeetingQuestion


@staff_member_required
def meeting_dashboard_view(request):
    """Main meeting dashboard view"""
    return render(
        request,
        "admin/meeting_service/meeting_dashboard.html",
        {
            "title": "Meeting Analytics Dashboard",
        },
    )


@staff_member_required
def dashboard_metrics_api(request):
    """API endpoint for key dashboard metrics"""
    try:
        # Calculate date ranges
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        sixty_days_ago = now - timedelta(days=60)

        # Current period metrics
        current_meetings = Meeting.objects.filter(created_at__gte=thirty_days_ago)
        previous_meetings = Meeting.objects.filter(
            created_at__gte=sixty_days_ago, created_at__lt=thirty_days_ago
        )

        # Total meetings
        total_meetings = current_meetings.count()
        previous_total = previous_meetings.count()
        meetings_change = calculate_percentage_change(total_meetings, previous_total)

        # Conversion rate (meetings that led to opportunities)
        converted_meetings = current_meetings.filter(
            lead__status__in=["qualified", "converted"]
        ).count()
        conversion_rate = (
            (converted_meetings / total_meetings * 100) if total_meetings > 0 else 0
        )

        previous_converted = previous_meetings.filter(
            lead__status__in=["qualified", "converted"]
        ).count()
        previous_conversion_rate = (
            (previous_converted / previous_total * 100) if previous_total > 0 else 0
        )
        conversion_change = conversion_rate - previous_conversion_rate

        # Upcoming meetings
        upcoming_meetings = Meeting.objects.filter(
            status="scheduled", scheduled_at__gt=now
        ).count()

        # Average duration
        avg_duration = (
            current_meetings.filter(actual_duration_minutes__isnull=False).aggregate(
                avg=Avg("actual_duration_minutes")
            )["avg"]
            or 0
        )

        previous_avg_duration = (
            previous_meetings.filter(actual_duration_minutes__isnull=False).aggregate(
                avg=Avg("actual_duration_minutes")
            )["avg"]
            or 0
        )
        duration_change = calculate_percentage_change(
            avg_duration, previous_avg_duration
        )

        # AI effectiveness (based on question effectiveness scores)
        ai_effectiveness = calculate_ai_effectiveness(current_meetings)
        previous_ai_effectiveness = calculate_ai_effectiveness(previous_meetings)
        ai_change = ai_effectiveness - previous_ai_effectiveness

        # Preparation score (based on pre-meeting intelligence usage)
        preparation_score = calculate_preparation_score(current_meetings)
        previous_preparation_score = calculate_preparation_score(previous_meetings)
        prep_change = preparation_score - previous_preparation_score

        return JsonResponse(
            {
                "total_meetings": total_meetings,
                "meetings_change": meetings_change,
                "conversion_rate": round(conversion_rate, 1),
                "conversion_change": round(conversion_change, 1),
                "upcoming_meetings": upcoming_meetings,
                "upcoming_change": 0,  # Would need historical tracking
                "avg_duration": round(avg_duration, 0),
                "duration_change": round(duration_change, 1),
                "ai_effectiveness": round(ai_effectiveness, 1),
                "ai_change": round(ai_change, 1),
                "preparation_score": round(preparation_score, 1),
                "prep_change": round(prep_change, 1),
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@staff_member_required
def dashboard_upcoming_meetings_api(request):
    """API endpoint for upcoming meetings with preparation status"""
    try:
        now = timezone.now()
        upcoming_meetings = (
            Meeting.objects.filter(status="scheduled", scheduled_at__gt=now)
            .select_related("lead")
            .order_by("scheduled_at")[:10]
        )

        meetings_data = []
        for meeting in upcoming_meetings:
            # Calculate preparation status
            prep_status = calculate_meeting_preparation_status(meeting)

            meetings_data.append(
                {
                    "id": str(meeting.id),
                    "title": meeting.title,
                    "scheduled_at": meeting.scheduled_at.strftime("%Y-%m-%d %H:%M"),
                    "company_name": (
                        meeting.lead.company_name if meeting.lead else "No Lead"
                    ),
                    "meeting_type": meeting.get_meeting_type_display(),
                    "duration_minutes": meeting.duration_minutes,
                    "status": meeting.status,
                    "status_display": meeting.get_status_display(),
                    "preparation_status": prep_status["status"],
                    "preparation_status_display": prep_status["display"],
                    "preparation_details": prep_status["details"],
                }
            )

        return JsonResponse({"meetings": meetings_data})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@staff_member_required
def dashboard_performance_metrics_api(request):
    """API endpoint for meeting performance metrics"""
    try:
        # Get performance metrics by meeting type
        meeting_types = Meeting.MeetingType.choices
        metrics_data = []

        for meeting_type_code, meeting_type_name in meeting_types:
            meetings = Meeting.objects.filter(meeting_type=meeting_type_code)

            if meetings.exists():
                total_meetings = meetings.count()
                completed_meetings = meetings.filter(status="completed")

                # Average duration
                avg_duration = (
                    completed_meetings.aggregate(avg=Avg("actual_duration_minutes"))[
                        "avg"
                    ]
                    or 0
                )

                # Conversion rate
                converted_count = meetings.filter(
                    lead__status__in=["qualified", "converted"]
                ).count()
                conversion_rate = (
                    (converted_count / total_meetings * 100)
                    if total_meetings > 0
                    else 0
                )

                # Success rate (completed vs scheduled)
                success_rate = (
                    (completed_meetings.count() / total_meetings * 100)
                    if total_meetings > 0
                    else 0
                )

                # Effectiveness (based on AI insights and outcomes)
                effectiveness = calculate_meeting_type_effectiveness(meeting_type_code)

                metrics_data.append(
                    {
                        "meeting_type": meeting_type_name,
                        "total_meetings": total_meetings,
                        "avg_duration": round(avg_duration, 0),
                        "conversion_rate": round(conversion_rate, 1),
                        "success_rate": round(success_rate, 1),
                        "effectiveness": round(effectiveness, 1),
                    }
                )

        # Generate chart data for performance trends
        chart_data = generate_performance_chart_data()

        return JsonResponse({"metrics": metrics_data, "chart_data": chart_data})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@staff_member_required
def dashboard_ai_effectiveness_api(request):
    """API endpoint for AI recommendation effectiveness tracking"""
    try:
        effectiveness_data = []

        # Pre-meeting intelligence effectiveness
        prep_effectiveness = calculate_feature_effectiveness("preparation_materials")
        effectiveness_data.append(
            {
                "feature_name": "Pre-meeting Intelligence",
                "usage_count": prep_effectiveness["usage_count"],
                "success_rate": prep_effectiveness["success_rate"],
                "effectiveness": prep_effectiveness["effectiveness"],
                "conversion_impact": prep_effectiveness["conversion_impact"],
                "trend_direction": prep_effectiveness["trend_direction"],
                "trend_indicator": prep_effectiveness["trend_indicator"],
            }
        )

        # Meeting questions effectiveness
        questions_effectiveness = calculate_feature_effectiveness("meeting_questions")
        effectiveness_data.append(
            {
                "feature_name": "AI-Generated Questions",
                "usage_count": questions_effectiveness["usage_count"],
                "success_rate": questions_effectiveness["success_rate"],
                "effectiveness": questions_effectiveness["effectiveness"],
                "conversion_impact": questions_effectiveness["conversion_impact"],
                "trend_direction": questions_effectiveness["trend_direction"],
                "trend_indicator": questions_effectiveness["trend_indicator"],
            }
        )

        # Meeting outcomes effectiveness
        outcomes_effectiveness = calculate_feature_effectiveness("meeting_outcomes")
        effectiveness_data.append(
            {
                "feature_name": "Outcome Analysis",
                "usage_count": outcomes_effectiveness["usage_count"],
                "success_rate": outcomes_effectiveness["success_rate"],
                "effectiveness": outcomes_effectiveness["effectiveness"],
                "conversion_impact": outcomes_effectiveness["conversion_impact"],
                "trend_direction": outcomes_effectiveness["trend_direction"],
                "trend_indicator": outcomes_effectiveness["trend_indicator"],
            }
        )

        # Lead scoring updates effectiveness
        scoring_effectiveness = calculate_feature_effectiveness("lead_scoring")
        effectiveness_data.append(
            {
                "feature_name": "Lead Scoring Updates",
                "usage_count": scoring_effectiveness["usage_count"],
                "success_rate": scoring_effectiveness["success_rate"],
                "effectiveness": scoring_effectiveness["effectiveness"],
                "conversion_impact": scoring_effectiveness["conversion_impact"],
                "trend_direction": scoring_effectiveness["trend_direction"],
                "trend_indicator": scoring_effectiveness["trend_indicator"],
            }
        )

        return JsonResponse({"effectiveness_data": effectiveness_data})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@staff_member_required
def dashboard_conversion_analytics_api(request):
    """API endpoint for conversion analytics"""
    try:
        # Conversion funnel data
        total_meetings = Meeting.objects.count()
        scheduled_meetings = Meeting.objects.filter(status="scheduled").count()
        completed_meetings = Meeting.objects.filter(status="completed").count()
        qualified_leads = Meeting.objects.filter(lead__status="qualified").count()
        converted_leads = Meeting.objects.filter(lead__status="converted").count()

        funnel_data = [
            {"stage": "Total Meetings", "count": total_meetings, "percentage": 100},
            {
                "stage": "Completed Meetings",
                "count": completed_meetings,
                "percentage": round(
                    (
                        (completed_meetings / total_meetings * 100)
                        if total_meetings > 0
                        else 0
                    ),
                    1,
                ),
            },
            {
                "stage": "Qualified Leads",
                "count": qualified_leads,
                "percentage": round(
                    (
                        (qualified_leads / total_meetings * 100)
                        if total_meetings > 0
                        else 0
                    ),
                    1,
                ),
            },
            {
                "stage": "Converted Leads",
                "count": converted_leads,
                "percentage": round(
                    (
                        (converted_leads / total_meetings * 100)
                        if total_meetings > 0
                        else 0
                    ),
                    1,
                ),
            },
        ]

        # Top converting meeting types
        meeting_types_conversion = []
        for meeting_type_code, meeting_type_name in Meeting.MeetingType.choices:
            meetings = Meeting.objects.filter(meeting_type=meeting_type_code)
            if meetings.exists():
                converted = meetings.filter(
                    lead__status__in=["qualified", "converted"]
                ).count()
                conversion_rate = (
                    (converted / meetings.count() * 100) if meetings.count() > 0 else 0
                )

                meeting_types_conversion.append(
                    {
                        "meeting_type": meeting_type_name,
                        "conversion_rate": round(conversion_rate, 1),
                    }
                )

        # Sort by conversion rate
        meeting_types_conversion.sort(key=lambda x: x["conversion_rate"], reverse=True)

        # Generate chart data
        chart_data = {
            "labels": [item["meeting_type"] for item in meeting_types_conversion[:5]],
            "data": [item["conversion_rate"] for item in meeting_types_conversion[:5]],
        }

        return JsonResponse(
            {
                "conversion_data": {
                    "funnel": funnel_data,
                    "top_types": meeting_types_conversion[:5],
                },
                "chart_data": chart_data,
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# Helper functions


def calculate_percentage_change(current: float, previous: float) -> float:
    """Calculate percentage change between two values"""
    if previous == 0:
        return 100 if current > 0 else 0
    return round(((current - previous) / previous) * 100, 1)


def calculate_ai_effectiveness(meetings_queryset) -> float:
    """Calculate overall AI effectiveness for a set of meetings"""
    if not meetings_queryset.exists():
        return 0

    # Get all questions for these meetings
    questions = MeetingQuestion.objects.filter(
        meeting__in=meetings_queryset, effectiveness_score__isnull=False
    )

    if not questions.exists():
        return 0

    avg_effectiveness = questions.aggregate(avg=Avg("effectiveness_score"))["avg"]
    return avg_effectiveness or 0


def calculate_preparation_score(meetings_queryset) -> float:
    """Calculate preparation score based on pre-meeting intelligence usage"""
    if not meetings_queryset.exists():
        return 0

    total_meetings = meetings_queryset.count()
    prepared_meetings = 0

    for meeting in meetings_queryset:
        # Check if meeting has preparation materials
        ai_insights = meeting.ai_insights or {}
        if (
            ai_insights.get("agenda")
            or ai_insights.get("talking_points")
            or ai_insights.get("preparation_materials")
        ):
            prepared_meetings += 1

    return (prepared_meetings / total_meetings * 100) if total_meetings > 0 else 0


def calculate_meeting_preparation_status(meeting) -> Dict[str, str]:
    """Calculate preparation status for a specific meeting"""
    ai_insights = meeting.ai_insights or {}

    preparation_items = [
        ai_insights.get("agenda"),
        ai_insights.get("talking_points"),
        ai_insights.get("preparation_materials"),
        ai_insights.get("competitive_analysis"),
    ]

    completed_items = sum(1 for item in preparation_items if item)
    total_items = len(preparation_items)

    if completed_items == total_items:
        return {
            "status": "complete",
            "display": "Fully Prepared",
            "details": f"{completed_items}/{total_items} items completed",
        }
    elif completed_items > 0:
        return {
            "status": "partial",
            "display": "Partially Prepared",
            "details": f"{completed_items}/{total_items} items completed",
        }
    else:
        return {
            "status": "pending",
            "display": "Preparation Pending",
            "details": f"{completed_items}/{total_items} items completed",
        }


def calculate_meeting_type_effectiveness(meeting_type: str) -> float:
    """Calculate effectiveness for a specific meeting type"""
    meetings = Meeting.objects.filter(meeting_type=meeting_type, status="completed")

    if not meetings.exists():
        return 0

    # Calculate based on multiple factors
    total_score = 0
    scored_meetings = 0

    for meeting in meetings:
        meeting_score = 0
        factors = 0

        # Factor 1: Lead conversion
        if meeting.lead and meeting.lead.status in ["qualified", "converted"]:
            meeting_score += 30
        factors += 1

        # Factor 2: Meeting completion vs scheduled duration
        if meeting.actual_duration_minutes and meeting.duration_minutes:
            duration_ratio = meeting.actual_duration_minutes / meeting.duration_minutes
            if 0.8 <= duration_ratio <= 1.2:  # Within 20% of planned duration
                meeting_score += 25
        factors += 1

        # Factor 3: AI insights quality
        ai_insights = meeting.ai_insights or {}
        if ai_insights.get("outcome") or ai_insights.get("action_items"):
            meeting_score += 25
        factors += 1

        # Factor 4: Question effectiveness
        questions = meeting.questions.filter(effectiveness_score__isnull=False)
        if questions.exists():
            avg_question_score = questions.aggregate(avg=Avg("effectiveness_score"))[
                "avg"
            ]
            meeting_score += (avg_question_score / 100) * 20
        factors += 1

        if factors > 0:
            total_score += meeting_score
            scored_meetings += 1

    return (total_score / scored_meetings) if scored_meetings > 0 else 0


def calculate_feature_effectiveness(feature_name: str) -> Dict[str, Any]:
    """Calculate effectiveness metrics for a specific AI feature"""
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    # Default values
    result = {
        "usage_count": 0,
        "success_rate": 0,
        "effectiveness": 0,
        "conversion_impact": 0,
        "trend_direction": "neutral",
        "trend_indicator": "➡️",
    }

    if feature_name == "preparation_materials":
        # Count meetings with preparation materials
        meetings_with_prep = Meeting.objects.filter(
            created_at__gte=thirty_days_ago,
            ai_insights__has_key="preparation_materials",
        )
        result["usage_count"] = meetings_with_prep.count()

        if meetings_with_prep.exists():
            # Success rate based on meeting completion
            completed = meetings_with_prep.filter(status="completed").count()
            result["success_rate"] = round((completed / result["usage_count"] * 100), 1)

            # Effectiveness based on lead conversion
            converted = meetings_with_prep.filter(
                lead__status__in=["qualified", "converted"]
            ).count()
            result["effectiveness"] = round(
                (converted / result["usage_count"] * 100), 1
            )

            # Conversion impact (compared to meetings without prep)
            meetings_without_prep = Meeting.objects.filter(
                created_at__gte=thirty_days_ago
            ).exclude(ai_insights__has_key="preparation_materials")

            if meetings_without_prep.exists():
                without_prep_conversion = (
                    meetings_without_prep.filter(
                        lead__status__in=["qualified", "converted"]
                    ).count()
                    / meetings_without_prep.count()
                    * 100
                )

                result["conversion_impact"] = round(
                    result["effectiveness"] - without_prep_conversion, 1
                )

    elif feature_name == "meeting_questions":
        # Count meetings with AI-generated questions
        meetings_with_questions = Meeting.objects.filter(
            created_at__gte=thirty_days_ago, questions__ai_generated=True
        ).distinct()
        result["usage_count"] = meetings_with_questions.count()

        if meetings_with_questions.exists():
            # Success rate based on questions asked
            questions_asked = MeetingQuestion.objects.filter(
                meeting__in=meetings_with_questions, asked_at__isnull=False
            ).count()
            total_questions = MeetingQuestion.objects.filter(
                meeting__in=meetings_with_questions
            ).count()
            result["success_rate"] = round(
                (questions_asked / total_questions * 100) if total_questions > 0 else 0,
                1,
            )

            # Effectiveness based on average question effectiveness
            avg_effectiveness = MeetingQuestion.objects.filter(
                meeting__in=meetings_with_questions, effectiveness_score__isnull=False
            ).aggregate(avg=Avg("effectiveness_score"))["avg"]
            result["effectiveness"] = round(avg_effectiveness or 0, 1)

    # Add trend calculation logic here
    result["trend_direction"] = (
        "positive"
        if result["effectiveness"] > 70
        else "negative" if result["effectiveness"] < 50 else "neutral"
    )
    result["trend_indicator"] = (
        "↗️"
        if result["trend_direction"] == "positive"
        else "↘️" if result["trend_direction"] == "negative" else "➡️"
    )

    return result


def generate_performance_chart_data() -> Dict[str, List]:
    """Generate chart data for performance trends"""
    # Get last 7 days of data
    now = timezone.now()
    dates = []
    success_rates = []

    for i in range(6, -1, -1):
        date = now - timedelta(days=i)
        dates.append(date.strftime("%m/%d"))

        # Calculate success rate for this day
        day_meetings = Meeting.objects.filter(
            created_at__date=date.date(), status="completed"
        )

        if day_meetings.exists():
            converted = day_meetings.filter(
                lead__status__in=["qualified", "converted"]
            ).count()
            success_rate = converted / day_meetings.count() * 100
        else:
            success_rate = 0

        success_rates.append(round(success_rate, 1))

    return {"labels": dates, "data": success_rates}
