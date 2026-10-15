"""
EduSync AI — Multi-Tool Agent for Personalized Student Success
SDG 4 (Quality Education) & SDG 9 (Industry, Innovation and Infrastructure)
Streamlit Application Main Entrypoint
"""

import os
import json
from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st

# Set page configuration first
st.set_page_config(
    page_title="EduSync AI — Student Success Agent",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Import internal services and tools
from services.persistence import get_db, DatabaseManager
from services.document_processor import extract_text_from_pdf, chunk_document_pages, TFIDFSearchEngine
from services.sample_data import (
    populate_sample_dbms_data,
    populate_sample_quiz_history,
    SAMPLE_TOPICS,
    DEMO_DISCLAIMER,
)
from services.llm_service import get_llm_service
from agent.orchestrator import MultiToolOrchestrator
from tools.document_search import document_search
from tools.quiz_generator import generate_quiz, record_quiz_submission
from tools.performance import analyze_performance
from tools.study_planner import create_study_plan, parse_and_validate_exam_date
from tools.progress import update_progress, get_student_summary

# ==============================================================================
# CUSTOM CSS FOR EDUCATION-TECHNOLOGY DARK MODERN AESTHETIC
# ==============================================================================
st.markdown("""
<style>
    /* Theme color variables */
    :root {
        --bg-main: #0e131f;
        --card-bg: #141c2e;
        --card-border: rgba(255, 255, 255, 0.08);
        --teal-accent: #00d2be;
        --blue-accent: #3b82f6;
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
    }

    /* Main container styling */
    .stApp {
        background-color: var(--bg-main);
        color: var(--text-primary);
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* Metric & Card styling */
    .edu-card {
        background: linear-gradient(145deg, #162035 0%, #111827 100%);
        border: 1px solid var(--card-border);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }

    .edu-card-highlight {
        background: linear-gradient(145deg, #132438 0%, #111a2e 100%);
        border: 1px solid rgba(0, 210, 190, 0.3);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }

    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: var(--teal-accent);
        margin: 4px 0;
    }

    .metric-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-secondary);
        font-weight: 600;
    }

    /* SDG Badges */
    .sdg-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        margin-right: 8px;
        color: white;
    }
    .sdg-4 { background-color: #c5192d; }
    .sdg-9 { background-color: #fd6925; }

    /* Trace Step Box */
    .trace-step {
        background: #0d1527;
        border-left: 4px solid var(--teal-accent);
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin-bottom: 10px;
        font-family: monospace;
        font-size: 0.9rem;
    }

    .trace-step-title {
        color: var(--teal-accent);
        font-weight: 700;
        margin-bottom: 4px;
    }

    .trace-step-body {
        color: #cbd5e1;
    }

    /* Topic Status Badges */
    .badge-strong {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid #10b981;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .badge-dev {
        background: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid #f59e0b;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .badge-weak {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid #ef4444;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    /* Disclaimer box */
    .disclaimer-banner {
        background-color: rgba(30, 41, 59, 0.7);
        border: 1px dashed rgba(148, 163, 184, 0.3);
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 0.82rem;
        color: #94a3b8;
        margin-top: 10px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# STATE & DATABASE INITIALIZATION
# ==============================================================================
DB_PATH = "edusync.db"
db = get_db(DB_PATH)

# Session state initialization
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Dashboard"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_quiz" not in st.session_state:
    st.session_state.current_quiz = None
if "quiz_submission_result" not in st.session_state:
    st.session_state.quiz_submission_result = None

# ==============================================================================
# SIDEBAR
# ==============================================================================
with st.sidebar:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
            <span style="font-size: 2rem;">🎓</span>
            <div>
                <h2 style="margin: 0; padding: 0; font-size: 1.4rem; color: #00d2be; font-weight: 800;">EduSync AI</h2>
                <div style="font-size: 0.75rem; color: #94a3b8;">Multi-Tool Academic Agent</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # SDG Alignment Badges
    st.markdown("""
        <div style="margin-bottom: 16px;">
            <span class="sdg-badge sdg-4">SDG 4: Quality Education</span>
            <span class="sdg-badge sdg-9">SDG 9: Innovation</span>
        </div>
    """, unsafe_allow_html=True)

    # API Key Configuration
    st.markdown("---")
    with st.expander("⚙️ AI Provider Settings", expanded=False):
        api_key_input = st.text_input(
            "Gemini API Key (Optional)",
            type="password",
            value=st.session_state.get("user_gemini_key", os.environ.get("GEMINI_API_KEY", "")),
            help="Leave empty to use deterministic Demo Mode.",
        )
        if api_key_input:
            st.session_state.user_gemini_key = api_key_input

    # Mode Indicator
    llm_service = get_llm_service(api_key=st.session_state.get("user_gemini_key", None))
    if llm_service.is_available():
        st.success(f"🟢 **AI Mode Active**\nModel: `{llm_service.model_name}`")
    else:
        st.info("🟡 **Demo Mode (Offline)**\nDeterministic Multi-Tool Routing")

    st.markdown("---")
    # Navigation
    menu_options = [
        "📊 Dashboard",
        "📚 Document Library",
        "🤖 AI Study Assistant",
        "📝 Quiz Generator",
        "📈 Performance Analyzer",
        "📅 Study Planner",
        "🎯 Progress Tracker",
    ]
    selected_page = st.radio("Navigation", menu_options, index=0)

    st.markdown("---")
    st.markdown("### ⚡ Quick Demo Data")
    if st.button("📥 Load Sample DBMS Material", use_container_width=True):
        added = populate_sample_dbms_data(db, force=False)
        added_quiz = populate_sample_quiz_history(db, force=False)
        if added or added_quiz:
            st.success("Sample DBMS syllabus, lecture notes & initial quiz history loaded!")
        else:
            st.info("Sample material is already loaded in the workspace.")
        st.rerun()

    if st.button("🗑️ Reset Database", use_container_width=True):
        db.reset_database()
        st.session_state.chat_history = []
        st.session_state.current_quiz = None
        st.session_state.quiz_submission_result = None
        if "plan_in_progress" in st.session_state:
            del st.session_state["plan_in_progress"]
        st.warning("Database reset to clean state.")
        st.rerun()

    st.markdown("""
        <div style="font-size: 0.72rem; color: #64748b; margin-top: 30px; text-align: center;">
            EduSync AI MVP v1.0<br/>
            Pairing SDG 4 & SDG 9 for Student Success
        </div>
    """, unsafe_allow_html=True)

# Strip icon prefix for page routing
current_page = selected_page.split(" ", 1)[1]


# ==============================================================================
# PAGE 1: DASHBOARD
# ==============================================================================
if current_page == "Dashboard":
    st.markdown("""
        <div style="margin-bottom: 24px;">
            <h1 style="color: #f8fafc; margin-bottom: 6px;">EduSync AI Dashboard</h1>
            <div style="color: #94a3b8; font-size: 1.05rem;">
                Autonomous multi-tool student success agent for undergraduate examination preparation.
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Top stats
    stats = db.get_dashboard_stats()
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
            <div class="edu-card">
                <div class="metric-label">Document Library</div>
                <div class="metric-value">{stats['document_count']}</div>
                <div style="font-size: 0.8rem; color: #94a3b8;">{stats['chunk_count']} searchable chunks</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class="edu-card">
                <div class="metric-label">Quiz Attempts</div>
                <div class="metric-value">{stats['quiz_attempts_count']}</div>
                <div style="font-size: 0.8rem; color: #94a3b8;">Diagnostic & topic drills</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class="edu-card">
                <div class="metric-label">Average Score</div>
                <div class="metric-value">{stats['average_quiz_score']}%</div>
                <div style="font-size: 0.8rem; color: #94a3b8;">Across evaluated topics</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
            <div class="edu-card">
                <div class="metric-label">Tasks Completed</div>
                <div class="metric-value">{stats['completed_study_tasks']}/{stats['total_study_tasks']}</div>
                <div style="font-size: 0.8rem; color: #94a3b8;">{stats['task_completion_rate']}% plan progress</div>
            </div>
        """, unsafe_allow_html=True)

    # Quick Start Action Banner
    st.markdown("""
        <div class="edu-card-highlight">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
                <div>
                    <h3 style="margin: 0; color: #00d2be;">🚀 5-Day Exam Preparation Workflow</h3>
                    <div style="color: #cbd5e1; font-size: 0.95rem; margin-top: 4px;">
                        Launch the complete multi-tool agent pipeline to synthesize notes, identify weak topics, and generate a daily schedule.
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("⚡ Launch 5-Day DBMS Exam Preparation Workflow", type="primary", use_container_width=True):
        # Auto load demo data if none exists
        if stats["document_count"] == 0:
            populate_sample_dbms_data(db, force=False)
            populate_sample_quiz_history(db)
        orchestrator = MultiToolOrchestrator(
            db_path=DB_PATH,
            api_key=st.session_state.get("user_gemini_key", None),
        )
        with st.spinner("Agent orchestrating tools: document_search -> get_summary -> analyze_performance -> create_study_plan..."):
            result = orchestrator.run("Prepare me for my DBMS exam in five days.")
            st.session_state.chat_history.append({"query": "Prepare me for my DBMS exam in five days.", "result": result})
            st.session_state.last_agent_result = result
            st.success("Workflow executed successfully! View the trace below and in the AI Study Assistant.")
            st.rerun()

    # Two column overview: Topic Health & Active Study Plan
    c_left, c_right = st.columns([1, 1])

    with c_left:
        st.markdown("### 🎯 Topic Mastery Status")
        perf = analyze_performance(db_path=DB_PATH)
        if perf["has_data"]:
            for topic, data in perf["topic_breakdown"].items():
                cls = data["classification"]
                badge_class = "badge-strong" if cls == "Strong" else ("badge-dev" if cls == "Developing" else "badge-weak")
                st.markdown(f"""
                    <div style="background: #141c2e; padding: 12px; border-radius: 8px; margin-bottom: 8px; border: 1px solid rgba(255,255,255,0.05); display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>{topic}</strong>
                            <div style="font-size: 0.78rem; color: #94a3b8;">{data['attempts']} attempt(s) • Score: {data['percentage']}%</div>
                        </div>
                        <span class="{badge_class}">{cls}</span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recorded quiz attempts. Take a quiz or load sample data to see topic mastery.")

    with c_right:
        st.markdown("### 📅 Active Study Plan")
        active_plan = db.get_active_study_plan()
        if active_plan:
            tasks = db.get_study_tasks(active_plan["id"])
            completed = sum(1 for t in tasks if t["completed"] == 1)
            total = len(tasks)
            st.markdown(f"""
                <div class="edu-card">
                    <h4 style="margin: 0; color: #00d2be;">{active_plan['subject']}</h4>
                    <div style="font-size: 0.85rem; color: #94a3b8; margin: 4px 0 10px 0;">
                        Target Exam: <strong>{active_plan['exam_date']}</strong> • Daily Hours: <strong>{active_plan['available_hours']} hrs/day</strong>
                    </div>
                    <div style="margin-bottom: 8px;">
                        Progress: <strong>{completed}/{total} tasks completed</strong>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            st.progress(completed / total if total > 0 else 0.0)
        else:
            st.info("No active study plan. Use the Study Planner or launch the Exam Prep workflow above.")

    # Recent Agent Activity Logs
    st.markdown("### 📜 Recent Agent Activity")
    recent_logs = db.get_recent_agent_logs(limit=5)
    if recent_logs:
        for log in recent_logs:
            with st.expander(f"🕒 {log['timestamp'][:16]} — Goal: {log['goal']} ({len(log['tools_trace'])} tools called)"):
                st.markdown(f"**Query**: *\"{log['user_query']}\"*")
                st.markdown(f"**Mode**: `{log['mode']}`")
                for trace in log["tools_trace"]:
                    st.markdown(f"- `Step {trace['step_number']}`: `{trace['tool_name']}` ({trace['status']}) — {trace['summary']}")
    else:
        st.write("No agent executions recorded yet.")


# ==============================================================================
# PAGE 2: DOCUMENT LIBRARY
# ==============================================================================
elif current_page == "Document Library":
    st.markdown("## 📚 Document Library & Retrieval (RAG)")
    st.markdown("Upload course syllabus PDFs and lecture notes to ground agent tools in your actual academic material.")

    col_upload, col_summary = st.columns([1.5, 1])

    with col_upload:
        uploaded_files = st.file_uploader(
            "Upload Course PDFs (Syllabus, Lecture Slides, Textbooks)",
            type=["pdf"],
            accept_multiple_files=True,
            help="Files are processed locally and securely indexed using TF-IDF for passage retrieval.",
        )

        if uploaded_files:
            if st.button("Process & Index Uploaded PDFs", type="primary"):
                processed_count = 0
                for uf in uploaded_files:
                    pages_data, warning = extract_text_from_pdf(uf, uf.name)
                    if warning:
                        st.warning(warning)
                    if pages_data:
                        chunks = chunk_document_pages(pages_data, uf.name, chunk_size=500, chunk_overlap=100)
                        db.save_document(
                            filename=uf.name,
                            file_type="PDF (Uploaded)",
                            num_chunks=len(chunks),
                            num_pages=len(pages_data),
                            chunks=chunks,
                            is_sample=False,
                        )
                        processed_count += 1
                st.success(f"Successfully processed and indexed {processed_count} document(s)!")
                st.rerun()

    with col_summary:
        st.markdown("""
            <div class="edu-card">
                <h4 style="margin: 0; color: #00d2be;">Grounding & RAG Security</h4>
                <div style="font-size: 0.85rem; color: #cbd5e1; margin-top: 8px; line-height: 1.5;">
                    • Uses <strong>pypdf</strong> for safe in-memory text parsing.<br/>
                    • Automatically detects empty and scanned PDFs.<br/>
                    • Extracts chunks with page-level provenance.<br/>
                    • TF-IDF vector retrieval with cosine scoring.<br/>
                    • In offline Demo Mode, documents never leave your system.
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🗂️ Indexed Documents")
    docs = db.get_documents()
    if docs:
        doc_df = pd.DataFrame([
            {
                "Filename": d["filename"],
                "Type": d["file_type"],
                "Pages": d["num_pages"],
                "Chunks": d["num_chunks"],
                "Indexed Time": d["upload_time"][:16],
                "Source": "Demo Dataset" if d["is_sample"] else "User Upload",
            }
            for d in docs
        ])
        st.dataframe(doc_df, use_container_width=True, hide_index=True)
    else:
        st.info("No documents currently indexed. Upload a PDF or click 'Load Sample DBMS Material' in the sidebar.")

    # Live Document Search Tester
    st.markdown("---")
    st.markdown("### 🔍 Live Document Passage Search")
    search_query = st.text_input("Enter search query or topic:", placeholder="e.g. 2NF partial functional dependency or B+ Tree leaf nodes")
    if search_query:
        with st.spinner("Searching document index..."):
            search_res = document_search(search_query, top_k=5, db_path=DB_PATH)
            if search_res["found"]:
                st.success(search_res["message"])
                for idx, c in enumerate(search_res["chunks"]):
                    score_pct = int(c["similarity_score"] * 100)
                    with st.expander(f"Passage #{idx+1} — {c['source']} (Page {c['page_number']}) — Relevance: {score_pct}%", expanded=(idx == 0)):
                        st.markdown(f"> {c['text']}")
            else:
                st.warning(search_res["message"])


# ==============================================================================
# PAGE 3: AI STUDY ASSISTANT (MULTI-TOOL AGENT ORCHESTRATION)
# ==============================================================================
elif current_page == "AI Study Assistant":
    st.markdown("## 🤖 AI Study Assistant — Multi-Tool Orchestrator")
    st.markdown("Ask natural language questions. The orchestrator decomposes your goal, selects tools, validates inputs, and synthesizes answers.")

    # Quick prompt chips
    st.markdown("**Suggested Student Requests:**")
    prompt_cols = st.columns(3)
    preset_query = None
    with prompt_cols[0]:
        if st.button("🎯 Prepare me for my DBMS exam in five days", use_container_width=True):
            preset_query = "Prepare me for my DBMS exam in five days."
    with prompt_cols[1]:
        if st.button("📝 Give me a quiz on indexing", use_container_width=True):
            preset_query = "Give me a quiz on indexing."
    with prompt_cols[2]:
        if st.button("🔍 Find normalization in my notes", use_container_width=True):
            preset_query = "Find information about normalization in my notes."

    user_query = st.text_input(
        "Enter your academic request:",
        value=preset_query if preset_query else "",
        placeholder="e.g. Prepare me for my DBMS exam in five days.",
    )

    if st.button("Send Request to Agent", type="primary") or preset_query:
        query_to_run = user_query if user_query else preset_query
        if query_to_run:
            orchestrator = MultiToolOrchestrator(
                db_path=DB_PATH,
                api_key=st.session_state.get("user_gemini_key", None),
            )
            with st.spinner("Orchestrating agent tools..."):
                result = orchestrator.run(query_to_run)
                st.session_state.chat_history.append({"query": query_to_run, "result": result})

    # Render Chat & Agent Execution Traces
    if st.session_state.chat_history:
        for item in reversed(st.session_state.chat_history):
            res = item["result"]
            st.markdown(f"""
                <div style="background: #111a2e; border-left: 4px solid #3b82f6; padding: 14px; border-radius: 4px; margin-top: 16px;">
                    <div style="font-size: 0.8rem; color: #94a3b8; font-weight: 700; text-transform: uppercase;">Student Request</div>
                    <div style="font-size: 1.1rem; color: #f8fafc; font-weight: 600; margin-top: 4px;">"{item['query']}"</div>
                </div>
            """, unsafe_allow_html=True)

            # AGENT EXECUTION TRACE BOX (CRITICAL FOR MULTI-TOOL DEMONSTRATION)
            st.markdown("#### ⚙️ Agent Multi-Tool Workflow Trace")
            st.markdown(f"""
                <div class="edu-card">
                    <div style="font-size: 0.85rem; color: #00d2be; font-weight: 700; margin-bottom: 8px;">
                        GOAL IDENTIFIED: {res.goal} • MODE: {res.mode} • ITERATIONS: {res.iterations}
                    </div>
                </div>
            """, unsafe_allow_html=True)

            for trace in res.traces:
                status_icon = "✓" if trace.status == "SUCCESS" else "⚠️"
                st.markdown(f"""
                    <div class="trace-step">
                        <div class="trace-step-title">{status_icon} Step {trace.step_number}: Tool Selected ➔ <code>{trace.tool_name}</code></div>
                        <div class="trace-step-body">
                            <strong>Arguments:</strong> <code>{json.dumps(trace.arguments)}</code><br/>
                            <strong>Status:</strong> {trace.status} • <strong>Result:</strong> {trace.summary}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            # Final response
            st.markdown("#### 💬 Synthesized Agent Response")
            st.markdown(res.final_response)

            # Recommended Action
            if res.recommended_next_action:
                st.markdown(f"""
                    <div class="edu-card-highlight">
                        <strong style="color: #00d2be;">💡 Recommended Next Action:</strong>
                        <div style="margin-top: 4px; color: #f1f5f9;">{res.recommended_next_action}</div>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown("---")


# ==============================================================================
# PAGE 4: QUIZ GENERATOR
# ==============================================================================
elif current_page == "Quiz Generator":
    st.markdown("## 📝 Quiz Generator & Diagnostic Assessment")
    st.markdown("Practice multiple choice questions grounded in your course materials. Submit answers to record performance.")

    c1, c2, c3 = st.columns([1.5, 1, 1])
    with c1:
        topic_choice = st.selectbox(
            "Select Course Topic",
            SAMPLE_TOPICS + ["Custom Topic..."],
            index=2,  # Normalization
        )
        if topic_choice == "Custom Topic...":
            topic_choice = st.text_input("Enter custom topic name:", value="Functional Dependencies")
    with c2:
        diff_choice = st.selectbox("Difficulty Level", ["easy", "medium", "hard"], index=1)
    with c3:
        num_q_choice = st.slider("Number of Questions", min_value=1, max_value=8, value=4)

    if st.button("Generate Topic Quiz", type="primary"):
        with st.spinner("Generating quiz grounded in course documents..."):
            quiz_res = generate_quiz(
                topic=topic_choice,
                difficulty=diff_choice,
                number_of_questions=num_q_choice,
                db_path=DB_PATH,
                api_key=st.session_state.get("user_gemini_key", None),
            )
            st.session_state.current_quiz = quiz_res
            st.session_state.quiz_submission_result = None

    # Render current quiz
    if st.session_state.current_quiz:
        q_data = st.session_state.current_quiz
        st.markdown(f"""
            <div class="edu-card" style="margin-top: 15px;">
                <h3 style="margin: 0; color: #00d2be;">{q_data['topic']} — Diagnostic Quiz</h3>
                <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 4px;">
                    Difficulty: <strong>{q_data['difficulty'].capitalize()}</strong> •
                    Engine: <strong>{q_data.get('generator', 'Deterministic')}</strong> •
                    Document Grounding: <strong>{'Yes (Uploaded notes)' if q_data.get('grounded_in_documents') else 'Course Syllabus'}</strong>
                </div>
            </div>
        """, unsafe_allow_html=True)

        user_answers = {}
        with st.form("quiz_form"):
            for q in q_data["questions"]:
                st.markdown(f"**Question {q['id']}:** {q['question']}")
                opts = q["options"]
                user_answers[str(q["id"])] = st.radio(
                    f"Choose answer for Q{q['id']}:",
                    opts,
                    key=f"q_{q['id']}",
                    index=None,
                )
                st.markdown("<br/>", unsafe_allow_html=True)

            submitted = st.form_submit_button("Submit Quiz Answers", type="primary")
            if submitted:
                sub_res = record_quiz_submission(
                    topic=q_data["topic"],
                    difficulty=q_data["difficulty"],
                    questions=q_data["questions"],
                    user_answers=user_answers,
                    db_path=DB_PATH,
                )
                st.session_state.quiz_submission_result = sub_res

    # Display quiz results
    if st.session_state.quiz_submission_result:
        res = st.session_state.quiz_submission_result
        pct = res["percentage"]
        score_color = "#10b981" if pct >= 80 else ("#f59e0b" if pct >= 60 else "#ef4444")
        st.markdown(f"""
            <div class="edu-card" style="border: 2px solid {score_color}; margin-top: 20px;">
                <h3 style="margin: 0; color: {score_color};">Quiz Result: {res['score']} / {res['total']} ({pct}%)</h3>
                <div style="font-size: 0.9rem; color: #cbd5e1; margin-top: 4px;">
                    Recorded in SQLite. Topic performance and learning gap analytics have been updated.
                </div>
            </div>
        """, unsafe_allow_html=True)

        for d in res["details"]:
            is_cor = d["is_correct"]
            icon = "✅" if is_cor else "❌"
            border_color = "rgba(16, 185, 129, 0.4)" if is_cor else "rgba(239, 68, 68, 0.4)"
            st.markdown(f"""
                <div style="background: #111a2e; border: 1px solid {border_color}; border-radius: 8px; padding: 12px; margin-bottom: 10px;">
                    <div><strong>{icon} Q{d['id']}: {d['question']}</strong></div>
                    <div style="font-size: 0.88rem; margin-top: 6px;">
                        Your answer: <code>{d['user_answer']}</code> | Correct: <strong style="color: #00d2be;">{d['correct_answer']}</strong>
                    </div>
                    <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 6px;">
                        💡 <strong>Explanation:</strong> {d['explanation']}
                    </div>
                    {f"<div style='font-size: 0.78rem; color: #64748b; margin-top: 4px;'>Source: {d['source']}</div>" if d.get('source') else ""}
                </div>
            """, unsafe_allow_html=True)


# ==============================================================================
# PAGE 5: PERFORMANCE ANALYZER
# ==============================================================================
elif current_page == "Performance Analyzer":
    st.markdown("## 📈 Performance Analyzer & Learning Gap Diagnosis")
    st.markdown("Analyzes quiz performance by topic using transparent score thresholds to classify areas needing attention.")

    perf = analyze_performance(db_path=DB_PATH)

    st.markdown(f"""
        <div class="disclaimer-banner">
            ℹ️ {perf['disclaimer']}
        </div>
    """, unsafe_allow_html=True)

    # Threshold configuration view
    with st.expander("⚙️ Score Threshold Configuration", expanded=False):
        st.markdown("""
            - **Strong (>= 80%)**: Student exhibits solid conceptual recall and problem-solving mastery.
            - **Developing (60% – 79.9%)**: Student understands fundamentals but needs reinforcement.
            - **Needs Attention (< 60%)**: Critical learning gap; prioritized in study plan.
        """)

    if perf["has_data"]:
        # Overall Summary Cards
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Overall Accuracy", f"{perf['overall_score']}%")
        c2.metric("Total Attempts", perf["total_attempts"])
        c3.metric("Strong Topics", len(perf["strong_topics"]))
        c4.metric("Needs Attention", len(perf["weak_topics"]))

        # Topic Breakdown Cards
        st.markdown("### 📋 Topic-Level Mastery Classifications")
        for topic, d in perf["topic_breakdown"].items():
            cls = d["classification"]
            badge_class = "badge-strong" if cls == "Strong" else ("badge-dev" if cls == "Developing" else "badge-weak")
            with st.container():
                st.markdown(f"""
                    <div class="edu-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h4 style="margin: 0; color: #f8fafc;">{topic}</h4>
                            <span class="{badge_class}">{cls}</span>
                        </div>
                        <div style="font-size: 1.1rem; color: #00d2be; font-weight: 700; margin: 6px 0;">
                            {d['percentage']}% ({d['score']} / {d['total_questions']} correct)
                        </div>
                        <div style="font-size: 0.85rem; color: #cbd5e1; margin-top: 4px;">
                            <strong>Determination:</strong> {d['rationale']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        # Actionable Recommendations
        st.markdown("### 🎯 Pedagogical Recommendations")
        for rec in perf["recommendations"]:
            st.info(f"👉 {rec}")

    else:
        st.info("No recorded quiz attempts found in the database. Complete a quiz in the Quiz Generator to calibrate your performance.")


# ==============================================================================
# PAGE 6: STUDY PLANNER
# ==============================================================================
elif current_page == "Study Planner":
    st.markdown("## 📅 Study Planner & Schedule Generator")
    st.markdown("Generates an adaptive, date-validated study schedule that allocates study time based on topic weaknesses.")

    with st.form("planner_form"):
        st.markdown("### Plan Generation Parameters")
        cp1, cp2 = st.columns(2)
        with cp1:
            subject_name = st.text_input("Course / Subject Name", value="Database Management Systems (DBMS)")
            exam_date_val = st.date_input(
                "Target Exam Date",
                value=date.today() + timedelta(days=5),
                min_value=date.today() + timedelta(days=1),
                help="Must be a future date (cannot be today or in the past).",
            )
        with cp2:
            daily_hours_val = st.slider("Available Daily Study Hours", min_value=1.0, max_value=10.0, value=3.0, step=0.5)
            selected_topics = st.multiselect(
                "Curriculum Topics",
                SAMPLE_TOPICS,
                default=SAMPLE_TOPICS,
            )

        submit_plan = st.form_submit_button("Generate Personalized Study Plan", type="primary")

        if submit_plan:
            perf = analyze_performance(db_path=DB_PATH)
            plan_res = create_study_plan(
                exam_date=exam_date_val.isoformat(),
                available_hours=daily_hours_val,
                topics=selected_topics,
                performance=perf,
                subject=subject_name,
                db_path=DB_PATH,
            )
            if plan_res["status"] == "SUCCESS":
                st.success(plan_res["message"])
                st.rerun()
            else:
                st.error(plan_res["message"])

    # Display active study plan
    active_plan = db.get_active_study_plan()
    if active_plan:
        st.markdown("---")
        st.markdown(f"### 🗓️ Active Schedule: {active_plan['subject']}")
        st.markdown(f"""
            <div class="edu-card">
                <div style="font-size: 0.9rem; color: #cbd5e1;">
                    Target Date: <strong>{active_plan['exam_date']}</strong> •
                    Daily Study Time: <strong>{active_plan['available_hours']} hrs/day</strong> •
                    Created: <strong>{active_plan['created_at'][:16]}</strong>
                </div>
            </div>
        """, unsafe_allow_html=True)

        tasks = db.get_study_tasks(active_plan["id"])

        # Group tasks by day
        days_grouped = {}
        for t in tasks:
            day_num = t["day_number"]
            if day_num not in days_grouped:
                days_grouped[day_num] = []
            days_grouped[day_num].append(t)

        for day_num, day_tasks in days_grouped.items():
            st.markdown(f"#### 📆 Day {day_num}")
            for task in day_tasks:
                task_id = task["id"]
                is_done = task["completed"] == 1
                type_badge = task["task_type"].upper()
                c_check, c_desc = st.columns([0.1, 0.9])
                with c_check:
                    new_val = st.checkbox(
                        f"Complete Task #{task_id}",
                        value=is_done,
                        key=f"task_{task_id}",
                        label_visibility="collapsed",
                    )
                    if new_val != is_done:
                        db.toggle_task_completion(task_id, new_val)
                        st.rerun()
                with c_desc:
                    line_style = "text-decoration: line-through; opacity: 0.6;" if is_done else ""
                    st.markdown(f"""
                        <div style="{line_style}">
                            <strong>[{type_badge}] {task['topic']}</strong> ({task['duration_hours']} hrs)<br/>
                            <span style="font-size: 0.88rem; color: #cbd5e1;">{task['task_description']}</span>
                        </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("No active study plan generated yet. Fill out the form above to build one.")


# ==============================================================================
# PAGE 7: PROGRESS TRACKER
# ==============================================================================
elif current_page == "Progress Tracker":
    st.markdown("## 🎯 Progress Tracker & Learning Analytics")
    st.markdown("Persistent learning analytics across quiz scores, completed study tasks, and multi-tool agent sessions.")

    summary = get_student_summary(db_path=DB_PATH)
    stats = summary["dashboard_stats"]

    # Top metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Uploaded Documents", f"{summary['documents_count']}")
    c2.metric("Quiz Attempts", f"{stats['quiz_attempts_count']}")
    c3.metric("Average Score", f"{stats['average_quiz_score']}%")
    c4.metric("Study Tasks Completed", f"{stats['completed_study_tasks']}/{stats['total_study_tasks']}")

    st.markdown("---")
    c_left, c_right = st.columns([1, 1])

    with c_left:
        st.markdown("### 📊 Quiz Score History")
        attempts = db.get_quiz_attempts()
        if attempts:
            chart_df = pd.DataFrame([
                {
                    "Topic": a["topic"],
                    "Score (%)": a["percentage"],
                    "Date": a["timestamp"][:16],
                }
                for a in attempts
            ])
            st.bar_chart(chart_df.set_index("Topic")["Score (%)"])
            st.dataframe(chart_df, use_container_width=True, hide_index=True)
        else:
            st.info("No quiz attempts recorded yet.")

    with c_right:
        st.markdown("### 🏆 Topic Mastery Classification")
        perf = analyze_performance(db_path=DB_PATH)
        if perf["has_data"]:
            counts_df = pd.DataFrame([
                {"Classification": "Strong (>=80%)", "Count": len(perf["strong_topics"])},
                {"Classification": "Developing (60-79%)", "Count": len(perf["developing_topics"])},
                {"Classification": "Needs Attention (<60%)", "Count": len(perf["weak_topics"])},
            ])
            st.bar_chart(counts_df.set_index("Classification")["Count"])
        else:
            st.info("No topic mastery data available yet.")

    st.markdown("---")
    st.markdown("### 📜 Agent Multi-Tool Execution History")
    agent_logs = db.get_recent_agent_logs(limit=10)
    if agent_logs:
        log_rows = []
        for l in agent_logs:
            log_rows.append({
                "Timestamp": l["timestamp"][:19],
                "Goal": l["goal"],
                "Tools Called": len(l["tools_trace"]),
                "Mode": l["mode"],
                "Query": l["user_query"],
            })
        st.dataframe(pd.DataFrame(log_rows), use_container_width=True, hide_index=True)
    else:
        st.write("No agent executions logged.")
