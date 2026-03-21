from __future__ import annotations


_STYLE = """
<style>
  :root {
    color-scheme: light;
    --bg: #f4f0e6;
    --panel: rgba(255, 252, 247, 0.92);
    --ink: #21313b;
    --muted: #63717c;
    --line: #d9cebd;
    --accent: #0f6d60;
    --accent-soft: #d8ebe4;
    --warn: #9b2c2c;
    --shadow: 0 18px 40px rgba(33, 49, 59, 0.08);
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
    color: var(--ink);
    background:
      radial-gradient(circle at top left, rgba(15, 109, 96, 0.18), transparent 28%),
      radial-gradient(circle at top right, rgba(209, 157, 94, 0.18), transparent 22%),
      linear-gradient(135deg, #f5efe4, #edf3f0 55%, #f6f0e8);
  }
  a { color: inherit; }
  header {
    padding: 28px 28px 12px;
  }
  .hero {
    display: flex;
    justify-content: space-between;
    gap: 18px;
    align-items: end;
    flex-wrap: wrap;
  }
  .hero h1 {
    margin: 0;
    font-size: 30px;
  }
  .hero p {
    margin: 10px 0 0;
    color: var(--muted);
    max-width: 720px;
    line-height: 1.6;
  }
  nav {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 18px;
  }
  nav a {
    text-decoration: none;
    padding: 10px 14px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.55);
    border: 1px solid rgba(15, 109, 96, 0.12);
  }
  nav a.active {
    background: var(--accent);
    color: white;
    border-color: var(--accent);
  }
  main {
    display: grid;
    gap: 18px;
    padding: 12px 28px 36px;
  }
  .panel {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 20px;
    padding: 18px;
    box-shadow: var(--shadow);
    backdrop-filter: blur(6px);
  }
  .panel h2, .panel h3 {
    margin: 0 0 12px;
  }
  .muted {
    color: var(--muted);
    font-size: 13px;
  }
  .error {
    color: var(--warn);
  }
  .cards {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 14px;
  }
  .card {
    padding: 16px;
    border-radius: 18px;
    background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(244, 250, 248, 0.95));
    border: 1px solid rgba(15, 109, 96, 0.12);
  }
  .card .label {
    font-size: 13px;
    color: var(--muted);
    margin-bottom: 8px;
  }
  .card .value {
    font-size: 28px;
    font-weight: 600;
  }
  .stack {
    display: grid;
    gap: 18px;
  }
  .toolbar {
    display: flex;
    gap: 12px;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
  }
  form {
    display: grid;
    gap: 12px;
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
  input, textarea, select, button {
    width: 100%;
    font: inherit;
  }
  input, textarea, select {
    padding: 10px 12px;
    border-radius: 12px;
    border: 1px solid var(--line);
    background: rgba(255,255,255,0.92);
  }
  textarea {
    min-height: 88px;
    resize: vertical;
  }
  button {
    border: 0;
    border-radius: 999px;
    padding: 10px 14px;
    background: var(--accent);
    color: white;
    cursor: pointer;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }
  th, td {
    text-align: left;
    padding: 10px 8px;
    border-bottom: 1px solid #ebe1d3;
    vertical-align: top;
  }
  th {
    color: var(--muted);
    font-weight: 600;
  }
  .full {
    grid-column: 1 / -1;
  }
  @media (max-width: 980px) {
    .cards {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    form {
      grid-template-columns: 1fr;
    }
    .full {
      grid-column: auto;
    }
  }
  @media (max-width: 640px) {
    header, main {
      padding-left: 16px;
      padding-right: 16px;
    }
    .cards {
      grid-template-columns: 1fr;
    }
  }
</style>
"""


