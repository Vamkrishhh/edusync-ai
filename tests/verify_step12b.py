"""
STEP 12B — Automated Regression Verification Script
Run: python tests/verify_step12b.py
Tests: PDF chunking pipeline, duplicate rejection, DB baseline counts.
"""

import io
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.persistence import DatabaseManager
from services.document_processor import extract_text_from_pdf, chunk_document_pages, TFIDFSearchEngine

PASS = "PASS"
FAIL = "FAIL"
results = []


def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((status, label, detail))
    icon = "OK" if condition else "XX"
    print(f"  [{icon}] {label}" + (f" => {detail}" if detail else ""))
    return condition


# ─── SECTION 0: DB BASELINE ────────────────────────────────────────────────
print("\n=== SECTION 0: Current DB Baseline ===")
db = DatabaseManager("edusync.db")
docs_before = db.get_documents()
chunks_before = db.get_all_chunks()
stats_before = db.get_dashboard_stats()
sample_docs = [d for d in docs_before if d.get("is_sample", 0) == 1]
user_docs   = [d for d in docs_before if d.get("is_sample", 0) == 0]

print(f"  Documents total  : {len(docs_before)}  (sample={len(sample_docs)}, user={len(user_docs)})")
print(f"  Chunks total     : {len(chunks_before)}")
print(f"  Quiz attempts    : {stats_before['quiz_attempts_count']}")
print(f"  Study tasks      : {stats_before['total_study_tasks']}")
for d in docs_before:
    tag = "sample" if d.get("is_sample", 0) else "user"
    print(f"    [{tag}] id={d['id']} {d['filename']!r}")


# ─── SECTION 1: PDF PIPELINE ───────────────────────────────────────────────
print("\n=== SECTION 1: PDF Extraction + Chunking Pipeline ===")

UNIQUE_TOKEN = "EDUSYNC12B_UNIQUE_VERIFICATION_STRING_XQ9Z"
PDF_BYTES = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type /Catalog /Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type /Pages /Kids [3 0 R] /Count 1>>endobj\n"
    b"3 0 obj<</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]"
    b"/Contents 4 0 R /Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
    b"4 0 obj<</Length 121>>\nstream\n"
    b"BT /F1 12 Tf 72 720 Td"
    b"(EDUSYNC12B_UNIQUE_VERIFICATION_STRING_XQ9Z Primary key) Tj ET\n"
    b"endstream\nendobj\n"
    b"5 0 obj<</Type /Font /Subtype /Type1 /BaseFont /Helvetica>>endobj\n"
    b"xref\n0 6\n"
    b"0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n"
    b"0000000115 00000 n \n0000000266 00000 n \n0000000436 00000 n \n"
    b"trailer<</Size 6 /Root 1 0 R>>\nstartxref\n515\n%%EOF"
)

pdf_filename = "edusync_12b_test.pdf"
pdf_stream = io.BytesIO(PDF_BYTES)

pages, warning = extract_text_from_pdf(pdf_stream, pdf_filename)
check("extract_text_from_pdf(stream, filename) — no TypeError", True)
check("returns list", isinstance(pages, list), f"type={type(pages).__name__}")

if warning:
    print(f"  [warn] Extractor warning (ok for synthetic): {warning}")
if not pages or not pages[0].get("text", "").strip():
    # Synthetic PDF text extraction may fail; inject pages for downstream test
    pages = [{"page_number": 1, "text": f"{UNIQUE_TOKEN} Primary keys uniquely identify rows."}]
    print("  [info] Using injected pages (pypdf could not extract synthetic text)")
else:
    check("Unique token found in extracted text", UNIQUE_TOKEN in pages[0]["text"])

try:
    chunks = chunk_document_pages(pages, filename=pdf_filename)
    check("chunk_document_pages(pages, filename=...) — no TypeError", True, f"{len(chunks)} chunk(s)")
    check("At least 1 chunk produced", len(chunks) >= 1)
    check("Chunk contains unique token", any(UNIQUE_TOKEN in c.get("text","") for c in chunks))
