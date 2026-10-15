"""
Comprehensive workflow testing to identify application errors.
"""
import sys
from datetime import date, timedelta
from services.persistence import get_db
from services.document_processor import extract_text_from_pdf, chunk_document_pages, TFIDFSearchEngine
from services.sample_data import populate_sample_dbms_data, populate_sample_quiz_history
from tools.document_search import document_search
from tools.quiz_generator import generate_quiz, record_quiz_submission
from tools.performance import analyze_performance
from tools.study_planner import create_study_plan
from tools.progress import get_student_summary
from agent.orchestrator import MultiToolOrchestrator

DB_PATH = "edusync.db"

def test_workflow_1_document_upload_and_search():
    """Test: Upload PDF, index, search, re-upload without duplicates"""
    print("\n=== WORKFLOW 1: Document Upload & Search ===")
    db = get_db(DB_PATH)
    
    # Load sample data
    populate_sample_dbms_data(db, force=False)
    
    # Get documents
    docs = db.get_documents()
    print(f"✓ Documents loaded: {len(docs)}")
    
    # Search for content
    result = document_search("normalization", top_k=3, db_path=DB_PATH)
    print(f"✓ Search result: found={result.get('found')}, chunks={len(result.get('chunks', []))}")
    
    # Re-upload same document (should not duplicate)
    initial_count = len(db.get_documents())
    populate_sample_dbms_data(db, force=False)
    final_count = len(db.get_documents())
    
    if initial_count == final_count:
        print(f"✓ No duplicates created: {initial_count} == {final_count}")
    else:
        print(f"✗ ERROR: Duplicates created! {initial_count} != {final_count}")
        return False
    
    return True

def test_workflow_2_quiz_generation_and_submission():
    """Test: Generate quiz, submit answers, verify score and history"""
    print("\n=== WORKFLOW 2: Quiz Generation & Submission ===")
    db = get_db(DB_PATH)
    
    # Generate quiz
    quiz = generate_quiz(
        topic="Indexing & Storage",
        difficulty="medium",
        number_of_questions=3,
        db_path=DB_PATH,
        api_key=None
    )
    
    if quiz.get("status") != "SUCCESS":
        print(f"✗ ERROR: Quiz generation failed: {quiz.get('message')}")
        return False
    
    print(f"✓ Quiz generated: {len(quiz['questions'])} questions")
    
    # Submit answers (all correct)
    user_answers = {}
    for q in quiz["questions"]:
        user_answers[str(q["id"])] = q["correct_answer"]
    
    result = record_quiz_submission(
        topic=quiz["topic"],
        difficulty=quiz["difficulty"],
        questions=quiz["questions"],
        user_answers=user_answers,
        db_path=DB_PATH
    )
    
    expected_score = len(quiz["questions"])
    actual_score = result.get("score", 0)
    
    if actual_score == expected_score:
        print(f"✓ Score correct: {actual_score}/{result.get('total')}")
    else:
        print(f"✗ ERROR: Score mismatch! Expected {expected_score}, got {actual_score}")
        return False
    
    # Verify history
    attempts = db.get_quiz_attempts()
    print(f"✓ Quiz attempts recorded: {len(attempts)}")
    
    return True

def test_workflow_3_performance_analysis():
    """Test: Analyze performance and verify metrics"""
    print("\n=== WORKFLOW 3: Performance Analysis ===")
    
    perf = analyze_performance(db_path=DB_PATH)
    
    print(f"✓ Has data: {perf.get('has_data')}")
    print(f"✓ Total attempts: {perf.get('total_attempts')}")
    print(f"✓ Overall score: {perf.get('overall_score')}%")
    print(f"✓ Weak topics: {len(perf.get('weak_topics', []))}")
    print(f"✓ Strong topics: {len(perf.get('strong_topics', []))}")
    
    if not perf.get("has_data"):
        print("✗ ERROR: Performance should have data after quiz submission")
        return False
    
    return True

