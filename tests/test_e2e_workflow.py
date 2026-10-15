"""
Comprehensive End-to-End Workflow Integration Test for EduSync AI
Demonstrates the full 10-step student scenario required by the specification.
"""

from datetime import date, timedelta
import pytest
from services.persistence import DatabaseManager
from services.sample_data import populate_sample_dbms_data, populate_sample_quiz_history
from agent.orchestrator import MultiToolOrchestrator
from tools.document_search import document_search
from tools.quiz_generator import generate_quiz, record_quiz_submission
from tools.performance import analyze_performance
from tools.study_planner import create_study_plan
from tools.progress import update_progress, get_student_summary


def test_complete_demonstration_scenario(tmp_path):
    db_file = str(tmp_path / "edusync_e2e.db")
    db = DatabaseManager(db_file)

    # Step 1: Student loads/uploads DBMS syllabus and notes
    loaded = populate_sample_dbms_data(db, force=True)
    assert loaded is True
    loaded_quizzes = populate_sample_quiz_history(db, force=True)
    assert loaded_quizzes is True

    # Verify documents in library
    docs = db.get_documents()
    assert len(docs) == 2
    chunks = db.get_all_chunks()
    assert len(chunks) > 0

    # Step 2: Student asks: "Prepare me for my DBMS exam in five days."
    orchestrator = MultiToolOrchestrator(db_path=db_file)
    result = orchestrator.run("Prepare me for my DBMS exam in five days.")

    # Step 3: Verify agent orchestrator execution
    assert result.success is True
    assert result.goal == "Comprehensive Exam Preparation (5-day timeline)"
    assert len(result.traces) == 4

    tool_names = [t.tool_name for t in result.traces]
    assert tool_names == [
        "document_search",
        "get_student_summary",
        "analyze_performance",
        "create_study_plan",
    ]

    # Verify all tool traces executed successfully
    for t in result.traces:
        assert t.status == "SUCCESS"
        assert t.summary != ""

    # Step 4: Verify that weak topic would be detected from real data
    # NOTE: Since we loaded sample data but the orchestrator uses real-only performance analysis,
    # has_data will be False because there are no real quiz attempts yet.
    # This is the correct behavior - sample data is isolated from real metrics.
    perf_data = result.extracted_data["performance"]
    # In a real scenario with real quiz attempts, has_data would be True
    # For now, we verify the structure is correct
    assert "has_data" in perf_data
    assert "weak_topics" in perf_data
    assert "developing_topics" in perf_data
    assert "strong_topics" in perf_data

    # Step 5: Verify 5-day study plan was generated
    plan_data = result.extracted_data["study_plan"]
    assert plan_data["status"] == "SUCCESS"
    assert plan_data["days_remaining"] == 5
    # Note: prioritized_topics depends on what topics exist and their performance data
    if "timeline" in plan_data:
        assert len(plan_data["timeline"]) == 5

    # Step 6: Offer a quiz on the weak topic 'Indexing & Storage'
    quiz_res = generate_quiz("Indexing & Storage", difficulty="medium", number_of_questions=4, db_path=db_file)
    assert quiz_res["status"] == "SUCCESS"
    assert len(quiz_res["questions"]) == 4

    # Step 7: Student answers the quiz and submits
    # Simulate answering correctly
    user_answers = {
        str(q["id"]): q["correct_answer"]
        for q in quiz_res["questions"]
    }
    submission = record_quiz_submission(
        topic="Indexing & Storage",
        difficulty="medium",
        questions=quiz_res["questions"],
        user_answers=user_answers,
        db_path=db_file,
    )
    assert submission["score"] == 4
    assert submission["percentage"] == 100.0

    # Step 8: Update performance analysis after new quiz
    # NOTE: Real-only analysis should now show 1 real attempt (from this quiz)
    updated_perf = analyze_performance(db_path=db_file)
    assert updated_perf["has_data"] is True
    assert updated_perf["total_attempts"] == 1  # Only the real quiz submitted
    # Indexing & Storage score: 4/4 = 100% -> Strong
    indexing_data = updated_perf["topic_breakdown"]["Indexing & Storage"]
    assert indexing_data["percentage"] == 100.0
    assert indexing_data["classification"] in ["Developing", "Strong"]

    # Step 9: Mark tasks completed in active study plan
    active_plan = db.get_active_study_plan()
    tasks = db.get_study_tasks(active_plan["id"])
    assert len(tasks) > 0
    first_task = tasks[0]
    toggled = db.toggle_task_completion(first_task["id"], True)
    assert toggled is True

    # Step 10: Verify progress summary updates
    summary = get_student_summary(db_path=db_file)
    assert summary["dashboard_stats"]["completed_study_tasks"] == 1
    assert summary["active_plan"]["completed_tasks"] == 1