def render_dashboard_page() -> str:
    body = """
<section class="panel stack">
  <div class="toolbar">
    <div>
      <h2>首页驾驶舱</h2>
      <div class="muted" id="dashboard-range">口径加载中</div>
    </div>
    <div class="muted">当前余额按实时交易余额；日利润与美元面额按当日已关闭账期。</div>
  </div>
  <div class="cards">
    <article class="card">
      <div class="label">当前总余额</div>
      <div class="value" id="summary-total-balance">0.00</div>
    </article>
    <article class="card">
      <div class="label">今日已实现利润</div>
      <div class="value" id="summary-profit">0.00</div>
    </article>
    <article class="card">
      <div class="label">今日美元面额</div>
      <div class="value" id="summary-usd">0.00</div>
    </article>
    <article class="card">
      <div class="label">未分配群数</div>
      <div class="value" id="summary-unassigned">0</div>
    </article>
  </div>
</section>
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
  <h2>最近账期快照</h2>
  <table id="periods-table">
    <thead>
      <tr><th>账期</th><th>关闭时间</th><th>群名</th><th>分组</th><th>期初</th><th>收款</th><th>使用</th><th>期末</th></tr>
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
  <p class="muted">输入账期 ID、群标识和修正值。保存后首页会按最新账期快照刷新。</p>
  <form id="adjustment-form">
    <input name="settlement_id" placeholder="账期 ID" required />
    <input name="group_key" placeholder="群标识，如 wechat:g-100" required />
    <input name="income_delta" placeholder="收款修正，默认 0" value="0" />
    <input name="expense_delta" placeholder="使用修正，默认 0" value="0" />
    <input name="opening_delta" placeholder="期初修正，默认 0" value="0" />
    <input name="closing_delta" placeholder="期末修正，默认 0" value="0" />
    <input name="created_by" placeholder="修正人" required />
    <textarea class="full" name="note" placeholder="修正说明" required></textarea>
    <button>提交修正</button>
  </form>
  <div id="form-status" class="muted"></div>
</section>
"""
    script = """
function money(value) {
  return Number(value || 0).toFixed(2);
}

async function loadDashboard() {
  const response = await fetch('/api/dashboard');
  const data = await response.json();
  const summary = data.summary || {};

  document.querySelector('#dashboard-range').textContent = summary.range_label || '按今日已关闭账期';
  document.querySelector('#summary-total-balance').textContent = money(summary.current_total_balance);
  document.querySelector('#summary-profit').textContent = money(summary.today_realized_profit);
  document.querySelector('#summary-usd').textContent = money(summary.today_total_usd_amount);
  document.querySelector('#summary-unassigned').textContent = String(summary.unassigned_group_count || 0);

  document.querySelector('#groups-table tbody').innerHTML = (data.current_groups || []).map((row) => `
    <tr>
      <td>${row.platform}</td>
      <td>${row.chat_name}</td>
      <td>${row.group_num ?? ''}</td>
      <td>${money(row.current_balance)}</td>
    </tr>
  `).join('');

  document.querySelector('#periods-table tbody').innerHTML = (data.recent_periods || []).map((row) => `
    <tr>
      <td>${row.period_id || row.settlement_id}</td>
      <td>${row.closed_at || row.settled_at || ''}</td>
      <td>${row.chat_name}</td>
      <td>${row.group_num ?? ''}</td>
      <td>${money(row.opening_balance)}</td>
      <td>${money(row.income)}</td>
      <td>${money(row.expense)}</td>
      <td>${money(row.closing_balance)}</td>
    </tr>
  `).join('');

  document.querySelector('#combos-table tbody').innerHTML = (data.combinations || []).map((row) => `
    <tr>
      <td>${row.label}</td>
      <td>${(row.group_numbers || []).join('+')}</td>
      <td>${row.group_count}</td>
      <td>${money(row.current_balance)}</td>
    </tr>
  `).join('');
}

document.querySelector('#adjustment-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = Object.fromEntries(new FormData(form).entries());
  for (const key of ['settlement_id', 'opening_delta', 'income_delta', 'expense_delta', 'closing_delta']) {
    payload[key] = Number(payload[key] || 0);
  }
  const response = await fetch('/api/adjustments', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const result = await response.json();
  const status = document.querySelector('#form-status');
  if (!response.ok) {
    status.className = 'error';
    status.textContent = result.error || '提交失败';
    return;
  }
  status.className = 'muted';
  status.textContent = `修正已保存，ID=${result.adjustment_id}`;
  form.reset();
  loadDashboard();
});

document.querySelector('#combo-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = Object.fromEntries(new FormData(form).entries());
  const response = await fetch('/api/group-combinations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const result = await response.json();
  const status = document.querySelector('#form-status');
  if (!response.ok) {
    status.className = 'error';
    status.textContent = result.error || '保存组合失败';
    return;
  }
  status.className = 'muted';
  status.textContent = `组合已保存，ID=${result.combination_id}`;
  form.reset();
  loadDashboard();
});

loadDashboard();
"""
    return _render_layout(
        title="总账中心",
        subtitle="驾驶舱先给信号，再决定进入哪个账期工作台或历史分析页。",
        active_path="/",
        body=body,
        script=script,
    )


