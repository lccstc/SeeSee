---
phase: 01
slug: candidate-contract-foundation
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-14
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `unittest` |
| **Config file** | none — repo uses `tests/support/postgres_test_case.py` and explicit commands |
| **Quick run command** | `cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend tests.test_runtime tests.test_webapp -v` |
| **Full suite command** | `cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest -v` |
| **Estimated runtime** | ~120 seconds |

---

## Sampling Rate

- **After every task commit:** Run the targeted `unittest` module(s) touched by the change.
- **After every plan wave:** Run the quick Phase 1 suite.
- **Before `/gsd-verify-work`:** Full suite must be green against PostgreSQL.
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | EVID-01 | T-01-01 | Candidate header + row persistence retains raw message, sender, chat, time, source line, and evidence without touching `quote_price_rows` | integration | `cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend -v` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | CAND-01 | T-01-02 | Runtime capture persists candidates only and does not deactivate/upsert active facts | integration | `cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_runtime -v` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 2 | CAND-02 | T-01-03 | Replay and exception save persist a new candidate run with parser lineage and snapshot hypothesis, but do not refresh the active board | integration | `cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_webapp -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `wxbot/bookkeeping-platform/tests/test_postgres_backend.py` — add candidate schema and persistence coverage for `quote_documents` metadata and `quote_candidate_rows`
- [ ] `wxbot/bookkeeping-platform/tests/test_runtime.py` — assert runtime candidate capture does not mutate active quote facts
- [ ] `wxbot/bookkeeping-platform/tests/test_webapp.py` — replace replay / harvest-save board-refresh assertions with candidate-only replay assertions
- [ ] PostgreSQL test availability at `127.0.0.1:5432` — current machine may need DB startup or alternate test DSN before execution

*If environment access remains unavailable, execution plans must explicitly flag DB-backed verification as blocked rather than silently skipping it.*

---

## Manual-Only Verifications

All Phase 1 requirement behaviors should have automated verification. Manual inspection is optional for debugging candidate payload shape, but not the acceptance gate.

---

## Validation Sign-Off

- [x] All tasks have an automated verification target or explicit Wave 0 dependency
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers current missing test references
- [x] No watch-mode flags
- [x] Feedback latency < 120s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-04-14
