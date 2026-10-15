"""
Programmatic audit of all seven pages via AppTest.
Checks for exceptions, stale data, broken workflows, and logic errors.
"""
import sys, os
sys.path.insert(0, '.')
os.environ['STREAMLIT_TESTING'] = '1'

from streamlit.testing.v1 import AppTest
from services.persistence import DatabaseManager
from services.sample_data import populate_sample_dbms_data, populate_sample_quiz_history
from tools.performance import analyze_performance
from tools.study_planner import create_study_plan
from datetime import date, timedelta

db = DatabaseManager('edusync.db')
stats = db.get_dashboard_stats()
print('=== PRE-TEST DB STATE ===')
print('  docs:', stats['document_count'], '  chunks:', stats['chunk_count'])
print('  quizzes:', stats['quiz_attempts_count'], '  avg_score:', stats['average_quiz_score'])
print('  tasks:', stats['total_study_tasks'], '  completed:', stats['completed_study_tasks'])
plan = db.get_active_study_plan()
print('  active_plan:', plan['subject'] if plan else 'none')

print()
print('=== PAGE LOAD TESTS ===')

pages = [
    '📊 Dashboard',
    '📚 Document Library',
    '🤖 AI Study Assistant',
    '📝 Quiz Generator',
    '📈 Performance Analyzer',
    '📅 Study Planner',
    '🎯 Progress Tracker',
]

for page in pages:
    at = AppTest.from_file('app.py', default_timeout=45)
    at.run()
    radio = at.sidebar.radio[0]
    radio.set_value(page).run()
    ex = at.exception
    if ex:
        print(f'  FAIL  {page}: {[str(e)[:80] for e in ex]}')
    else:
        print(f'  PASS  {page}')

print()
print('=== WORKFLOW: Performance metrics match quiz attempts ===')
perf = analyze_performance(db_path='edusync.db')
attempts = db.get_quiz_attempts()
print('  DB quiz attempts:', len(attempts))
print('  perf.total_attempts:', perf['total_attempts'])
print('  Match:', len(attempts) == perf['total_attempts'])
print('  overall_score:', perf['overall_score'])
# Verify manual calculation
if attempts:
    manual_avg = round(sum(float(a['percentage']) for a in attempts) / len(attempts), 1)
    print('  Manual avg:', manual_avg, '  Match:', abs(manual_avg - float(perf['overall_score'])) < 0.2)

print()
print('=== WORKFLOW: Study plan date validity ===')
if plan:
    from tools.study_planner import parse_and_validate_exam_date
    val = parse_and_validate_exam_date(plan['exam_date'])
    print('  exam_date:', plan['exam_date'])
    print('  is_valid:', val.get('is_valid'))
    print('  days_remaining:', val.get('days_remaining', 'expired/invalid'))
    if not val.get('is_valid'):
        print('  ERROR: Active plan has an expired exam date - dashboard will show negative days!')

print()
print('=== WORKFLOW: Quiz generate + submit ===')
from tools.quiz_generator import generate_quiz, record_quiz_submission
import tempfile
tmp_db = tempfile.mktemp(suffix='.db')
tdb = DatabaseManager(tmp_db)
populate_sample_dbms_data(tdb, force=False)
q = generate_quiz('Normalization', difficulty='easy', number_of_questions=3, db_path=tmp_db, api_key=None)
print('  Quiz generated:', q['status'], '  questions:', len(q.get('questions', [])))
if q['status'] == 'SUCCESS' and q.get('questions'):
    ua = {str(qq['id']): qq['correct_answer'] for qq in q['questions']}
    res = record_quiz_submission(
        topic=q['topic'], difficulty=q['difficulty'],
        questions=q['questions'], user_answers=ua, db_path=tmp_db
    )
    print('  Submit result:', res.get('score'), '/', res.get('total_questions'), '=', res.get('percentage'), '%')
    print('  attempt_id present:', 'attempt_id' in res)
    print('  details present:', 'details' in res or 'graded_questions' in res)

import os as _os
try: _os.remove(tmp_db)
except: pass

print()
print('=== DONE ===')
