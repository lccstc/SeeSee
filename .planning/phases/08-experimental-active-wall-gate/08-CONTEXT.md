# Phase 08: Experimental Active Wall Gate - Context

**Gathered:** 2026-04-15  
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 08 exists to let the current quote pipeline update a real operator-owned experimental wall under full system custody.

The important distinction is:

- this is **not** a pure shadow / no-op validation phase
- this is **not** formal production authority handoff

By the end of Phase 07, the system can already:

- ingest real raw messages
- generate candidates
- validate rows into `publishable / held / rejected`
- manage repair cases and bounded remediation
- protect active facts behind a guarded publisher
- record snapshot semantics
- explain one message end-to-end through the operator workbench
- expose a searchable failure dictionary

What is still missing is the operating mode boundary for live use:

- the system must be allowed to mutate the wall **for one operator's daily use**
- but it must do so without silently becoming the default production authority
- and without enabling downstream automation such as notify / settle / broadcast / push

Phase 08 addresses that gap. It defines and implements the experimental wall gate: the pipeline is allowed to update the wall through the guarded publisher, while the whole system still declares itself experimental, evidence-heavy, and downstream-off.

</domain>

<decisions>
## Implementation Decisions

### Experimental wall is a real wall, but not formal production authority
- **D-01:** Phase 08 enables real wall mutation through the guarded publisher for operator use; it does not stay no-op-only.
- **D-02:** The resulting wall is explicitly an **experimental active wall**, not the formal production truth authority for downstream business.
- **D-03:** The phase must make the operating mode visible in UI and configuration so nobody confuses “live experimental wall” with “formal production handoff”.

### Custody rules remain unchanged
- **D-04:** All wall mutation in experimental mode must still go through the guarded publisher.
- **D-05:** Validator custody, snapshot semantics, and evidence lineage from Phases 02/03/04 remain mandatory.
- **D-06:** `0 publishable_rows` must still no-op; unresolved snapshot decisions must still default to delta-safe behavior.

### Downstream automation stays off
- **D-07:** Experimental wall mode must not automatically trigger settlement, customer notification, outward messaging, or any other downstream side effect.
- **D-08:** Any existing or future path that could treat wall updates as operational approval must remain disabled or explicitly gated off in this phase.
- **D-09:** Experimental wall mode is for observation and operator decision support, not for unattended business execution.

### Observation becomes first-class
- **D-10:** Operators need a concise top-level view of experimental running health, not only per-message drilling.
- **D-11:** The quotes surface should show experimental-mode status and a minimal set of operating metrics: wall updates, exceptions, mixed outcomes, remediation success/escalation, and risky mutation surfaces.
- **D-12:** These observation surfaces must remain proof-oriented and auditable, not fuzzy “AI confidence dashboard” theater.

### Promotion to formal production must be explicit
- **D-13:** Phase 08 must end with a concrete promotion contract: what signals say “keep experimental”, and what signals say “eligible for formal production authority”.
- **D-14:** Promotion criteria must be business-readable, not just buried in tests.
- **D-15:** This phase does not itself perform the handoff to formal production authority; it only defines the go / no-go gate.

### Explicit non-goals
- **D-16:** Phase 08 does not re-open parser architecture, validator semantics, or repair workflow design.
- **D-17:** Phase 08 does not grant automatic downstream actions.
- **D-18:** Phase 08 does not claim the system is fully ready for company-wide production just because the experimental wall is running.

### the agent's Discretion
- Exact flag / config shape for experimental wall mode, provided it is obvious, testable, and not easily confused with formal production authority
- Exact metric selection and UI placement, provided one operator can quickly judge wall health from `/quotes`
- Exact documentation structure for promotion criteria, provided it is concrete enough to govern future handoff

</decisions>

<specifics>
## Specific Ideas

- The current `/quotes` page is already the operator center; Phase 08 should extend it rather than invent a second control room.
- Experimental wall mode should likely be explicit in config / runtime state and also visible on the page.
- A small daily operations strip at the top of `/quotes` is likely enough for v1: wall updates, exceptions, mixed outcomes, remediation success, escalation, risky snapshot-authorized changes.
- Promotion criteria should likely live both in `.planning/` and in an operator-visible explanation panel.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product and governance
- `.planning/PROJECT.md` — core hard rules, especially “宁可不上墙，不可误上墙”
- `.planning/REQUIREMENTS.md` — `GOV-01`
- `.planning/ROADMAP.md` — Phase 08 rewritten as experimental active wall gate
- `.planning/STATE.md` — current focus after Phase 07 completion
- `PROJECT/P8单人运营实验墙上线标准.md` — business-language operating boundary for this phase
- `AGENTS.md` — project constraints, fact custody, downstream-off expectations

### Prior phase outputs
- `.planning/phases/03-fact-protection-publisher/03-VERIFICATION.md`
- `.planning/phases/04-snapshot-delta-semantics/04-VERIFICATION.md`
- `.planning/phases/07-operator-verification-failure-dictionary/07-VERIFICATION.md`

### Existing implementation surfaces
- `wxbot/bookkeeping-platform/bookkeeping_core/quote_publisher.py`
- `wxbot/bookkeeping-platform/bookkeeping_core/quote_snapshot.py`
- `wxbot/bookkeeping-platform/bookkeeping_core/database.py`
- `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py`
- `wxbot/bookkeeping-platform/bookkeeping_web/app.py`
- `wxbot/bookkeeping-platform/bookkeeping_web/pages.py`
- `wxbot/bookkeeping-platform/tests/test_postgres_backend.py`
- `wxbot/bookkeeping-platform/tests/test_runtime.py`
- `wxbot/bookkeeping-platform/tests/test_webapp.py`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Guarded publisher custody already exists and is enforced.
- Snapshot semantics already default unresolved messages to delta-safe behavior.
- The quotes page already exposes operator workbench, exception pool, and failure dictionary.
- The system already distinguishes publishable rows, untouched rows, and repair states.

### Established Patterns
- Brownfield-safe additive changes are preferred over rewrites.
- Operator wording must stay factual and proof-oriented.
- Risky authority transitions are already split into explicit phases instead of being silently smuggled into helper code.

### Integration Points
- Runtime quote publish path in `bookkeeping_core/quotes.py`
- Guarded publish execution in `quote_publisher.py`
- Operator surface in `/quotes`
- Config / environment / runtime mode boundary in `reporting_server.py` and `bookkeeping_web/app.py`

### Risk Hotspots
- If the system mutates the wall without clear experimental-mode labeling, users may mistake it for formal production authority.
- If downstream actions are not explicitly gated off, wall mutation may accidentally trigger broader business behavior.
- If observation metrics are too weak, the operator will not know whether the experimental wall is truly improving.

</code_context>

<deferred>
## Deferred Ideas

- Formal production authority handoff after experimental-wall proving period
- Automatic downstream notification / settlement / customer actions
- Multi-operator operating model and permissions beyond the single-owner scenario

</deferred>

---

*Phase: 08-experimental-active-wall-gate*  
*Context gathered: 2026-04-15*
