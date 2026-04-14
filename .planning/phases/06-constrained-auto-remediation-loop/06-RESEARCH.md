# Phase 06: Constrained Auto-Remediation Loop - Research

**Researched:** 2026-04-14  
**Domain:** Bounded, system-owned remediation on top of the Phase 05 repair-case substrate for the quote-wall parser pipeline [VERIFIED: `.planning/ROADMAP.md`; `.planning/REQUIREMENTS.md`; `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`]  
**Confidence:** MEDIUM [VERIFIED: `.planning/ROADMAP.md`; `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md`; `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`]

<user_constraints>
## User Constraints

No `06-CONTEXT.md` exists in the phase directory at research time, so the constraints below are copied from the user request instead of a phase context file. [VERIFIED: phase init via `gsd-tools init phase-op`; user request]

### Locked Decisions
- One-group-one-profile remains the main architecture. [VERIFIED: user request; `AGENTS.md`; `.planning/PROJECT.md`]
- Default repair priority order should be `group profile -> group section -> bootstrap -> shared rule -> global core`. [VERIFIED: user request; `.planning/ROADMAP.md`]
- Do not turn the LLM into the rule source or publisher. [VERIFIED: user request; `AGENTS.md`; `.planning/PROJECT.md`]
- System owns final custody; subagents only propose repairs. [VERIFIED: user request; `AGENTS.md`; `.planning/PROJECT.md`; `.planning/ROADMAP.md`]
- No remediation step may mutate active quote facts directly. [VERIFIED: user request; `AGENTS.md`; `.planning/REQUIREMENTS.md`; `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md`]
- This phase is about constrained remediation workflow, not publisher or snapshot semantics. [VERIFIED: user request; `.planning/ROADMAP.md`]
- The workflow must be iterative: failure package -> subagent repair attempt -> system replay/validator -> failure log stacking -> retry with history -> max 3 attempts -> escalate to main agent/human. [VERIFIED: user request]
- Avoid regex hell; favor group-profile grammar evolution and deterministic artifacts. [VERIFIED: user request; `AGENTS.md`; `.planning/PROJECT.md`]

### Claude's Discretion
- Exact additive schema for proposal metadata, as long as Phase 05 append-only attempt history remains authoritative. [VERIFIED: `.planning/phases/05-exception-repair-state-machine/05-RESEARCH.md`; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`]
- Exact executor shape for staged writes and replay/validator/regression gates, as long as active quote facts remain untouched. [VERIFIED: user request; `.planning/REQUIREMENTS.md`; `wxbot/bookkeeping-platform/tests/test_webapp.py`]
- Exact plan split into 2-3 executable plans. [VERIFIED: user request; `.planning/ROADMAP.md`]

### Deferred Ideas (OUT OF SCOPE)
- Guarded publisher ownership and active-fact mutation control remain Phase 03. [VERIFIED: user request; `.planning/ROADMAP.md`; `.planning/REQUIREMENTS.md`]
- `full_snapshot` / `delta_update` execution semantics remain Phase 04. [VERIFIED: user request; `.planning/ROADMAP.md`; `.planning/REQUIREMENTS.md`]
- Operator workbench UX remains Phase 07, although Phase 06 should emit data that Phase 07 can surface. [VERIFIED: `.planning/ROADMAP.md`]
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INDU-01 | System drives repair cases through a constrained remediation workflow with bounded attempts, cumulative failure logs, and escalation after repeated failure. [VERIFIED: `.planning/REQUIREMENTS.md`] | Extend Phase 05 attempt rows with proposal metadata, keep attempts append-only, add an explicit `max_attempts=3` case budget, and make the system executor own replay/validator/regression gates plus escalation rollups. [VERIFIED: user request; `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`] |
| INDU-02 | User can promote repeated exception patterns into deterministic fixes such as group profiles, sections, bootstrap configs, shared rules, scripts, skills, or unit tests, prioritizing group-level fixes before global parser changes. [VERIFIED: `.planning/REQUIREMENTS.md`] | Use existing group-profile merge helpers, bootstrap profile generator, scoped dictionary aliases, and repo tests as the only absorption targets; require repeated cross-group proof before shared/global promotion. [VERIFIED: user request; `wxbot/bookkeeping-platform/bookkeeping_web/app.py`; `wxbot/bookkeeping-platform/scripts/bootstrap_quote_group_profiles.py`; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`] |
</phase_requirements>

## Summary

Phase 05 already gives Phase 06 the right substrate: runtime and replay failures open durable `quote_repair_cases`, each case can freeze profile/template evidence, baseline replay is candidate-only, attempts are append-only, and rollups already expose `attempt_count`, `failure_log_json`, and `escalation_state`. [VERIFIED: `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md`; `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`] What is still missing is proposal custody: the current attempt model does not record proposal scope/kind/artifact, the current escalation heuristic trips after two non-better attempts instead of the requested fixed budget of three, and there is no system-owned executor that constrains what a subagent may propose or where a successful fix may be absorbed. [VERIFIED: user request; `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`]

The safest brownfield direction is to keep Phase 05 tables, extend attempt rows with deterministic proposal metadata, and introduce one remediation executor that is the only component allowed to stage proposal artifacts, run replay/validator/regression gates, and absorb a fix into deterministic targets. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`; `wxbot/bookkeeping-platform/bookkeeping_web/app.py`] Subagents should never write `quote_group_profiles`, `quote_dictionary_aliases`, or repo code directly; they should emit a bounded proposal artifact that the system validates against the current repair case's allowed scope. [VERIFIED: user request; `AGENTS.md`; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`]

