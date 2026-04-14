# Phase 04: Snapshot / Delta Semantics - Context

**Gathered:** 2026-04-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 04 exists to turn message-level snapshot semantics from passive metadata into guarded publish behavior. Phase 01 already gave every candidate document `snapshot_hypothesis` fields. Phase 02.1 already captured gold fixtures with `message_decision` values such as `full_snapshot`, `delta_update`, and `unresolved`. Phase 03 then put one guarded publisher in charge of active quote mutation. This phase connects those three pieces.

The goal is not “smarter parsing”. The goal is to ensure the publisher treats message scope safely:

- unresolved messages default to `delta_update`
- only confirmed `full_snapshot` may inactivate unseen prior SKUs
- v1 keeps a human confirmation gate for disputed cases

This phase does not hand default production authority to the pipeline, does not replace the operator verification workbench planned for Phase 07, and does not widen publisher custody beyond the guarded core path created in Phase 03.

</domain>

<decisions>
## Implementation Decisions

### Snapshot semantics are message-level publish semantics
- **D-01:** `full_snapshot`, `delta_update`, and `unresolved` are message-level decisions, not row-level flags.
- **D-02:** The system must carry both a system hypothesis and, when applicable, a human-confirmed decision with explicit lineage.
- **D-03:** Candidate-level `snapshot_hypothesis` remains evidence; publish execution must consume a resolved snapshot decision surface rather than infer silently inside the publisher.

### Safe default is always delta
- **D-04:** If classification is unresolved, ambiguous, or unconfirmed, the publisher must behave as `delta_update`.
- **D-05:** `delta_update` means “upsert only the publishable rows from this message; do not infer that absent SKUs should disappear.”
- **D-06:** `full_snapshot` is the only mode allowed to inactivate unseen prior SKUs, and only after explicit confirmation.

### Phase 04 must refine publisher behavior without re-opening custody
- **D-07:** Phase 03’s guarded publisher remains the only place that may mutate `quote_price_rows`.
- **D-08:** Phase 04 may add snapshot-aware publish modes or decision inputs, but it must not create alternate delete/retract/apply side doors.
- **D-09:** Snapshot-aware publish behavior must keep the same transaction, rollback, and lock guarantees established in Phase 03.

### v1 keeps a human confirmation gate
- **D-10:** The system may produce a candidate snapshot hypothesis automatically, but disputed or high-impact `full_snapshot` classification still needs operator confirmation in v1.
- **D-11:** Human confirmation must be durable and auditable: who confirmed, when, for which quote document, and based on what evidence.
- **D-12:** Confirmation is not itself publication. It authorizes safe snapshot semantics when a guarded publish is later invoked.

### Brownfield and corpus constraints matter
- **D-13:** Phase 02.1 gold fixtures already carry message-level `full_snapshot` / `delta_update` / `unresolved` judgments, so Phase 04 should reuse them as regression material rather than inventing abstract examples.
- **D-14:** Shift boards, handoff boards, and explicit “单独更新/补几条” messages are the primary business cues; the system should start from those finite stable patterns instead of aiming at a universal language model classifier.
- **D-15:** Mixed or partial validator outcomes must not be misread as `full_snapshot` just because the message is long. Safety beats coverage.

### Explicit non-goals
- **D-16:** Phase 04 does not make runtime default to production publication; validation-first posture remains.
- **D-17:** Phase 04 does not build the full candidate/validator/publish inspection UI. It only adds the minimal human confirmation gate needed for snapshot semantics.
- **D-18:** Phase 04 does not weaken the “宁可不上墙，不可误上墙” rule to improve coverage.

### the agent's Discretion
- Exact schema shape for durable snapshot decisions, provided it preserves system hypothesis, optional operator confirmation, and publish-facing resolved semantics
- Exact publisher mode API, provided delta/default-safe behavior is explicit and testable
- Exact confirmation route/page placement, provided it stays proof-oriented and does not bypass the guarded publisher

</decisions>

<specifics>
## Specific Ideas

- A small dedicated `quote_snapshot.py` module is likely cleaner than smuggling all classification logic into `quotes.py` or `quote_publisher.py`.
- The guarded publisher probably needs at least two real mutation semantics after this phase:
  - `delta_update`
  - `full_snapshot_confirmed`
