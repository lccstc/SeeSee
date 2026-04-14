# Phase 07: Operator Verification & Failure Dictionary - Research

**Date:** 2026-04-15  
**Status:** Complete

## Research Summary

Phase 07 should not invent a second pipeline. The codebase already has almost every durable ingredient needed to explain one message end-to-end:

- candidate rows
- validation runs and row decisions
- snapshot decisions
- repair-case summaries and attempts
- guarded publish semantics

The missing piece is not raw data. It is a coherent operator-facing evidence surface and a project-level failure dictionary.

The best brownfield move is:

1. add message-level evidence read helpers keyed by `quote_document_id`
2. expose them through narrow web APIs
3. render a focused workbench in the quotes page
4. build a searchable failure dictionary from repair cases, fixtures, and known-good fixes

This keeps Phase 07 aligned with current architecture instead of creating a separate diagnostic subsystem.

## What Already Exists

### Durable evidence already in PostgreSQL

`BookkeepingDB` already persists:

- `quote_documents`
- `quote_candidate_rows`
- `quote_validation_runs`
- `quote_validation_row_results`
- `quote_snapshot_decisions`
- `quote_repair_cases`
- `quote_repair_case_attempts`

The existing APIs already surface exceptions and compact repair summaries. This means Phase 07 should mostly assemble and clarify evidence, not reconstruct it from logs.

### Publisher custody already exists

Phase 03 made the guarded publisher the only place allowed to mutate `quote_price_rows`.  
Phase 04 added snapshot semantics and proof-only operator confirmation.

Therefore Phase 07 can safely explain:

- why rows were publishable or not
- which snapshot semantics applied
- whether the publisher would no-op, delta-upsert, or confirmed-full apply

without introducing a new mutation path.

### Failure dictionary concept is already captured

The lexicon concept is already documented in `.planning/research/FAILURE-DICTIONARY.md`.  
That document gives the minimal entry shape and the key distinction:

- repair case = case file
- failure dictionary = handbook

Phase 07 should implement the first searchable version of that handbook.

## Architectural Read from Graphify

`graphify-out/GRAPH_REPORT.md` highlights exactly the surfaces this phase should sit on:

- database layer is a core “god node”
- web route layer is a major community
- quote parsing / template engine / runtime tests are already isolated communities

This supports a layered Phase 07 implementation:

- read aggregation in `bookkeeping_core/database.py`
- route + payload assembly in `bookkeeping_web/app.py`
- operator UI in `bookkeeping_web/pages.py`
- regressions in `tests.test_postgres_backend` and `tests.test_webapp`

This is consistent with repo architecture instead of crossing boundaries.

## Decision: Do We Need A `quote_publish_attempts` Table Now?

**Conclusion:** probably not for v1 of Phase 07.

Reasoning:

- Phase 03/04 already established publish semantics and guarded no-op logic
- The operator’s immediate need is explanatory evidence, not a historical analytics warehouse
- A derived “publish reasoning” object can explain:
  - validation status
  - row-level final decisions
  - snapshot mode
  - expected guarded publish behavior

That is enough to satisfy `EVID-02` without committing the phase to a new high-cardinality event log.

If a durable publish-attempt history proves necessary later, it can be added after the operator workbench is validated.

## Recommended Data Model For Phase 07

### Message-level verification payload

Recommended API input:

- `quote_document_id`

Recommended payload sections:

- `message`
  - chat, sender, message time, parser info, repair status
- `snapshot`
  - system hypothesis, resolved decision, source, confirmer, proof wording
- `candidates`
  - all candidate rows with key evidence fields
- `validation`
  - latest validation run summary
  - row results grouped by `publishable`, `held`, `rejected`
- `publish_reasoning`
  - expected guarded behavior:
    - `validation_only`
    - `delta_safe_upsert_only`
    - `confirmed_full_snapshot_apply`
    - `no_publish`
  - explanation of why rows were untouched
- `repair`
  - repair-case summary
  - last attempts and blocked reasons

### Failure dictionary entry

Recommended durable fields for v1:

- `entry_key`
- `failure_code`
- `symptom`
- `trigger_pattern`
- `root_cause`
- `preferred_scope`
- `do_first`
- `do_not_do`
- `known_good_fix`
- `replay_fixture_refs_json`
- `test_refs_json`
- `related_groups_json`
- `frequency`
- `first_seen_at`
- `last_seen_at`
- `source_case_ids_json`

This can be additive and small enough to search from web and future agents.

## Workbench UX Guidance

The operator view should answer one question quickly:

> “Why did this message not become the exact wall result I expected?”

So the workbench should prioritize:

1. row class separation
   - publishable
   - held
   - rejected
   - untouched due to snapshot/publisher semantics
2. short, explicit reason labels
3. repair-case linkage
4. proof-only wording

It should avoid:

- giant raw JSON dumps by default
- language that sounds like “already上墙”
- parser-centric language that hides validator or publisher decisions

## Risks and Mitigations

### Risk 1: Evidence surface accidentally becomes a side door
Mitigation:
- make evidence APIs read-only
- keep snapshot confirm and other stateful actions on existing guarded endpoints

### Risk 2: Lexicon becomes a garbage pile
Mitigation:
- store structured entries, not raw conversation dumps
- aggregate repeated cases under one entry
- only keep references to cases and fixtures, not full raw text duplication

### Risk 3: Operators confuse parser failure with publish no-op
Mitigation:
- include explicit publish reasoning object
- show “untouched because delta/no publish/blocked” separately from “rejected by validator”

### Risk 4: Fresh agents still need session memory
Mitigation:
- add searchable dictionary lookup by failure code, trigger pattern, and related group
- include forbidden fixes and known-good fixes in every entry

## Recommended Plan Structure

- `07-01`: build message-level evidence payloads and read helpers
- `07-02`: expose web workbench and proof-oriented operator inspection UI
- `07-03`: build searchable failure dictionary / repair lexicon and wire it into the workbench

## Open Questions Resolved

1. **Should Phase 07 add new publish authority?**  
   No. It must remain read/proof-oriented.

2. **Should Phase 07 depend on brand-new runtime mutation flows?**  
   No. It should explain existing state, not add new authority.

3. **Should the failure dictionary be a markdown note only?**  
   No. The markdown research note remains a seed, but Phase 07 needs a searchable structured implementation.

## Final Recommendation

Implement Phase 07 as a read-first diagnostic layer plus structured repair handbook:

- one message-level evidence payload
- one operator workbench
- one searchable failure dictionary

This satisfies the product need without widening risk.
