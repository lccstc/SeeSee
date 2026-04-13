# Phase 1: Candidate Contract Foundation - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 only establishes the boundary between raw message input, candidate generation, evidence capture, and any later fact mutation. It does not try to finish the whole guarded publisher redesign in one shot. Its job is to make `message-level parse result + row candidates` the mandatory intermediate contract so later validation, fact protection, snapshot semantics, replay, and exception handling all build on the same object model.

</domain>

<decisions>
## Implementation Decisions

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

### the agent's Discretion
- Exact table layout, naming, and whether candidate persistence is one table plus child rows or multiple focused tables
- Exact fingerprint algorithm and evidence serialization format
- How to adapt existing parser outputs into the new contract with the least risky migration path

</decisions>

<specifics>
## Specific Ideas

- The project’s core rule for quote-wall correctness remains: `宁可不上墙，不可误上墙`.
- Message-level states must be able to express `parsed`, `partial`, `failed`, and `ambiguous`, because “some rows extracted” and “safe to publish” are different questions.
- The candidate contract should become the common language across runtime parsing, replay, exception review, and later validator / publisher stages.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product and governance
- `.planning/PROJECT.md` — Hard rules for candidate-only parsing, fact protection, exception handling, replay, and v1 shadow-mode intent
- `.planning/REQUIREMENTS.md` — Phase-linked requirements, especially `EVID-01`, `CAND-01`, and `CAND-02`
- `.planning/ROADMAP.md` — Phase 1 boundary and success criteria
- `AGENTS.md` — Repo-level operating rules, quote-wall risk posture, and brownfield constraints

### Current quote-wall implementation
- `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py` — Current capture flow already computes `publishable_rows` but still deactivates and upserts directly inside quote capture
- `wxbot/bookkeeping-platform/bookkeeping_core/database.py` — Current persistence API includes `record_quote_document`, `deactivate_old_quotes_for_group`, and `upsert_quote_price_row_with_history`
- `wxbot/bookkeeping-platform/bookkeeping_web/app.py` — Replay path currently reparses exceptions and can still mutate active rows directly

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `QuoteCaptureService` in `bookkeeping_core/quotes.py`: already has a parser result shape, exception recording flow, and a preliminary `publishable_rows` concept that can be adapted into the formal candidate contract
- `record_quote_document(...)` in `bookkeeping_core/database.py`: a likely anchor for message-level evidence persistence, though it is currently not rich enough for full candidate semantics
- Existing exception recording APIs: useful for preserving failure evidence while the contract is introduced

### Established Patterns
- The system already records message-level parse metadata elsewhere through `record_parse_result(...)`; Phase 1 can align quote-wall candidate records with that broader “message outcome is explicit” pattern
- Quote-wall parsing currently mixes parse, confidence filtering, exception recording, deactivation, and fact upsert in one service path; the phase must separate these concerns without destabilizing unrelated finance flows

### Integration Points
- Runtime quote ingestion in `bookkeeping_core/quotes.py`
- Exception replay flow in `bookkeeping_web/app.py`
- Quote persistence boundary in `bookkeeping_core/database.py`

### Risk Hotspots
- `deactivate_old_quotes_for_group(...)` currently runs before durable publication safeguards are explicit, which is incompatible with the future default-safe `delta_update` posture
- Replay currently has fact-mutation capability, so Phase 1 must include replay in the candidate boundary instead of only fixing the runtime path

</code_context>

<deferred>
## Deferred Ideas

- Final single guarded publisher ownership and bypass removal details belong to Phase 3
- Full `full_snapshot` / `delta_update` publish semantics belong to Phase 4, though Phase 1 must already carry the message-level hypothesis fields needed for that work

</deferred>

---

*Phase: 01-candidate-contract-foundation*
*Context gathered: 2026-04-13*
