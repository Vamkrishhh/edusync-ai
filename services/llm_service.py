"""
EduSync AI — LLM Service (Google GenAI SDK Integration)
Provides optional Gemini API calls with graceful fallback to deterministic logic.
"""

import json
import os
import re
from typing import Any, Dict, List, Optional

try:
    from google import genai
    from google.genai import types
    HAS_GENAI_PKG = True
except ImportError:
    HAS_GENAI_PKG = False


class LLMService:
    """
    Wrapper for Google GenAI SDK.
    Never exposes API keys; provides transparent mode flags.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        # Read from explicit argument, then env variable, then Streamlit secrets
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not self.api_key:
            try:
                import streamlit as st
                if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                    self.api_key = st.secrets["GEMINI_API_KEY"]
            except Exception:
                pass

        self.model_name = (
            model_name
            or os.environ.get("GEMINI_MODEL")
            or "gemini-2.5-flash"
        )
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initializes genai.Client if key is available."""
        if HAS_GENAI_PKG and self.api_key and self.api_key.strip():
            try:
                self.client = genai.Client(api_key=self.api_key.strip())
            except Exception:
                self.client = None
        else:
            self.client = None

    def is_available(self) -> bool:
        """Returns True if Gemini client is successfully configured."""
        return self.client is not None

    def get_mode_description(self) -> str:
        """Returns readable operational mode description."""
        if self.is_available():
            return f"AI Mode (Google Gemini: {self.model_name})"
        return "Demo Mode (Deterministic Fallback Engine)"

    def generate_quiz_llm(
        self,
        topic: str,
        difficulty: str,
        num_questions: int,
        context_chunks: List[Dict[str, Any]],
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Generates grounded MCQs using Gemini.
        Returns None if client is unavailable or generation fails.
        """
        if not self.is_available():
            return None

        context_text = "\n\n".join([
            f"[Source: {c.get('source', 'Notes')} Page {c.get('page_number', '?')}]: {c.get('text', '')}"
            for c in context_chunks[:6]
        ])

        prompt = f"""You are an expert undergraduate computer science professor creating an exam quiz.
Generate {num_questions} multiple-choice questions on the topic: '{topic}' with difficulty: '{difficulty}'.

GROUNDING RULE:
Base the questions strictly on the following course material whenever relevant:
---
{context_text if context_text else 'No specific document passages provided; use core computer science curricula principles.'}
---

Output MUST be valid JSON array of objects with the following exact keys:
[
  {{
    "id": 1,
    "topic": "{topic}",
    "difficulty": "{difficulty}",
    "question": "Question text here?",
    "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "correct_answer": "B) ...",
    "explanation": "Brief explanation of why this answer is correct and why others are incorrect.",
    "source": "Document name or topic reference"
  }}
]
Do not wrap in markdown tags if possible, or use standard ```json ``` formatting. Ensure the array has exactly {num_questions} items.
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            raw_text = response.text or ""
            # Extract JSON block
            json_match = re.search(r"\[.*\]", raw_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                if isinstance(parsed, list) and len(parsed) > 0:
                    return parsed
        except Exception as e:
            # Silently catch and return None to trigger safe deterministic fallback
            return None

        return None

    def synthesize_response_llm(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        performance_summary: Dict[str, Any],
        study_plan: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Synthesizes an intelligent, grounded student advisory response.
        Returns None if Gemini is unavailable or fails.
        """
        if not self.is_available():
            return None

        docs_context = "\n\n".join([
            f"- [{c.get('source')} p.{c.get('page_number')}]: {c.get('text')[:300]}..."
            for c in retrieved_chunks[:5]
        ]) if retrieved_chunks else "No specific document chunks retrieved."

        perf_context = json.dumps(performance_summary, indent=2)
        plan_context = json.dumps(study_plan, indent=2) if study_plan else "No plan created yet."

        prompt = f"""You are EduSync AI, an empathetic and highly structured multi-tool academic advisor for undergraduate students.

STUDENT QUERY:
"{query}"

RETRIEVED COURSE MATERIAL (GROUND TRUTH):
{docs_context}

STUDENT QUIZ PERFORMANCE DATA:
{perf_context}

ACTIVE STUDY PLAN:
{plan_context}

GUIDELINES:
1. Ground your advice in the retrieved notes and syllabus.
2. Clearly distinguish information derived from their uploaded documents versus general academic suggestions.
3. Be encouraging, precise, and actionable.
4. Conclude with a clear 'Recommended Next Step' (e.g. taking a specific quiz or reviewing a weak topic).
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            return response.text
        except Exception:
            return None


# Helper singleton
_default_llm_service: Optional[LLMService] = None


def get_llm_service(api_key: Optional[str] = None, model_name: Optional[str] = None) -> LLMService:
    global _default_llm_service
    # Always reinitialize if a key is explicitly provided (e.g. user saved a new key),
    # or if no instance exists yet.
    if _default_llm_service is None or api_key is not None:
        _default_llm_service = LLMService(api_key=api_key, model_name=model_name)
    return _default_llm_service
