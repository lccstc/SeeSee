---
phase: 01-candidate-contract-foundation
reviewed: 2026-04-13T18:17:10Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - wxbot/bookkeeping-platform/bookkeeping_core/quote_candidates.py
  - wxbot/bookkeeping-platform/bookkeeping_core/database.py
  - wxbot/bookkeeping-platform/sql/postgres_schema.sql
  - wxbot/bookkeeping-platform/tests/test_postgres_backend.py
  - wxbot/bookkeeping-platform/bookkeeping_core/quotes.py
  - wxbot/bookkeeping-platform/tests/test_runtime.py
  - wxbot/bookkeeping-platform/bookkeeping_web/app.py
  - wxbot/bookkeeping-platform/bookkeeping_web/pages.py
  - wxbot/bookkeeping-platform/tests/test_webapp.py
findings:
  critical: 0
  warning: 3
  info: 0
  total: 3
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-04-13T18:17:10Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Phase 01 does preserve the candidate-only boundary: the key PostgreSQL-backed tests for candidate persistence, runtime capture, and harvest replay all passed. The main problems are in the safety loop around replay and in the durability of the new candidate evidence model: replay can silently drop fresh failures, document-level parser confidence is being persisted incorrectly, and the new lineage tables are not enforced by database constraints.

## Warnings

### WR-01: Harvest replay can hide fresh replay failures instead of returning them to the exception pool

**File:** `wxbot/bookkeeping-platform/bookkeeping_web/app.py:1119-1183`, `wxbot/bookkeeping-platform/bookkeeping_web/app.py:1310-1340`

**Issue:** `resolved_fully` is decided from the pre-replay exception pool, then the latest-message replay is executed with `record_exceptions=False`. If the freshly saved template still leaves unparsed lines or non-publishable rows in the full raw message, the replay path returns `remaining_lines` but does not persist those failures to `quote_parse_exceptions`, and the original exception can still be marked `resolved`. That breaks the stated Phase 01 contract that replay closes the loop and that failed samples remain replayable in the exception pool.

**Fix:**
```python
replay_result = _replay_latest_quote_document_with_current_template(
    db,
    exc_row=exc_row,
    record_exceptions=True,
)
resolved_fully = not replay_result["remaining_lines"] and replay_result["exceptions"] == 0
```

### WR-02: Candidate headers discard parser confidence and persist every candidate document as `confidence = 0`

**File:** `wxbot/bookkeeping-platform/bookkeeping_core/quote_candidates.py:44-65`, `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py:542-555`, `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py:818-860`, `wxbot/bookkeeping-platform/bookkeeping_core/database.py:1342-1365`

**Issue:** `ParsedQuoteDocument` already carries a document-level `confidence`, but `QuoteCandidateMessage` has no corresponding field, and `record_quote_candidate_bundle()` hardcodes the stored header confidence to `0`. Runtime and replay candidate documents therefore look indistinguishable from total parse failures at the `quote_documents` level, even when the parser returned high-confidence rows. That corrupts persisted evidence and will mislead any later validator, replay inspector, or analytics code that reads document confidence.

**Fix:**
```python
@dataclass(slots=True)
class QuoteCandidateMessage:
    ...
    confidence: float

# populate from parsed.confidence / explicit defaults
confidence=parsed.confidence

# persist the real value
document["confidence"]
```

### WR-03: The new candidate lineage tables are not protected by foreign keys

**File:** `wxbot/bookkeeping-platform/sql/postgres_schema.sql:229-280`

**Issue:** `quote_documents.replay_of_quote_document_id` and `quote_candidate_rows.quote_document_id` are stored as plain `BIGINT` columns with no `REFERENCES quote_documents(id)` constraint. That means replay headers can point at nonexistent parents and candidate rows can become orphaned without the database rejecting them. For a phase whose goal is “可追溯、可验证、不可误发布”, this leaves the new evidence chain weaker than the runtime code assumes.

**Fix:**
```sql
ALTER TABLE quote_documents
  ADD CONSTRAINT fk_quote_documents_replay_parent
  FOREIGN KEY (replay_of_quote_document_id) REFERENCES quote_documents(id);

ALTER TABLE quote_candidate_rows
  ADD CONSTRAINT fk_quote_candidate_rows_document
  FOREIGN KEY (quote_document_id) REFERENCES quote_documents(id) ON DELETE CASCADE;
```

## Residual Risks / Testing Gaps

- The reviewed tests cover happy-path candidate persistence and replay, but they do not exercise the case where a harvest-save replay still produces fresh exceptions after the operator believes the message is resolved.
- No test currently asserts the stored `quote_documents.confidence` value for runtime/replay candidates, so the incorrect `0` persists unnoticed.
- Candidate schema fail-fast coverage checks table/column presence, but not relational integrity guarantees such as foreign keys.

---

_Reviewed: 2026-04-13T18:17:10Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
