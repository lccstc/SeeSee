# Phase 01: Candidate Contract Foundation - Research

**Researched:** 2026-04-14
**Domain:** Brownfield quote-wall candidate contract, evidence persistence, and parser-to-fact boundary
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
### Candidate contract shape
- **D-01:** Candidate contract is two-layered: `message-level parse result` plus `row candidates`. Row-only output is not acceptable because later `full_snapshot` / `delta_update` classification, replay, exception comparison, and human review all need message-level context.
- **D-02:** `message-level parse result` is the authoritative container for parser outcome, parse status, parser lineage, message fingerprint, snapshot hypothesis, and later validation / publish decisions.
- **D-03:** `row candidates` are detail records under the message container. They express extracted quote intent, normalization state, row-level publishability, and field-level evidence, but do not directly mutate active facts.

### Hard publication boundary
- **D-04:** Phase 1 may preserve parts of the current publish shell temporarily, but any later `deactivate` / `upsert` must consume candidate contract output. Parser-internal transient results may not write facts directly anymore.
- **D-05:** This phase does not need to finish the final single guarded publisher. That stronger custody boundary is still a Phase 3 objective. But Phase 1 must remove the implicit mode where runtime or replay paths skip candidate creation and go straight from parser output to fact writes.
- **D-06:** Phase 1 is successful only if downstream phases can assume a stable chain of `raw input -> candidate -> evidence -> later publish decision`, with no return to parser-direct fact mutation.

### Required evidence and decision fields
- **D-07:** Every message-level candidate record must retain at least: `raw_message`, `message_id`, `chat_id`, `sender`, `message_time`, `parser_template`, `parser_version`, `parser_kind`, `parse_status`, `message_fingerprint`, `snapshot_hypothesis`, `snapshot_hypothesis_reason`, and structured `rejection_reasons`.
- **D-08:** Every row candidate must retain at least: `source_line`, `line_confidence`, `normalized_sku_key`, `normalization_status`, `row_publishable`, `field_sources` or equivalent extraction spans, and `restriction_parse_status`.
- **D-09:** Phase 1 should capture enough evidence to support later validation and replay decisions, not just input logging. If a field is required for later `publishable_rows`, fact diffing, exception clustering, or operator review, it belongs in the candidate contract now.

### Brownfield persistence strategy
- **D-10:** Candidate store and fact store must remain semantically separate. Candidate records are for audit, replay, debugging, and exception handling. Fact rows are for active published wall state.
- **D-11:** Prefer minimum necessary schema extension. If current `quote_documents` cannot represent candidate semantics cleanly, add candidate-related tables or fields. Do not overload `quote_price_rows` with candidate meaning.
- **D-12:** This phase is not an architecture cleanup exercise. Schema changes are allowed only when they are the smallest reliable way to enforce the candidate boundary in the existing brownfield system.

### Claude's Discretion
- Exact table layout, naming, and whether candidate persistence is one table plus child rows or multiple focused tables
- Exact fingerprint algorithm and evidence serialization format
- How to adapt existing parser outputs into the new contract with the least risky migration path

### Deferred Ideas (OUT OF SCOPE)
- Final single guarded publisher ownership and bypass removal details belong to Phase 3
- Full `full_snapshot` / `delta_update` publish semantics belong to Phase 4, though Phase 1 must already carry the message-level hypothesis fields needed for that work
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EVID-01 | User can trace every candidate or published quote row back to the exact raw message, source line, sender, group, and message time | Use `quote_documents` as the immutable message header and add `quote_candidate_rows` with `source_line`, `field_sources`, and stable `normalized_sku_key`. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/database.py] |
| CAND-01 | System creates quote candidates without directly mutating active quote facts | Remove `deactivate_old_quotes_for_group()` and `upsert_quote_price_row_with_history()` from runtime capture and replay helper paths; persist candidates only. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_web/app.py] |
| CAND-02 | Each candidate preserves parser/template/rule lineage and message-type hypothesis for later debugging | Extend message header metadata with `parser_kind`, `parser_template`, `parser_version`, `snapshot_hypothesis`, `snapshot_hypothesis_reason`, and structured rejection payloads. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: .planning/phases/01-candidate-contract-foundation/01-CONTEXT.md] |
</phase_requirements>

## Project Constraints (from AGENTS.md)