**Primary recommendation:** Keep subagents proposal-only, add explicit scope/kind/budget metadata to repair attempts, and let a system-owned executor enforce `group_profile -> group_section -> bootstrap -> shared_rule -> global_core` with replay, validator, regression, and max-3-attempt escalation gates before any absorption. [VERIFIED: user request; `.planning/ROADMAP.md`; `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`; `wxbot/bookkeeping-platform/bookkeeping_web/app.py`]

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.14.3 [VERIFIED: local env `wxbot/bookkeeping-platform/.venv/bin/python --version`] | Existing runtime for repair-case state, parser logic, replay helpers, and tests. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`; `wxbot/bookkeeping-platform/bookkeeping_web/app.py`] | Phase 06 can extend current services without introducing a second runtime. [VERIFIED: `AGENTS.md`; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`] |
| PostgreSQL | `psql` CLI 16.13 available; local server at `127.0.0.1:5432` was not responding during research. [VERIFIED: local env `psql --version`; `pg_isready -h 127.0.0.1 -p 5432`] | Formal persistence for repair cases, attempts, profiles, aliases, candidate documents, and validation runs. [VERIFIED: `AGENTS.md`; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`] | Phase 06 needs additive relational state and append-only attempt lineage, not ad hoc files. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`; `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md`] |
| psycopg | 3.3.3 [VERIFIED: `.planning/phases/05-exception-repair-state-machine/05-RESEARCH.md`] | Existing PostgreSQL driver for DB helpers and test schemas. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`; `wxbot/bookkeeping-platform/tests/support/postgres_test_case.py`] | No new DB access layer is needed. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `unittest` | stdlib with Python 3.14.3 [VERIFIED: local env `python3 --version`; `wxbot/bookkeeping-platform/tests/`] | Existing test framework for repair-case, runtime, replay, and bootstrap regressions. [VERIFIED: `AGENTS.md`; `wxbot/bookkeeping-platform/tests/test_postgres_backend.py`; `wxbot/bookkeeping-platform/tests/test_runtime.py`; `wxbot/bookkeeping-platform/tests/test_webapp.py`; `wxbot/bookkeeping-platform/tests/test_bootstrap_quote_group_profiles.py`] | Use for every Phase 06 gate and Wave 0 test gap. [VERIFIED: `AGENTS.md`; `.planning/config.json`] |
| Existing repair-case services | repo-local [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`] | Packages cases, creates baseline attempts, records append-only repair attempts, and computes rollups. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`] | Extend instead of replacing for proposal metadata, budget, and executor orchestration. [VERIFIED: `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md`] |
| Existing replay helper | repo-local [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_web/app.py`] | Replays the latest quote document with current template/profile while keeping `mutated_active_facts: False`. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_web/app.py`; `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md`] | Use as the proof engine for every remediation attempt. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`; `wxbot/bookkeeping-platform/tests/test_webapp.py`] |
| Bootstrap profile generator | repo-local [VERIFIED: `wxbot/bookkeeping-platform/scripts/bootstrap_quote_group_profiles.py`] | Produces deterministic `group-parser` profile payloads from approved fixtures without touching persistence. [VERIFIED: `wxbot/bookkeeping-platform/scripts/bootstrap_quote_group_profiles.py`; `wxbot/bookkeeping-platform/tests/test_bootstrap_quote_group_profiles.py`] | Use only for `missing_group_template` / `missing_template_config` style cases after approved-fixture proof. [VERIFIED: `wxbot/bookkeeping-platform/scripts/bootstrap_quote_group_profiles.py`; `wxbot/bookkeeping-platform/tests/test_runtime.py`] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Extend Phase 05 attempt rows with proposal metadata | Create a parallel remediation table set | A parallel table set duplicates already-correct append-only attempt lineage and makes Phase 05 summaries less authoritative. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`; `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md`] |
| System-owned staged executor | Let subagents write profiles/code directly | Direct writes violate system custody, widen blast radius, and make replay-gated rollback harder. [VERIFIED: user request; `AGENTS.md`; `.planning/PROJECT.md`] |
| Group-first promotion ladder | Promote shared/global fixes after the first local success | Single-case promotion pushes the system toward a global parser and raises regression risk across unrelated groups. [VERIFIED: user request; `AGENTS.md`; `.planning/PROJECT.md`; `.planning/ROADMAP.md`] |

**Installation:** No new third-party package is recommended for Phase 06. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`; `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`]  
**Version verification:** Python `3.14.3`, Node `v25.9.0`, npm `11.12.1`, and `psql 16.13` are installed locally; PostgreSQL server availability is currently missing on `127.0.0.1:5432`. [VERIFIED: local env `node --version`; `npm --version`; `python3 --version`; `psql --version`; `pg_isready -h 127.0.0.1 -p 5432`]

## Architecture Patterns

### Recommended Project Structure
```text
wxbot/bookkeeping-platform/
├── bookkeeping_core/
│   ├── repair_cases.py          # extend attempt metadata, budgeting, executor orchestration
│   ├── database.py              # additive columns/helpers for remediation proposals and gates
│   ├── quotes.py                # reuse parser/profile resolution, no direct fact writes
│   └── remediation.py           # optional small module for staged proposal apply/rollback
├── bookkeeping_web/
│   └── app.py                   # later read/debug surfaces only; not the executor authority
├── scripts/
│   └── bootstrap_quote_group_profiles.py
└── tests/
    ├── test_postgres_backend.py
    ├── test_runtime.py
    ├── test_webapp.py
    └── test_bootstrap_quote_group_profiles.py
```

### 1. Repair-Case State / Attempt Model Needed Beyond Phase 5

Phase 05 already persists case lifecycle, baseline linkage, append-only attempts, and cumulative failure logs; Phase 06 should reuse that model rather than adding a second workflow object. [VERIFIED: `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md`; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`; `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`] The minimum missing state is proposal metadata, allowed scope, fixed budget, and per-gate results. [VERIFIED: user request; `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`]

**Recommended additive fields on `quote_repair_case_attempts`:**

| Field | Purpose | Why add it |
|-------|---------|------------|
| `proposal_scope` | `group_profile`, `group_section`, `bootstrap`, `shared_rule`, or `global_core` [VERIFIED: user request] | Lets the executor reject out-of-order or over-broad proposals before any replay. [VERIFIED: user request; `.planning/ROADMAP.md`] |
| `proposal_kind` | Deterministic artifact type such as `profile_defaults_patch`, `section_merge`, `bootstrap_payload`, `dictionary_alias_upsert`, or `core_patch`. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`; `wxbot/bookkeeping-platform/bookkeeping_web/app.py`; `wxbot/bookkeeping-platform/scripts/bootstrap_quote_group_profiles.py`] | Separates "where" from "what" and keeps attempts queryable. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`] |
| `proposal_payload_json` | The normalized artifact the subagent proposed. [ASSUMED] | Needed so attempts remain reproducible and auditable after prompt context is gone. [ASSUMED] |
| `gate_summary_json` | Replay/validator/regression gate results for the attempt. [VERIFIED: user request; `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`] | Prevents success/failure from collapsing into one freeform note. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`] |
| `absorbed_target` / `absorbed_at` | Where a successful attempt was actually absorbed. [ASSUMED] | Distinguishes "proposal passed in staging" from "system absorbed it". [ASSUMED] |

