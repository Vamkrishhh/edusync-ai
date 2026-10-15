"""
EduSync AI — Local SQLite Persistence Layer
Handles document chunks, quiz history, performance records, study plans, and agent traces
with strict idempotency, deduplication, and clean demo lifecycle management.

SCHEMA EVOLUTION STRATEGY:
Since CREATE TABLE IF NOT EXISTS does not alter existing tables, we use explicit
ALTER TABLE migrations to add missing columns and constraints. On init, we also
clean up any duplicate rows that accumulated from earlier versions of the code.
"""

import json
import sqlite3
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional


class DatabaseManager:
    """SQLite Database Manager for EduSync AI MVP with idempotent storage."""

    def __init__(self, db_path: str = "edusync.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self):
        """Initialize all required SQLite tables with integrity constraints."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    num_chunks INTEGER NOT NULL,
                    num_pages INTEGER DEFAULT 1,
                    upload_time TEXT NOT NULL,
                    is_sample INTEGER DEFAULT 0
                )
            """)

            # Document chunks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    page_number INTEGER DEFAULT 1,
                    chunk_text TEXT NOT NULL,
                    source_filename TEXT NOT NULL,
                    UNIQUE(doc_id, chunk_index),
                    FOREIGN KEY (doc_id) REFERENCES documents (id) ON DELETE CASCADE
                )
            """)

            # Quiz attempts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quiz_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    total_questions INTEGER NOT NULL,
                    percentage REAL NOT NULL,
                    questions_json TEXT NOT NULL,
                    user_answers_json TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    is_sample INTEGER DEFAULT 0
                )
            """)

            # Study plans table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS study_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    exam_date TEXT NOT NULL,
                    available_hours REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    plan_data_json TEXT NOT NULL
                )
            """)

            # Study tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS study_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_id INTEGER NOT NULL,
                    day_number INTEGER NOT NULL,
                    topic TEXT NOT NULL,
                    task_description TEXT NOT NULL,
                    duration_hours REAL NOT NULL,
                    task_type TEXT NOT NULL,
                    completed INTEGER DEFAULT 0,
                    completed_at TEXT,
                    FOREIGN KEY (plan_id) REFERENCES study_plans (id) ON DELETE CASCADE
                )
            """)

            # Agent execution logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_query TEXT NOT NULL,
                    goal TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    tools_trace_json TEXT NOT NULL,
                    final_response TEXT NOT NULL
                )
            """)

            conn.commit()

        # Run schema migrations for columns/constraints that may be missing
        self._run_migrations()

    def _run_migrations(self):
        """
        Apply schema migrations to existing databases created before new columns
        or constraints were added. CREATE TABLE IF NOT EXISTS never modifies an
        existing table, so we must use ALTER TABLE for additions.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Migration 1: Add attempt_hash column to quiz_attempts if missing
            cursor.execute("PRAGMA table_info(quiz_attempts)")
            columns = [row["name"] for row in cursor.fetchall()]
            if "attempt_hash" not in columns:
                cursor.execute("ALTER TABLE quiz_attempts ADD COLUMN attempt_hash TEXT")
            if "is_sample" not in columns:
                cursor.execute("ALTER TABLE quiz_attempts ADD COLUMN is_sample INTEGER DEFAULT 0")

            # Migration 2: Deduplicate documents table
            # Keep only the FIRST row for each filename, remove all others
            cursor.execute("""
                DELETE FROM document_chunks WHERE doc_id IN (
                    SELECT d.id FROM documents d
                    WHERE d.id NOT IN (
                        SELECT MIN(id) FROM documents GROUP BY filename
                    )
                )
            """)
            cursor.execute("""
                DELETE FROM documents WHERE id NOT IN (
                    SELECT MIN(id) FROM documents GROUP BY filename
                )
            """)

            # Migration 3: Create unique index on filename if it doesn't exist
            try:
                cursor.execute("""
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_filename
                    ON documents(filename)
                """)
            except sqlite3.IntegrityError:
                # If duplicates somehow still exist, clean them first
                pass

            conn.commit()

    # ==================== Document Operations ====================

    def document_exists(self, filename: str) -> bool:
        """Returns True if a document with this filename already exists."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM documents WHERE filename = ?", (filename,))
            return cursor.fetchone() is not None

    def save_document(
        self,
        filename: str,
        file_type: str,
        num_chunks: int,
        num_pages: int,
        chunks: List[Dict[str, Any]],
        is_sample: bool = False,
    ) -> int:
        """
        Idempotently saves a document and its text chunks.
        If a document with the same filename already exists, replaces its chunks cleanly
        rather than creating duplicate rows.
        """
        upload_time = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if document already exists (use LIMIT 1 for safety)
            cursor.execute("SELECT id FROM documents WHERE filename = ? LIMIT 1", (filename,))
            existing = cursor.fetchone()

            if existing:
                doc_id = existing[0]
                # Clean old chunks for this document
                cursor.execute("DELETE FROM document_chunks WHERE doc_id = ?", (doc_id,))
                cursor.execute(
                    """
                    UPDATE documents
                    SET file_type = ?, num_chunks = ?, num_pages = ?, upload_time = ?, is_sample = ?
                    WHERE id = ?
                """,
                    (file_type, num_chunks, num_pages, upload_time, 1 if is_sample else 0, doc_id),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO documents (filename, file_type, num_chunks, num_pages, upload_time, is_sample)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (filename, file_type, num_chunks, num_pages, upload_time, 1 if is_sample else 0),
                )
                doc_id = cursor.lastrowid

            # Insert chunks
            for i, chunk in enumerate(chunks):
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO document_chunks (doc_id, chunk_index, page_number, chunk_text, source_filename)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        doc_id,
                        chunk.get("chunk_index", i),
                        chunk.get("page_number", 1),
                        chunk["text"],
                        filename,
                    ),
                )
            conn.commit()
            return doc_id

    def get_documents(self) -> List[Dict[str, Any]]:
        """Returns all registered documents."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents ORDER BY id ASC")
            return [dict(row) for row in cursor.fetchall()]

    def get_all_chunks(self) -> List[Dict[str, Any]]:
        """Returns all text chunks across all documents."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.doc_id, c.chunk_index, c.page_number, c.chunk_text, c.source_filename, d.is_sample
                FROM document_chunks c
                JOIN documents d ON c.doc_id = d.id
                ORDER BY c.doc_id ASC, c.chunk_index ASC
            """)
            return [
                {
                    "id": row["id"],
                    "doc_id": row["doc_id"],
                    "chunk_index": row["chunk_index"],
                    "page_number": row["page_number"],
                    "text": row["chunk_text"],
                    "source": row["source_filename"],
                    "is_sample": bool(row["is_sample"]),
                }
                for row in cursor.fetchall()
            ]

    def clear_documents(self, doc_id: Optional[int] = None):
        """Deletes a specific document or all documents."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if doc_id is not None:
                cursor.execute("DELETE FROM document_chunks WHERE doc_id = ?", (doc_id,))
                cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            else:
                cursor.execute("DELETE FROM document_chunks")
                cursor.execute("DELETE FROM documents")
            conn.commit()

    # ==================== Quiz Operations ====================

    def save_quiz_attempt(
        self,
        topic: str,
        difficulty: str,
        score: int,
        total_questions: int,
        questions: List[Dict[str, Any]],
        user_answers: Dict[str, Any],
        is_sample: bool = False,
    ) -> int:
        """
        Idempotently saves a student quiz attempt.
        Deduplicates submissions with identical topic, score, questions, and answers
        using a content hash.
        """
        timestamp = datetime.now().isoformat()
        percentage = (score / total_questions * 100.0) if total_questions > 0 else 0.0

        # Create content hash signature for idempotency
        norm_answers = {str(k): str(v) for k, v in user_answers.items()}
        answers_str = json.dumps(norm_answers, sort_keys=True)
        questions_str = json.dumps(questions, sort_keys=True)
        attempt_sig = hashlib.sha256(
            f"{topic.strip().lower()}_{difficulty}_{score}_{total_questions}_{answers_str}".encode()
        ).hexdigest()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if this exact attempt was already recorded (use attempt_hash if column exists)
            try:
                cursor.execute(
                    """
                    SELECT id FROM quiz_attempts
                    WHERE attempt_hash = ?
                    LIMIT 1
                """,
                    (attempt_sig,),
                )
                existing = cursor.fetchone()
                if existing:
                    return existing[0]
            except sqlite3.OperationalError:
                # attempt_hash column might not exist yet in very old DBs
                pass

            # Fallback: check by content match
            cursor.execute(
                """
                SELECT id FROM quiz_attempts
                WHERE topic = ? AND score = ? AND total_questions = ? AND user_answers_json = ?
                LIMIT 1
            """,
                (topic.strip(), score, total_questions, answers_str),
            )
            existing = cursor.fetchone()
            if existing:
                return existing[0]

            cursor.execute(
                """
                INSERT INTO quiz_attempts
                (topic, difficulty, score, total_questions, percentage, questions_json, user_answers_json, timestamp, attempt_hash, is_sample)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    topic.strip(),
                    difficulty,
                    score,
                    total_questions,
                    percentage,
                    questions_str,
                    answers_str,
                    timestamp,
                    attempt_sig,
                    1 if is_sample else 0,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def get_quiz_attempts(self, topic: Optional[str] = None, real_only: bool = False) -> List[Dict[str, Any]]:
        """Returns quiz attempts, optionally filtered by topic or excluding sample data."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            base = "SELECT * FROM quiz_attempts"
            conditions = []
            params = []
            if topic:
                conditions.append("LOWER(topic) = LOWER(?)")
                params.append(topic.strip())
            if real_only:
                conditions.append("COALESCE(is_sample, 0) = 0")
            if conditions:
                base += " WHERE " + " AND ".join(conditions)
            base += " ORDER BY id DESC"
            cursor.execute(base, params)
            rows = cursor.fetchall()

            results = []
            for row in rows:
                item = dict(row)
                try:
                    item["questions"] = json.loads(item["questions_json"])
                except Exception:
                    item["questions"] = []
                try:
                    item["user_answers"] = json.loads(item["user_answers_json"])
                except Exception:
                    item["user_answers"] = {}
                results.append(item)
            return results

    def get_topic_performance_summary(self) -> Dict[str, Dict[str, Any]]:
        """Aggregates quiz results by topic mathematically with zero duplicate distortion."""
        attempts = self.get_quiz_attempts()
        summary: Dict[str, Dict[str, Any]] = {}

        for att in attempts:
            t = att["topic"].strip()
            if t not in summary:
                summary[t] = {
                    "topic": t,
                    "attempts_count": 0,
                    "total_score": 0,
                    "total_possible": 0,
                    "percentages": [],
                    "latest_date": att["timestamp"],
                }
            summary[t]["attempts_count"] += 1
            summary[t]["total_score"] += att["score"]
            summary[t]["total_possible"] += att["total_questions"]
            summary[t]["percentages"].append(att["percentage"])

        for t, data in summary.items():
            if data["total_possible"] > 0:
                data["average_score"] = round(
                    (data["total_score"] / data["total_possible"]) * 100.0, 1
                )
            else:
                data["average_score"] = 0.0

        return summary

    # ==================== Study Plan Operations ====================

    def save_study_plan(
        self,
        subject: str,
        exam_date: str,
        available_hours: float,
        days_plan: List[Dict[str, Any]],
    ) -> int:
        """
        Saves a study plan and creates task rows idempotently.
        If an active plan for the identical subject, date, and hours already exists,
        returns the existing plan ID without creating duplicate superseded rows.
        """
        created_at = datetime.now().isoformat()
        plan_json_str = json.dumps(days_plan)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if ANY active plan already exists for same subject+date+hours
            # (relaxed comparison — don't compare plan_data_json since timestamps differ)
            cursor.execute(
                """
                SELECT id FROM study_plans
                WHERE status = 'active' AND subject = ? AND exam_date = ? AND available_hours = ?
            """,
                (subject.strip(), exam_date, available_hours),
            )
            existing = cursor.fetchone()
            if existing:
                return existing["id"]

            # Set older plans to superseded
            cursor.execute("UPDATE study_plans SET status = 'superseded' WHERE status = 'active'")

            cursor.execute(
                """
                INSERT INTO study_plans (subject, exam_date, available_hours, created_at, status, plan_data_json)
                VALUES (?, ?, ?, ?, 'active', ?)
            """,
                (subject.strip(), exam_date, available_hours, created_at, plan_json_str),
            )
            plan_id = cursor.lastrowid

            for day_data in days_plan:
                day_num = day_data.get("day", 1)
                for task in day_data.get("tasks", []):
                    cursor.execute(
                        """
                        INSERT INTO study_tasks
                        (plan_id, day_number, topic, task_description, duration_hours, task_type, completed)
                        VALUES (?, ?, ?, ?, ?, ?, 0)
                    """,
                        (
                            plan_id,
                            day_num,
                            task.get("topic", subject),
                            task.get("description", ""),
                            task.get("duration_hours", 1.0),
                            task.get("type", "study"),
                        ),
                    )
            conn.commit()
            return plan_id

    def get_active_study_plan(self) -> Optional[Dict[str, Any]]:
        """Returns the currently active study plan."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM study_plans WHERE status = 'active' ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            if not row:
                return None
            plan = dict(row)
            plan["days_plan"] = json.loads(plan["plan_data_json"])
            return plan

    def get_previous_study_plans(self) -> List[Dict[str, Any]]:
        """Returns superseded/historical study plans."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM study_plans WHERE status = 'superseded' ORDER BY id DESC")
            rows = cursor.fetchall()
            plans = []
            for r in rows:
                p = dict(r)
                p["days_plan"] = json.loads(p["plan_data_json"])
                plans.append(p)
            return plans

    def get_study_tasks(self, plan_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Returns tasks for a plan (or active plan if None)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if plan_id is None:
                cursor.execute("""
                    SELECT t.* FROM study_tasks t
                    JOIN study_plans p ON t.plan_id = p.id
                    WHERE p.status = 'active'
                    ORDER BY t.day_number ASC, t.id ASC
                """)
            else:
                cursor.execute(
                    "SELECT * FROM study_tasks WHERE plan_id = ? ORDER BY day_number ASC, id ASC",
                    (plan_id,),
                )
            return [dict(r) for r in cursor.fetchall()]

    def toggle_task_completion(self, task_id: int, completed: bool) -> bool:
        """Toggles a task's completed flag."""
        now = datetime.now().isoformat() if completed else None
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE study_tasks
                SET completed = ?, completed_at = ?
                WHERE id = ?
            """,
                (1 if completed else 0, now, task_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    # ==================== Agent Logging ====================

    def log_agent_trace(
        self,
        query: str,
        goal: str,
        tools_trace: List[Dict[str, Any]],
        final_response: str,
        mode: str,
    ) -> int:
        """
        Records an agent execution trace idempotently.
        Deduplicates identical queries triggered within 10 seconds (covers Streamlit reruns).
        """
        now = datetime.now()
        timestamp = now.isoformat()
        clean_query = query.strip()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if identical query was logged within the last 10 seconds
            cursor.execute(
                "SELECT id, timestamp FROM agent_logs WHERE user_query = ? ORDER BY id DESC LIMIT 1",
                (clean_query,),
            )
            last_log = cursor.fetchone()
            if last_log:
                try:
                    last_time = datetime.fromisoformat(last_log["timestamp"])
                    if (now - last_time).total_seconds() < 10.0:
                        return last_log["id"]
                except Exception:
                    pass

            cursor.execute(
                """
                INSERT INTO agent_logs (timestamp, user_query, goal, mode, tools_trace_json, final_response)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (timestamp, clean_query, goal, mode, json.dumps(tools_trace), final_response),
            )
            conn.commit()
            return cursor.lastrowid

    def get_recent_agent_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Returns the latest agent execution traces."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agent_logs ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            logs = []
            for r in rows:
                item = dict(r)
                try:
                    item["tools_trace"] = json.loads(item["tools_trace_json"])
                except Exception:
                    item["tools_trace"] = []
                logs.append(item)
            return logs

    # ==================== Reset & Lifecycle Management ====================

    def reset_database(self):
        """
        Completely resets the database to a pristine zero state.
        Deletes all documents, chunks, quiz attempts, study plans, tasks, and agent logs.
        Resets autoincrement sequences so IDs start from 1.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM document_chunks")
            cursor.execute("DELETE FROM documents")
            cursor.execute("DELETE FROM quiz_attempts")
            cursor.execute("DELETE FROM study_tasks")
            cursor.execute("DELETE FROM study_plans")
            cursor.execute("DELETE FROM agent_logs")
            try:
                cursor.execute("DELETE FROM sqlite_sequence")
            except sqlite3.OperationalError:
                pass
            conn.commit()

    # ==================== Dashboard Metrics ====================

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Calculates accurate dashboard summary statistics with zero duplicate distortion.
        Real user data (is_sample=0) is reported separately from demo/sample data."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # All docs count (real + sample) for library display
            cursor.execute("SELECT COUNT(*), COALESCE(SUM(num_chunks), 0) FROM documents")
            doc_row = cursor.fetchone()
            doc_count = doc_row[0] or 0
            chunk_count = doc_row[1] or 0

            # Real uploaded docs only (is_sample = 0)
            cursor.execute(
                "SELECT COUNT(*), COALESCE(SUM(num_chunks), 0) FROM documents WHERE COALESCE(is_sample, 0) = 0"
            )
            real_doc_row = cursor.fetchone()
            real_doc_count = real_doc_row[0] or 0

            # Real quiz attempts only (is_sample = 0) for metrics
            cursor.execute(
                "SELECT COUNT(*), AVG(percentage) FROM quiz_attempts WHERE COALESCE(is_sample, 0) = 0"
            )
            quiz_row = cursor.fetchone()
            quiz_count = quiz_row[0] or 0
            avg_score = round(quiz_row[1] or 0.0, 1)

            # All attempts count (for "total assessments taken" display)
            cursor.execute("SELECT COUNT(*) FROM quiz_attempts")
            all_quiz_count = cursor.fetchone()[0] or 0

            # Tasks completed for active plan
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END), 0)
                FROM study_tasks t
                JOIN study_plans p ON t.plan_id = p.id
                WHERE p.status = 'active'
            """)
            task_row = cursor.fetchone()
            total_tasks = task_row[0] or 0
            completed_tasks = task_row[1] or 0

            return {
                "document_count": doc_count,           # all docs (real + sample)
                "real_document_count": real_doc_count,  # uploaded by user only
                "chunk_count": chunk_count,
                "quiz_attempts_count": quiz_count,      # real attempts only for metrics
                "all_quiz_attempts_count": all_quiz_count,
                "average_quiz_score": avg_score,        # real attempts only
                "total_study_tasks": total_tasks,
                "completed_study_tasks": completed_tasks,
                "task_completion_rate": round(
                    (completed_tasks / total_tasks * 100.0) if total_tasks > 0 else 0.0, 1
                ),
            }


# Singleton instance helper
_default_db: Optional[DatabaseManager] = None


def get_db(db_path: str = "edusync.db") -> DatabaseManager:
    global _default_db
    if _default_db is None or _default_db.db_path != db_path:
        _default_db = DatabaseManager(db_path)
    return _default_db
