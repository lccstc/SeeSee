# Requirements: SeeSee 报价墙硬验证系统

**Defined:** 2026-04-13
**Core Value:** 把供应商群原始消息转成“可追溯、可验证、不可误发布”的报价事实，宁可不上墙，也绝不把错价、错面额、错国家/币种上墙。

## v1 Requirements

### Evidence

- [ ] **EVID-01**: User can trace every candidate or published quote row back to the exact raw message, source line, sender, group, and message time
- [ ] **EVID-02**: User can inspect why a row was accepted, rejected, held, or left untouched during a publish attempt

### Candidate Generation

- [ ] **CAND-01**: System creates quote candidates without directly mutating active quote facts
- [ ] **CAND-02**: Each candidate preserves parser/template/rule lineage and message-type hypothesis for later debugging

### Validation

- [ ] **VALI-01**: System validates every candidate row against a fixed quote schema before publish evaluation
- [ ] **VALI-02**: System applies explicit business-rule validation and records structured rejection reasons for invalid candidates
- [ ] **VALI-03**: System computes `publishable_rows` separately from rejected rows and held rows

### Fact Protection

- [ ] **FACT-01**: Failed parse, validation, or publish attempts leave prior active quote facts untouched
- [ ] **FACT-02**: If a message produces no `publishable_rows`, the system performs no publish for that message
- [ ] **FACT-03**: No route, script, page action, Agent, or SubAgent can bypass validator and publisher safeguards to mutate active quotes directly

### Snapshot Semantics

- [ ] **SNAP-01**: System records each message as candidate `full_snapshot`, candidate `delta_update`, or unresolved classification
- [ ] **SNAP-02**: Unresolved or unconfirmed classification defaults to `delta_update` behavior
- [ ] **SNAP-03**: Only a confirmed `full_snapshot` may inactivate previously active SKUs that are absent from the current message

### Exceptions & Replay

- [ ] **EXCP-01**: Every failed, partial, rejected, or unclassifiable parse attempt enters the exception pool
- [ ] **EXCP-02**: User can replay a stored raw message through the current parser and validator chain
- [ ] **EXCP-03**: User can compare replay outcomes before and after a template, rule, or code fix

### Industrialization

- [ ] **INDU-01**: User can promote repeated exception patterns into deterministic fixes such as templates, rules, scripts, skills, or unit tests
- [ ] **INDU-02**: System surfaces repeated failure patterns so high-frequency errors can be prioritized for industrialized fixes

### Operator Verification

- [ ] **OPS-01**: User can inspect candidate rows, rejected rows, held rows, and `publishable_rows` for an individual message
- [ ] **OPS-02**: User can confirm `full_snapshot` versus `delta_update` during v1 debugging without granting automatic publish authority

### Governance

- [ ] **GOV-01**: User can run the pipeline in validation or shadow mode without letting it automatically replace the current production publish flow

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

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| EVID-01 | Phase 1 | Pending |
| EVID-02 | Phase 7 | Pending |
| CAND-01 | Phase 1 | Pending |
| CAND-02 | Phase 1 | Pending |
| VALI-01 | Phase 2 | Pending |
| VALI-02 | Phase 2 | Pending |
| VALI-03 | Phase 2 | Pending |
| FACT-01 | Phase 3 | Pending |
| FACT-02 | Phase 3 | Pending |
| FACT-03 | Phase 3 | Pending |
| SNAP-01 | Phase 4 | Pending |
| SNAP-02 | Phase 4 | Pending |
| SNAP-03 | Phase 4 | Pending |
| EXCP-01 | Phase 5 | Pending |
| EXCP-02 | Phase 5 | Pending |
| EXCP-03 | Phase 5 | Pending |
| INDU-01 | Phase 6 | Pending |
| INDU-02 | Phase 6 | Pending |
| OPS-01 | Phase 7 | Pending |
| OPS-02 | Phase 4 | Pending |
| GOV-01 | Phase 8 | Pending |

**Coverage:**
- v1 requirements: 21 total
- Mapped to phases: 21
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-13*
*Last updated: 2026-04-13 after initial definition*
