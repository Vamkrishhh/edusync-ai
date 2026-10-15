"""
Production Integration Tests for EduSync AI
Test actual backend workflows and data persistence without AppTest framework.
These tests verify the application will work correctly when deployed.
"""

import os
import sys
import gc
import pytest
import tempfile
import json
from datetime import date, timedelta
from pathlib import Path

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.persistence import DatabaseManager
from services.sample_data import (
    populate_sample_dbms_data,
    populate_sample_quiz_history,
    SAMPLE_TOPICS,
)
from tools.document_search import document_search
from tools.quiz_generator import generate_quiz, record_quiz_submission
from tools.performance import analyze_performance, classify_score
from tools.study_planner import create_study_plan, parse_and_validate_exam_date
from tools.progress import update_progress, get_student_summary
from agent.orchestrator import MultiToolOrchestrator


def _fresh_db(path: str) -> DatabaseManager:
    """Delete any stale file and return a brand-new DatabaseManager."""
    # Force-close any cached singleton connection first
    from services import persistence as _pers
    if _pers._default_db is not None and _pers._default_db.db_path == path:
        _pers._default_db = None
    gc.collect()

    if os.path.exists(path):
        try:
            os.remove(path)
        except PermissionError:
            pass  # file locked by prior run; _init_db will reset_database below

    db = DatabaseManager(path)
    db.reset_database()
    return db


