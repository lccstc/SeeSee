# Phase 3: Fact Protection Publisher - Research

**Researched:** 2026-04-13 [VERIFIED: local environment date]
**Domain:** Guarded quote-fact publication in a PostgreSQL-backed brownfield runtime [VERIFIED: codebase `.planning/ROADMAP.md`; VERIFIED: codebase `AGENTS.md`]
**Confidence:** HIGH [VERIFIED: codebase audit; CITED: https://www.postgresql.org/docs/current/explicit-locking.html; CITED: https://www.psycopg.org/psycopg3/docs/basic/transactions.html]

<user_constraints>
## User Constraints (from CONTEXT.md)

No phase-specific `*-CONTEXT.md` existed in `.planning/phases/03-fact-protection-publisher/` at research time, so there were no additional locked per-phase decisions to copy verbatim. [VERIFIED: `node /Users/newlcc/.codex/get-shit-done/bin/gsd-tools.cjs init phase-op 3`]
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FACT-01 | Failed parse, validation, or publish attempts leave prior active quote facts untouched. [VERIFIED: codebase `.planning/REQUIREMENTS.md`] | Use one transaction-scoped publisher, remove per-helper commits, and lock per group before any active-row mutation. [VERIFIED: codebase `bookkeeping_core/database.py:1327-1468`; CITED: https://www.psycopg.org/psycopg3/docs/basic/transactions.html; CITED: https://www.postgresql.org/docs/current/explicit-locking.html] |
| FACT-02 | If a message produces no `publishable_rows`, the system performs no publish for that message. [VERIFIED: codebase `.planning/REQUIREMENTS.md`] | Make zero-`publishable_rows` a guarded publisher no-op before any deactivate/supersede/apply step. [VERIFIED: codebase `bookkeeping_core/quotes.py:675-699`; VERIFIED: codebase `.planning/ROADMAP.md`] |
| FACT-03 | No route, script, page action, Agent, or SubAgent can bypass validator and publisher safeguards to mutate active quotes directly. [VERIFIED: codebase `.planning/REQUIREMENTS.md`] | Route runtime, replay, and web actions through one publisher API and add an architecture test that forbids direct calls to quote-fact mutation helpers outside an allowlist. [VERIFIED: codebase `bookkeeping_core/runtime.py:21-32`; VERIFIED: codebase `bookkeeping_web/app.py:1012-1144`; VERIFIED: codebase `bookkeeping_web/app.py:1533-1545`; VERIFIED: codebase `tests/support/postgres_test_case.py:15-103`] |
</phase_requirements>

## Summary

The current brownfield runtime does not yet have publisher custody. `QuoteCaptureService.capture_from_message()` computes `publishable_rows`, then directly calls `deactivate_old_quotes_for_group()` before inserting any replacement rows, and each helper commits independently. [VERIFIED: codebase `bookkeeping_core/quotes.py:675-780`; VERIFIED: codebase `bookkeeping_core/database.py:1327-1468`] This means a failure after deactivate and before all replacement inserts can leave the wall in a corrupted intermediate state, which directly violates `FACT-01`. [VERIFIED: codebase `.planning/REQUIREMENTS.md`; VERIFIED: codebase `bookkeeping_core/database.py:1368-1378`; VERIFIED: codebase `bookkeeping_core/database.py:1432-1468`]

The safest repo-specific architecture is to introduce one guarded publisher in `bookkeeping_core/` and make every fact mutation go through it. [VERIFIED: codebase `AGENTS.md`; VERIFIED: codebase `.planning/PROJECT.md`; VERIFIED: codebase `.planning/ROADMAP.md`] That publisher should own a single transaction, take a transaction-level advisory lock per `source_group_key`, optionally lock the currently-live rows for that group with `SELECT ... FOR UPDATE`, decide no-op versus apply before any destructive write, and commit exactly once at the end. [CITED: https://www.psycopg.org/psycopg3/docs/basic/transactions.html; CITED: https://www.postgresql.org/docs/current/explicit-locking.html; CITED: https://www.postgresql.org/docs/current/functions-admin.html]

Replay must not remain a second publish implementation. `_replay_latest_quote_document_with_current_template()` currently repeats the same direct deactivate-and-upsert sequence from the web layer, and `/api/quotes/delete` directly deletes `quote_price_rows` without going through any validator or publisher semantics. [VERIFIED: codebase `bookkeeping_web/app.py:1012-1144`; VERIFIED: codebase `bookkeeping_web/app.py:1533-1545`] Phase 3 should collapse runtime publish, replay apply, and any future manual retract/apply operations into one publisher entrypoint, then add a structural test that fails if routes, scripts, or agents call low-level quote mutation helpers directly. [VERIFIED: codebase `bookkeeping_core/runtime.py:21-32`; VERIFIED: codebase `scripts/seed_quote_demo.py:183-205`; VERIFIED: codebase `tests/support/postgres_test_case.py:15-103`]

**Primary recommendation:** Implement a `QuoteFactPublisher` that owns the only public active-quote mutation API, wraps all mutation in one transaction, treats zero `publishable_rows` as a no-op, and backs the app-level custody with a partial unique index plus an architecture test. [VERIFIED: codebase audit; CITED: https://www.psycopg.org/psycopg3/docs/basic/transactions.html; CITED: https://www.postgresql.org/docs/current/indexes-partial.html; CITED: https://www.postgresql.org/docs/16/ddl-constraints.html]

## Repo Constraints

- Core business rules must live under `wxbot/bookkeeping-platform/bookkeeping_core/`, while `bookkeeping_web/app.py` and `pages.py` stay as route/display layers. [VERIFIED: codebase `AGENTS.md`]
- PostgreSQL is the production fact source, and SQLite is not the runtime fact source for this project. [VERIFIED: codebase `AGENTS.md`; VERIFIED: codebase `bookkeeping_core/database.py:2908-2918`]
- Parser/model/agent output may produce candidates, but may not directly publish quote facts. [VERIFIED: codebase `AGENTS.md`; VERIFIED: codebase `.planning/PROJECT.md`; VERIFIED: codebase `.planning/REQUIREMENTS.md`]
- Default-safe behavior is mandatory: failure must lead to “no update”, not to clearing or mis-inactivating historical active rows. [VERIFIED: codebase `AGENTS.md`; VERIFIED: codebase `.planning/PROJECT.md`; VERIFIED: codebase `.planning/REQUIREMENTS.md`]

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PostgreSQL | Local environment is `16.13`; current official docs show supported lines `18/17/16/15/14`. [VERIFIED: local env `psql --version`; CITED: https://www.postgresql.org/docs/current/explicit-locking.html] | System-of-record quote facts, transactional publish custody, row/advisory locking, and integrity constraints. [VERIFIED: codebase `AGENTS.md`; CITED: https://www.postgresql.org/docs/current/explicit-locking.html; CITED: https://www.postgresql.org/docs/current/indexes-partial.html] | The repo already requires a PostgreSQL DSN at runtime, and PostgreSQL gives the exact transaction, lock, and index primitives this phase needs without adding another service. [VERIFIED: codebase `bookkeeping_core/database.py:35-40`; VERIFIED: codebase `bookkeeping_core/database.py:2908-2918`; CITED: https://www.postgresql.org/docs/current/functions-admin.html] |
| `psycopg[binary]` | Repo pin: `>=3.3,<4`; local venv: `3.3.3`; PyPI latest shown: `3.3.3` released `2026-02-18`. [VERIFIED: codebase `wxbot/bookkeeping-platform/requirements-dev.txt`; VERIFIED: local env `wxbot/bookkeeping-platform/.venv/bin/python -c 'import psycopg; print(psycopg.__version__)'`; CITED: https://pypi.org/project/psycopg-binary/] | Python DB driver for the publisher transaction boundary. [VERIFIED: codebase `bookkeeping_core/database.py:2908-2918`] | Psycopg 3 transaction contexts and savepoint-backed nested transactions match this repo’s need to make quote publication atomic without introducing an ORM. [CITED: https://www.psycopg.org/psycopg3/docs/basic/transactions.html] |
| Python + `unittest` | Local Python `3.14.3`; psycopg-binary requires `>=3.10`; tests use stdlib `unittest`. [VERIFIED: local env `python3 --version`; CITED: https://pypi.org/project/psycopg-binary/; VERIFIED: codebase `tests/support/postgres_test_case.py:1-15`] | Runtime implementation and architecture/integration tests. [VERIFIED: codebase `bookkeeping_core/runtime.py:1-32`; VERIFIED: codebase `tests/test_webapp.py`; VERIFIED: codebase `tests/test_runtime.py`] | The repo already uses stdlib `unittest` and schema-per-test PostgreSQL isolation, so Phase 3 should extend that instead of adding a second test framework. [VERIFIED: codebase `tests/support/postgres_test_case.py:15-103`; VERIFIED: codebase `.planning/config.json`] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| PostgreSQL transaction-level advisory locks | Current PostgreSQL docs, section `9.28.10` / `13.3.5`. [CITED: https://www.postgresql.org/docs/current/functions-admin.html; CITED: https://www.postgresql.org/docs/current/explicit-locking.html] | Serialize publishes per `source_group_key` without introducing Redis or a second coordinator. [CITED: https://www.postgresql.org/docs/current/functions-admin.html] | Use exactly once per guarded publish transaction so two publishers for the same group cannot interleave deactivate/supersede/apply steps. [CITED: https://www.postgresql.org/docs/current/explicit-locking.html] |
| `SELECT ... FOR UPDATE` row locks | Current PostgreSQL docs, section `13.3.2`. [CITED: https://www.postgresql.org/docs/current/explicit-locking.html] | Lock currently-live rows that may be superseded or inactivated during publish. [CITED: https://www.postgresql.org/docs/current/explicit-locking.html] | Use after taking the per-group advisory lock and before mutating live rows, especially once Phase 4 adds `full_snapshot`/`delta_update` semantics. [CITED: https://www.postgresql.org/docs/current/explicit-locking.html; VERIFIED: codebase `.planning/ROADMAP.md`] |
| Partial unique index | Current PostgreSQL docs, section `11.8`. [CITED: https://www.postgresql.org/docs/current/indexes-partial.html] | DB-level backstop so only one live active row exists for a given quote identity. [CITED: https://www.postgresql.org/docs/current/indexes-partial.html] | Use as a safety net under the publisher for the “live active row” invariant; do not use it as a substitute for publish logic. [CITED: https://www.postgresql.org/docs/current/indexes-partial.html] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PostgreSQL transaction-level advisory lock | Redis/distributed lock service | Adds a second coordination system the repo does not currently operate; PostgreSQL already provides transaction-scoped advisory locks. [VERIFIED: codebase stack; CITED: https://www.postgresql.org/docs/current/functions-admin.html; CITED: https://www.postgresql.org/docs/current/explicit-locking.html] |
| Psycopg transaction context around the whole publish | Keep current helper-level `commit()` calls | Current helper-level commits create an intermediate-state corruption window between deactivate and insert. [VERIFIED: codebase `bookkeeping_core/database.py:1368-1378`; VERIFIED: codebase `bookkeeping_core/database.py:1432-1468`; CITED: https://www.psycopg.org/psycopg3/docs/basic/transactions.html] |
| Partial unique index for cross-row live-state invariant | `CHECK` constraint for “one active row” | PostgreSQL documents that `CHECK` constraints must not reference other table rows; cross-row invariants should use `UNIQUE`, `EXCLUDE`, or other mechanisms. [CITED: https://www.postgresql.org/docs/16/ddl-constraints.html] |
| One publisher API plus architecture test | Prompt/policy reminder to not call low-level helpers | Prompt discipline cannot stop a route or script from calling `deactivate_old_quotes_for_group()` or raw SQL. [VERIFIED: codebase `bookkeeping_web/app.py:1012-1144`; VERIFIED: codebase `bookkeeping_web/app.py:1533-1545`; VERIFIED: codebase `AGENTS.md`] |

**Installation:** Existing repo dependencies are sufficient; Phase 3 does not require a new library. [VERIFIED: codebase `wxbot/bookkeeping-platform/requirements-dev.txt`; VERIFIED: codebase `bookkeeping_core/database.py:2908-2918`]

```bash
cd wxbot/bookkeeping-platform
./.venv/bin/pip install -r requirements-dev.txt
```

**Version verification:** `requirements-dev.txt` already pins `psycopg[binary]>=3.3,<4`; the local venv has `3.3.3` installed; PyPI shows `3.3.3` as the latest release on `2026-02-18`. [VERIFIED: codebase `wxbot/bookkeeping-platform/requirements-dev.txt`; VERIFIED: local env `wxbot/bookkeeping-platform/.venv/bin/python -c 'import psycopg; print(psycopg.__version__)'`; CITED: https://pypi.org/project/psycopg-binary/]

## Architecture Patterns

### Recommended Project Structure
```text
wxbot/bookkeeping-platform/bookkeeping_core/
├── quote_publisher.py        # single public publish/apply/no-op API
├── quotes.py                 # parse/candidate capture only; no direct active-row mutation
├── database.py               # private quote mutation primitives + schema bootstrap
└── runtime.py                # runtime calls publisher, not raw DB quote helpers

wxbot/bookkeeping-platform/bookkeeping_web/
└── app.py                    # replay/admin actions call publisher or validation preview only

wxbot/bookkeeping-platform/tests/
├── test_quote_publisher.py   # atomic publish / failure preservation / zero-row no-op
└── test_quote_architecture.py # forbid direct quote mutation calls outside allowlist
```
[VERIFIED: codebase `bookkeeping_core/runtime.py:21-32`; VERIFIED: codebase `bookkeeping_web/app.py:1012-1144`; VERIFIED: codebase `bookkeeping_web/app.py:1533-1545`; VERIFIED: codebase test layout]

### Pattern 1: Single Custody Publisher
**What:** Add one publisher service that accepts a validated publish command and is the only public API allowed to mutate `quote_price_rows`. [VERIFIED: codebase `.planning/ROADMAP.md`; VERIFIED: codebase `.planning/REQUIREMENTS.md`]  
**When to use:** Use for runtime message applies, replay applies, and any future audited retract/apply action that changes active quote facts. [VERIFIED: codebase `bookkeeping_core/runtime.py:21-32`; VERIFIED: codebase `bookkeeping_web/app.py:1012-1144`; VERIFIED: codebase `bookkeeping_web/app.py:1533-1545`]  
**Example:**
```python
# Source: psycopg transaction contexts + PostgreSQL advisory and row locks
with psycopg.connect(dsn, autocommit=True) as conn:
    with conn.transaction():
        cur = conn.cursor()
        cur.execute("SELECT pg_advisory_xact_lock(%s)", (lock_key,))
        cur.execute(
            """
            SELECT id
            FROM quote_price_rows
            WHERE source_group_key = %s
              AND quote_status = 'active'
              AND expires_at IS NULL
            FOR UPDATE
            """,
            (source_group_key,),
        )
        # decide noop/apply, then write document + rows, then commit on context exit
```
`with conn.transaction()` starts a transaction, commits on clean exit, and rolls back on exception; nested uses become savepoints. [CITED: https://www.psycopg.org/psycopg3/docs/basic/transactions.html] `pg_advisory_xact_lock()` gives a transaction-level advisory lock; `FOR UPDATE` blocks concurrent writers on the same rows until the transaction ends. [CITED: https://www.postgresql.org/docs/current/functions-admin.html; CITED: https://www.postgresql.org/docs/current/explicit-locking.html]

### Pattern 2: No-Op Before Destructive Work
**What:** Decide whether the publish is `noop_zero_publishable`, `noop_validation_failed`, `applied`, or `failed` before calling any deactivate/supersede helper. [VERIFIED: codebase `.planning/REQUIREMENTS.md`; VERIFIED: codebase `.planning/ROADMAP.md`]  
**When to use:** Every publish attempt, including replay-triggered applies from exception handling. [VERIFIED: codebase `bookkeeping_web/app.py:1207-1316`]  
**Example:**
```python
# Source: repo requirement FACT-02
if not publishable_rows:
    return {
        "applied": False,
        "reason": "zero_publishable_rows",
        "mutated_active_facts": False,
    }
```
This must run before any call equivalent to `deactivate_old_quotes_for_group()` or `upsert_quote_price_row_with_history()`. [VERIFIED: codebase `bookkeeping_core/quotes.py:675-699`; VERIFIED: codebase `.planning/REQUIREMENTS.md`]

### Pattern 3: DB Backstop for Live-Row Invariant
**What:** Add a partial unique index over the live-row identity so the database refuses multiple simultaneously-live rows for the same group/SKU tuple. [CITED: https://www.postgresql.org/docs/current/indexes-partial.html]  
**When to use:** Use as a safety net under the publisher, not as a replacement for validator/publisher logic. [CITED: https://www.postgresql.org/docs/current/indexes-partial.html]  
**Example:**
```sql
-- Source: PostgreSQL partial unique index pattern adapted to quote_price_rows
CREATE UNIQUE INDEX quote_price_rows_one_live_row
ON quote_price_rows (
  source_group_key,
  card_type,
  country_or_currency,
  amount_range,
  form_factor,
  COALESCE(multiplier, '')
)
WHERE quote_status = 'active' AND expires_at IS NULL;
```
PostgreSQL documents that a partial unique index enforces uniqueness only among rows matching its predicate. [CITED: https://www.postgresql.org/docs/current/indexes-partial.html]

### Pattern 4: Structural Bypass Guard
**What:** Add an architecture test that fails if app/runtime/script modules call low-level quote-fact mutation helpers directly outside an allowlist. [VERIFIED: codebase `tests/support/postgres_test_case.py:15-103`; VERIFIED: codebase current bypass callsites]  
**When to use:** Use for `FACT-03`; this is the cheapest code-level guard available in Python without introducing DB role separation. [VERIFIED: codebase stack; VERIFIED: codebase `.planning/REQUIREMENTS.md`]  
**Example:**
```python
# Source: repo unittest stack
FORBIDDEN = {"deactivate_old_quotes_for_group", "upsert_quote_price_row_with_history"}
ALLOWED_FILES = {"bookkeeping_core/quote_publisher.py", "tests/"}

# Parse ASTs and fail if a forbidden attribute call appears outside ALLOWED_FILES.
```
This should guard runtime, web, and scripts, while still allowing test fixture setup where explicitly whitelisted. [VERIFIED: codebase `bookkeeping_core/runtime.py:21-32`; VERIFIED: codebase `bookkeeping_web/app.py:1012-1144`; VERIFIED: codebase `scripts/seed_quote_demo.py:183-205`]

### Anti-Patterns to Avoid
- **Deactivate-first outside a transaction:** Current code deactivates group rows before recording the new publish in the same atomic unit, which creates a loss window. [VERIFIED: codebase `bookkeeping_core/quotes.py:694-699`; VERIFIED: codebase `bookkeeping_core/database.py:1371-1378`]
- **Second publisher hidden in replay:** `_replay_latest_quote_document_with_current_template()` is a duplicate publish implementation in the web layer. [VERIFIED: codebase `bookkeeping_web/app.py:1012-1144`]
- **Direct row deletion route:** `/api/quotes/delete` directly deletes active rows with raw SQL and no publisher custody. [VERIFIED: codebase `bookkeeping_web/app.py:1533-1545`]
- **Cross-row correctness in `CHECK`:** PostgreSQL explicitly warns against using `CHECK` constraints for rules involving other table rows. [CITED: https://www.postgresql.org/docs/16/ddl-constraints.html]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Atomic publish boundary | A chain of helper methods that each call `commit()` | One psycopg transaction context around the full publish. | Psycopg 3 already provides commit/rollback/savepoint handling; the current per-helper commit style is the corruption vector. [VERIFIED: codebase `bookkeeping_core/database.py:1368-1378`; VERIFIED: codebase `bookkeeping_core/database.py:1432-1468`; CITED: https://www.psycopg.org/psycopg3/docs/basic/transactions.html] |
| Concurrency control | In-process Python lock or “last write wins” | `pg_advisory_xact_lock()` plus consistent lock order. | PostgreSQL advisory locks are built for application-defined resources and auto-release at transaction end when taken at xact scope. [CITED: https://www.postgresql.org/docs/current/explicit-locking.html; CITED: https://www.postgresql.org/docs/current/functions-admin.html] |
| Live-row uniqueness | App-side scan-and-hope only | Partial unique index on the live-row predicate. | PostgreSQL partial unique indexes enforce the subset invariant even if application code regresses. [CITED: https://www.postgresql.org/docs/current/indexes-partial.html] |
| Cross-row invariants in DDL | `CHECK` across other rows | `UNIQUE`/partial unique index or publisher logic. | PostgreSQL documents that `CHECK` cannot safely guarantee conditions involving other rows. [CITED: https://www.postgresql.org/docs/16/ddl-constraints.html] |
| Bypass prevention | Prompt reminders or review convention only | Architecture test plus removal/disablement of direct routes. | This repo already has direct mutation callsites; policy alone did not prevent them. [VERIFIED: codebase `bookkeeping_web/app.py:1012-1144`; VERIFIED: codebase `bookkeeping_web/app.py:1533-1545`; VERIFIED: codebase `AGENTS.md`] |

**Key insight:** This phase is primarily about transaction custody and structural enforcement, not smarter parsing. [VERIFIED: codebase `AGENTS.md`; VERIFIED: codebase `.planning/PROJECT.md`; VERIFIED: codebase `.planning/ROADMAP.md`]

## Common Pitfalls

### Pitfall 1: Split Commits Create a Corruption Window
**What goes wrong:** Old active rows are deactivated or superseded, then a later insert fails, leaving the wall partially or fully wrong. [VERIFIED: codebase `bookkeeping_core/database.py:1371-1378`; VERIFIED: codebase `bookkeeping_core/database.py:1408-1468`]  
**Why it happens:** The current helper methods call `commit()` independently, so a publish is not atomic. [VERIFIED: codebase `bookkeeping_core/database.py:1368-1378`; VERIFIED: codebase `bookkeeping_core/database.py:1467-1468`]  
**How to avoid:** Remove commits from the inner quote mutation helpers and commit once from the publisher transaction context. [CITED: https://www.psycopg.org/psycopg3/docs/basic/transactions.html; VERIFIED: codebase recommendation]  
**Warning signs:** A test that injects a failure between deactivate and insert changes board state even though publish returned failure. [VERIFIED: requirement FACT-01]

### Pitfall 2: Replay Becomes a Second Publisher
**What goes wrong:** Runtime and replay apply different write sequences, so fixes that look safe in replay still diverge from production behavior. [VERIFIED: codebase `bookkeeping_core/quotes.py:694-780`; VERIFIED: codebase `bookkeeping_web/app.py:1012-1144`]  
**Why it happens:** Replay currently reimplements publish logic in the web layer instead of calling a shared publisher. [VERIFIED: codebase `bookkeeping_web/app.py:1012-1144`]  
**How to avoid:** Replay should build the same publish command and call the same guarded publisher with an explicit mode. [VERIFIED: codebase architecture recommendation]  
**Warning signs:** Two codepaths need separate fixes whenever publish semantics change. [VERIFIED: codebase audit]

### Pitfall 3: Zero `publishable_rows` Still Causes Active-State Mutation
**What goes wrong:** A message with only rejected/held rows still clears or supersedes live facts. [VERIFIED: requirement FACT-02]  
**Why it happens:** Empty-or-invalid publish decisions are not treated as explicit no-ops before mutation. [VERIFIED: codebase `bookkeeping_core/quotes.py:675-699`]  
**How to avoid:** Make `publishable_rows == []` return before any deactivate/supersede step and test it directly. [VERIFIED: requirement FACT-02; VERIFIED: codebase recommendation]  
**Warning signs:** Publish result says `rows=0` but `quote_price_rows` history changes. [VERIFIED: requirement FACT-02]

### Pitfall 4: Deadlocks From Inconsistent Lock Ordering
**What goes wrong:** Two concurrent publishes block each other and PostgreSQL aborts one transaction. [CITED: https://www.postgresql.org/docs/current/explicit-locking.html]  
**Why it happens:** Explicit locks increase deadlock risk when callers acquire multiple locks in inconsistent order. [CITED: https://www.postgresql.org/docs/current/explicit-locking.html]  
**How to avoid:** Always acquire locks in the same order: advisory lock on `source_group_key` first, then row locks for the live rows being updated. [CITED: https://www.postgresql.org/docs/current/explicit-locking.html]  
**Warning signs:** Intermittent deadlock exceptions under concurrent publish tests. [CITED: https://www.postgresql.org/docs/current/explicit-locking.html]

### Pitfall 5: Using `CHECK` for a Cross-Row Invariant
**What goes wrong:** A schema rule appears to work in simple tests but cannot guarantee “only one live row” across rows. [CITED: https://www.postgresql.org/docs/16/ddl-constraints.html]  
**Why it happens:** PostgreSQL does not support `CHECK` constraints that depend on other table rows. [CITED: https://www.postgresql.org/docs/16/ddl-constraints.html]  
**How to avoid:** Use a partial unique index for the live-row invariant and keep business publish logic in code. [CITED: https://www.postgresql.org/docs/current/indexes-partial.html; CITED: https://www.postgresql.org/docs/16/ddl-constraints.html]  
**Warning signs:** Proposed DDL references the same table through a function or subquery inside `CHECK`. [CITED: https://www.postgresql.org/docs/16/ddl-constraints.html]

## Code Examples

Verified patterns from official sources:

### Atomic Publish Block With Psycopg 3
```python
# Source: https://www.psycopg.org/psycopg3/docs/basic/transactions.html
import psycopg

with psycopg.connect(dsn, autocommit=True) as conn:
    with conn.transaction():
        cur = conn.cursor()
        cur.execute("SELECT pg_advisory_xact_lock(%s)", (lock_key,))
        cur.execute(
            "SELECT id FROM quote_price_rows "
            "WHERE source_group_key = %s AND quote_status = 'active' "
            "AND expires_at IS NULL FOR UPDATE",
            (source_group_key,),
        )
        # apply publish batch here; exception => rollback
```
[CITED: https://www.psycopg.org/psycopg3/docs/basic/transactions.html; CITED: https://www.postgresql.org/docs/current/functions-admin.html; CITED: https://www.postgresql.org/docs/current/explicit-locking.html]

### Partial Unique Index For Live Rows
```sql
-- Source pattern: https://www.postgresql.org/docs/current/indexes-partial.html
CREATE UNIQUE INDEX quote_price_rows_one_live_row
ON quote_price_rows (
  source_group_key,
  card_type,
  country_or_currency,
  amount_range,
  form_factor,
  COALESCE(multiplier, '')
)
WHERE quote_status = 'active' AND expires_at IS NULL;
```
[CITED: https://www.postgresql.org/docs/current/indexes-partial.html]

### Repo Architecture Test Pattern
```python
# Source: repo unittest stack + FACT-03 requirement
import ast
from pathlib import Path
import unittest

FORBIDDEN = {"deactivate_old_quotes_for_group", "upsert_quote_price_row_with_history"}
ALLOWED = {"bookkeeping_core/quote_publisher.py"}

class QuoteArchitectureTests(unittest.TestCase):
    def test_only_publisher_mutates_quote_facts(self):
        for path in Path("wxbot/bookkeeping-platform").rglob("*.py"):
            rel = str(path.relative_to("wxbot/bookkeeping-platform"))
            if rel in ALLOWED or rel.startswith("tests/"):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute) and node.attr in FORBIDDEN:
                    self.fail(f"{rel} bypasses guarded publisher via {node.attr}")
```
[VERIFIED: codebase `tests/support/postgres_test_case.py:15-103`; VERIFIED: codebase `.planning/REQUIREMENTS.md`; VERIFIED: codebase current bypass callsites]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual commit discipline inside low-level helpers. [VERIFIED: codebase `bookkeeping_core/database.py:1327-1468`] | Psycopg 3 transaction contexts with nested savepoint support are the current documented pattern. [CITED: https://www.psycopg.org/psycopg3/docs/basic/transactions.html] | Psycopg 3 is current in PyPI at `3.3.3` on `2026-02-18`. [CITED: https://pypi.org/project/psycopg-binary/] | Phase 3 should lean into one transaction-owned publisher instead of adding more manual `commit()` points. [VERIFIED: codebase recommendation] |
| Pure app-side “scan then write” invariants. [VERIFIED: codebase `bookkeeping_core/database.py:1408-1436`] | PostgreSQL still treats partial unique indexes as the standard way to enforce subset uniqueness. [CITED: https://www.postgresql.org/docs/current/indexes-partial.html] | Current PostgreSQL docs are for version `18`, with supported lines `18/17/16/15/14`. [CITED: https://www.postgresql.org/docs/current/indexes-partial.html] | Use DB constraints as a backstop under the publisher so regressions fail closed. [VERIFIED: codebase recommendation] |
| Assuming a single process means no coordination is needed. [ASSUMED] | PostgreSQL advisory locks remain the documented application-defined lock primitive for awkward MVCC cases. [CITED: https://www.postgresql.org/docs/current/explicit-locking.html; CITED: https://www.postgresql.org/docs/current/functions-admin.html] | Current PostgreSQL 18 docs still document both session-level and transaction-level advisory locks. [CITED: https://www.postgresql.org/docs/current/explicit-locking.html] | Publish concurrency should be coordinated inside PostgreSQL, not with an in-memory lock. [VERIFIED: codebase recommendation] |

**Deprecated/outdated:**
- Direct web-layer quote deletion as a normal maintenance path is incompatible with Phase 3 custody requirements and should be disabled or replaced by an audited publisher-mediated retract flow. [VERIFIED: codebase `bookkeeping_web/app.py:1533-1545`; VERIFIED: codebase `.planning/REQUIREMENTS.md`]
- Duplicate publish implementations in runtime and replay are outdated for this roadmap because Phase 3 explicitly requires one guarded publisher. [VERIFIED: codebase `.planning/ROADMAP.md`; VERIFIED: codebase `bookkeeping_core/quotes.py:694-780`; VERIFIED: codebase `bookkeeping_web/app.py:1012-1144`]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Concurrent publishes for the same `source_group_key` are plausible enough in this brownfield runtime that a per-group advisory lock is worth the complexity. [ASSUMED] | State of the Art / Architecture Patterns | If concurrency is actually impossible in deployment, the lock is extra complexity; if concurrency is possible and we skip it, publish races remain. |

## Open Questions

1. **Should Phase 3 introduce a `quote_publish_attempts` table now, or defer publish-attempt evidence to Phase 7?**  
What we know: There is no existing publish-attempt table, and current quote rows only reference `quote_document_id`. [VERIFIED: codebase grep for `quote_publish*`; VERIFIED: codebase `bookkeeping_core/database.py`]  
What's unclear: Whether the team wants explicit custody/audit rows in Phase 3 or only atomicity plus blocked bypasses. [VERIFIED: codebase roadmap sequencing]  
Recommendation: Add a minimal publish-attempt record now if schema change is acceptable, because it gives no-op/failure custody and makes later operator evidence cheaper. [VERIFIED: brownfield schema extension allowed in `AGENTS.md`; VERIFIED: codebase `.planning/PROJECT.md`]

2. **Should `/api/quotes/delete` be removed immediately, or turned into an audited retract operation?**  
What we know: The current route directly executes `DELETE FROM quote_price_rows` and commits. [VERIFIED: codebase `bookkeeping_web/app.py:1533-1545`]  
What's unclear: Whether operators still rely on this endpoint for manual cleanup today. [VERIFIED: codebase has route, but usage was not measured in this session]  
Recommendation: For Phase 3, default to disable/remove it unless the user explicitly needs retract capability now; if retract is needed, make it a publisher-owned, audited operation instead of raw delete. [VERIFIED: requirement FACT-03; VERIFIED: codebase recommendation]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | Runtime and tests | ✓ [VERIFIED: local env `python3 --version`] | `3.14.3` [VERIFIED: local env `python3 --version`] | `wxbot/bookkeeping-platform/.venv/bin/python` is also present. [VERIFIED: local env `wxbot/bookkeeping-platform/.venv/bin/python --version`] |
| `psycopg[binary]` in project venv | Publisher implementation and PostgreSQL tests | ✓ [VERIFIED: local env `wxbot/bookkeeping-platform/.venv/bin/python -c 'import psycopg; print(psycopg.__version__)'`] | `3.3.3` [VERIFIED: local env `wxbot/bookkeeping-platform/.venv/bin/python -c 'import psycopg; print(psycopg.__version__)'`] | Install via `./.venv/bin/pip install -r requirements-dev.txt` if the venv drifts. [VERIFIED: codebase `wxbot/bookkeeping-platform/requirements-dev.txt`] |
| PostgreSQL client (`psql`) | Schema/index verification and local diagnostics | ✓ [VERIFIED: local env `psql --version`] | `16.13` [VERIFIED: local env `psql --version`] | Use a remote DSN if local server is not started. [VERIFIED: codebase `tests/support/postgres_test_case.py:11-23`] |
| PostgreSQL server on `127.0.0.1:5432` | Running the test suite against default local DSN | ✗ right now [VERIFIED: local env `pg_isready -h 127.0.0.1 -p 5432`] | — | Set `BOOKKEEPING_TEST_DSN` to a reachable PostgreSQL DSN or start the local server. [VERIFIED: codebase `tests/support/postgres_test_case.py:11-23`] |

**Missing dependencies with no fallback:**
- A reachable PostgreSQL server is currently missing for default local test execution. [VERIFIED: local env `pg_isready -h 127.0.0.1 -p 5432`; VERIFIED: codebase `tests/support/postgres_test_case.py:11-23`]

**Missing dependencies with fallback:**
- None beyond pointing `BOOKKEEPING_TEST_DSN` at another PostgreSQL instance. [VERIFIED: codebase `tests/support/postgres_test_case.py:11-23`]

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Python stdlib `unittest` with PostgreSQL schema-isolated `PostgresTestCase`. [VERIFIED: codebase `tests/support/postgres_test_case.py:1-103`] |
| Config file | None; tests are discovered as Python modules under `wxbot/bookkeeping-platform/tests/`. [VERIFIED: codebase tree; VERIFIED: codebase `README.md:94-103`] |
| Quick run command | `cd wxbot/bookkeeping-platform && ./.venv/bin/python -m unittest tests.test_webapp -v` [VERIFIED: codebase `README.md:94-95`; VERIFIED: local env `.venv/bin/python --version`] |
| Full suite command | `cd wxbot/bookkeeping-platform && ./.venv/bin/python -m unittest -v tests.test_ingestion_alignment tests.test_periods tests.test_reporting tests.test_analytics tests.test_webapp tests.test_postgres_backend` [VERIFIED: codebase `README.md:96-103`] |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FACT-01 | A publish failure after lock acquisition but before commit leaves prior active facts unchanged. [VERIFIED: requirement FACT-01] | integration | `cd wxbot/bookkeeping-platform && ./.venv/bin/python -m unittest tests.test_quote_publisher.QuoteFactPublisherTests.test_publish_failure_preserves_existing_active_rows -v` | ❌ Wave 0 [VERIFIED: codebase test audit] |
| FACT-02 | Zero `publishable_rows` returns no-op and does not mutate active facts. [VERIFIED: requirement FACT-02] | integration | `cd wxbot/bookkeeping-platform && ./.venv/bin/python -m unittest tests.test_quote_publisher.QuoteFactPublisherTests.test_zero_publishable_rows_is_noop -v` | ❌ Wave 0 [VERIFIED: codebase test audit] |
| FACT-03 | Runtime/web/scripts cannot call low-level quote mutation helpers outside the guarded publisher. [VERIFIED: requirement FACT-03] | architecture | `cd wxbot/bookkeeping-platform && ./.venv/bin/python -m unittest tests.test_quote_architecture.QuoteArchitectureTests.test_only_publisher_mutates_quote_facts -v` | ❌ Wave 0 [VERIFIED: codebase test audit] |

### Sampling Rate
- **Per task commit:** `cd wxbot/bookkeeping-platform && ./.venv/bin/python -m unittest tests.test_quote_publisher tests.test_quote_architecture -v` [VERIFIED: repo test stack]
- **Per wave merge:** `cd wxbot/bookkeeping-platform && ./.venv/bin/python -m unittest tests.test_webapp tests.test_runtime tests.test_quote_publisher tests.test_quote_architecture -v` [VERIFIED: repo test stack]
- **Phase gate:** Full suite green before `/gsd-verify-work`. [VERIFIED: codebase `.planning/config.json`]

### Wave 0 Gaps
- [ ] `wxbot/bookkeeping-platform/tests/test_quote_publisher.py` — atomic publish, rollback preservation, and zero-row no-op coverage for `FACT-01` and `FACT-02`. [VERIFIED: codebase test audit]
- [ ] `wxbot/bookkeeping-platform/tests/test_quote_architecture.py` — structural allowlist test for `FACT-03`. [VERIFIED: codebase test audit]
- [ ] `wxbot/bookkeeping-platform/tests/test_webapp.py` additions — prove `/api/quotes/delete` is disabled or routed through the guarded path. [VERIFIED: codebase `bookkeeping_web/app.py:1533-1545`; VERIFIED: codebase existing `test_webapp.py` coverage audit]
- [ ] Reachable PostgreSQL test DSN — default local port is not accepting connections right now. [VERIFIED: local env `pg_isready -h 127.0.0.1 -p 5432`] 

## Security Domain

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no for this phase’s core publisher logic. [VERIFIED: phase scope in `.planning/ROADMAP.md`] | Existing route auth/admin password remains orthogonal to publish custody. [VERIFIED: codebase `bookkeeping_web/app.py`] |
| V3 Session Management | no for this phase’s core publisher logic. [VERIFIED: phase scope in `.planning/ROADMAP.md`] | Not a primary concern of active-quote mutation custody. [VERIFIED: phase scope] |
| V4 Access Control | yes. [VERIFIED: requirement FACT-03] | Remove raw delete/bypass routes and enforce one publisher entrypoint with architecture tests. [VERIFIED: codebase `bookkeeping_web/app.py:1533-1545`; VERIFIED: codebase recommendation] |
| V5 Input Validation | yes. [VERIFIED: requirement FACT-02; VERIFIED: roadmap dependency on Phase 2 validators] | Publisher only accepts already-validated publish commands and explicitly no-ops when `publishable_rows` is empty. [VERIFIED: codebase `.planning/ROADMAP.md`; VERIFIED: requirement FACT-02] |
| V6 Cryptography | no. [VERIFIED: phase scope in `.planning/ROADMAP.md`] | Not applicable to quote-fact publication custody. [VERIFIED: phase scope] |

### Known Threat Patterns for This Stack
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Unauthorized fact mutation path in app code | Tampering | Remove raw delete route, route replay/runtime through publisher, add architecture allowlist test. [VERIFIED: codebase `bookkeeping_web/app.py:1012-1144`; VERIFIED: codebase `bookkeeping_web/app.py:1533-1545`; VERIFIED: requirement FACT-03] |
| Concurrent publish race on same group | Tampering | Transaction-level advisory lock on `source_group_key`, then row locks on live rows. [CITED: https://www.postgresql.org/docs/current/functions-admin.html; CITED: https://www.postgresql.org/docs/current/explicit-locking.html] |
| Partial failure clears wall | Tampering / Availability | One transaction for the whole publish so exception => rollback. [CITED: https://www.psycopg.org/psycopg3/docs/basic/transactions.html; VERIFIED: requirement FACT-01] |
| Cross-row invariant regression | Tampering | Partial unique index over live-row predicate. [CITED: https://www.postgresql.org/docs/current/indexes-partial.html] |
| Long-held locks causing stalls | Availability | Keep publisher transaction short and never wait for user input inside it. [CITED: https://www.postgresql.org/docs/current/explicit-locking.html] |

## Sources

### Primary (HIGH confidence)
- Codebase audit: `.planning/REQUIREMENTS.md`, `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `AGENTS.md`, `bookkeeping_core/quotes.py`, `bookkeeping_core/database.py`, `bookkeeping_core/runtime.py`, `bookkeeping_web/app.py`, `tests/support/postgres_test_case.py` — current mutation paths, project constraints, and test stack. [VERIFIED: codebase]
- Psycopg 3 transactions documentation — transaction contexts, rollback semantics, nested transaction/savepoint behavior. [CITED: https://www.psycopg.org/psycopg3/docs/basic/transactions.html]
- PostgreSQL explicit locking documentation — row locks, advisory locks, deadlock guidance, transaction-end lock release semantics. [CITED: https://www.postgresql.org/docs/current/explicit-locking.html]
- PostgreSQL advisory lock functions documentation — `pg_advisory_xact_lock()` and related functions. [CITED: https://www.postgresql.org/docs/current/functions-admin.html]
- PostgreSQL partial indexes documentation — partial unique index pattern. [CITED: https://www.postgresql.org/docs/current/indexes-partial.html]
- PostgreSQL constraints documentation — warning that `CHECK` should not enforce cross-row conditions. [CITED: https://www.postgresql.org/docs/16/ddl-constraints.html]

### Secondary (MEDIUM confidence)
- PyPI `psycopg-binary` page — current package release and Python-version metadata. [CITED: https://pypi.org/project/psycopg-binary/]

### Tertiary (LOW confidence)
- None. [VERIFIED: research log]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - the repo already uses PostgreSQL + psycopg, and the supporting transaction/lock/index features are documented in current official sources. [VERIFIED: codebase `bookkeeping_core/database.py`; CITED: https://www.postgresql.org/docs/current/explicit-locking.html; CITED: https://www.psycopg.org/psycopg3/docs/basic/transactions.html]
- Architecture: HIGH - the recommendation directly addresses the observed bypasses and corruption window in current code and uses official transaction/locking primitives. [VERIFIED: codebase `bookkeeping_core/quotes.py:675-780`; VERIFIED: codebase `bookkeeping_web/app.py:1012-1144`; VERIFIED: codebase `bookkeeping_web/app.py:1533-1545`; CITED: https://www.postgresql.org/docs/current/functions-admin.html]
- Pitfalls: HIGH - each pitfall is either present in current code or documented by PostgreSQL/psycopg. [VERIFIED: codebase audit; CITED: https://www.postgresql.org/docs/16/ddl-constraints.html; CITED: https://www.postgresql.org/docs/current/explicit-locking.html]

**Research date:** 2026-04-13 [VERIFIED: local environment date]
**Valid until:** 2026-05-13 for repo findings; re-check package and PostgreSQL doc versions if planning slips beyond 30 days. [CITED: https://pypi.org/project/psycopg-binary/; CITED: https://www.postgresql.org/docs/current/explicit-locking.html]
