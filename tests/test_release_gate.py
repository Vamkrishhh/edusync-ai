"""Final release candidate: full journey test executed programmatically."""
import sys, os
sys.path.insert(0, os.path.abspath("."))
sys.stdout.reconfigure(encoding="utf-8")

from services.persistence import get_db
from services.sample_data import populate_sample_dbms_data, populate_sample_quiz_history
from tools.performance import analyze_performance
from tools.study_planner import parse_and_validate_exam_date
from tools.quiz_generator import generate_quiz, record_quiz_submission
from tools.document_search import document_search
from agent.orchestrator import MultiToolOrchestrator

DB = "edusync.db"
db = get_db(DB)

# --- STEP 1: RESET ---
print("=== STEP 1: RESET ===")
db.reset_database()
s = db.get_dashboard_stats()
assert s["document_count"] == 0
assert s["quiz_attempts_count"] == 0
print(f"  OK — clean state: docs={s['document_count']} quizzes={s['quiz_attempts_count']}")

# --- STEP 2: LOAD DEMO DATA ---
print("\n=== STEP 2: LOAD DEMO DATA ===")
added_docs   = populate_sample_dbms_data(db, force=False)
added_quizzes = populate_sample_quiz_history(db, force=False)
assert added_docs   is True,  "FAIL: Expected True on first load (docs)"
assert added_quizzes is True, "FAIL: Expected True on first load (quizzes)"
s = db.get_dashboard_stats()
print(f"  OK — docs={s['document_count']} quizzes={s['quiz_attempts_count']} avg_score={s['average_quiz_score']}%")

# --- STEP 3: KNOWLEDGE PAGE ---
print("\n=== STEP 3: KNOWLEDGE PAGE ===")
docs = db.get_documents()
for d in docs:
    print(f"  [{d['id']}] {d['filename']} | {d['file_type']} | {d['num_pages']}p | {d['num_chunks']} sections")
assert len(docs) == 2, f"FAIL: Expected 2 docs, got {len(docs)}"
print(f"  OK — {len(docs)} documents, no duplicates")

# --- STEP 4A: REAL PERFORMANCE DATA (should be empty) ---
print("\n=== STEP 4A: REAL PERFORMANCE (after demo load) ===")
perf_real = analyze_performance(db_path=DB)
print(f"  Real data - has_data={perf_real['has_data']} attempts={perf_real['total_attempts']}")
assert perf_real["has_data"] is False, "FAIL: real performance should be empty with only sample data"
assert perf_real["total_attempts"] == 0, "FAIL: real attempts should be 0"
print(f"  OK — real metrics correctly empty (demo data excluded)")

# --- STEP 4B: SAMPLE-INCLUSIVE PERFORMANCE DATA ---
print("\n=== STEP 4B: SAMPLE-INCLUSIVE PERFORMANCE ===")
perf_demo = analyze_performance(db_path=DB, include_sample=True)
print(f"  Demo-inclusive - has_data={perf_demo['has_data']} attempts={perf_demo['total_attempts']}")
if perf_demo["has_data"]:
    for t, d in perf_demo["topic_breakdown"].items():
        print(f"  {t}: {d['percentage']}% ({d['classification']})")
assert perf_demo["has_data"] is True, "FAIL: expected performance data from demo quizzes when include_sample=True"
assert perf_demo["total_attempts"] == 2, "FAIL: expected exactly 2 demo attempts"

# --- STEP 5: AI TUTOR ORCHESTRATION ---
print("\n=== STEP 5: AI TUTOR — EXAM PREP ===")
orch = MultiToolOrchestrator(db_path=DB, api_key=None)
result = orch.run("Prepare me for my DBMS exam in five days.")
assert result.success, "FAIL: orchestrator returned success=False"
tool_names = [t.tool_name for t in result.traces]
print(f"  success={result.success}")
print(f"  tools={tool_names}")
print(f"  iterations={result.iterations}")
print(f"  response_preview={result.final_response[:200]}")
assert len(result.traces) >= 3, "FAIL: expected at least 3 tool calls"

# --- STEP 6: QUIZ ---
print("\n=== STEP 6: QUIZ — NORMALIZATION ===")
quiz = generate_quiz(topic="Normalization", difficulty="easy", num_questions=4, db_path=DB, api_key=None)
assert quiz["status"] == "SUCCESS", f"FAIL: quiz status={quiz['status']}"
print(f"  generated {len(quiz['questions'])} questions")
user_answers = {str(q["id"]): q["options"][0] for q in quiz["questions"]}
res = record_quiz_submission(quiz, user_answers, DB)
pct = int(res["score"] / res["total_questions"] * 100)
print(f"  submitted — score={res['score']}/{res['total_questions']} ({pct}%)")

