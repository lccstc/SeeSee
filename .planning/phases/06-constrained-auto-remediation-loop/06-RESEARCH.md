---
phase: 06-constrained-auto-remediation-loop
status: researched
created: 2026-04-14
source: plan-phase
---

# Phase 06 Research — Constrained Auto-Remediation Loop

## Goal

Build a bounded remediation workflow on top of Phase 05 repair cases so the system can try deterministic, replay-safe quote-parser repairs without granting subagents publish authority or global rule freedom.

This phase is not about making the parser "more magical". It is about making exception repair repeatable, auditable, and safely absorbable.

## Starting Point

Phase 05 already provides:

- durable `quote_repair_cases`
- immutable baseline attempts
- append-only `quote_repair_case_attempts`
- compact repair summaries on exception rows
- brownfield handler sync for resolve / reopen / harvest-save / result-save

That means Phase 06 should not invent a second exception workflow. It should consume the Phase 05 case/attempt substrate directly.

## Key Findings

### 1. Phase 06 needs a remediation protocol, not another parser layer

The dominant risk is not missing data storage. The dominant risk is letting repair attempts become informal edits to templates and parser logic without a shared proof standard.

The workflow therefore needs one canonical remediation protocol:

1. read repair case and prior failure history
2. choose a bounded write scope
3. propose a deterministic repair
4. replay and validate
5. run regressions matched to the chosen scope
6. absorb only if all gates pass
7. otherwise append a failure log and either retry or escalate

### 2. Group-level fixes should be the default, not the fallback

The project's operating assumption remains valid: each customer group is a finite grammar, not an open-ended universal parsing problem.

So the default remediation priority should be:

1. `group profile`
2. `group section`
3. `bootstrap config`
4. `shared deterministic rule`
5. `global core`

The system should require evidence before promoting a fix upward:

- one-group-only evidence should stay group-bound
- repeated multi-group evidence can justify shared-rule promotion
- global-core changes require the strongest proof and broadest regressions

### 3. Subagents must operate in proposal mode only

Subagents can help with:

- producing a template diff
- adding a new section
- adjusting bootstrap config
- proposing a shared deterministic rule
- writing targeted regression tests
- generating a failure analysis summary

Subagents must not:

- mutate `quote_price_rows`
- bypass validator custody
- redefine publish semantics
- treat prompt guesses as proof
- absorb a repair without replay + validator + regression success

The system, not the subagent, must decide whether a proposal is admissible and whether it becomes absorbed.

### 4. The remediation workflow should use the existing attempt history instead of inventing parallel logs

Phase 05 already stores append-only attempts and recomputed failure summaries. Phase 06 should extend that substrate with remediation-specific metadata rather than writing a separate remediation log.

Recommended attempt metadata additions:

- `proposal_scope`: `group_profile | group_section | bootstrap | shared_rule | global_core`
- `proposal_kind`: template patch, section add, bootstrap patch, shared rule patch, core parser patch, test-only proof
- `history_read`: structured proof that prior failure logs were loaded before the attempt
- `gate_results`: replay / validator / regression outcomes
- `absorption_decision`: absorbed / rejected / escalated

### 5. Three-attempt escalation should be explicit state, not convention

The user requirement is clear:

- attempt 1: constrained repair
- attempt 2: constrained repair with prior failure log
- attempt 3: constrained repair with full attempt history
- still failing: escalate to main agent / human

So escalation should become a system-owned transition, not a social rule. The workflow should cap retry count and refuse a fourth automatic remediation attempt.

### 6. Successful repairs must industrialize immediately

If a repair succeeds but does not leave behind deterministic artifacts, the system will drift back into prompt-only heroics.

Absorption should therefore require one or more deterministic outputs:

- updated group profile / section
- updated bootstrap config
- added shared deterministic rule
- new fixture or regression
- new script/skill hook where appropriate

The fix is only complete when future replay uses the artifact rather than the subagent's memory.

## Recommended Plan Decomposition

### Plan 06-01 — Remediation Attempt Contract & Escalation Loop

Focus:

- remediation attempt metadata
- legal remediation states
- max-attempt enforcement
- failure-log stacking
- "must read history before retry" enforcement

Why first:

Without a formal attempt protocol, later absorption and scope-priority logic will be ungoverned.

### Plan 06-02 — Group-First Scope Router & Safe Write Boundaries

Focus:

- deterministic scope selection
- proposal scope classifier
- group-first priority enforcement
- promotion criteria for shared/global changes
- safe write-set guardrails for subagents

Why second:

This turns remediation from "patch whatever works" into "patch the smallest safe surface first".

### Plan 06-03 — Absorption Gates & Industrialization Outputs

Focus:

- replay + validator + regression gate orchestration
- absorbed vs rejected attempt outcomes
- deterministic artifact emission
- follow-up fixture/test generation
- escalation-ready summaries for failed attempts

Why third:

This closes the loop so successful fixes become durable system behavior rather than ephemeral experiments.

## Risks To Guard Against

### Hidden publisher creep

No remediation attempt may touch publish authority or active quote facts. Phase 06 remains candidate/validation/remediation custody only.

### Shared-rule over-promotion

If the workflow promotes one-group fixes to shared/global too early, it will reintroduce cross-group fragility.

### Repeated prompt retries with no state

If the second and third attempts do not consume structured prior failure history, the workflow will only repeat the first failure with different wording.

### "Successful" repair without deterministic artifact

If a subagent passes replay once but leaves no template/rule/test behind, the system has not actually learned anything.

## Planning Guidance

- Prefer additive metadata and orchestration helpers over large schema redesigns.
- Reuse Phase 05 repair-case and attempt tables; extend them only where remediation evidence genuinely requires structured fields.
- Keep Phase 06 headless/system-oriented; operator-facing inspection remains Phase 07.
- Treat remediation as candidate-side grammar evolution only; publisher and snapshot semantics stay deferred to Phases 03 and 04.

## Research Conclusion

Phase 06 should be implemented as a system-owned remediation state machine that:

- starts from existing repair cases
- enforces bounded attempts
- prefers group-level fixes
- requires prior-failure-history consumption
- proves every proposal through replay + validator + regression gates
- absorbs only deterministic artifacts
- escalates after repeated failure instead of looping forever

## RESEARCH COMPLETE

Phase 06 is best decomposed into:

1. remediation-attempt contract + escalation loop
2. group-first scope router + safe write boundaries
3. absorption gates + deterministic industrialization outputs