**Recommended additive state on `quote_repair_cases`:**

| Field | Purpose | Recommendation |
|-------|---------|----------------|
| `max_attempts` | Freeze the budget per case. [VERIFIED: user request] | Store `3` explicitly so future phases do not reinterpret historical cases. [VERIFIED: user request] |
| `current_scope` | Next allowed proposal scope. [VERIFIED: user request] | Seed with `group_profile` and advance only when lower scopes are exhausted or disproven. [VERIFIED: user request; `.planning/PROJECT.md`] |
| `case_summary_json.next_action` | Planner/operator hint such as `retry_group_section` or `escalate_shared_rule`. [ASSUMED] | Keep most derived guidance in rollup JSON instead of widening the column surface too much. [ASSUMED] |

**State recommendation:** keep the existing case lifecycle enums for coarse workflow state, but add attempt-level gate phases such as `proposal_recorded`, `scope_rejected`, `replay_failed`, `validator_failed`, `regression_failed`, and `ready_to_absorb` inside `gate_summary_json` rather than exploding the case-level enum list. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`] This is the smallest brownfield change that still makes Phase 06 auditable. [VERIFIED: `AGENTS.md`; `.planning/PROJECT.md`]

### 2. Bounded Remediation Attempt Protocol

Use one system-owned remediation executor with this protocol. [VERIFIED: user request; `.planning/ROADMAP.md`; `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`]

1. System selects a `ready_for_attempt` or `attempt_failed` case, reads its baseline attempt, prior failure log, current scope, and remaining budget. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`]
2. System packages a bounded prompt/input bundle for the subagent: raw message, source-line residue, frozen profile snapshot, baseline comparison, prior failed proposals, and the one allowed `proposal_scope`. [VERIFIED: user request; `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md`; `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`]
3. Subagent returns exactly one deterministic proposal artifact; no direct file, DB, or page write is allowed. [VERIFIED: user request; `AGENTS.md`; `.planning/PROJECT.md`]
4. System normalizes the proposal into `proposal_payload_json`, rejects it immediately if the scope or artifact kind exceeds the case's allowed scope, and records that as a failed attempt. [VERIFIED: user request; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`] 
5. System stages the proposal in an isolated apply layer, runs replay, validator, and scope-specific regressions, and only then marks the attempt absorbable or failed. [VERIFIED: user request; `wxbot/bookkeeping-platform/bookkeeping_web/app.py`; `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`] 
6. If the attempt fails, the executor appends a new failure-log entry and feeds the full stacked history into the next retry. [VERIFIED: user request; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`] 
7. After the third failed attempt, or earlier when the next legal scope is shared/global, the case escalates to main-agent/human. [VERIFIED: user request]

### 3. Safe Write Scopes for Subagents

Subagents should be proposal-only. [VERIFIED: user request; `AGENTS.md`; `.planning/PROJECT.md`] The system executor may perform staged writes; only the system may absorb a passed proposal into a real target. [VERIFIED: user request; `.planning/REQUIREMENTS.md`; `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md`]

| Scope | What subagent may emit | What the system may stage | What the system may absorb after gates | Never allowed |
|------|-------------------------|----------------------------|----------------------------------------|---------------|
| `group_profile` | Patch to owning group's defaults/parser/template config for one `platform + chat_id`. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`] | In-memory or temp-db `quote_group_profiles` overlay. [ASSUMED] | One `quote_group_profiles` row via `upsert_quote_group_profile(...)`. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`] | Direct write to live profile by subagent. [VERIFIED: user request] |
| `group_section` | One derived section merge artifact. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_web/app.py`] | `_merge_strict_section_template_config(...)` or `_merge_group_parser_template_config(...)` against a staged config. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_web/app.py`] | Updated owning `template_config` only. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`; `wxbot/bookkeeping-platform/bookkeeping_web/app.py`] | Freeform regex bundle spanning multiple groups. [VERIFIED: user request; `AGENTS.md`] |
| `bootstrap` | Approved-fixture bootstrap request or payload. [VERIFIED: `wxbot/bookkeeping-platform/scripts/bootstrap_quote_group_profiles.py`] | `build_bootstrap_profile_payload(...)` output in staging. [VERIFIED: `wxbot/bookkeeping-platform/scripts/bootstrap_quote_group_profiles.py`] | One owning `quote_group_profiles` upsert after approved-fixture replay proof. [VERIFIED: `wxbot/bookkeeping-platform/tests/test_bootstrap_quote_group_profiles.py`; `wxbot/bookkeeping-platform/tests/test_runtime.py`] | Generating bootstrap from unapproved fixtures. [VERIFIED: `wxbot/bookkeeping-platform/tests/test_bootstrap_quote_group_profiles.py`] |
| `shared_rule` | Scoped alias or reusable deterministic rule proposal. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`; `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py`] | Temp alias rows or temp reusable rule branch. [ASSUMED] | `quote_dictionary_aliases` rows first; code only if alias/config cannot express the fix. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`; `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py`] | Jumping to global code for a single-group formatting issue. [VERIFIED: user request; `.planning/PROJECT.md`] |
| `global_core` | Patch proposal only. [VERIFIED: user request] | Temp worktree or staged patch for repo tests. [ASSUMED] | Main-agent/human-reviewed code change in `bookkeeping_core/quotes.py`, `template_engine.py`, or builtin alias sources. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py`; `wxbot/bookkeeping-platform/bookkeeping_core/template_engine.py`] | Auto-apply by subagent. [VERIFIED: user request] |

**Hard denylist:** no subagent may write `quote_price_rows`, mutate active quote facts, mark publish decisions, resolve cases as `closed_resolved` without gates, or bypass validator custody. [VERIFIED: user request; `AGENTS.md`; `.planning/REQUIREMENTS.md`; `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md`]

### 4. Group-First Promotion Order and Promotion Criteria

The promotion ladder should be strict, not advisory. [VERIFIED: user request]

| Order | Scope | Use when | Promote upward only when |
|------|-------|----------|---------------------------|
| 1 | `group_profile` | Failure is explainable by missing or wrong owning-group defaults or parser template selection. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`; `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py`] | Lower-cost group-default change cannot express the missing structure. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py`] |
| 2 | `group_section` | The group already has a profile, but one new section/header grammar needs to be merged. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_web/app.py`] | Two attempts at group-local grammar evolution fail or the same shape appears in multiple groups. [VERIFIED: user request; `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`] |
| 3 | `bootstrap` | The case is effectively `missing_group_template` / `missing_template_config` and an approved fixture can seed a conservative group parser. [VERIFIED: `wxbot/bookkeeping-platform/tests/test_runtime.py`; `wxbot/bookkeeping-platform/scripts/bootstrap_quote_group_profiles.py`] | No approved fixture exists, or bootstrap still leaves unresolved residue needing shared logic. [VERIFIED: `wxbot/bookkeeping-platform/scripts/bootstrap_quote_group_profiles.py`; `wxbot/bookkeeping-platform/tests/test_bootstrap_quote_group_profiles.py`] |
| 4 | `shared_rule` | The same deterministic mapping or reusable grammar fix is now proven across at least two distinct groups or corpus fixtures. [ASSUMED] | Alias/rule reuse is still insufficient and a parser-core bug spans groups. [ASSUMED] |
| 5 | `global_core` | The failure is a true parser-core or template-engine defect that group config and shared aliases cannot represent. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py`; `wxbot/bookkeeping-platform/bookkeeping_core/template_engine.py`] | Human/main-agent accepts code-level blast radius and cross-group regression gate. [VERIFIED: user request; `AGENTS.md`] |

**Concrete promotion criteria:**
- Never promote beyond the owning group after one local success. [VERIFIED: user request; `.planning/PROJECT.md`]
- Require repeated shape proof before `shared_rule`; the minimum should be two distinct owning groups or one owning group plus one approved corpus fixture that reproduces the same deterministic need. [ASSUMED]
- Prefer `quote_dictionary_aliases` before core code when the repeated failure is alias/canonicalization related, because the repo already supports global and scoped alias rows. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`; `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py`] 
- Treat `global_core` as a main-agent/human lane even if a subagent first surfaced the idea. [VERIFIED: user request]

