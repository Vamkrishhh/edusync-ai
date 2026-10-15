"""
EduSync AI — Specialist Agents
Implements KnowledgeAgent, AssessmentAgent, PerformanceAgent, PlanningAgent, and ProgressAgent.
Each agent encapsulates its domain, delegates to existing tools, and returns structured data.
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from agent.base import BaseAgent
from tools.document_search import document_search
from tools.quiz_generator import generate_quiz
from tools.performance import analyze_performance
from tools.study_planner import create_study_plan
from tools.progress import get_student_summary, update_progress


class KnowledgeAgent(BaseAgent):
    """
    KnowledgeAgent: Specialist for syllabus, document indexing, and semantic passage retrieval.
    Wraps document_search tool.
    """

    def __init__(self, db_path: str = "edusync.db"):
        super().__init__(
            name="KnowledgeAgent",
            description="Retrieves document chunks, syllabus topics, and reference passages from uploaded materials.",
            db_path=db_path,
        )

    def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        top_k = context.get("top_k", 5) if context else 5
        search_query = context.get("search_query", query) if context else query

        res = document_search(query=search_query, top_k=top_k, db_path=self.db_path)
        return {
            "status": res.get("status", "SUCCESS"),
            "agent": self.name,
            "message": res.get("message", f"Retrieved {res.get('count', 0)} document passage(s)."),
            "data": res,
            "chunks": res.get("chunks", []),
            "count": res.get("count", 0),
            "found": res.get("found", False),
        }


class AssessmentAgent(BaseAgent):
    """
    AssessmentAgent: Specialist for generating quizzes, diagnostic questions, and assessment tracking.
    Wraps quiz_generator tool.
    """

    def __init__(self, db_path: str = "edusync.db", api_key: Optional[str] = None):
        super().__init__(
            name="AssessmentAgent",
            description="Generates grounded multiple-choice quizzes and diagnostic assessments.",
            db_path=db_path,
        )
        self.api_key = api_key

    def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        topic = context.get("topic", "Normalization") if context else "Normalization"
        difficulty = context.get("difficulty", "medium") if context else "medium"
        num_questions = context.get("number_of_questions", 5) if context else 5

        res = generate_quiz(
            topic=topic,
            difficulty=difficulty,
            number_of_questions=num_questions,
            db_path=self.db_path,
            api_key=self.api_key,
        )
        return {
            "status": res.get("status", "SUCCESS"),
            "agent": self.name,
            "message": res.get("message", f"Generated assessment for topic '{topic}'."),
            "data": res,
            "topic": topic,
            "quiz": res,
        }


class PerformanceAgent(BaseAgent):
    """
    PerformanceAgent: Specialist for analyzing quiz history, identifying weak topics and mastery levels.
    Wraps performance analysis tool.
    """

    def __init__(self, db_path: str = "edusync.db"):
        super().__init__(
            name="PerformanceAgent",
            description="Analyzes assessment results, detects knowledge gaps, and calculates topic mastery.",
            db_path=db_path,
        )

    def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        perf_res = analyze_performance(db_path=self.db_path)
        weak_count = len(perf_res.get("weak_topics", []))
        summary_msg = (
            f"Assessed {perf_res['total_attempts']} quiz attempt(s). Identified {weak_count} topic(s) needing attention."
            if perf_res.get("has_data")
            else "No past quizzes found. Calibrated with baseline diagnostic parameters."
        )

        return {
            "status": "SUCCESS",
            "agent": self.name,
            "message": summary_msg,
            "data": perf_res,
            "weak_topics": perf_res.get("weak_topics", []),
            "strong_topics": perf_res.get("strong_topics", []),
            "developing_topics": perf_res.get("developing_topics", []),
            "has_data": perf_res.get("has_data", False),
        }


class PlanningAgent(BaseAgent):
    """
    PlanningAgent: Specialist for creating and adapting personalized study plans.
    Wraps study_planner tool.
    """

    def __init__(self, db_path: str = "edusync.db"):
        super().__init__(
            name="PlanningAgent",
            description="Generates and adapts timetable schedules calibrated against exam deadlines and student weak areas.",
            db_path=db_path,
        )

    def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ctx = context or {}
        days = ctx.get("days", 5)
        subject = ctx.get("subject", "Database Management Systems")
        exam_date = ctx.get("exam_date") or (date.today() + timedelta(days=days)).isoformat()
        daily_hours = ctx.get("daily_hours", 3.0)
        perf_data = ctx.get("performance", {})
        topics = ctx.get("topics") or [
            "ER & Relational Model",
            "SQL & Query Optimization",
            "Normalization",
            "Transactions & Concurrency",
            "Indexing & Storage",
        ]

        plan_res = create_study_plan(
            exam_date=exam_date,
            available_hours=daily_hours,
            topics=topics,
            performance=perf_data,
            subject=subject,
            db_path=self.db_path,
        )

        return {
            "status": plan_res.get("status", "SUCCESS"),
            "agent": self.name,
            "message": plan_res.get("message", f"Created {days}-day plan for {subject}."),
            "data": plan_res,
            "study_plan": plan_res,
        }


class ProgressAgent(BaseAgent):
    """
    ProgressAgent: Specialist for logging, tracking, and summarizing student progress across modules.
    Wraps progress tools.
    """

    def __init__(self, db_path: str = "edusync.db"):
        super().__init__(
            name="ProgressAgent",
            description="Tracks completed tasks, logs milestone completions, and returns student progress overview.",
            db_path=db_path,
        )

    def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ctx = context or {}
        action = ctx.get("action", "summary")

        if action == "update" and "task_id" in ctx:
            upd_res = update_progress(
                task_id=ctx["task_id"],
                completed=ctx.get("completed", True),
                db_path=self.db_path,
            )
            return {
                "status": upd_res.get("status", "SUCCESS"),
                "agent": self.name,
                "message": upd_res.get("message", "Progress updated."),
                "data": upd_res,
            }

        # Default action: summary
        summary_res = get_student_summary(db_path=self.db_path)
        return {
            "status": "SUCCESS",
            "agent": self.name,
            "message": (
                f"Student holds {summary_res.get('documents_count', 0)} document(s) and "
                f"{summary_res.get('dashboard_stats', {}).get('quiz_attempts_count', 0)} quiz attempt(s)."
            ),
            "data": summary_res,
            "summary": summary_res,
        }