- Gold fixtures from `tests/fixtures/quote_exception_corpus/gold_top8.json` already encode valuable message-level judgments and reasons; they should become a planning input, not just a historical note.
- v1 human confirmation can be intentionally minimal: a message-level confirm/reclassify surface that writes durable decision state without automatically publishing.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product and governance
- `.planning/PROJECT.md` — hard rules for fact protection, delta-safe defaults, and no prompt-defined publish authority
- `.planning/REQUIREMENTS.md` — `SNAP-*` and `OPS-02` requirements
- `.planning/ROADMAP.md` — Phase ordering and dependency on guarded publisher custody
- `.planning/STATE.md` — current focus after Phase 03 completion
- `AGENTS.md` — repo-level constraints, especially “default delta”, “only confirmed full may inactivate unseen SKUs”, and validation-first posture

### Prior phase outputs
- `.planning/phases/01-candidate-contract-foundation/01-CONTEXT.md` — why snapshot semantics are message-level and why message metadata already carries `snapshot_hypothesis`
- `.planning/phases/02.1-real-exception-corpus-candidate-coverage/02.1-CONTEXT.md` — curated gold samples already include message-level snapshot judgments
- `.planning/phases/03-fact-protection-publisher/03-CONTEXT.md` — Phase 03 explicitly deferred snapshot execution semantics to Phase 04
- `.planning/phases/03-fact-protection-publisher/03-VERIFICATION.md` — publisher custody, no-op, rollback, and bypass protection are already in place

### Existing implementation surfaces
- `wxbot/bookkeeping-platform/bookkeeping_core/quote_candidates.py` — candidate message carries `snapshot_hypothesis` and reason
- `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py` — runtime still stamps `snapshot_hypothesis="unresolved"` and calls the publisher in `validation_only`
- `wxbot/bookkeeping-platform/bookkeeping_core/quote_publisher.py` — current guarded publisher only knows `validation_only` and replacement-style publish mode
- `wxbot/bookkeeping-platform/bookkeeping_core/quote_validation.py` — message-level validation decisions (`publishable_rows_available`, `mixed_outcome`, `no_publish`) already exist and must not be conflated with snapshot semantics
- `wxbot/bookkeeping-platform/tests/fixtures/quote_exception_corpus/gold_top8.json` — real-sample message-level snapshot judgments and reasons
- `wxbot/bookkeeping-platform/tests/test_postgres_backend.py`
- `wxbot/bookkeeping-platform/tests/test_runtime.py`
- `wxbot/bookkeeping-platform/tests/test_webapp.py`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Candidate documents already persist `snapshot_hypothesis` and `snapshot_hypothesis_reason`.
- Real corpus fixtures already encode message-level `full_snapshot` / `delta_update` / `unresolved` expectations.
- The guarded publisher already owns transaction/rollback/lock custody, so snapshot semantics can be added without re-opening mutation authority.

### Established Patterns
- This project prefers additive durable surfaces over rewriting brownfield tables wholesale.
- Operator-facing proof flows remain fact-neutral unless they deliberately invoke the guarded publisher.
- High-risk business rules belong in core code and tests, not in prompts.

### Integration Points
- Candidate stamping in `bookkeeping_core/quotes.py`
- Guarded mutation semantics in `bookkeeping_core/quote_publisher.py`
- Minimal operator confirmation surface in `bookkeeping_web/app.py`
- PG/runtime/web regressions in `tests/test_postgres_backend.py`, `tests/test_runtime.py`, and `tests/test_webapp.py`

### Risk Hotspots
- Current publisher replacement semantics would inactivate everything for a group if used naively.
- Current runtime stamps every message as `snapshot_hypothesis="unresolved"`, so Phase 04 must not pretend classification already exists.
- A human confirmation surface could accidentally become a publish side door if it mutates facts directly instead of persisting only snapshot decisions.

</code_context>

<deferred>
## Deferred Ideas

- Rich operator debugging UI remains Phase 07
- Full shadow-mode production comparison remains Phase 08
- Automatic high-confidence snapshot confirmation remains v2 (`AUTO-01`), not v1

</deferred>

---

*Phase: 04-snapshot-delta-semantics*
*Context gathered: 2026-04-15*