### 5. Validation Gates After Each Attempt

Every attempt must pass all applicable gates; "comparison is better" is necessary but not sufficient for absorption. [VERIFIED: user request; `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`]

| Gate | Requirement | Pass rule |
|------|-------------|-----------|
| Proposal schema gate | Proposal payload must match the one allowed `proposal_scope` and artifact type. [VERIFIED: user request] | Reject immediately if the artifact targets a wider scope than the case allows. [VERIFIED: user request] |
| Candidate-only replay gate | Attempt replay must stay fact-neutral. [VERIFIED: user request; `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md`] | `replayed=true` and `mutated_active_facts=False`. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`; `wxbot/bookkeeping-platform/bookkeeping_web/app.py`] |
| Validator gate | Attempt must improve or safely preserve candidate/validator outcome. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/quote_validation.py`; `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`] | `message_decision` rank must not fall, `publishable_row_count` must not drop, `rejected_row_count` and `held_row_count` must not increase, and comparison classification must be `better`. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`; `wxbot/bookkeeping-platform/bookkeeping_core/quote_validation.py`] |
| Residue gate | Remaining unresolved lines should strictly decrease for a local grammar fix. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`] | `remaining_lines` count must go down unless the case was already zero-residue and only validator quality improved. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`] |
| Scope regression gate | Broader scopes need broader proof. [VERIFIED: user request; `.planning/ROADMAP.md`] | `group_profile/group_section`: owning-case replay + targeted runtime/web tests; `bootstrap`: add bootstrap fixture and runtime candidate-only proof; `shared_rule/global_core`: run cross-group corpus/template/runtime/web regressions. [VERIFIED: `wxbot/bookkeeping-platform/tests/test_runtime.py`; `wxbot/bookkeeping-platform/tests/test_webapp.py`; `wxbot/bookkeeping-platform/tests/test_bootstrap_quote_group_profiles.py`; `wxbot/bookkeeping-platform/tests/test_template_engine.py`] |
| Absorption gate | Only the system can commit the passed artifact into a deterministic target. [VERIFIED: user request; `.planning/PROJECT.md`] | Record `absorbed_target`, close the case, and keep the attempt row immutable. [ASSUMED] |

### 6. Escalation Policy After Repeated Failures

Phase 05 currently escalates after two non-better failures by switching the case state to `escalated` once `failure_log_json` reaches length 2. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`] Phase 06 should replace that implicit heuristic with the explicit user-requested budget: max three repair attempts per case before escalation. [VERIFIED: user request]

**Recommended policy:**