- Quote parsing, validation, publication, and exception rules must stay in `wxbot/bookkeeping-platform/bookkeeping_core/`; page code may display them but may not own them. [VERIFIED: AGENTS.md]
- `POST /api/core/messages` is the formal runtime message entry, so the Phase 1 boundary must be enforced inside core runtime paths, not in adapters. [VERIFIED: AGENTS.md] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/runtime.py]
- PostgreSQL is the runtime source of truth and SQLite is explicitly disallowed for runtime facts, so candidate persistence should be designed for PostgreSQL first. [VERIFIED: AGENTS.md] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/database.py]
- The repo standard test framework is `unittest`, and quote-wall work should prioritize replay safety, exception handling, and active-fact protection before convenience. [VERIFIED: AGENTS.md]
- No project-local `.claude/skills/` or `.agents/skills/` directory exists in this repo, so there are no repo-specific skill conventions to accommodate beyond the existing GSD workflow. [VERIFIED: .claude/launch.json] [VERIFIED: .claude/settings.local.json]

## Summary

Phase 1 should be planned as a brownfield custody split, not as a parser rewrite. The current system already has a message header object (`quote_documents`), in-memory parse objects (`ParsedQuoteDocument`, `ParsedQuoteRow`, `ParsedQuoteException`), and an exception store, but `QuoteCaptureService.capture_from_message()` still deactivates old rows and inserts new `quote_price_rows` immediately after parsing. The replay helper `_replay_latest_quote_document_with_current_template()` repeats the same fact-mutation pattern, so runtime and replay are both bypass paths today. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_web/app.py]

The safest Phase 1 cut is additive: keep `quote_documents` as the message-level candidate header, add explicit candidate-only metadata columns to it, add a new `quote_candidate_rows` child table, and make both runtime capture and replay persist only `quote_documents` + `quote_candidate_rows` + `quote_parse_exceptions`. This preserves existing exception and raw-message workflows while stopping parser-direct writes into `quote_price_rows`, which is currently the table behind `/api/quotes/board`. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/database.py] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_web/app.py] [VERIFIED: .planning/ROADMAP.md]

The planning consequence is significant: several existing tests and web flows assume that a successful replay or harvest immediately refreshes the quote board. Those expectations are incompatible with Phase 1 and should be rewritten around candidate persistence, replay evidence, and explicit “no fact mutation” assertions. That is acceptable because the project’s own roadmap and project docs say v1 is validation-first and does not take over production publication. [VERIFIED: wxbot/bookkeeping-platform/tests/test_webapp.py] [VERIFIED: .planning/PROJECT.md] [VERIFIED: .planning/ROADMAP.md]

