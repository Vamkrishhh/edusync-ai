"""
EduSync AI — Tier-1 Autonomous Multi-Tool Educational Platform
SDG 4 (Quality Education) & SDG 9 (Industry, Innovation & Infrastructure)
Engineered for speed, visual excellence, and complete functional integrity.
"""

import os
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="EduSync AI — Student Success Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Internal tools & persistence
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
from tools.performance import analyze_performance, classify_score
from tools.study_planner import create_study_plan, parse_and_validate_exam_date
from tools.progress import update_progress, get_student_summary

DB_PATH = "edusync.db"
db = get_db(DB_PATH)

# ─────────────────────────────────────────────────────────────────────────────
# MODERN SAAS PRODUCT DESIGN SYSTEM (CSS)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg-base: #0c0e14;
    --bg-surface: #141721;
    --bg-surface-elevated: #1a1e2b;
    --border-subtle: #222634;
    --border-strong: #2e3447;
    --primary: #4f6bf5;
    --primary-hover: #3b57e0;
    --primary-subtle: rgba(79, 107, 245, 0.12);
    --emerald: #10b981;
    --amber: #f59e0b;
    --rose: #ef4444;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
}

* {
    box-sizing: border-box;
}

html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], p, h1, h2, h3, h4, h5, h6, input, select, textarea, button {
    font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
}

/* Explicitly preserve Streamlit Material Symbols icon ligatures */
[data-testid*="stIcon"],
[data-testid*="Icon"],
[data-testid="stIconMaterial"],
[class*="material-symbols"],
[class*="material-icons"],
[data-testid="stSidebarCollapseButton"] button span,
[data-testid="stExpanderToggleIcon"],
[data-testid="stExpander"] summary span,
[data-testid="stTextInput"] button span,
[data-testid="stBaseButton-headerNoPadding"] span,
span[translate="no"],
.material-icons,
.material-symbols-rounded {
    font-family: "Material Symbols Rounded" !important;
    font-weight: normal !important;
    font-style: normal !important;
    line-height: 1 !important;
    letter-spacing: normal !important;
    text-transform: none !important;
    white-space: nowrap !important;
    word-wrap: normal !important;
    direction: ltr !important;
}

/* Background Atmosphere */
.stApp {
    background-color: var(--bg-base);
    color: var(--text-primary);
}

#MainMenu, footer { visibility: hidden; }
header { background: transparent !important; }

/* Main Container */
.block-container {
    max-width: 1200px !important;
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}

/* Sidebar Customization */
[data-testid="stSidebar"] {
    background-color: #10131c !important;
    border-right: 1px solid var(--border-subtle) !important;
    padding-top: 0.8rem;
}

/* Sidebar Navigation Items */
[data-testid="stSidebar"] div[role="radiogroup"] {
    gap: 4px;
}
[data-testid="stSidebar"] div[role="radiogroup"] label {
    background: transparent;
    border-radius: 6px;
    padding: 8px 12px;
    margin: 2px 0;
    transition: background 0.15s ease;
    border: 1px solid transparent;
}
[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(255, 255, 255, 0.04);
}
[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {
    background: var(--primary-subtle);
    border: 1px solid rgba(79, 107, 245, 0.3);
}
[data-testid="stSidebar"] div[role="radiogroup"] label p {
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    color: var(--text-primary) !important;
}

/* Typography */
h1 {
    font-size: 1.65rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.025em !important;
    color: #f8fafc !important;
    margin-bottom: 0.25rem !important;
    line-height: 1.25 !important;
}
h2 {
    font-size: 1.2rem !important;
    font-weight: 600 !important;
    letter-spacing: -0.015em !important;
    color: #e2e8f0 !important;
    margin-top: 1rem !important;
    margin-bottom: 0.5rem !important;
}
h3 {
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: var(--text-muted) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    margin-top: 1.2rem !important;
    margin-bottom: 0.5rem !important;
}

/* Clean Structured Cards */
.acad-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    padding: 1.2rem 1.35rem;
    margin-bottom: 1rem;
}

.glass-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    padding: 1.15rem 1.25rem;
    margin-bottom: 0.85rem;
}

/* Metric Display Blocks */
.metric-box {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    padding: 1rem 1.15rem;
    height: 100%;
}
.metric-num {
    font-size: 1.75rem;
    font-weight: 700;
    color: #f8fafc;
    line-height: 1.15;
    margin-top: 6px;
    margin-bottom: 3px;
    letter-spacing: -0.02em;
}
.metric-title {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
}
.metric-sub {
    font-size: 0.78rem;
    color: var(--text-secondary);
}

/* Badges & Pills */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: 4px;
    letter-spacing: 0.01em;
}
.badge-emerald { background: rgba(16, 185, 129, 0.1); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.2); }
.badge-amber   { background: rgba(245, 158, 11, 0.1); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.2); }
.badge-rose    { background: rgba(239, 68, 68, 0.1);  color: #f87171; border: 1px solid rgba(239, 68, 68, 0.2); }
.badge-indigo  { background: rgba(79, 107, 245, 0.12); color: #818cf8; border: 1px solid rgba(79, 107, 245, 0.25); }
.badge-slate   { background: rgba(148, 163, 184, 0.08); color: #94a3b8; border: 1px solid var(--border-subtle); }

/* Progress Bars */
.prog-container {
    width: 100%;
    height: 6px;
    background: #1e2230;
    border-radius: 3px;
    overflow: hidden;
    margin-top: 6px;
}
.prog-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.4s ease;
}

/* Multi-Tool Execution Trace Card */
.trace-step {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-left: 3px solid var(--primary);
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
}
.trace-step-title {
    font-weight: 700;
    color: #f8fafc;
    font-size: 0.92rem;
    font-family: 'JetBrains Mono', monospace;
}
.trace-step-body {
    color: #cbd5e1;
    font-size: 0.85rem;
    margin-top: 4px;
    line-height: 1.5;
}

/* Button & Form Elements */
div.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 0.5rem 1.1rem !important;
    transition: all 0.15s ease !important;
}
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35) !important;
    color: #ffffff !important;
}
div.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(79, 70, 229, 0.5) !important;
}

/* Input Fields */
.stTextInput > div > div > input, .stTextArea > div > div > textarea {
    background-color: rgba(17, 24, 39, 0.85) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
    color: #ffffff !important;
}
.stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.25) !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# STATE INITIALIZATION
# ─────────────────────────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_quiz" not in st.session_state:
    st.session_state.current_quiz = None
if "quiz_result" not in st.session_state:
    st.session_state.quiz_result = None
if "active_tab_redirect" not in st.session_state:
    st.session_state.active_tab_redirect = None
if "search_query_trigger" not in st.session_state:
    st.session_state.search_query_trigger = ""
if "preset_agent_query" not in st.session_state:
    st.session_state.preset_agent_query = ""
# selected_nav_page is the SINGLE SOURCE OF TRUTH for navigation.
# Never write to the radio widget key directly — let the radio reflect
# selected_nav_page via its index= parameter only.
if "selected_nav_page" not in st.session_state:
    st.session_state.selected_nav_page = "📊 Dashboard"

def get_score_color(pct: float) -> str:
    if pct >= 75: return "var(--emerald)"
    if pct >= 50: return "var(--amber)"
    return "var(--rose)"

def get_badge_markup(pct: float) -> str:
    if pct >= 75: return f'<span class="badge badge-emerald">Strong ({pct}%)</span>'
    if pct >= 50: return f'<span class="badge badge-amber">Developing ({pct}%)</span>'
    return f'<span class="badge badge-rose">Needs Attention ({pct}%)</span>'