def render_workbench_page() -> str:
    body = """
<section class="panel stack">
  <div class="toolbar">
    <div>
      <h2>账期工作台</h2>
      <div class="muted" id="workbench-range">请选择一个账期</div>
    </div>
    <label>
      <span class="muted">账期</span>
      <select id="period-select"></select>
    </label>
  </div>
  <div class="cards">
    <article class="card">
      <div class="label">账期利润</div>
      <div class="value" id="workbench-profit">0.00</div>
    </article>
    <article class="card">
      <div class="label">账期美元面额</div>
      <div class="value" id="workbench-usd">0.00</div>
    </article>
    <article class="card">
      <div class="label">群数量</div>
      <div class="value" id="workbench-groups">0</div>
    </article>
    <article class="card">
      <div class="label">交易笔数</div>
      <div class="value" id="workbench-transactions">0</div>
    </article>
  </div>
</section>
<section class="panel">
  <h2>群快照</h2>
  <table id="workbench-groups-table">
    <thead>
      <tr><th>群名</th><th>角色</th><th>期初</th><th>收款</th><th>使用</th><th>期末</th><th>交易笔数</th></tr>
    </thead>
    <tbody></tbody>
  </table>
</section>
<section class="panel">
  <h2>卡种统计</h2>
  <table id="workbench-cards-table">
    <thead>
      <tr><th>卡种</th><th>角色</th><th>美元面额</th><th>人民币金额</th><th>单面额</th><th>张数</th></tr>
    </thead>
    <tbody></tbody>
  </table>
</section>
"""
    script = """
function money(value) {
  return Number(value || 0).toFixed(2);
}

function updatePeriodOptions(periods, selectedId) {
  const select = document.querySelector('#period-select');
  select.innerHTML = periods.map((period) => `
    <option value="${period.id}">${period.id} · ${period.closed_at}</option>
  `).join('');
  if (selectedId) {
    select.value = String(selectedId);
  }
}

async function loadWorkbench(periodId) {
  const params = new URLSearchParams();
  if (periodId) {
    params.set('period_id', String(periodId));
  }
  const response = await fetch(`/api/workbench?${params.toString()}`);
  const data = await response.json();
  const selected = data.selected_period;
  const summary = data.summary || {};

  updatePeriodOptions(data.periods || [], selected ? selected.id : '');
  if (selected) {
    document.querySelector('#workbench-range').textContent =
      `${selected.start_at} 至 ${selected.end_at}，关闭于 ${selected.closed_at}`;
    history.replaceState({}, '', `/workbench?period_id=${selected.id}`);
  } else {
    document.querySelector('#workbench-range').textContent = '暂无已关闭账期';
  }

  document.querySelector('#workbench-profit').textContent = money(summary.profit);
  document.querySelector('#workbench-usd').textContent = money(summary.total_usd_amount);
  document.querySelector('#workbench-groups').textContent = String(summary.group_count || 0);
  document.querySelector('#workbench-transactions').textContent = String(summary.transaction_count || 0);

  document.querySelector('#workbench-groups-table tbody').innerHTML = (data.group_rows || []).map((row) => `
    <tr>
      <td>${row.chat_name}</td>
      <td>${row.business_role || ''}</td>
      <td>${money(row.opening_balance)}</td>
      <td>${money(row.income)}</td>
      <td>${money(row.expense)}</td>
      <td>${money(row.closing_balance)}</td>
      <td>${row.transaction_count}</td>
    </tr>
  `).join('');

  document.querySelector('#workbench-cards-table tbody').innerHTML = (data.card_stats || []).map((row) => `
    <tr>
      <td>${row.card_type}</td>
      <td>${row.business_role || ''}</td>
      <td>${money(row.usd_amount)}</td>
      <td>${money(row.rmb_amount)}</td>
      <td>${row.unit_face_value ?? ''}</td>
      <td>${row.unit_count ?? ''}</td>
    </tr>
  `).join('');
}

document.querySelector('#period-select').addEventListener('change', (event) => {
  loadWorkbench(event.currentTarget.value);
});

const initialPeriodId = new URLSearchParams(window.location.search).get('period_id');
loadWorkbench(initialPeriodId);
"""
    return _render_layout(
        title="账期工作台",
        subtitle="固定看一个账期的起止时间、群快照和卡种明细，不把实时余额与历史快照混在一起。",
        active_path="/workbench",
        body=body,
        script=script,
    )