**Primary recommendation:** Upgrade `quote_documents` into the message-level candidate container, add a new `quote_candidate_rows` table, and make runtime plus replay write candidates and exceptions only; leave `quote_price_rows` untouched until the guarded publisher phase. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_web/app.py] [VERIFIED: .planning/phases/01-candidate-contract-foundation/01-CONTEXT.md]

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `dataclasses` + `typing` | Python 3.14.3 runtime in repo `.venv` [VERIFIED: local env] | Internal candidate contract types and serialization boundaries | The repo already uses `@dataclass(slots=True)` for `NormalizedMessageEnvelope` and parsed quote objects, while Python docs state `TypedDict` is only a type-checking contract and remains a plain `dict` at runtime, so dataclasses are the right internal boundary and `TypedDict` should stay at JSON/API edges. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/contracts.py] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py] [CITED: https://docs.python.org/3/library/typing.html] |
| PostgreSQL tables + `jsonb` evidence columns | Local CLI `psql` 16.13; runtime requires PostgreSQL DSN [VERIFIED: local env] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/database.py] | Candidate header persistence, row evidence, structured rejection payloads, and later validator handoff | PostgreSQL already backs runtime schema verification, and official docs recommend `jsonb` for most applications because it validates JSON, avoids reparsing, and supports indexing. [VERIFIED: wxbot/bookkeeping-platform/sql/postgres_schema.sql] [CITED: https://www.postgresql.org/docs/current/datatype-json.html] |
| `psycopg` | 3.3.3 in project `.venv` [VERIFIED: local env] | PostgreSQL driver used by `BookkeepingDB` | The existing database layer already depends on `psycopg`, so Phase 1 should stay inside the current DB adapter instead of introducing a second persistence client. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/database.py] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `unittest` | Python stdlib under Python 3.14.3 [VERIFIED: local env] | Contract, persistence, runtime, and replay regression tests | Use for all Phase 1 verification because the repo already standardizes on `unittest` and ships a PostgreSQL test base. [VERIFIED: AGENTS.md] [VERIFIED: wxbot/bookkeeping-platform/tests/support/postgres_test_case.py] |
| `PostgresTestCase` | Repo-local test base [VERIFIED: wxbot/bookkeeping-platform/tests/support/postgres_test_case.py] | Per-test schema isolation via `postgres_schema.sql` | Use for any test that exercises candidate tables or runtime capture because it matches the repo’s schema-verified runtime model. [VERIFIED: wxbot/bookkeeping-platform/tests/support/postgres_test_case.py] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `quote_documents` header + new `quote_candidate_rows` | Brand-new `quote_candidate_messages` plus child rows | Cleaner naming, but it duplicates the existing message-header role, forces broader exception/replay rewiring, and increases blast radius with no safety gain in Phase 1. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/database.py] [VERIFIED: wxbot/bookkeeping-platform/tests/test_webapp.py] |
| `jsonb` for `field_sources` / rejection payloads | Store JSON as `TEXT` | The repo already stores some JSON as text, but official PostgreSQL docs say `jsonb` is the better default for queryable structured payloads, which matters for later replay diffing and exception clustering. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/database.py] [CITED: https://www.postgresql.org/docs/current/datatype-json.html] |
| Dataclass internal contract | `TypedDict` everywhere | Python docs say `TypedDict` instances are runtime `dict`s with no runtime key enforcement, so it does not create a hard internal boundary by itself. [CITED: https://docs.python.org/3/library/typing.html] |

**Installation:** No new library is required for the core implementation if the phase stays within Python stdlib + existing `psycopg`. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/database.py] [VERIFIED: local env]

**Version verification:** `python3 --version` returned `Python 3.14.3`, `wxbot/bookkeeping-platform/.venv/bin/python -c "import psycopg; print(psycopg.__version__)"` returned `3.3.3`, and `psql --version` returned `16.13`. [VERIFIED: local env]

## Architecture Patterns

### Recommended Project Structure

```text
wxbot/bookkeeping-platform/bookkeeping_core/
├── quotes.py                  # Parser selection and brownfield orchestration only
├── quote_candidates.py        # NEW: candidate dataclasses, serializers, and bundle helpers
├── database.py                # NEW: candidate insert/query methods and schema verification updates
└── runtime.py                 # Calls candidate-only capture path

wxbot/bookkeeping-platform/bookkeeping_web/
└── app.py                     # Replay and exception save paths call candidate-only replay helper

wxbot/bookkeeping-platform/tests/
├── test_postgres_backend.py   # Candidate schema and persistence contract
├── test_runtime.py            # Runtime capture does not mutate active facts
└── test_webapp.py             # Replay/harvest save no longer refreshes board directly
```

This structure keeps all custody rules inside `bookkeeping_core`, matches AGENTS.md placement rules, and minimizes churn by leaving `pages.py` and the existing board read model alone. [VERIFIED: AGENTS.md] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/runtime.py]

### Pattern 1: Message Header Plus Child Candidate Rows

**What:** Persist one message-level candidate header per source message in `quote_documents`, then persist zero-to-many candidate rows in a new child table keyed by `quote_document_id`. [VERIFIED: .planning/phases/01-candidate-contract-foundation/01-CONTEXT.md]

**When to use:** Use this for every parser path, including normal runtime parsing, inquiry-context reply parsing, and replay of historical exceptions. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_web/app.py]

**Recommended schema shape:** [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/database.py] [CITED: https://www.postgresql.org/docs/current/datatype-json.html] [CITED: https://www.postgresql.org/docs/current/sql-altertable.html]

```sql
ALTER TABLE quote_documents
  ADD COLUMN IF NOT EXISTS parser_kind TEXT NOT NULL DEFAULT 'unknown',
  ADD COLUMN IF NOT EXISTS message_fingerprint TEXT NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS snapshot_hypothesis TEXT NOT NULL DEFAULT 'unresolved',
  ADD COLUMN IF NOT EXISTS snapshot_hypothesis_reason TEXT NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS rejection_reasons_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS run_kind TEXT NOT NULL DEFAULT 'runtime',
  ADD COLUMN IF NOT EXISTS replay_of_quote_document_id BIGINT;

CREATE TABLE IF NOT EXISTS quote_candidate_rows (
  id BIGSERIAL PRIMARY KEY,
  quote_document_id BIGINT NOT NULL,
  row_ordinal INTEGER NOT NULL,
  source_line TEXT NOT NULL,
  source_line_index INTEGER,
  line_confidence NUMERIC(6,4) NOT NULL,
  normalized_sku_key TEXT NOT NULL,
  normalization_status TEXT NOT NULL,
  row_publishable BOOLEAN NOT NULL DEFAULT FALSE,
  publishability_basis TEXT NOT NULL DEFAULT 'parser_prevalidation',
  restriction_parse_status TEXT NOT NULL,
  card_type TEXT,
  country_or_currency TEXT,
  amount_range TEXT,
  multiplier TEXT,
  form_factor TEXT,
  price NUMERIC(18,6),
  quote_status TEXT NOT NULL DEFAULT 'candidate',
  restriction_text TEXT NOT NULL DEFAULT '',
  field_sources_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  rejection_reasons_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  parser_template TEXT NOT NULL,
  parser_version TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (quote_document_id, row_ordinal)
);
```

### Pattern 2: Parser Adapters Return Contracts, Not Side Effects

**What:** Split parsing into two steps: `parse_*()` returns a `QuoteCandidateMessage`, and a separate writer persists the candidate bundle. The parser returns no DB side effects and never calls `deactivate_old_quotes_for_group()` or `upsert_quote_price_row_with_history()`. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py]

