"""
Tests for study plan date validation, topic weighting, and task scheduling.
"""

from datetime import date, timedelta
import pytest
from tools.study_planner import parse_and_validate_exam_date, create_study_plan


def test_exam_date_validation():
    today = date.today()

    # Valid future date
    future_date = (today + timedelta(days=5)).isoformat()
    val = parse_and_validate_exam_date(future_date)
    assert val["is_valid"] is True
    assert val["days_remaining"] == 5

    # Past date
    past_date = (today - timedelta(days=1)).isoformat()
    val_past = parse_and_validate_exam_date(past_date)
    assert val_past["is_valid"] is False
    assert "must be in the future" in val_past["error"]

    # Today's date (cannot schedule sessions after or on exam day)
    val_today = parse_and_validate_exam_date(today.isoformat())
    assert val_today["is_valid"] is False


def test_study_plan_invalid_hours(tmp_path):
    db_file = str(tmp_path / "test_hours.db")
    future_date = (date.today() + timedelta(days=5)).isoformat()

    # Zero or negative hours
    res0 = create_study_plan(future_date, available_hours=0, db_path=db_file)
    assert res0["status"] == "FAILED"
    assert "must be greater than 0" in res0["message"]

    # Excessive hours
    res24 = create_study_plan(future_date, available_hours=24, db_path=db_file)
    assert res24["status"] == "FAILED"
    assert "maximum 16" in res24["message"]


def test_study_plan_prioritizes_weak_topics(tmp_path):
    db_file = str(tmp_path / "test_priority.db")
    future_date = (date.today() + timedelta(days=5)).isoformat()

    mock_performance = {
        "weak_topics": [{"topic": "Indexing & Storage"}],
        "developing_topics": [{"topic": "Transactions & Concurrency"}],
        "strong_topics": [{"topic": "SQL"}],
    }

    res = create_study_plan(
        exam_date=future_date,
        available_hours=4.0,
        topics=["SQL", "Indexing & Storage", "Transactions & Concurrency"],
        performance=mock_performance,
        subject="DBMS",
        db_path=db_file,
    )

    assert res["status"] == "SUCCESS"
    assert res["days_remaining"] == 5
    assert res["total_study_hours"] == 20.0
    assert len(res["timeline"]) == 5

    # Check that highest weighted topic is weak topic
    prioritized = res["prioritized_topics"]
    assert prioritized[0]["topic"] == "Indexing & Storage"
    assert prioritized[0]["weight"] > prioritized[-1]["weight"]