# --- STEP 7A: REAL PERFORMANCE UPDATE (should now have 1 real attempt) ---
print("\n=== STEP 7A: REAL PERFORMANCE UPDATE ===")
perf_real_after = analyze_performance(db_path=DB)
print(f"  Real performance: has_data={perf_real_after['has_data']} attempts={perf_real_after['total_attempts']}")
assert perf_real_after["has_data"] is True, "FAIL: should have real data after quiz submission"
assert perf_real_after["total_attempts"] == 1, "FAIL: should have exactly 1 real attempt"
for t, d in perf_real_after["topic_breakdown"].items():
    print(f"  {t}: {d['percentage']}% ({d['classification']})")
print(f"  OK — real metrics now populated from student quiz")

# --- STEP 7B: SAMPLE-INCLUSIVE PERFORMANCE UPDATE (should have 1 real + 2 sample = 3 total) ---
print("\n=== STEP 7B: SAMPLE-INCLUSIVE PERFORMANCE UPDATE ===")
perf_all_after = analyze_performance(db_path=DB, include_sample=True)
print(f"  All data: has_data={perf_all_after['has_data']} attempts={perf_all_after['total_attempts']}")
assert perf_all_after["has_data"] is True
assert perf_all_after["total_attempts"] == 3, f"FAIL: expected 3 total (1 real + 2 sample), got {perf_all_after['total_attempts']}"
for t, d in perf_all_after["topic_breakdown"].items():
    print(f"  {t}: {d['percentage']}% ({d['classification']})")
print(f"  OK — demo-inclusive shows all 3 attempts")

# --- STEP 8: STUDY PLAN ---
print("\n=== STEP 8: STUDY PLAN ===")
plan = db.get_active_study_plan()
if plan:
    val   = parse_and_validate_exam_date(plan["exam_date"])
    tasks = db.get_study_tasks(plan["id"])
    print(f"  subject={plan['subject']} exam={plan['exam_date']} days_remaining={val.get('days_remaining')} tasks={len(tasks)}")
    if tasks:
        db.toggle_task_completion(tasks[0]["id"], True)
        refreshed = db.get_study_tasks(plan["id"])
        completed = [t for t in refreshed if t["completed"] == 1]
        assert len(completed) >= 1, "FAIL: task completion did not persist"
        print(f"  OK — marked task '{tasks[0]['topic']}' complete. Completed count: {len(completed)}")
else:
    print("  WARNING: No active study plan (AI created one above, should exist)")

# --- STEP 9: OVERVIEW STATE (verify real attempts only) ---
print("\n=== STEP 9: DASHBOARD STATE ===")
s2 = db.get_dashboard_stats()
print(f"  docs={s2['document_count']} real_quizzes={s2['quiz_attempts_count']} avg_score={s2['average_quiz_score']}%")
print(f"  all_quizzes={s2['all_quiz_attempts_count']} (real + sample)")
assert s2["document_count"] == 2, "FAIL: expected 2 documents"
assert s2["quiz_attempts_count"] == 1, f"FAIL: expected 1 real quiz attempt, got {s2['quiz_attempts_count']}"
assert s2["all_quiz_attempts_count"] == 3, f"FAIL: expected 3 total attempts (1 real + 2 sample), got {s2['all_quiz_attempts_count']}"
print(f"  OK — real metrics: 1 quiz attempt, sample data isolated")

# --- STEP 10: IDEMPOTENCY / DUPLICATE LOAD ---
print("\n=== STEP 10: DUPLICATE DEMO LOAD ===")
a2 = populate_sample_dbms_data(db, force=False)
b2 = populate_sample_quiz_history(db, force=False)
assert a2 is False, f"FAIL: second doc load should return False, got {a2}"
assert b2 is False, f"FAIL: second quiz load should return False, got {b2}"
docs3 = db.get_documents()
assert len(docs3) == 2, f"FAIL: doc count after 2nd load = {len(docs3)}"
print(f"  OK — both loads returned False; doc count unchanged at {len(docs3)}")

# --- STEP 11: BLANK TOPIC QUIZ ---
print("\n=== STEP 11: BLANK TOPIC QUIZ (negative) ===")
q_blank = generate_quiz(topic="", difficulty="easy", num_questions=4, db_path=DB, api_key=None)
assert q_blank["status"] in ("SUCCESS", "FALLBACK", "ERROR", "FAILURE", "FAILED"), f"FAIL: unexpected status {q_blank['status']}"
print(f"  OK — returned status={q_blank['status']} (no crash)")

# --- STEP 12: PAST EXAM DATE ---
print("\n=== STEP 12: PAST EXAM DATE (negative) ===")
v = parse_and_validate_exam_date("2020-01-01")
assert v.get("is_valid") is False, f"FAIL: past date should be invalid, got {v}"
print(f"  OK — is_valid={v.get('is_valid')} error='{v.get('error', '')[:60]}'")

# --- STEP 13: DOCUMENT SEARCH ---
print("\n=== STEP 13: DOCUMENT SEARCH ===")
sr = document_search("normalization", db_path=DB)
assert sr.get("found") is True and sr.get("count", 0) > 0, "FAIL: no chunks found matching normalization"
print(f"  OK — found {sr['count']} chunks, top result from: {sr['chunks'][0].get('source')}")

print("\n==========================================")
print("ALL 13 ACCEPTANCE CHECKS PASSED")
print("==========================================")
