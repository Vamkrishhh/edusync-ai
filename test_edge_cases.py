"""
Edge case and error scenario testing
"""
import sys
from datetime import date, timedelta
from services.persistence import get_db
from services.document_processor import extract_text_from_pdf
from tools.quiz_generator import generate_quiz, record_quiz_submission
from tools.study_planner import create_study_plan, parse_and_validate_exam_date
from tools.performance import analyze_performance
from io import BytesIO

def test_empty_database_workflows():
    """Test all workflows with completely empty database"""
    print("\n=== EDGE CASE 1: Empty Database Workflows ===")
    
    # Create fresh DB
    db = get_db("test_empty.db")
    db.reset_database()
    
    # Test 1: Performance with no data
    perf = analyze_performance(db_path="test_empty.db")
    if perf.get("has_data"):
        print("✗ ERROR: Empty DB should have has_data=False")
        return False
    print("✓ Performance handles empty DB correctly")
    
    # Test 2: Quiz with no documents
    quiz = generate_quiz("Test Topic", "easy", 2, db_path="test_empty.db")
    if quiz.get("status") != "SUCCESS":
        print(f"✗ ERROR: Quiz should work without documents: {quiz.get('message')}")
        return False
    print("✓ Quiz works without documents (uses fallback)")
    
    # Test 3: Study plan with no performance data
    exam_date = (date.today() + timedelta(days=3)).isoformat()
    plan = create_study_plan(
        exam_date=exam_date,
        available_hours=2.0,
        topics=["Topic1", "Topic2"],
        subject="Test Subject",
        performance=None,
        db_path="test_empty.db"
    )
    if plan.get("status") != "SUCCESS":
        print(f"✗ ERROR: Plan should work without performance: {plan.get('message')}")
        return False
    print("✓ Study plan works without performance data")
    
    import os
    try:
        os.remove("test_empty.db")
    except:
        pass
    
    return True

def test_invalid_exam_dates():
    """Test date validation for study plans"""
    print("\n=== EDGE CASE 2: Invalid Exam Dates ===")
    
    db = get_db("test_dates.db")
    db.reset_database()
    
    # Test 1: Past date
    past_date = (date.today() - timedelta(days=1)).isoformat()
    result = parse_and_validate_exam_date(past_date)
    if result.get("is_valid"):
        print(f"✗ ERROR: Past date should be invalid: {past_date}")
        return False
    print(f"✓ Past date rejected: {result.get('message')}")
    
    # Test 2: Today (should be invalid)
    today = date.today().isoformat()
    result = parse_and_validate_exam_date(today)
    if result.get("is_valid"):
        print(f"✗ ERROR: Today should be invalid for new plans")
        return False
    print(f"✓ Today rejected: {result.get('message')}")
    
    # Test 3: Future date (valid)
    future = (date.today() + timedelta(days=7)).isoformat()
    result = parse_and_validate_exam_date(future)
    if not result.get("is_valid"):
        print(f"✗ ERROR: Future date should be valid: {result.get('message')}")
        return False
    print(f"✓ Future date accepted: {result.get('days_remaining')} days")
    
    # Test 4: Create plan with past date should fail
    plan = create_study_plan(
        exam_date=past_date,
        available_hours=2.0,
        topics=["Topic1"],
        subject="Test",
        performance=None,
        db_path="test_dates.db"
    )
    if plan.get("status") == "SUCCESS":
        print("✗ ERROR: Plan with past date should fail")
        return False
    print(f"✓ Plan with past date rejected: {plan.get('message')}")
    
    import os
    try:
        os.remove("test_dates.db")
    except:
        pass
    
    return True