**When to use:** Apply this to `capture_from_message()` first, then to the replay helper so runtime and replay share the same custody boundary. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/runtime.py] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_web/app.py]

**Example:** [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/contracts.py] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py] [CITED: https://docs.python.org/3/library/typing.html]

```python
from dataclasses import dataclass, field

@dataclass(slots=True)
class QuoteCandidateRow:
    row_ordinal: int
    source_line: str
    source_line_index: int | None
    line_confidence: float
    normalized_sku_key: str
    normalization_status: str
    row_publishable: bool
    restriction_parse_status: str
    card_type: str | None = None
    country_or_currency: str | None = None
    amount_range: str | None = None
    multiplier: str | None = None
    form_factor: str | None = None
    price: float | None = None
    quote_status: str = "candidate"
    restriction_text: str = ""
    field_sources: dict[str, dict[str, object]] = field(default_factory=dict)
    rejection_reasons: list[dict[str, str]] = field(default_factory=list)

@dataclass(slots=True)
class QuoteCandidateMessage:
    platform: str
    chat_id: str
    chat_name: str
    message_id: str
    sender_id: str
    sender_name: str
    raw_message: str
    message_time: str
    parser_kind: str
    parser_template: str
    parser_version: str
    parse_status: str
    message_fingerprint: str
    snapshot_hypothesis: str
    snapshot_hypothesis_reason: str
    rejection_reasons: list[dict[str, str]]
    rows: list[QuoteCandidateRow]
```

### Pattern 3: Replay Generates a New Candidate Run, Not New Active Facts

**What:** Replay should parse the stored raw message with the current template/config, persist a new candidate run (`run_kind='replay'`), and return comparison-ready metadata. It should not modify `quote_price_rows` and should not deactivate old facts. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_web/app.py] [VERIFIED: .planning/ROADMAP.md]

**When to use:** Use this in `_replay_latest_quote_document_with_current_template()` and in any later replay tooling. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_web/app.py]

**Example:**

```python
def replay_quote_document_to_candidates(db, *, quote_document_id: int) -> dict[str, object]:
    original = db.get_quote_document_bundle(quote_document_id=quote_document_id)
    candidate = parse_quote_message_to_candidate(
        raw_text=original["document"]["raw_text"],
        profile=original["group_profile"],
        run_kind="replay",
        replay_of_quote_document_id=quote_document_id,
    )
    persisted = db.record_quote_candidate_bundle(candidate)
    return {
        "replayed": True,
        "quote_document_id": persisted["quote_document_id"],
        "candidate_rows": persisted["candidate_row_count"],
        "exceptions": persisted["exception_count"],
        "mutated_active_facts": False,
    }
```

### Anti-Patterns to Avoid

- **Parser-side `deactivate` before durable candidate persistence:** Today runtime and replay both do this, and it violates the project rule that failure must not touch prior active facts. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_web/app.py]
- **Reusing `quote_price_rows` as both candidate store and fact store:** This would force every future validator, replay, and operator tool to infer state from active-fact rows, which directly conflicts with D-10 and makes Phase 3 harder. [VERIFIED: .planning/phases/01-candidate-contract-foundation/01-CONTEXT.md] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/database.py]
- **Treating `parse_status` as publish status:** Existing `parse_status` values (`parsed`, `empty`, `ignored`, `unparsable`) do not encode validator outcome or guarded publication outcome. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/database.py]
- **Encoding field evidence in free-form strings only:** Current rows keep `source_line` but no structured field lineage, which is insufficient for later per-field debugging. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Candidate persistence | Ad-hoc dict blobs stuffed into `quote_price_rows` | Dedicated `quote_candidate_rows` plus structured `jsonb` evidence columns | Facts and candidates have different semantics, retention needs, and read patterns. [VERIFIED: .planning/phases/01-candidate-contract-foundation/01-CONTEXT.md] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/database.py] |
| Internal contract boundary | Unvalidated plain dicts passed between parser, DB, and replay code | Dataclass-based internal models with explicit serializer methods | The repo already uses dataclasses, and `TypedDict` does not enforce keys at runtime. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/contracts.py] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py] [CITED: https://docs.python.org/3/library/typing.html] |
| Schema rollout | Hand-maintained one-off SQL edits outside repo schema files | Update both `sql/postgres_schema.sql` and `BookkeepingDB._verify_schema()` expectations together | Runtime startup fails on schema mismatch, so planner must treat schema and verifier changes as one task. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/database.py] [VERIFIED: wxbot/bookkeeping-platform/sql/postgres_schema.sql] |
| Replay verification | Board refresh as proof that replay succeeded | Candidate bundle persistence plus explicit candidate-count / exception-count assertions | Board mutation is exactly the side effect Phase 1 is supposed to remove. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_web/app.py] [VERIFIED: wxbot/bookkeeping-platform/tests/test_webapp.py] |

