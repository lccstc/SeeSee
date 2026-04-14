# Phase 04: Snapshot / Delta Semantics - Research

**Researched:** 2026-04-15  
**Status:** Complete

## Executive Summary

Local codebase inspection confirms that Phase 04 is genuinely unimplemented today:

- candidate documents persist `snapshot_hypothesis`, but runtime hard-codes it to `unresolved`
- the validator has message-level decisions, but those are about publishability, not snapshot semantics
- the guarded publisher only understands `validation_only` and a replacement-style publish mode
- gold corpus fixtures already carry real-sample `full_snapshot` / `delta_update` / `unresolved` judgments

The planning implication is clear: Phase 04 should not revisit parser breadth. It should introduce a durable snapshot decision surface, teach the guarded publisher to distinguish `delta_update` from confirmed `full_snapshot`, and add a minimal human confirmation gate for v1.

## Verified Findings

| Area | Finding | Evidence |
| --- | --- | --- |
| Candidate metadata | `QuoteCandidateMessage` already stores `snapshot_hypothesis` and `snapshot_hypothesis_reason` | `wxbot/bookkeeping-platform/bookkeeping_core/quote_candidates.py` |
| Runtime behavior | Quote capture currently stamps both strict-template and missing-template messages as `snapshot_hypothesis=\"unresolved\"`, `snapshot_hypothesis_reason=\"phase1-default\"` | `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py` |
| Publisher behavior | The guarded publisher currently only recognizes `validation_only` and `replace_group_active_rows` | `wxbot/bookkeeping-platform/bookkeeping_core/quote_publisher.py` |
| Validation behavior | `message_decision` is about validation outcome (`publishable_rows_available`, `mixed_outcome`, `no_publish`), not snapshot scope | `wxbot/bookkeeping-platform/bookkeeping_core/quote_validation.py` |
| Corpus evidence | Gold fixtures already encode real message-level judgments and reasons for `full_snapshot`, `delta_update`, and `unresolved` | `wxbot/bookkeeping-platform/tests/fixtures/quote_exception_corpus/gold_top8.json` |
| Prior planning | Phase 01 and Phase 03 both explicitly defer real snapshot execution semantics to Phase 04 | `.planning/phases/01-candidate-contract-foundation/01-CONTEXT.md`, `.planning/phases/03-fact-protection-publisher/03-CONTEXT.md` |

## Requirement Mapping

| Requirement | Implication for Phase 04 |
| --- | --- |
| `SNAP-01` | Need a durable message-level snapshot decision model, not just candidate metadata |
| `SNAP-02` | Unresolved decisions must route to delta-safe publisher behavior |
| `SNAP-03` | Publisher must only inactivate unseen prior SKUs when a message is confirmed `full_snapshot` |
| `OPS-02` | Need a minimal operator confirmation flow in v1 that persists the decision without becoming a publish side door |

## Design Conclusions

### 1. Snapshot semantics need their own durable surface

Reusing `snapshot_hypothesis` alone is not enough. That field is candidate evidence and currently defaults to `unresolved`. Phase 04 needs a durable, publish-facing surface that can hold:

- system hypothesis
- reasoning/evidence
- current resolved decision
- optional operator confirmation lineage

This can be an additive table or additive document-linked surface, but it must be queryable by the guarded publisher without re-deriving semantics ad hoc.

### 2. Publisher behavior must branch on snapshot decision, not on message length or parser shape

Phase 03 established one guarded publisher. Phase 04 should keep that ownership and make publish behavior explicit:

- `delta_update`: upsert publishable rows only; do not deactivate unseen group rows
- `full_snapshot_confirmed`: upsert publishable rows and inactivate previously active rows absent from this confirmed snapshot
- `unresolved`: behave as `delta_update` by default

This keeps “default safe” semantics structural.

### 3. Human confirmation should stay narrow in v1

The repo does not yet have a dedicated workbench for candidate/validator/publish evidence. That is Phase 07. Phase 04 therefore only needs a minimal operator gate:

- inspect one message’s current snapshot hypothesis
- confirm or override as `full_snapshot` / `delta_update`
- persist who/when/why
- do **not** publish automatically as a side effect

### 4. Gold fixtures are the right regression substrate

Because real message-level judgments already exist in the corpus, Phase 04 should not plan around synthetic examples alone. Planning and tests should explicitly use:

- full-board handoff messages
- explicit “单独更新” delta cases
- unresolved/noisy messages

so the classification and publisher semantics are tied to live business patterns.

## Risks and Countermeasures

| Risk | Why it matters | Countermeasure |
| --- | --- | --- |
| Reusing replacement-style publish mode as implicit full snapshot | Could inactivate unseen SKUs on ambiguous messages | Require explicit confirmed full-snapshot decision before any absent-row inactivation |
| Conflating validator `message_decision` with snapshot semantics | Validation outcome and snapshot scope answer different questions | Keep snapshot decision surface separate from validation result surface |
| Human confirmation route becomes a hidden publish path | Would re-open a side door around guarded custody | Confirmation endpoint may only persist decision metadata; guarded publisher remains the only mutation path |
| Overfitting snapshot classification to prompt-like heuristics | Violates system-owned semantics | Favor deterministic message cues plus corpus-backed tests; unresolved stays delta-safe |

## Recommended Plan Shape

Phase 04 should be planned in three waves:

1. **Decision model + persistence**
   Add a durable snapshot decision surface and deterministic hypothesis scaffolding.
2. **Publisher semantics**
   Teach the guarded publisher to implement delta-safe default behavior and confirmed-full inactivation.
3. **v1 operator confirmation**
   Add a minimal confirmation flow that records human decisions without granting direct publish authority.

## Open Questions Resolved During Research

- **Should Phase 04 replace the validator’s `message_decision`?** No. Validation and snapshot semantics remain separate surfaces.
- **Should runtime start publishing by default in this phase?** No. Validation-first posture remains; Phase 04 prepares semantics, not default production handoff.
- **Do we already have evidence for message-level decisions?** Yes. Gold corpus fixtures provide real-sample decisions and reasons.

## Research Completeness

All findings in this note were verified from the local codebase and planning artifacts. No external browsing was needed.

---

*Phase: 04-snapshot-delta-semantics*
*Research completed: 2026-04-15*