def test_duplicate_quiz_submission():
    """Test that duplicate quiz submissions are handled correctly"""
    print("\n=== EDGE CASE 3: Duplicate Quiz Submission ===")
    
    db = get_db("test_dup.db")
    db.reset_database()
    
    # Generate quiz
    quiz = generate_quiz("Test Topic", "easy", 2, db_path="test_dup.db")
    
    # Submit same answers twice
    answers = {str(q["id"]): q["correct_answer"] for q in quiz["questions"]}
    
    result1 = record_quiz_submission(
        topic=quiz["topic"],
        difficulty=quiz["difficulty"],
        questions=quiz["questions"],
        user_answers=answers,
        db_path="test_dup.db"
    )
    
    attempts_after_1 = len(db.get_quiz_attempts())
    
    result2 = record_quiz_submission(
        topic=quiz["topic"],
        difficulty=quiz["difficulty"],
        questions=quiz["questions"],
        user_answers=answers,
        db_path="test_dup.db"
    )
    
    attempts_after_2 = len(db.get_quiz_attempts())
    
    if attempts_after_1 != attempts_after_2:
        print(f"✗ ERROR: Duplicate submission created new attempt: {attempts_after_1} -> {attempts_after_2}")
        return False
    
    print(f"✓ Duplicate submission prevented: {attempts_after_1} attempts (no increase)")
    
    import os
    try:
        os.remove("test_dup.db")
    except:
        pass
    
    return True

def test_invalid_study_hours():
    """Test study plan with invalid hour values"""
    print("\n=== EDGE CASE 4: Invalid Study Hours ===")
    
    db = get_db("test_hours.db")
    db.reset_database()
    
    exam_date = (date.today() + timedelta(days=3)).isoformat()
    
    # Test 1: Zero hours
    plan = create_study_plan(
        exam_date=exam_date,
        available_hours=0.0,
        topics=["Topic1"],
        subject="Test",
        performance=None,
        db_path="test_hours.db"
    )
    if plan.get("status") == "SUCCESS":
        print("✗ ERROR: Zero hours should be rejected")
        return False
    print(f"✓ Zero hours rejected: {plan.get('message')}")
    
    # Test 2: Negative hours
    plan = create_study_plan(
        exam_date=exam_date,
        available_hours=-2.0,
        topics=["Topic1"],
        subject="Test",
        performance=None,
        db_path="test_hours.db"
    )
    if plan.get("status") == "SUCCESS":
        print("✗ ERROR: Negative hours should be rejected")
        return False
    print(f"✓ Negative hours rejected: {plan.get('message')}")
    
    # Test 3: Excessive hours (>16)
    plan = create_study_plan(
        exam_date=exam_date,
        available_hours=20.0,
        topics=["Topic1"],
        subject="Test",
        performance=None,
        db_path="test_hours.db"
    )
    if plan.get("status") == "SUCCESS":
        print("✗ ERROR: Excessive hours (>16) should be rejected")
        return False
    print(f"✓ Excessive hours rejected: {plan.get('message')}")
    
    # Test 4: Valid hours
    plan = create_study_plan(
        exam_date=exam_date,
        available_hours=4.0,
        topics=["Topic1"],
        subject="Test",
        performance=None,
        db_path="test_hours.db"
    )
    if plan.get("status") != "SUCCESS":
        print(f"✗ ERROR: Valid hours should be accepted: {plan.get('message')}")
        return False
    print(f"✓ Valid hours accepted: 4.0 hours/day")
    
    import os
    try:
        os.remove("test_hours.db")
    except:
        pass
    
    return True

