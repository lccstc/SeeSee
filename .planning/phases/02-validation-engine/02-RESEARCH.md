---
phase: 02-validation-engine
researched: 2026-04-14
status: ready
confidence: high
source_context: requirements-plus-phase1
---

# Phase 02: Validation Engine - Research

**Scope note:** No dedicated `02-CONTEXT.md` exists yet. This research is based on `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, Phase 01 verification, and the current brownfield code paths.

## Summary

Phase 01 already created a durable candidate boundary, but the repo still has no formal validator layer. Today, candidate rows carry parser-side hints such as `row_publishable`, `normalization_status`, `restriction_parse_status`, and `rejection_reasons`, but those fields are still parser output, not system custody. There is no persisted validation run, no stable rejection taxonomy, and no durable `publishable_rows` surface for later publisher work.

The safest Phase 02 cut is:

1. Keep candidate rows immutable as parser evidence.
2. Add a separate validation layer with its own run header and row decisions.
3. Run validation automatically after candidate persistence in both runtime and replay paths.
4. Persist structured row outcomes so later phases can consume `publishable_rows` without re-deriving them ad hoc.

## Current Brownfield Findings

### Candidate evidence already exists

- `bookkeeping_core/quote_candidates.py` defines a stable message-level candidate and row-level candidate contract.
- `bookkeeping_core/database.py` persists those records into `quote_documents` and `quote_candidate_rows`.
- `bookkeeping_core/quotes.py` already computes parser-side hints:
  - `normalization_status`
  - `row_publishable`
  - `publishability_basis="parser_prevalidation"`
  - `restriction_parse_status`
  - parser-side `rejection_reasons`

This means Phase 02 does not need to rediscover row structure. It needs to formalize custody and separate parser hints from validator verdicts.

### No validator persistence exists yet

- There is no `quote_validation_runs` or equivalent table.
- There is no stable API for “latest validation result for quote_document_id”.
- Runtime and replay currently stop after candidate persistence plus exception recording.

Without a persisted validator layer, Phase 03 would be forced to either:

- trust parser-side `row_publishable`, which violates the project rules, or
- recompute validation inline during publish, which would make replay, comparison, and debugging much weaker.

## Recommended Design

### Decision 1: candidate rows remain immutable evidence

Do **not** overwrite `quote_candidate_rows` with final validator decisions.

Reason:

- Candidate rows represent parser output and source evidence.
- Validation must be rerunnable as rules evolve.
- Replay comparison later needs to distinguish:
  - what the parser proposed
  - what the validator allowed
  - what the publisher finally used

If validator state is written back into candidate rows, those layers get blurred immediately.

### Decision 2: persist validation as run header + row decisions

Recommended additive schema:

```sql
CREATE TABLE quote_validation_runs (
  id BIGSERIAL PRIMARY KEY,
  quote_document_id BIGINT NOT NULL REFERENCES quote_documents(id) ON DELETE CASCADE,
  validator_version TEXT NOT NULL,
  run_kind TEXT NOT NULL DEFAULT 'runtime',
  message_decision TEXT NOT NULL,
  validation_status TEXT NOT NULL,
  candidate_row_count INTEGER NOT NULL DEFAULT 0,
  publishable_row_count INTEGER NOT NULL DEFAULT 0,
  rejected_row_count INTEGER NOT NULL DEFAULT 0,
  held_row_count INTEGER NOT NULL DEFAULT 0,
  summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE quote_validation_row_results (
  id BIGSERIAL PRIMARY KEY,
  validation_run_id BIGINT NOT NULL REFERENCES quote_validation_runs(id) ON DELETE CASCADE,
  quote_candidate_row_id BIGINT NOT NULL REFERENCES quote_candidate_rows(id) ON DELETE CASCADE,
  row_ordinal INTEGER NOT NULL,
  schema_status TEXT NOT NULL,
  business_status TEXT NOT NULL,
  final_decision TEXT NOT NULL,
  decision_basis TEXT NOT NULL,
  rejection_reasons_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  hold_reasons_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (validation_run_id, quote_candidate_row_id)
);
```

Why this shape:

- `quote_validation_runs` gives one durable verdict per message per validation execution.
- `quote_validation_row_results` makes mixed outcomes first-class: one message can produce publishable, rejected, and held rows together.
- `quote_candidate_row_id` preserves direct lineage back to source evidence.

### Decision 3: validation is staged, not monolithic

Recommended row pipeline:

1. `schema` stage
   - required normalized fields exist
   - `normalized_sku_key` is non-empty
   - `source_line` exists
   - `price` is numeric and positive
2. `business` stage
   - `quote_status` must be `active`
   - low confidence becomes `held`, not auto-publishable
   - partial normalization becomes `held`
   - ambiguous restriction parsing becomes `held`
   - duplicate normalized SKU in the same message becomes `held`
3. `decision` stage
   - `publishable`
   - `rejected`
   - `held`

This matches the project rule that accuracy outranks coverage. Unclear rows should drift toward `held`, not toward inferred publishability.

### Decision 4: parser prevalidation becomes input, not verdict

Phase 01 `row_publishable` and parser-side `rejection_reasons` should remain available as upstream evidence, but they must be treated as advisory. Phase 02 validator output becomes the formal system decision.

Recommended rule:

- parser hints may inform validator reasoning
- parser hints may not define final `publishable_rows`

### Decision 5: validation should run automatically after candidate persistence

Phase 02 should wire validation into:

- `QuoteCaptureService.capture_from_message(...)`
- replay helper `_replay_latest_quote_document_with_current_template(...)`

Reason:

- every candidate document should have a current validator verdict
- later publisher work should consume persisted validation results, not opportunistic inline recomputation

## Recommended Taxonomy

Stable codes should be machine-readable and persist in JSON, for example:

- `schema_missing_card_type`
- `schema_missing_country_or_currency`
- `schema_invalid_amount_range`
- `schema_invalid_price`
- `business_quote_status_not_active`
- `business_low_confidence_hold`
- `business_partial_normalization_hold`
- `business_ambiguous_restriction_hold`
- `business_duplicate_sku_in_message_hold`
- `message_no_candidate_rows`

The important part is stability, not perfect naming. Phase 03+ will depend on these codes.

## Integration Guidance

### Runtime path

After `record_quote_candidate_bundle(candidate=...)` returns `quote_document_id`, runtime should:

1. load persisted candidate rows for that document
2. execute validator
3. persist one validation run plus row decisions
4. return validation summary metadata without mutating active facts

### Replay path

Replay should do the same, but the persisted validation run should retain replay lineage through the original quote document.

### Web/API surface

Phase 02 does **not** need a user-facing validation workbench yet. Query helpers in `database.py` are enough. Operator UI belongs to Phase 07.

## Anti-Patterns To Avoid

- Writing final validator decisions back into `quote_candidate_rows`
- Reusing parser-side `row_publishable` as the authoritative publish decision
- Waiting until Phase 03 to persist validation, because that would force guarded publisher work to invent its own result model
- Turning low-confidence or ambiguous rows into rejections by default; those should usually be `held`
- Letting replay validate differently from runtime

## Planning Consequence

Phase 02 should be split into three plans:

1. validator contract, persistence schema, and durable rejection taxonomy
2. schema validation plus automatic runtime/replay validation execution
3. business-rule evaluation plus durable `publishable_rows` separation helpers

