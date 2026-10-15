from services.persistence import get_db
db = get_db('edusync_test.db')
db.reset_database()
from services.sample_data import populate_sample_quiz_history
result = populate_sample_quiz_history(db, force=True)
print(f'populate result: {result}')
attempts = db.get_quiz_attempts()
print(f'total attempts: {len(attempts)}')
for a in attempts:
    print(f"  Topic={a['topic']}, Score={a['score']}, is_sample={a.get('is_sample')}")
stats = db.get_dashboard_stats()
print(f"stats quiz_attempts={stats['quiz_attempts_count']}, all_attempts={stats.get('all_quiz_attempts_count')}")
perf = db.get_quiz_attempts(real_only=False)
print(f"real_only=False: {len(perf)} attempts")
