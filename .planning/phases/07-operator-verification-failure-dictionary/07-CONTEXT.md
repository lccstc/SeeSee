# Phase 07: Operator Verification & Failure Dictionary - Context

**Gathered:** 2026-04-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 07 exists to make the current quote pipeline explain itself at message level.

By the end of Phase 06, the system can:

- ingest raw group messages into candidate bundles
- split validation outcomes into `publishable`, `held`, `rejected`, and `mixed_outcome`
- route failures into `repair_case`
- run bounded auto-remediation
- keep active facts behind one guarded publisher
- record snapshot semantics without letting operator confirmation mutate the wall directly

What it still cannot do cleanly is let an operator answer the practical questions:

- For this exact message, which candidate rows existed?
- Which rows were published, rejected, held, or left untouched, and why?
- What snapshot decision applied to this message?
- Did the publisher no-op, delta-upsert, or confirmed-full apply?
- When remediation failed three times, what is the reusable repair knowledge future agents should consult first?

This phase addresses that gap.

The goal is not to widen authority. The goal is to expose message-level evidence and turn repair-case history into a searchable failure dictionary / repair lexicon. The workbench must remain proof-oriented. It may explain publisher decisions, but it must not create a bypass around validator or guarded publisher custody.

</domain>

<decisions>
## Implementation Decisions

### Operator workbench is read-first, not authority-first
- **D-01:** Phase 07 adds inspection and debugging evidence, not new publish authority.
- **D-02:** The workbench may show candidate rows, validation rows, snapshot decisions, repair status, and publish semantics, but it must not mutate `quote_price_rows` directly.
- **D-03:** Existing mutation endpoints (`harvest-save`, snapshot confirm, guarded publish paths) keep their current custody boundaries; Phase 07 must not smuggle side-effecting writes into “view evidence” APIs.

### Message-level evidence is the primary debugging unit
- **D-04:** The operator evidence model is message-centric: one quote document should expose message metadata, candidate rows, validation decisions, snapshot semantics, repair status, and publish intent in one coherent payload.
- **D-05:** Evidence must distinguish row classes explicitly: `candidate`, `publishable`, `held`, `rejected`, and “untouched because publish mode did not authorize mutation”.
- **D-06:** Publish evidence should explain both action and non-action. “No change” is a first-class result, not a missing state.

### Publish evidence must remain grounded in system lineage
- **D-07:** Publish decision evidence must derive from validator-held rows and snapshot semantics, not from parser claims or UI guesses.
- **D-08:** If there is no durable publish-attempt log yet, Phase 07 may add an additive publish-evidence surface, but it must preserve the same validator lineage and guarded-publisher custody introduced in Phase 03/04.
- **D-09:** Operator wording must stay proof-only and factual: explain why rows were or were not eligible, without implying that confirmation or inspection itself changed active facts.

### Failure dictionary is a project knowledge asset, not a log dump
- **D-10:** Repair-case history remains the case file; the failure dictionary is the indexed handbook built from repeated case patterns, known-good fixes, and explicit “do not do” rules.
- **D-11:** Failure dictionary entries must be structured enough that a fresh main agent or subagent can query them without prior chat context.
- **D-12:** The dictionary must preserve negative knowledge, including forbidden fixes such as:
  - auto-remediation must not expand skeletons in an existing group profile by default
  - `横白卡图 / 整卡卡密` must not be absorbed as `country_or_currency`
  - validator / publisher custody must not be bypassed

### Brownfield fit matters more than elegance
- **D-13:** Phase 07 should reuse existing durable surfaces (`quote_candidate_rows`, `quote_validation_runs`, `quote_validation_row_results`, `quote_snapshot_decisions`, `quote_repair_cases`, `quote_repair_case_attempts`) before inventing parallel stores.
- **D-14:** If a new additive table is needed for publish evidence or dictionary entries, it must be narrow, auditable, and justified by a concrete debugging gap.
- **D-15:** The web workbench should layer on top of `bookkeeping_web/app.py` + `pages.py`, which already expose exceptions and repair summaries, instead of creating a separate app.

### Explicit non-goals
- **D-16:** Phase 07 does not replace the production publish flow with shadow-mode gating; that remains Phase 08.
- **D-17:** Phase 07 does not improve parsing coverage directly; it improves observability and repair knowledge.
- **D-18:** Phase 07 does not weaken any guarded publisher or snapshot confirmation protections.

### the agent's Discretion
- Exact payload shape for message-level verification evidence, provided it cleanly links candidate, validation, snapshot, repair, and publish semantics
- Exact storage shape for failure dictionary entries, provided it stays searchable, structured, and additive
- Exact page placement for the workbench, provided it is easy for operators to inspect one message end-to-end

