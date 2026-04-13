---
phase: 05
slug: exception-repair-state-machine
status: planned
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-14
---

# Phase 05 — Validation Strategy

> Validation contract for the exception-repair-state-machine phase.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `unittest` |
| **Database** | PostgreSQL via `BOOKKEEPING_TEST_DSN` |
| **Quick run command** | `cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend tests.test_runtime tests.test_webapp -v` |
| **Full suite command** | `cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_quote_validation tests.test_postgres_backend tests.test_runtime tests.test_webapp -v` |
| **Estimated runtime** | ~210 seconds |

## Fast Smoke Commands

Use these after each task before the broader module-level gate:

| Focus | Command |
|-------|---------|
| Repair-case packaging lineage | `cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend.RepairCaseTests -v` |
| Runtime failure -> repair-case sync | `cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_runtime.RuntimeRepairCaseTests -v` |
| Replay baseline / handler sync | `cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_webapp.WebRepairCaseTests -v` |

## Sampling Rate

- After every task commit: run the task-local command in the verification map.
- After every task implementation step: run the matching fast smoke command first.
- After every plan wave: run the quick Phase 05 suite.
- Before phase verification: the full suite must be green on PostgreSQL.
- Max feedback latency: 210 seconds.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|--------|
| 05-01-01 | 01 | 1 | EXCP-01, EXCP-02 | T-05-01-01 / T-05-01-02 | repair cases are additive, one-per-exception, and keep `quote_parse_exceptions` plus validator tables as canonical evidence | integration | `cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend.RepairCaseTests -v` | ⬜ pending |
| 05-01-02 | 01 | 1 | EXCP-01, EXCP-02 | T-05-01-03 / T-05-01-04 | runtime failure packaging opens repair cases for parse failures and validator no-publish outcomes without mutating active facts | integration | `cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_runtime.RuntimeRepairCaseTests -v` | ⬜ pending |
| 05-02-01 | 02 | 2 | EXCP-02, EXCP-03 | T-05-02-01 / T-05-02-02 | every packaged case can persist one immutable baseline attempt tied to group-profile lineage | integration | `cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend.RepairCaseTests -v` | ⬜ pending |
| 05-02-02 | 02 | 2 | EXCP-03 | T-05-02-03 / T-05-02-04 | before/after replay comparisons stay candidate-only, do not fork duplicate repair cases, and remain durable through replay `quote_documents` plus validation runs | integration | `cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_webapp.WebRepairCaseTests -v` | ⬜ pending |
| 05-03-01 | 03 | 3 | EXCP-02, EXCP-03 | T-05-03-01 / T-05-03-02 | attempt history is append-only, baseline remains immutable, and repeated failure becomes escalation-ready rather than overwritten | integration | `cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend.RepairCaseTests -v` | ⬜ pending |
| 05-03-02 | 03 | 3 | EXCP-01, EXCP-02 | T-05-03-03 / T-05-03-04 | existing exception APIs surface repair-case summaries and keep handler-driven repair-case state synchronized without adding publisher or remediation controls | integration | `cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_webapp.WebRepairCaseTests -v` | ⬜ pending |

## Wave 0 Requirements

No separate Wave 0 is required. Phase 05 extends existing brownfield test surfaces directly:

- `tests.test_postgres_backend` covers additive schema, FK lineage, and state-transition persistence.
- `tests.test_runtime` covers runtime failure packaging into repair cases.
- `tests.test_webapp` covers replay baseline persistence, replay-to-case linking, handler synchronization, and exception-surface summaries.

If PostgreSQL is unavailable, execution must mark verification blocked instead of skipping it.

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Repair-case payload matches operator expectations for a real top-volume exception | EXCP-02 | the business meaning of packaged evidence still needs human judgment | Use one real corpus-backed exception, inspect the stored case row and baseline attempt, and confirm raw message, source line, group profile snapshot, validator summary, and remaining-line evidence all match the originating message |
| Before/after comparison language is useful without implying publish authority | EXCP-03 | wording drift can create false operator confidence | Trigger a replayed baseline through the existing exception flow and confirm the response describes candidate/validator deltas only, with no suggestion that active quotes were changed |

## Deferred Boundaries

- Phase 05 validation must reject any change that writes `quote_price_rows` or otherwise mutates active quote facts. That is Phase 03.
- Phase 05 validation must reject any change that executes `full_snapshot` or `delta_update` semantics beyond recording unresolved evidence. That is Phase 04.
- Phase 05 validation must reject any automated retry loop, retry cap enforcement, or fix proposal execution. That is Phase 06.

## Validation Sign-Off

- [x] Every auto task has an automated verification command.
- [x] Validation relies on PostgreSQL, not SQLite shortcuts.
- [x] Runtime, DB, and web replay surfaces are all covered.
- [x] No watch mode or speculative infra is required.
- [x] Deferred boundaries for Phase 03, Phase 04, and Phase 06 are explicit.
- [x] `nyquist_compliant: true` is set in frontmatter.

**Approval:** planned 2026-04-14
