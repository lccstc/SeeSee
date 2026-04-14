# Roadmap: SeeSee 报价墙硬验证系统

## Overview

This roadmap turns the current brownfield quote wall into a formal validation pipeline. The sequence is deliberate: first separate candidates from facts, then build validators, then prove the group-profile evolution loop against the real exception pool through a repair state machine and constrained remediation workflow, and only after that harden publish authority, snapshot semantics, operator verification, and shadow-mode gates. The governing idea is not to train a万能解析器, but to keep evolving each group's own profile as a finite, verifiable grammar.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Candidate Contract Foundation** - Split parsing output from active fact publication and formalize candidate objects
- [x] **Phase 2: Validation Engine** - Add fixed schema validation, business validation, and `publishable_rows`
- [x] **Phase 2.1: Real Exception Corpus & Candidate Coverage (INSERTED)** - Build the real-sample corpus and harden candidate generation against live exception shapes
- [x] **Phase 5: Exception Repair State Machine** - Turn every failure into a durable repair case with replay baseline, attempt history, and escalation state
- [x] **Phase 6: Constrained Auto-Remediation Loop** - Let subagents propose bounded repairs that must survive replay, validator, and regression gates before absorption
- [x] **Phase 3: Fact Protection Publisher** - Make one guarded publisher the only path that can mutate active quote facts
- [x] **Phase 4: Snapshot / Delta Semantics** - Distinguish `full_snapshot` from `delta_update` and default safely
- [x] **Phase 7: Operator Verification Workbench** - Expose message-level candidate, rejection, and publish decision evidence for debugging
- [ ] **Phase 8: Shadow Validation Gate** - Run the pipeline safely in validation mode without handing it default production authority

## Phase Details

### Phase 1: Candidate Contract Foundation
**Goal**: Formalize a message-to-candidate pipeline where parsers can propose quote rows but cannot directly publish active facts.
**Depends on**: Nothing (first phase)
**Requirements**: [EVID-01, CAND-01, CAND-02]
**Success Criteria** (what must be TRUE):
  1. Raw message evidence remains the authoritative input for quote parsing decisions
  2. Parser output is represented as candidate objects rather than direct active-fact writes
  3. Candidate objects retain source message, source line, and parser lineage needed for later validation
**Plans**: 3 plans

Plans:
- [x] 01-01-PLAN.md — Define the candidate contract, additive quote-document metadata, and `quote_candidate_rows` persistence
- [x] 01-02-PLAN.md — Route runtime quote capture through candidate-only persistence and preserve exception evidence
- [x] 01-03-PLAN.md — Convert replay/harvest-save to replay candidate runs and rebaseline web tests away from board mutation

### Phase 2: Validation Engine
**Goal**: Build explicit schema and business validators that separate `publishable_rows` from invalid or held rows.
**Depends on**: Phase 1
**Requirements**: [VALI-01, VALI-02, VALI-03]
**Success Criteria** (what must be TRUE):
  1. Every candidate row is evaluated against a fixed quote schema before publication
  2. Business-rule failures are recorded with structured rejection reasons
  3. A message can produce valid, rejected, and held rows in the same evaluation without ambiguity
**Plans**: 3 plans

Plans:
- [x] 02-01-PLAN.md — Define validator contract, additive persistence schema, and durable rejection taxonomy
- [x] 02-02-PLAN.md — Implement schema validation and run it automatically for runtime/replay candidate bundles
- [x] 02-03-PLAN.md — Add business-rule validation and durable `publishable_rows` separation helpers

### Phase 02.1: Real Exception Corpus & Candidate Coverage (INSERTED)

**Goal:** Build a real exception corpus and improve candidate generation coverage against live customer quote shapes before guarded publisher work.
**Requirements**: [CORP-01, CORP-02, COV-01, COV-02]
**Depends on:** Phase 2
**Success Criteria** (what must be TRUE):
  1. The repository contains a refreshable corpus index plus replayable gold samples for the top exception-heavy chats without hiding long-tail shapes
  2. Candidate generation handles multi-section boards, mixed quote/rule/manual text, and scoped numeric rows conservatively with explicit evidence
  3. Top-volume missing-template groups can be bootstrapped and verified through runtime/replay regressions without changing validator or publisher custody
**Plans:** 3 plans

Plans:
- [x] 02.1-01-PLAN.md — Build refreshable corpus assets and curated gold fixtures with an operator approval gate
- [x] 02.1-02-PLAN.md — Harden deterministic candidate generation for dominant structural failure shapes
- [x] 02.1-03-PLAN.md — Bootstrap top-volume group coverage and prove it through runtime/replay regressions

### Phase 5: Exception Repair State Machine
**Goal**: Turn every failure into a durable repair case with explicit state, replay baseline, and cumulative remediation history.
**Depends on**: Phase 02.1
**Requirements**: [EXCP-01, EXCP-02, EXCP-03]
**Success Criteria** (what must be TRUE):
  1. Failed, partial, and rejected parse attempts always enter the exception pool as structured repair cases
  2. Each repair case carries replay-critical context, including current group profile/template version, candidate/validator result, unmatched evidence, and prior attempts
  3. Before/after replay comparisons show whether a proposed fix actually improved the owning group's grammar safely
**Plans**: 3 plans

Plans:
- [x] 05-01-PLAN.md — Introduce repair-case state, additive persistence, and system-owned evidence packaging for every exception
- [x] 05-02-PLAN.md — Implement immutable baseline replay, replay-to-case linking, and durable before/after comparison substrate
- [x] 05-03-PLAN.md — Add append-only attempt history, failure-log stacking, handler state sync, and escalation-ready summaries

