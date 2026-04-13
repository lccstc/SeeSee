# Roadmap: SeeSee 报价墙硬验证系统

## Overview

This roadmap turns the current brownfield quote wall into a formal validation pipeline. The sequence is deliberate: first separate candidates from facts, then build validators and publisher safeguards, then make snapshot/delta semantics explicit, then harden exception replay and industrialization, and only after that build the operator verification surfaces and shadow-mode gate needed to trust the system on real samples.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Candidate Contract Foundation** - Split parsing output from active fact publication and formalize candidate objects
- [x] **Phase 2: Validation Engine** - Add fixed schema validation, business validation, and `publishable_rows`
- [x] **Phase 2.1: Real Exception Corpus & Candidate Coverage (INSERTED)** - Build the real-sample corpus and harden candidate generation against live exception shapes
- [ ] **Phase 3: Fact Protection Publisher** - Make one guarded publisher the only path that can mutate active quote facts
- [ ] **Phase 4: Snapshot / Delta Semantics** - Distinguish `full_snapshot` from `delta_update` and default safely
- [ ] **Phase 5: Exception Replay Loop** - Make every failure replayable and comparable before/after fixes
- [ ] **Phase 6: Industrialization Loop** - Turn repeated failures into deterministic rules, templates, scripts, skills, and tests
- [ ] **Phase 7: Operator Verification Workbench** - Expose message-level candidate, rejection, and publish decision evidence for debugging
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

### Phase 3: Fact Protection Publisher
**Goal**: Ensure that only a guarded publisher can change active quote facts, and that failures never corrupt existing wall state.
**Depends on**: Phase 02.1
**Requirements**: [FACT-01, FACT-02, FACT-03]
**Success Criteria** (what must be TRUE):
  1. No parse, validation, or publish failure clears existing active quote facts
  2. Messages with zero `publishable_rows` result in no active-fact mutation
  3. UI actions, scripts, and agent-driven operations cannot bypass the guarded publish path
**Plans**: TBD

Plans:
- [ ] 03-01: Centralize active-quote mutation behind one publisher service
- [ ] 03-02: Add protective no-op behavior for failed or empty publish attempts
- [ ] 03-03: Remove or block bypass paths that write active quotes directly

### Phase 4: Snapshot / Delta Semantics
**Goal**: Make `full_snapshot` and `delta_update` explicit message semantics with safe defaults and human confirmation in v1.
**Depends on**: Phase 3
**Requirements**: [SNAP-01, SNAP-02, SNAP-03, OPS-02]
**Success Criteria** (what must be TRUE):
  1. Each message carries an explicit snapshot-type decision or unresolved state
  2. Unresolved messages behave as `delta_update` rather than destructive replacement
  3. Only confirmed `full_snapshot` messages may inactivate unseen prior SKUs
**Plans**: TBD

Plans:
- [ ] 04-01: Define message-level snapshot classification model and safe default behavior
- [ ] 04-02: Wire classification into publisher inactivation rules
- [ ] 04-03: Add v1 human confirmation flow for disputed snapshot classification

### Phase 5: Exception Replay Loop
**Goal**: Turn every failure into replayable evidence that can be used to verify fixes before trusting them.
**Depends on**: Phase 4
**Requirements**: [EXCP-01, EXCP-02, EXCP-03]
**Success Criteria** (what must be TRUE):
  1. Failed, partial, and rejected parse attempts always enter the exception pool
  2. Operators can replay a stored message through the current parser and validator chain
  3. Before/after replay comparisons show whether a fix actually improved the result safely
**Plans**: TBD

Plans:
- [ ] 05-01: Enrich exception records with replay-critical evidence
- [ ] 05-02: Implement deterministic replay path against stored raw messages
- [ ] 05-03: Add before/after replay comparison outputs for debugging

### Phase 6: Industrialization Loop
**Goal**: Ensure recurring failures become durable deterministic fixes instead of permanent manual work.
**Depends on**: Phase 5
**Requirements**: [INDU-01, INDU-02]
**Success Criteria** (what must be TRUE):
  1. Repeated exception patterns are visible and reviewable as a backlog of industrialization candidates
  2. High-frequency failure patterns can be promoted into deterministic templates, rules, scripts, skills, or tests
  3. The same failure shape becomes less likely to recur without relying on prompt tweaks alone
**Plans**: TBD

Plans:
- [ ] 06-01: Add repeated-failure visibility and prioritization
- [ ] 06-02: Define promotion paths into templates, code rules, scripts, skills, and tests
- [ ] 06-03: Close the loop with regression coverage from real failures

### Phase 7: Operator Verification Workbench
**Goal**: Give the operator a message-level debugging view into candidate rows, rejected rows, held rows, and final publish decisions.
**Depends on**: Phase 6
**Requirements**: [EVID-02, OPS-01]
**Success Criteria** (what must be TRUE):
  1. For a single message, the operator can inspect candidate rows, rejected rows, held rows, and `publishable_rows`
  2. The operator can see why rows were published, rejected, or left untouched
  3. The workbench improves debugging accuracy without granting a bypass around validator or publisher safeguards
**Plans**: TBD

Plans:
- [ ] 07-01: Design message-level verification payloads and APIs
- [ ] 07-02: Expose candidate / validator / publish decision evidence in the web workbench
- [ ] 07-03: Add debugging affordances oriented around real exception handling

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
Phases execute in numeric order: 1 → 2 → 2.1 → 3 → 4 → 5 → 6 → 7 → 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Candidate Contract Foundation | 3/3 | Completed | 2026-04-14 |
| 2. Validation Engine | 3/3 | Completed | 2026-04-14 |
| 2.1. Real Exception Corpus & Candidate Coverage | 3/3 | Completed | 2026-04-14 |
| 3. Fact Protection Publisher | 0/3 | Not started | - |
| 4. Snapshot / Delta Semantics | 0/3 | Not started | - |
| 5. Exception Replay Loop | 0/3 | Not started | - |
| 6. Industrialization Loop | 0/3 | Not started | - |
| 7. Operator Verification Workbench | 0/3 | Not started | - |
| 8. Shadow Validation Gate | 0/3 | Not started | - |