1. `attempt 1`: must stay in the initial `group_profile` scope unless the failure package proves that no profile exists and an approved bootstrap fixture is already available. [VERIFIED: user request; `wxbot/bookkeeping-platform/scripts/bootstrap_quote_group_profiles.py`]  
2. `attempt 2`: may advance one step in the promotion ladder if attempt 1 failed for scope-fit reasons and the failure log proves why. [VERIFIED: user request; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`]  
3. `attempt 3`: last bounded try; if it fails, mark `escalated` with `escalation_reason` such as `budget_exhausted`, `requires_shared_rule`, `requires_global_core`, or `proposal_out_of_scope`. [ASSUMED]  
4. Escalate immediately, without consuming the full budget, when the next legal step is `shared_rule` or `global_core`, because that is no longer a safe subagent-only lane. [VERIFIED: user request; `AGENTS.md`]  
5. The escalation packet should include raw message, baseline attempt, all prior proposal artifacts, failure-log stack, and the system's recommended next scope for the main agent/human. [VERIFIED: user request; `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md`]  

### 7. Recommended Plan Decomposition

Use three executable plans. [VERIFIED: user request; `.planning/ROADMAP.md`]

| Plan | Scope | Why it should be separate |
|------|-------|---------------------------|
| `06-01` | Extend repair-case persistence and executor substrate: attempt proposal metadata, `max_attempts=3`, current-scope rollups, and one system-owned remediation executor API/service. [VERIFIED: user request; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`; `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`] | This is the state and custody foundation; later plans should build on stable attempt records, not improvise them. [VERIFIED: `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md`] |
| `06-02` | Implement group-first policy and safe staged absorption targets: group-profile patching, section merge flow, bootstrap flow, and scope rejection rules. [VERIFIED: user request; `wxbot/bookkeeping-platform/bookkeeping_web/app.py`; `wxbot/bookkeeping-platform/scripts/bootstrap_quote_group_profiles.py`] | This is the core remediation behavior and the main blast-radius control. [VERIFIED: `AGENTS.md`; `.planning/PROJECT.md`] |
| `06-03` | Add validation, regression, and escalation gates: monotonic validator checks, cross-group promotion criteria, escalation packets, and full test coverage. [VERIFIED: user request; `wxbot/bookkeeping-platform/bookkeeping_core/quote_validation.py`; `wxbot/bookkeeping-platform/tests/test_postgres_backend.py`; `wxbot/bookkeeping-platform/tests/test_runtime.py`; `wxbot/bookkeeping-platform/tests/test_webapp.py`] | This closes the loop and proves that successful fixes are safe while repeated failures terminate cleanly. [VERIFIED: user request; `.planning/REQUIREMENTS.md`] |

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Attempt history | A second remediation log outside repair cases | Existing `quote_repair_case_attempts` plus additive proposal/gate metadata. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`; `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`] | Phase 05 already guarantees append-only lineage and rollups. [VERIFIED: `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md`] |
| Replay proof | A new remediation-specific replay path | `_replay_latest_quote_document_with_current_template(...)` reused through repair-case services. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_web/app.py`; `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`] | The existing helper is already candidate-only and verified not to mutate active facts. [VERIFIED: `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md`] |
| Group grammar writes | Freeform JSON surgery on `template_config` | Existing merge helpers and `upsert_quote_group_profile(...)`. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_web/app.py`; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`] | Existing helpers preserve section IDs, priorities, and parser-version expectations. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_web/app.py`] |
| Bootstrap generation | Prompt-crafted template JSON | `build_bootstrap_profile_payload(...)` from approved fixtures. [VERIFIED: `wxbot/bookkeeping-platform/scripts/bootstrap_quote_group_profiles.py`; `wxbot/bookkeeping-platform/tests/test_bootstrap_quote_group_profiles.py`] | The script already enforces approved fixtures and candidate-only seed semantics. [VERIFIED: `wxbot/bookkeeping-platform/scripts/bootstrap_quote_group_profiles.py`] |
| Reusable shared mappings | Hard-coded regex bundles in parser code | `quote_dictionary_aliases` scoped/global rows first, then code only if config cannot represent the fix. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`; `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py`] | This keeps repeated alias/canonicalization issues out of parser-core churn. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`] |

**Key insight:** Phase 06 should industrialize the custody loop, not invent a smarter parser. [VERIFIED: user request; `AGENTS.md`; `.planning/PROJECT.md`] The brownfield already has the deterministic artifacts needed for safe absorption; what it lacks is bounded proposal governance. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`; `wxbot/bookkeeping-platform/bookkeeping_web/app.py`; `.planning/ROADMAP.md`]

## Common Pitfalls

### Pitfall 1: Treating `comparison=better` as auto-absorb
**What goes wrong:** A proposal can look "better" on one coarse metric while still increasing rejected or held rows, or broadening parser blast radius. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`; `wxbot/bookkeeping-platform/bookkeeping_core/quote_validation.py`]  
**Why it happens:** Phase 05 comparison logic is designed for before/after evidence, not final Phase 06 absorption governance. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`]  
**How to avoid:** Add explicit monotonic validator and regression gates before absorption. [VERIFIED: user request; `wxbot/bookkeeping-platform/bookkeeping_core/quote_validation.py`]  
**Warning signs:** `publishable_row_count` rises but `rejected_row_count` or `held_row_count` also rises. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`; `wxbot/bookkeeping-platform/bookkeeping_core/quote_validation.py`]  

### Pitfall 2: Letting subagents touch live persistence
**What goes wrong:** A failed repair attempt can mutate the owning group profile or shared config before replay proof exists. [VERIFIED: user request; `AGENTS.md`]  
**Why it happens:** The current repo has admin/UI endpoints that write group profiles directly after operator flows, and those patterns are tempting to reuse naively. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_web/app.py`; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`]  
**How to avoid:** Keep subagents proposal-only and route all absorption through one system executor. [VERIFIED: user request; `.planning/PROJECT.md`]  
**Warning signs:** A remediation flow calls `upsert_quote_group_profile(...)` before storing a proposal attempt and running replay. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`]  

### Pitfall 3: Promoting shared/global too early
**What goes wrong:** One noisy case forces parser-core churn and creates cross-group regressions. [VERIFIED: user request; `.planning/PROJECT.md`]  
**Why it happens:** Shared/global fixes look cheaper than maintaining per-group grammar discipline. [VERIFIED: `AGENTS.md`; `.planning/PROJECT.md`]  
**How to avoid:** Enforce the promotion ladder in code and require repeated cross-group proof before `shared_rule` or `global_core`. [VERIFIED: user request]  
**Warning signs:** The same case jumps from `group_profile` failure straight to core code changes without trying section/bootstrap or proving repetition. [VERIFIED: user request]  