**Key insight:** The brownfield system already has enough scaffolding to add a candidate custody layer without a rewrite, but that only works if `quote_price_rows` stops being the parser’s output table. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/database.py]

## Common Pitfalls

### Pitfall 1: Dual-Write Transition

**What goes wrong:** The code writes new candidate rows and still writes `quote_price_rows`, so the phase appears complete on paper while parser-direct publication still exists in practice. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py]

**Why it happens:** Brownfield migrations often keep the old “working” write path as a fallback, but here that fallback is the exact behavior the phase is supposed to eliminate. [VERIFIED: .planning/ROADMAP.md]

**How to avoid:** Plan an explicit cutover step where `capture_from_message()` and replay helper methods stop calling `deactivate_old_quotes_for_group()` and `upsert_quote_price_row_with_history()` entirely. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_web/app.py]

**Warning signs:** Quote board rows change after runtime capture or replay even though no guarded publisher exists yet. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/database.py]

### Pitfall 2: Losing Evidence Granularity

**What goes wrong:** The message header keeps only `raw_text`, while row candidates lose the specific source line or field lineage that produced each normalized value. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py]

**Why it happens:** Current parsed row objects carry `source_line` and normalized fields, but there is no structured `field_sources` persistence yet. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py]

**How to avoid:** Make `field_sources_json` a first-class column in the row table and populate it during parser adaptation, even if Phase 1 starts with line-level evidence rather than character spans. [VERIFIED: .planning/phases/01-candidate-contract-foundation/01-CONTEXT.md] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py]

**Warning signs:** Two rows with the same normalized SKU cannot be explained back to different source lines during debugging. [VERIFIED: .planning/REQUIREMENTS.md]

### Pitfall 3: Replay Still Behaves Like Publish

**What goes wrong:** Exception save flows continue to use replay as a board-refresh mechanism, so replay remains a hidden fact publisher. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_web/app.py] [VERIFIED: wxbot/bookkeeping-platform/tests/test_webapp.py]

**Why it happens:** Current harvest-save logic resolves the exception and immediately replays the latest quote document into active rows when the exception is considered fully handled. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_web/app.py]

**How to avoid:** Redefine replay output as “new candidate run persisted” and update tests/UI payloads to report candidate counts and remaining lines instead of board rows. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_web/app.py]

**Warning signs:** `harvest-save` tests still assert board row counts after replay. [VERIFIED: wxbot/bookkeeping-platform/tests/test_webapp.py]

### Pitfall 4: Schema Additions Without Verifier Updates

**What goes wrong:** New columns or tables are added to `postgres_schema.sql` but not to `_verify_schema()`, or vice versa, causing runtime boot failure. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/database.py]

**Why it happens:** `BookkeepingDB` verifies expected table columns at startup and raises on mismatch. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/database.py]

**How to avoid:** Plan schema DDL, `_verify_schema()` updates, and `PostgresTestCase` schema application changes in one atomic unit. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/database.py] [VERIFIED: wxbot/bookkeeping-platform/tests/support/postgres_test_case.py]

**Warning signs:** `RuntimeError: PostgreSQL schema mismatch` during test or runtime startup. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/database.py]

## Code Examples

Verified patterns from the codebase and official docs:

### Candidate Bundle Serializer