</decisions>

<specifics>
## Specific Ideas

- A dedicated evidence builder in `bookkeeping_web/app.py` is probably cleaner than spreading ad hoc JSON assembly across several routes.
- The verification payload should probably be addressable by `quote_document_id`, because that is the stable join point across candidate rows, validation runs, snapshot decisions, repair cases, and guarded publish lineage.
- A compact “publish reasoning” object may be enough for v1 even if there is not yet a full `quote_publish_attempts` history table.
- The failure dictionary can start with deterministic indexing of repeated repair cases, approved fixtures, and explicit hard rules already written in `.planning/research/FAILURE-DICTIONARY.md`.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product and governance
- `.planning/PROJECT.md` — hard rules for proof-only operator tooling and the failure dictionary insight
- `.planning/REQUIREMENTS.md` — `EVID-02`, `OPS-01`, `INDU-03`
- `.planning/ROADMAP.md` — Phase 07 goal, dependency, and success criteria
- `.planning/STATE.md` — current focus after Phase 04 completion
- `.planning/research/FAILURE-DICTIONARY.md` — the newly captured lexicon concept and minimum entry shape
- `AGENTS.md` — repo-level constraints, especially no bypass around validator / publisher and “not a万能解析器”

### Prior phase outputs
- `.planning/phases/03-fact-protection-publisher/03-CONTEXT.md` — publish custody and no-op semantics already established
- `.planning/phases/03-fact-protection-publisher/03-VERIFICATION.md` — guarded publisher evidence remains Phase 07 scope
- `.planning/phases/04-snapshot-delta-semantics/04-CONTEXT.md` — Phase 04 intentionally left rich operator debugging UI to Phase 07
- `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md` — repair-case linkage is already durable
- `.planning/phases/06-constrained-auto-remediation-loop/06-VERIFICATION.md` — remediation attempts, escalation, and known blocked patterns now exist and should feed the dictionary

### Existing implementation surfaces
- `graphify-out/GRAPH_REPORT.md` — confirms the database layer, web routes, and quote parsing communities are the dominant integration nodes for this phase
- `wxbot/bookkeeping-platform/bookkeeping_core/database.py` — current candidate / validation / exception / repair surfaces and likely home for additive read helpers
- `wxbot/bookkeeping-platform/bookkeeping_web/app.py` — existing exception endpoints and route layer
- `wxbot/bookkeeping-platform/bookkeeping_web/pages.py` — quotes page workbench rendering and current operator actions
- `wxbot/bookkeeping-platform/bookkeeping_core/quote_publisher.py` — publish mode semantics and guarded no-op behavior
- `wxbot/bookkeeping-platform/bookkeeping_core/quote_snapshot.py` — message-level snapshot decision contract
- `wxbot/bookkeeping-platform/tests/test_postgres_backend.py`
- `wxbot/bookkeeping-platform/tests/test_runtime.py`
- `wxbot/bookkeeping-platform/tests/test_webapp.py`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `quote_candidate_rows` already provide row-level candidate evidence.
- `quote_validation_runs` and `quote_validation_row_results` already provide durable row decisions.
- `quote_snapshot_decisions` already provide message-level snapshot lineage.
- `quote_repair_cases` and `quote_repair_case_attempts` already provide repair history, escalation state, and known blocked outcomes.
- The quotes page already exposes open exceptions and repair summaries, so the workbench can extend an established operator surface instead of starting from zero.

### Established Patterns
- Brownfield-safe additive schema is preferred over rewriting existing fact tables.
- Proof-only UI wording matters and is already guarded by tests.
- High-risk state transitions belong in the core database layer and deterministic web handlers, not in prompts.

### Integration Points
- Add read helpers in `BookkeepingDB` for message-level evidence aggregation
- Add narrow JSON endpoints in `bookkeeping_web/app.py`
- Extend the existing quotes page workbench in `bookkeeping_web/pages.py`
- Add lexicon generation / lookup support from repair cases, fixtures, and known-good fix references

### Risk Hotspots
- A poorly designed workbench could accidentally imply operator inspection itself caused publication.
- A naive evidence payload could rely on parser claims rather than validator-held rows.
- A naive lexicon builder could turn repair logs into an unbounded blob instead of a searchable handbook.
- If publish evidence is inferred sloppily, the operator may misread “untouched due to delta/no-op” as “parser failed”.

</code_context>

<deferred>
## Deferred Ideas

- Full production shadow-gate comparison remains Phase 08
- Automatic publish-attempt analytics dashboards remain later work
- Rich cross-group lexicon clustering beyond deterministic rule families can wait until v2

</deferred>

---

*Phase: 07-operator-verification-failure-dictionary*
*Context gathered: 2026-04-15*