### Pitfall 4: Retrying without history
**What goes wrong:** Attempts loop on the same failed idea with different wording. [VERIFIED: user request; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`]  
**Why it happens:** The proposer sees only the raw message, not prior failed proposals and gate results. [VERIFIED: user request]  
**How to avoid:** Always include stacked failure logs and prior proposal artifacts in the next attempt package. [VERIFIED: user request; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`]  
**Warning signs:** Multiple attempts in `failure_log_json` share the same failure note or scope with no new evidence. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`]  

## Code Examples

Verified patterns already in the repo that Phase 06 should reuse:

### Append-Only Repair Attempts
```python
# Source: wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py
attempt = db.create_quote_repair_case_attempt(
    repair_case_id=repair_case_id,
    attempt_kind=REPAIR_ATTEMPT_KIND_REPAIR,
    attempt_number=next_attempt_number,
    trigger=str(trigger or "").strip() or "repair_attempt",
    quote_document_id=_existing_quote_document_id(db=db, value=replay_result.get("quote_document_id")),
    validation_run_id=_existing_validation_run_id(db=db, value=replay_result.get("validation_run_id")),
    replayed_from_quote_document_id=_maybe_int(repair_case.get("origin_quote_document_id")),
    group_profile_id=_maybe_int(repair_case.get("group_profile_id")),
    attempt_summary=attempt_summary,
    outcome_state=_baseline_attempt_outcome_state(replay_result=replay_result),
    failure_note=str(replay_result.get("reason") or ""),
)
```
[VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`]

### Group-Parser Section Merge
```python
# Source: wxbot/bookkeeping-platform/bookkeeping_web/app.py
merged_config = _merge_group_parser_template_config(
    str((group_profile or {}).get("template_config") or ""),
    derived_sections=derived_sections,
    max_sections=GROUP_PARSER_MAX_SECTIONS,
)
db.upsert_quote_group_profile(
    platform=platform,
    chat_id=chat_id,
    chat_name=chat_name,
    parser_template="group-parser",
    template_config=merged_config,
)
```
[VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_web/app.py`; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`]

### Approved Bootstrap Payload Generation
```python
# Source: wxbot/bookkeeping-platform/scripts/bootstrap_quote_group_profiles.py
payload = build_bootstrap_profile_payload(
    fixture_name="sk_steam_price_update",
    platform="wechat",
    chat_id="room-bootstrap-sk",
)
```
[VERIFIED: `wxbot/bookkeeping-platform/scripts/bootstrap_quote_group_profiles.py`; `wxbot/bookkeeping-platform/tests/test_bootstrap_quote_group_profiles.py`]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Exception rows carried manual resolution state only. [VERIFIED: `wxbot/bookkeeping-platform/sql/postgres_schema.sql`; `.planning/phases/05-exception-repair-state-machine/05-RESEARCH.md`] | Repair cases now own lifecycle, baseline replay, attempt history, and rollups. [VERIFIED: `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md`; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`] | Phase 05 on 2026-04-14. [VERIFIED: `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md`] | Phase 06 can add bounded automation without rebuilding failure packaging. [VERIFIED: `.planning/ROADMAP.md`] |
| Exception fixes can be saved through admin/operator flows that write group profiles directly after preview/replay. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_web/app.py`] | Recommended Phase 06 approach is to route subagent ideas through proposal artifacts plus a system-owned staged executor before any absorption. [ASSUMED] | Phase 06 recommendation. [ASSUMED] | Preserves custody while still enabling iterative repair. [ASSUMED] |

**Deprecated/outdated:**
- Prompt-only repair suggestions with no deterministic artifact or replay proof are not acceptable for this phase. [VERIFIED: user request; `AGENTS.md`; `.planning/PROJECT.md`]
- Implicit escalation after two failures is outdated for Phase 06 because the user explicitly asked for a max budget of three attempts. [VERIFIED: user request; `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Proposal artifacts should be stored directly on `quote_repair_case_attempts` as JSON rather than in a separate remediation table. [ASSUMED] | Architecture Patterns | Planner may choose a slightly different schema split. |
| A2 | Cross-group proof for `shared_rule` should require at least two distinct groups or one group plus one approved corpus fixture. [ASSUMED] | Promotion Order | Promotion may be too strict or too loose for actual operator workload. |
| A3 | Successful absorption metadata should be stored as `absorbed_target` / `absorbed_at` on attempt records. [ASSUMED] | State / Attempt Model | Implementation may instead place this in case summary JSON or a separate audit log. |

## Open Questions

1. **Should Phase 06 persist proposals in the DB only, or also write reviewable artifact files under `.planning/`?**
   - What we know: DB-backed attempts already exist and are the current authoritative repair history. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`; `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md`]
   - What's unclear: Whether the operator wants filesystem-visible proposal artifacts for easier manual review. [ASSUMED]
   - Recommendation: Start DB-only for custody and auditability; add mirrored artifact files later only if operator review pain appears in practice. [ASSUMED]

2. **Should `global_core` proposals ever be auto-applied by the system executor?**
   - What we know: The user requires system custody but also explicitly wants escalation to main-agent/human after repeated failure. [VERIFIED: user request]
   - What's unclear: Whether a future phase should let the executor auto-absorb low-risk core fixes after cross-group proof. [ASSUMED]
   - Recommendation: No; keep `global_core` as escalate-only in Phase 06. [ASSUMED]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Project venv Python | Phase 06 implementation and tests [VERIFIED: `AGENTS.md`; `wxbot/bookkeeping-platform/tests/`] | ✓ [VERIFIED: local env `wxbot/bookkeeping-platform/.venv/bin/python --version`] | 3.14.3 [VERIFIED: local env `wxbot/bookkeeping-platform/.venv/bin/python --version`] | — |