### Phase 6: Constrained Auto-Remediation Loop
**Goal**: Ensure recurring failures move through a bounded remediation workflow that prefers group-level fixes, proves safety by replay, and escalates after repeated failure.
**Depends on**: Phase 5
**Requirements**: [INDU-01, INDU-02]
**Success Criteria** (what must be TRUE):
  1. Subagents can only propose bounded repairs against repair cases and must read prior failure logs before each retry
  2. The workflow prefers fixes in the owning group profile / section / bootstrap before promoting shared parser rules
  3. Every absorbed fix survives replay, validator, and regression gates; repeated failure escalates instead of looping forever
**Plans**: 3 plans

Plans:
- [x] 06-01: Implement bounded subagent remediation attempts with cumulative failure logging and max-attempt escalation
- [x] 06-02: Define remediation priority order: group profile -> group section -> bootstrap -> shared rule -> global core
- [x] 06-03: Close the loop by promoting successful repairs into deterministic templates, rules, scripts, skills, and tests

### Phase 3: Fact Protection Publisher
**Goal**: Ensure that only a guarded publisher can change active quote facts, and that failures never corrupt existing wall state.
**Depends on**: Phase 6
**Requirements**: [FACT-01, FACT-02, FACT-03]
**Success Criteria** (what must be TRUE):
  1. No parse, validation, or publish failure clears existing active quote facts
  2. Messages with zero `publishable_rows` result in no active-fact mutation
  3. UI actions, scripts, and agent-driven operations cannot bypass the guarded publish path
**Plans**: 3 plans

Plans:
- [x] 03-01-PLAN.md — Centralize active-quote mutation behind one guarded publisher service
- [x] 03-02-PLAN.md — Add explicit no-op, transaction, and rollback protections for publish attempts
- [x] 03-03-PLAN.md — Remove or block web/script bypasses and add structural publisher-custody tests

### Phase 4: Snapshot / Delta Semantics
**Goal**: Make `full_snapshot` and `delta_update` explicit message semantics with safe defaults and human confirmation in v1.
**Depends on**: Phase 3
**Requirements**: [SNAP-01, SNAP-02, SNAP-03, OPS-02]
**Success Criteria** (what must be TRUE):
  1. Each message carries an explicit snapshot-type decision or unresolved state
  2. Unresolved messages behave as `delta_update` rather than destructive replacement
  3. Only confirmed `full_snapshot` messages may inactivate unseen prior SKUs
**Plans**: 3 plans

Plans:
- [x] 04-01-PLAN.md — Define a durable snapshot decision model and deterministic message-level hypothesis scaffolding
- [x] 04-02-PLAN.md — Wire delta-safe default behavior and confirmed-full inactivation into the guarded publisher
- [x] 04-03-PLAN.md — Add a narrow v1 human confirmation flow that records snapshot decisions without publishing

### Phase 7: Operator Verification & Failure Dictionary
**Goal**: Give the operator a message-level debugging view into candidate rows, rejected rows, held rows, and final publish decisions, while turning repair-case history into a searchable failure dictionary for future agents.
**Depends on**: Phase 6
**Requirements**: [EVID-02, OPS-01, INDU-03]
**Success Criteria** (what must be TRUE):
  1. For a single message, the operator can inspect candidate rows, rejected rows, held rows, and `publishable_rows`
  2. The operator can see why rows were published, rejected, or left untouched
  3. The workbench improves debugging accuracy without granting a bypass around validator or publisher safeguards
  4. Repeated repair-case failures are indexed into a searchable failure dictionary that new agents can query before proposing fixes
**Plans**: 07-01, 07-02, 07-03

Plans:
- [x] 07-01: Design message-level verification payloads and APIs
- [x] 07-02: Expose candidate / validator / publish decision evidence in the web workbench
- [x] 07-03: Build the failure dictionary / repair lexicon from repair cases, replay fixtures, and known-good fixes

### Phase 8: Shadow Validation Gate
**Goal**: Run the full pipeline in validation mode against real samples without handing it default authority over production publication.
**Depends on**: Phase 7
**Requirements**: [GOV-01]
**Success Criteria** (what must be TRUE):
  1. The pipeline can run in shadow mode and produce proposed publish results without automatically taking over production
  2. The operator can compare proposed results against current wall state and replay evidence
  3. The project has a clear go/no-go boundary before any future production handoff
**Plans**: TBD

Plans:
- [ ] 08-01: Add validation-only execution mode and publish suppression
- [ ] 08-02: Add comparison outputs between proposed publishes and current wall state
- [ ] 08-03: Define acceptance gate for any future production adoption

## Progress

**Execution Order:**
Phases execute in strategic order: 1 → 2 → 2.1 → 5 → 6 → 3 → 4 → 7 → 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Candidate Contract Foundation | 3/3 | Completed | 2026-04-14 |
| 2. Validation Engine | 3/3 | Completed | 2026-04-14 |
| 2.1. Real Exception Corpus & Candidate Coverage | 3/3 | Completed | 2026-04-14 |
| 5. Exception Repair State Machine | 3/3 | Completed | 2026-04-14 |
| 6. Constrained Auto-Remediation Loop | 3/3 | Completed | 2026-04-14 |
| 3. Fact Protection Publisher | 3/3 | Completed | 2026-04-15 |
| 4. Snapshot / Delta Semantics | 3/3 | Completed | 2026-04-15 |
| 7. Operator Verification & Failure Dictionary | 3/3 | Completed | 2026-04-15 |
| 8. Shadow Validation Gate | 0/3 | Not started | - |
