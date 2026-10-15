"""
Tests for multi-tool agent orchestration, intent parsing, and execution traces.
"""

import pytest
from agent.orchestrator import MultiToolOrchestrator
from services.persistence import DatabaseManager
from services.sample_data import populate_sample_dbms_data, populate_sample_quiz_history


def test_intent_parsing():
    orchestrator = MultiToolOrchestrator(db_path=":memory:")

    # 1. Exam prep intent
    prep_intent = orchestrator.determine_intent("Prepare me for my DBMS exam in five days")
    assert prep_intent["goal"] == "exam_preparation"
    assert prep_intent["days"] == 5

    # 2. Quiz intent
    quiz_intent = orchestrator.determine_intent("Give me a quiz on indexing")
    assert quiz_intent["goal"] == "quiz_generation"
    assert "Indexing" in quiz_intent["topic"]

    # 3. Search intent
    search_intent = orchestrator.determine_intent("Find information about normalization in my notes")
    assert search_intent["goal"] == "document_search"

    # 4. Performance intent
    perf_intent = orchestrator.determine_intent("How did I do on my quizzes and what are my weak topics?")
    assert perf_intent["goal"] == "performance_analysis"


def test_orchestration_exam_prep_workflow(tmp_path):
    db_file = str(tmp_path / "test_agent_workflow.db")
    db = DatabaseManager(db_file)

    # Pre-populate sample documents & quiz history
    populate_sample_dbms_data(db)
    populate_sample_quiz_history(db)

    orchestrator = MultiToolOrchestrator(db_path=db_file)
    result = orchestrator.run("Prepare me for my DBMS exam in five days", context={"daily_hours": 3.0})

    assert result.success is True
    assert result.iterations >= 4  # document_search, get_student_summary, analyze_performance, create_study_plan
    assert len(result.traces) >= 4

    # Verify tool execution order & traces
    tool_names = [t.tool_name for t in result.traces]
    assert "document_search" in tool_names
    assert "get_student_summary" in tool_names
    assert "analyze_performance" in tool_names
    assert "create_study_plan" in tool_names

    # All tools should succeed
    for trace in result.traces:
        assert trace.status == "SUCCESS"
        assert len(trace.summary) > 0

    assert "Exam Preparation" in result.final_response
    assert len(result.recommended_next_action) > 0

    # Verify execution logged to SQLite
    recent_logs = db.get_recent_agent_logs(limit=5)
    assert len(recent_logs) >= 1
    assert recent_logs[0]["goal"] == result.goal
