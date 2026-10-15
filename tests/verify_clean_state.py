"""Quick clean-state verification for the release gate."""
from services.persistence import get_db
from services.sample_data import populate_sample_dbms_data, populate_sample_quiz_history
from tools.performance import analyze_performance

db = get_db("edusync.db")
db.reset_database()

# First load
a = populate_sample_dbms_data(db, force=False)
b = populate_sample_quiz_history(db, force=False)

s       = db.get_dashboard_stats()
docs    = db.get_documents()
quizzes = db.get_quiz_attempts()
logs    = db.get_recent_agent_logs()
plan    = db.get_active_study_plan()
perf    = analyze_performance("edusync.db")

print("=== AFTER FIRST LOAD ===")
print(f"Documents       : {s['document_count']}")
print(f"Quiz attempts   : {s['quiz_attempts_count']}")
print(f"Avg score       : {s['average_quiz_score']}%")
print(f"Agent logs      : {len(logs)}")
print(f"Active plan     : {plan is not None}")
print(f"Perf has_data   : {perf['has_data']}")
if perf['has_data']:
    print(f"Topics          : {list(perf['topic_breakdown'].keys())}")

# Idempotency check (second load)
a2 = populate_sample_dbms_data(db, force=False)
b2 = populate_sample_quiz_history(db, force=False)

docs2    = db.get_documents()
quizzes2 = db.get_quiz_attempts()

print()
print("=== IDEMPOTENCY (SECOND LOAD) ===")
print(f"Docs added   : {a2}  (expected: False)")
print(f"Quizzes added: {b2}  (expected: False)")
print(f"Doc count    : {len(docs2)}  (expected: 2)")
print(f"Quiz count   : {len(quizzes2)}  (expected: 2)")

assert not a2,          "FAIL: duplicate docs on second load"
assert not b2,          "FAIL: duplicate quizzes on second load"
assert len(docs2) == 2, f"FAIL: expected 2 docs, got {len(docs2)}"
assert len(quizzes2) == 2, f"FAIL: expected 2 quiz attempts, got {len(quizzes2)}"

print()
print("=== RESULT: ALL CHECKS PASSED ===")