```python
def row_to_record(document_id: int, row: QuoteCandidateRow) -> dict[str, object]:
    return {
        "quote_document_id": document_id,
        "row_ordinal": row.row_ordinal,
        "source_line": row.source_line,
        "source_line_index": row.source_line_index,
        "line_confidence": row.line_confidence,
        "normalized_sku_key": row.normalized_sku_key,
        "normalization_status": row.normalization_status,
        "row_publishable": row.row_publishable,
        "publishability_basis": "parser_prevalidation",
        "restriction_parse_status": row.restriction_parse_status,
        "card_type": row.card_type,
        "country_or_currency": row.country_or_currency,
        "amount_range": row.amount_range,
        "multiplier": row.multiplier,
        "form_factor": row.form_factor,
        "price": row.price,
        "quote_status": row.quote_status,
        "restriction_text": row.restriction_text,
        "field_sources_json": row.field_sources,
        "rejection_reasons_json": row.rejection_reasons,
    }
```

Source: repo dataclass usage in `contracts.py` and `quotes.py`, plus PostgreSQL `jsonb` recommendation for structured payloads. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/contracts.py] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py] [CITED: https://www.postgresql.org/docs/current/datatype-json.html]

### No-Fact-Mutation Runtime Guard

```python
def capture_from_message(...):
    candidate = parse_quote_message_to_candidate(...)
    persisted = self.db.record_quote_candidate_bundle(candidate)
    return {
        "captured": True,
        "document_id": persisted["quote_document_id"],
        "candidate_rows": persisted["candidate_row_count"],
        "exceptions": persisted["exception_count"],
        "mutated_active_facts": False,
    }
```

Source: replacement pattern for the current runtime path that now mutates `quote_price_rows` directly. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/runtime.py] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Parser output deactivates old rows and inserts new `quote_price_rows` immediately | Parser output persists candidate header/rows only; guarded publisher is a later phase | Roadmap defined on 2026-04-13 for Phase 1/3 split. [VERIFIED: .planning/ROADMAP.md] | Prevents runtime and replay from acting as hidden publishers. [VERIFIED: .planning/ROADMAP.md] |
| Replay proves success by refreshing board rows | Replay proves success by generating a new candidate run and preserving evidence | Required by Phase 1 boundary and replay exception goals. [VERIFIED: .planning/phases/01-candidate-contract-foundation/01-CONTEXT.md] | Makes replay safe before the guarded publisher exists. [VERIFIED: .planning/phases/01-candidate-contract-foundation/01-CONTEXT.md] |
| Message parse metadata lives in `message_parse_results` for finance/chat classification only | Quote candidate pipeline extends message-level metadata on `quote_documents` for quote-specific lineage and hypotheses | Recommended for this phase based on existing schema split. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/database.py] | Avoids overloading generic parse classification with quote-specific lifecycle state. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/database.py] |

**Deprecated/outdated:**

- Runtime or replay code that calls `deactivate_old_quotes_for_group()` before candidate custody exists is outdated for this phase and should be removed, not wrapped. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_web/app.py]
- Tests that use board mutation as the success condition for replay are outdated for this phase and must be rebaselined. [VERIFIED: wxbot/bookkeeping-platform/tests/test_webapp.py]

## Assumptions Log

All material claims in this research were verified from the local codebase, project planning documents, local environment probes, or official documentation. No unresolved `[ASSUMED]` claims remain.

## Open Questions (RESOLVED)

1. **Should Phase 1 expose a minimal read API for candidate bundles, or keep candidate inspection DB-only until Phase 7?**
   - Resolution: Keep Phase 1 inspection DB/query-helper only. Do not add a new HTTP inspection surface in this phase.
   - Why: Phase 1’s job is to establish candidate custody and persistence boundaries, not to expand operator UI scope. A DB/query helper is enough to support tests, replay verification, and later workbench phases without dragging web/API surface area into this foundational cut. [VERIFIED: .planning/ROADMAP.md] [VERIFIED: .planning/phases/01-candidate-contract-foundation/01-CONTEXT.md]

2. **How strict should the initial `field_sources_json` be?**
   - Resolution: Require line-level evidence plus raw field fragments in Phase 1. Do not require character offsets yet.
   - Why: This satisfies `EVID-01` and Phase 1 replay/debugging needs with minimum schema complexity, while keeping the structure extensible for a later tightening pass if line-level evidence proves insufficient. [VERIFIED: .planning/phases/01-candidate-contract-foundation/01-CONTEXT.md] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Project virtualenv Python | Running repo tests and `psycopg` imports | ✓ [VERIFIED: local env] | Python 3.14.3 [VERIFIED: local env] | None needed |
