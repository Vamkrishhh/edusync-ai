"""
EduSync AI — Tool 3: performance
Calculates topic-level performance and classifies learning gaps using transparent thresholds.
"""

from typing import Any, Dict, List, Optional
from services.persistence import get_db

# Default configurable thresholds
DEFAULT_STRONG_THRESHOLD = 80.0
DEFAULT_DEVELOPING_THRESHOLD = 60.0

PERFORMANCE_DISCLAIMER = (
    "ASSESSMENT NOTICE: These classifications are based solely on recorded quiz attempts "
    "within EduSync AI. They provide directional guidance and do not represent a comprehensive "
    "measure of overall student capability."
)


def classify_score(
    percentage: float,
    strong_thresh: float = DEFAULT_STRONG_THRESHOLD,
    developing_thresh: float = DEFAULT_DEVELOPING_THRESHOLD,
) -> str:
    """Classifies a percentage score into Strong, Developing, or Needs Attention."""
    if percentage >= strong_thresh:
        return "Strong"
    elif percentage >= developing_thresh:
        return "Developing"
    else:
        return "Needs Attention"


def analyze_performance(
    results: Optional[List[Dict[str, Any]]] = None,
    strong_thresh: float = DEFAULT_STRONG_THRESHOLD,
    developing_thresh: float = DEFAULT_DEVELOPING_THRESHOLD,
    db_path: str = "edusync.db",
    include_sample: bool = False,
) -> Dict[str, Any]:
    """
    Analyzes student quiz results by topic and identifies learning gaps.

    Args:
        results: Optional list of quiz attempt dicts. If None, queries DB.
        strong_thresh: Percentage cutoff for Strong (default: 80.0%)
        developing_thresh: Percentage cutoff for Developing (default: 60.0%)
        db_path: Path to database
        include_sample: If True, include demo/sample attempts in analysis (default: False)

    Returns:
        Structured performance analysis dictionary.
    """
    db = get_db(db_path)
    # Use only real (non-sample) attempts unless caller explicitly passes results or requests sample data
    attempts = results if results is not None else db.get_quiz_attempts(real_only=not include_sample)

    # Handle empty/missing data state
    if not attempts:
        return {
            "status": "SUCCESS",
            "has_data": False,
            "total_attempts": 0,
            "overall_score": 0.0,
            "topic_breakdown": {},
            "strong_topics": [],
            "developing_topics": [],
            "weak_topics": [],
            "recommendations": [
                "No previous quiz attempts recorded. Take a quick diagnostic quiz on any topic in the Quiz Generator to calibrate your preparation."
            ],
            "disclaimer": PERFORMANCE_DISCLAIMER,
            "thresholds": {
                "strong": f">={strong_thresh}%",
                "developing": f"{developing_thresh}%–{strong_thresh - 0.1}%",
                "needs_attention": f"<{developing_thresh}%",
            },
            "message": "No recorded quiz attempts found. Using student confidence or diagnostic baseline.",
        }

    # Aggregate by topic
    topic_map: Dict[str, Dict[str, Any]] = {}
    total_score = 0
    total_possible = 0

    for att in attempts:
        t = att.get("topic", "General").strip()
        score = att.get("score", 0)
        num_q = att.get("total_questions", 0)

        if t not in topic_map:
            topic_map[t] = {
                "topic": t,
                "score": 0,
                "total_questions": 0,
                "attempts_count": 0,
                "scores_list": [],
            }

        topic_map[t]["score"] += score
        topic_map[t]["total_questions"] += num_q
        topic_map[t]["attempts_count"] += 1
        topic_map[t]["scores_list"].append(att.get("percentage", 0.0))

        total_score += score
        total_possible += num_q

    overall_pct = (
        round((total_score / total_possible) * 100.0, 1) if total_possible > 0 else 0.0
    )

    strong_topics: List[Dict[str, Any]] = []
    developing_topics: List[Dict[str, Any]] = []
    weak_topics: List[Dict[str, Any]] = []

    topic_breakdown: Dict[str, Any] = {}

    for t, d in topic_map.items():
        pct = (
            round((d["score"] / d["total_questions"]) * 100.0, 1)
            if d["total_questions"] > 0
            else 0.0
        )
        classification = classify_score(pct, strong_thresh, developing_thresh)

        rationale = (
            f"Achieved {pct}% ({d['score']}/{d['total_questions']} across {d['attempts_count']} attempt(s)). "
            f"Categorized as '{classification}' based on threshold criteria (Strong >= {strong_thresh}%, "
            f"Developing >= {developing_thresh}%, Needs Attention < {developing_thresh}%)."
        )

        entry = {
            "topic": t,
            "percentage": pct,
            "score": d["score"],
            "total_questions": d["total_questions"],
            "attempts": d["attempts_count"],
            "classification": classification,
            "rationale": rationale,
        }

        topic_breakdown[t] = entry

        if classification == "Strong":
            strong_topics.append(entry)
        elif classification == "Developing":
            developing_topics.append(entry)
        else:
            weak_topics.append(entry)

    # Generate specific, actionable recommendations
    recommendations = []
    if weak_topics:
        weak_names = ", ".join([f"'{w['topic']}'" for w in weak_topics])
        recommendations.append(
            f"Prioritize immediate concept review and practice for weak topics: {weak_names}."
        )
    if developing_topics:
        dev_names = ", ".join([f"'{d['topic']}'" for d in developing_topics])
        recommendations.append(
            f"Schedule reinforcement drills and targeted MCQs for developing topics: {dev_names}."
        )
    if strong_topics:
        strong_names = ", ".join([f"'{s['topic']}'" for s in strong_topics])
        recommendations.append(
            f"Maintain mastery in strong areas ({strong_names}) through brief spaced revision sessions."
        )
    if not weak_topics and not developing_topics:
        recommendations.append(
            "Excellent performance across evaluated topics! Focus on full-length mock exams and edge cases."
        )

    return {
        "status": "SUCCESS",
        "has_data": True,
        "total_attempts": len(attempts),
        "overall_score": overall_pct,
        "topic_breakdown": topic_breakdown,
        "strong_topics": strong_topics,
        "developing_topics": developing_topics,
        "weak_topics": weak_topics,
        "recommendations": recommendations,
        "disclaimer": PERFORMANCE_DISCLAIMER,
        "thresholds": {
            "strong": f">={strong_thresh}%",
            "developing": f"{developing_thresh}%–{strong_thresh - 0.1}%",
            "needs_attention": f"<{developing_thresh}%",
        },
        "message": f"Evaluated {len(attempts)} quiz attempts across {len(topic_breakdown)} topic(s).",
    }