def _invalidate_data_cache():
    """Call this after any action that writes to the DB so the next render re-fetches fresh data."""
    for k in ("_cached_stats", "_cached_plan", "_cached_perf"):
        st.session_state.pop(k, None)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="padding: 6px 0 16px 0; display:flex; align-items:center; gap:10px;">
            <div style="background:linear-gradient(135deg, #6366f1, #06b6d4); width:36px; height:36px; border-radius:10px; display:flex; align-items:center; justify-content:center; box-shadow:0 4px 12px rgba(99,102,241,0.4); font-size:1.15rem;">
                🎓
            </div>
            <div>
                <div style="font-weight:800; font-size:1.15rem; color:#ffffff; letter-spacing:-0.03em;">EduSync <span style="color:#6366f1;">AI</span></div>
                <div style="font-size:0.72rem; color:#94a3b8; font-weight:500;">Multi-Tool Academic Agent</div>
            </div>
        </div>
        <div style="display:flex; gap:6px; margin-bottom:12px;">
            <span class="badge badge-slate" style="font-size:0.68rem;">SDG 4: Quality Education</span>
            <span class="badge badge-slate" style="font-size:0.68rem;">SDG 9: Innovation</span>
        </div>
    """, unsafe_allow_html=True)

    # Mode Indicator
    llm = get_llm_service(st.session_state.get("user_gemini_key"))
    if llm.is_available():
        st.success("🟢 **AI Mode Active**\nModel: `gemini-2.5-flash`")
    else:
        st.info("🟡 **Demo Mode (Offline)**\nDeterministic Multi-Tool Routing")

    # API Configuration
    with st.expander("⚙️ AI Provider Settings", expanded=False):
        key_input = st.text_input("Gemini API Key", value=st.session_state.get("user_gemini_key", ""), type="password")
        if st.button("Save Key", use_container_width=True):
            st.session_state.user_gemini_key = key_input.strip() if key_input.strip() else None
            st.success("Key updated.")
            st.rerun()

    st.markdown("---")

    # Navigation menu
    menu_options = [
        "📊 Dashboard",
        "📚 Document Library",
        "🤖 AI Study Assistant",
        "📝 Quiz Generator",
        "📈 Performance Analyzer",
        "📅 Study Planner",
        "🎯 Progress Tracker",
    ]

    # Resolve any pending redirect BEFORE rendering the radio widget.
    # This ensures the correct index is passed to st.radio on this very render.
    if st.session_state.active_tab_redirect:
        redirect_target = st.session_state.active_tab_redirect.lower()
        for opt in menu_options:
            # Match by keyword fragment so "Dashboard", "Quiz Generator", etc. all resolve
            if redirect_target in opt.lower():
                st.session_state.selected_nav_page = opt
                if "_nav_radio_widget" in st.session_state:
                    del st.session_state["_nav_radio_widget"]
                break
        st.session_state.active_tab_redirect = None

    # Guard: ensure selected_nav_page is always a valid menu option
    if st.session_state.selected_nav_page not in menu_options:
        st.session_state.selected_nav_page = menu_options[0]

    # CRITICAL: Do NOT give this radio a key= that matches a session_state variable
    # we write to programmatically. Using key= means Streamlit owns that slot and will
    # override any external writes on widget reconciliation.
    # Instead, drive navigation entirely via index= from selected_nav_page.
    selected_page = st.radio(
        "Navigation",
        menu_options,
        index=menu_options.index(st.session_state.selected_nav_page),
        key="_nav_radio_widget"  # internal key — never written to externally
    )
    # User manually clicked a nav item — update the source of truth
    if selected_page != st.session_state.selected_nav_page:
        st.session_state.selected_nav_page = selected_page
        # Clear preset query when navigating away from AI Tutor to prevent stale re-fire
        if selected_page != "🤖 AI Study Assistant":
            st.session_state.preset_agent_query = ""
        st.rerun()
    selected_page = st.session_state.selected_nav_page
    st.markdown("---")
    st.markdown("<div style='font-size:0.75rem; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:6px;'>⚡ Quick Demo Data</div>", unsafe_allow_html=True)

    if st.button("📥 Load Sample DBMS Material", use_container_width=True):
        added = populate_sample_dbms_data(db, force=False)
        added_quiz = populate_sample_quiz_history(db, force=False)
        if added or added_quiz:
            st.success("Sample DBMS material loaded successfully!")
        else:
            st.info("Sample material is already loaded.")
        _invalidate_data_cache()  # force fresh DB read on next render
        st.rerun()

    if st.button("🗑️ Reset Workspace", use_container_width=True):
        db.reset_database()
        st.session_state.chat_history = []
        st.session_state.current_quiz = None
        st.session_state.quiz_result = None
        st.session_state.preset_agent_query = ""
        st.session_state.search_query_trigger = ""
        _invalidate_data_cache()  # force fresh DB read on next render
        st.success("Workspace reset.")
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# CORE DATA FETCH (lazy, cached in session_state per render cycle)
# These are READ-ONLY queries. They run at most once per rerun, never write data.
# The cache is invalidated explicitly (via _invalidate_data_cache()) after any
# action that mutates the DB. The function is defined above near helper fns.
# ─────────────────────────────────────────────────────────────────────────────
if "_cached_stats" not in st.session_state:
    st.session_state["_cached_stats"] = db.get_dashboard_stats()
if "_cached_plan" not in st.session_state:
    st.session_state["_cached_plan"] = db.get_active_study_plan()
if "_cached_perf" not in st.session_state:
    st.session_state["_cached_perf"] = analyze_performance(db_path=DB_PATH)

stats = st.session_state["_cached_stats"]
active_plan = st.session_state["_cached_plan"]
perf = st.session_state["_cached_perf"]

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1: 📊 DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
if selected_page == "📊 Dashboard":
    doc_count = stats["document_count"]
    real_doc_count = stats.get("real_document_count", 0)
    quiz_count = stats["quiz_attempts_count"]      # real attempts only
    avg_score = stats["average_quiz_score"]         # real attempts only
    has_sample_data = (doc_count > real_doc_count) or (stats.get("all_quiz_attempts_count", 0) > quiz_count)

    # 1. TOP HEADER (compact, professional academic identity)
    st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:1.25rem; border-bottom:1px solid var(--border-subtle); padding-bottom:0.75rem;">
            <div>
                <span style="font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--primary);">EduSync AI</span>
                <h1 style="margin:0; font-size:1.65rem; font-weight:700; color:#f8fafc; letter-spacing:-0.025em;">Your Learning Overview</h1>
                <p style="margin:0; font-size:0.86rem; color:var(--text-secondary); margin-top:2px;">Track exam readiness, active syllabus milestones, and targeted study priorities.</p>
            </div>
            <div style="text-align:right;">
                <span class="badge badge-slate">Academic Workspace</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Demo data notice — shown only when sample data is present
    if has_sample_data:
        st.info(
            "**Demo data active.** Some metrics below include sample DBMS content loaded via 'Load Sample DBMS Material'. "
            "Scores labeled **Demo** are not your own quiz results. Upload your own notes and take real quizzes to replace them.",
            icon="ℹ️",
        )

    # Calculate exam context & days
    exam_subject = "Database Management Systems (DBMS)"
    days_left = 5
    plan_progress_pct = 0
    total_tasks = 0
    completed_tasks = 0
    tasks = []

    if active_plan:
        exam_subject = active_plan.get("subject", exam_subject)
        val = parse_and_validate_exam_date(active_plan["exam_date"])
        days_left = val.get("days_remaining", 5)
        tasks = db.get_study_tasks(active_plan["id"])
        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t["completed"] == 1)
        plan_progress_pct = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    # Weak topic extraction
    weak_topics = perf.get("weak_topics", [])
    primary_weak_topic = weak_topics[0]["topic"] if weak_topics else ("Indexing & Storage" if perf.get("has_data") else "None detected")
    weak_score_val = weak_topics[0].get("percentage", 40) if weak_topics else None

    # 2. EXAM STATUS (Visual focal point: DBMS, Exam in 5 days, progress & next action)
    st.markdown(f"""
        <div class="acad-card" style="border-left: 3px solid var(--primary); background: #131722; padding: 1.25rem 1.4rem; margin-bottom: 1.25rem;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;">
                <div style="flex: 1; min-width: 260px;">
                    <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
                        <span style="font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:var(--text-muted);">Primary Target</span>
                        <span class="badge badge-indigo">Exam in {days_left} Days</span>
                    </div>
                    <div style="font-size:1.35rem; font-weight:700; color:#f8fafc; letter-spacing:-0.015em;">{exam_subject}</div>
                    <div style="font-size:0.86rem; color:var(--text-secondary); margin-top:4px;">
                        Schedule: <b>{days_left} days remaining</b> · Milestone completion: <b>{completed_tasks}/{total_tasks} study tasks</b> ({plan_progress_pct}%)
                    </div>
                    <div class="prog-container" style="max-width:440px; margin-top:8px;">
                        <div class="prog-fill" style="width:{plan_progress_pct}%; background:var(--primary);"></div>
                    </div>
                </div>
                <div style="text-align:right; min-width:200px;">
                    <div style="font-size:0.72rem; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; color:var(--text-muted);">Recommended Next Action</div>
                    <div style="font-size:0.95rem; font-weight:600; color:#cbd5e1; margin-top:2px;">Practice {primary_weak_topic}</div>
                    <div style="font-size:0.78rem; color:var(--text-muted); margin-top:2px;">Calibrated to address lowest mastery topic</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 3. LEARNING SNAPSHOT (Compact, information-dense metrics)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        acc_color = "var(--emerald)" if avg_score >= 70 else ("var(--amber)" if avg_score >= 50 else "var(--rose)")
        acc_label = f"{avg_score}%" if quiz_count > 0 else "—"
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Average Accuracy</div>
                <div class="metric-num" style="color:{acc_color if quiz_count > 0 else 'var(--text-muted)'};">{acc_label}</div>
                <div class="metric-sub">{'Across ' + str(quiz_count) + ' your quizzes' if quiz_count > 0 else 'No real quiz data yet'}</div>
            </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Assessments Taken</div>
                <div class="metric-num">{quiz_count}</div>
                <div class="metric-sub">{'Your recorded quizzes' if quiz_count > 0 else 'Take a quiz to start tracking'}</div>
            </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Documents Indexed</div>
                <div class="metric-num">{doc_count}</div>
                <div class="metric-sub">{'Real: ' + str(real_doc_count) + ', Demo: ' + str(doc_count - real_doc_count) if has_sample_data else 'Uploaded files'}</div>
            </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Current Weak Area</div>
                <div class="metric-num" style="font-size:1.15rem; margin-top:8px; line-height:1.3; color:#f87171;">{primary_weak_topic}</div>
                <div class="metric-sub">{f'Score: {weak_score_val}%' if weak_score_val is not None else 'Needs baseline testing'}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    # 4 & 5: TWO-COLUMN MAIN WORKSPACE (Today's Plan on left, Topic Mastery & Next Action on right)
    col_plan, col_right = st.columns([1.1, 0.9], gap="large")

    with col_plan:
        # 4. TODAY'S PLAN
        st.markdown("<h3>Today's Study Plan</h3>", unsafe_allow_html=True)
        if tasks:
            # Partition tasks into Completed, Current (first incomplete), and Upcoming
            current_found = False
            for t in tasks[:5]:
                is_done = (t["completed"] == 1)
                task_id = t["id"]
                day_num = t["day_number"]
                topic_name = t["topic"]
                duration = t["duration_hours"]
                t_type = t["task_type"].capitalize()

                if is_done:
                    status_badge = '<span class="badge badge-slate">Completed</span>'
                elif not current_found:
                    status_badge = '<span class="badge badge-indigo">Current Focus</span>'
                    current_found = True
                else:
                    status_badge = '<span class="badge badge-slate">Upcoming</span>'

                # Task display row with interactive checkbox
                st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px; font-size:0.8rem; color:var(--text-secondary);">
                        <span>Day {day_num} · {t_type} ({duration}h)</span>
                        {status_badge}
                    </div>
                """, unsafe_allow_html=True)

                chk_key = f"dash_task_{task_id}"
                if chk_key not in st.session_state:
                    st.session_state[chk_key] = is_done
                chk = st.checkbox(
                    label=f"{topic_name}",
                    key=chk_key
                )
                if chk != is_done:
                    db.toggle_task_completion(task_id, chk)
                    _invalidate_data_cache()
                    st.rerun()

                st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="acad-card" style="text-align:left; padding:1.25rem;">
                    <div style="font-weight:600; color:#f8fafc; font-size:0.95rem; margin-bottom:4px;">No Active Plan Created</div>
                    <div style="color:var(--text-secondary); font-size:0.84rem; margin-bottom:12px;">Generate a tailored study plan calibrated against your exam timeline and learning materials.</div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Generate 5-Day Plan", key="btn_create_plan_dash", type="primary", use_container_width=True):
                st.session_state.preset_agent_query = "Prepare me for my DBMS exam in five days."
                st.session_state.selected_nav_page = "🤖 AI Study Assistant"
                st.session_state.active_tab_redirect = "AI Study Assistant"
                st.rerun()

    with col_right:
        # 6. NEXT ACTION (Prioritized action button, navigates without reload)
        st.markdown("<h3>Prioritized Action</h3>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class="acad-card" style="margin-bottom:12px; padding:1rem 1.2rem;">
                <div style="font-weight:600; color:#f8fafc; font-size:0.92rem; margin-bottom:2px;">Target Weak Spot: {primary_weak_topic}</div>
                <div style="font-size:0.82rem; color:var(--text-secondary); margin-bottom:10px;">Immediate practice test to raise retention on your lowest-performing module.</div>
            </div>
        """, unsafe_allow_html=True)

        if st.button(f"Practice {primary_weak_topic}", key="btn_next_action_quiz", type="primary", use_container_width=True):
            st.session_state.selected_nav_page = "📝 Quiz Generator"
            st.session_state.active_tab_redirect = "Quiz Generator"
            st.rerun()

        st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)

        # 5. TOPIC MASTERY (Restrained progress indicators, weak topics obvious without loud colors)
        st.markdown("<h3>Topic Mastery</h3>", unsafe_allow_html=True)
        topic_breakdown = perf.get("topic_breakdown", {})
        if perf.get("has_data") and topic_breakdown:
            for top_name, top_info in sorted(topic_breakdown.items(), key=lambda x: x[1]["percentage"]):
                pct = top_info["percentage"]
                if pct >= 75:
                    bar_fill_color = "var(--emerald)"
                    tag = '<span class="badge badge-emerald">Strong</span>'
                elif pct >= 50:
                    bar_fill_color = "var(--amber)"
                    tag = '<span class="badge badge-amber">Developing</span>'
                else:
                    bar_fill_color = "var(--rose)"
                    tag = '<span class="badge badge-rose">Attention</span>'

                st.markdown(f"""
                    <div style="margin-bottom:10px; background:#141721; padding:8px 12px; border-radius:6px; border:1px solid var(--border-subtle);">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                            <span style="font-size:0.86rem; font-weight:600; color:#f8fafc;">{top_name}</span>
                            <div style="display:flex; align-items:center; gap:6px;">
                                <span style="font-size:0.82rem; font-weight:600; color:var(--text-secondary);">{pct}%</span>
                                {tag}
                            </div>
                        </div>
                        <div class="prog-container" style="margin-top:2px;">
                            <div class="prog-fill" style="width:{pct}%; background:{bar_fill_color};"></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="acad-card" style="padding:1rem;">
                    <div style="font-size:0.85rem; color:var(--text-secondary);">No assessment data recorded yet. Complete a quiz to populate mastery breakdown.</div>
                </div>
            """, unsafe_allow_html=True)

    # 7. RECENT ACTIVITY (Recent assessments/milestones without exposing raw developer logs)
    st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)
    st.markdown("<h3>Recent Activity</h3>", unsafe_allow_html=True)
    recent_attempts = db.get_quiz_attempts()
    if recent_attempts:
        act_cols = st.columns(min(len(recent_attempts), 3))
        for idx, att in enumerate(recent_attempts[:3]):
            with act_cols[idx]:
                score_pct = att["percentage"]
                score_tag = f"{att['score']}/{att['total_questions']}"
                date_str = att["timestamp"].split("T")[0] if "T" in att["timestamp"] else att["timestamp"]
                badge_markup = '<span class="badge badge-emerald">Passed</span>' if score_pct >= 60 else '<span class="badge badge-rose">Needs Review</span>'
                st.markdown(f"""
                    <div class="acad-card" style="margin-bottom:0; padding:0.9rem 1rem;">
                        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:4px;">
                            <span style="font-size:0.86rem; font-weight:600; color:#f8fafc;">{att['topic']}</span>
                            {badge_markup}
                        </div>
                        <div style="font-size:0.8rem; color:var(--text-secondary);">
                            Score: <b>{score_tag}</b> ({int(score_pct)}%) · {date_str}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="acad-card" style="padding:0.9rem 1rem; color:var(--text-muted); font-size:0.84rem;">
                No recent activity recorded.
            </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2: 📚 DOCUMENT LIBRARY & SEARCH
# ─────────────────────────────────────────────────────────────────────────────
elif selected_page == "📚 Document Library":
    all_docs = db.get_documents()
    total_docs = len(all_docs)
    total_chunks = sum(d.get("num_chunks", 0) for d in all_docs)
    last_doc_name = all_docs[-1]["filename"] if all_docs else "None"

    # 1. HEADER
    st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:1.25rem; border-bottom:1px solid var(--border-subtle); padding-bottom:0.75rem;">
            <div>
                <span style="font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--primary);">Course Knowledge Base</span>
                <h1 style="margin:0; font-size:1.65rem; font-weight:700; color:#f8fafc; letter-spacing:-0.025em;">Knowledge Library</h1>
                <p style="margin:0; font-size:0.86rem; color:var(--text-secondary); margin-top:2px;">Your indexed course material, ready for AI-powered retrieval.</p>
            </div>
            <div style="text-align:right;">
                <span class="badge badge-slate">Grounded Knowledge</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 2. LIBRARY SUMMARY (Compact metrics without fabricated statistics)
    sum_c1, sum_c2, sum_c3 = st.columns(3)
    with sum_c1:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Documents Indexed</div>
                <div class="metric-num">{total_docs}</div>
                <div class="metric-sub">Syllabus & lecture reference files</div>
            </div>
        """, unsafe_allow_html=True)
    with sum_c2:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Content Passages</div>
                <div class="metric-num">{total_chunks}</div>
                <div class="metric-sub">Indexed text sections available for search</div>
            </div>
        """, unsafe_allow_html=True)
    with sum_c3:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Latest Reference</div>
                <div class="metric-num" style="font-size:1.15rem; margin-top:8px; line-height:1.3; color:#f8fafc; text-overflow:ellipsis; overflow:hidden; white-space:nowrap;">{last_doc_name}</div>
                <div class="metric-sub">Most recently registered resource</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    # 5. SEARCH KNOWLEDGE (Prominent academic search with relevance and AI Tutor handoff)
    st.markdown("<h3>Search Knowledge</h3>", unsafe_allow_html=True)
    search_col1, search_col2 = st.columns([4.2, 1])
    with search_col1:
        search_query = st.text_input(
            label="Search course notes",
            placeholder="Search keywords e.g. 'normalization', 'indexing', 'transactions'...",
            label_visibility="collapsed",
            key="doc_search_input"
        )
    with search_col2:
        execute_search = st.button("Search Notes", type="primary", use_container_width=True)

    active_query = search_query.strip()
    if execute_search and active_query:
        st.session_state.search_query_trigger = active_query
    elif not active_query and st.session_state.search_query_trigger:
        active_query = st.session_state.search_query_trigger

    if active_query:
        with st.spinner(f"Searching indexed material for '{active_query}'..."):
            s_res = document_search(query=active_query, top_k=5, db_path=DB_PATH)
            chunks_found = s_res.get("chunks", []) if s_res.get("found") else []

            if chunks_found:
                st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px; margin-bottom:12px;">
                        <span style="font-size:0.86rem; color:var(--text-secondary);">Found <b>{len(chunks_found)} matching passage(s)</b> for <span style="color:#f8fafc;">"{active_query}"</span></span>
                    </div>
                """, unsafe_allow_html=True)

                # Ask AI Tutor about this search query (direct seamless handoff)
                ask_tutor_col1, ask_tutor_col2 = st.columns([3, 1])
                with ask_tutor_col2:
                    if st.button("Ask AI Tutor About This", key="btn_ask_tutor_search", use_container_width=True):
                        st.session_state.preset_agent_query = f"Explain {active_query} based on my notes."
                        st.session_state.selected_nav_page = "🤖 AI Study Assistant"
                        st.rerun()

                for idx, c in enumerate(chunks_found):
                    sim_score = int(c.get("similarity_score", 0) * 100)
                    score_badge = '<span class="badge badge-emerald">High Relevance</span>' if sim_score >= 40 else '<span class="badge badge-indigo">Relevant Match</span>'
                    st.markdown(f"""
                        <div class="acad-card" style="margin-bottom:10px; border-left:3px solid var(--primary); padding:1rem 1.25rem;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                <span style="font-weight:600; color:#f8fafc; font-size:0.9rem;">Source: {c['source']} · Page {c.get('page_number', 1)}</span>
                                {score_badge}
                            </div>
                            <div style="color:#cbd5e1; font-size:0.86rem; line-height:1.65; background:#0f121a; padding:10px 12px; border-radius:6px; border:1px solid var(--border-subtle);">
                                {c['text']}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="acad-card" style="padding:1rem 1.2rem; margin-top:8px;">
                        <div style="font-weight:600; color:#f8fafc; font-size:0.9rem; margin-bottom:4px;">No Passages Found</div>
                        <div style="font-size:0.84rem; color:var(--text-secondary);">No relevant notes matched "{active_query}". Try related keywords or verify course material is indexed below.</div>
                    </div>
                """, unsafe_allow_html=True)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    # 3. DOCUMENT LIST & 6. EMPTY STATE
    st.markdown("<h3>Indexed Course Documents</h3>", unsafe_allow_html=True)
    if all_docs:
        doc_cols = st.columns(2)
        for idx, d in enumerate(all_docs):
            with doc_cols[idx % 2]:
                upload_dt = d.get("upload_time", "").split("T")[0] if "T" in d.get("upload_time", "") else d.get("upload_time", "")
                is_sample = d.get("is_sample", 0) == 1
                sample_tag = '<span class="badge badge-slate">Sample Material</span>' if is_sample else '<span class="badge badge-indigo">Uploaded</span>'
                st.markdown(f"""
                    <div class="acad-card" style="margin-bottom:12px; padding:1.1rem 1.25rem;">
                        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:6px;">
                            <div style="font-weight:600; color:#f8fafc; font-size:0.95rem;">{d['filename']}</div>
                            <span class="badge badge-emerald">Indexed</span>
                        </div>
                        <div style="font-size:0.8rem; color:var(--text-secondary); margin-bottom:6px;">
                            {d['file_type']} · {d['num_pages']} Pages · {d['num_chunks']} Search Chunks
                        </div>
                        <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.75rem; color:var(--text-muted); border-top:1px solid rgba(255,255,255,0.04); padding-top:6px; margin-top:6px;">
                            <span>Registered: {upload_dt or 'Active'}</span>
                            {sample_tag}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    else:
        # 6. EMPTY STATE
        st.markdown("""
            <div class="acad-card" style="padding:1.5rem; text-align:left;">
                <div style="font-weight:600; color:#f8fafc; font-size:0.95rem; margin-bottom:4px;">No Course Material Indexed Yet</div>
                <div style="font-size:0.85rem; color:var(--text-secondary); line-height:1.6; max-width:600px; margin-bottom:12px;">
                    Upload your course syllabus, lecture slides, or textbook PDFs below to enable semantic retrieval, 
                    targeted quiz question generation, and grounded AI study tutoring.
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)

    # 4. ADD / INDEX DOCUMENT (Explicit user action required)
    st.markdown("<h3>Add Course Document</h3>", unsafe_allow_html=True)
    with st.container():
        st.markdown("""
            <div style="font-size:0.82rem; color:var(--text-secondary); margin-bottom:8px;">
                Select a PDF syllabus, lecture deck, or revision document to index into your personal knowledge base.
            </div>
        """, unsafe_allow_html=True)

        uploaded_pdf = st.file_uploader(
            "Select course document",
            type=["pdf"],
            key="pdf_uploader_widget",
            label_visibility="collapsed"
        )

        if uploaded_pdf is not None:
            up_col1, up_col2 = st.columns([3, 1])
            with up_col1:
                st.markdown(f"""
                    <div style="font-size:0.85rem; color:var(--text-primary); padding:8px 0;">
                        Selected: <b>{uploaded_pdf.name}</b> ({int(uploaded_pdf.size / 1024)} KB)
                    </div>
                """, unsafe_allow_html=True)
            with up_col2:
                if st.button("Index Document", type="primary", use_container_width=True):
                    with st.spinner(f"Extracting and indexing '{uploaded_pdf.name}'..."):
                        try:
                            pages, extract_warning = extract_text_from_pdf(uploaded_pdf, uploaded_pdf.name)
                            if extract_warning:
                                st.warning(extract_warning)
                            chunks = chunk_document_pages(pages, filename=uploaded_pdf.name)
                            doc_id = db.save_document(
                                filename=uploaded_pdf.name,
                                file_type="PDF",
                                num_chunks=len(chunks),
                                num_pages=len(pages),
                                chunks=chunks
                            )
                            st.success(f"Indexed '{uploaded_pdf.name}' ({len(chunks)} passages ready).")
                            _invalidate_data_cache()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to process document: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 3: 🤖 AI STUDY ASSISTANT (MULTI-TOOL AGENT)