def test_quiz_scoring_accuracy():
    """Test quiz scoring with various answer combinations"""
    print("\n=== EDGE CASE 5: Quiz Scoring Accuracy ===")
    
    db = get_db("test_scoring.db")
    db.reset_database()
    
    quiz = generate_quiz("Test Topic", "easy", 4, db_path="test_scoring.db")
    questions = quiz["questions"]
    
    # Test 1: All correct
    answers_all_correct = {str(q["id"]): q["correct_answer"] for q in questions}
    result = record_quiz_submission(
        topic=quiz["topic"],
        difficulty=quiz["difficulty"],
        questions=questions,
        user_answers=answers_all_correct,
        db_path="test_scoring.db"
    )
    
    if result["score"] != len(questions):
        print(f"✗ ERROR: All correct should score {len(questions)}, got {result['score']}")
        return False
    if abs(result["percentage"] - 100.0) > 0.1:
        print(f"✗ ERROR: All correct should be 100%, got {result['percentage']}")
        return False
    print(f"✓ All correct: {result['score']}/{result['total']} = {result['percentage']}%")
    
    # Test 2: All wrong
    answers_all_wrong = {str(q["id"]): "Wrong Answer" for q in questions}
    result = record_quiz_submission(
        topic="Test Topic 2",  # Different topic to avoid dedup
        difficulty=quiz["difficulty"],
        questions=questions,
        user_answers=answers_all_wrong,
        db_path="test_scoring.db"
    )
    
    if result["score"] != 0:
        print(f"✗ ERROR: All wrong should score 0, got {result['score']}")
        return False
    if result["percentage"] != 0.0:
        print(f"✗ ERROR: All wrong should be 0%, got {result['percentage']}")
        return False
    print(f"✓ All wrong: {result['score']}/{result['total']} = {result['percentage']}%")
    
    # Test 3: Half correct
    answers_half = {
        str(questions[0]["id"]): questions[0]["correct_answer"],
        str(questions[1]["id"]): questions[1]["correct_answer"],
        str(questions[2]["id"]): "Wrong",
        str(questions[3]["id"]): "Wrong",
    }
    result = record_quiz_submission(
        topic="Test Topic 3",
        difficulty=quiz["difficulty"],
        questions=questions,
        user_answers=answers_half,
        db_path="test_scoring.db"
    )
    
    expected_score = 2
    expected_pct = 50.0
    if result["score"] != expected_score:
        print(f"✗ ERROR: Half correct should score {expected_score}, got {result['score']}")
        return False
    if abs(result["percentage"] - expected_pct) > 0.1:
        print(f"✗ ERROR: Half correct should be ~{expected_pct}%, got {result['percentage']}")
        return False
    print(f"✓ Half correct: {result['score']}/{result['total']} = {result['percentage']}%")
    
    import os
    try:
        os.remove("test_scoring.db")
    except:
        pass
    
    return True

def test_performance_classification():
    """Test performance classification thresholds"""
    print("\n=== EDGE CASE 6: Performance Classification ===")
    
    from tools.performance import classify_score
    
    # Test thresholds - classify_score returns a string, not a dict
    tests = [
        (85.0, "Strong"),
        (80.0, "Strong"),
        (79.9, "Developing"),
        (70.0, "Developing"),
        (60.0, "Developing"),
        (59.9, "Needs Attention"),
        (40.0, "Needs Attention"),
        (0.0, "Needs Attention"),
    ]
    
    for score, expected_classification in tests:
        result = classify_score(score)
        if result != expected_classification:
            print(f"✗ ERROR: Score {score}% should be '{expected_classification}', got '{result}'")
            return False
    
    print(f"✓ All {len(tests)} classification thresholds correct")
    
    return True

def main():
    """Run all edge case tests"""
    print("=" * 60)
    print("EDUSYNC AI - EDGE CASE & ERROR SCENARIO TESTING")
    print("=" * 60)
    
    tests = [
        test_empty_database_workflows,
        test_invalid_exam_dates,
        test_duplicate_quiz_submission,
        test_invalid_study_hours,
        test_quiz_scoring_accuracy,
        test_performance_classification,
    ]
    
    results = []
    for test in tests:
        try:
            success = test()
            results.append((test.__name__, success))
        except Exception as e:
            print(f"\n✗ EXCEPTION in {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test.__name__, False))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL EDGE CASES HANDLED CORRECTLY")
        return 0
    else:
        print(f"\n⚠️  {total - passed} EDGE CASE(S) FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
