"""
EduSync AI — Tool 2: quiz_generator
Generates topic quizzes grounded in uploaded notes or course syllabus.
Supports both Gemini LLM generation and transparent deterministic fallback.
"""

from typing import Any, Dict, List, Optional
from services.persistence import get_db
from services.llm_service import get_llm_service
from services.sample_data import DEMO_QUESTION_BANK
from tools.document_search import document_search


def generate_quiz(
    topic: str,
    difficulty: str = "medium",
    number_of_questions: int = 5,
    db_path: str = "edusync.db",
    api_key: Optional[str] = None,
    num_questions: Optional[int] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Generates a structured multiple-choice quiz on a selected topic.

    Args:
        topic: Course topic (e.g., 'Normalization', 'Indexing & Storage')
        difficulty: 'easy', 'medium', or 'hard' (default: 'medium')
        number_of_questions: Number of MCQs (between 1 and 10)
        db_path: Path to database
        api_key: Optional Gemini API key override
        num_questions: Alias for number_of_questions

    Returns:
        Dict with status, questions list, generator metadata, and grounding info.
    """
    if num_questions is not None:
        number_of_questions = num_questions

    # 1. Input Validation
    if not isinstance(topic, str) or len(topic.strip()) < 2:
        return {
            "status": "FAILED",
            "message": "Topic must be a valid string of at least 2 characters.",
            "questions": [],
        }

    cleaned_topic = topic.strip()
    valid_difficulties = ["easy", "medium", "hard"]
    norm_difficulty = difficulty.lower() if difficulty.lower() in valid_difficulties else "medium"

    try:
        num_q = max(1, min(int(number_of_questions), 10))
    except (ValueError, TypeError):
        num_q = 5

    # 2. Retrieve document grounding
    search_res = document_search(cleaned_topic, top_k=6, db_path=db_path)
    retrieved_chunks = search_res.get("chunks", [])
    has_retrieved_docs = len(retrieved_chunks) > 0

    # 3. Try Gemini LLM if available
    llm = get_llm_service(api_key=api_key)
    if llm.is_available():
        llm_questions = llm.generate_quiz_llm(
            topic=cleaned_topic,
            difficulty=norm_difficulty,
            num_questions=num_q,
            context_chunks=retrieved_chunks,
        )
        if llm_questions and len(llm_questions) >= 1:
            return {
                "status": "SUCCESS",
                "topic": cleaned_topic,
                "difficulty": norm_difficulty,
                "generator": f"Gemini AI ({llm.model_name})",
                "grounded_in_documents": has_retrieved_docs,
                "questions_count": len(llm_questions[:num_q]),
                "questions": llm_questions[:num_q],
                "message": f"Generated {len(llm_questions[:num_q])} questions using Gemini AI grounded in course content.",
            }

    # 4. Transparent Deterministic Fallback
    # First: Check demo bank matching the topic
    fallback_questions: List[Dict[str, Any]] = []

    # Filter demo bank by topic keyword match
    for item in DEMO_QUESTION_BANK:
        item_topic = item["topic"].lower()
        if (
            cleaned_topic.lower() in item_topic
            or item_topic in cleaned_topic.lower()
            or any(w in item_topic for w in cleaned_topic.lower().split() if len(w) > 3)
        ):
            q_copy = dict(item)
            fallback_questions.append(q_copy)

    # If demo bank has insufficient questions, also include general academic questions from bank
    if len(fallback_questions) < num_q:
        for item in DEMO_QUESTION_BANK:
            if item not in fallback_questions:
                fallback_questions.append(dict(item))
            if len(fallback_questions) >= num_q:
                break

    # If document chunks were retrieved, augment source attribution
    source_label = (
        f"Grounded in uploaded: {retrieved_chunks[0]['source']} (p.{retrieved_chunks[0]['page_number']})"
        if has_retrieved_docs
        else "Syllabus Knowledge Base (Demo Mode)"
    )

    final_questions = fallback_questions[:num_q]
    for idx, q in enumerate(final_questions):
        q["id"] = idx + 1
        if has_retrieved_docs and not q.get("source"):
            q["source"] = source_label

    return {
        "status": "SUCCESS",
        "topic": cleaned_topic,
        "difficulty": norm_difficulty,
        "generator": "Deterministic Fallback Engine (Demo Mode)",
        "grounded_in_documents": has_retrieved_docs,
        "questions_count": len(final_questions),
        "questions": final_questions,
        "message": (
            f"Generated {len(final_questions)} question(s) using the deterministic engine. "
            + ("Grounded in retrieved course notes." if has_retrieved_docs else "Using standard curriculum questions.")
        ),
    }


def score_quiz(
    questions: List[Dict[str, Any]],
    user_answers: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Evaluates student answers against correct answers.

    Args:
        questions: List of question dicts
        user_answers: Dict mapping question id (str or int) to chosen option string

    Returns:
        Scoring result with breakdown, score, total, and percentage.
    """
    if not questions:
        return {
            "score": 0,
            "total": 0,
            "percentage": 0.0,
            "details": [],
        }

    total = len(questions)
    score = 0
    details = []

    for q in questions:
        qid_str = str(q.get("id", ""))
        raw_chosen = user_answers.get(qid_str)
        chosen = str(raw_chosen).strip() if raw_chosen is not None else ""
        correct = str(q.get("correct_answer", "")).strip()

        chosen_clean = chosen
        correct_clean = correct

        # Extract leading option letter if present (e.g. 'A' from 'A) ...' or 'A. ...' or 'A')
        chosen_letter = chosen_clean[0].upper() if chosen_clean else ""
        correct_letter = correct_clean[0].upper() if correct_clean else ""

        is_correct = (
            chosen_clean.lower() == correct_clean.lower()
            or (len(chosen_clean) == 1 and chosen_letter == correct_letter)
            or (len(chosen_clean) >= 2 and correct_clean.startswith(chosen_clean[:2]))
            or (len(correct_clean) >= 2 and chosen_clean.startswith(correct_clean[:2]))
        )

        if is_correct:
            score += 1

        details.append({
            "id": q["id"],
            "question": q["question"],
            "user_answer": chosen if chosen else "Unanswered",
            "correct_answer": correct,
            "is_correct": is_correct,
            "explanation": q.get("explanation", ""),
            "source": q.get("source", ""),
        })

    percentage = round((score / total) * 100.0, 1) if total > 0 else 0.0

    return {
        "score": score,
        "total": total,
        "percentage": percentage,
        "details": details,
    }


def record_quiz_submission(
    topic: Any = None,
    difficulty: Optional[str] = None,
    questions: Optional[List[Dict[str, Any]]] = None,
    user_answers: Optional[Dict[str, Any]] = None,
    db_path: str = "edusync.db",
    **kwargs,
) -> Dict[str, Any]:
    """
    Scores and persists a quiz attempt to SQLite.
    Supports both signatures:
      - record_quiz_submission(topic, difficulty, questions, user_answers, db_path)
      - record_quiz_submission(quiz_dict, user_answers, db_path)
    """
    if isinstance(topic, dict):
        quiz_dict = topic
        actual_answers = difficulty if isinstance(difficulty, dict) else (user_answers or {})
        actual_db_path = questions if isinstance(questions, str) else db_path
        actual_topic = quiz_dict.get("topic", "General")
        actual_diff = quiz_dict.get("difficulty", "medium")
        actual_questions = quiz_dict.get("questions", [])
    else:
        actual_topic = topic or "General"
        actual_diff = difficulty or "medium"
        actual_questions = questions or []
        actual_answers = user_answers or {}
        actual_db_path = db_path

    scoring = score_quiz(actual_questions, actual_answers)
    db = get_db(actual_db_path)
    attempt_id = db.save_quiz_attempt(
        topic=actual_topic,
        difficulty=actual_diff,
        score=scoring["score"],
        total_questions=scoring["total"],
        questions=actual_questions,
        user_answers=actual_answers,
    )
    scoring["attempt_id"] = attempt_id
    scoring["topic"] = actual_topic
    scoring["total_questions"] = scoring["total"]
    scoring["graded_questions"] = scoring["details"]
    return scoring