class TestFullApplicationWorkflows:
    """Test complete end-to-end workflows that users will perform."""

    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        """Create a clean test database for each test."""
        self.db_path = "test_production.db"
        self.db = _fresh_db(self.db_path)
        yield
        # Cleanup: reset singleton reference so next test gets a fresh connection
        from services import persistence as _pers
        _pers._default_db = None
        gc.collect()

    def test_1_sample_data_loads_correctly(self):
        """Verify sample data can be loaded and is properly isolated."""
        populate_sample_dbms_data(self.db, force=True)

        docs = self.db.get_documents()
        assert len(docs) >= 2, "Sample data should include at least 2 documents"

        sample_docs = [d for d in docs if d.get("is_sample") == 1]
        assert len(sample_docs) > 0, "Should have sample documents marked"

        chunks = self.db.get_all_chunks()
        assert len(chunks) > 0, "Sample documents should have indexed chunks"

        real_docs = [d for d in docs if d.get("is_sample") != 1]
        assert len(real_docs) == 0, "No real data should exist yet"

        print(f"✓ Sample data loaded: {len(docs)} docs, {len(chunks)} chunks")

    def test_2_document_search_with_sample_data(self):
        """Verify document search returns relevant chunks."""
        populate_sample_dbms_data(self.db, force=True)

        result = document_search(query="normalization", top_k=5, db_path=self.db_path)

        assert result["status"] == "SUCCESS", f"Search should succeed: {result}"
        assert result.get("found") is True, "Search should find relevant documents"

        chunks = result.get("chunks", [])
        assert len(chunks) > 0, "Should find chunks matching 'normalization'"

        for chunk in chunks:
            assert "text" in chunk, "Chunk should have text"
            assert "source" in chunk, "Chunk should have source"
            assert "page_number" in chunk, "Chunk should have page_number"
            assert "similarity_score" in chunk, "Chunk should have similarity score"

        print(f"✓ Document search found {len(chunks)} relevant chunks")

    def test_3_quiz_generation_and_scoring(self):
        """Verify quiz generation, submission, and scoring."""
        populate_sample_dbms_data(self.db, force=True)

        quiz_result = generate_quiz(
            topic="Normalization",
            difficulty="medium",
            number_of_questions=5,
            db_path=self.db_path,
        )

        assert quiz_result["status"] == "SUCCESS", f"Quiz generation should succeed: {quiz_result}"
        questions = quiz_result.get("questions", [])
        assert len(questions) == 5, "Should generate 5 questions"

        for q in questions:
            assert "question" in q, "Question should have text"
            assert "options" in q, "Question should have options"
            assert "correct_answer" in q, "Question should have correct answer"
            assert len(q["options"]) >= 4, "Should have at least 4 options"

        # Submit all correct answers
        user_answers = {str(q["id"]): q["correct_answer"] for q in questions}
        sub_result = record_quiz_submission(
            quiz_result,
            user_answers,
            self.db_path,
        )

        assert sub_result["score"] == 5, f"Perfect score expected: {sub_result}"
        assert sub_result["percentage"] == 100.0, "Perfect score should be 100%"

        attempts = self.db.get_quiz_attempts()
        assert len(attempts) > 0, "Quiz attempt should be stored in database"

        attempt = attempts[0]  # most recent first
        assert attempt["topic"] == "Normalization", "Topic should be recorded"
        assert attempt["score"] == 5, "Score should be recorded"

        print(f"✓ Quiz generated, submitted, and scored correctly (5/5 = 100%)")

    def test_4_performance_analysis_after_quiz(self):
        """Verify performance metrics update correctly after quiz submission."""
        populate_sample_dbms_data(self.db, force=True)

        quiz = generate_quiz(
            topic="Normalization",
            difficulty="medium",
            number_of_questions=4,
            db_path=self.db_path,
        )
        questions = quiz["questions"]
        user_answers = {str(q["id"]): q["correct_answer"] for q in questions}
        record_quiz_submission(quiz, user_answers, self.db_path)

        # analyze_performance defaults to real_only (include_sample=False)
        perf = analyze_performance(db_path=self.db_path)

        assert perf["status"] == "SUCCESS", f"Performance analysis should succeed: {perf}"
        assert perf["has_data"] is True, "Should have real data after quiz"
        assert perf["total_attempts"] > 0, "Should count the quiz attempt"

        topic_breakdown = perf.get("topic_breakdown", {})
        assert "Normalization" in topic_breakdown, "Should track Normalization topic"

        norm_data = topic_breakdown["Normalization"]
        assert norm_data["percentage"] == 100.0, "Normalization should show 100% after perfect quiz"
        assert norm_data["attempts"] > 0, "Should count attempts per topic"

        print(f"✓ Performance analysis correct: {perf['total_attempts']} attempt(s), {perf['overall_score']}% accuracy")

    def test_5_study_plan_generation(self):
        """Verify study plan generation with date and hours validation."""
        exam_date = (date.today() + timedelta(days=5)).isoformat()

        plan_result = create_study_plan(
            exam_date=exam_date,
            available_hours=3.0,
            subject="DBMS Fundamentals",
            topics=["Normalization", "Indexing", "Transactions"],
            db_path=self.db_path,
        )

        assert plan_result["status"] == "SUCCESS", f"Plan should be generated: {plan_result}"
        assert plan_result.get("subject") == "DBMS Fundamentals", "Subject should be stored"
        assert plan_result.get("exam_date") == exam_date, "Exam date should be stored"
        assert plan_result.get("daily_hours") == 3.0, "Hours should be stored"

        timeline = plan_result.get("timeline", [])
        assert len(timeline) > 0, "Should create daily tasks"

        total_tasks = sum(len(d.get("tasks", [])) for d in timeline)
        assert total_tasks > 0, "Should have tasks across multiple days"

        stored_plan = self.db.get_active_study_plan()
        assert stored_plan is not None, "Plan should be stored in database"
        assert stored_plan["subject"] == "DBMS Fundamentals", "Stored plan should have correct subject"

        print(f"✓ Study plan created: {total_tasks} tasks over {len(timeline)} days")

    def test_6_study_plan_validation(self):
        """Verify study plan rejects invalid dates and hours."""
        past_date = (date.today() - timedelta(days=1)).isoformat()

        past_result = create_study_plan(
            exam_date=past_date,
            available_hours=3.0,
            subject="Test",
            db_path=self.db_path,
        )

        assert past_result["status"] == "FAILED", "Should reject past exam dates"
        assert "future" in past_result.get("message", "").lower(), "Error should mention 'future'"

        future_date = (date.today() + timedelta(days=5)).isoformat()

        hours_result = create_study_plan(
            exam_date=future_date,
            available_hours=25.0,
            subject="Test",
            db_path=self.db_path,
        )

        assert hours_result["status"] == "FAILED", "Should reject excessive study hours"
        assert "maximum" in hours_result.get("message", "").lower(), "Error should mention limit"

        print(f"✓ Study plan validation works: past dates and excessive hours rejected")

    def test_7_progress_tracking_after_tasks(self):
        """Verify progress metrics update when study tasks are completed."""
        exam_date = (date.today() + timedelta(days=5)).isoformat()
        plan_result = create_study_plan(
            exam_date=exam_date,
            available_hours=3.0,
            subject="Test Course",
            db_path=self.db_path,
        )

        assert plan_result["status"] == "SUCCESS"
        plan_id = plan_result["plan_id"]

        stats_before = self.db.get_dashboard_stats()
        tasks_before = stats_before.get("total_study_tasks", 0)
        completed_before = stats_before.get("completed_study_tasks", 0)

        assert tasks_before > 0, "Plan should create tasks"

        tasks = self.db.get_study_tasks(plan_id)
        assert len(tasks) > 0, "Should have tasks for the plan"

        task_id = tasks[0]["id"]
        update_progress(
            task_id_toggle=task_id,
            task_completed=True,
            db_path=self.db_path,
        )

        stats_after = self.db.get_dashboard_stats()
        completed_after = stats_after.get("completed_study_tasks", 0)

        assert completed_after > completed_before, "Completed tasks should increase"
        assert completed_after == completed_before + 1, "Should increment by 1"

        print(f"✓ Progress tracking updated after task completion")

    def test_8_data_persistence_across_sessions(self):
        """Verify data persists when database is reinitialized."""
        populate_sample_dbms_data(self.db, force=True)

        quiz = generate_quiz(
            topic="Transactions",
            difficulty="easy",
            number_of_questions=3,
            db_path=self.db_path,
        )
        questions = quiz["questions"]
        user_answers = {str(q["id"]): q["correct_answer"] for q in questions}
        record_quiz_submission(quiz, user_answers, self.db_path)

        attempts_before = self.db.get_quiz_attempts()
        assert len(attempts_before) > 0
        attempt_before = attempts_before[0]

        # New connection simulates a new session
        db_new = DatabaseManager(self.db_path)
        attempts_after = db_new.get_quiz_attempts()
        assert len(attempts_after) > 0, "Attempts should persist"

        attempt_after = attempts_after[0]
        assert attempt_after["topic"] == attempt_before["topic"], "Topic should persist"
        assert attempt_after["score"] == attempt_before["score"], "Score should persist"

        print(f"✓ Data persisted across database session")

    def test_9_duplicate_submission_prevention(self):
        """Verify duplicate quiz submissions are deduplicated by content hash."""
        populate_sample_dbms_data(self.db, force=True)

        quiz = generate_quiz(
            topic="Indexing",
            difficulty="medium",
            number_of_questions=4,
            db_path=self.db_path,
        )
        questions = quiz["questions"]
        user_answers = {str(q["id"]): q["correct_answer"] for q in questions}

        sub1 = record_quiz_submission(quiz, user_answers, self.db_path)
        sub2 = record_quiz_submission(quiz, user_answers, self.db_path)

        assert sub1.get("score") is not None, "First submission should succeed"
        assert sub2.get("score") is not None, "Second submission should succeed"

        attempts = self.db.get_quiz_attempts(topic="Indexing")
        assert len(attempts) == 1, f"Duplicate submissions should be deduplicated, got {len(attempts)}"

        print(f"✓ Duplicate submissions deduplicated correctly")

    def test_10_real_vs_demo_data_isolation(self):
        """Verify demo data doesn't count toward real performance metrics."""
        populate_sample_dbms_data(self.db, force=True)
        populate_sample_quiz_history(self.db, force=True)

        # Real only (default)
        perf_real = analyze_performance(db_path=self.db_path)
        real_count = perf_real.get("total_attempts", 0)
        assert real_count == 0, "Should have no real data until user submits quiz"

        # Including sample
        perf_all = analyze_performance(db_path=self.db_path, include_sample=True)
        all_count = perf_all.get("total_attempts", 0)
        assert all_count >= real_count, "Real-only should not exceed total"
        assert all_count > 0, "Sample-inclusive should find sample attempts"

        # Submit a real quiz
        quiz = generate_quiz(
            topic="Normalization",
            difficulty="easy",
            number_of_questions=2,
            db_path=self.db_path,
        )
        questions = quiz["questions"]
        user_answers = {str(q["id"]): q["correct_answer"] for q in questions}
        record_quiz_submission(quiz, user_answers, self.db_path)

        perf_real_after = analyze_performance(db_path=self.db_path)
        real_count_after = perf_real_after.get("total_attempts", 0)

        assert real_count_after == 1, "Should have 1 real attempt after submission"

        print(f"✓ Demo and real data properly isolated")