# ─────────────────────────────────────────────────────────────────────────────
elif selected_page == "🤖 AI Study Assistant":
    # 1. HEADER (Academic Study Tutor)
    st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:1.25rem; border-bottom:1px solid var(--border-subtle); padding-bottom:0.75rem;">
            <div>
                <span style="font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--primary);">Central Intelligence</span>
                <h1 style="margin:0; font-size:1.65rem; font-weight:700; color:#f8fafc; letter-spacing:-0.025em;">AI Study Tutor</h1>
                <p style="margin:0; font-size:0.86rem; color:var(--text-secondary); margin-top:2px;">Ask about your coursework, preparation, performance, or study plan.</p>
            </div>
            <div style="text-align:right;">
                <span class="badge badge-slate">Multi-Agent System</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 2. INPUT AREA (Prominent query composer with clean example prompts)
    st.markdown("""
        <div style="font-size:0.78rem; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; color:var(--text-muted); margin-bottom:6px;">
            Suggested Inquiries
        </div>
    """, unsafe_allow_html=True)

    prompt_cols = st.columns(4)
    with prompt_cols[0]:
        if st.button("Prepare me for my DBMS exam in five days", key="ex_prep", use_container_width=True):
            st.session_state.preset_agent_query = "Prepare me for my DBMS exam in five days."
            st.rerun()
    with prompt_cols[1]:
        if st.button("Explain normalization from my notes", key="ex_norm", use_container_width=True):
            st.session_state.preset_agent_query = "Find normalization in my notes."
            st.rerun()
    with prompt_cols[2]:
        if st.button("What should I study today?", key="ex_plan", use_container_width=True):
            st.session_state.preset_agent_query = "What should I study today according to my study plan?"
            st.rerun()
    with prompt_cols[3]:
        if st.button("Create a quiz on indexing", key="ex_quiz", use_container_width=True):
            st.session_state.preset_agent_query = "Give me a quiz on indexing."
            st.rerun()

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # Query composer input with prefill
    prefill_val = st.session_state.preset_agent_query
    input_col, btn_col = st.columns([4.2, 1])
    with input_col:
        user_query = st.text_input(
            "Query composer",
            placeholder="Type your academic question, syllabus topic, or exam deadline...",
            value=prefill_val,
            label_visibility="collapsed"
        )
    with btn_col:
        send_clicked = st.button("Submit Query", type="primary", use_container_width=True)

    # Agent execution trigger
    if send_clicked and user_query.strip():
        query_to_run = user_query.strip()
        # Clear the prefill so the input box is empty on the next render.
        st.session_state.preset_agent_query = ""
        orch = MultiToolOrchestrator(
            db_path=DB_PATH,
            api_key=st.session_state.get("user_gemini_key", None),
        )
        with st.spinner("Supervisor coordinating specialist agents..."):
            result = orch.run(query_to_run)
            st.session_state.chat_history.append({"query": query_to_run, "result": result})
            _invalidate_data_cache()
            st.rerun()
    elif send_clicked and not user_query.strip():
        st.warning("Please enter a question or select an example prompt above.")

    # 6. EMPTY STATE (When no conversation exists yet)
    if not st.session_state.chat_history:
        st.markdown("<div style='height:1.25rem;'></div>", unsafe_allow_html=True)
        st.markdown("""
            <div class="acad-card" style="padding:1.75rem 1.5rem; text-align:left;">
                <div style="font-size:0.95rem; font-weight:600; color:#f8fafc; margin-bottom:4px;">Ready to Assist</div>
                <div style="font-size:0.86rem; color:var(--text-secondary); line-height:1.6; max-width:680px;">
                    Enter an academic question or select an example above. The <b>Supervisor Agent</b> decomposes your request 
                    and delegates retrieval, diagnostic assessment, performance analytics, and study timetable planning to 
                    dedicated specialist agents in real time.
                </div>
            </div>
        """, unsafe_allow_html=True)

    # 3, 4, 5. RESPONSE AREA & AGENT ACTIVITY (Render conversation in reverse chronological order)
    if st.session_state.chat_history:
        # Agent role lookup for structured reporting
        agent_descriptions = {
            "SupervisorAgent": "Coordinated planning and synthesized final grounded response",
            "KnowledgeAgent": "Retrieved course notes and verified curriculum syllabus units",
            "AssessmentAgent": "Generated diagnostic assessment questions and answer options",
            "PerformanceAgent": "Analyzed quiz history and evaluated student mastery levels",
            "PlanningAgent": "Generated adaptive study timetable calibrated against exam timeline",
            "ProgressAgent": "Inspected learning milestones and recorded student status",
        }

        for item_idx, item in enumerate(reversed(st.session_state.chat_history)):
            res = item["result"]
            query_str = item["query"]

            st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

            # Query Card
            st.markdown(f"""
                <div style="background:#10131c; border:1px solid var(--border-subtle); border-left:3px solid var(--primary); padding:10px 14px; border-radius:6px; margin-bottom:12px;">
                    <div style="font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:var(--text-muted);">Inquiry</div>
                    <div style="font-size:1rem; font-weight:600; color:#f8fafc; margin-top:2px;">{query_str}</div>
                </div>
            """, unsafe_allow_html=True)

            # 3. RESPONSE AREA (Structured Supervisor Response)
            st.markdown(f"""
                <div class="acad-card" style="padding:1.4rem; margin-bottom:12px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; border-bottom:1px solid var(--border-subtle); padding-bottom:8px;">
                        <span style="font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:var(--primary);">Supervisor Response</span>
                        <span class="badge badge-slate">{res.goal}</span>
                    </div>
                    <div style="color:#e2e8f0; font-size:0.92rem; line-height:1.7;">
                        {res.final_response}
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # 5. RECOMMENDED ACTION (Direct navigation without reload)
            rec_action = res.recommended_next_action
            if rec_action:
                st.markdown(f"""
                    <div style="background:#131722; border:1px solid var(--border-subtle); border-radius:6px; padding:10px 14px; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                        <div>
                            <div style="font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; color:var(--text-muted);">Recommended Next Step</div>
                            <div style="font-size:0.88rem; font-weight:600; color:#f8fafc;">{rec_action}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                # Context-aware navigation button based on recommendation text
                rec_lower = rec_action.lower()
                btn_action_label = "Proceed to Next Action"
                target_nav = "📝 Quiz Generator"

                if "quiz" in rec_lower or "diagnostic" in rec_lower or "test" in rec_lower:
                    btn_action_label = "Open Quiz Generator"
                    target_nav = "📝 Quiz Generator"
                elif "study plan" in rec_lower or "timetable" in rec_lower or "planner" in rec_lower or "schedule" in rec_lower:
                    btn_action_label = "Open Study Planner"
                    target_nav = "📅 Study Planner"
                elif "notes" in rec_lower or "library" in rec_lower or "document" in rec_lower:
                    btn_action_label = "Open Document Library"
                    target_nav = "📚 Document Library"
                elif "analytic" in rec_lower or "performance" in rec_lower:
                    btn_action_label = "Open Performance Analytics"
                    target_nav = "📈 Performance Analyzer"

                if st.button(btn_action_label, key=f"btn_rec_{item_idx}", type="primary"):
                    st.session_state.selected_nav_page = target_nav
                    st.rerun()

            # 4. AGENT ACTIVITY (Restrained, only showing actual participating agents and clean summaries)
            st.markdown("""
                <div style="font-size:0.78rem; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; color:var(--text-muted); margin-top:16px; margin-bottom:8px;">
                    Agent Activity
                </div>
            """, unsafe_allow_html=True)

            participating = getattr(res, "participating_agents", ["SupervisorAgent"])
            traces_by_agent: Dict[str, List[Any]] = {}
            for t in res.traces:
                t_agent = t.tool_name.split()[0] if " " in t.tool_name else t.tool_name
                traces_by_agent.setdefault(t_agent, []).append(t)

            st.markdown('<div class="acad-card" style="padding:10px 14px; margin-bottom:1.5rem;">', unsafe_allow_html=True)
            for agent_name in participating:
                agent_traces = traces_by_agent.get(agent_name, [])
                is_failed = any(t.status == "FAILED" for t in agent_traces)
                status_icon = "⚠️" if is_failed else "✓"
                status_color = "var(--rose)" if is_failed else "var(--emerald)"
                responsibility = agent_descriptions.get(agent_name, "Specialist agent task execution")

                # Concise action summary
                if agent_traces:
                    summary_text = agent_traces[0].summary
                elif agent_name == "SupervisorAgent":
                    summary_text = f"Analyzed inquiry, selected {len(participating)-1} specialist agent(s), and synthesized response"
                else:
                    summary_text = "Participated in specialist coordination workflow"

                st.markdown(f"""
                    <div style="padding:7px 0; border-bottom:1px solid rgba(255,255,255,0.04);">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div style="display:flex; align-items:center; gap:6px;">
                                <span style="color:{status_color}; font-weight:700; font-size:0.85rem;">{status_icon}</span>
                                <span style="font-size:0.88rem; font-weight:600; color:#f8fafc;">{agent_name}</span>
                            </div>
                            <span style="font-size:0.72rem; color:var(--text-muted);">{responsibility}</span>
                        </div>
                        <div style="font-size:0.82rem; color:var(--text-secondary); margin-left:18px; margin-top:2px;">
                            {summary_text}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 4: 📝 QUIZ GENERATOR
# ─────────────────────────────────────────────────────────────────────────────
elif selected_page == "📝 Quiz Generator":
    # 1. HEADER
    st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:1.25rem; border-bottom:1px solid var(--border-subtle); padding-bottom:0.75rem;">
            <div>
                <span style="font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--primary);">Diagnostic Evaluation</span>
                <h1 style="margin:0; font-size:1.65rem; font-weight:700; color:#f8fafc; letter-spacing:-0.025em;">Assessments</h1>
                <p style="margin:0; font-size:0.86rem; color:var(--text-secondary); margin-top:2px;">Measure what you know and identify what needs attention.</p>
            </div>
            <div style="text-align:right;">
                <span class="badge badge-slate">Adaptive Diagnostics</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 8. AGENT CONTEXT (If navigated from AI Tutor or Study Plan)
    if st.session_state.get("preset_agent_query"):
        st.markdown("""
            <div style="background:#131722; border:1px solid var(--border-subtle); border-left:3px solid var(--primary); padding:8px 12px; border-radius:4px; margin-bottom:12px; font-size:0.8rem; color:var(--text-secondary);">
                <b>Recommended by your learning plan:</b> Calibrated to address your current syllabus milestone and diagnostic baseline.
            </div>
        """, unsafe_allow_html=True)

    # STATE 1: CONFIGURATION & PRE-ASSESSMENT CONTEXT
    if st.session_state.current_quiz is None:
        q_col1, q_col2 = st.columns([1.1, 0.9], gap="large")

        with q_col1:
            st.markdown("<h3>Configure Assessment</h3>", unsafe_allow_html=True)
            quiz_topic = st.selectbox(
                label="Topic",
                options=[
                    "Indexing & Storage",
                    "Normalization",
                    "SQL & Query Optimization",
                    "Relational Model & Integrity",
                    "Transactions & Concurrency"
                ],
                index=0
            )
            quiz_diff = st.selectbox("Difficulty Level", ["easy", "medium", "hard"], index=1)
            quiz_num = st.slider("Number of Questions", min_value=2, max_value=8, value=5)

            if st.button("Generate Topic Assessment", type="primary", use_container_width=True):
                with st.spinner(f"Generating diagnostic questions for {quiz_topic}..."):
                    q_res = generate_quiz(
                        topic=quiz_topic,
                        difficulty=quiz_diff,
                        number_of_questions=quiz_num,
                        db_path=DB_PATH,
                        api_key=st.session_state.get("user_gemini_key")
                    )
                    if q_res.get("status") == "SUCCESS":
                        st.session_state.current_quiz = q_res
                        st.session_state.quiz_result = None
                        st.rerun()
                    else:
                        st.error(q_res.get("message", "Error generating assessment."))

        with q_col2:
            # 2. ASSESSMENT CONTEXT (Real previous performance and mastery data)
            st.markdown("<h3>Assessment Context</h3>", unsafe_allow_html=True)
            topic_history = perf.get("topic_breakdown", {}).get(quiz_topic)
            if topic_history:
                t_pct = topic_history.get("percentage", 0)
                t_att = topic_history.get("total_attempts", topic_history.get("attempts", 1))
                t_badge = '<span class="badge badge-rose">Needs Attention</span>' if t_pct < 60 else ('<span class="badge badge-amber">Developing</span>' if t_pct < 80 else '<span class="badge badge-emerald">Strong</span>')
                reason_text = f"Your current accuracy on <b>{quiz_topic}</b> is <b>{t_pct}%</b> across {t_att} attempt(s). A focused 5-question test will pinpoint remaining conceptual gaps."
            else:
                t_pct = None
                t_badge = '<span class="badge badge-slate">Unassessed Baseline</span>'
                reason_text = f"No past quiz records found for <b>{quiz_topic}</b>. Taking this diagnostic assessment will establish your baseline mastery score."

            st.markdown(f"""
                <div class="acad-card" style="padding:1.15rem 1.25rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span style="font-weight:600; color:#f8fafc; font-size:0.92rem;">{quiz_topic}</span>
                        {t_badge}
                    </div>
                    <div style="font-size:0.82rem; color:var(--text-secondary); line-height:1.6; margin-bottom:10px;">
                        {reason_text}
                    </div>
                    <div style="border-top:1px solid rgba(255,255,255,0.05); padding-top:8px; font-size:0.78rem; color:var(--text-muted);">
                        Course: <b>Database Management Systems (DBMS)</b> · Recommended: <b>{quiz_diff.capitalize()} difficulty</b>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # STATE 2: ACTIVE QUIZ IN PROGRESS
    elif st.session_state.quiz_result is None:
        quiz = st.session_state.current_quiz
        q_count = len(quiz["questions"])

        # 4. ACTIVE QUIZ (Header with progress indicator)
        st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; border-bottom:1px solid var(--border-subtle); padding-bottom:8px;">
                <div>
                    <span style="font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:var(--primary);">Active Assessment</span>
                    <h2 style="margin:2px 0; font-size:1.3rem; font-weight:700; color:#f8fafc;">{quiz['topic']}</h2>
                </div>
                <div style="display:flex; gap:6px; align-items:center;">
                    <span class="badge badge-indigo">{quiz['difficulty'].capitalize()}</span>
                    <span class="badge badge-slate">{q_count} Questions</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # 5. SUBMISSION (Form-guarded execution to guarantee 1 click = 1 write, no reruns resubmitting)
        with st.form("assessment_active_form", clear_on_submit=False):
            user_answers = {}
            for idx, q in enumerate(quiz["questions"]):
                st.markdown(f"""
                    <div style="margin-top:12px; margin-bottom:6px; font-size:0.92rem; font-weight:600; color:#f8fafc;">
                        Question {idx+1} of {q_count}
                    </div>
                    <div style="font-size:0.88rem; color:#cbd5e1; margin-bottom:8px; line-height:1.5;">
                        {q['question']}
                    </div>
                """, unsafe_allow_html=True)

                chosen_opt = st.radio(
                    label=f"Options for question {idx+1}",
                    options=q["options"],
                    key=f"quiz_opt_{q['id']}",
                    label_visibility="collapsed"
                )
                user_answers[str(q["id"])] = chosen_opt
                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

            sub_col1, sub_col2 = st.columns([1.2, 3.8])
            with sub_col1:
                submitted = st.form_submit_button("Submit Assessment", type="primary", use_container_width=True)

            if submitted:
                sub_res = record_quiz_submission(
                    topic=quiz["topic"],
                    difficulty=quiz["difficulty"],
                    questions=quiz["questions"],
                    user_answers=user_answers,
                    db_path=DB_PATH
                )
                st.session_state.quiz_result = sub_res
                _invalidate_data_cache()  # force fresh DB read on next render
                st.rerun()

        if st.button("Cancel & Exit", key="btn_cancel_assessment"):
            st.session_state.current_quiz = None
            st.session_state.quiz_result = None
            st.rerun()

    # STATE 3: RESULTS & ADAPTIVE NEXT ACTION
    else:
        # 6. RESULTS
        sub_res = st.session_state.quiz_result
        score = sub_res.get("score", 0)
        total = sub_res.get("total", sub_res.get("total_questions", 1))
        pct = sub_res.get("percentage", 0.0)
        topic_name = sub_res.get("topic", "Assessment")

        if pct >= 80:
            class_badge = '<span class="badge badge-emerald">Strong (≥80%)</span>'
            insight_text = f"Excellent mastery on <b>{topic_name}</b>. You have demonstrated comprehensive grasp of core principles."
            action_btn_text = "Continue to Next Syllabus Topic"
            next_topic_target = "Normalization"
        elif pct >= 60:
            class_badge = '<span class="badge badge-amber">Developing (60–79%)</span>'
            insight_text = f"Satisfactory grasp on <b>{topic_name}</b>, but some conceptual gaps remain. Targeted review is recommended."
            action_btn_text = "Review Notes & Retry"
            next_topic_target = topic_name
        else:
            class_badge = '<span class="badge badge-rose">Needs Attention (<60%)</span>'
            insight_text = f"Accuracy on <b>{topic_name}</b> is below passing threshold. We recommend an urgent study block before testing again."
            action_btn_text = f"Practice {topic_name}"
            next_topic_target = topic_name

        st.markdown(f"""
            <div class="acad-card" style="padding:1.4rem 1.5rem; margin-bottom:1.25rem;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;">
                    <div>
                        <div style="font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:var(--text-muted);">Assessment Result</div>
                        <div style="font-size:2rem; font-weight:700; color:#f8fafc; letter-spacing:-0.02em; margin-top:2px;">
                            {score} / {total} <span style="font-size:1.15rem; font-weight:600; color:var(--text-secondary);">({int(pct)}%)</span>
                        </div>
                        <div style="font-size:0.86rem; color:var(--text-secondary); margin-top:4px;">
                            {insight_text}
                        </div>
                    </div>
                    <div style="text-align:right;">
                        {class_badge}
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # 7. ADAPTIVE NEXT ACTION (Obvious next step routing without manual reload)
        st.markdown("<h3>Adaptive Next Action</h3>", unsafe_allow_html=True)
        act_col1, act_col2, act_col3 = st.columns([1.5, 1.2, 1.3])

        with act_col1:
            if st.button(action_btn_text, key="btn_adapt_next", type="primary", use_container_width=True):
                if pct >= 80:
                    st.session_state.current_quiz = None
                    st.session_state.quiz_result = None
                    st.session_state.selected_nav_page = "📅 Study Planner"
                else:
                    # Retry or practice
                    st.session_state.current_quiz = None
                    st.session_state.quiz_result = None
                st.rerun()

        with act_col2:
            if st.button("Search Topic Notes", key="btn_review_notes", use_container_width=True):
                st.session_state.search_query_trigger = topic_name
                st.session_state.selected_nav_page = "📚 Document Library"
                st.rerun()

        with act_col3:
            if st.button("Return to Dashboard", key="btn_ret_dash", use_container_width=True):
                st.session_state.current_quiz = None
                st.session_state.quiz_result = None
                st.session_state.selected_nav_page = "📊 Dashboard"
                st.rerun()

        st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

        # Detailed question breakdown with explanation review
        st.markdown("<h3>Question Breakdown</h3>", unsafe_allow_html=True)
        details = sub_res.get("details", sub_res.get("graded_questions", []))
        for idx, q in enumerate(details):
            is_correct = q.get("is_correct", False)
            border_c = "var(--emerald)" if is_correct else "var(--rose)"
            icon = "✓" if is_correct else "✗"
            tag_markup = '<span class="badge badge-emerald">Correct</span>' if is_correct else '<span class="badge badge-rose">Incorrect</span>'

            st.markdown(f"""
                <div class="acad-card" style="border-left:3px solid {border_c}; padding:1rem 1.25rem; margin-bottom:10px;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:6px;">
                        <div style="font-weight:600; color:#f8fafc; font-size:0.92rem;">
                            {idx+1}. {q['question']}
                        </div>
                        {tag_markup}
                    </div>
                    <div style="font-size:0.84rem; color:var(--text-secondary); margin-bottom:4px;">
                        Your answer: <span style="color:{'#34d399' if is_correct else '#f87171'}; font-weight:600;">{q.get('user_answer', 'None')}</span>
                    </div>
                    <div style="font-size:0.84rem; color:#cbd5e1; margin-bottom:8px;">
                        Correct answer: <span style="color:#34d399; font-weight:600;">{q.get('correct_answer', '')}</span>
                    </div>
                    <div style="background:#0f121a; border:1px solid var(--border-subtle); border-radius:4px; padding:8px 10px; font-size:0.8rem; color:#94a3b8; line-height:1.5;">
                        <b>Explanation:</b> {q.get('explanation', '')}
                    </div>
                </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 5: 📈 PERFORMANCE ANALYZER
# ─────────────────────────────────────────────────────────────────────────────
elif selected_page == "📈 Performance Analyzer":

    # ── 1. HEADER ────────────────────────────────────────────────────────────
    st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:1.25rem; border-bottom:1px solid var(--border-subtle); padding-bottom:0.75rem;">
            <div>
                <span style="font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--primary);">EduSync AI</span>
                <h1 style="margin:0; font-size:1.65rem; font-weight:700; color:#f8fafc; letter-spacing:-0.025em;">Performance</h1>
                <p style="margin:0; font-size:0.86rem; color:var(--text-secondary); margin-top:2px;">Understand your learning gaps and decide what to practice next.</p>
            </div>
            <div style="text-align:right;">
                <span class="badge badge-slate">Academic Analytics</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ── 2. PERFORMANCE SNAPSHOT ──────────────────────────────────────────────
    total_attempts = perf.get("total_attempts", stats.get("quiz_attempts_count", 0))
    overall_accuracy = perf.get("overall_score", stats.get("average_quiz_score", 0.0))
    strong_topics_list = perf.get("strong_topics", [])
    weak_topics_list = perf.get("weak_topics", [])
    developing_topics_list = perf.get("developing_topics", [])
    topic_breakdown = perf.get("topic_breakdown", {})

    strong_count = len(strong_topics_list)
    weak_count = len(weak_topics_list)

    acc_color = "#10b981" if overall_accuracy >= 80 else ("#f59e0b" if overall_accuracy >= 60 else "#ef4444")
    acc_label = "Strong" if overall_accuracy >= 80 else ("Developing" if overall_accuracy >= 60 else "Needs Attention")

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Overall Accuracy</div>
                <div class="metric-num" style="color:{acc_color};">{overall_accuracy}%</div>
                <div class="metric-sub">{acc_label} aggregate standing</div>
            </div>
        """, unsafe_allow_html=True)
    with s2:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Total Assessments</div>
                <div class="metric-num">{total_attempts}</div>
                <div class="metric-sub">Completed evaluations</div>
            </div>
        """, unsafe_allow_html=True)
    with s3:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Strong Topics</div>
                <div class="metric-num" style="color:#10b981;">{strong_count}</div>
                <div class="metric-sub">Meeting ≥80% threshold</div>
            </div>
        """, unsafe_allow_html=True)
    with s4:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Topics Needing Attention</div>
                <div class="metric-num" style="color:#ef4444;">{weak_count}</div>
                <div class="metric-sub">Falling below 60% threshold</div>
            </div>
        """, unsafe_allow_html=True)

    # ── 3. TOPIC MASTERY ─────────────────────────────────────────────────────
    st.markdown("""
        <div style="margin-top:1.5rem; margin-bottom:0.75rem;">
            <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted);">Topic Mastery</div>
            <div style="font-size:1.1rem; font-weight:600; color:#f8fafc; margin-top:2px;">Performance breakdown by subject area</div>
        </div>
    """, unsafe_allow_html=True)

    if perf.get("has_data") and topic_breakdown:
        st.markdown("""
            <div style="display:grid; grid-template-columns:2.5fr 1.2fr 1fr 140px; gap:12px; padding:6px 14px;
                        font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em;
                        color:var(--text-muted); border-bottom:1px solid var(--border-subtle); margin-bottom:6px;">
                <div>Topic</div>
                <div>Accuracy & Score</div>
                <div>Attempts</div>
                <div style="text-align:right;">Classification</div>
            </div>
        """, unsafe_allow_html=True)

        sorted_topics = sorted(topic_breakdown.items(), key=lambda x: (x[1]["percentage"], x[0]))
        for t_name, t_info in sorted_topics:
            t_pct = t_info["percentage"]
            t_score = t_info.get("score", 0)
            t_total = t_info.get("total_questions", 0)
            t_attempts = t_info.get("attempts", 1)

            if t_pct >= 80.0:
                t_badge = '<span class="badge badge-emerald">Strong</span>'
                t_color = "#10b981"
            elif t_pct >= 60.0:
                t_badge = '<span class="badge badge-amber">Developing</span>'
                t_color = "#f59e0b"
            else:
                t_badge = '<span class="badge badge-rose">Needs Attention</span>'
                t_color = "#ef4444"

            st.markdown(f"""
                <div style="background:#131722; border:1px solid var(--border-subtle); border-radius:8px;
                            padding:12px 14px; margin-bottom:8px;">
                    <div style="display:grid; grid-template-columns:2.5fr 1.2fr 1fr 140px; gap:12px; align-items:center;">
                        <div style="font-weight:600; color:#f1f5f9; font-size:0.92rem;">{t_name}</div>
                        <div>
                            <span style="font-weight:700; color:{t_color}; font-size:0.92rem;">{t_pct}%</span>
                            <span style="font-size:0.8rem; color:var(--text-muted); margin-left:6px;">({t_score}/{t_total} correct)</span>
                        </div>
                        <div style="font-size:0.85rem; color:var(--text-secondary);">{t_attempts} attempt{'s' if t_attempts != 1 else ''}</div>
                        <div style="text-align:right;">{t_badge}</div>
                    </div>
                    <div class="prog-container" style="margin-top:10px; height:6px; background:#1e2230; border-radius:3px; overflow:hidden;">
                        <div class="prog-fill" style="width:{min(max(t_pct, 0.0), 100.0)}%; height:100%; background:{t_color}; border-radius:3px;"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="acad-card" style="text-align:center; padding:2rem;">
                <div style="font-size:0.95rem; color:var(--text-secondary); font-weight:600;">No Assessment Data Recorded</div>
                <div style="font-size:0.82rem; color:var(--text-muted); margin-top:4px;">Take a practice quiz to generate topic mastery metrics and progress tracking.</div>
            </div>
        """, unsafe_allow_html=True)

    # ── 4. LEARNING DIAGNOSIS ────────────────────────────────────────────────
    st.markdown("""
        <div style="margin-top:1.75rem; margin-bottom:0.75rem;">
            <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted);">Learning Diagnosis</div>
            <div style="font-size:1.1rem; font-weight:600; color:#f8fafc; margin-top:2px;">Data-backed diagnostic findings</div>
        </div>
    """, unsafe_allow_html=True)

    if perf.get("has_data") and topic_breakdown:
        diagnosis_entries = []
        for wt in weak_topics_list:
            diagnosis_entries.append({
                "topic": wt["topic"],
                "color": "#ef4444",
                "label": "Needs Attention",
                "text": f"{wt['topic']} is your main attention area at {wt['percentage']}% ({wt['score']}/{wt['total_questions']} correct across {wt['attempts']} attempt{'s' if wt['attempts'] != 1 else ''})."
            })
        for dt in developing_topics_list:
            diagnosis_entries.append({
                "topic": dt["topic"],
                "color": "#f59e0b",
                "label": "Developing",
                "text": f"{dt['topic']} is currently developing at {dt['percentage']}% ({dt['score']}/{dt['total_questions']} correct across {dt['attempts']} attempt{'s' if dt['attempts'] != 1 else ''})."
            })
        for st_t in strong_topics_list:
            diagnosis_entries.append({
                "topic": st_t["topic"],
                "color": "#10b981",
                "label": "Strong",
                "text": f"{st_t['topic']} is currently strong at {st_t['percentage']}% ({st_t['score']}/{st_t['total_questions']} correct across {st_t['attempts']} attempt{'s' if st_t['attempts'] != 1 else ''})."
            })

        for entry in diagnosis_entries:
            st.markdown(f"""
                <div style="display:flex; align-items:flex-start; gap:12px; padding:12px 16px;
                            background:#131722; border:1px solid var(--border-subtle); border-radius:8px;
                            margin-bottom:8px; border-left:3px solid {entry['color']};">
                    <div style="flex:1;">
                        <div style="font-size:0.7rem; font-weight:700; text-transform:uppercase;
                                     letter-spacing:0.06em; color:{entry['color']};">{entry['label']}</div>
                        <div style="font-size:0.88rem; color:#cbd5e1; margin-top:3px; line-height:1.5;">{entry['text']}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="acad-card" style="padding:1.2rem;">
                <div style="font-size:0.88rem; color:var(--text-secondary);">Insufficient performance data to generate diagnostic findings. Complete an evaluation first.</div>
            </div>
        """, unsafe_allow_html=True)

    # ── 5. WHAT TO DO NEXT ───────────────────────────────────────────────────
    st.markdown("""
        <div style="margin-top:1.75rem; margin-bottom:0.75rem;">
            <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted);">What To Do Next</div>
            <div style="font-size:1.1rem; font-weight:600; color:#f8fafc; margin-top:2px;">Targeted recommendations based on actual mastery</div>
        </div>
    """, unsafe_allow_html=True)

    if perf.get("has_data") and topic_breakdown:
        action_items = []
        for wt in weak_topics_list:
            action_items.append({
                "type": "weak",
                "topic": wt["topic"],
                "badge": '<span class="badge badge-rose">Needs Attention</span>',
                "color": "#ef4444",
                "desc": f"Score is {wt['percentage']}%. Take a focused diagnostic assessment on {wt['topic']} to reinforce foundational concepts.",
                "btn_label": f"Practice {wt['topic']}",
                "target_page": "📝 Quiz Generator",
                "is_primary": True,
            })
        for dt in developing_topics_list:
            action_items.append({
                "type": "developing",
                "topic": dt["topic"],
                "badge": '<span class="badge badge-amber">Developing</span>',
                "color": "#f59e0b",
                "desc": f"Score is {dt['percentage']}%. Review course notes and reference materials on {dt['topic']}, then retry an assessment.",
                "btn_label": "Review Notes",
                "target_page": "📚 Document Library",
                "is_primary": False,
            })
        for st_t in strong_topics_list:
            action_items.append({
                "type": "strong",
                "topic": st_t["topic"],
                "badge": '<span class="badge badge-emerald">Strong</span>',
                "color": "#10b981",
                "desc": f"Score is {st_t['percentage']}%. Mastery achieved. Continue to next scheduled topic in your study plan.",
                "btn_label": "Continue in Plan",
                "target_page": "📅 Study Planner",
                "is_primary": False,
            })

        for idx, act in enumerate(action_items):
            act_col1, act_col2 = st.columns([3.2, 1.2], gap="medium")
            with act_col1:
                st.markdown(f"""
                    <div style="padding:4px 0 8px 0;">
                        <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
                            <span style="font-size:0.92rem; font-weight:700; color:#f1f5f9;">{act['topic']}</span>
                            {act['badge']}
                        </div>
                        <div style="font-size:0.84rem; color:var(--text-secondary); line-height:1.45;">{act['desc']}</div>
                    </div>
                """, unsafe_allow_html=True)
            with act_col2:
                btn_type = "primary" if act["is_primary"] else "secondary"
                safe_slug = act["topic"].lower().replace(" ", "_").replace("&", "and")
                if st.button(
                    act["btn_label"],
                    key=f"perf_act_{safe_slug}_{idx}",
                    type=btn_type,
                    use_container_width=True
                ):
                    st.session_state.selected_nav_page = act["target_page"]
                    st.session_state.active_tab_redirect = act["target_page"]
                    st.rerun()
            st.markdown("<div style='height:1px; background:var(--border-subtle); margin-bottom:8px;'></div>", unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="acad-card" style="padding:1.25rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                <div>
                    <div style="font-weight:600; color:#f8fafc; font-size:0.92rem;">Take an initial diagnostic evaluation</div>
                    <div style="font-size:0.82rem; color:var(--text-muted); margin-top:2px;">No quiz attempts recorded. Complete a quiz to unlock tailored next steps.</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Open Quiz Generator", key="perf_empty_action_btn", type="primary", use_container_width=False):
            st.session_state.selected_nav_page = "📝 Quiz Generator"
            st.session_state.active_tab_redirect = "Quiz Generator"
            st.rerun()

    # ── 6. ASSESSMENT HISTORY ────────────────────────────────────────────────
    st.markdown("""
        <div style="margin-top:1.75rem; margin-bottom:0.75rem;">
            <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted);">Assessment History</div>
            <div style="font-size:1.1rem; font-weight:600; color:#f8fafc; margin-top:2px;">All recorded evaluation attempts</div>
        </div>
    """, unsafe_allow_html=True)

    all_attempts = db.get_quiz_attempts()
    if all_attempts:
        st.markdown("""
            <div style="display:grid; grid-template-columns:2.5fr 1fr 1fr 140px 1.2fr; gap:10px; padding:6px 14px;
                        font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em;
                        color:var(--text-muted); border-bottom:1px solid var(--border-subtle); margin-bottom:6px;">
                <div>Topic</div>
                <div>Score</div>
                <div>Percentage</div>
                <div>Classification</div>
                <div style="text-align:right;">Date & Time</div>
            </div>
        """, unsafe_allow_html=True)

        for att in all_attempts:
            att_pct = float(att.get("percentage", 0.0))
            att_score = att.get("score", 0)
            att_total = att.get("total_questions", 0)
            att_topic = att.get("topic", "—")
            raw_ts = att.get("timestamp", "")

            if raw_ts:
                try:
                    dt_obj = datetime.fromisoformat(raw_ts)
                    att_date = dt_obj.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    att_date = raw_ts[:16].replace("T", " ")
            else:
                att_date = "—"

            if att_pct >= 80.0:
                att_badge = '<span class="badge badge-emerald">Strong</span>'
                att_color = "#10b981"
            elif att_pct >= 60.0:
                att_badge = '<span class="badge badge-amber">Developing</span>'
                att_color = "#f59e0b"
            else:
                att_badge = '<span class="badge badge-rose">Needs Attention</span>'
                att_color = "#ef4444"

            st.markdown(f"""
                <div style="display:grid; grid-template-columns:2.5fr 1fr 1fr 140px 1.2fr; gap:10px; align-items:center;
                            padding:10px 14px; background:#131722; border:1px solid var(--border-subtle);
                            border-radius:6px; margin-bottom:4px;">
                    <div style="font-weight:600; color:#f1f5f9; font-size:0.88rem;">{att_topic}</div>
                    <div style="font-size:0.86rem; color:#cbd5e1;">{att_score} / {att_total}</div>
                    <div style="font-size:0.86rem; font-weight:700; color:{att_color};">{att_pct}%</div>
                    <div>{att_badge}</div>
                    <div style="text-align:right; font-size:0.78rem; color:var(--text-muted); font-family:'JetBrains Mono', monospace;">{att_date}</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="acad-card" style="text-align:center; padding:1.5rem;">
                <div style="font-size:0.9rem; color:var(--text-secondary);">No assessment history recorded.</div>
                <div style="font-size:0.82rem; color:var(--text-muted); margin-top:4px;">Completed quizzes will be logged here with scores and timestamps.</div>
            </div>
        """, unsafe_allow_html=True)

    # ── 7. PROGRESS INTERPRETATION ───────────────────────────────────────────
    st.markdown("""
        <div style="margin-top:1.75rem; margin-bottom:0.75rem;">
            <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted);">Progress Interpretation</div>
            <div style="font-size:1.1rem; font-weight:600; color:#f8fafc; margin-top:2px;">Longitudinal performance trajectory</div>
        </div>
    """, unsafe_allow_html=True)

    if all_attempts and len(all_attempts) >= 3:
        sorted_attempts = sorted(all_attempts, key=lambda x: x.get("timestamp") or str(x.get("id", 0)))
        mid = len(sorted_attempts) // 2
        first_half = sorted_attempts[:mid]
        second_half = sorted_attempts[mid:]

        avg_first = sum(float(a.get("percentage", 0.0)) for a in first_half) / len(first_half)
        avg_second = sum(float(a.get("percentage", 0.0)) for a in second_half) / len(second_half)
        diff = round(avg_second - avg_first, 1)

        if diff > 5.0:
            trend_badge = '<span class="badge badge-emerald">Improving</span>'
            trend_color = "#10b981"
            trend_title = "Improving Trajectory"
            trend_msg = f"Recent attempts average {avg_second:.1f}% compared to {avg_first:.1f}% in earlier attempts (+{diff}% change). Your performance is trending upward."
        elif diff < -5.0:
            trend_badge = '<span class="badge badge-rose">Declining</span>'
            trend_color = "#ef4444"
            trend_title = "Declining Trajectory"
            trend_msg = f"Recent attempts average {avg_second:.1f}% compared to {avg_first:.1f}% in earlier attempts ({diff}% change). Recent evaluations indicate emerging knowledge gaps that need review."
        else:
            trend_badge = '<span class="badge badge-amber">Stable</span>'
            trend_color = "#f59e0b"
            trend_title = "Stable Trajectory"
            trend_msg = f"Average performance is consistent across attempts ({avg_first:.1f}% in earlier attempts vs. {avg_second:.1f}% in recent attempts, {diff:+.1f}% change). Targeted practice on weak areas can break this plateau."

        st.markdown(f"""
            <div style="background:#131722; border:1px solid var(--border-subtle); border-radius:8px;
                        padding:1.1rem 1.4rem; border-left:3px solid {trend_color};">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                    <div style="font-size:0.92rem; font-weight:700; color:#f8fafc;">{trend_title}</div>
                    {trend_badge}
                </div>
                <div style="font-size:0.88rem; color:#cbd5e1; line-height:1.55;">{trend_msg}</div>
                <div style="font-size:0.75rem; color:var(--text-muted); margin-top:8px;">
                    Calculated from {len(all_attempts)} recorded attempts evaluated in chronological sequence.
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        attempts_count = len(all_attempts) if all_attempts else 0
        attempts_needed = max(0, 3 - attempts_count)
        st.markdown(f"""
            <div style="background:#131722; border:1px solid var(--border-subtle); border-radius:8px;
                        padding:1.1rem 1.4rem;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                    <div style="font-size:0.92rem; font-weight:600; color:#f8fafc;">Insufficient Historical Data</div>
                    <span class="badge badge-slate">Baseline Pending</span>
                </div>
                <div style="font-size:0.88rem; color:var(--text-secondary); line-height:1.55;">
                    Insufficient historical data to determine a performance trend. A minimum of 3 completed assessments is required to establish a meaningful trajectory.
                </div>
                <div style="font-size:0.75rem; color:var(--text-muted); margin-top:6px;">
                    Currently recorded: {attempts_count}/3 attempts (complete {attempts_needed} more assessment{'s' if attempts_needed != 1 else ''} to unlock trajectory analysis).
                </div>
            </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 6: 📅 STUDY PLANNER
# ─────────────────────────────────────────────────────────────────────────────
elif selected_page == "📅 Study Planner":

    # ── 1. HEADER ────────────────────────────────────────────────────────────
    st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:1.25rem; border-bottom:1px solid var(--border-subtle); padding-bottom:0.75rem;">
            <div>
                <span style="font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--primary);">EduSync AI</span>
                <h1 style="margin:0; font-size:1.65rem; font-weight:700; color:#f8fafc; letter-spacing:-0.025em;">Study Plan</h1>
                <p style="margin:0; font-size:0.86rem; color:var(--text-secondary); margin-top:2px;">Turn your exam deadline and learning gaps into a realistic daily plan.</p>
            </div>
            <div style="text-align:right;">
                <span class="badge badge-slate">Exam Preparation</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Re-read cached plan (invalidated after plan creation/reset)
    active_plan = st.session_state.get("_cached_plan", db.get_active_study_plan())

    # ── 2. PLAN OVERVIEW ─────────────────────────────────────────────────────
    if active_plan:
        val = parse_and_validate_exam_date(active_plan["exam_date"])
        days_left = val.get("days_remaining", 0)
        tasks = db.get_study_tasks(active_plan["id"])
        plan_hours = active_plan.get("available_hours", active_plan.get("daily_hours", 3.0))

        completed_count = sum(1 for t in tasks if t["completed"] == 1)
        total_count = len(tasks)
        pct_complete = int((completed_count / total_count) * 100) if total_count > 0 else 0

        # Status badge
        if days_left <= 0:
            plan_status_badge = '<span class="badge badge-rose">Exam Day / Past</span>'
        elif days_left == 1:
            plan_status_badge = '<span class="badge badge-rose">Final Day</span>'
        elif days_left <= 2:
            plan_status_badge = '<span class="badge badge-amber">Last 2 Days</span>'
        else:
            plan_status_badge = '<span class="badge badge-indigo">Active</span>'

        total_study_hours = round(plan_hours * days_left, 1) if days_left > 0 else 0.0

        # Overview card
        st.markdown(f"""
            <div style="background:#131722; border:1px solid var(--border-subtle); border-radius:8px;
                        padding:1.2rem 1.4rem; margin-bottom:1.25rem; border-left:3px solid var(--primary);">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;">
                    <div style="flex:1; min-width:260px;">
                        <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:var(--text-muted); margin-bottom:4px;">Active Plan</div>
                        <div style="font-size:1.3rem; font-weight:700; color:#f8fafc; letter-spacing:-0.015em; margin-bottom:4px;">{active_plan['subject']}</div>
                        <div style="font-size:0.84rem; color:var(--text-secondary);">
                            Exam date: <b style="color:#f1f5f9;">{active_plan['exam_date']}</b>
                            &nbsp;·&nbsp; {plan_hours}h/day
                            &nbsp;·&nbsp; {days_left} day{'s' if days_left != 1 else ''} remaining
                        </div>
                    </div>
                    <div style="display:flex; gap:28px; flex-wrap:wrap; align-items:center;">
                        <div style="text-align:center;">
                            <div style="font-size:1.5rem; font-weight:700; color:var(--primary);">{days_left}</div>
                            <div style="font-size:0.7rem; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; color:var(--text-muted);">Days Left</div>
                        </div>
                        <div style="text-align:center;">
                            <div style="font-size:1.5rem; font-weight:700; color:#10b981;">{completed_count}</div>
                            <div style="font-size:0.7rem; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; color:var(--text-muted);">Completed</div>
                        </div>
                        <div style="text-align:center;">
                            <div style="font-size:1.5rem; font-weight:700; color:#f59e0b;">{total_count - completed_count}</div>
                            <div style="font-size:0.7rem; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; color:var(--text-muted);">Remaining</div>
                        </div>
                        <div style="text-align:center;">
                            {plan_status_badge}
                        </div>
                    </div>
                </div>
                <div style="margin-top:14px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
                        <span style="font-size:0.78rem; color:var(--text-secondary); font-weight:600;">Plan Completion</span>
                        <span style="font-size:0.78rem; font-weight:700; color:{'#10b981' if pct_complete >= 80 else '#f59e0b' if pct_complete >= 40 else '#94a3b8'};">{pct_complete}%</span>
                    </div>
                    <div class="prog-container" style="height:6px;">
                        <div class="prog-fill" style="width:{pct_complete}%; background:{'#10b981' if pct_complete >= 80 else 'var(--primary)'};"></div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # ── 3. PRIORITIZATION CONTEXT ─────────────────────────────────────────
        weak_topics_list  = perf.get("weak_topics", [])
        strong_topics_list = perf.get("strong_topics", [])
        developing_topics_list = perf.get("developing_topics", [])

        if perf.get("has_data") and (weak_topics_list or developing_topics_list or strong_topics_list):
            st.markdown("""
                <div style="margin-top:0.5rem; margin-bottom:0.75rem;">
                    <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted);">Performance-Aware Prioritization</div>
                    <div style="font-size:1.05rem; font-weight:600; color:#f8fafc; margin-top:2px;">How weak topics shaped this plan</div>
                </div>
            """, unsafe_allow_html=True)

            priority_rows = []
            for wt in weak_topics_list:
                priority_rows.append((wt["topic"], "High Priority", "#ef4444", "badge-rose",
                    f"{wt['percentage']}% accuracy — highest weight in schedule (3×)"))
            for dt in developing_topics_list:
                priority_rows.append((dt["topic"], "Moderate Priority", "#f59e0b", "badge-amber",
                    f"{dt['percentage']}% accuracy — medium weight in schedule (2×)"))
            for st_t in strong_topics_list:
                priority_rows.append((st_t["topic"], "Maintenance", "#10b981", "badge-emerald",
                    f"{st_t['percentage']}% accuracy — lower weight, maintenance revision only (1×)"))

            for row_topic, row_label, row_color, row_badge, row_note in priority_rows:
                st.markdown(f"""
                    <div style="display:flex; align-items:center; gap:12px; padding:9px 14px;
                                background:#131722; border:1px solid var(--border-subtle); border-radius:6px;
                                margin-bottom:5px; border-left:3px solid {row_color};">
                        <div style="flex:1;">
                            <span style="font-weight:600; color:#f1f5f9; font-size:0.88rem;">{row_topic}</span>
                            <span style="font-size:0.78rem; color:var(--text-muted); margin-left:8px;">{row_note}</span>
                        </div>
                        <span class="badge {row_badge}">{row_label}</span>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

        # ── 4. DAILY SCHEDULE ─────────────────────────────────────────────────
        if tasks:
            st.markdown("""
                <div style="margin-top:1.25rem; margin-bottom:0.75rem;">
                    <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted);">Daily Schedule</div>
                    <div style="font-size:1.1rem; font-weight:600; color:#f8fafc; margin-top:2px;">Task-by-task breakdown with completion tracking</div>
                </div>
            """, unsafe_allow_html=True)

            today_str = date.today().isoformat()
            day_groups: Dict[int, List[Dict[str, Any]]] = {}
            for t in tasks:
                day_groups.setdefault(t["day_number"], []).append(t)

            # Load plan_data_json to get dates per day
            import json
            days_plan_raw = active_plan.get("days_plan", [])
            day_dates: Dict[int, str] = {}
            day_focuses: Dict[int, str] = {}
            for dp in days_plan_raw:
                d_num = dp.get("day", dp.get("day_number"))
                if d_num:
                    day_dates[d_num] = dp.get("date", "")
                    day_focuses[d_num] = dp.get("focus", "")

            for d_num in sorted(day_groups.keys()):
                day_task_list = day_groups[d_num]
                day_date_str = day_dates.get(d_num, "")
                day_focus = day_focuses.get(d_num, "")
                day_completed = sum(1 for t in day_task_list if t["completed"] == 1)
                day_total = len(day_task_list)
                day_pct = int((day_completed / day_total) * 100) if day_total > 0 else 0

                # Identify day label
                is_today = (day_date_str == today_str)
                if is_today:
                    day_label_badge = '<span class="badge badge-indigo">Today</span>'
                elif day_date_str and day_date_str < today_str:
                    day_label_badge = '<span class="badge badge-slate">Past</span>'
                elif d_num == max(day_groups.keys()):
                    day_label_badge = '<span class="badge badge-rose">Final Day</span>'
                else:
                    day_label_badge = ""

                day_color = "#10b981" if day_pct == 100 else ("var(--primary)" if is_today else "var(--border-subtle)")
                done_color = "#10b981" if day_pct == 100 else "var(--text-muted)"
                date_span = f'<span style="font-size:0.8rem; color:var(--text-muted);">· {day_date_str}</span>' if day_date_str else ""
                focus_span = f'<span style="font-size:0.78rem; color:var(--text-secondary);">{day_focus}</span>' if day_focus else ""

                # Day header (using continuous HTML string without indentation to prevent markdown code block parsing)
                day_header_html = (
                    f'<div style="display:flex; justify-content:space-between; align-items:center; '
                    f'padding:10px 14px; background:#0f1219; border:1px solid {day_color}; '
                    f'border-radius:6px; margin-top:10px; margin-bottom:4px;">'
                    f'<div style="display:flex; align-items:center; gap:10px;">'
                    f'<span style="font-size:0.88rem; font-weight:700; color:#f8fafc;">Day {d_num}</span>'
                    f'{" " + day_label_badge if day_label_badge else ""}'
                    f'{" " + date_span if date_span else ""}'
                    f'</div>'
                    f'<div style="display:flex; align-items:center; gap:10px;">'
                    f'{focus_span}'
                    f'<span style="font-size:0.75rem; font-weight:600; color:{done_color};">{day_completed}/{day_total} done</span>'
                    f'</div>'
                    f'</div>'
                )
                st.markdown(day_header_html, unsafe_allow_html=True)

                # Task rows
                for t in day_task_list:
                    is_t_done = (t["completed"] == 1)

                    type_colors = {
                        "concept": ("var(--primary)", "badge-indigo"),
                        "practice": ("#f59e0b", "badge-amber"),
                        "revision": ("#10b981", "badge-emerald"),
                        "mock": ("#ef4444", "badge-rose"),
                    }
                    t_type_key = t.get("task_type", "concept").lower()
                    t_color, t_badge_cls = type_colors.get(t_type_key, ("var(--primary)", "badge-indigo"))

                    done_style = "opacity:0.55;" if is_t_done else ""
                    done_line = "text-decoration:line-through; color:var(--text-muted);" if is_t_done else "color:#cbd5e1;"

                    col_chk, col_info = st.columns([0.06, 0.94])
                    with col_chk:
                        chk = st.checkbox(
                            f"Complete {t['topic']} task {t['id']}",
                            value=is_t_done,
                            key=f"planner_task_{t['id']}",
                            label_visibility="collapsed"
                        )
                        if chk != is_t_done:
                            db.toggle_task_completion(t["id"], chk)
                            _invalidate_data_cache()
                            st.rerun()

                    with col_info:
                        task_desc = t.get('task_description', t['topic'])
                        task_row_html = (
                            f'<div style="padding:2px 0 8px 0; {done_style}">'
                            f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:2px;">'
                            f'<span class="badge {t_badge_cls}" style="font-size:0.65rem;">{t_type_key.capitalize()}</span>'
                            f'<span style="font-weight:600; font-size:0.86rem; color:#f1f5f9;">{t["topic"]}</span>'
                            f'<span style="font-size:0.78rem; color:var(--text-muted);">· {t["duration_hours"]}h</span>'
                            f'</div>'
                            f'<div style="font-size:0.84rem; {done_line} line-height:1.4;">{task_desc}</div>'
                            f'</div>'
                        )
                        st.markdown(task_row_html, unsafe_allow_html=True)

        # ── 5. NEXT ACTIONS ───────────────────────────────────────────────────
        st.markdown("""
            <div style="margin-top:1.75rem; margin-bottom:0.75rem;">
                <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted);">Next Actions</div>
                <div style="font-size:1.05rem; font-weight:600; color:#f8fafc; margin-top:2px;">Continue your preparation</div>
            </div>
        """, unsafe_allow_html=True)

        act_c1, act_c2, act_c3 = st.columns(3)
        with act_c1:
            if weak_topics_list:
                weak_topic_name = weak_topics_list[0]["topic"]
                if st.button(f"Practice {weak_topic_name}", key="sp_act_practice", type="primary", use_container_width=True):
                    st.session_state.selected_nav_page = "📝 Quiz Generator"
                    st.session_state.active_tab_redirect = "Quiz Generator"
                    st.rerun()
            else:
                if st.button("Take an Assessment", key="sp_act_quiz", use_container_width=True):
                    st.session_state.selected_nav_page = "📝 Quiz Generator"
                    st.session_state.active_tab_redirect = "Quiz Generator"
                    st.rerun()
        with act_c2:
            if st.button("Review Course Notes", key="sp_act_notes", use_container_width=True):
                st.session_state.selected_nav_page = "📚 Document Library"
                st.session_state.active_tab_redirect = "Document Library"
                st.rerun()
        with act_c3:
            if st.button("View Performance", key="sp_act_perf", use_container_width=True):
                st.session_state.selected_nav_page = "📈 Performance Analyzer"
                st.session_state.active_tab_redirect = "Performance Analyzer"
                st.rerun()

    else:
        # ── NO PLAN STATE ─────────────────────────────────────────────────────
        st.markdown("""
            <div class="acad-card" style="text-align:center; padding:2.5rem 2rem; margin-bottom:1.25rem;">
                <div style="font-size:1rem; font-weight:700; color:#f8fafc; margin-bottom:6px;">No Active Study Plan</div>
                <div style="font-size:0.86rem; color:var(--text-secondary); max-width:480px; margin:0 auto;">
                    Configure your exam deadline, topics, and daily availability below to generate a prioritized, day-by-day study schedule.
                </div>
            </div>
        """, unsafe_allow_html=True)

    # ── 6. PLAN CONFIGURATION FORM ────────────────────────────────────────────
    st.markdown(f"""
        <div style="margin-top:1.75rem; margin-bottom:0.75rem;">
            <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted);">{'Regenerate' if active_plan else 'Configure'} Study Plan</div>
            <div style="font-size:1.05rem; font-weight:600; color:#f8fafc; margin-top:2px;">{'Create a new plan to replace the current one' if active_plan else 'Set your exam deadline and availability'}</div>
        </div>
    """, unsafe_allow_html=True)

    available_course_topics = [
        "ER & Relational Model",
        "SQL & Query Optimization",
        "Normalization",
        "Transactions & Concurrency",
        "Indexing & Storage",
    ]

    with st.form("custom_study_plan_form"):
        cfg_c1, cfg_c2 = st.columns([2, 1.5])
        with cfg_c1:
            p_subject = st.text_input(
                "Subject / Course Name",
                value=active_plan["subject"] if active_plan else "Database Management Systems (DBMS)",
                placeholder="e.g. Database Management Systems"
            )
        with cfg_c2:
            target_exam_date = st.date_input(
                "Exam Date",
                value=date.today() + timedelta(days=5),
                min_value=date.today() + timedelta(days=1),
                help="Must be at least 1 day in the future. Past dates are not accepted."
            )

        selected_topics = st.multiselect(
            "Topics to Cover",
            options=available_course_topics,
            default=available_course_topics,
            help="Select which topics to schedule across your study plan."
        )

        study_hours = st.slider(
            "Daily Study Hours",
            min_value=1.0, max_value=8.0,
            value=float(active_plan["available_hours"]) if active_plan else 3.0,
            step=0.5,
            help="Realistic daily hours available for study (1–8 hrs)"
        )

        generate_submitted = st.form_submit_button(
            "Generate Study Plan" if not active_plan else "Regenerate Study Plan",
            type="primary",
            use_container_width=True
        )
        if generate_submitted:
            if not p_subject.strip():
                st.error("Subject name is required. Please enter a course or subject name.")
            elif not selected_topics:
                st.error("Please select at least one topic to include in your study plan.")
            else:
                with st.spinner("Generating personalized study plan..."):
                    p_res = create_study_plan(
                        exam_date=target_exam_date.isoformat(),
                        available_hours=study_hours,
                        topics=selected_topics,
                        subject=p_subject.strip(),
                        performance=perf if perf.get("has_data") else None,
                        db_path=DB_PATH
                    )
                    if p_res.get("status") == "SUCCESS":
                        days_gen = p_res.get("days_remaining", 0)
                        tasks_gen = p_res.get("total_tasks", 0)
                        st.success(f"Study plan generated: {days_gen}-day schedule with {tasks_gen} tasks.")
                        _invalidate_data_cache()
                        st.rerun()
                    else:
                        st.error(p_res.get("message", "Could not generate a study plan. Check your inputs."))

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 7: 🎯 PROGRESS TRACKER
# ─────────────────────────────────────────────────────────────────────────────
elif selected_page == "🎯 Progress Tracker":

    # ── 1. HEADER ────────────────────────────────────────────────────────────
    st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:1.25rem; border-bottom:1px solid var(--border-subtle); padding-bottom:0.75rem;">
            <div>
                <span style="font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--primary);">EduSync AI</span>
                <h1 style="margin:0; font-size:1.65rem; font-weight:700; color:#f8fafc; letter-spacing:-0.025em;">Learning Progress</h1>
                <p style="margin:0; font-size:0.86rem; color:var(--text-secondary); margin-top:2px;">Track what you have completed and how your understanding is developing.</p>
            </div>
            <div style="text-align:right;">
                <span class="badge badge-slate">Progress &amp; Mastery</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ── DATA GATHERING (Read-only, no mutations) ──────────────────────────────
    active_plan = st.session_state.get("_cached_plan", db.get_active_study_plan())
    plan_tasks = db.get_study_tasks(active_plan["id"]) if active_plan else []
    completed_plan_tasks = [t for t in plan_tasks if t["completed"] == 1]
    completed_tasks_count = len(completed_plan_tasks)
    total_tasks_count = len(plan_tasks)
    remaining_tasks_count = max(0, total_tasks_count - completed_tasks_count)
    plan_pct = int((completed_tasks_count / total_tasks_count) * 100) if total_tasks_count > 0 else 0

    quiz_attempts_count = stats.get("quiz_attempts_count", 0)
    avg_quiz_score = stats.get("average_quiz_score", 0.0)
    all_attempts = db.get_quiz_attempts()

    if avg_quiz_score >= 80.0:
        avg_score_color = "#10b981"
        accuracy_label = "Strong retention"
    elif avg_quiz_score >= 60.0:
        avg_score_color = "#f59e0b"
        accuracy_label = "Developing mastery"
    elif quiz_attempts_count > 0:
        avg_score_color = "#ef4444"
        accuracy_label = "Gaps identified"
    else:
        avg_score_color = "var(--text-muted)"
        accuracy_label = "No assessments taken"

    # ── 2. PROGRESS SNAPSHOT ─────────────────────────────────────────────────
    st.markdown("""
        <div style="margin-bottom:0.75rem;">
            <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted);">Progress Snapshot</div>
            <div style="font-size:1.05rem; font-weight:600; color:#f8fafc; margin-top:2px;">Execution vs. comprehension metrics</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; margin-bottom:0.75rem;">
            <div class="metric-box">
                <div class="metric-num" style="color:#10b981;">{completed_tasks_count}</div>
                <div class="metric-title">Completed Tasks</div>
                <div class="metric-sub">{plan_pct}% of plan done</div>
            </div>
            <div class="metric-box">
                <div class="metric-num" style="color:#f59e0b;">{remaining_tasks_count}</div>
                <div class="metric-title">Remaining Tasks</div>
                <div class="metric-sub">Out of {total_tasks_count} total</div>
            </div>
            <div class="metric-box">
                <div class="metric-num" style="color:var(--primary);">{quiz_attempts_count}</div>
                <div class="metric-title">Assessments Taken</div>
                <div class="metric-sub">Recorded evaluations</div>
            </div>
            <div class="metric-box">
                <div class="metric-num" style="color:{avg_score_color};">{avg_quiz_score:.1f}%</div>
                <div class="metric-title">Overall Accuracy</div>
                <div class="metric-sub">{accuracy_label}</div>
            </div>
        </div>
        <div style="font-size:0.76rem; color:var(--text-muted); line-height:1.45; margin-bottom:1.5rem; padding:0 4px;">
            <span style="font-weight:600; color:#cbd5e1;">Metric Distinction:</span> Task completion measures study time and schedule execution, while assessment accuracy measures demonstrated topic comprehension on diagnostic questions.
        </div>
    """, unsafe_allow_html=True)

    # ── 3. STUDY PLAN PROGRESS ───────────────────────────────────────────────
    st.markdown("""
        <div style="margin-bottom:0.75rem;">
            <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted);">Active Study Plan</div>
            <div style="font-size:1.05rem; font-weight:600; color:#f8fafc; margin-top:2px;">Schedule execution status</div>
        </div>
    """, unsafe_allow_html=True)

    if active_plan and plan_tasks:
        val = parse_and_validate_exam_date(active_plan["exam_date"])
        days_left = val.get("days_remaining", 0)
        plan_hours = active_plan.get("available_hours", active_plan.get("daily_hours", 3.0))

        # Task type counts
        concept_tasks = sum(1 for t in plan_tasks if t.get("task_type") == "concept")
        practice_tasks = sum(1 for t in plan_tasks if t.get("task_type") == "practice")
        revision_tasks = sum(1 for t in plan_tasks if t.get("task_type") == "revision")
        mock_tasks = sum(1 for t in plan_tasks if t.get("task_type") == "mock")

        concept_done = sum(1 for t in plan_tasks if t.get("task_type") == "concept" and t["completed"] == 1)
        practice_done = sum(1 for t in plan_tasks if t.get("task_type") == "practice" and t["completed"] == 1)
        revision_done = sum(1 for t in plan_tasks if t.get("task_type") == "revision" and t["completed"] == 1)
        mock_done = sum(1 for t in plan_tasks if t.get("task_type") == "mock" and t["completed"] == 1)

        prog_bar_color = "#10b981" if plan_pct >= 80 else ("var(--primary)" if plan_pct > 0 else "var(--border-subtle)")

        st.markdown(f"""
            <div style="background:#131722; border:1px solid var(--border-subtle); border-radius:8px;
                        padding:1.2rem 1.4rem; margin-bottom:1.5rem; border-left:3px solid var(--primary);">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px; margin-bottom:12px;">
                    <div>
                        <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:var(--text-muted); margin-bottom:3px;">Course Scope</div>
                        <div style="font-size:1.25rem; font-weight:700; color:#f8fafc; letter-spacing:-0.015em;">{active_plan['subject']}</div>
                        <div style="font-size:0.84rem; color:var(--text-secondary); margin-top:2px;">
                            Exam date: <b style="color:#f1f5f9;">{active_plan['exam_date']}</b>
                            &nbsp;·&nbsp; {plan_hours}h/day
                            &nbsp;·&nbsp; {days_left} day{'s' if days_left != 1 else ''} remaining
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <span class="badge badge-indigo">{completed_tasks_count} of {total_tasks_count} Tasks Completed</span>
                        <div style="font-size:0.75rem; color:var(--text-muted); margin-top:4px;">{remaining_tasks_count} task{'s' if remaining_tasks_count != 1 else ''} remaining</div>
                    </div>
                </div>
                <div style="margin-bottom:12px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
                        <span style="font-size:0.78rem; color:var(--text-secondary); font-weight:600;">Plan Execution</span>
                        <span style="font-size:0.78rem; font-weight:700; color:{'#10b981' if plan_pct >= 80 else '#f59e0b' if plan_pct >= 40 else '#94a3b8'};">{plan_pct}%</span>
                    </div>
                    <div class="prog-container" style="height:6px;">
                        <div class="prog-fill" style="width:{plan_pct}%; background:{prog_bar_color};"></div>
                    </div>
                </div>
                <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:8px; padding-top:8px; border-top:1px solid var(--border-subtle);">
                    <div style="font-size:0.78rem; color:var(--text-secondary);">
                        <span class="badge badge-indigo" style="font-size:0.65rem; margin-right:4px;">Concept</span>
                        <b>{concept_done}/{concept_tasks}</b>
                    </div>
                    <div style="font-size:0.78rem; color:var(--text-secondary);">
                        <span class="badge badge-amber" style="font-size:0.65rem; margin-right:4px;">Practice</span>
                        <b>{practice_done}/{practice_tasks}</b>
                    </div>
                    <div style="font-size:0.78rem; color:var(--text-secondary);">
                        <span class="badge badge-emerald" style="font-size:0.65rem; margin-right:4px;">Revision</span>
                        <b>{revision_done}/{revision_tasks}</b>
                    </div>
                    <div style="font-size:0.78rem; color:var(--text-secondary);">
                        <span class="badge badge-rose" style="font-size:0.65rem; margin-right:4px;">Mock</span>
                        <b>{mock_done}/{mock_tasks}</b>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="acad-card" style="padding:1.5rem 1.75rem; margin-bottom:1.5rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:14px;">
                <div>
                    <div style="font-size:0.95rem; font-weight:600; color:#f8fafc;">No Active Study Plan Configured</div>
                    <div style="font-size:0.84rem; color:var(--text-secondary); margin-top:2px;">Configure your exam deadline and daily hours in the Study Planner to generate an active daily schedule.</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Configure Study Plan", key="pt_empty_plan_btn", type="primary"):
            st.session_state.selected_nav_page = "📅 Study Planner"
            st.session_state.active_tab_redirect = "Study Planner"
            st.rerun()

    # ── 4. TOPIC MASTERY ─────────────────────────────────────────────────────
    st.markdown("""
        <div style="margin-bottom:0.75rem;">
            <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted);">Topic Mastery</div>
            <div style="font-size:1.05rem; font-weight:600; color:#f8fafc; margin-top:2px;">Evaluated knowledge by syllabus area</div>
        </div>
    """, unsafe_allow_html=True)

    if perf.get("has_data") and perf.get("topic_breakdown"):
        for t_name, t_info in sorted(perf["topic_breakdown"].items(), key=lambda x: x[1]["percentage"]):
            t_pct = float(t_info.get("percentage", 0.0))
            t_score = t_info.get("score", 0)
            t_total = t_info.get("total_questions", 0)
            t_attempts = t_info.get("attempts", t_info.get("attempts_count", 0))

            if t_pct >= 80.0:
                m_badge = '<span class="badge badge-emerald">Strong</span>'
                m_bar_color = "#10b981"
            elif t_pct >= 60.0:
                m_badge = '<span class="badge badge-amber">Developing</span>'
                m_bar_color = "#f59e0b"
            else:
                m_badge = '<span class="badge badge-rose">Needs Attention</span>'
                m_bar_color = "#ef4444"

            st.markdown(f"""
                <div style="background:#131722; border:1px solid var(--border-subtle); border-radius:6px;
                            padding:12px 16px; margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                        <div style="display:flex; align-items:center; gap:10px;">
                            <span style="font-weight:600; color:#f8fafc; font-size:0.92rem;">{t_name}</span>
                            {m_badge}
                            <span style="font-size:0.75rem; color:var(--text-muted);">({t_attempts} attempt{'s' if t_attempts != 1 else ''})</span>
                        </div>
                        <div style="text-align:right;">
                            <span style="font-weight:700; color:{m_bar_color}; font-size:0.92rem;">{t_pct:.1f}%</span>
                            <span style="font-size:0.78rem; color:var(--text-muted); margin-left:6px;">({t_score}/{t_total} pts)</span>
                        </div>
                    </div>
                    <div class="prog-container" style="height:6px;">
                        <div class="prog-fill" style="width:{t_pct}%; background:{m_bar_color};"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("""
            <div style="font-size:0.75rem; color:var(--text-muted); margin-top:4px; margin-bottom:1.5rem;">
                Thresholds: <b>≥80% Strong</b> &nbsp;·&nbsp; <b>60–79% Developing</b> &nbsp;·&nbsp; <b>&lt;60% Needs Attention</b>. Mastery is determined strictly from quiz evaluations, not task checkboxes.
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="acad-card" style="padding:1.5rem; text-align:center; margin-bottom:1.5rem;">
                <div style="font-size:0.92rem; font-weight:600; color:#f8fafc;">No Topic Assessments Logged</div>
                <div style="font-size:0.84rem; color:var(--text-secondary); margin-top:3px;">Take an assessment in Quiz Generator to calculate your topic mastery breakdown.</div>
            </div>
        """, unsafe_allow_html=True)

    # ── 5. RECENT ACTIVITY ───────────────────────────────────────────────────
    st.markdown("""
        <div style="margin-bottom:0.75rem;">
            <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted);">Recent Activity</div>
            <div style="font-size:1.05rem; font-weight:600; color:#f8fafc; margin-top:2px;">Chronological evaluations and task completions</div>
        </div>
    """, unsafe_allow_html=True)

    # Query recent completed tasks directly from DB (read-only)
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, topic, task_description, duration_hours, task_type, completed_at
            FROM study_tasks
            WHERE completed = 1
            ORDER BY completed_at DESC, id DESC
            LIMIT 5
        """)
        recent_completed_tasks = [dict(r) for r in cursor.fetchall()]

    act_col1, act_col2 = st.columns(2)

    with act_col1:
        st.markdown("""
            <div style="font-size:0.84rem; font-weight:600; color:#e2e8f0; margin-bottom:8px;">
                📝 Assessment Evaluations
            </div>
        """, unsafe_allow_html=True)

        if all_attempts:
            for att in all_attempts[:4]:
                att_pct = float(att.get("percentage", 0.0))
                att_score = att.get("score", 0)
                att_total = att.get("total_questions", 0)
                att_topic = att.get("topic", "—")
                raw_ts = att.get("timestamp", "")
                if raw_ts:
                    try:
                        dt_obj = datetime.fromisoformat(raw_ts)
                        att_date = dt_obj.strftime("%b %d, %H:%M")
                    except Exception:
                        att_date = raw_ts[:16].replace("T", " ")
                else:
                    att_date = "—"

                if att_pct >= 80.0:
                    badge_cls = "badge-emerald"
                elif att_pct >= 60.0:
                    badge_cls = "badge-amber"
                else:
                    badge_cls = "badge-rose"

                st.markdown(f"""
                    <div style="background:#131722; border:1px solid var(--border-subtle); border-radius:6px;
                                padding:9px 12px; margin-bottom:6px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:600; color:#f1f5f9; font-size:0.86rem;">{att_topic}</span>
                            <span class="badge {badge_cls}" style="font-size:0.68rem;">{att_pct:.0f}% ({att_score}/{att_total})</span>
                        </div>
                        <div style="font-size:0.75rem; color:var(--text-muted); margin-top:3px; font-family:'JetBrains Mono', monospace;">
                            Evaluated: {att_date}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="acad-card" style="padding:1.2rem; text-align:center;">
                    <div style="font-size:0.84rem; color:var(--text-secondary);">No assessment attempts recorded.</div>
                </div>
            """, unsafe_allow_html=True)

    with act_col2:
        st.markdown("""
            <div style="font-size:0.84rem; font-weight:600; color:#e2e8f0; margin-bottom:8px;">
                ✅ Completed Study Tasks
            </div>
        """, unsafe_allow_html=True)

        if recent_completed_tasks:
            for ct in recent_completed_tasks:
                ct_topic = ct.get("topic", "Study Task")
                ct_desc = ct.get("task_description", "")
                ct_dur = ct.get("duration_hours", 1.0)
                raw_ts = ct.get("completed_at", "")
                if raw_ts:
                    try:
                        dt_obj = datetime.fromisoformat(raw_ts)
                        ct_date = dt_obj.strftime("%b %d, %H:%M")
                    except Exception:
                        ct_date = raw_ts[:16].replace("T", " ")
                else:
                    ct_date = "Completed"

                st.markdown(f"""
                    <div style="background:#131722; border:1px solid var(--border-subtle); border-radius:6px;
                                padding:9px 12px; margin-bottom:6px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:600; color:#f1f5f9; font-size:0.86rem;">{ct_topic}</span>
                            <span class="badge badge-emerald" style="font-size:0.68rem;">{ct_dur}h Done</span>
                        </div>
                        <div style="font-size:0.78rem; color:#94a3b8; margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                            {ct_desc}
                        </div>
                        <div style="font-size:0.75rem; color:var(--text-muted); margin-top:3px; font-family:'JetBrains Mono', monospace;">
                            Finished: {ct_date}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="acad-card" style="padding:1.2rem; text-align:center;">
                    <div style="font-size:0.84rem; color:var(--text-secondary);">No study tasks marked complete yet.</div>
                    <div style="font-size:0.76rem; color:var(--text-muted); margin-top:3px;">Mark tasks complete in Study Planner as you work through them.</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)

    # ── 6. PROGRESS INSIGHTS ─────────────────────────────────────────────────
    st.markdown("""
        <div style="margin-bottom:0.75rem;">
            <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted);">Progress Insights</div>
            <div style="font-size:1.05rem; font-weight:600; color:#f8fafc; margin-top:2px;">Evidence-supported learning observations</div>
        </div>
    """, unsafe_allow_html=True)

    insights = []

    # 1. Topic Gap Evidence
    weak_list = perf.get("weak_topics", [])
    strong_list = perf.get("strong_topics", [])

    if weak_list:
        w_names = ", ".join([f"{w['topic']} ({w['percentage']:.0f}%)" for w in weak_list])
        insights.append((
            "Persistent Knowledge Gap",
            f"Assessment records indicate immediate review is needed on <b>{w_names}</b>. These concepts represent your primary vulnerability for upcoming examinations.",
            "#ef4444",
            "badge-rose"
        ))

    if strong_list:
        s_names = ", ".join([f"{s['topic']} ({s['percentage']:.0f}%)" for s in strong_list])
        insights.append((
            "Demonstrated Strength",
            f"Consistent high accuracy demonstrated on <b>{s_names}</b>. Shift daily study hours toward weaker syllabus sections while retaining light periodic maintenance.",
            "#10b981",
            "badge-emerald"
        ))

    # 2. Execution Evidence
    if active_plan:
        if completed_tasks_count > 0:
            insights.append((
                "Plan Execution Underway",
                f"You have completed <b>{completed_tasks_count} of {total_tasks_count}</b> scheduled study tasks ({plan_pct}%). Maintain momentum to cover remaining practice sessions before the exam deadline.",
                "var(--primary)",
                "badge-indigo"
            ))
        else:
            insights.append((
                "Schedule Pending Start",
                f"Your active study plan has <b>{total_tasks_count} scheduled tasks</b> awaiting commencement. Completing Day 1 tasks will establish early momentum on prioritized topics.",
                "#f59e0b",
                "badge-amber"
            ))

    # 3. Trajectory / Historical Depth
    if len(all_attempts) >= 3:
        sorted_att = sorted(all_attempts, key=lambda x: x.get("timestamp") or str(x.get("id", 0)))
        mid = len(sorted_att) // 2
        f_half = sorted_att[:mid]
        s_half = sorted_att[mid:]
        avg_f = sum(x.get("percentage", 0.0) for x in f_half) / len(f_half)
        avg_s = sum(x.get("percentage", 0.0) for x in s_half) / len(s_half)
        diff = avg_s - avg_f

        if diff > 5.0:
            insights.append((
                "Upward Accuracy Trajectory",
                f"Recent evaluation attempts average <b>{avg_s:.1f}%</b> compared to <b>{avg_f:.1f}%</b> in earlier attempts (+{diff:.1f}% increase). Learning retention is advancing.",
                "#10b981",
                "badge-emerald"
            ))
        elif diff < -5.0:
            insights.append((
                "Emerging Gaps Observed",
                f"Recent evaluations average <b>{avg_s:.1f}%</b> compared to <b>{avg_f:.1f}%</b> initially ({diff:.1f}% change). Review challenging topics before taking further quizzes.",
                "#ef4444",
                "badge-rose"
            ))
        else:
            insights.append((
                "Stable Performance Baseline",
                f"Evaluation scores are steady across attempts ({avg_f:.1f}% earlier vs. {avg_s:.1f}% recent). Targeted drills on attention topics will break this plateau.",
                "#f59e0b",
                "badge-amber"
            ))
    else:
        insights.append((
            "Longitudinal Trend Pending",
            f"Currently recorded: <b>{len(all_attempts)}/3 required evaluations</b>. At least 3 assessment attempts are necessary to establish a verified performance trajectory. Streaks and consistency milestones are withheld until sufficient data exists.",
            "var(--text-muted)",
            "badge-slate"
        ))

    for title, msg, color, badge_cls in insights:
        st.markdown(f"""
            <div style="background:#131722; border:1px solid var(--border-subtle); border-radius:6px;
                        padding:11px 14px; margin-bottom:8px; border-left:3px solid {color};">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                    <span style="font-weight:600; color:#f8fafc; font-size:0.9rem;">{title}</span>
                    <span class="badge {badge_cls}">{title.split()[0]}</span>
                </div>
                <div style="font-size:0.84rem; color:var(--text-secondary); line-height:1.5;">{msg}</div>
            </div>
        """, unsafe_allow_html=True)

    # ── 7. NEXT ACTIONS ───────────────────────────────────────────────────────
    st.markdown("""
        <div style="margin-top:1.5rem; margin-bottom:0.75rem;">
            <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted);">Next Actions</div>
            <div style="font-size:1.05rem; font-weight:600; color:#f8fafc; margin-top:2px;">Targeted next steps to advance your progress</div>
        </div>
    """, unsafe_allow_html=True)

    act_c1, act_c2, act_c3 = st.columns(3)

    with act_c1:
        if st.button("📅 Resume Study Plan", key="pt_act_plan", type="primary", use_container_width=True):
            st.session_state.selected_nav_page = "📅 Study Planner"
            st.session_state.active_tab_redirect = "Study Planner"
            st.rerun()

    with act_c2:
        if weak_list:
            w_name = weak_list[0]["topic"]
            btn_lbl = f"📝 Practice {w_name}"
        else:
            btn_lbl = "📝 Take an Assessment"

        if st.button(btn_lbl, key="pt_act_quiz", use_container_width=True):
            st.session_state.selected_nav_page = "📝 Quiz Generator"
            st.session_state.active_tab_redirect = "Quiz Generator"
            st.rerun()

    with act_c3:
        if st.button("📈 Inspect Performance", key="pt_act_perf", use_container_width=True):
            st.session_state.selected_nav_page = "📈 Performance Analyzer"
            st.session_state.active_tab_redirect = "Performance Analyzer"
            st.rerun()


