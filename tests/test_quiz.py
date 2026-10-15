"""
Tests for quiz generation, scoring, and persistence.
"""

import pytest
from services.persistence import DatabaseManager
from tools.quiz_generator import generate_quiz, score_quiz, record_quiz_submission


def test_score_quiz_calculation():
    questions = [
        {
            "id": 1,
            "question": "What is 1NF?",
            "options": ["A) Atomic", "B) Non-atomic"],
            "correct_answer": "A) Atomic",
        },
        {
            "id": 2,
            "question": "What does A stand for in ACID?",
            "options": ["A) Association", "B) Atomicity"],
            "correct_answer": "B) Atomicity",
        },
    ]

    # Both correct
    res1 = score_quiz(questions, {"1": "A) Atomic", "2": "B) Atomicity"})
    assert res1["score"] == 2
    assert res1["total"] == 2
    assert res1["percentage"] == 100.0

    # Prefix match test
    res2 = score_quiz(questions, {"1": "A", "2": "B"})
    assert res2["score"] == 2

    # One wrong
    res3 = score_quiz(questions, {"1": "A", "2": "A"})
    assert res3["score"] == 1
    assert res3["percentage"] == 50.0


def test_generate_quiz_fallback(tmp_path):
    db_file = str(tmp_path / "test_quiz.db")
    res = generate_quiz("Normalization", difficulty="medium", number_of_questions=3, db_path=db_file)

    assert res["status"] == "SUCCESS"
    assert len(res["questions"]) == 3
    assert res["topic"] == "Normalization"
    for q in res["questions"]:
        assert "question" in q
        assert "options" in q
        assert len(q["options"]) == 4
        assert "correct_answer" in q
        assert "explanation" in q


def test_record_quiz_submission(tmp_path):
    db_file = str(tmp_path / "test_submission.db")
    db = DatabaseManager(db_file)

    questions = [
        {"id": 1, "question": "Q1", "options": ["A", "B"], "correct_answer": "A"},
    ]
    sub = record_quiz_submission(
        topic="SQL",
        difficulty="easy",
        questions=questions,
        user_answers={"1": "A"},
        db_path=db_file,
    )

    assert sub["score"] == 1
    assert sub["percentage"] == 100.0
    assert "attempt_id" in sub

    # Verify stored in SQLite
    attempts = db.get_quiz_attempts("SQL")
    assert len(attempts) == 1
    assert attempts[0]["score"] == 1