| `psycopg` in project `.venv` | `BookkeepingDB` runtime and PostgreSQL tests | ✓ [VERIFIED: local env] | 3.3.3 [VERIFIED: local env] | None needed |
| PostgreSQL server on `127.0.0.1:5432` | `PostgresTestCase`, runtime DB, and any integration verification | ✗ [VERIFIED: local env] | — | Provide `BOOKKEEPING_TEST_DSN` to a reachable DB or start local PostgreSQL |
| `psql` CLI | Manual schema/application troubleshooting | ✓ [VERIFIED: local env] | 16.13 [VERIFIED: local env] | Use application logs if CLI is unavailable |

**Missing dependencies with no fallback:**

- A reachable PostgreSQL server is required for any automated Phase 1 integration tests that use `PostgresTestCase`; without it, only static/code review work can proceed. [VERIFIED: wxbot/bookkeeping-platform/tests/support/postgres_test_case.py] [VERIFIED: local env]

**Missing dependencies with fallback:**

- None. [VERIFIED: local env]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | `unittest` under project `.venv` [VERIFIED: AGENTS.md] [VERIFIED: wxbot/bookkeeping-platform/tests/support/postgres_test_case.py] |
| Config file | none; tests use repo-local base classes and explicit commands [VERIFIED: wxbot/bookkeeping-platform/tests/support/postgres_test_case.py] |
| Quick run command | `cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend tests.test_runtime tests.test_webapp -v` [VERIFIED: AGENTS.md] [VERIFIED: wxbot/bookkeeping-platform/tests/support/postgres_test_case.py] |
| Full suite command | `cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest -v` [VERIFIED: AGENTS.md] [VERIFIED: wxbot/bookkeeping-platform/tests/support/postgres_test_case.py] |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EVID-01 | Candidate header and row retain raw message, source line, sender, group, and time | integration | `... -m unittest tests.test_postgres_backend -v` with new candidate persistence tests [VERIFIED: wxbot/bookkeeping-platform/tests/test_postgres_backend.py] | ❌ Wave 0 |
| CAND-01 | Runtime capture and replay create candidates without mutating `quote_price_rows` | integration | `... -m unittest tests.test_runtime tests.test_webapp -v` with new no-mutation assertions [VERIFIED: wxbot/bookkeeping-platform/tests/test_runtime.py] [VERIFIED: wxbot/bookkeeping-platform/tests/test_webapp.py] | ❌ Wave 0 |
| CAND-02 | Candidate header preserves parser lineage and snapshot hypothesis fields | integration | `... -m unittest tests.test_postgres_backend tests.test_runtime -v` with lineage assertions [VERIFIED: wxbot/bookkeeping-platform/tests/test_postgres_backend.py] [VERIFIED: wxbot/bookkeeping-platform/tests/test_runtime.py] | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** run the targeted `unittest` module(s) touched by the change. [VERIFIED: AGENTS.md]
- **Per wave merge:** run the quick Phase 1 suite across backend/runtime/webapp candidate tests. [VERIFIED: wxbot/bookkeeping-platform/tests/support/postgres_test_case.py]
- **Phase gate:** full `unittest` suite green against PostgreSQL before `/gsd-verify-work`. [VERIFIED: .planning/config.json]

### Wave 0 Gaps

- [ ] `tests/test_postgres_backend.py` — add candidate table schema and persistence contract coverage for `quote_documents` metadata + `quote_candidate_rows`. [VERIFIED: wxbot/bookkeeping-platform/tests/test_postgres_backend.py]
- [ ] `tests/test_runtime.py` — add runtime assertion that candidate capture produces no new active quote rows. [VERIFIED: wxbot/bookkeeping-platform/tests/test_runtime.py]
- [ ] `tests/test_webapp.py` — replace replay/harvest-save board-refresh expectations with candidate-only replay assertions. [VERIFIED: wxbot/bookkeeping-platform/tests/test_webapp.py]
- [ ] Local or remote PostgreSQL availability — current machine has no server responding on `127.0.0.1:5432`. [VERIFIED: local env]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no [VERIFIED: phase scope] | Existing runtime bearer token and quote admin password remain unchanged in this phase. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_web/app.py] |
| V3 Session Management | no [VERIFIED: phase scope] | WSGI app is stateless for these endpoints. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_web/app.py] |
| V4 Access Control | yes [VERIFIED: phase scope] | Candidate inspection or replay helpers must remain behind existing core token / admin password boundaries and must not expose a new write-bypass path. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_web/app.py] |
| V5 Input Validation | yes [VERIFIED: phase scope] | Candidate metadata and row fields should be normalized through explicit code paths and stored as structured values, not inferred later from free text. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py] |
| V6 Cryptography | yes [VERIFIED: phase scope] | Use standard SHA-256 from Python stdlib for message fingerprints; do not invent a custom hash. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/database.py] |

