"""
Tests for document processing, chunking, and TF-IDF search.
"""

import os
import pytest
from services.document_processor import chunk_document_pages, TFIDFSearchEngine
from services.persistence import DatabaseManager
from tools.document_search import document_search


def test_chunking_preserves_metadata():
    pages = [
        {"page_number": 1, "text": "This is page 1 content. " * 30},
        {"page_number": 2, "text": "This is page 2 content. " * 30},
    ]
    chunks = chunk_document_pages(pages, "lecture_1.pdf", chunk_size=200, chunk_overlap=50)

    assert len(chunks) > 2
    # Verify metadata on all chunks
    for c in chunks:
        assert c["source"] == "lecture_1.pdf"
        assert c["page_number"] in [1, 2]
        assert "chunk_index" in c
        assert len(c["text"]) > 0


def test_tfidf_retrieval(tmp_path):
    chunks = [
        {"id": 1, "text": "Normalization eliminates database redundancy and partial functional dependencies in 2NF.", "page_number": 1, "source": "dbms.pdf", "is_sample": False},
        {"id": 2, "text": "B+ Tree indexes store keys in balanced leaf nodes linked for range query scans.", "page_number": 2, "source": "dbms.pdf", "is_sample": False},
        {"id": 3, "text": "Transactions follow ACID rules where Atomicity ensures all or nothing commits.", "page_number": 3, "source": "dbms.pdf", "is_sample": False},
    ]

    engine = TFIDFSearchEngine(chunks)

    # Search for normalization
    norm_results = engine.search("functional dependencies 2NF", top_k=2)
    assert len(norm_results) > 0
    assert "Normalization" in norm_results[0]["text"]
    assert norm_results[0]["similarity_score"] > 0.05

    # Search for trees
    tree_results = engine.search("B+ Tree index range scan", top_k=1)
    assert len(tree_results) > 0
    assert "B+ Tree" in tree_results[0]["text"]


def test_document_search_empty_database(tmp_path):
    db_file = str(tmp_path / "test_empty.db")
    db = DatabaseManager(db_file)  # Inits empty tables

    res = document_search("normalization", db_path=db_file)
    assert res["status"] == "SUCCESS"
    assert res["found"] is False
    assert len(res["chunks"]) == 0
    assert "No documents found" in res["message"]


def test_document_search_no_match(tmp_path):
    db_file = str(tmp_path / "test_nomatch.db")
    db = DatabaseManager(db_file)

    chunks = [
        {"chunk_index": 0, "page_number": 1, "text": "Photosynthesis is the process by which green plants make food.", "source": "biology.pdf"}
    ]
    db.save_document("biology.pdf", "PDF", 1, 1, chunks)

    res = document_search("Relational Database BCNF", db_path=db_file)
    assert res["status"] == "SUCCESS"
    assert res["found"] is False
    assert len(res["chunks"]) == 0


def test_pdf_file_extraction():
    from services.document_processor import extract_text_from_pdf
    if os.path.exists("sample_dbms_notes.pdf"):
        with open("sample_dbms_notes.pdf", "rb") as f:
            pages, warning = extract_text_from_pdf(f, "sample_dbms_notes.pdf")
            assert len(pages) >= 1
            assert "Normalization" in pages[0]["text"]
            assert "ACID" in pages[0]["text"]
