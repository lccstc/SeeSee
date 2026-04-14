# Requirements: SeeSee 报价墙硬验证系统

**Defined:** 2026-04-13
**Core Value:** 把供应商群原始消息转成“可追溯、可验证、不可误发布”的报价事实，宁可不上墙，也绝不把错价、错面额、错国家/币种上墙。

## v1 Requirements

### Evidence

- [ ] **EVID-01**: User can trace every candidate or published quote row back to the exact raw message, source line, sender, group, and message time
- [x] **EVID-02**: User can inspect why a row was accepted, rejected, held, or left untouched during a publish attempt

### Candidate Generation

- [ ] **CAND-01**: System creates quote candidates without directly mutating active quote facts
- [ ] **CAND-02**: Each candidate preserves parser/template/rule lineage and message-type hypothesis for later debugging

### Validation

- [x] **VALI-01**: System validates every candidate row against a fixed quote schema before publish evaluation
- [x] **VALI-02**: System applies explicit business-rule validation and records structured rejection reasons for invalid candidates
- [x] **VALI-03**: System computes `publishable_rows` separately from rejected rows and held rows

### Corpus & Candidate Coverage

- [ ] **CORP-01**: System maintains a refreshable index of the live quote exception pool, prioritizing the current top 8 exception-heavy chats while keeping long-tail chats visible
- [ ] **CORP-02**: System stores replayable gold samples with message-level and row-level expected outcomes, including `publishable` / `held` / `rejected` judgments and `full_snapshot` / `delta_update` / `unresolved` labels
- [ ] **COV-01**: System deterministically improves candidate generation for dominant live failure shapes, including section splitting, quote-versus-rule/manual classification, and scoped numeric rows with explicit evidence
- [ ] **COV-02**: System can bootstrap top-volume missing-template groups into conservative group-parser coverage and prove the result through runtime/replay regression tests without bypassing validator custody

### Fact Protection

- [x] **FACT-01**: Failed parse, validation, or publish attempts leave prior active quote facts untouched
- [x] **FACT-02**: If a message produces no `publishable_rows`, the system performs no publish for that message
- [x] **FACT-03**: No route, script, page action, Agent, or SubAgent can bypass validator and publisher safeguards to mutate active quotes directly

### Snapshot Semantics

- [x] **SNAP-01**: System records each message as candidate `full_snapshot`, candidate `delta_update`, or unresolved classification
- [x] **SNAP-02**: Unresolved or unconfirmed classification defaults to `delta_update` behavior
- [x] **SNAP-03**: Only a confirmed `full_snapshot` may inactivate previously active SKUs that are absent from the current message

### Exceptions & Replay

- [x] **EXCP-01**: Every failed, partial, rejected, or unclassifiable parse attempt enters the exception pool as a durable repair case rather than a disposable log line
- [x] **EXCP-02**: Each repair case carries the raw message, current group profile/template version, candidate result, validator result, unmatched evidence, and replay baseline needed for constrained remediation
- [x] **EXCP-03**: User can replay a stored raw message through the current parser and validator chain and compare before/after outcomes for a proposed fix

### Industrialization

- [ ] **INDU-01**: System drives repair cases through a constrained remediation workflow with bounded attempts, cumulative failure logs, and escalation after repeated failure
- [ ] **INDU-02**: User can promote repeated exception patterns into deterministic fixes such as group profiles, sections, bootstrap configs, shared rules, scripts, skills, or unit tests, prioritizing group-level fixes before global parser changes
- [x] **INDU-03**: System converts repair-case failure history into a structured failure dictionary / repair lexicon so fresh agents can retrieve symptoms, root causes, preferred scopes, forbidden fixes, replay fixtures, and known-good repairs without relying on prior chat context

### Operator Verification

- [x] **OPS-01**: User can inspect candidate rows, rejected rows, held rows, and `publishable_rows` for an individual message
- [x] **OPS-02**: User can confirm `full_snapshot` versus `delta_update` during v1 debugging without granting automatic publish authority

### Governance

- [x] **GOV-01**: User can run the pipeline as an operator-owned experimental active wall that updates the wall through system custody, while still preventing automatic downstream actions or default production takeover

## v2 Requirements

### Classification Automation

- **AUTO-01**: System can auto-confirm `full_snapshot` versus `delta_update` only when evidence is strong and review history proves it is safe
- **AUTO-02**: System can suggest likely rule/template fixes for recurring exception patterns without granting those suggestions publish authority

### Exception Operations

- **AUTO-03**: System clusters repeated exception shapes automatically to accelerate industrialization
- **AUTO-04**: System can produce prioritized remediation queues from exception frequency and business impact

## Out of Scope

| Feature | Reason |
|---------|--------|
| Letting an LLM directly decide final publish results | Violates hard system-custody requirement for pricing facts |
| Rebuilding finance or settlement services | This project is about quote-wall parsing and publication safety, not ledger redesign |
| Replacing the entire brownfield architecture upfront | Current mandate is minimum necessary change, not architecture cleanup for its own sake |
| Directly taking over production publish authority in v1 | v1 is for validation, replay, and manual comparison first |
| Relying on prompt-only rules as long-term correctness mechanism | Business and publish rules must live in explicit system code and tests |
| Pursuing a global万能解析器 that replaces one-group-one-profile | The project assumes each group is a finite stable pattern set; fixes should land in the owning group profile first |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| EVID-01 | Phase 1 | Pending |
| EVID-02 | Phase 7 | Complete |
| CAND-01 | Phase 1 | Pending |
| CAND-02 | Phase 1 | Pending |
| VALI-01 | Phase 2 | Complete |
| VALI-02 | Phase 2 | Complete |
| VALI-03 | Phase 2 | Complete |
| CORP-01 | Phase 2.1 | Pending |
| CORP-02 | Phase 2.1 | Pending |
| COV-01 | Phase 2.1 | Pending |
| COV-02 | Phase 2.1 | Pending |
| EXCP-01 | Phase 5 | Complete |
| EXCP-02 | Phase 5 | Complete |
| EXCP-03 | Phase 5 | Complete |
| INDU-01 | Phase 6 | Pending |
| INDU-02 | Phase 6 | Pending |
| INDU-03 | Phase 7 | Complete |
| FACT-01 | Phase 3 | Complete |
| FACT-02 | Phase 3 | Complete |
| FACT-03 | Phase 3 | Complete |
| SNAP-01 | Phase 4 | Complete |
| SNAP-02 | Phase 4 | Complete |
| SNAP-03 | Phase 4 | Complete |
| OPS-01 | Phase 7 | Complete |
| OPS-02 | Phase 4 | Complete |
| GOV-01 | Phase 8 | Completed |

**Coverage:**
- v1 requirements: 26 total
- Mapped to phases: 26
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-13*
*Last updated: 2026-04-15 after Phase 08 experimental active wall verification*