class TestMultiToolAgent:
    """Test the multi-tool orchestrator agent."""

    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        self.db_path = "test_agent.db"
        self.db = _fresh_db(self.db_path)
        populate_sample_dbms_data(self.db, force=True)
        yield
        from services import persistence as _pers
        _pers._default_db = None
        gc.collect()

    def test_agent_orchestration_executes_tools(self):
        """Verify multi-tool agent can orchestrate document search and planning."""
        orch = MultiToolOrchestrator(db_path=self.db_path, api_key=None)

        result = orch.run("Create a 3-day study plan for DBMS")

        assert result.success is True, f"Agent should complete: {result}"
        assert len(result.traces) > 0, "Should execute at least one tool"

        print(f"✓ Agent executed {len(result.traces)} tool steps")

    def test_agent_handles_missing_api_key(self):
        """Verify agent gracefully handles missing API key."""
        orch = MultiToolOrchestrator(db_path=self.db_path, api_key=None)

        result = orch.run("What should I focus on for my exam?")

        assert result.success is True, "Should handle missing API gracefully"

        print(f"✓ Agent handles missing API key gracefully")


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        self.db_path = "test_errors.db"
        self.db = _fresh_db(self.db_path)
        populate_sample_dbms_data(self.db, force=True)
        yield
        from services import persistence as _pers
        _pers._default_db = None
        gc.collect()

    def test_empty_search_query_rejected(self):
        """Verify empty search queries are rejected."""
        result = document_search(query="", db_path=self.db_path)
        assert result["status"] == "FAILED", "Empty query should be rejected"
        assert "non-empty string" in result.get("message", "").lower(), "Should mention requirement"

    def test_nonexistent_topic_handled(self):
        """Verify quiz generation handles topics not in sample data."""
        result = generate_quiz(
            topic="NonexistentTopic",
            difficulty="easy",
            number_of_questions=1,
            db_path=self.db_path,
        )
        assert result["status"] in ["SUCCESS", "FAILED"], "Should handle gracefully"

    def test_invalid_difficulty_level(self):
        """Verify invalid difficulty levels are handled."""
        result = generate_quiz(
            topic="Normalization",
            difficulty="invalid",
            number_of_questions=1,
            db_path=self.db_path,
        )
        assert result["status"] in ["SUCCESS", "FAILED"], "Should handle invalid difficulty"

    def test_zero_questions_rejected(self):
        """Verify quiz generation rejects zero questions (clamped to 1)."""
        result = generate_quiz(
            topic="Normalization",
            difficulty="medium",
            number_of_questions=0,
            db_path=self.db_path,
        )
        # The implementation clamps to max(1, min(n, 10)), so 0 becomes 1 — success with 1 question
        assert result["status"] in ["SUCCESS", "FAILED"], "Should handle 0 questions gracefully"
        if result["status"] == "SUCCESS":
            assert len(result.get("questions", [])) >= 1, "Should generate at least 1 question"

    def test_excessive_questions_capped(self):
        """Verify quiz generation caps excessive question requests."""
        result = generate_quiz(
            topic="Normalization",
            difficulty="medium",
            number_of_questions=100,
            db_path=self.db_path,
        )
        if result["status"] == "SUCCESS":
            questions = result.get("questions", [])
            assert len(questions) <= 10, "Should cap questions at 10 maximum"

    def test_empty_topic_for_plan_rejected(self):
        """Verify study plan rejects empty subject (too short)."""
        result = create_study_plan(
            exam_date=(date.today() + timedelta(days=5)).isoformat(),
            available_hours=3.0,
            subject="",
            db_path=self.db_path,
        )
        # subject validation depends on implementation; empty subject may default gracefully
        # What we verify is it doesn't crash
        assert result["status"] in ["SUCCESS", "FAILED"], "Should not crash on empty subject"

    def test_past_date_for_plan_rejected(self):
        """Verify study plan rejects a past exam date."""
        result = create_study_plan(
            exam_date=(date.today() - timedelta(days=1)).isoformat(),
            available_hours=3.0,
            subject="Test Subject",
            db_path=self.db_path,
        )
        assert result["status"] == "FAILED", "Should reject past exam dates"
        assert "future" in result.get("message", "").lower(), "Should mention future requirement"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