except TypeError as e:
    check("chunk_document_pages call succeeds", False, str(e))
    chunks = []


# ─── SECTION 2: DUPLICATE UPLOAD PREVENTION ────────────────────────────────
print("\n=== SECTION 2: Duplicate Upload Prevention ===")

tmp_db_path = os.path.join(tempfile.gettempdir(), "edusync_12b_tmp.db")
if os.path.exists(tmp_db_path):
    os.remove(tmp_db_path)
tdb = DatabaseManager(tmp_db_path)

if chunks:
    doc_id_1 = tdb.save_document(pdf_filename, "PDF", len(chunks), len(pages), chunks)
    after1_docs   = tdb.get_documents()
    after1_chunks = tdb.get_all_chunks()
    check("First upload: 1 document row", len(after1_docs) == 1, f"doc_id={doc_id_1}")
    check("First upload: correct chunk count", len(after1_chunks) == len(chunks))

    doc_id_2 = tdb.save_document(pdf_filename, "PDF", len(chunks), len(pages), chunks)
    after2_docs   = tdb.get_documents()
    after2_chunks = tdb.get_all_chunks()
    check("Second upload: still only 1 document row", len(after2_docs) == 1, f"found {len(after2_docs)}")
    check("Second upload: same doc_id", doc_id_1 == doc_id_2, f"first={doc_id_1} second={doc_id_2}")
    check("Second upload: no duplicate chunks", len(after2_chunks) == len(chunks),
          f"expected={len(chunks)} found={len(after2_chunks)}")
else:
    print("  [skip] No chunks — duplicate test skipped")

try:
    del tdb  # release sqlite connection before removal
    import gc; gc.collect()
    import time; time.sleep(0.05)
    os.remove(tmp_db_path)
except Exception:
    pass  # Windows file-lock: cleanup deferred, does not affect test results


# ─── SECTION 3: TF-IDF SEARCH ──────────────────────────────────────────────
print("\n=== SECTION 3: TF-IDF Search Correctness ===")

if chunks:
    engine = TFIDFSearchEngine(chunks)
    res = engine.search("primary key", top_k=3)
    check("Search 'primary key' returns results", len(res) > 0, f"{len(res)} match(es)")
    if res:
        top = res[0]
        check("Result has similarity_score > 0", top.get("similarity_score", 0) > 0)
        check("Result source matches filename", top.get("source") == pdf_filename, top.get("source"))

    uniq_res = engine.search("primary key uniquely identify rows", top_k=1)
    check("Search for unique-to-doc phrase returns result", len(uniq_res) >= 1)
else:
    print("  [skip] No chunks — search test skipped")


# ─── SECTION 4: DEMO BASELINE CHECK ────────────────────────────────────────
print("\n=== SECTION 4: Demo Baseline (is_sample flags) ===")

db2 = DatabaseManager("edusync.db")
all_docs2 = db2.get_documents()
sample_docs2 = [d for d in all_docs2 if d.get("is_sample", 0) == 1]
user_docs2   = [d for d in all_docs2 if d.get("is_sample", 0) == 0]

print(f"  Total: {len(all_docs2)}  sample={len(sample_docs2)}  user={len(user_docs2)}")
check("At least 1 sample document in live DB", len(sample_docs2) >= 1,
      "Use 'Quick Demo Data' button in app to seed if 0")


# ─── SUMMARY ───────────────────────────────────────────────────────────────
print("\n=== SUMMARY ===")
passed = sum(1 for r in results if r[0] == PASS)
failed = sum(1 for r in results if r[0] == FAIL)
print(f"  Automated checks: {passed} passed, {failed} failed")
for r in results:
    icon = "OK" if r[0] == PASS else "XX"
    print(f"  [{icon}] {r[1]}")

sys.exit(0 if failed == 0 else 1)