### Known Threat Patterns for This Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Parser or replay directly mutates active quote facts | Tampering / Elevation of Privilege | Remove runtime and replay writes to `quote_price_rows`; candidate-only persistence until guarded publisher exists. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_web/app.py] |
| Lossy evidence prevents operator from proving where a candidate came from | Repudiation | Persist immutable raw message, source line, sender, message time, and structured `field_sources_json`. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py] |
| Schema drift creates partial deployment where some nodes understand candidates and others do not | Tampering / Denial of Service | Update `postgres_schema.sql` and `_verify_schema()` atomically so mismatches fail fast. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/database.py] [VERIFIED: wxbot/bookkeeping-platform/sql/postgres_schema.sql] |
| Admin exception workflows silently become publish shortcuts | Elevation of Privilege | Keep result-save and harvest-save focused on template/candidate outcomes; do not let them refresh active facts in Phase 1. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_web/app.py] |

## Sources

### Primary (HIGH confidence)

- `.planning/phases/01-candidate-contract-foundation/01-CONTEXT.md` - locked decisions for candidate shape, evidence fields, and brownfield persistence boundary. [VERIFIED: .planning/phases/01-candidate-contract-foundation/01-CONTEXT.md]
- `.planning/REQUIREMENTS.md` - Phase 1 requirement targets `EVID-01`, `CAND-01`, and `CAND-02`. [VERIFIED: .planning/REQUIREMENTS.md]
- `.planning/ROADMAP.md` - phase boundary and success criteria for Candidate Contract Foundation. [VERIFIED: .planning/ROADMAP.md]
- `.planning/PROJECT.md` - validation-first scope and no-production-takeover rule. [VERIFIED: .planning/PROJECT.md]
- `AGENTS.md` - project operating rules, runtime entrypoint, PostgreSQL rule, and quote-wall safety posture. [VERIFIED: AGENTS.md]
- `graphify-out/GRAPH_REPORT.md` - architecture map showing database layer, quote parsing, and web route hotspots. [VERIFIED: graphify-out/GRAPH_REPORT.md]
- `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py` - current in-memory parsed types and runtime direct fact mutation path. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py]
- `wxbot/bookkeeping-platform/bookkeeping_core/database.py` - current quote schema, schema verifier, and board read model. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/database.py]
- `wxbot/bookkeeping-platform/bookkeeping_web/app.py` - replay helper and exception save behavior. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_web/app.py]
- `wxbot/bookkeeping-platform/bookkeeping_core/runtime.py` - runtime calls quote capture before finance parsing. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/runtime.py]
- `wxbot/bookkeeping-platform/tests/support/postgres_test_case.py` - PostgreSQL testing model and DSN requirements. [VERIFIED: wxbot/bookkeeping-platform/tests/support/postgres_test_case.py]
- `wxbot/bookkeeping-platform/tests/test_webapp.py` - current tests that still expect replay-driven board refresh. [VERIFIED: wxbot/bookkeeping-platform/tests/test_webapp.py]
- `https://www.postgresql.org/docs/current/datatype-json.html` - official `jsonb` guidance and indexing rationale. [CITED: https://www.postgresql.org/docs/current/datatype-json.html]
- `https://www.postgresql.org/docs/current/sql-altertable.html` - official `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` semantics for additive schema rollout. [CITED: https://www.postgresql.org/docs/current/sql-altertable.html]
- `https://docs.python.org/3/library/typing.html` - official `TypedDict` runtime semantics. [CITED: https://docs.python.org/3/library/typing.html]

### Secondary (MEDIUM confidence)

- Local environment probes for Python, `psql`, `.venv`, `psycopg`, and `pg_isready`. [VERIFIED: local env]

### Tertiary (LOW confidence)

- None.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - Existing repo stack, environment probes, and official PostgreSQL/Python docs all agree. [VERIFIED: local env] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/database.py] [CITED: https://www.postgresql.org/docs/current/datatype-json.html]
- Architecture: HIGH - The runtime write path, replay write path, schema verifier, and roadmap boundary are all directly visible in the code and planning docs. [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_core/quotes.py] [VERIFIED: wxbot/bookkeeping-platform/bookkeeping_web/app.py] [VERIFIED: .planning/ROADMAP.md]
- Pitfalls: HIGH - Each listed pitfall is backed by a current code path, current test, or explicit project rule. [VERIFIED: wxbot/bookkeeping-platform/tests/test_webapp.py] [VERIFIED: AGENTS.md]

**Research date:** 2026-04-14
**Valid until:** 2026-05-14 for repo-internal findings; re-check environment availability before execution.
