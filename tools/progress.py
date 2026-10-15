"""
EduSync AI — Tool 5 & 6: progress
Tracks quiz attempts, task completions, and returns student learning summaries.
"""

from typing import Any, Dict, List, Optional
from services.persistence import get_db
from tools.performance import analyze_performance


def update_progress(
    topic: Optional[str] = None,
    score: Optional[float] = None,
    completed_tasks: Optional[List[int]] = None,
    task_id_toggle: Optional[int] = None,
    task_completed: Optional[bool] = None,
    db_path: str = "edusync.db",
) -> Dict[str, Any]:
    """
    Updates student learning progress (task completion or custom score record).

    Args:
        topic: Topic name if logging an external score
        score: Score percentage (0-100)
        completed_tasks: List of task IDs to mark complete
        task_id_toggle: Specific task ID to toggle
        task_completed: Target completion state (True/False)
        db_path: Path to database

    Returns:
        Updated progress summary dictionary.
    """
    db = get_db(db_path)
    updates_made = []

    # 1. Update task completions
    if completed_tasks:
        for tid in completed_tasks:
            try:
                db.toggle_task_completion(int(tid), True)
                updates_made.append(f"Marked task #{tid} as completed.")
            except Exception:
                pass

    if task_id_toggle is not None and task_completed is not None:
        db.toggle_task_completion(int(task_id_toggle), bool(task_completed))
        state_label = "completed" if task_completed else "pending"
        updates_made.append(f"Updated task #{task_id_toggle} to {state_label}.")

    # 2. Log manual score if provided
    if topic and score is not None:
        try:
            score_val = float(score)
            db.save_quiz_attempt(
                topic=topic.strip(),
                difficulty="medium",
                score=int(round(score_val / 20.0)),  # Approx 5-question scale
                total_questions=5,
                questions=[],
                user_answers={},
            )
            updates_made.append(f"Recorded progress score of {score_val}% for '{topic}'.")
        except Exception:
            pass

    # 3. Retrieve fresh student summary
    summary = get_student_summary(db_path=db_path)

    return {
        "status": "SUCCESS",
        "updates": updates_made,
        "summary": summary,
        "message": "Learning progress successfully updated."
        if updates_made
        else "No modifications specified; current summary retrieved.",
    }


def get_student_summary(db_path: str = "edusync.db") -> Dict[str, Any]:
    """
    Returns the comprehensive current learning state of the student.

    Returns:
        Dict with document metrics, quiz analytics, weak topics, active plan progress, and recent logs.
    """
    db = get_db(db_path)
    stats = db.get_dashboard_stats()
    perf = analyze_performance(db_path=db_path)
    active_plan = db.get_active_study_plan()
    tasks = db.get_study_tasks() if active_plan else []

    completed_tasks_count = sum(1 for t in tasks if t.get("completed", 0) == 1)
    total_tasks_count = len(tasks)

    plan_summary = None
    if active_plan:
        plan_summary = {
            "plan_id": active_plan["id"],
            "subject": active_plan["subject"],
            "exam_date": active_plan["exam_date"],
            "available_hours": active_plan["available_hours"],
            "total_tasks": total_tasks_count,
            "completed_tasks": completed_tasks_count,
            "completion_percentage": round(
                (completed_tasks_count / total_tasks_count * 100) if total_tasks_count > 0 else 0.0,
                1,
            ),
            "created_at": active_plan["created_at"],
        }

    return {
        "status": "SUCCESS",
        "dashboard_stats": stats,
        "performance": {
            "overall_score": perf.get("overall_score", 0.0),
            "total_attempts": perf.get("total_attempts", 0),
            "strong_topics_count": len(perf.get("strong_topics", [])),
            "developing_topics_count": len(perf.get("developing_topics", [])),
            "weak_topics_count": len(perf.get("weak_topics", [])),
            "weak_topics": [w["topic"] for w in perf.get("weak_topics", [])],
            "developing_topics": [d["topic"] for d in perf.get("developing_topics", [])],
            "strong_topics": [s["topic"] for s in perf.get("strong_topics", [])],
        },
        "active_plan": plan_summary,
        "documents_count": stats["document_count"],
        "chunks_count": stats["chunk_count"],
        "message": (
            f"Student has {stats['document_count']} document(s), {stats['quiz_attempts_count']} quiz attempt(s), "
            f"and {completed_tasks_count}/{total_tasks_count} study tasks completed."
        ),
    }
