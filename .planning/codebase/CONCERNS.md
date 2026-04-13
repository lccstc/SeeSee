# Concerns

## Highest-Risk Areas

### 1. Quote Wall Accuracy Path

The repo context makes this explicit: quote parsing is a high-risk subsystem because wrong prices reaching the wall are unacceptable.

Code hotspots:

- `wxbot/bookkeeping-platform/bookkeeping_core/template_engine.py`
- `wxbot/bookkeeping-platform/bookkeeping_core/quotes.py`
- `wxbot/bookkeeping-platform/bookkeeping_web/app.py`
- `wxbot/bookkeeping-platform/bookkeeping_web/pages.py`
- `wxbot/bookkeeping-platform/tests/test_template_engine.py`
- `wxbot/bookkeeping-platform/tests/test_webapp.py`

Risk pattern:

- a small parsing or replay change can create silent price corruption
- exception handling and template save/replay are operationally critical

### 2. Large Monolithic Web Files

Two files are major maintenance pressure points:

- `wxbot/bookkeeping-platform/bookkeeping_web/app.py`
- `wxbot/bookkeeping-platform/bookkeeping_web/pages.py`

Why this matters:

- route sprawl makes behavior discovery harder
- auth, parsing, reporting, quote management, reconciliation, and settlement all meet in one routing file
- inline frontend code increases accidental coupling between API payload shape and UI behavior

### 3. `BookkeepingDB` as a God Object

Graphify flags `BookkeepingDB` and `_BookkeepingStoreBase` as highly connected nodes.

Implication:

- persistence changes have unusually wide blast radius
- quote parsing, reporting, reconciliation, runtime ingestion, and tests all couple to the same store surface

### 4. Multi-Runtime Operational Drift

The system depends on coordination across:

- PostgreSQL
- Python core server
- WhatsApp adapter
- WeChat adapter

Operational runbooks already warn that startup order matters. This usually means:

- stale adapter code can break outbound delivery
- token mismatch can create silent auth failures
- one process can appear healthy while the end-to-end path is broken

## Security / Safety Concerns

- Core endpoints rely on shared bearer-token auth in `bookkeeping_web/app.py`
- Admin dictionary writes rely on `QUOTE_ADMIN_PASSWORD`
- Config files such as `config.wechat.json` and `config.json` are operationally sensitive and should be treated as secrets-adjacent
- The repo contains real-environment flavored documentation and DSN examples, so generated docs must avoid copying actual credentials

## Technical Debt Signals

- Manual WSGI routing instead of a framework router increases change friction
- HTML/CSS/JS embedded in Python strings increases review complexity
- The repository still contains SQLite-era artifacts even though runtime policy is PostgreSQL-only
- The WhatsApp adapter reconnect and polling logic is operationally important but still relatively thin and custom

## Testing Risks

- Strong regression coverage exists, but it is concentrated around known workflows
- Browser-level behavior is not validated through a real browser suite in this repo
- End-to-end adapter/core/database verification still depends on manual or operational testing

## Practical Precautions

- Treat changes under `template_engine.py`, quote exception handlers, and template save/replay flows as high risk
- Add or update tests before changing `bookkeeping_web/app.py` route behavior
- Avoid moving business logic into adapters
- Validate auth and outbound action flows whenever touching `POST /api/core/messages`, `/api/core/actions`, or adapter send paths
