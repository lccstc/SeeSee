# Phase 03: Fact Protection Publisher - Context

**Gathered:** 2026-04-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 03 exists to take active quote-fact mutation authority away from ad hoc runtime, replay, page, and script codepaths and place it behind one guarded publisher. Phase 01/02 already split candidate generation from validator verdicts, and Phase 05/06 proved that exceptions, repair cases, and remediation can evolve group profiles without touching active facts. This phase now makes that separation structural: only one publisher path may mutate `quote_price_rows`, and failures must always collapse to “no update”.

This phase is about transaction custody and structural enforcement, not smarter parsing. It does not re-open candidate generation, does not redefine remediation behavior, and does not yet settle `full_snapshot` versus `delta_update` execution semantics. Those message semantics remain Phase 04 work.

</domain>

<decisions>
## Implementation Decisions

### Publisher custody becomes the only mutation authority
- **D-01:** Active quote facts must be mutated only through one core-owned publisher entrypoint in `bookkeeping_core/`.
- **D-02:** Runtime quote capture, replay apply flows, and any manual retract/apply operation must call that same publisher or perform no fact mutation at all.
- **D-03:** Low-level helpers such as `deactivate_old_quotes_for_group()` and `upsert_quote_price_row_with_history()` may remain as internal primitives, but direct callsites outside the guarded publisher must be treated as architectural violations.

### Failure means no update
- **D-04:** Zero `publishable_rows` is an explicit publish no-op, not an implicit “do nothing if lucky”.
- **D-05:** Parse failure, validator failure, mixed outcome without an approved publish subset, or publish-time exception must never clear or partially corrupt existing active rows.
- **D-06:** The publisher must decide no-op versus apply before any destructive mutation step begins.

### Atomicity and locking are phase-critical
- **D-07:** A publish attempt must execute inside one PostgreSQL transaction owned by the publisher.
- **D-08:** The publisher must serialize per source group, using PostgreSQL-native locking rather than process-local locks or prompt discipline.
- **D-09:** Inner database helpers used by the publisher must not independently `commit()` halfway through a publish batch.

### Brownfield semantics stay narrow in Phase 03
- **D-10:** Phase 03 centralizes publish authority before refining snapshot semantics. It must not silently invent `full_snapshot` / `delta_update` behavior inside a hidden helper.
- **D-11:** Where current brownfield flows still need a replacement-style publish mode, that mode must be explicit and publisher-owned so Phase 04 can later swap in safe snapshot-aware behavior.
- **D-12:** Until Phase 04 lands, unresolved message semantics remain default-safe: if the publisher cannot justify a fact mutation, it must no-op.

### Web and script routes do not get side doors
- **D-13:** `/api/quotes/delete`, replay apply paths, seed/demo scripts, and future agent tools must not bypass validator + publisher custody with raw SQL or helper calls.
- **D-14:** If a legacy route cannot yet be expressed safely through the guarded publisher, Phase 03 should disable or narrow it rather than preserve a bypass.
- **D-15:** Structural tests are required because policy reminders alone already failed in this repo.

### Explicit non-goals
- **D-16:** Phase 03 does not decide `full_snapshot` / `delta_update`; it only makes sure future publish execution has one owner.
- **D-17:** Phase 03 does not turn validation-mode results into default production publishes; shadow-mode adoption remains Phase 08.
- **D-18:** Phase 03 does not replace the failure dictionary, operator workbench, or remediation loop. It only gives those later surfaces a safe fact-mutation gate to call.

### the agent's Discretion
- Exact publisher module/class/function shape, provided there is one obvious allowlisted mutation API
- Whether additive publish-attempt persistence is needed now or can stay implicit until Phase 07, as long as custody and no-op guarantees are testable
- Exact route behavior for legacy delete/replay actions, provided bypasses are structurally removed or blocked

</decisions>

<specifics>
## Specific Ideas

- The current repo already proved candidate/validator/remediation can be fact-neutral, so Phase 03 should preserve that discipline and only add a guarded fact boundary.
- A dedicated `quote_publisher.py` module is the most readable allowlist target for later architecture tests.
- The publisher should accept validator-owned `publishable_rows` plus explicit publish mode metadata, rather than rediscovering row validity from parser output.
- Raw delete behavior from the web layer should not survive this phase in its current form.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product and governance
- `.planning/PROJECT.md` — Hard rules for validator custody, fact protection, and no direct publication
- `.planning/REQUIREMENTS.md` — `FACT-*` requirements and the wider quote-wall safety posture
- `.planning/ROADMAP.md` — Phase ordering after remediation validation
- `.planning/STATE.md` — Current focus and post-Phase-06 position
- `AGENTS.md` — Repo-level constraints: one-group-one-profile, no prompt-defined publish authority, PostgreSQL as fact source

### Prior phase outputs
- `.planning/phases/02-validation-engine/02-VERIFICATION.md` — `publishable_rows` now belong to validator outputs
- `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md` — repair cases are fact-neutral proof objects
- `.planning/phases/06-constrained-auto-remediation-loop/06-VERIFICATION.md` — remediation attempts are bounded and do not mutate active facts
- `.planning/research/FAILURE-DICTIONARY.md` — future agents need searchable repair knowledge instead of hidden side effects

### Existing quote-wall implementation
- `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py` — runtime quote capture currently chooses when to attempt active-fact writes
- `wxbot/bookkeeping-platform/bookkeeping_core/database.py` — current active-row mutation helpers and commit behavior
- `wxbot/bookkeeping-platform/bookkeeping_web/app.py` — replay apply and delete routes that still carry bypass risk
- `wxbot/bookkeeping-platform/scripts/seed_quote_demo.py` — seed/demo script currently using direct `quote_price_rows` deletion
- `wxbot/bookkeeping-platform/tests/test_postgres_backend.py`
- `wxbot/bookkeeping-platform/tests/test_runtime.py`
- `wxbot/bookkeeping-platform/tests/test_webapp.py`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Validator outputs already persist durable row/message decisions, so Phase 03 should consume `publishable_rows` instead of trusting parser-side hints.
- Runtime and replay already know how to preserve candidate evidence and exception evidence without fact mutation.
- PostgreSQL-backed tests already exist and are the right place to prove atomic publish/no-op guarantees.

### Established Patterns
- This repo increasingly adds additive durable surfaces rather than replacing brownfield data models wholesale.
- Quote-wall safety work already prefers system-owned deterministic rules over prompt-only behavior; the publisher should continue that pattern.

### Integration Points
- `QuoteCaptureService.capture_from_message()` in `bookkeeping_core/quotes.py`
- Active row helpers in `bookkeeping_core/database.py`
- Replay/result-save/delete handlers in `bookkeeping_web/app.py`
- PostgreSQL schema + regression surfaces in `wxbot/bookkeeping-platform/sql/postgres_schema.sql` and tests

### Risk Hotspots
- Current inner DB helpers commit independently, which leaves a corruption window if deactivate succeeds before replacement rows finish.
- Replay still behaves like a second publisher implementation in the web layer.
- `/api/quotes/delete` currently operates as a direct active-row delete path.
- If Phase 03 quietly bakes snapshot semantics into the publisher now, it will overlap Phase 04 and hide destructive assumptions.

</code_context>

<deferred>
## Deferred Ideas

- `full_snapshot` / `delta_update` classification and unseen-SKU inactivation rules remain Phase 04
- Operator-facing publish evidence and failure dictionary UI remain Phase 07
- Shadow-mode publish suppression and production go/no-go gates remain Phase 08

</deferred>

---

*Phase: 03-fact-protection-publisher*
*Context gathered: 2026-04-15*
