"""
EduSync AI — Tool 1: document_search
Retrieves relevant passages and source metadata from uploaded course materials using TF-IDF.
"""

from typing import Any, Dict, List, Optional
from services.persistence import get_db
from services.document_processor import TFIDFSearchEngine


def document_search(
    query: str,
    top_k: int = 5,
    db_path: str = "edusync.db",
    min_score: float = 0.04,
) -> Dict[str, Any]:
    """
    Retrieves the most relevant passages from uploaded documents for a student query.

    Args:
        query: Natural language search query or topic keyword
        top_k: Maximum number of chunks to return (default: 5)
        db_path: Path to SQLite database
        min_score: Minimum cosine similarity threshold (default: 0.04)

    Returns:
        Structured result dictionary with status, chunks, and source metadata.
    """
    # 1. Input Validation
    if not isinstance(query, str) or not query.strip():
        return {
            "status": "FAILED",
            "query": query,
            "count": 0,
            "found": False,
            "chunks": [],
            "message": "Query must be a non-empty string.",
        }

    cleaned_query = query.strip()
    db = get_db(db_path)
    chunks = db.get_all_chunks()

    # 2. Check if documents exist
    if not chunks:
        return {
            "status": "SUCCESS",
            "query": cleaned_query,
            "count": 0,
            "found": False,
            "chunks": [],
            "message": (
                "No documents found in the library. Please upload lecture notes or syllabus "
                "PDFs in the Document Library section or load the sample DBMS dataset."
            ),
        }

    # 3. TF-IDF Retrieval
    search_engine = TFIDFSearchEngine(chunks)
    matched_chunks = search_engine.search(cleaned_query, top_k=top_k, min_score=min_score)

    if not matched_chunks:
        return {
            "status": "SUCCESS",
            "query": cleaned_query,
            "count": 0,
            "found": False,
            "chunks": [],
            "message": (
                f"No relevant passages found matching '{cleaned_query}'. "
                "Try using related academic terms or verify that the topic is covered in your uploaded files."
            ),
        }

    # 4. Format outputs with source attribution
    formatted_chunks = []
    for c in matched_chunks:
        formatted_chunks.append({
            "chunk_id": c.get("id"),
            "source": c.get("source", "Uploaded Document"),
            "page_number": c.get("page_number", 1),
            "similarity_score": c.get("similarity_score", 0.0),
            "text": c.get("text", "").strip(),
            "is_sample": c.get("is_sample", False),
        })

    return {
        "status": "SUCCESS",
        "query": cleaned_query,
        "count": len(formatted_chunks),
        "found": True,
        "chunks": formatted_chunks,
        "message": f"Successfully retrieved {len(formatted_chunks)} relevant passage(s) from course materials.",
    }
