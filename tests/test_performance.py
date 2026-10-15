"""
Tests for performance classification and score thresholds.
"""

import pytest
from services.persistence import DatabaseManager
from tools.performance import classify_score, analyze_performance


def test_classify_score_thresholds():
    # Strong: >= 80%
    assert classify_score(80.0) == "Strong"
    assert classify_score(95.0) == "Strong"
    assert classify_score(100.0) == "Strong"

    # Developing: 60%–79.9%
    assert classify_score(60.0) == "Developing"
    assert classify_score(75.5) == "Developing"
    assert classify_score(79.9) == "Developing"

    # Needs Attention: < 60%
    assert classify_score(59.9) == "Needs Attention"
    assert classify_score(40.0) == "Needs Attention"
    assert classify_score(0.0) == "Needs Attention"


def test_analyze_performance_aggregation(tmp_path):
    db_file = str(tmp_path / "test_perf.db")
    db = DatabaseManager(db_file)

    # 1. Normalization: 4/5 (80%) -> Strong
    db.save_quiz_attempt("Normalization", "medium", 4, 5, [], {})

    # 2. Indexing: 2/5 (40%) -> Needs Attention
    db.save_quiz_attempt("Indexing", "medium", 2, 5, [], {})

    # 3. SQL: 7/10 (70%) -> Developing
    db.save_quiz_attempt("SQL", "medium", 7, 10, [], {})

    analysis = analyze_performance(db_path=db_file)

    assert analysis["status"] == "SUCCESS"
    assert analysis["has_data"] is True
    assert analysis["total_attempts"] == 3

    # Check topic categories
    strong_topics = [t["topic"] for t in analysis["strong_topics"]]
    dev_topics = [t["topic"] for t in analysis["developing_topics"]]
    weak_topics = [t["topic"] for t in analysis["weak_topics"]]

    assert "Normalization" in strong_topics
    assert "SQL" in dev_topics
    assert "Indexing" in weak_topics

    # Check rationales
    assert "Needs Attention" in analysis["topic_breakdown"]["Indexing"]["rationale"]
    assert len(analysis["recommendations"]) > 0


def test_analyze_performance_empty(tmp_path):
    db_file = str(tmp_path / "test_empty_perf.db")
    db = DatabaseManager(db_file)

    analysis = analyze_performance(db_path=db_file)
    assert analysis["has_data"] is False
    assert analysis["total_attempts"] == 0
    assert len(analysis["weak_topics"]) == 0
    assert "No recorded quiz attempts" in analysis["message"]