def test_workflow_4_study_plan_creation():
    """Test: Generate study plan, complete tasks, verify state"""
    print("\n=== WORKFLOW 4: Study Plan Creation ===")
    db = get_db(DB_PATH)
    
    # Get performance for plan
    perf = analyze_performance(db_path=DB_PATH)
    
    # Create study plan
    exam_date = (date.today() + timedelta(days=5)).isoformat()
    plan_result = create_study_plan(
        exam_date=exam_date,
        available_hours=3.0,
        topics=["Indexing & Storage", "Normalization", "Transactions & Concurrency"],
        subject="Database Management Systems",
        performance=perf,
        db_path=DB_PATH
    )
    
    if plan_result.get("status") != "SUCCESS":
        print(f"✗ ERROR: Study plan creation failed: {plan_result.get('message')}")
        return False
    
    print(f"✓ Study plan created: {plan_result.get('days_remaining')} days, {plan_result.get('total_tasks')} tasks")
    
    # Get tasks
    active_plan = db.get_active_study_plan()
    tasks = db.get_study_tasks(active_plan["id"])
    
    print(f"✓ Tasks retrieved: {len(tasks)}")
    
    # Complete first task
    if tasks:
        task_id = tasks[0]["id"]
        db.toggle_task_completion(task_id, True)
        updated_tasks = db.get_study_tasks(active_plan["id"])
        completed_count = sum(1 for t in updated_tasks if t["completed"] == 1)
        print(f"✓ Task completed: {completed_count} completed tasks")
    
    return True

def test_workflow_5_agent_multiple_queries():
    """Test: Submit multiple AI queries and verify each gets correct response"""
    print("\n=== WORKFLOW 5: Multiple AI Tutor Queries ===")
    
    orch = MultiToolOrchestrator(db_path=DB_PATH, api_key=None)
    
    queries = [
        "What topics should I study today?",
        "Find information about normalization",
        "Generate a quiz on indexing"
    ]
    
    results = []
    for i, query in enumerate(queries):
        print(f"\n  Query {i+1}: {query}")
        result = orch.run(query)
        results.append(result)
        print(f"  ✓ Response received: {len(result.final_response)} chars")
        print(f"  ✓ Traces: {len(result.traces)}")
    
    # Verify all queries got responses
    for i, result in enumerate(results):
        if not result.final_response or len(result.final_response) < 10:
            print(f"✗ ERROR: Query {i+1} got empty or invalid response")
            return False
    
    print(f"\n✓ All {len(queries)} queries handled successfully")
    return True

def test_workflow_6_page_navigation_state():
    """Test: Verify navigation state persistence"""
    print("\n=== WORKFLOW 6: Page Navigation State ===")
    db = get_db(DB_PATH)
    
    # Verify data persists across navigation
    docs_before = len(db.get_documents())
    attempts_before = len(db.get_quiz_attempts())
    plan_before = db.get_active_study_plan()
    
    # Simulate state check
    docs_after = len(db.get_documents())
    attempts_after = len(db.get_quiz_attempts())
    plan_after = db.get_active_study_plan()
    
    if docs_before != docs_after:
        print(f"✗ ERROR: Document count changed: {docs_before} != {docs_after}")
        return False
    
    if attempts_before != attempts_after:
        print(f"✗ ERROR: Quiz attempts changed: {attempts_before} != {attempts_after}")
        return False
    
    print(f"✓ State persists: {docs_after} docs, {attempts_after} attempts")
    return True

def test_workflow_7_database_initialization():
    """Test: Reset and reinitialize database"""
    print("\n=== WORKFLOW 7: Database Reset & Initialization ===")
    db = get_db(DB_PATH)
    
    # Reset database
    db.reset_database()
    print("✓ Database reset")
    
    # Verify clean state
    docs = db.get_documents()
    attempts = db.get_quiz_attempts()
    plan = db.get_active_study_plan()
    
    if len(docs) != 0:
        print(f"✗ ERROR: Documents not cleared: {len(docs)}")
        return False
    
    if len(attempts) != 0:
        print(f"✗ ERROR: Quiz attempts not cleared: {len(attempts)}")
        return False
    
    if plan is not None:
        print(f"✗ ERROR: Study plan not cleared")
        return False
    
    print("✓ Database in clean state")
    
    # Reload sample data
    populate_sample_dbms_data(db, force=True)
    populate_sample_quiz_history(db, force=True)
    
    docs_after = len(db.get_documents())
    attempts_after = len(db.get_quiz_attempts())
    
    print(f"✓ Sample data reloaded: {docs_after} docs, {attempts_after} attempts")
    
    return True

def main():
    """Run all workflow tests"""
    print("=" * 60)
    print("EDUSYNC AI - COMPREHENSIVE WORKFLOW TESTING")
    print("=" * 60)
    
    tests = [
        test_workflow_1_document_upload_and_search,
        test_workflow_2_quiz_generation_and_submission,
        test_workflow_3_performance_analysis,
        test_workflow_4_study_plan_creation,
        test_workflow_5_agent_multiple_queries,
        test_workflow_6_page_navigation_state,
        test_workflow_7_database_initialization,
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
        print("\n🎉 ALL WORKFLOWS PASSED - APPLICATION READY")
        return 0
    else:
        print(f"\n⚠️  {total - passed} WORKFLOW(S) FAILED - NEEDS FIXING")
        return 1

if __name__ == "__main__":
    sys.exit(main())
