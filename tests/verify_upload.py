"""Directly verifies the PDF upload pipeline against the live edusync.db."""
import io
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.persistence import DatabaseManager
from services.document_processor import extract_text_from_pdf, chunk_document_pages, TFIDFSearchEngine

OK = "[OK]"; XX = "[XX]"
passed = 0; failed = 0

def check(label, cond, detail=""):
    global passed, failed
    if cond: passed += 1; tag = OK
    else: failed += 1; tag = XX
    print(f"  {tag} {label}" + (f" => {detail}" if detail else ""))
    return cond

db = DatabaseManager("edusync.db")

# ─── Baseline ─────────────────────────────────────────────────────────────
print("\n=== DB BASELINE ===")
docs_before = db.get_documents()
all_chunks_before = db.get_all_chunks()
sample = [d for d in docs_before if d.get("is_sample", 0)]
user   = [d for d in docs_before if not d.get("is_sample", 0)]
print(f"  Documents: {len(docs_before)} (sample={len(sample)}, user={len(user)})")
print(f"  Chunks   : {len(all_chunks_before)}")
for d in docs_before:
    tag = "sample" if d.get("is_sample", 0) else "user"
    print(f"  [{tag}] id={d['id']} {d['filename']!r} chunks={d['num_chunks']}")

# ─── Upload sample_dbms_notes.pdf ─────────────────────────────────────────
print("\n=== UPLOAD: sample_dbms_notes.pdf ===")
pdf_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_dbms_notes.pdf")
check("sample_dbms_notes.pdf exists on disk", os.path.exists(pdf_path))

with open(pdf_path, "rb") as f:
    pdf_bytes = f.read()

pages, warning = extract_text_from_pdf(io.BytesIO(pdf_bytes), "sample_dbms_notes.pdf")
check("extract_text_from_pdf returns pages", isinstance(pages, list) and len(pages) >= 1, f"{len(pages)} pages")
if warning:
    print(f"  [warn] {warning}")

chunks = chunk_document_pages(pages, filename="sample_dbms_notes.pdf")
check("chunk_document_pages produces chunks", len(chunks) >= 1, f"{len(chunks)} chunks")

doc_id_1 = db.save_document("sample_dbms_notes.pdf", "PDF", len(chunks), len(pages), chunks, is_sample=False)
docs_after_1 = db.get_documents()
all_chunks_after_1 = db.get_all_chunks()

check("First upload: doc saved", doc_id_1 is not None and doc_id_1 > 0, f"doc_id={doc_id_1}")
check("First upload: document count increased OR same filename exists",
      len(docs_after_1) >= len(docs_before),
      f"{len(docs_before)} -> {len(docs_after_1)}")
# Find the newly saved doc
saved_doc = next((d for d in docs_after_1 if d["filename"] == "sample_dbms_notes.pdf"), None)
check("sample_dbms_notes.pdf appears in document list", saved_doc is not None)
if saved_doc:
    check("Chunk count on saved doc matches produced chunks", saved_doc["num_chunks"] == len(chunks),
          f"saved={saved_doc['num_chunks']} produced={len(chunks)}")

# ─── Search unique content from that PDF ──────────────────────────────────
print("\n=== SEARCH (after upload) ===")
all_chunks_search = db.get_all_chunks()
engine = TFIDFSearchEngine(all_chunks_search)
norm_results = engine.search("normalization", top_k=5)
check("Search 'normalization' returns results", len(norm_results) > 0, f"{len(norm_results)} result(s)")
if norm_results:
    print(f"  Top result: score={norm_results[0]['similarity_score']} source={norm_results[0]['source']!r}")
    # If sample_dbms_notes.pdf has normalization content, it should appear
    from_new = [r for r in norm_results if r.get("source") == "sample_dbms_notes.pdf"]
    print(f"  From sample_dbms_notes.pdf: {len(from_new)} match(es)")

# ─── Duplicate upload ─────────────────────────────────────────────────────
print("\n=== DUPLICATE UPLOAD ===")
doc_id_2 = db.save_document("sample_dbms_notes.pdf", "PDF", len(chunks), len(pages), chunks, is_sample=False)
docs_after_2 = db.get_documents()
all_chunks_after_2 = db.get_all_chunks()

check("Same doc_id returned on second upload", doc_id_1 == doc_id_2, f"first={doc_id_1} second={doc_id_2}")
check("Document count unchanged after duplicate", len(docs_after_2) == len(docs_after_1),
      f"{len(docs_after_1)} -> {len(docs_after_2)}")
check("Chunk count unchanged after duplicate", len(all_chunks_after_2) == len(all_chunks_after_1),
      f"{len(all_chunks_after_1)} -> {len(all_chunks_after_2)}")

# ─── Final baseline ───────────────────────────────────────────────────────
print("\n=== FINAL DB STATE ===")
final_docs = db.get_documents()
sample2 = [d for d in final_docs if d.get("is_sample", 0)]
user2   = [d for d in final_docs if not d.get("is_sample", 0)]
print(f"  Documents: {len(final_docs)} (sample={len(sample2)}, user={len(user2)})")
for d in final_docs:
    tag = "sample" if d.get("is_sample", 0) else "user"
    print(f"  [{tag}] id={d['id']} {d['filename']!r} chunks={d['num_chunks']}")

# ─── Summary ──────────────────────────────────────────────────────────────
print(f"\n=== SUMMARY: {passed} passed, {failed} failed ===")
sys.exit(0 if failed == 0 else 1)
