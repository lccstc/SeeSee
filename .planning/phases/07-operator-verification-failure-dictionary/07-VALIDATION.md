---
phase: 07
slug: operator-verification-failure-dictionary
status: planned
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-15
---

# Phase 07 — Validation Strategy

> Validation contract for the operator verification workbench and failure dictionary.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `unittest` |
| **Quick run command** | `cd wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend tests.test_webapp -v` |
| **Full suite command** | `cd wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend tests.test_runtime tests.test_webapp tests.test_quote_validation -v` |
| **Estimated runtime** | ~240 seconds |

## Sampling Rate

- After every task commit: run the quick run command
- After every wave: run the full suite command
- Before verification: full suite must be green
- Max feedback latency: 240 seconds

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Secure Behavior | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------------|-----------|-------------------|--------|
| 07-01-01 | 01 | 1 | OPS-01, EVID-02 | one message can be inspected through a coherent evidence payload spanning candidate, validation, snapshot, repair, and publish reasoning | integration | `tests.test_postgres_backend tests.test_webapp` | ✅ planned |
| 07-01-02 | 01 | 1 | EVID-02 | payload explains untouched / no-op / delta-safe outcomes instead of hiding them | unit/integration | `tests.test_postgres_backend tests.test_webapp` | ✅ planned |
| 07-02-01 | 02 | 2 | OPS-01 | operator web workbench exposes evidence clearly without direct fact mutation | integration | `tests.test_webapp` | ✅ planned |
| 07-02-02 | 02 | 2 | EVID-02 | workbench wording remains proof-only and does not imply “already上墙” | integration/manual | `tests.test_webapp` | ✅ planned |
| 07-03-01 | 03 | 3 | INDU-03 | repeated repair failures are indexed into a searchable structured lexicon rather than a raw log blob | integration | `tests.test_postgres_backend tests.test_webapp` | ✅ planned |
| 07-03-02 | 03 | 3 | INDU-03, OPS-01 | operator can jump from a case/evidence view to relevant dictionary knowledge for standard fixes and forbidden fixes | integration/manual | `tests.test_webapp tests.test_postgres_backend` | ✅ planned |

## Wave 0 Requirements

No separate Wave 0 is required.

Missing regression surfaces should be created inside the first task that needs them:

- message-level evidence payload regressions in `tests.test_postgres_backend`
- workbench render / API regressions in `tests.test_webapp`
- lexicon search / entry-shape regressions in `tests.test_postgres_backend` and `tests.test_webapp`

## Manual-Only Verifications

| Behavior | Why Manual | Test Instructions |
|----------|------------|-------------------|
| A real operator can tell why rows were accepted, rejected, held, or untouched without reading raw SQL/JSON | debugging clarity is partly a UX judgment | Open one mixed-outcome case and one strict failure case in the dev workbench; confirm the reasoning matches business intuition |
| The failure dictionary feels like a lookup handbook instead of a log dump | usefulness depends on discoverability and wording | Search for one known blocked pattern (for example “新增骨架” or “横白卡图”), verify the entry shows symptom, root cause, do first, and forbidden fix clearly |

## Validation Sign-Off

- [x] Every auto task has an automated verify path
- [x] No more than two tasks between meaningful regressions
- [x] Wave-local feedback stays under 240 seconds
- [x] Manual verification is reserved for clarity and handbook usability checks
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** planned
