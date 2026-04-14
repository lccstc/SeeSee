---
phase: 06
slug: constrained-auto-remediation-loop
status: planned
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-14
---

# Phase 06 — Validation Strategy

> Validation contract for bounded remediation workflow changes.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `unittest` |
| **Quick run command** | `cd wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend tests.test_runtime -v` |
| **Full suite command** | `cd wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_template_engine tests.test_postgres_backend tests.test_runtime tests.test_webapp -v` |
| **Estimated runtime** | ~150 seconds |

## Sampling Rate

- After every task commit: run the quick run command
- After every plan wave: run the full suite command
- Before verification: full suite must be green
- Max feedback latency: 150 seconds

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Secure Behavior | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------------|-----------|-------------------|--------|
| 06-01-01 | 01 | 1 | INDU-01 | remediation attempts are bounded, append-only, and escalation-aware | unit/integration | `tests.test_postgres_backend tests.test_runtime` | ✅ planned |
| 06-01-02 | 01 | 1 | INDU-01 | retry attempts must load prior failure history before a new attempt is accepted | unit/integration | `tests.test_postgres_backend tests.test_runtime` | ✅ planned |
| 06-02-01 | 02 | 2 | INDU-02 | group-first remediation scope is enforced before shared/global promotion | unit | `tests.test_template_engine tests.test_postgres_backend` | ✅ planned |
| 06-02-02 | 02 | 2 | INDU-02 | subagent-safe write scopes stay inside candidate/template/bootstrap layers and avoid fact mutation | unit/integration | `tests.test_postgres_backend tests.test_runtime tests.test_webapp` | ✅ planned |
| 06-03-01 | 03 | 3 | INDU-01, INDU-02 | successful repairs absorb only after replay + validator + regression gates pass | integration | `tests.test_postgres_backend tests.test_runtime` | ✅ planned |
| 06-03-02 | 03 | 3 | INDU-02 | successful repairs emit deterministic artifacts and repeated failures escalate after max attempts | integration | `tests.test_template_engine tests.test_postgres_backend tests.test_runtime tests.test_webapp` | ✅ planned |

## Wave 0 Requirements

No separate Wave 0 is required.

Missing regression surfaces should be created inside the first task that needs them:

- remediation-attempt state and retry gating tests in `tests.test_postgres_backend` / `tests.test_runtime`
- scope-router and promotion tests in `tests.test_template_engine` or a new remediation-focused test module if needed
- absorption and non-publisher guarantees in `tests.test_runtime` / `tests.test_webapp`

## Manual-Only Verifications

| Behavior | Why Manual | Test Instructions |
|----------|------------|-------------------|
| Escalation summaries are understandable to Leo/operator workflows | wording quality still needs business judgment | Review one case that hits max attempts and confirm the summary distinguishes “repair failed and escalated” from “repair succeeded but not published” |
| Successful absorbed repairs feel like deterministic system behavior rather than hidden prompt magic | trust signaling and operator confidence are not binary | Review one absorbed repair and confirm the resulting artifact is visible as template/rule/test evidence, not just a transient agent output |

## Validation Sign-Off

- [x] Every auto task has an automated verify path
- [x] No more than two tasks between meaningful regressions
- [x] Wave-local feedback stays under 150 seconds
- [x] Manual verification is reserved for business wording and trust signals
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** planned
