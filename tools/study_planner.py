"""
EduSync AI — Tool 4: study_planner
Produces prioritized, date-validated study schedules that dynamically adapt to weak topics.
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from services.persistence import get_db


def parse_and_validate_exam_date(exam_date_input: Union[str, date, datetime]) -> Dict[str, Any]:
    """
    Validates that the exam date is in the future.

    Returns:
        Dict with 'is_valid', 'exam_date', 'days_remaining', or 'error'.
    """
    today = date.today()

    if isinstance(exam_date_input, datetime):
        parsed_date = exam_date_input.date()
    elif isinstance(exam_date_input, date):
        parsed_date = exam_date_input
    elif isinstance(exam_date_input, str):
        cleaned = exam_date_input.strip()
        # Handle '5 days' format if passed
        if "day" in cleaned.lower():
            import re
            m = re.search(r"(\d+)\s*day", cleaned.lower())
            if m:
                days_add = int(m.group(1))
                parsed_date = today + timedelta(days=days_add)
            else:
                return {
                    "is_valid": False,
                    "error": f"Could not parse relative date from '{exam_date_input}'. Use YYYY-MM-DD.",
                }
        else:
            try:
                parsed_date = datetime.strptime(cleaned, "%Y-%m-%d").date()
            except ValueError:
                try:
                    parsed_date = datetime.strptime(cleaned, "%d-%m-%Y").date()
                except ValueError:
                    return {
                        "is_valid": False,
                        "error": f"Invalid date format '{exam_date_input}'. Please use YYYY-MM-DD.",
                    }
    else:
        return {"is_valid": False, "error": "Invalid exam date type provided."}

    days_diff = (parsed_date - today).days

    if days_diff <= 0:
        return {
            "is_valid": False,
            "error": (
                f"The exam date ({parsed_date.isoformat()}) must be in the future. "
                f"Today is {today.isoformat()}. Study sessions cannot be scheduled in the past or on exam day."
            ),
        }

    return {
        "is_valid": True,
        "exam_date": parsed_date,
        "days_remaining": days_diff,
        "today": today,
    }


def create_study_plan(
    exam_date: Union[str, date],
    available_hours: float,
    topics: Optional[List[str]] = None,
    performance: Optional[Dict[str, Any]] = None,
    subject: str = "Database Management Systems",
    db_path: str = "edusync.db",
) -> Dict[str, Any]:
    """
    Generates a prioritized study schedule allocated across remaining days.

    Args:
        exam_date: Exam date (YYYY-MM-DD or date object)
        available_hours: Daily study time in hours (> 0 and <= 16)
        topics: List of topic names (if None, uses default/syllabus topics)
        performance: Output from analyze_performance or dict with weak_topics
        subject: Course or subject name
        db_path: SQLite DB path

    Returns:
        Structured study plan dictionary including timeline and task list.
    """
    # 1. Date Validation
    date_val = parse_and_validate_exam_date(exam_date)
    if not date_val["is_valid"]:
        return {
            "status": "FAILED",
            "message": date_val["error"],
            "plan": None,
        }

    days_remaining = date_val["days_remaining"]
    valid_exam_date = date_val["exam_date"]
    today = date_val["today"]

    # 2. Hours Validation
    try:
        daily_hours = float(available_hours)
    except (ValueError, TypeError):
        return {
            "status": "FAILED",
            "message": f"Invalid available hours '{available_hours}'. Must be a positive number.",
            "plan": None,
        }

    if daily_hours <= 0.0 or daily_hours > 16.0:
        return {
            "status": "FAILED",
            "message": (
                f"Available daily study hours ({daily_hours} hrs) must be greater than 0 "
                "and realistic (maximum 16 hours/day to prevent burnout)."
            ),
            "plan": None,
        }

    # 3. Topic Gathering
    candidate_topics = topics if topics and len(topics) > 0 else [
        "ER & Relational Model",
        "SQL & Query Optimization",
        "Normalization",
        "Transactions & Concurrency",
        "Indexing & Storage",
    ]

    # 4. Weight Calculation based on Performance
    weak_names = set()
    dev_names = set()
    strong_names = set()

    if performance and isinstance(performance, dict):
        for w in performance.get("weak_topics", []):
            weak_names.add(w.get("topic", "").lower())
        for d in performance.get("developing_topics", []):
            dev_names.add(d.get("topic", "").lower())
        for s in performance.get("strong_topics", []):
            strong_names.add(s.get("topic", "").lower())

    weighted_topics = []
    for t in candidate_topics:
        t_lower = t.lower()
        if t_lower in weak_names:
            weight = 3.0  # High urgency
            status = "Needs Attention (High Priority)"
        elif t_lower in dev_names:
            weight = 2.0  # Medium urgency
            status = "Developing (Moderate Priority)"
        elif t_lower in strong_names:
            weight = 1.0  # Low urgency / maintenance
            status = "Strong (Maintenance)"
        else:
            weight = 1.5  # Neutral / untested
            status = "Untested"

        weighted_topics.append({"topic": t, "weight": weight, "status": status})

    # Sort topics by weight descending so weakest topics get tackled first
    weighted_topics.sort(key=lambda x: -x["weight"])

    # 5. Build Day-by-Day Timeline
    days_plan: List[Dict[str, Any]] = []

    # Strategy:
    # If 1 day: split into concept review + practice + final review
    # If >= 2 days:
    # Final day is always Mock Exam & Formula Revision.
    # Penultimate day is Targeted Practice & Revision.
    # Earlier days focus on topic study in priority order.

    if days_remaining == 1:
        # Emergency 1-day plan
        current_date = today
        t1 = weighted_topics[0]["topic"] if weighted_topics else subject
        t2 = weighted_topics[1]["topic"] if len(weighted_topics) > 1 else subject
        tasks = [
            {
                "topic": t1,
                "description": f"Intensive Concept Review & High-Yield Summary: {t1}",
                "duration_hours": round(daily_hours * 0.45, 1),
                "type": "concept",
            },
            {
                "topic": t2,
                "description": f"Targeted Problem Solving & Practice MCQs: {t2}",
                "duration_hours": round(daily_hours * 0.35, 1),
                "type": "practice",
            },
            {
                "topic": "Comprehensive Revision",
                "description": "Final High-Yield Formula and Definition Check",
                "duration_hours": round(daily_hours * 0.20, 1),
                "type": "revision",
            },
        ]
        days_plan.append({
            "day": 1,
            "date": current_date.isoformat(),
            "focus": "Emergency Rapid Revision & Weak Topic Triage",
            "tasks": tasks,
        })
    else:
        concept_days = max(1, days_remaining - 2)
        # Distribute topics across concept_days
        num_topics = len(weighted_topics)

        for day_idx in range(1, days_remaining + 1):
            day_date = today + timedelta(days=day_idx - 1)

            if day_idx <= concept_days:
                # Map to topics
                t_idx = (day_idx - 1) % num_topics
                primary_t = weighted_topics[t_idx]
                secondary_t = weighted_topics[(t_idx + 1) % num_topics] if num_topics > 1 else None

                tasks = [
                    {
                        "topic": primary_t["topic"],
                        "description": f"Deep Concept Study & Notes Breakdown ({primary_t['status']})",
                        "duration_hours": round(daily_hours * 0.65, 1),
                        "type": "concept",
                    },
                    {
                        "topic": primary_t["topic"],
                        "description": f"Active Recall & Quiz Practice on {primary_t['topic']}",
                        "duration_hours": round(daily_hours * 0.35, 1),
                        "type": "practice",
                    },
                ]
                focus = f"Core Mastery: {primary_t['topic']}"

            elif day_idx == days_remaining - 1:
                # Penultimate day: Targeted Revision & Weak topic drills
                weakest_label = weighted_topics[0]["topic"] if weighted_topics else subject
                tasks = [
                    {
                        "topic": weakest_label,
                        "description": f"Targeted Drill on Weakest Areas: {weakest_label}",
                        "duration_hours": round(daily_hours * 0.50, 1),
                        "type": "practice",
                    },
                    {
                        "topic": "Cumulative Revision",
                        "description": "Consolidated Formula & Diagram Review across all Units",
                        "duration_hours": round(daily_hours * 0.50, 1),
                        "type": "revision",
                    },
                ]
                focus = "Targeted Weak-Area Drills & Cross-Topic Revision"

            else:
                # Final day before exam: Mock Test + Light Review
                tasks = [
                    {
                        "topic": subject,
                        "description": "Timed Comprehensive Diagnostic Mock Exam (Full Course Scope)",
                        "duration_hours": round(daily_hours * 0.55, 1),
                        "type": "mock",
                    },
                    {
                        "topic": "Final Exam Prep",
                        "description": "Light High-Yield Summary Review & Rest to Prevent Fatigue",
                        "duration_hours": round(daily_hours * 0.45, 1),
                        "type": "revision",
                    },
                ]
                focus = "Mock Examination & Final Readiness Check"

            days_plan.append({
                "day": day_idx,
                "date": day_date.isoformat(),
                "focus": focus,
                "tasks": tasks,
            })

    # 6. Save active plan to DB
    db = get_db(db_path)
    plan_id = db.save_study_plan(
        subject=subject,
        exam_date=valid_exam_date.isoformat(),
        available_hours=daily_hours,
        days_plan=days_plan,
    )

    total_tasks_count = sum(len(d["tasks"]) for d in days_plan)

    return {
        "status": "SUCCESS",
        "plan_id": plan_id,
        "subject": subject,
        "exam_date": valid_exam_date.isoformat(),
        "days_remaining": days_remaining,
        "daily_hours": daily_hours,
        "total_study_hours": round(daily_hours * days_remaining, 1),
        "total_tasks": total_tasks_count,
        "timeline": days_plan,
        "prioritized_topics": weighted_topics,
        "message": (
            f"Successfully generated a prioritized {days_remaining}-day study plan "
            f"for '{subject}' allocating {daily_hours} hours/day."
        ),
    }
