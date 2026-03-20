from __future__ import annotations

import json
from pathlib import Path

from bookkeeping_core.database import BookkeepingDB
from bookkeeping_core.reporting import ReportingService
from bookkeeping_core.sync_events import ingest_sync_events


HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>总账中心</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f5f1e8;
      --panel: #fffdf9;
      --ink: #1d2a35;
      --line: #d8cfc2;
      --accent: #0d6b5d;
      --warn: #9b2c2c;
    }
    body { margin: 0; font-family: "PingFang SC", "Microsoft YaHei", sans-serif; background: linear-gradient(135deg, #f5f1e8, #eef4f2); color: var(--ink); }
    header { padding: 24px 28px 8px; }
    h1 { margin: 0; font-size: 28px; }
    p { margin: 8px 0 0; color: #576574; }
    main { display: grid; gap: 18px; padding: 18px 28px 32px; }
    .panel { background: var(--panel); border: 1px solid var(--line); border-radius: 18px; padding: 18px; box-shadow: 0 8px 30px rgba(29, 42, 53, 0.08); }
    .panel h2 { margin: 0 0 12px; font-size: 18px; }
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th, td { text-align: left; padding: 10px 8px; border-bottom: 1px solid #eee4d7; }
    th { color: #5b6873; font-weight: 600; }
    form { display: grid; gap: 10px; grid-template-columns: repeat(4, minmax(0, 1fr)); }
    form input, form textarea { width: 100%; box-sizing: border-box; border: 1px solid var(--line); border-radius: 10px; padding: 10px 12px; font: inherit; background: #fff; }
    form textarea { grid-column: 1 / -1; min-height: 88px; resize: vertical; }
    form button { grid-column: 1 / span 1; border: 0; border-radius: 999px; background: var(--accent); color: white; padding: 10px 14px; font: inherit; cursor: pointer; }
    .muted { color: #6c7a86; font-size: 13px; }
    .error { color: var(--warn); }
    @media (max-width: 900px) {
      form { grid-template-columns: 1fr; }
      form button { grid-column: auto; }
    }
  </style>
</head>
<body>
  <header>
    <h1>总账中心</h1>
    <p>先替代人工账表：看当前余额、看账期结果、做人工修正。</p>
  </header>
  <main>
    <section class="panel">
      <h2>当前群余额</h2>
      <table id="groups-table">
        <thead>
          <tr><th>平台</th><th>群名</th><th>分组</th><th>当前余额</th></tr>
        </thead>
        <tbody></tbody>
      </table>
    </section>
    <section class="panel">
      <h2>最近账期</h2>
      <table id="periods-table">
        <thead>
          <tr><th>账期</th><th>群名</th><th>分组</th><th>期初</th><th>收款</th><th>使用</th><th>期末</th></tr>
        </thead>
        <tbody></tbody>
      </table>
    </section>
    <section class="panel">
      <h2>组合分组汇总</h2>
      <table id="combos-table">
        <thead>
          <tr><th>名称</th><th>包含分组</th><th>群数量</th><th>当前余额</th></tr>
        </thead>
        <tbody></tbody>
      </table>
      <form id="combo-form" style="margin-top: 14px;">
        <input name="name" placeholder="组合名称，如 客户总览" required />
        <input name="group_numbers" placeholder="分组号，逗号分隔，如 5,7,8" required />
        <input name="created_by" placeholder="创建人" required />
        <input name="note" placeholder="备注" />
        <button type="submit">保存组合</button>
      </form>
    </section>
    <section class="panel">
      <h2>人工修正</h2>
      <p class="muted">输入账期 ID、群标识和修正值。修正后会自动刷新最近账期。</p>
      <form id="adjustment-form">
        <input name="settlement_id" placeholder="账期 ID" required />
        <input name="group_key" placeholder="群标识，如 wechat:g-100" required />
        <input name="income_delta" placeholder="收款修正，默认 0" value="0" />
        <input name="expense_delta" placeholder="使用修正，默认 0" value="0" />
        <input name="opening_delta" placeholder="期初修正，默认 0" value="0" />
        <input name="closing_delta" placeholder="期末修正，默认 0" value="0" />
        <input name="created_by" placeholder="修正人" required />
        <textarea name="note" placeholder="修正说明" required></textarea>
        <button type="submit">提交修正</button>
      </form>
      <div id="form-status" class="muted"></div>
    </section>
  </main>
  <script>
    async function loadDashboard() {
      const resp = await fetch('/api/dashboard');
      const data = await resp.json();

      const groupsBody = document.querySelector('#groups-table tbody');
      groupsBody.innerHTML = data.current_groups.map((row) => `
        <tr>
          <td>${row.platform}</td>
          <td>${row.chat_name}</td>
          <td>${row.group_num ?? ''}</td>
          <td>${Number(row.current_balance).toFixed(2)}</td>
        </tr>
      `).join('');

      const periodsBody = document.querySelector('#periods-table tbody');
      periodsBody.innerHTML = data.recent_periods.map((row) => `
        <tr>
          <td>${row.settlement_id}</td>
          <td>${row.chat_name}</td>
          <td>${row.group_num ?? ''}</td>
          <td>${Number(row.opening_balance).toFixed(2)}</td>
          <td>${Number(row.income).toFixed(2)}</td>
          <td>${Number(row.expense).toFixed(2)}</td>
          <td>${Number(row.closing_balance).toFixed(2)}</td>
        </tr>
      `).join('');

      const combosBody = document.querySelector('#combos-table tbody');
      combosBody.innerHTML = data.combinations.map((row) => `
        <tr>
          <td>${row.label}</td>
          <td>${row.group_numbers.join('+')}</td>
          <td>${row.group_count}</td>
          <td>${Number(row.current_balance).toFixed(2)}</td>
        </tr>
      `).join('');
    }

    document.querySelector('#adjustment-form').addEventListener('submit', async (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      const data = Object.fromEntries(new FormData(form).entries());
      for (const key of ['settlement_id', 'opening_delta', 'income_delta', 'expense_delta', 'closing_delta']) {
        data[key] = Number(data[key] || 0);
      }
      const resp = await fetch('/api/adjustments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      const result = await resp.json();
      const status = document.querySelector('#form-status');
      if (!resp.ok) {
        status.textContent = result.error || '提交失败';
        status.className = 'error';
        return;
      }
      status.textContent = `修正已保存，ID=${result.adjustment_id}`;
      status.className = 'muted';
      form.reset();
      loadDashboard();
    });

    document.querySelector('#combo-form').addEventListener('submit', async (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      const data = Object.fromEntries(new FormData(form).entries());
      data.group_numbers = String(data.group_numbers || '');
      const resp = await fetch('/api/group-combinations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      const result = await resp.json();
      const status = document.querySelector('#form-status');
      if (!resp.ok) {
        status.textContent = result.error || '保存组合失败';
        status.className = 'error';
        return;
      }
      status.textContent = `组合已保存，ID=${result.combination_id}`;
      status.className = 'muted';
      form.reset();
      loadDashboard();
    });

    loadDashboard();
  </script>
</body>
</html>
"""


def create_app(db_target: str | Path, sync_token: str | None = None):
    db_file = db_target

    def app(environ, start_response):
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "/")
        if path == "/":
            return _respond_html(start_response, HTML)
        if path == "/api/dashboard" and method == "GET":
            return _with_db(db_file, start_response, _handle_dashboard)
        if path == "/api/adjustments" and method == "POST":
            return _with_db(db_file, start_response, _handle_adjustments, environ)
        if path == "/api/group-combinations":
            return _with_db(db_file, start_response, _handle_group_combinations, environ)
        if path == "/api/sync/events" and method == "POST":
            if not _is_authorized(environ, sync_token):
                return _respond_json(start_response, 401, {"error": "Unauthorized"})
            return _with_db(db_file, start_response, _handle_sync_events, environ)
        return _respond_json(start_response, 404, {"error": f"Unknown path: {path}"})

    return app


def _with_db(db_target: str | Path, start_response, handler, environ=None):
    db = BookkeepingDB(db_target)
    try:
        return handler(db, start_response, environ)
    finally:
        db.close()


def _handle_dashboard(db: BookkeepingDB, start_response, environ=None):
    payload = ReportingService(db).build_dashboard_payload()
    return _respond_json(start_response, 200, payload)


def _handle_adjustments(db: BookkeepingDB, start_response, environ):
    try:
        payload = _read_json_body(environ)
        adjustment_id = db.add_manual_adjustment(
            settlement_id=int(payload["settlement_id"]),
            group_key=str(payload["group_key"]),
            opening_delta=float(payload.get("opening_delta", 0)),
            income_delta=float(payload.get("income_delta", 0)),
            expense_delta=float(payload.get("expense_delta", 0)),
            closing_delta=float(payload.get("closing_delta", 0)),
            note=str(payload["note"]),
            created_by=str(payload["created_by"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        return _respond_json(start_response, 400, {"error": f"Bad payload: {exc}"})
    return _respond_json(start_response, 200, {"adjustment_id": adjustment_id})


def _handle_group_combinations(db: BookkeepingDB, start_response, environ):
    method = environ.get("REQUEST_METHOD", "GET").upper()
    if method == "GET":
        payload = ReportingService(db).list_combination_summaries()
        return _respond_json(start_response, 200, payload)

    try:
        payload = _read_json_body(environ)
        raw_numbers = payload.get("group_numbers", [])
        if isinstance(raw_numbers, str):
            numbers = [int(item) for item in raw_numbers.split(",") if item.strip()]
        else:
            numbers = [int(item) for item in raw_numbers]
        combination_id = db.save_group_combination(
            name=str(payload["name"]),
            group_numbers=numbers,
            note=str(payload.get("note", "")),
            created_by=str(payload.get("created_by", "web")),
        )
    except (KeyError, TypeError, ValueError) as exc:
        return _respond_json(start_response, 400, {"error": f"Bad payload: {exc}"})
    return _respond_json(start_response, 200, {"combination_id": combination_id})


def _handle_sync_events(db: BookkeepingDB, start_response, environ):
    try:
        payload = _read_json_body(environ)
        events = payload.get("events", [])
        if not isinstance(events, list):
            raise ValueError("events must be a list")
        result = ingest_sync_events(db, events)
    except (KeyError, TypeError, ValueError) as exc:
        return _respond_json(start_response, 400, {"error": f"Bad payload: {exc}"})
    return _respond_json(start_response, 200, result)


def _read_json_body(environ) -> dict:
    length = int(environ.get("CONTENT_LENGTH") or "0")
    raw = environ["wsgi.input"].read(length) if length > 0 else b"{}"
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def _respond_json(start_response, status_code: int, payload: dict | list):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    start_response(
        f"{status_code} {'OK' if status_code < 400 else 'ERROR'}",
        [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]


def _respond_html(start_response, html: str):
    body = html.encode("utf-8")
    start_response(
        "200 OK",
        [
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]


def _is_authorized(environ, sync_token: str | None) -> bool:
    if not sync_token:
        return False
    header = str(environ.get("HTTP_AUTHORIZATION") or "").strip()
    return header == f"Bearer {sync_token}"
