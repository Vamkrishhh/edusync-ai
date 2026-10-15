import pytest
import sqlite3
import json
from datetime import datetime, date, timedelta
from services.persistence import DatabaseManager
from services.sample_data import populate_sample_dbms_data, populate_sample_quiz_history
from agent.orchestrator import MultiToolOrchestrator

@pytest.fixture
def fresh_db(tmp_path):
    db_path = str(tmp_path / "test_regression.db")
    db = DatabaseManager(db_path)
    # Ensure zero state
    db.reset_database()
    return db, db_path

def test_1_2_3_sample_data_idempotency(fresh_db):
    db, _ = fresh_db
    
    # Run first time
    added = populate_sample_dbms_data(db, force=False)
    assert added is True
    
    docs = db.get_documents()
    assert len(docs) == 2
    
    chunks = db.get_all_chunks()
    assert len(chunks) == 6
    
    # Run second time with force=False
    added2 = populate_sample_dbms_data(db, force=False)
    assert added2 is False
    
    # Run third time with force=True (simulates old behavior)
    added3 = populate_sample_dbms_data(db, force=True)
    assert added3 is True # True means it processed it, but DB should still deduplicate
    
    docs = db.get_documents()
    assert len(docs) == 2, "Duplicate documents created despite unique constraint!"
    
    chunks = db.get_all_chunks()
    assert len(chunks) == 6, "Duplicate chunks created!"

def test_6_quiz_double_submission(fresh_db):
    db, _ = fresh_db
    
    added = populate_sample_quiz_history(db, force=False)
    assert added is True
    
    attempts = db.get_quiz_attempts()
    assert len(attempts) == 2
    
    added2 = populate_sample_quiz_history(db, force=False)
    assert added2 is False
    
    # Manually try to double submit identical quiz attempt
    q_data = [{"q": "1"}, {"q": "2"}]
    u_ans = {"1": "A"}
    
    id1 = db.save_quiz_attempt("Test Topic", "easy", 1, 2, q_data, u_ans)
    id2 = db.save_quiz_attempt("Test Topic", "easy", 1, 2, q_data, u_ans)
    
    assert id1 == id2, "Quiz attempt was not deduplicated!"
    
    attempts = db.get_quiz_attempts()
    assert len(attempts) == 3

def test_7_repeated_plan_generation(fresh_db):
    db, _ = fresh_db
    
    plan_data = [{"day": 1, "tasks": [{"topic": "Test"}]}]
    id1 = db.save_study_plan("Subject A", "2026-12-01", 3.0, plan_data)
    
    # Generate same plan again
    id2 = db.save_study_plan("Subject A", "2026-12-01", 3.0, plan_data)
    
    assert id1 == id2, "Study plan was silently duplicated instead of returned existing!"
    
    plans = db.get_previous_study_plans()
    assert len(plans) == 0 # no superseded plans
    
    active = db.get_active_study_plan()
    assert active is not None
    assert active["id"] == id1

def test_4_5_duplicate_agent_run(fresh_db):
    db, db_path = fresh_db
    orchestrator = MultiToolOrchestrator(db_path=db_path, api_key=None)
    
    # Run once
    result1 = orchestrator.run("What should I study today?")
    
    # The agent log should have 1 entry
    logs = db.get_recent_agent_logs()
    assert len(logs) == 1
    
    # Immediately run again (simulates rapid Streamlit rerun)
    result2 = orchestrator.run("What should I study today?")
    
    logs2 = db.get_recent_agent_logs()
    assert len(logs2) == 1, "Agent execution was duplicated despite 10s dedup window!"

def test_8_reset_database_correctness(fresh_db):
    db, _ = fresh_db
    
    populate_sample_dbms_data(db, force=False)
    populate_sample_quiz_history(db, force=False)
    db.log_agent_trace("Test", "Goal", [], "Final", "Demo")
    
    db.reset_database()
    
    assert len(db.get_documents()) == 0
    assert len(db.get_all_chunks()) == 0
    assert len(db.get_quiz_attempts()) == 0
    assert len(db.get_recent_agent_logs()) == 0
    assert db.get_active_study_plan() is None