| PostgreSQL CLI (`psql`) | DB schema work and manual inspection [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`] | ✓ [VERIFIED: local env `psql --version`] | 16.13 [VERIFIED: local env `psql --version`] | — |
| PostgreSQL server on `127.0.0.1:5432` | Postgres-backed unit/integration tests [VERIFIED: `wxbot/bookkeeping-platform/tests/support/postgres_test_case.py`] | ✗ at research time [VERIFIED: local env `pg_isready -h 127.0.0.1 -p 5432`] | — | Start local test DB or provide `BOOKKEEPING_TEST_DSN` to another reachable server. [VERIFIED: `wxbot/bookkeeping-platform/tests/support/postgres_test_case.py`] |
| Node / npm | GSD planning helpers only, not quote runtime itself [VERIFIED: phase init via `gsd-tools`; `.planning/config.json`] | ✓ [VERIFIED: local env `node --version`; `npm --version`] | Node `v25.9.0`, npm `11.12.1` [VERIFIED: local env `node --version`; `npm --version`] | — |

**Missing dependencies with no fallback:**
- None for research itself. [VERIFIED: this session]

**Missing dependencies with fallback:**
- Local PostgreSQL server is not running on the default port; tests can still proceed once `BOOKKEEPING_TEST_DSN` points to a reachable PostgreSQL instance. [VERIFIED: local env `pg_isready -h 127.0.0.1 -p 5432`; `wxbot/bookkeeping-platform/tests/support/postgres_test_case.py`]

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `unittest` on PostgreSQL-backed `PostgresTestCase`. [VERIFIED: `AGENTS.md`; `wxbot/bookkeeping-platform/tests/support/postgres_test_case.py`] |
| Config file | none; tests are invoked directly with `python -m unittest`. [VERIFIED: `AGENTS.md`; `wxbot/bookkeeping-platform/tests/`] |
| Quick run command | `BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend.RepairCaseTests tests.test_runtime.RuntimeRepairCaseTests tests.test_webapp.WebRepairCaseTests -v` [VERIFIED: `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md`; `wxbot/bookkeeping-platform/tests/test_postgres_backend.py`; `wxbot/bookkeeping-platform/tests/test_runtime.py`; `wxbot/bookkeeping-platform/tests/test_webapp.py`] |
| Full suite command | `BOOKKEEPING_TEST_DSN=postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_quote_validation tests.test_postgres_backend tests.test_runtime tests.test_webapp tests.test_bootstrap_quote_group_profiles -v` [VERIFIED: `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md`; `wxbot/bookkeeping-platform/tests/test_quote_validation.py`; `wxbot/bookkeeping-platform/tests/test_bootstrap_quote_group_profiles.py`] |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INDU-01 | Bounded attempts, stacked failure logs, and max-3 escalation are enforced by the system executor. [VERIFIED: user request; `.planning/REQUIREMENTS.md`] | unit + integration | `BOOKKEEPING_TEST_DSN=... PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_postgres_backend tests.test_runtime -v` [VERIFIED: `wxbot/bookkeeping-platform/tests/test_postgres_backend.py`; `wxbot/bookkeeping-platform/tests/test_runtime.py`] | ✅ existing modules, but new Phase 06 cases are still needed. [VERIFIED: `wxbot/bookkeeping-platform/tests/test_postgres_backend.py`; `wxbot/bookkeeping-platform/tests/test_runtime.py`] |
| INDU-02 | Group-first promotion and safe absorption only allow deterministic fixes after replay/validator/regression proof. [VERIFIED: user request; `.planning/REQUIREMENTS.md`] | integration + regression | `BOOKKEEPING_TEST_DSN=... PYTHONPATH=. ./.venv/bin/python -m unittest tests.test_webapp tests.test_bootstrap_quote_group_profiles tests.test_template_engine -v` [VERIFIED: `wxbot/bookkeeping-platform/tests/test_webapp.py`; `wxbot/bookkeeping-platform/tests/test_bootstrap_quote_group_profiles.py`; `wxbot/bookkeeping-platform/tests/test_template_engine.py`] | ✅ existing modules, but new Phase 06 cases are still needed. [VERIFIED: `wxbot/bookkeeping-platform/tests/test_webapp.py`; `wxbot/bookkeeping-platform/tests/test_bootstrap_quote_group_profiles.py`; `wxbot/bookkeeping-platform/tests/test_template_engine.py`] |

### Sampling Rate
- **Per task commit:** run the quick repair-case suite plus any new focused Phase 06 tests. [VERIFIED: `.planning/config.json`; `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md`]
- **Per wave merge:** run the full suite command including bootstrap and validator tests. [VERIFIED: `.planning/config.json`; `wxbot/bookkeeping-platform/tests/`] 
- **Phase gate:** full suite green and at least one corpus-backed remediation case proves no active-fact mutation and correct escalation behavior. [VERIFIED: user request; `.planning/REQUIREMENTS.md`] 

### Wave 0 Gaps
- [ ] Add DB-level tests for `proposal_scope`, `proposal_kind`, `max_attempts=3`, and escalation reasons in [`wxbot/bookkeeping-platform/tests/test_postgres_backend.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_postgres_backend.py). [VERIFIED: `wxbot/bookkeeping-platform/tests/test_postgres_backend.py`; user request]
- [ ] Add runtime/executor tests that reject out-of-scope proposals and preserve candidate-only replay in [`wxbot/bookkeeping-platform/tests/test_runtime.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_runtime.py). [VERIFIED: `wxbot/bookkeeping-platform/tests/test_runtime.py`; user request]
- [ ] Add web/service regression tests for group-section and bootstrap absorption gates in [`wxbot/bookkeeping-platform/tests/test_webapp.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_webapp.py). [VERIFIED: `wxbot/bookkeeping-platform/tests/test_webapp.py`; user request]
- [ ] Add cross-group promotion regression cases, likely in [`wxbot/bookkeeping-platform/tests/test_template_engine.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_template_engine.py) and [`wxbot/bookkeeping-platform/tests/test_bootstrap_quote_group_profiles.py`](/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform/tests/test_bootstrap_quote_group_profiles.py). [VERIFIED: `wxbot/bookkeeping-platform/tests/test_template_engine.py`; `wxbot/bookkeeping-platform/tests/test_bootstrap_quote_group_profiles.py`; user request]
- [ ] Ensure a reachable PostgreSQL test DSN exists before implementation begins; the default local server was not reachable during research. [VERIFIED: local env `pg_isready -h 127.0.0.1 -p 5432`; `wxbot/bookkeeping-platform/tests/support/postgres_test_case.py`]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_web/app.py`; `wxbot/bookkeeping-platform/bookkeeping_core/commands.py`; `wxbot/bookkeeping-platform/bookkeeping_core/service.py`] | Quote-mutation endpoints require `QUOTE_ADMIN_PASSWORD`, and admin/master users are tracked in code and DB helpers. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_web/app.py`; `wxbot/bookkeeping-platform/bookkeeping_core/commands.py`; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`] |
| V3 Session Management | no major browser-session layer found in researched Phase 06 surfaces. [VERIFIED: search `session|cookie|csrf` over `bookkeeping_web/app.py` and `bookkeeping_core/*`] | Keep remediation endpoints stateless and request-scoped; do not introduce long-lived session authority for subagents. [VERIFIED: user request; `AGENTS.md`] |
| V4 Access Control | yes [VERIFIED: user request; `AGENTS.md`; `wxbot/bookkeeping-platform/bookkeeping_web/app.py`] | System executor is the only absorption authority; subagents remain proposal-only. [VERIFIED: user request; `.planning/PROJECT.md`] |
| V5 Input Validation | yes [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/quote_validation.py`; `wxbot/bookkeeping-platform/bookkeeping_web/app.py`] | Validate proposal schema, replay outputs, and candidate documents before any absorption. [VERIFIED: user request; `wxbot/bookkeeping-platform/bookkeeping_core/quote_validation.py`] |
| V6 Cryptography | limited/no for this phase. [VERIFIED: search `hashlib|hmac|encrypt|decrypt|crypto|bcrypt|argon|pbkdf` over researched surfaces] | No hand-rolled secrecy or signature scheme is needed for Phase 06; current hashing usage is for fingerprints, not publish custody. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`; `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py`; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`] |

### Known Threat Patterns for This Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Subagent proposes a wider-scope fix than the case allows | Elevation of Privilege | Enforce `proposal_scope` and `current_scope` checks before staging or replay. [VERIFIED: user request] |
| Proposal attempts to mutate active quote facts | Tampering | Keep replay candidate-only and deny any write path to `quote_price_rows` from remediation. [VERIFIED: user request; `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md`] |
| Repeated retries loop forever | Denial of Service / Reliability | Persist `max_attempts=3`, stack failure logs, and escalate deterministically. [VERIFIED: user request] |
| Shared/global promotion from a single noisy case | Tampering | Require repeated cross-group proof and human/main-agent escalation for `global_core`. [VERIFIED: user request; `AGENTS.md`] |
| Prompt injection / freeform output sneaks in non-deterministic rules | Tampering | Accept only normalized deterministic proposal artifacts, never freeform rule text as authoritative state. [VERIFIED: user request; `.planning/PROJECT.md`; `AGENTS.md`] |

## Sources

### Primary (HIGH confidence)
- `.planning/PROJECT.md` - hard system-custody, one-group-one-profile, and no-bypass constraints. [VERIFIED: `.planning/PROJECT.md`]
- `.planning/REQUIREMENTS.md` - `INDU-01`, `INDU-02`, and out-of-scope boundaries. [VERIFIED: `.planning/REQUIREMENTS.md`]
- `.planning/ROADMAP.md` - Phase 06 goal, success criteria, and roadmap ordering. [VERIFIED: `.planning/ROADMAP.md`]
- `.planning/STATE.md` - current execution position and confirmed Phase 05 completion state. [VERIFIED: `.planning/STATE.md`]
- `.planning/phases/05-exception-repair-state-machine/05-RESEARCH.md` - intended Phase 05 model and deferrals into Phase 06. [VERIFIED: `.planning/phases/05-exception-repair-state-machine/05-RESEARCH.md`]
- `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md` - verified Phase 05 behavior, tests, and boundaries. [VERIFIED: `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md`]
- `AGENTS.md` - project-specific hard rules for quote-wall work. [VERIFIED: `AGENTS.md`]
- `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py` - current repair-case lifecycle, attempt recording, comparison logic, and escalation heuristic. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`]
- `wxbot/bookkeeping-platform/bookkeeping_core/database.py` - repair-case, attempt, group-profile, and alias persistence surfaces. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_core/database.py`]
- `wxbot/bookkeeping-platform/bookkeeping_web/app.py` - current replay helper, group-profile merge helpers, and admin save flows. [VERIFIED: `wxbot/bookkeeping-platform/bookkeeping_web/app.py`]
- `wxbot/bookkeeping-platform/scripts/bootstrap_quote_group_profiles.py` - deterministic bootstrap payload generation from approved fixtures. [VERIFIED: `wxbot/bookkeeping-platform/scripts/bootstrap_quote_group_profiles.py`]

### Secondary (MEDIUM confidence)
- Local environment probes for Python, Node, npm, `psql`, and `pg_isready`. [VERIFIED: local env commands run in this session]

### Tertiary (LOW confidence)
- None. [VERIFIED: this research used repo docs/code and local environment only]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all stack claims are repo-local or locally probed. [VERIFIED: local env commands; `AGENTS.md`; `wxbot/bookkeeping-platform/bookkeeping_core/database.py`]
- Architecture: MEDIUM - Phase 05 substrate is verified, but Phase 06 executor/promotion design includes bounded recommendations not yet implemented. [VERIFIED: `.planning/phases/05-exception-repair-state-machine/05-VERIFICATION.md`; `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`; Assumptions Log]
- Pitfalls: HIGH - each pitfall is directly grounded in current code paths and the user's explicit business constraints. [VERIFIED: user request; `AGENTS.md`; `wxbot/bookkeeping-platform/bookkeeping_core/repair_cases.py`; `wxbot/bookkeeping-platform/bookkeeping_web/app.py`]

**Research date:** 2026-04-14 [VERIFIED: session date]  
**Valid until:** 2026-05-14 for repo-internal design assumptions, or sooner if Phase 05 substrate changes materially. [ASSUMED]
