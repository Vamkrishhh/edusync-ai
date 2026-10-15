"""
EduSync AI — Supervisor Agent
Coordinates multi-agent planning, delegates tasks to specialist agents,
synthesizes responses, and logs unified execution traces.
"""

import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from agent.base import BaseAgent
from agent.specialists import (
    KnowledgeAgent,
    AssessmentAgent,
    PerformanceAgent,
    PlanningAgent,
    ProgressAgent,
)
from agent.state import AgentResult, ToolTrace
from services.llm_service import get_llm_service
from services.persistence import get_db


class SupervisorAgent(BaseAgent):
    """
    SupervisorAgent:
    - Receives student request
    - Analyzes intent and plans execution
    - Coordinates specialist agents (KnowledgeAgent, AssessmentAgent, PerformanceAgent, PlanningAgent, ProgressAgent)
    - Synthesizes final grounded response
    """

    def __init__(self, db_path: str = "edusync.db", api_key: Optional[str] = None):
        super().__init__(
            name="SupervisorAgent",
            description="High-level orchestrator that plans, delegates to specialist agents, and synthesizes final response.",
            db_path=db_path,
        )
        self.api_key = api_key
        self.llm = get_llm_service(api_key=api_key)

        # Initialize specialists
        self.knowledge_agent = KnowledgeAgent(db_path=db_path)
        self.assessment_agent = AssessmentAgent(db_path=db_path, api_key=api_key)
        self.performance_agent = PerformanceAgent(db_path=db_path)
        self.planning_agent = PlanningAgent(db_path=db_path)
        self.progress_agent = ProgressAgent(db_path=db_path)

    def determine_intent(self, query: str) -> Dict[str, Any]:
        """
        Parses query to determine student intent, target timeline, subject, and specialist agents required.
        """
        q = query.strip().lower()

        # 1. Exam preparation workflow (e.g. "Prepare me for my DBMS exam in five days")
        days_match = re.search(r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*days?", q)
        word_to_num = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
        }

        days_val = 5
        if days_match:
            raw_d = days_match.group(1)
            days_val = word_to_num.get(raw_d, int(raw_d) if raw_d.isdigit() else 5)

        is_exam_prep = any(phrase in q for phrase in [
            "prepare me", "exam in", "exam in five", "upcoming exam", "prepare for my",
            "study plan for exam", "ready for exam", "exam preparation"
        ])

        if is_exam_prep or ("exam" in q and ("day" in q or "plan" in q or "prepare" in q)):
            subject = "Database Management Systems"
            if "dbms" in q:
                subject = "Database Management Systems (DBMS)"
            elif "operating system" in q or "os" in q.split():
                subject = "Operating Systems"
            elif "data structure" in q or "dsa" in q.split():
                subject = "Data Structures & Algorithms"

            return {
                "goal": "exam_preparation",
                "label": f"Comprehensive Exam Preparation ({days_val}-day timeline)",
                "days": days_val,
                "subject": subject,
                "agents": ["KnowledgeAgent", "PerformanceAgent", "PlanningAgent"],
            }

        # 2. Performance / Score Analysis
        if any(w in q for w in ["scored", "score", "performance", "weak", "weakness", "how did i do", "analytics", "learning gap", "how am i doing"]):
            return {
                "goal": "performance_analysis",
                "label": "Student Performance & Mastery Analysis",
                "agents": ["PerformanceAgent"],
            }

        # 3. Quiz / Assessment Request
        if any(phrase in q for phrase in ["quiz", "test me", "generate quiz", "take a quiz", "questions on", "practice test", "mcq"]):
            topic = "Normalization"
            for candidate in [
                "normalization", "indexing & storage", "indexing", "transactions & concurrency",
                "transactions", "sql", "relational model", "er model", "concurrency control"
            ]:
                if candidate in q:
                    topic = candidate.title()
                    break

            return {
                "goal": "quiz_generation",
                "label": f"Practice Quiz on '{topic}'",
                "topic": topic,
                "agents": ["KnowledgeAgent", "AssessmentAgent"],
            }

        # 4. Progress / Learning Status
        if any(w in q for w in ["progress", "summary", "how much completed", "status", "milestone"]):
            return {
                "goal": "student_progress",
                "label": "Student Progress Tracking & Status",
                "agents": ["ProgressAgent", "PerformanceAgent"],
            }

        # 5. Study Schedule / Timetable
        if any(w in q for w in ["study plan", "schedule", "routine", "timetable"]):
            return {
                "goal": "study_planning",
                "label": "Personalized Study Schedule Creation",
                "days": days_val,
                "agents": ["PerformanceAgent", "PlanningAgent"],
            }

        # 6. Document / Knowledge Retrieval
        if any(w in q for w in ["find", "search", "notes on", "what is", "explain", "look up", "information about"]):
            clean_q = re.sub(r"^(find|search|look up|what is|explain|information about|in my notes)\s*", "", q)
            clean_q = re.sub(r"in my notes.*$", "", clean_q).strip()
            return {
                "goal": "document_search",
                "label": f"Semantic Search for '{clean_q or query}'",
                "search_query": clean_q or query,
                "agents": ["KnowledgeAgent"],
            }

        # Default: Progress & General Advisory
        return {
            "goal": "student_summary",
            "label": "Student Learning Status & Academic Advisory",
            "agents": ["ProgressAgent", "PerformanceAgent"],
        }

    def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """
        Executes multi-agent workflow:
        1. Supervisor analyzes intent
        2. Specialist agents execute in required order with error isolation
        3. Supervisor synthesizes response
        4. Logs full multi-agent trace to SQLite
        """
        parsed_intent = self.determine_intent(query)
        goal = parsed_intent["goal"]
        traces: List[ToolTrace] = []
        extracted_data: Dict[str, Any] = {}
        participating_agents: List[str] = [self.name]
        step = 1

        mode = (
            f"AI Mode (Gemini: {self.llm.model_name})"
            if self.llm.is_available()
            else "Demo Mode (Deterministic Engine)"
        )

        # =========================================================================
        # SCENARIO 1: EXAM PREPARATION
        # Supervisor → KnowledgeAgent → PerformanceAgent → PlanningAgent (and Progress check)
        # =========================================================================
        if goal == "exam_preparation":
            days = parsed_intent.get("days", 5)
            subject = parsed_intent.get("subject", "Database Management Systems")
            calc_exam_date = (date.today() + timedelta(days=days)).isoformat()
            daily_hours = context.get("daily_hours", 3.0) if context else 3.0

            # Step 1: KnowledgeAgent retrieves syllabus topics & course scope
            search_query = f"{subject} syllabus unit topics"
            k_res = self.knowledge_agent.safe_run(
                query=search_query,
                context={"search_query": search_query, "top_k": 5}
            )
            extracted_data["knowledge"] = k_res
            participating_agents.append(self.knowledge_agent.name)
            traces.append(ToolTrace(
                step_number=step,
                tool_name="document_search",
                agent_name=self.knowledge_agent.name,
                arguments={"query": search_query, "top_k": 5},
                status=k_res["status"],
                summary=f"KnowledgeAgent retrieved {k_res.get('count', 0)} syllabus passage(s).",
                data=k_res.get("data"),
            ))
            step += 1

            # Step 2: ProgressAgent checks baseline records
            prog_res = self.progress_agent.safe_run(query="status")
            extracted_data["progress"] = prog_res
            participating_agents.append(self.progress_agent.name)
            traces.append(ToolTrace(
                step_number=step,
                tool_name="get_student_summary",
                agent_name=self.progress_agent.name,
                arguments={},
                status=prog_res["status"],
                summary=prog_res.get("message", "Progress snapshot recorded."),
                data=prog_res.get("data"),
            ))
            step += 1

            # Step 3: PerformanceAgent assesses past quizzes and weaknesses
            perf_res = self.performance_agent.safe_run(query="analyze")
            extracted_data["performance"] = perf_res
            participating_agents.append(self.performance_agent.name)
            weak_count = len(perf_res.get("weak_topics", []))
            traces.append(ToolTrace(
                step_number=step,
                tool_name="analyze_performance",
                agent_name=self.performance_agent.name,
                arguments={},
                status=perf_res["status"],
                summary=perf_res.get("message", f"Identified {weak_count} weak topic(s)."),
                data=perf_res.get("data"),
            ))
            step += 1

            # Step 4: PlanningAgent creates adaptive schedule
            plan_res = self.planning_agent.safe_run(
                query=f"Create {days}-day plan for {subject}",
                context={
                    "days": days,
                    "subject": subject,
                    "exam_date": calc_exam_date,
                    "daily_hours": daily_hours,
                    "performance": perf_res.get("data", {}),
                }
            )
            extracted_data["planning"] = plan_res
            extracted_data["study_plan"] = plan_res.get("data", plan_res)
            participating_agents.append(self.planning_agent.name)
            plan_data = plan_res.get("data", {})
            traces.append(ToolTrace(
                step_number=step,
                tool_name="create_study_plan",
                agent_name=self.planning_agent.name,
                arguments={
                    "exam_date": calc_exam_date,
                    "available_hours": daily_hours,
                    "subject": subject,
                },
                status=plan_res["status"],
                summary=plan_res.get("message", f"Generated {days}-day adaptive study plan."),
                data=plan_data,
            ))
            step += 1

            # Supervisor synthesizes final response
            if self.llm.is_available():
                final_text = self.llm.synthesize_response_llm(
                    query=query,
                    retrieved_chunks=k_res.get("chunks", []),
                    performance_summary=perf_res.get("data", {}),
                    study_plan=plan_data,
                )
            else:
                final_text = None

            weak_list = [w["topic"] for w in perf_res.get("weak_topics", [])]
            weak_str = ", ".join(weak_list) if weak_list else "None identified yet (calibrated to baseline)"

            if not final_text:
                total_hours = plan_data.get("total_study_hours", days * daily_hours)
                final_text = (
                    f"### 🎯 Exam Preparation Roadmap for {subject}\n\n"
                    f"**SupervisorAgent** coordinated 4 specialist agents to prepare your comprehensive study strategy for **{days} days** "
                    f"({daily_hours} hours/day):\n\n"
                    f"1. **KnowledgeAgent**: Extracted curriculum structure from course syllabus and identified 5 core modules.\n"
                    f"2. **ProgressAgent**: Evaluated document repository and confirmed baseline learning metrics.\n"
                    f"3. **PerformanceAgent**: Diagnosed current quiz scores. Weak areas prioritized: **{weak_str}**.\n"
                    f"4. **PlanningAgent**: Synthesized a prioritized {days}-day timetable allocating **{total_hours} total study hours**, "
                    f"reserving intensive review for weak topics, practice for the penultimate day, and mock test on the final day.\n\n"
                    f"**Next Steps:** Navigate to the **Study Planner** tab to see your day-by-day timetable and check off tasks."
                )

            recommended_action = (
                f"Navigate to Assessments and take a 5-question diagnostic quiz on "
                f"'{weak_list[0] if weak_list else 'Normalization'}'."
            )

        # =========================================================================
        # SCENARIO 2: QUIZ GENERATION
        # Supervisor → KnowledgeAgent → AssessmentAgent
        # =========================================================================
        elif goal == "quiz_generation":
            topic = parsed_intent.get("topic", "Normalization")

            # Step 1: KnowledgeAgent retrieves notes for grounding
            k_res = self.knowledge_agent.safe_run(
                query=topic,
                context={"search_query": topic, "top_k": 4}
            )
            extracted_data["knowledge"] = k_res
            participating_agents.append(self.knowledge_agent.name)
            traces.append(ToolTrace(
                step_number=step,
                tool_name="document_search",
                agent_name=self.knowledge_agent.name,
                arguments={"query": topic, "top_k": 4},
                status=k_res["status"],
                summary=f"KnowledgeAgent retrieved {k_res.get('count', 0)} notes chunk(s) on '{topic}'.",
                data=k_res.get("data"),
            ))
            step += 1

            # Step 2: AssessmentAgent generates the quiz
            q_res = self.assessment_agent.safe_run(
                query=f"Generate quiz for {topic}",
                context={"topic": topic, "difficulty": "medium", "number_of_questions": 5}
            )
            extracted_data["assessment"] = q_res
            participating_agents.append(self.assessment_agent.name)
            quiz_data = q_res.get("data", {})
            traces.append(ToolTrace(
                step_number=step,
                tool_name="generate_quiz",
                agent_name=self.assessment_agent.name,
                arguments={"topic": topic, "difficulty": "medium", "number_of_questions": 5},
                status=q_res["status"],
                summary=q_res.get("message", f"Generated 5 questions for {topic}."),
                data=quiz_data,
            ))
            step += 1

            final_text = (
                f"### 📝 Practice Quiz Ready: {topic}\n\n"
                f"**SupervisorAgent** delegated creation to **AssessmentAgent** (grounded via **KnowledgeAgent**):\n\n"
                f"- **Topic**: {topic}\n"
                f"- **Engine**: {quiz_data.get('generator', 'Deterministic')}\n"
                f"- **Document Grounding**: {'Yes (Verified notes)' if quiz_data.get('grounded_in_documents') else 'Standard curriculum'}\n\n"
                f"You can take this assessment now in the **Quiz Generator** tab to test your recall."
            )
            recommended_action = f"Complete the practice questions for '{topic}' to update your topic score."

        # =========================================================================
        # SCENARIO 3: DOCUMENT SEARCH
        # Supervisor → KnowledgeAgent
        # =========================================================================
        elif goal == "document_search":
            search_query = parsed_intent.get("search_query", query)
            k_res = self.knowledge_agent.safe_run(
                query=search_query,
                context={"search_query": search_query, "top_k": 5}
            )
            extracted_data["knowledge"] = k_res
            participating_agents.append(self.knowledge_agent.name)
            traces.append(ToolTrace(
                step_number=step,
                tool_name="document_search",
                agent_name=self.knowledge_agent.name,
                arguments={"query": search_query, "top_k": 5},
                status=k_res["status"],
                summary=k_res.get("message", f"Retrieved {k_res.get('count', 0)} chunk(s)."),
                data=k_res.get("data"),
            ))
            step += 1

            if k_res.get("found"):
                passages = k_res.get("chunks", [])[:3]
                passages_str = "\n\n".join([
                    f"> **[{c['source']} — Page {c.get('page_number', 1)} — Relevance: {int(c.get('similarity_score', 0)*100)}%]**\n"
                    f"> {c['text'][:400]}..."
                    for c in passages
                ])
                final_text = (
                    f"### 📚 Retrieved Passages for '{search_query}'\n\n"
                    f"**KnowledgeAgent** retrieved the top matches directly from your uploaded materials:\n\n"
                    f"{passages_str}\n\n"
                    f"*Note: Passages are extracted verbatim using TF-IDF cosine similarity.*"
                )
                recommended_action = f"Generate a practice quiz on '{search_query}' to verify your retention."
            else:
                final_text = (
                    f"### 🔍 No Relevant Information Found\n\n"
                    f"{k_res.get('message', 'No chunks matched your query.')}\n\n"
                    f"Try uploading relevant notes in the **Document Library** or clicking 'Load Sample DBMS Material'."
                )
                recommended_action = "Upload lecture slides or syllabus documents in the Document Library."

        # =========================================================================
        # SCENARIO 4: PERFORMANCE ANALYSIS
        # Supervisor → PerformanceAgent
        # =========================================================================
        elif goal == "performance_analysis":
            perf_res = self.performance_agent.safe_run(query="analyze")
            extracted_data["performance"] = perf_res
            participating_agents.append(self.performance_agent.name)
            perf_data = perf_res.get("data", {})
            traces.append(ToolTrace(
                step_number=step,
                tool_name="analyze_performance",
                agent_name=self.performance_agent.name,
                arguments={},
                status=perf_res["status"],
                summary=perf_res.get("message", "Analyzed performance history."),
                data=perf_data,
            ))
            step += 1

            if perf_res.get("has_data"):
                final_text = (
                    f"### 📊 Student Performance Analysis\n\n"
                    f"**PerformanceAgent** evaluated your recorded assessment history:\n\n"
                    f"- **Overall Quiz Average**: {perf_data.get('overall_score', 0)}%\n"
                    f"- **Total Attempts Recorded**: {perf_data.get('total_attempts', 0)}\n\n"
                    f"**Mastery Breakdown:**\n"
                    f"- 🟢 **Strong (>=80%)**: {', '.join([s['topic'] for s in perf_res.get('strong_topics', [])]) or 'None yet'}\n"
                    f"- 🟡 **Developing (60–79%)**: {', '.join([d['topic'] for d in perf_res.get('developing_topics', [])]) or 'None'}\n"
                    f"- 🔴 **Needs Attention (<60%)**: {', '.join([w['topic'] for w in perf_res.get('weak_topics', [])]) or 'None'}\n\n"
                    f"**Primary Recommendation:** {perf_data.get('recommendations', ['Focus on weak topics'])[0]}\n\n"
                    f"*{perf_data.get('disclaimer', '')}*"
                )
                weak_top = perf_res.get("weak_topics", [])
                recommended_action = f"Schedule a revision block for '{weak_top[0]['topic'] if weak_top else 'core concepts'}'."
            else:
                final_text = (
                    f"### 📊 Performance Calibration\n\n"
                    f"{perf_res.get('message', 'No past quiz history.')}\n\n"
                    f"Take a practice quiz in the Assessments tab to enable personalized gap analysis."
                )
                recommended_action = "Open Quiz Generator and take your first diagnostic test."

        # =========================================================================
        # SCENARIO 5: STUDY PLANNING
        # Supervisor → PerformanceAgent → PlanningAgent
        # =========================================================================
        elif goal == "study_planning":
            days = parsed_intent.get("days", 5)
            perf_res = self.performance_agent.safe_run(query="analyze")
            extracted_data["performance"] = perf_res
            participating_agents.append(self.performance_agent.name)
            traces.append(ToolTrace(
                step_number=step,
                tool_name="analyze_performance",
                agent_name=self.performance_agent.name,
                arguments={},
                status=perf_res["status"],
                summary=perf_res.get("message", "Analyzed mastery levels for scheduling."),
                data=perf_res.get("data"),
            ))
            step += 1

            calc_exam_date = (date.today() + timedelta(days=days)).isoformat()
            plan_res = self.planning_agent.safe_run(
                query=f"Create {days}-day plan",
                context={
                    "days": days,
                    "exam_date": calc_exam_date,
                    "daily_hours": 3.0,
                    "performance": perf_res.get("data", {}),
                }
            )
            extracted_data["planning"] = plan_res
            extracted_data["study_plan"] = plan_res.get("data", plan_res)
            participating_agents.append(self.planning_agent.name)
            traces.append(ToolTrace(
                step_number=step,
                tool_name="create_study_plan",
                agent_name=self.planning_agent.name,
                arguments={"days": days, "daily_hours": 3.0},
                status=plan_res["status"],
                summary=plan_res.get("message", f"Created {days}-day study timetable."),
                data=plan_res.get("data"),
            ))
            step += 1

            final_text = (
                f"### 📅 Study Schedule Created\n\n"
                f"**SupervisorAgent** coordinated with **PerformanceAgent** and **PlanningAgent** to build a {days}-day schedule.\n\n"
                f"Your schedule has been saved. View and check off daily study tasks in the **Study Planner** tab."
            )
            recommended_action = "Review today's assigned tasks in the Study Planner."

        # =========================================================================
        # SCENARIO 6: PROGRESS / SUMMARY
        # Supervisor → ProgressAgent → PerformanceAgent
        # =========================================================================
        else:
            prog_res = self.progress_agent.safe_run(query="summary")
            extracted_data["progress"] = prog_res
            participating_agents.append(self.progress_agent.name)
            summary_data = prog_res.get("data", {})
            traces.append(ToolTrace(
                step_number=step,
                tool_name="get_student_summary",
                agent_name=self.progress_agent.name,
                arguments={},
                status=prog_res["status"],
                summary=prog_res.get("message", "Retrieved student progress."),
                data=summary_data,
            ))
            step += 1

            perf_res = self.performance_agent.safe_run(query="analyze")
            extracted_data["performance"] = perf_res
            participating_agents.append(self.performance_agent.name)
            traces.append(ToolTrace(
                step_number=step,
                tool_name="analyze_performance",
                agent_name=self.performance_agent.name,
                arguments={},
                status=perf_res["status"],
                summary=perf_res.get("message", "Analyzed performance overview."),
                data=perf_res.get("data"),
            ))
            step += 1

            stats_dict = summary_data.get("dashboard_stats", {})
            final_text = (
                f"### 📈 Current Learning Summary\n\n"
                f"**SupervisorAgent** compiled your progress status via **ProgressAgent** and **PerformanceAgent**:\n\n"
                f"- **Uploaded Documents**: {summary_data.get('documents_count', 0)} files ({summary_data.get('chunks_count', 0)} chunks)\n"
                f"- **Quizzes Attempted**: {stats_dict.get('quiz_attempts_count', 0)} "
                f"(Avg: {stats_dict.get('average_quiz_score', 0)}%)\n"
                f"- **Study Tasks Completed**: {stats_dict.get('completed_study_tasks', 0)} / "
                f"{stats_dict.get('total_study_tasks', 0)}\n\n"
                f"Check the **Progress Tracker** for interactive charts and mastery trends."
            )
            recommended_action = "Work through pending tasks in your active study plan or test yourself on a new topic."

        # Unique participating agents list preserving order
        unique_agents = []
        for a in participating_agents:
            if a not in unique_agents:
                unique_agents.append(a)

        # Log trace to DB for audit history
        db = get_db(self.db_path)
        db.log_agent_trace(
            query=query,
            goal=parsed_intent.get("label", goal),
            tools_trace=[t.to_dict() for t in traces],
            final_response=final_text,
            mode=mode,
        )

        return AgentResult(
            user_query=query,
            goal=parsed_intent.get("label", goal),
            mode=mode,
            traces=traces,
            final_response=final_text,
            recommended_next_action=recommended_action,
            success=True,
            iterations=len(traces),
            extracted_data=extracted_data,
            participating_agents=unique_agents,
        )


# MultiToolOrchestrator is retained as an alias for backwards compatibility
class MultiToolOrchestrator(SupervisorAgent):
    """Backwards-compatible alias for SupervisorAgent."""
    pass
