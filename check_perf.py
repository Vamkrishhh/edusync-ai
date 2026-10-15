import sys
sys.path.insert(0, '.')
from services.persistence import DatabaseManager
from tools.performance import analyze_performance

db = DatabaseManager('edusync.db')
attempts = db.get_quiz_attempts()
print('All quiz attempts:')
total_score = 0
total_questions = 0
for a in attempts:
    pct = float(a['percentage'])
    s = a['score']
    tq = a['total_questions']
    total_score += s
    total_questions += tq
    print('  topic=' + a['topic'] + '  score=' + str(s) + '/' + str(tq) + '  pct=' + str(pct))

print()
correct_overall = round((total_score / total_questions) * 100.0, 1) if total_questions else 0
naive_avg = round(sum(float(a['percentage']) for a in attempts) / len(attempts), 1) if attempts else 0
print('Correct overall (weighted by total questions):', correct_overall)
print('Naive average of stored percentages:', naive_avg)

perf = analyze_performance(db_path='edusync.db')
print('analyze_performance overall_score:', perf['overall_score'])
print()
print('Dashboard stats avg_score:', db.get_dashboard_stats()['average_quiz_score'])
print()
# The discrepancy: analyze_performance uses score/total_questions (correct weighted calc)
# Dashboard uses AVG(percentage) from SQL (naive average of stored pct values)
# These differ when questions count varies across attempts
print('Discrepancy explanation:')
print('  performance.py overall_score = sum(score)/sum(questions) =', correct_overall)
print('  dashboard avg = AVG(percentage col) = SQL AVG of stored values')
print('  stored pct values:', [float(a['percentage']) for a in attempts])
print('  SQL AVG:', round(sum(float(a['percentage']) for a in attempts)/len(attempts), 1))