def render_history_page() -> str:
    body = """
<section class="panel stack">
  <div class="toolbar">
    <div>
      <h2>跑账历史</h2>
      <div class="muted" id="history-range">请选择时间范围</div>
    </div>
    <div class="muted">按已关闭账期筛选，支持卡种关键字和排序切换。</div>
  </div>
  <form id="history-form">
    <input type="date" name="start_date" required />
    <input type="date" name="end_date" required />
    <input name="card_keyword" placeholder="卡种关键字，如 steam" />
    <select name="sort_by">
      <option value="usd_amount">按美元面额</option>
      <option value="rmb_amount">按人民币金额</option>
      <option value="unit_count">按张数</option>
      <option value="period_count">按覆盖账期数</option>
    </select>
    <button>刷新分析</button>
  </form>
  <div class="cards">
    <article class="card">
      <div class="label">账期数量</div>
      <div class="value" id="history-period-count">0</div>
    </article>
    <article class="card">
      <div class="label">区间利润</div>
      <div class="value" id="history-profit">0.00</div>
    </article>
    <article class="card">
      <div class="label">区间美元面额</div>
      <div class="value" id="history-usd">0.00</div>
    </article>
    <article class="card">
      <div class="label">卡种数</div>
      <div class="value" id="history-card-type-count">0</div>
    </article>
  </div>
</section>
<section class="panel">
  <h2>账期列表</h2>
  <table id="history-periods-table">
    <thead>
      <tr><th>账期</th><th>关闭时间</th><th>利润</th><th>美元面额</th><th>群数量</th><th>交易笔数</th></tr>
    </thead>
    <tbody></tbody>
  </table>
</section>
<section class="panel">
  <h2>卡种排行</h2>
  <table id="history-cards-table">
    <thead>
      <tr><th>卡种</th><th>美元面额</th><th>人民币金额</th><th>张数</th><th>覆盖账期数</th><th>记录数</th></tr>
    </thead>
    <tbody></tbody>
  </table>
</section>
"""
    script = """
function money(value) {
  return Number(value || 0).toFixed(2);
}

function localDate(offsetDays = 0) {
  const now = new Date();
  now.setDate(now.getDate() + offsetDays);
  return now.toISOString().slice(0, 10);
}

function monthStart() {
  const now = new Date();
  now.setDate(1);
  return now.toISOString().slice(0, 10);
}

async function loadHistoryFromForm(pushUrl = false) {
  const form = document.querySelector('#history-form');
  const params = new URLSearchParams(new FormData(form));
  const response = await fetch(`/api/history?${params.toString()}`);
  const data = await response.json();

  if (pushUrl) {
    history.replaceState({}, '', `/history?${params.toString()}`);
  }

  document.querySelector('#history-range').textContent = (data.range || {}).label || '未选择时间范围';
  document.querySelector('#history-period-count').textContent = String((data.summary || {}).period_count || 0);
  document.querySelector('#history-profit').textContent = money((data.summary || {}).total_profit);
  document.querySelector('#history-usd').textContent = money((data.summary || {}).total_usd_amount);
  document.querySelector('#history-card-type-count').textContent = String((data.summary || {}).card_type_count || 0);

  document.querySelector('#history-periods-table tbody').innerHTML = (data.period_rows || []).map((row) => `
    <tr>
      <td>${row.id}</td>
      <td>${row.closed_at}</td>
      <td>${money(row.profit)}</td>
      <td>${money(row.total_usd_amount)}</td>
      <td>${row.group_count}</td>
      <td>${row.transaction_count}</td>
    </tr>
  `).join('');

  document.querySelector('#history-cards-table tbody').innerHTML = (data.card_rankings || []).map((row) => `
    <tr>
      <td>${row.card_type}</td>
      <td>${money(row.usd_amount)}</td>
      <td>${money(row.rmb_amount)}</td>
      <td>${row.unit_count}</td>
      <td>${row.period_count}</td>
      <td>${row.row_count}</td>
    </tr>
  `).join('');
}

const urlParams = new URLSearchParams(window.location.search);
const form = document.querySelector('#history-form');
form.elements.start_date.value = urlParams.get('start_date') || monthStart();
form.elements.end_date.value = urlParams.get('end_date') || localDate();
form.elements.card_keyword.value = urlParams.get('card_keyword') || '';
form.elements.sort_by.value = urlParams.get('sort_by') || 'usd_amount';
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  await loadHistoryFromForm(true);
});

loadHistoryFromForm();
"""
    return _render_layout(
        title="跑账历史",
        subtitle="用账期区间看利润与卡种排名，先确定时间口径，再比较卡面结构变化。",
        active_path="/history",
        body=body,
        script=script,
    )


def _render_layout(*, title: str, subtitle: str, active_path: str, body: str, script: str) -> str:
    nav = """
<nav>
  <a href="/" class="%s">首页驾驶舱</a>
  <a href="/workbench" class="%s">账期工作台</a>
  <a href="/history" class="%s">跑账历史</a>
</nav>
""" % (
        "active" if active_path == "/" else "",
        "active" if active_path == "/workbench" else "",
        "active" if active_path == "/history" else "",
    )
    return (
        "<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
        f"<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{title}</title>"
        f"{_STYLE}</head><body><header><div class=\"hero\"><div><h1>{title}</h1>"
        f"<p>{subtitle}</p></div></div>{nav}</header><main>{body}</main><script>{script}</script></body></html>"
    )
