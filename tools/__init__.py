"""
EduSync AI — Tools Package
Exposes the 6 callable agent tools with uniform interfaces.
"""

from tools.document_search import document_search
from tools.quiz_generator import generate_quiz, score_quiz, record_quiz_submission
from tools.performance import analyze_performance, classify_score
from tools.study_planner import create_study_plan, parse_and_validate_exam_date
from tools.progress import update_progress, get_student_summary

__all__ = [
    "document_search",
    "generate_quiz",
    "score_quiz",
    "record_quiz_submission",
    "analyze_performance",
    "classify_score",
    "create_study_plan",
    "parse_and_validate_exam_date",
    "update_progress",
    "get_student_summary",
]
