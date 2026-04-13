# Stack Research

## Research Question

供应商群报价墙如果目标是“宁可漏，不可错”，标准技术栈不应该是“模型主导解析”，而应该是“证据驱动的确定性发布管道”。

## Recommended Stack

### 1. Message Ingestion

- Keep using the existing adapter architecture:
  - `wechat_adapter`
  - `whatsapp-bookkeeping`
- Keep raw message persistence in PostgreSQL through the current Python core
- Treat the raw incoming message as immutable source evidence

**Why**

The current repo already has working ingress, raw message storage, and core routing. Replacing this would waste time and introduce risk without improving quote correctness.

### 2. Candidate Generation Layer

- Keep deterministic template engines as the primary candidate source:
  - `group-parser-v1`
  - `strict-section-v1`
- Add an explicit candidate object model instead of letting parsers write active facts directly
- Allow optional local heuristic or model-assisted helpers only behind the candidate interface

**Why**

The parser should produce possibilities, not facts. This is the cleanest way to keep the system in charge.

### 3. Validation Layer

- Implement explicit validators in Python core code, not in prompt text:
  - schema validator
  - field normalizer
  - business rule validator
  - snapshot/delta guard
  - publishability evaluator

**Why**

This is the actual safety boundary. If this layer is weak, every other part of the system is cosmetic.

### 4. Fact Protection Layer

- Keep active quote facts in PostgreSQL
- Add a publishing service that is the only write path into active quote state
- Require the publisher to receive:
  - source message identity
  - classification (`full_snapshot` or `delta_update`)
  - validated candidate rows
  - `publishable_rows`

**Why**

The publisher is where “do not clear old active on failure” and “default to delta” become enforceable.

### 5. Exception / Replay Layer

- Keep exception pool in PostgreSQL and current web UI
- Extend around existing structures rather than replacing them
- Replay should be first-class:
  - replay raw message
  - replay with current template/rules
  - replay after manual fix
  - persist outcomes for regression tests

**Why**

The repo already has exception handling and template maintenance. The missing piece is turning this into a disciplined improvement loop.

## Recommended Non-Goals

- Do not put LLM prompts on the critical publish path
- Do not use confidence scores alone as publish permission
- Do not refactor the whole app into a new framework
- Do not mix quote-wall release rules into finance or settlement services

## Fit With Existing Repo

Best-fit implementation language and placement:

- Python core services in `wxbot/bookkeeping-platform/bookkeeping_core/`
- Route wiring in `wxbot/bookkeeping-platform/bookkeeping_web/app.py`
- UI-only affordances in `wxbot/bookkeeping-platform/bookkeeping_web/pages.py`
- Replay and regression tests in `wxbot/bookkeeping-platform/tests/`

## Confidence

- High: current repo structure is already suitable for this direction
- High: deterministic candidate + validator + publisher is a better fit than model-first parsing
- Medium: minimal PostgreSQL schema additions may be useful for publish auditability and replay states
