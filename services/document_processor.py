"""
EduSync AI — Document Processor & Retrieval (RAG) Service
Handles PDF text extraction with pypdf, safe chunking, and TF-IDF semantic document search.
"""

import io
import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pypdf
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def extract_text_from_pdf(
    file_bytes_or_stream: Any, filename: str
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Safely extracts text page-by-page from a PDF file.

    Returns:
        (pages_list, warning_message)
        pages_list: [{'page_number': int, 'text': str}]
        warning_message: str if scanned, empty, or problematic; None if successful.
    """
    pages_data: List[Dict[str, Any]] = []
    warning: Optional[str] = None

    try:
        # Wrap bytes in BytesIO if needed
        if isinstance(file_bytes_or_stream, bytes):
            stream = io.BytesIO(file_bytes_or_stream)
        elif hasattr(file_bytes_or_stream, "read"):
            # Could be a Streamlit UploadedFile or file object
            raw_bytes = file_bytes_or_stream.read()
            if hasattr(file_bytes_or_stream, "seek"):
                file_bytes_or_stream.seek(0)
            stream = io.BytesIO(raw_bytes)
        else:
            stream = file_bytes_or_stream

        reader = pypdf.PdfReader(stream)

        if len(reader.pages) == 0:
            return [], f"The file '{filename}' has 0 pages (empty PDF)."

        total_extracted_chars = 0
        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            try:
                page_text = page.extract_text() or ""
            except Exception as pe:
                page_text = f"[Error extracting text from page {page_num}: {str(pe)}]"

            # Clean up whitespace
            cleaned_text = re.sub(r"[ \t]+", " ", page_text).strip()
            total_extracted_chars += len(cleaned_text)

            pages_data.append({"page_number": page_num, "text": cleaned_text})

        if total_extracted_chars < 50:
            warning = (
                f"The document '{filename}' contains very little extractable text ({total_extracted_chars} characters). "
                "It may be a scanned image or empty PDF. OCR is required for scanned documents."
            )

    except pypdf.errors.PdfReadError as pre:
        return [], f"Failed to read '{filename}': Invalid or corrupted PDF file ({str(pre)})."
    except Exception as e:
        return [], f"An unexpected error occurred while parsing '{filename}': {str(e)}"

    return pages_data, warning


def chunk_document_pages(
    pages_data: List[Dict[str, Any]],
    filename: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> List[Dict[str, Any]]:
    """
    Splits page texts into chunks while preserving page numbers and source metadata.

    Args:
        pages_data: List of {'page_number': int, 'text': str}
        filename: Source file name
        chunk_size: Target characters per chunk
        chunk_overlap: Overlap in characters between adjacent chunks

    Returns:
        List of chunk dicts:
        [{'chunk_index': int, 'page_number': int, 'text': str, 'source': str}]
    """
    all_chunks: List[Dict[str, Any]] = []
    chunk_counter = 0

    for page in pages_data:
        page_num = page["page_number"]
        text = page["text"].strip()

        if not text:
            continue

        # If text is shorter than chunk_size, keep as single chunk
        if len(text) <= chunk_size:
            all_chunks.append({
                "chunk_index": chunk_counter,
                "page_number": page_num,
                "text": text,
                "source": filename,
            })
            chunk_counter += 1
            continue

        # Split into overlapping windows
        start = 0
        text_len = len(text)
        step = max(chunk_size - chunk_overlap, 100)

        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunk_content = text[start:end].strip()

            if chunk_content:
                all_chunks.append({
                    "chunk_index": chunk_counter,
                    "page_number": page_num,
                    "text": chunk_content,
                    "source": filename,
                })
                chunk_counter += 1

            if end >= text_len:
                break
            start += step

    return all_chunks


class TFIDFSearchEngine:
    """
    TF-IDF Vectorizer and Cosine Similarity search engine for document chunks.
    No external vector DB required; runs in-memory and scales smoothly for student notes.
    """

    def __init__(self, chunks: Optional[List[Dict[str, Any]]] = None):
        self.chunks: List[Dict[str, Any]] = chunks or []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        if self.chunks:
            self.index_chunks(self.chunks)

    def index_chunks(self, chunks: List[Dict[str, Any]]):
        """Builds TF-IDF index across chunks."""
        self.chunks = chunks
        if not chunks:
            self.vectorizer = None
            self.tfidf_matrix = None
            return

        corpus = [c["text"] for c in chunks]
        # Token pattern supports alphanumeric including terms like 1NF, 2NF, B+Tree, ACID, SQL
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            token_pattern=r"(?u)\b[A-Za-z0-9_\+\-]+\b",
            ngram_range=(1, 2),
            max_features=10000,
            sublinear_tf=True,
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def search(
        self, query: str, top_k: int = 5, min_score: float = 0.05
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top_k relevant chunks matching the query.

        Returns:
            List of matched chunk dicts enriched with 'similarity_score'.
        """
        if not self.chunks or self.vectorizer is None or self.tfidf_matrix is None:
            return []

        cleaned_query = query.strip()
        if not cleaned_query:
            return []

        try:
            query_vec = self.vectorizer.transform([cleaned_query])
            scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

            # Filter by min_score
            matched_indices = np.where(scores >= min_score)[0]
            if len(matched_indices) == 0:
                return []

            # Sort descending
            sorted_indices = matched_indices[np.argsort(-scores[matched_indices])]
            top_indices = sorted_indices[:top_k]

            results = []
            for idx in top_indices:
                chunk = dict(self.chunks[idx])
                chunk["similarity_score"] = round(float(scores[idx]), 4)
                results.append(chunk)

            return results
        except Exception:
            return []
