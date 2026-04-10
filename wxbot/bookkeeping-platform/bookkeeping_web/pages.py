from __future__ import annotations


_STYLE = """
<style>
  :root {
    color-scheme: light;
    --bg: #e5e7eb;
    --panel: #ffffff;
    --ink: #111827;
    --muted: #4b5563;
    --line: #cbd5e1;
    --accent: #0f766e;
    --accent-soft: #ccfbf1;
    --warn: #b91c1c;
    --shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
    color: var(--ink);
    background: var(--bg);
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
    border-radius: 8px;
    background: #ffffff;
    border: 1px solid var(--line);
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
    border-radius: 8px;
    padding: 18px;
    box-shadow: var(--shadow);
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
    border-radius: 8px;
    background: #ffffff;
    border: 1px solid var(--line);
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
    border-radius: 8px;
    border: 1px solid var(--line);
    background: #ffffff;
  }
  textarea {
    min-height: 88px;
    resize: vertical;
  }
  button {
    border: 0;
    border-radius: 8px;
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
    border-bottom: 1px solid var(--line);
    vertical-align: top;
  }
  th {
    color: var(--muted);
    font-weight: 600;
  }
  .table-wrap {
    overflow-x: auto;
  }
  .status-chip {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 72px;
    padding: 4px 10px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 600;
  }
  .status-chip.settled {
    background: var(--accent-soft);
    color: var(--accent);
  }
  .status-chip.unsettled {
    background: rgba(155, 44, 44, 0.12);
    color: var(--warn);
  }
  .mono {
    font-family: "SFMono-Regular", "Menlo", monospace;
    font-size: 12px;
  }
  .entry-grid {
    display: grid;
    gap: 14px;
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
  .entry-card {
    display: grid;
    gap: 6px;
    padding: 18px;
    border-radius: 8px;
    text-decoration: none;
    background: #ffffff;
    border: 1px solid var(--line);
  }
  .entry-card strong {
    font-size: 18px;
  }
  .subgrid {
    display: grid;
    gap: 18px;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .subpanel {
    padding: 16px;
    border-radius: 8px;
    background: #f8fafc;
    border: 1px solid var(--line);
  }
  .action-stack {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
  .action-stack button,
  .action-stack a {
    width: auto;
    flex: 0 0 auto;
  }
  .detail-list {
    display: grid;
    gap: 8px;
    margin: 0;
  }
  .detail-list div {
    display: grid;
    gap: 4px;
  }
  .detail-list dt {
    margin: 0;
    color: var(--muted);
    font-size: 12px;
    font-weight: 600;
  }
  .detail-list dd {
    margin: 0;
    line-height: 1.5;
    word-break: break-word;
  }
  .trace-status-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: grid;
    gap: 8px;
  }
  .trace-status-list li {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    align-items: center;
    padding: 8px 10px;
    border-radius: 8px;
    background: #ffffff;
    border: 1px solid var(--line);
  }
  .table-note {
    margin-top: 8px;
  }
  .quote-stack {
    display: grid;
    gap: 16px;
  }
  .quote-metrics {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
  }
  .quote-metric {
    padding: 14px;
    border-radius: 8px;
    background: #ffffff;
    border: 1px solid var(--line);
  }
  .quote-metric .label {
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 6px;
  }
  .quote-metric .value {
    font-size: 24px;
    font-weight: 600;
  }
  .quote-filter-grid {
    display: grid;
    grid-template-columns: 1.4fr 1fr 1fr 1fr 0.8fr;
    gap: 10px;
  }
  .quote-filter-grid input,
  .quote-filter-grid select,
  .quote-filter-grid button {
    border-radius: 8px;
  }
  .quote-table th,
  .quote-table td {
    white-space: nowrap;
  }
  .quote-table td.quote-note {
    white-space: normal;
    min-width: 240px;
  }
  .quote-table td.wrap {
    white-space: normal;
    min-width: 220px;
  }
  .quote-status-chip {
    display: inline-flex;
    align-items: center;
    padding: 4px 8px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 600;
  }
  .quote-status-chip.live {
    background: var(--accent-soft);
    color: var(--accent);
  }
  .quote-status-chip.watch {
    background: rgba(209, 157, 94, 0.18);
    color: #8a5200;
  }
  .quote-status-chip.stale {
    background: #fee2e2;
    color: #b91c1c;
  }
  .quote-status-chip.blocked {
    background: rgba(155, 44, 44, 0.12);
    color: var(--warn);
  }
  .quote-status-chip.pending {
    background: rgba(99, 113, 124, 0.14);
    color: var(--muted);
  }
  .quote-change-chip {
    display: inline-flex;
    align-items: center;
    padding: 4px 8px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 600;
  }
  .quote-change-chip.new {
    background: #dbeafe;
    color: #1d4ed8;
  }
  .quote-change-chip.up {
    background: #dcfce7;
    color: #15803d;
  }
  .quote-change-chip.down {
    background: #fee2e2;
    color: #b91c1c;
  }
  .quote-change-chip.flat {
    background: #f1f5f9;
    color: #475569;
  }
  .quote-note {
    color: var(--muted);
    font-size: 12px;
    line-height: 1.45;
  }
  .quote-age.stale {
    color: #b91c1c;
    font-weight: 700;
  }
  .quote-link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: auto;
    padding: 10px 12px;
    border-radius: 8px;
    background: var(--accent);
    color: white;
    text-decoration: none;
    border: 1px solid var(--accent);
  }
  .quote-source-detail {
    color: var(--muted);
    display: block;
    font-size: 12px;
    margin-top: 3px;
  }
  .quote-template-help {
    background: #f8fafc;
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 12px;
  }
  .quote-template-help strong {
    display: block;
    margin-bottom: 6px;
  }
  .quote-modal-backdrop {
    align-items: center;
    background: rgba(15, 23, 42, 0.38);
    bottom: 0;
    display: none;
    justify-content: center;
    left: 0;
    padding: 24px;
    position: fixed;
    right: 0;
    top: 0;
    z-index: 50;
  }
  .quote-modal-backdrop.open {
    display: flex;
  }
  .quote-modal {
    background: #ffffff;
    border: 1px solid var(--line);
    border-radius: 8px;
    box-shadow: 0 20px 60px rgba(15, 23, 42, 0.25);
    max-height: 86vh;
    max-width: 980px;
    overflow: auto;
    padding: 18px;
    width: min(980px, 100%);
  }
  .quote-modal-header {
    align-items: start;
    display: flex;
    gap: 12px;
    justify-content: space-between;
    margin-bottom: 12px;
  }
  .quote-modal-header h2 {
    margin: 0;
  }
  .quote-modal-close {
    width: auto;
  }
  .diff-highlight {
    color: #b42318;
    font-weight: 600;
  }
  .diff-safe {
    color: #067647;
    font-weight: 600;
  }
  .full {
    grid-column: 1 / -1;
  }
  .inline-link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: auto;
    padding: 10px 14px;
    border-radius: 8px;
    background: var(--accent);
    color: white;
    text-decoration: none;
    border: 1px solid var(--accent);
  }
  .toolbar-actions {
    display: flex;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
  }
  .toolbar-actions input {
    flex: 1 1 320px;
    min-width: 240px;
  }
  .toolbar-actions button {
    width: auto;
    flex: 0 0 auto;
  }
  @media (max-width: 980px) {
    .cards {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .quote-metrics,
    .quote-filter-grid {
      grid-template-columns: 1fr;
    }
    .entry-grid,
    .subgrid {
      grid-template-columns: 1fr;
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
    <div class="muted">当前余额按实时交易余额；今日已实现利润只看结算账期；当前实时预估利润单独展示。</div>
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
      <div class="label">当前实时预估利润</div>
      <div class="value" id="summary-estimated-profit">0.00</div>
    </article>
    <article class="card">
      <div class="label">实时账期总计刀数</div>
      <div class="value" id="summary-vendor-usd">0.00</div>
    </article>
    <article class="card">
      <div class="label">未归属/待处理群数</div>
      <div class="value" id="summary-unassigned">0</div>
    </article>
  </div>
</section>
<section class="panel stack">
  <div class="toolbar">
    <div>
      <h2>当前实时卡统计</h2>
      <div class="muted">用最新实时交易估算本轮客户卖卡、供应商拿卡和预估利润。</div>
    </div>
  </div>
  <div class="subgrid">
    <section class="subpanel">
      <h3>客户侧</h3>
      <div class="muted" id="dashboard-current-customer-summary">加载中</div>
      <div class="table-wrap">
        <table id="dashboard-current-customer-table">
          <thead>
            <tr><th>卡种</th><th>刀数</th><th>金额</th><th>差额</th><th>利润</th></tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </section>
    <section class="subpanel">
      <h3>供应商侧</h3>
      <div class="muted" id="dashboard-current-vendor-summary">加载中</div>
      <div class="table-wrap">
        <table id="dashboard-current-vendor-table">
          <thead>
            <tr><th>卡种</th><th>刀数</th><th>金额</th></tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </section>
  </div>
</section>
<section class="panel stack">
  <div class="toolbar">
    <div>
      <h2>最新识别交易流</h2>
      <div class="muted">默认展示最近识别的全部结构化交易，快速确认采集、解析和关账状态。</div>
    </div>
    <div class="muted">首页只做观察，不在这里发起修正或治理动作。</div>
  </div>
  <div class="table-wrap">
    <table id="latest-transactions-table">
      <thead>
        <tr><th>群</th><th>角色</th><th>发送人</th><th>分类</th><th>汇率</th><th>刀数</th><th>人民币</th><th>时间</th><th>状态</th></tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>
</section>
<section class="panel stack">
  <div>
    <h2>工作入口</h2>
    <div class="muted">首页给信号，真正的账期查看、关账、修正和组合治理都进入工作台处理。</div>
  </div>
  <div class="entry-grid">
    <a class="entry-card" href="/workbench">
      <strong>进入账期工作台</strong>
      <span>查看账期摘要、结构化交易明细、群快照和卡种统计，并承接关账与治理动作。</span>
    </a>
    <a class="entry-card" href="/reconciliation">
      <strong>进入对账中心</strong>
      <span>按逐笔台账检查汇率、RMB 加减、修改痕迹和财务补录，并一键导出给财务核对。</span>
    </a>
    <a class="entry-card" href="/role-mapping">
      <strong>进入角色映射页</strong>
      <span>专门核对群角色、组号默认规则和口语别名归一化，不再把映射表塞在首页或工作台里。</span>
    </a>
    <a class="entry-card" href="/history">
      <strong>进入跑账历史页</strong>
      <span>按时间区间比较利润与卡种结构变化，做复盘和趋势分析。</span>
    </a>
  </div>
</section>
"""
    script = """
function money(value) {
  return Number(value || 0).toFixed(2);
}

function compactNumber(value) {
  if (value === null || value === undefined || value === '') {
    return '';
  }
  return Number(value).toFixed(2).replace(/\\.00$/, '');
}

function rateText(value) {
  if (value === null || value === undefined || value === '') {
    return '—';
  }
  return compactNumber(value);
}

function statusChip(status) {
  const normalized = status === 'settled' ? 'settled' : 'unsettled';
  const label = normalized === 'settled' ? '结算' : '实时';
  return `<span class="status-chip ${normalized}">${label}</span>`;
}

function roleText(role) {
  if (role === 'customer') return '客户';
  if (role === 'vendor') return '供应商';
  if (role === 'internal') return '内部';
  return '未归属';
}

function roleSourceText(source) {
  if (source === 'manual') return '手工指定';
  if (source === 'group_num') return '组号映射';
  return '未映射';
}

function roleCardSummaryText(block) {
  return `合计 ${money(block.total_usd_amount)} 刀 / ${money(block.total_display_rmb_amount ?? block.total_rmb_amount)} 元`;
}

function signedMoney(value) {
  const number = Number(value || 0);
  return `${number > 0 ? '+' : ''}${money(number)}`;
}

function diffClass(value) {
  return Number(value || 0) === 0 ? 'diff-safe' : 'diff-highlight';
}

function buildCardRowMap(rows) {
  const map = {};
  for (const row of (rows || [])) {
    const cardType = String(row.card_type || '').trim();
    if (!cardType) continue;
    map[cardType] = {
      card_type: cardType,
      usd_amount: Number(row.usd_amount ?? 0),
      rmb_amount: Number(row.rmb_amount ?? 0),
      display_rmb_amount: Number(row.display_rmb_amount ?? row.rmb_amount ?? 0),
    };
  }
  return map;
}

function alignRoleCardRows(customerRows, vendorRows) {
  const customerMap = buildCardRowMap(customerRows);
  const vendorMap = buildCardRowMap(vendorRows);
  const allCardTypes = Array.from(new Set([
    ...Object.keys(customerMap),
    ...Object.keys(vendorMap),
  ])).sort((a, b) => a.localeCompare(b, 'en', { sensitivity: 'base' }));

  const zeroRowFor = (cardType) => ({
    card_type: cardType,
    usd_amount: 0,
    rmb_amount: 0,
    display_rmb_amount: 0,
  });

  return {
    customerRows: allCardTypes.map((cardType) => customerMap[cardType] || zeroRowFor(cardType)),
    vendorRows: allCardTypes.map((cardType) => vendorMap[cardType] || zeroRowFor(cardType)),
  };
}

function renderRoleCardTable(tableId, rows, emptyText, options = {}) {
  const showDiff = Boolean(options.showDiff);
  const diffKnifeByCardType = options.diffKnifeByCardType || {};
  const profitByCardType = options.profitByCardType || {};
  const colspan = showDiff ? 5 : 3;
  document.querySelector(`${tableId} tbody`).innerHTML = rows.length
    ? rows.map((row) => `
      <tr>
        <td>${row.card_type}</td>
        <td>${money(row.usd_amount)}</td>
        <td>${money(row.display_rmb_amount ?? row.rmb_amount)}</td>
        ${showDiff ? `<td><span class="${diffClass(diffKnifeByCardType[row.card_type] ?? 0)}">${signedMoney(diffKnifeByCardType[row.card_type] ?? 0)}</span></td><td>${signedMoney(profitByCardType[row.card_type] ?? 0)}</td>` : ''}
      </tr>
    `).join('')
    : `<tr><td colspan="${colspan}" class="muted">${emptyText}</td></tr>`;
}

async function loadDashboard() {
  const response = await fetch('/api/dashboard');
  const data = await response.json();
  const summary = data.summary || {};

  document.querySelector('#dashboard-range').textContent = summary.today_period_count
    ? (summary.range_label || '按今日结算账期')
    : `${summary.range_label || '按今日结算账期'}，今日暂无结算账期，请同时参考当前实时预估利润`;
  document.querySelector('#summary-total-balance').textContent = money(summary.current_total_balance);
  document.querySelector('#summary-profit').textContent = money(summary.today_realized_profit);
  document.querySelector('#summary-estimated-profit').textContent = money(summary.current_estimated_profit);
  document.querySelector('#summary-vendor-usd').textContent = money(summary.current_vendor_card_usd_amount);
  document.querySelector('#summary-unassigned').textContent = String(summary.unassigned_group_count || 0);
  const currentBreakdown = summary.current_role_card_breakdown || {};
  const currentCustomer = currentBreakdown.customer || { rows: [], total_usd_amount: 0, total_rmb_amount: 0, total_unit_count: 0 };
  const currentVendor = currentBreakdown.vendor || { rows: [], total_usd_amount: 0, total_rmb_amount: 0, total_unit_count: 0 };
  const alignedRows = alignRoleCardRows(currentCustomer.rows || [], currentVendor.rows || []);
  const vendorAmountByCardType = {};
  const vendorKnifeByCardType = {};
  for (const row of alignedRows.vendorRows) {
    vendorAmountByCardType[row.card_type] = Number(row.display_rmb_amount ?? row.rmb_amount ?? 0);
    vendorKnifeByCardType[row.card_type] = Number(row.usd_amount ?? 0);
  }
  const customerDiffKnifeByCardType = {};
  const customerProfitByCardType = {};
  for (const row of alignedRows.customerRows) {
    const customerAmount = Number(row.display_rmb_amount ?? row.rmb_amount ?? 0);
    const customerKnife = Number(row.usd_amount ?? 0);
    const vendorAmount = Number(vendorAmountByCardType[row.card_type] ?? 0);
    const vendorKnife = Number(vendorKnifeByCardType[row.card_type] ?? 0);
    customerDiffKnifeByCardType[row.card_type] = customerKnife - vendorKnife;
    customerProfitByCardType[row.card_type] = customerAmount - vendorAmount;
  }
  document.querySelector('#dashboard-current-customer-summary').textContent = roleCardSummaryText(currentCustomer);
  document.querySelector('#dashboard-current-vendor-summary').textContent = roleCardSummaryText(currentVendor);
  renderRoleCardTable(
    '#dashboard-current-customer-table',
    alignedRows.customerRows,
    '当前暂无客户卡统计',
    {
      showDiff: true,
      diffKnifeByCardType: customerDiffKnifeByCardType,
      profitByCardType: customerProfitByCardType,
    }
  );
  renderRoleCardTable('#dashboard-current-vendor-table', alignedRows.vendorRows, '当前暂无供应商卡统计');
  const transactions = data.latest_transactions || [];
  document.querySelector('#latest-transactions-table tbody').innerHTML = transactions.length
    ? transactions.map((row) => `
      <tr>
        <td>${row.chat_name}</td>
        <td>${roleText(row.business_role)}</td>
        <td>${row.sender_name}</td>
        <td>${row.category}</td>
        <td>${rateText(row.rate)}</td>
        <td>${money(row.display_usd_amount)}</td>
        <td>${money(row.display_rmb_amount ?? row.rmb_value)}</td>
        <td>${row.created_at}</td>
        <td>${statusChip(row.period_status)}</td>
      </tr>
    `).join('')
    : '<tr><td colspan="9" class="muted">暂无最近识别交易</td></tr>';
}

loadDashboard();
"""
    return _render_layout(
        title="总账中心",
        subtitle="驾驶舱先给信号，再决定进入哪个账期工作台或历史分析页。",
        active_path="/",
        body=body,
        script=script,
    )


def render_quotes_page() -> str:
    body = """
<section class="panel stack">
  <div class="toolbar">
    <div>
      <h2>报价墙</h2>
      <div class="muted" id="quote-board-range">当前客人报价加载中</div>
    </div>
    <div class="toolbar-actions">
      <button type="button" id="quote-refresh-btn">刷新</button>
      <a class="quote-link" href="#quote-exceptions">查看异常</a>
    </div>
  </div>
  <div class="quote-metrics">
    <article class="quote-metric">
      <div class="label">当前可用</div>
      <div class="value" id="quote-live-count">0</div>
    </article>
    <article class="quote-metric">
      <div class="label">来源客人群</div>
      <div class="value" id="quote-source-count">0</div>
    </article>
    <article class="quote-metric">
      <div class="label">异常数量</div>
      <div class="value" id="quote-exception-count">0</div>
    </article>
  </div>
  <form id="quote-filter-form" class="quote-filter-grid">
    <input name="search" id="quote-search" type="search" placeholder="搜卡种 / 国家 / 面额 / 形态 / 限制" autocomplete="off" />
    <input name="card_type" id="quote-card-type" placeholder="卡种，如 Steam" />
    <input name="country_or_currency" id="quote-country" placeholder="国家 / 币种，如 USD" />
    <input name="source_group_key" id="quote-source-group" placeholder="客人群 Key" />
    <select name="quote_status" id="quote-status">
      <option value="">全部状态</option>
      <option value="live">可用</option>
      <option value="stale">超时</option>
      <option value="watch">观察</option>
      <option value="blocked">不收</option>
      <option value="pending">待处理</option>
    </select>
    <select name="form_factor" id="quote-form-factor">
      <option value="">全部形态</option>
      <option value="card">卡图</option>
      <option value="code">代码</option>
      <option value="paper">纸质</option>
      <option value="electron">电子</option>
      <option value="horizontal">横板</option>
      <option value="vertical">竖卡</option>
    </select>
    <button type="submit">筛选</button>
    <button type="button" id="quote-filter-clear">清空</button>
  </form>
  <div class="muted" id="quote-filter-status">按卡种看当前最高价；点“刷新”重新拉取报价墙数据。</div>
  <div class="table-wrap">
    <table id="quote-board-table" class="quote-table">
      <thead>
        <tr><th>卡种</th><th>国家 / 币种</th><th>面额 / 条件</th><th>形态</th><th>最高价</th><th>变化</th><th>客人群</th><th>发送者ID</th><th>更新时间</th><th>已存在</th><th>状态</th><th>限制</th><th>操作</th></tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>
</section>
<section class="panel stack" id="quote-profile-panel">
  <div class="toolbar">
    <div>
      <h2>客人群模板</h2>
      <div class="muted">先配置群默认卡种、解析模板和超时时间；实机测试时按测试群逐个补。</div>
    </div>
  </div>
  <form id="quote-profile-form" class="quote-filter-grid">
    <input name="platform" placeholder="平台，如 whatsapp" />
    <input name="chat_id" placeholder="群ID / chat_id" required />
    <input name="chat_name" placeholder="群名" />
    <input name="default_card_type" placeholder="默认卡种，如 Apple" />
    <input name="default_country_or_currency" placeholder="默认国家/币种，如 USD" />
    <input name="default_form_factor" placeholder="默认形态，如 横白/竖卡/代码" />
    <input name="default_multiplier" placeholder="默认倍数，可空，如 50X" />
    <input name="parser_template" placeholder="模板，如 apple_modifier_sheet" list="quote-template-options" />
    <datalist id="quote-template-options">
      <option value="sectioned_group_sheet"></option>
      <option value="group_fixed_sheet"></option>
      <option value="apple_modifier_sheet"></option>
      <option value="section_sheet"></option>
      <option value="simple_sheet"></option>
    </datalist>
    <input name="stale_after_minutes" placeholder="超时分钟，如 30" />
    <textarea name="template_config" placeholder="高级模板配置，可先留空"></textarea>
    <button type="submit">保存模板</button>
    <button type="button" id="quote-profile-clear">清空表单</button>
  </form>
  <div class="muted" id="quote-profile-prefill-status">可从异常区一键填充群模板。</div>
  <div class="quote-template-help">
    <strong>group_fixed_sheet</strong>
    <div class="muted">群专用固定模板：建议配好默认卡种 + 默认币种；按 `100=5.55` / `300/400/500=5.55` 解析，`#...` 作为限制说明，`#竖卡-0.1` 可派生形态价。</div>
  </div>
  <div class="quote-template-help">
    <strong>apple_modifier_sheet</strong>
    <div class="muted">Apple 群模板：默认卡种 Apple；识别 US横白卡 基准价；识别 50X 倍数；#竖卡-0.1 / #电子-0.15 / #代码-0.3 按同一上下文派生价格；默认 30 分钟超时。</div>
  </div>
  <div class="table-wrap">
    <table id="quote-profile-table" class="quote-table">
      <thead>
        <tr><th>平台</th><th>群ID</th><th>群名</th><th>默认卡种</th><th>默认币种</th><th>默认形态</th><th>默认倍数</th><th>模板</th><th>超时</th><th>备注</th></tr>
      </thead>
      <tbody><tr><td colspan="10" class="muted">暂无模板配置</td></tr></tbody>
    </table>
  </div>
</section>
<section class="panel stack" id="quote-inquiry-panel">
  <div class="toolbar">
    <div>
      <h2>短回复上下文</h2>
      <div class="muted">供应商或同事问完价格后，先建上下文；同一个客人群下一条短回复如 6.25 才能补成完整报价。</div>
    </div>
  </div>
  <form id="quote-inquiry-form" class="quote-filter-grid">
    <input name="chat_id" placeholder="回复客人群ID / chat_id" required />
    <input name="chat_name" placeholder="回复客人群名" />
    <input name="card_type" placeholder="卡种，如 Apple" required />
    <input name="country_or_currency" placeholder="国家 / 币种，如 UK" required />
    <input name="amount_range" placeholder="面额，如 10" required />
    <input name="form_factor" placeholder="形态，如 不限 / 代码" />
    <input name="multiplier" placeholder="倍数，可空" />
    <input name="prompt_text" placeholder="原始询价，如 Apple UK 10 现在什么价" />
    <button type="submit">创建上下文</button>
  </form>
  <div class="table-wrap">
    <table id="quote-inquiry-table" class="quote-table">
      <thead>
        <tr><th>状态</th><th>客人群</th><th>卡种</th><th>国家 / 币种</th><th>面额</th><th>形态</th><th>有效到</th><th>来源询价</th></tr>
      </thead>
      <tbody><tr><td colspan="8" class="muted">暂无短回复上下文</td></tr></tbody>
    </table>
  </div>
</section>
<section class="panel stack" id="quote-exceptions">
  <div class="toolbar">
    <div>
      <h2>异常区</h2>
      <div class="muted" id="quote-exception-range">低置信、缺上下文、模板不匹配会先放在这里。</div>
    </div>
  </div>
  <div class="table-wrap">
    <table id="quote-exception-table" class="quote-table">
      <thead>
        <tr><th>时间</th><th>来源客人群</th><th>发送者ID</th><th>异常行</th><th>原因</th><th>建议处理</th><th>模板</th><th>置信度</th><th>状态</th><th>操作</th></tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>
</section>
<div class="quote-modal-backdrop" id="quote-ranking-modal" aria-hidden="true">
  <div class="quote-modal" role="dialog" aria-modal="true" aria-labelledby="quote-ranking-title">
    <div class="quote-modal-header">
      <div>
        <h2>报价排名</h2>
        <div class="muted" id="quote-ranking-title">点击报价墙任意一行查看同 SKU 客人排名。</div>
      </div>
      <button class="quote-modal-close" type="button" id="quote-ranking-close">关闭</button>
    </div>
    <div class="table-wrap">
      <table id="quote-ranking-table" class="quote-table">
        <thead>
          <tr><th>排名</th><th>客人群</th><th>价格</th><th>变化</th><th>更新时间</th><th>已存在</th><th>限制</th></tr>
        </thead>
        <tbody><tr><td colspan="7" class="muted">未选择报价行</td></tr></tbody>
      </table>
    </div>
  </div>
</div>
<div class="quote-modal-backdrop" id="quote-annotate-modal" aria-hidden="true">
  <div class="quote-modal" role="dialog" aria-modal="true">
    <div class="quote-modal-header">
      <div><h2>标注异常行</h2></div>
      <button class="quote-modal-close" type="button" id="quote-annotate-close">关闭</button>
    </div>
    <div style="padding: 12px 0;">
      <div class="muted" style="margin-bottom:8px;">原文</div>
      <div id="quote-annotate-source" style="background:#f5f5f5;padding:8px;border-radius:4px;font-family:monospace;word-break:break-all;"></div>
      <form id="quote-annotate-form" style="margin-top:12px;display:flex;flex-direction:column;gap:8px;">
        <input type="hidden" name="exception_id" value="">
        <label>卡种 <input type="text" name="card_type" placeholder="如：XBOX、FT"></label>
        <label>国家 <input type="text" name="country" placeholder="如：加拿大、美国"></label>
        <label>面额 <input type="text" name="amount" placeholder="如：10-1000"></label>
        <label>形态 <input type="text" name="form_factor" placeholder="如：实卡、代码"></label>
        <label>价格 <input type="text" name="price" placeholder="如：3.4"></label>
      </form>
      <div class="muted" style="margin-top:8px;">预览 pattern</div>
      <div id="quote-annotate-preview" style="font-family:monospace;color:#0a0;"></div>
    </div>
    <div style="display:flex;gap:8px;justify-content:flex-end;">
      <button type="button" id="quote-annotate-cancel">取消</button>
      <button type="button" id="quote-annotate-submit" style="font-weight:bold;">确认并保存</button>
    </div>
  </div>
</div>
"""
    script = """
const QUOTE_STALE_MINUTES = 30;

function compactNumber(value) {
  if (value === null || value === undefined || value === '') {
    return '';
  }
  return Number(value).toFixed(2).replace(/\\.00$/, '');
}

function textValue(value, fallback = '—') {
  const text = String(value ?? '').trim();
  return text || fallback;
}

function formatQuoteTime(value) {
  const text = String(value || '').trim();
  if (!text) return '—';
  const date = parseQuoteDate(text);
  if (!date) return text;
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const dd = String(date.getDate()).padStart(2, '0');
  const hh = String(date.getHours()).padStart(2, '0');
  const mi = String(date.getMinutes()).padStart(2, '0');
  const ss = String(date.getSeconds()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd} ${hh}:${mi}:${ss}`;
}

function quoteStatusClass(status) {
  const normalized = String(status || '').toLowerCase();
  if (normalized === 'live' || normalized === 'active' || normalized === 'available') return 'live';
  if (normalized === 'watch' || normalized === 'attention') return 'watch';
  if (normalized === 'blocked' || normalized === 'disabled' || normalized === 'rejected') return 'blocked';
  if (normalized === 'ignored' || normalized === 'resolved') return 'watch';
  return 'pending';
}

function quoteStatusText(status) {
  const normalized = String(status || '').toLowerCase();
  if (normalized === 'live' || normalized === 'active' || normalized === 'available') return '可用';
  if (normalized === 'watch' || normalized === 'attention') return '观察';
  if (normalized === 'blocked' || normalized === 'disabled' || normalized === 'rejected') return '不收';
  if (normalized === 'ignored') return '已忽略';
  if (normalized === 'resolved') return '已处理';
  if (normalized === 'open') return '等待回复';
  if (normalized === 'pending' || normalized === 'review') return '待处理';
  return textValue(status);
}

function quoteDisplayStatusClass(row) {
  if (quoteIsStale(row) && quoteStatusClass(row.quote_status || row.status) === 'live') {
    return 'stale';
  }
  return quoteStatusClass(row.quote_status || row.status);
}

function quoteDisplayStatusText(row) {
  if (quoteIsStale(row) && quoteStatusClass(row.quote_status || row.status) === 'live') {
    return '超时';
  }
  return quoteStatusText(row.quote_status || row.status);
}

function quoteChangeClass(status) {
  const normalized = String(status || '').toLowerCase();
  if (normalized === 'new') return 'new';
  if (normalized === 'up' || normalized === 'rise') return 'up';
  if (normalized === 'down' || normalized === 'drop') return 'down';
  return 'flat';
}

function quoteChangeText(row) {
  const status = quoteChangeClass(row.change_status);
  const delta = row.price_change;
  if (status === 'new') return '新增';
  if (status === 'up') return `涨价 +${compactNumber(delta)}`;
  if (status === 'down') return `跌价 ${compactNumber(delta)}`;
  return '持平';
}

function quoteFormFactorText(value) {
  const normalized = normalizeFormFactorText(value);
  if (!normalized) return '—';
  return normalized;
}

function normalizeFormFactorText(value) {
  const text = String(value || '').trim();
  if (!text) return '';
  const lowered = text.toLowerCase();
  if (
    text.includes('横白')
    || text.includes('横卡')
    || text.includes('横板')
    || text.includes('卡图')
    || text.includes('图片')
    || lowered === 'horizontal'
    || lowered === 'photo'
    || lowered === 'image'
    || lowered === 'card'
  ) return '横白';
  if (text.includes('竖卡') || text.includes('竖板') || lowered === 'vertical') return '竖卡';
  if (text.includes('代码') || lowered === 'code') return '代码';
  if (text.includes('电子') || lowered === 'electron' || lowered === 'electronic') return '电子';
  if (text.includes('纸质') || lowered === 'paper') return '纸质';
  return text;
}

function quoteCountryText(row) {
  return textValue(row.country_or_currency || row.currency || row.country || row.region);
}

function quoteAmountText(row) {
  return textValue(
    row.amount_label
      || row.amount_display
      || row.amount_range
      || row.face_value_range
      || row.condition_text
      || row.amount
  );
}

function quoteSourceText(row) {
  return textValue(row.source_group_name || row.chat_name || row.source_group_key || row.group_key);
}

function quoteSourceDetailText(row) {
  return textValue(row.chat_id || row.source_group_key || row.group_key);
}

function quoteRestrictionText(row) {
  return textValue(row.restriction_text || row.note || row.remark);
}

function quoteExceptionActions(row) {
  const status = String(row.resolution_status || row.status || 'open').toLowerCase();
  if (status !== 'open') {
    return '<span class="muted">已处理</span>';
  }
  const actions = [];
  if (String(row.reason || '') === 'blocked_or_question_line') {
    actions.push(`<button type="button" data-quote-exception-attach="${row.id}">附加限制</button>`);
  }
  actions.push(`<button type="button" data-quote-template-prefill="${row.id}">一键建模板</button>`);
  actions.push(`<button type="button" data-quote-exception-annotate="${row.id}">标注</button>`);
  if (String(row.reason || '').includes('unknown')) {
    actions.push(`<button type="button" data-quote-dictionary-prefill="${row.id}">添加到字典</button>`);
  }
  actions.push(`<button type="button" data-quote-exception-ignore="${row.id}">忽略</button>`);
  return actions.join('');
}

function parseQuoteDate(value) {
  const text = String(value || '').trim();
  if (!text) return null;
  let normalized = text.includes('T') ? text : text.replace(' ', 'T');
  if (!/(Z|[+-]\\d{2}:?\\d{2})$/.test(normalized)) {
    normalized = `${normalized}Z`;
  }
  const date = new Date(normalized);
  return Number.isNaN(date.getTime()) ? null : date;
}

function quoteAgeMinutes(value) {
  const date = parseQuoteDate(value);
  if (!date) return null;
  const diffSeconds = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));
  return Math.floor(diffSeconds / 60);
}

function quoteAgeText(value) {
  const date = parseQuoteDate(value);
  if (!date) return '—';
  const diffSeconds = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));
  if (diffSeconds < 60) return '刚刚';
  const minutes = Math.floor(diffSeconds / 60);
  if (minutes < 60) return `${minutes}分钟`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    const restMinutes = minutes % 60;
    return restMinutes ? `${hours}小时${restMinutes}分钟` : `${hours}小时`;
  }
  const days = Math.floor(hours / 24);
  const restHours = hours % 24;
  return restHours ? `${days}天${restHours}小时` : `${days}天`;
}

function quoteIsStale(row) {
  const minutes = quoteAgeMinutes(row.effective_at || row.message_time || row.created_at || row.updated_at || row.received_at);
  const threshold = Number(row.stale_after_minutes || QUOTE_STALE_MINUTES);
  return minutes !== null && minutes >= threshold;
}

function quoteAgeClass(row) {
  return quoteIsStale(row) ? 'quote-age stale' : 'quote-age';
}

function quoteSearchText(row) {
  return [
    row.card_type,
    row.country_or_currency,
    row.currency,
    row.country,
    row.region,
    row.amount_label,
    row.amount_range,
    row.face_value_range,
    row.condition_text,
    row.form_factor,
    row.restriction_text,
    row.note,
    row.remark,
    row.source_group_name,
    row.source_group_key,
    row.sender_id,
  ].map((item) => String(item || '').toLowerCase()).join(' ');
}

function quoteRowMatches(row, filters) {
  const search = String(filters.search || '').trim().toLowerCase();
  if (search && !quoteSearchText(row).includes(search)) {
    return false;
  }
  if (filters.card_type && String(row.card_type || '').toLowerCase() !== String(filters.card_type).toLowerCase()) {
    return false;
  }
  if (filters.country_or_currency) {
    const country = String(row.country_or_currency || row.currency || row.country || row.region || '').toLowerCase();
    if (country !== String(filters.country_or_currency).toLowerCase()) {
      return false;
    }
  }
  if (filters.source_group_key && String(row.source_group_key || row.group_key || '').toLowerCase() !== String(filters.source_group_key).toLowerCase()) {
    return false;
  }
  if (filters.quote_status) {
    if (quoteDisplayStatusClass(row) !== String(filters.quote_status).toLowerCase()) {
      return false;
    }
  }
  if (filters.form_factor) {
    const rowForm = normalizeFormFactorText(row.form_factor || '');
    const filterForm = normalizeFormFactorText(filters.form_factor || '');
    if (rowForm !== filterForm) {
      return false;
    }
  }
  return true;
}

function latestQuoteTime(rows) {
  let latest = '';
  for (const row of rows || []) {
    const value = String(row.updated_at || row.effective_at || row.created_at || row.message_time || row.received_at || '');
    if (value && value > latest) {
      latest = value;
    }
  }
  return formatQuoteTime(latest);
}

let allQuoteRows = [];
let allQuoteExceptions = [];
let allQuoteProfiles = [];
let allQuoteInquiries = [];

function currentQuoteFilters() {
  const form = document.querySelector('#quote-filter-form');
  return Object.fromEntries(new FormData(form).entries());
}

function renderQuoteBoard(rows) {
  const filteredRows = rows.filter((row) => quoteRowMatches(row, currentQuoteFilters()));
  document.querySelector('#quote-live-count').textContent = String(filteredRows.length);
  document.querySelector('#quote-source-count').textContent = String(new Set(filteredRows.map((row) => quoteSourceText(row))).size);
  document.querySelector('#quote-board-range').textContent = filteredRows.length
    ? `已加载 ${filteredRows.length} 条可用报价，最新更新时间 ${latestQuoteTime(filteredRows) || '—'}。`
    : '当前没有可用报价。';
  document.querySelector('#quote-filter-status').textContent = filteredRows.length
    ? `当前显示 ${filteredRows.length} 条报价。`
    : '没有匹配的报价。';
  document.querySelector('#quote-board-table tbody').innerHTML = filteredRows.length
    ? filteredRows.map((row) => `
      <tr>
        <td>${textValue(row.card_type)}</td>
        <td>${quoteCountryText(row)}</td>
        <td>${quoteAmountText(row)}</td>
        <td>${quoteFormFactorText(row.form_factor || row.quote_form_factor)}</td>
        <td>${compactNumber(row.price ?? row.rate ?? row.quote_price ?? '')}</td>
        <td><span class="quote-change-chip ${quoteChangeClass(row.change_status)}">${quoteChangeText(row)}</span></td>
        <td>${quoteSourceText(row)}<span class="quote-source-detail">${quoteSourceDetailText(row)}</span></td>
        <td>${textValue(row.sender_id)}</td>
        <td>${formatQuoteTime(row.updated_at || row.effective_at || row.created_at || row.message_time || row.received_at)}</td>
        <td class="${quoteAgeClass(row)}">${quoteAgeText(row.effective_at || row.message_time || row.created_at || row.updated_at || row.received_at)}</td>
        <td><span class="quote-status-chip ${quoteDisplayStatusClass(row)}">${quoteDisplayStatusText(row)}</span></td>
        <td class="quote-note">${quoteRestrictionText(row)}</td>
        <td><button type="button" data-quote-ranking-id="${row.id}">排名</button> <button type="button" class="quote-delete-btn" data-quote-delete-id="${row.id}" style="color:#c0392b;border-color:#c0392b">删除</button></td>
      </tr>
    `).join('')
    : '<tr><td colspan="13" class="muted">暂无可用报价</td></tr>';
  bindQuoteRankingButtons();
  bindQuoteDeleteButtons();
}

function bindQuoteDeleteButtons() {
  document.querySelectorAll('[data-quote-delete-id]').forEach((button) => {
    button.addEventListener('click', async () => {
      const id = button.dataset.quoteDeleteId;
      if (!confirm('确定删除这条报价？')) return;
      button.disabled = true;
      button.textContent = '删除中...';
      try {
        const resp = await fetch('/api/quotes/delete', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({id: Number(id)})
        });
        const data = await resp.json();
        if (data.deleted) {
          button.closest('tr').remove();
        } else {
          alert('删除失败: ' + (data.error || '未知错误'));
          button.disabled = false;
          button.textContent = '删除';
        }
      } catch (e) {
        alert('删除失败: ' + e.message);
        button.disabled = false;
        button.textContent = '删除';
      }
    });
  });
}

function bindQuoteRankingButtons() {
  document.querySelectorAll('[data-quote-ranking-id]').forEach((button) => {
    button.addEventListener('click', async () => {
      const row = allQuoteRows.find((item) => String(item.id) === String(button.dataset.quoteRankingId));
      if (row) {
        await loadQuoteRanking(row);
      }
    });
  });
}

async function loadQuoteRanking(row) {
  document.querySelector('#quote-ranking-modal').classList.add('open');
  document.querySelector('#quote-ranking-modal').setAttribute('aria-hidden', 'false');
  document.querySelector('#quote-ranking-title').textContent = `${textValue(row.card_type)} / ${quoteCountryText(row)} / ${quoteAmountText(row)} / ${quoteFormFactorText(row.form_factor)}：加载中`;
  document.querySelector('#quote-ranking-table tbody').innerHTML = '<tr><td colspan="7" class="muted">正在加载排名</td></tr>';
  const params = new URLSearchParams({
    card_type: row.card_type || '',
    country_or_currency: row.country_or_currency || '',
    amount_range: row.amount_range || '',
    form_factor: row.form_factor || '',
  });
  if (row.multiplier) {
    params.set('multiplier', row.multiplier);
  }
  const response = await fetch(`/api/quotes/rankings?${params.toString()}`);
  const payload = await response.json();
  const rankingRows = Array.isArray(payload.rows) ? payload.rows : [];
  document.querySelector('#quote-ranking-title').textContent = `${textValue(row.card_type)} / ${quoteCountryText(row)} / ${quoteAmountText(row)} / ${quoteFormFactorText(row.form_factor)}：共 ${rankingRows.length} 个来源`;
  document.querySelector('#quote-ranking-table tbody').innerHTML = rankingRows.length
    ? rankingRows.map((item, index) => `
      <tr>
        <td>${index + 1}</td>
        <td>${quoteSourceText(item)}<span class="quote-source-detail">${quoteSourceDetailText(item)}</span></td>
        <td>${compactNumber(item.price)}</td>
        <td><span class="quote-change-chip ${quoteChangeClass(item.change_status)}">${quoteChangeText(item)}</span></td>
        <td>${formatQuoteTime(item.effective_at || item.message_time || item.created_at)}</td>
        <td class="${quoteAgeClass(item)}">${quoteAgeText(item.effective_at || item.message_time || item.created_at)}</td>
        <td class="quote-note">${quoteRestrictionText(item)}</td>
      </tr>
    `).join('')
    : '<tr><td colspan="7" class="muted">没有同 SKU 排名数据</td></tr>';
}

function closeQuoteRankingModal() {
  document.querySelector('#quote-ranking-modal').classList.remove('open');
  document.querySelector('#quote-ranking-modal').setAttribute('aria-hidden', 'true');
}

function renderQuoteProfiles(rows) {
  allQuoteProfiles = rows || [];
  document.querySelector('#quote-profile-table tbody').innerHTML = allQuoteProfiles.length
    ? allQuoteProfiles.map((row) => `
      <tr>
        <td>${textValue(row.platform)}</td>
        <td>${textValue(row.chat_id)}</td>
        <td>${textValue(row.chat_name)}</td>
        <td>${textValue(row.default_card_type)}</td>
        <td>${textValue(row.default_country_or_currency)}</td>
        <td>${textValue(row.default_form_factor)}</td>
        <td>${textValue(row.default_multiplier)}</td>
        <td>${textValue(row.parser_template)}</td>
        <td>${textValue(row.stale_after_minutes)}分钟</td>
        <td class="quote-note">${textValue(row.note)}</td>
      </tr>
    `).join('')
    : '<tr><td colspan="10" class="muted">暂无模板配置</td></tr>';
}

function renderQuoteInquiries(rows) {
  allQuoteInquiries = rows || [];
  document.querySelector('#quote-inquiry-table tbody').innerHTML = allQuoteInquiries.length
    ? allQuoteInquiries.map((row) => `
      <tr>
        <td><span class="quote-status-chip ${quoteStatusClass(row.status)}">${quoteStatusText(row.status)}</span></td>
        <td>${textValue(row.chat_name || row.chat_id)}<span class="quote-source-detail">${textValue(row.chat_id)}</span></td>
        <td>${textValue(row.card_type)}</td>
        <td>${textValue(row.country_or_currency)}</td>
        <td>${textValue(row.amount_range)}${row.multiplier ? ` / ${textValue(row.multiplier)}` : ''}</td>
        <td>${quoteFormFactorText(row.form_factor)}</td>
        <td>${formatQuoteTime(row.expires_at)}</td>
        <td class="quote-note">${textValue(row.prompt_text)}</td>
      </tr>
    `).join('')
    : '<tr><td colspan="8" class="muted">暂无短回复上下文</td></tr>';
}

function renderQuoteExceptions(rows) {
  const filteredRows = rows;
  document.querySelector('#quote-exception-count').textContent = String(filteredRows.length);
  document.querySelector('#quote-exception-range').textContent = filteredRows.length
    ? `已收集 ${filteredRows.length} 条异常，优先处理模板不匹配和缺上下文短报价。`
    : '当前没有异常。';
  document.querySelector('#quote-exception-table tbody').innerHTML = filteredRows.length
    ? filteredRows.map((row) => `
      <tr>
        <td>${formatQuoteTime(row.message_time || row.created_at || row.updated_at || row.received_at)}</td>
        <td>${textValue(row.source_group_name || row.chat_name || row.source_group_key || row.group_key)}<span class="quote-source-detail">${quoteSourceDetailText(row)}</span></td>
        <td>${textValue(row.sender_id)}</td>
        <td class="quote-note">${textValue(row.source_line || row.line || row.text)}</td>
        <td>${textValue(row.reason_label || row.reason || row.error_reason || row.status)}</td>
        <td class="quote-note">${textValue(row.suggested_action || row.resolution_note)}</td>
        <td>${textValue(row.template_version || row.template_name || row.parser_version)}</td>
        <td>${textValue(row.confidence)}</td>
        <td><span class="quote-status-chip ${quoteStatusClass(row.resolution_status || row.status)}">${quoteStatusText(row.resolution_status || row.status)}</span></td>
        <td>${quoteExceptionActions(row)}</td>
      </tr>
    `).join('')
    : '<tr><td colspan="10" class="muted">暂无异常</td></tr>';
  bindQuoteExceptionButtons();
}

function bindQuoteExceptionButtons() {
  document.querySelectorAll('[data-quote-exception-ignore]').forEach((button) => {
    button.addEventListener('click', async () => {
      await fetch('/api/quotes/exceptions/resolve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          exception_id: Number(button.dataset.quoteExceptionIgnore),
          resolution_status: 'ignored',
          resolution_note: 'web ignored',
        }),
      });
      await loadQuotesData();
    });
  });
  document.querySelectorAll('[data-quote-exception-attach]').forEach((button) => {
    button.addEventListener('click', async () => {
      const response = await fetch('/api/quotes/exceptions/resolve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          exception_id: Number(button.dataset.quoteExceptionAttach),
          resolution_status: 'attached',
        }),
      });
      const payload = await response.json();
      if (payload.status && payload.status !== 'attached') {
        alert(`暂时不能自动附加：${payload.status}`);
      }
      await loadQuotesData();
    });
  });
  document.querySelectorAll('[data-quote-template-prefill]').forEach((button) => {
    button.addEventListener('click', () => {
      const row = allQuoteExceptions.find((item) => String(item.id) === String(button.dataset.quoteTemplatePrefill));
      if (row) fillQuoteProfileFromException(row);
    });
  });
  document.querySelectorAll('[data-quote-dictionary-prefill]').forEach((button) => {
    button.addEventListener('click', () => {
      const row = allQuoteExceptions.find((item) => String(item.id) === String(button.dataset.quoteDictionaryPrefill));
      if (row) openDictionaryPrefill(row);
    });
  });
  document.querySelectorAll('[data-quote-exception-annotate]').forEach((button) => {
    button.addEventListener('click', () => {
      const row = allQuoteExceptions.find((item) => String(item.id) === String(button.dataset.quoteExceptionAnnotate));
      if (row) openAnnotateModal(row);
    });
  });
}

function openAnnotateModal(row) {
  const modal = document.querySelector('#quote-annotate-modal');
  const form = document.querySelector('#quote-annotate-form');
  form.reset();
  form.exception_id.value = row.id;
  document.querySelector('#quote-annotate-source').textContent = row.source_line || '';
  updateAnnotatePreview();
  modal.setAttribute('aria-hidden', 'false');
}

function closeAnnotateModal() {
  document.querySelector('#quote-annotate-modal').setAttribute('aria-hidden', 'true');
}

function updateAnnotatePreview() {
  const form = document.querySelector('#quote-annotate-form');
  const source = document.querySelector('#quote-annotate-source').textContent;
  const fields = {
    card_type: form.card_type.value.trim(),
    country: form.country.value.trim(),
    amount: form.amount.value.trim(),
    form_factor: form.form_factor.value.trim(),
    price: form.price.value.trim(),
  };
  const parts = [];
  const items = Object.entries(fields).filter(([, v]) => v);
  items.sort((a, b) => {
    const ia = source.indexOf(a[1]);
    const ib = source.indexOf(b[1]);
    if (ia === -1 || ib === -1) return 0;
    return ia - ib;
  });
  let lastEnd = 0;
  for (const [name, value] of items) {
    const idx = source.indexOf(value, lastEnd);
    if (idx === -1) continue;
    if (idx > lastEnd) {
      parts.push(source.slice(lastEnd, idx));
    }
    parts.push('{' + name + '}');
    lastEnd = idx + value.length;
  }
  if (lastEnd < source.length) {
    const tail = source.slice(lastEnd);
    if (/\\([^)]*\\)\\s*$/.test(tail)) {
      parts.push('{restriction}');
    } else {
      parts.push(tail);
    }
  }
  document.querySelector('#quote-annotate-preview').textContent = parts.join('') || '（填写字段后预览）';
}

document.querySelector('#quote-annotate-close').addEventListener('click', closeAnnotateModal);
document.querySelector('#quote-annotate-cancel').addEventListener('click', closeAnnotateModal);
document.querySelector('#quote-annotate-form').addEventListener('input', updateAnnotatePreview);

document.querySelector('#quote-annotate-submit').addEventListener('click', async () => {
  const form = document.querySelector('#quote-annotate-form');
  const fields = {};
  if (form.card_type.value.trim()) fields.card_type = form.card_type.value.trim();
  if (form.country.value.trim()) fields.country = form.country.value.trim();
  if (form.amount.value.trim()) fields.amount = form.amount.value.trim();
  if (form.form_factor.value.trim()) fields.form_factor = form.form_factor.value.trim();
  if (form.price.value.trim()) fields.price = form.price.value.trim();
  if (Object.keys(fields).length === 0) {
    alert('至少填写一个字段');
    return;
  }
  const response = await fetch('/api/quotes/exceptions/resolve', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      exception_id: Number(form.exception_id.value),
      resolution_status: 'annotate',
      fields: fields,
    }),
  });
  const payload = await response.json();
  if (payload.error) {
    alert(`标注失败：${payload.error}`);
    return;
  }
  closeAnnotateModal();
  await loadQuotesData();
});

function sourcePlatform(row) {
  if (row.platform) return row.platform;
  const source = String(row.source_group_key || row.group_key || '');
  return source.includes(':') ? source.split(':', 1)[0] : 'whatsapp';
}

function fillQuoteProfileFromException(row) {
  const form = document.querySelector('#quote-profile-form');
  const existing = allQuoteProfiles.find((item) =>
    String(item.platform || 'whatsapp') === sourcePlatform(row)
    && String(item.chat_id || '') === String(row.chat_id || '')
  );
  form.platform.value = existing?.platform || sourcePlatform(row);
  form.chat_id.value = existing?.chat_id || row.chat_id || '';
  form.chat_name.value = existing?.chat_name || row.chat_name || row.source_group_name || row.chat_id || '';
  form.default_card_type.value = existing?.default_card_type || 'Apple';
  form.default_country_or_currency.value = existing?.default_country_or_currency || 'USD';
  form.default_form_factor.value = existing?.default_form_factor || '横白';
  form.default_multiplier.value = existing?.default_multiplier || '';
  form.parser_template.value = existing?.parser_template || 'sectioned_group_sheet';
  form.stale_after_minutes.value = existing?.stale_after_minutes || '30';
  form.template_config.value = existing?.template_config || '';
  document.querySelector('#quote-profile-prefill-status').textContent =
    `已从异常填充：${row.chat_name || row.chat_id || '未知群'} / ${row.chat_id || ''} / ${row.source_line || ''}`;
  document.querySelector('#quote-profile-panel').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function guessDictionaryAlias(row) {
  const source = String(row.source_line || '').trim();
  const beforePrice = source.split(/[0-9=：:]/, 1)[0].trim();
  return beforePrice.replace(/[【】\\[\\]#（）()，,、]/g, '').trim() || source;
}

function openDictionaryPrefill(row) {
  const params = new URLSearchParams({
    category: String(row.reason || '').includes('card') ? 'card_type' : 'country_currency',
    alias: guessDictionaryAlias(row),
    scope_platform: sourcePlatform(row),
    scope_chat_id: row.chat_id || '',
    note: `${row.chat_name || ''} ${row.source_line || ''}`.trim(),
  });
  window.location.href = `/quote-dictionary?${params.toString()}`;
}

async function loadQuotesData() {
  const [boardResponse, exceptionResponse, profileResponse, inquiryResponse] = await Promise.all([
    fetch('/api/quotes/board'),
    fetch('/api/quotes/exceptions'),
    fetch('/api/quotes/group-profiles'),
    fetch('/api/quotes/inquiries'),
  ]);
  const boardPayload = await boardResponse.json();
  const exceptionPayload = await exceptionResponse.json();
  const profilePayload = await profileResponse.json();
  const inquiryPayload = await inquiryResponse.json();
  allQuoteRows = Array.isArray(boardPayload.rows) ? boardPayload.rows : [];
  allQuoteExceptions = Array.isArray(exceptionPayload.rows) ? exceptionPayload.rows : [];
  renderQuoteBoard(allQuoteRows);
  renderQuoteExceptions(allQuoteExceptions);
  renderQuoteProfiles(Array.isArray(profilePayload.rows) ? profilePayload.rows : []);
  renderQuoteInquiries(Array.isArray(inquiryPayload.rows) ? inquiryPayload.rows : []);
}

function syncQuoteUrl() {
  const form = document.querySelector('#quote-filter-form');
  const params = new URLSearchParams(new FormData(form));
  Array.from(params.entries()).forEach(([key, value]) => {
    if (!String(value || '').trim()) {
      params.delete(key);
    }
  });
  const query = params.toString();
  history.replaceState({}, '', query ? `/quotes?${query}` : '/quotes');
}

document.querySelector('#quote-filter-form').addEventListener('submit', (event) => {
  event.preventDefault();
  syncQuoteUrl();
  renderQuoteBoard(allQuoteRows);
});

document.querySelector('#quote-filter-form').addEventListener('input', () => {
  syncQuoteUrl();
  renderQuoteBoard(allQuoteRows);
});

document.querySelector('#quote-filter-clear').addEventListener('click', () => {
  document.querySelector('#quote-filter-form').reset();
  syncQuoteUrl();
  renderQuoteBoard(allQuoteRows);
});

document.querySelector('#quote-refresh-btn').addEventListener('click', async () => {
  await loadQuotesData();
});

document.querySelector('#quote-profile-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(event.currentTarget).entries());
  await fetch('/api/quotes/group-profiles', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  await loadQuotesData();
});

document.querySelector('#quote-profile-clear').addEventListener('click', () => {
  document.querySelector('#quote-profile-form').reset();
  document.querySelector('#quote-profile-prefill-status').textContent = '可从异常区一键填充群模板。';
});

document.querySelector('#quote-inquiry-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(event.currentTarget).entries());
  await fetch('/api/quotes/inquiries', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  event.currentTarget.reset();
  await loadQuotesData();
});

document.querySelector('#quote-ranking-close').addEventListener('click', closeQuoteRankingModal);
document.querySelector('#quote-ranking-modal').addEventListener('click', (event) => {
  if (event.target === event.currentTarget) {
    closeQuoteRankingModal();
  }
});

const quoteQuery = new URLSearchParams(window.location.search);
const quoteFieldIds = {
  search: 'quote-search',
  card_type: 'quote-card-type',
  country_or_currency: 'quote-country',
  source_group_key: 'quote-source-group',
  quote_status: 'quote-status',
  form_factor: 'quote-form-factor',
};
for (const [key, id] of Object.entries(quoteFieldIds)) {
  const node = document.querySelector(`#${id}`);
  const value = quoteQuery.get(key);
  if (node && value) {
    node.value = value;
  }
}
loadQuotesData();
setInterval(() => {
  loadQuotesData().catch(() => {});
}, 60000);
"""
    return _render_layout(
        title="报价墙",
        subtitle="先看当前同卡最高价，再下钻到来源群、条件和异常。",
        active_path="/quotes",
        body=body,
        script=script,
    )


def render_quote_dictionary_page() -> str:
    body = """
<section class="panel stack">
  <div class="toolbar">
    <div>
      <h2>报价字典</h2>
      <div class="muted">维护国家/币种、卡种和形态别名；群级别名优先于全局别名。</div>
    </div>
    <label>
      <span class="muted">类别筛选</span>
      <select id="dict-filter-category">
        <option value="">全部</option>
        <option value="country_currency">国家/币种</option>
        <option value="card_type">卡种</option>
        <option value="form_factor">形态</option>
      </select>
    </label>
  </div>
  <div class="muted">
    使用说明：1) 表格会显示“内置+自定义”映射。2) 点“编辑/复制到表单”可回填。3) 只有“自定义”支持停用；内置项请用同名自定义覆盖。
  </div>
  <form id="quote-dictionary-form" class="quote-filter-grid">
    <select name="category" id="dict-category" required>
      <option value="country_currency">国家/币种</option>
      <option value="card_type">卡种</option>
      <option value="form_factor">形态</option>
    </select>
    <input name="alias" id="dict-alias" placeholder="别名，如 香港 / iTunes / 白卡图" required />
    <input name="canonical_value" id="dict-canonical" placeholder="标准值，如 HKD / Apple / 横白" required />
    <input name="scope_platform" id="dict-platform" placeholder="平台，可空，如 whatsapp" />
    <input name="scope_chat_id" id="dict-chat-id" placeholder="群ID，可空；填了表示仅该群生效" />
    <input name="note" id="dict-note" placeholder="备注，可空" />
    <button type="submit">保存别名</button>
    <button type="button" id="dict-clear">清空</button>
  </form>
  <div class="muted" id="dict-prefill-status">修改会要求输入管理口令。</div>
  <div class="table-wrap">
    <table id="quote-dictionary-table" class="quote-table">
      <thead>
        <tr><th>类别</th><th>别名</th><th>你输入</th><th>内部标准值</th><th>范围</th><th>来源</th><th>状态</th><th>备注</th><th>更新时间</th><th>操作</th></tr>
      </thead>
      <tbody><tr><td colspan="10" class="muted">加载中</td></tr></tbody>
    </table>
  </div>
</section>
"""
    script = r"""
const categoryText = {
  country_currency: '国家/币种',
  card_type: '卡种',
  form_factor: '形态',
};
let dictionaryRows = [];

function textValue(value) {
  const text = String(value ?? '').trim();
  return text || '—';
}

function formatTime(value) {
  const text = String(value || '').trim();
  if (!text) return '—';
  const normalized = text.includes('T') ? text : text.replace(' ', 'T');
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) return text;
  return date.toLocaleString('zh-CN', { hour12: false });
}

function renderDictionary(rows) {
  dictionaryRows = rows || [];
  const selectedCategory = document.querySelector('#dict-filter-category')?.value || '';
  const visibleRows = selectedCategory
    ? dictionaryRows.filter((row) => String(row.category || '') === selectedCategory)
    : dictionaryRows;
  const customCount = dictionaryRows.filter((row) => row.source === 'custom').length;
  const builtinCount = dictionaryRows.filter((row) => row.source === 'builtin').length;
  document.querySelector('#dict-prefill-status').textContent = `已加载 ${dictionaryRows.length} 条映射（自定义 ${customCount}，内置 ${builtinCount}）；当前显示 ${visibleRows.length} 条。修改会要求输入管理口令。`;
  document.querySelector('#quote-dictionary-table tbody').innerHTML = visibleRows.length
    ? visibleRows.map((row) => `
      <tr>
        <td>${categoryText[row.category] || textValue(row.category)}</td>
        <td>${textValue(row.alias)}</td>
        <td>${textValue(row.canonical_input || row.canonical_value)}</td>
        <td>${textValue(row.canonical_value)}</td>
        <td>${row.scope_chat_id ? `${textValue(row.scope_platform)} / ${textValue(row.scope_chat_id)}` : '全局'}</td>
        <td>${row.source === 'builtin' ? '内置' : '自定义'}</td>
        <td>${Number(row.enabled) ? '启用' : '停用'}</td>
        <td>${textValue(row.note)}</td>
        <td>${formatTime(row.updated_at || row.created_at)}</td>
        <td>${row.editable ? `<button type="button" data-dict-edit="${row.id}">编辑</button> ${Number(row.enabled) ? `<button type="button" data-dict-disable="${row.id}">停用</button>` : ''}` : `<button type="button" data-dict-edit="${row.id}">复制到表单</button>`}</td>
      </tr>
    `).join('')
    : '<tr><td colspan="10" class="muted">暂无字典别名</td></tr>';
  bindDictionaryActions();
}

async function loadDictionary() {
  const category = document.querySelector('#dict-filter-category')?.value || '';
  const params = new URLSearchParams({ include_builtin: '1' });
  if (category) params.set('category', category);
  const response = await fetch(`/api/quotes/dictionary?${params.toString()}`);
  const payload = await response.json();
  renderDictionary(Array.isArray(payload.rows) ? payload.rows : []);
}

function fillDictionaryForm(row) {
  const form = document.querySelector('#quote-dictionary-form');
  form.category.value = row.category || 'country_currency';
  form.alias.value = row.alias || '';
  form.canonical_value.value = row.canonical_input || row.canonical_value || '';
  form.scope_platform.value = row.scope_platform || '';
  form.scope_chat_id.value = row.scope_chat_id || '';
  form.note.value = row.note || '';
}

function bindDictionaryActions() {
  document.querySelectorAll('[data-dict-edit]').forEach((button) => {
    button.addEventListener('click', () => {
      const row = dictionaryRows.find((item) => String(item.id) === String(button.dataset.dictEdit));
      if (row) fillDictionaryForm(row);
    });
  });
  document.querySelectorAll('[data-dict-disable]').forEach((button) => {
    button.addEventListener('click', async () => {
      const adminPassword = window.prompt('请输入管理口令以停用该别名');
      if (!adminPassword) return;
      await fetch('/api/quotes/dictionary/disable', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: Number(button.dataset.dictDisable), admin_password: adminPassword }),
      });
      await loadDictionary();
    });
  });
}

document.querySelector('#quote-dictionary-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(event.currentTarget).entries());
  payload.canonical_input = String(payload.canonical_value || '').trim();
  const adminPassword = window.prompt('请输入管理口令以保存字典');
  if (!adminPassword) return;
  payload.admin_password = adminPassword;
  const response = await fetch('/api/quotes/dictionary', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const result = await response.json();
  if (!response.ok) {
    alert(result.error || '保存失败');
    return;
  }
  await loadDictionary();
});

document.querySelector('#dict-clear').addEventListener('click', () => {
  document.querySelector('#quote-dictionary-form').reset();
});
document.querySelector('#dict-filter-category').addEventListener('change', () => {
  loadDictionary();
});

const query = new URLSearchParams(window.location.search);
const prefill = {
  category: query.get('category') || '',
  alias: query.get('alias') || '',
  canonical_value: query.get('canonical_value') || '',
  scope_platform: query.get('scope_platform') || '',
  scope_chat_id: query.get('scope_chat_id') || '',
  note: query.get('note') || '',
};
if (Object.values(prefill).some(Boolean)) {
  fillDictionaryForm(prefill);
  if (prefill.category) {
    document.querySelector('#dict-filter-category').value = prefill.category;
  }
  document.querySelector('#dict-prefill-status').textContent = '已从异常区带入字典草稿，确认标准值后输入管理口令保存。';
}
loadDictionary();
"""
    return _render_layout(
        title="报价字典",
        subtitle="把群里的叫法映射到标准卡种、币种和形态。",
        active_path="/quote-dictionary",
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
  <form id="close-period-form">
    <input name="closed_by" placeholder="结账人备注" required />
    <button type="submit">一键结账</button>
  </form>
  <div id="close-period-status" class="muted">直接调用后端关账服务，口径等同 `/alljs`；本次实际参与结账的群会各自收到一条结账回执。</div>
  <form id="group-broadcast-form">
    <input name="created_by" placeholder="群发人备注" required />
    <input name="group_num" type="number" min="0" max="9" step="1" placeholder="分组号，如 1" required />
    <textarea class="full" name="message" placeholder="群发内容，等同 `/diy 1 自定义内容` 里的消息正文" required></textarea>
    <button type="submit">群发到分组</button>
  </form>
  <div id="group-broadcast-status" class="muted">Web 群发会进入统一出站队列，由各平台适配器依次投递到该分组下的所有群；“群发人备注”只用于审计记录。</div>
  <div class="cards">
    <article class="card">
      <div class="label" id="workbench-profit-label">账期利润</div>
      <div class="value" id="workbench-profit">0.00</div>
    </article>
    <article class="card">
      <div class="label" id="workbench-customer-label">账期客户卡金额</div>
      <div class="value" id="workbench-customer-amount">0.00</div>
    </article>
    <article class="card">
      <div class="label" id="workbench-vendor-label">账期供应商卡金额</div>
      <div class="value" id="workbench-vendor-amount">0.00</div>
    </article>
    <article class="card">
      <div class="label">群数量</div>
      <div class="value" id="workbench-groups">0</div>
    </article>
    <article class="card">
      <div class="label">客户交易</div>
      <div class="value" id="workbench-customer-transactions">0</div>
    </article>
    <article class="card">
      <div class="label">供应商交易</div>
      <div class="value" id="workbench-vendor-transactions">0</div>
    </article>
  </div>
</section>
<section class="panel">
  <div class="toolbar">
    <div>
      <h2 id="workbench-role-card-title">账期客户/供应商卡统计</h2>
      <div class="muted">利润 = 客户正数金额 + 供应商负数金额。客户余额和供应商欠款继续体现在群快照，不直接并入利润。</div>
    </div>
  </div>
  <div class="subgrid">
    <section class="subpanel">
      <h3>客户侧</h3>
      <div class="muted" id="workbench-customer-summary">加载中</div>
      <div class="table-wrap">
        <table id="workbench-customer-cards-table">
          <thead>
            <tr><th>卡种</th><th>刀数</th><th>金额</th><th>差额</th><th>利润</th></tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </section>
    <section class="subpanel">
      <h3>供应商侧</h3>
      <div class="muted" id="workbench-vendor-summary">加载中</div>
      <div class="table-wrap">
        <table id="workbench-vendor-cards-table">
          <thead>
            <tr><th>卡种</th><th>刀数</th><th>金额</th><th>利润</th></tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </section>
  </div>
</section>
<section class="panel">
  <h2>群快照</h2>
  <div class="table-wrap">
    <table id="workbench-groups-table">
      <thead>
        <tr><th>群名</th><th>角色</th><th>期初</th><th>收款</th><th>使用</th><th>期末</th><th>刀数</th><th>交易笔数</th></tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>
</section>
<section class="panel">
  <h2>卡种统计</h2>
  <div class="table-wrap">
    <table id="workbench-cards-table">
      <thead>
        <tr><th>卡种</th><th>角色</th><th>刀数</th><th>人民币金额</th></tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>
</section>
<section class="panel">
  <div class="toolbar">
    <div>
      <h2>当前实时窗口</h2>
      <div class="muted" id="workbench-live-range">显示最近一次结算之后到现在的实时交易，用于本轮结算前回查。</div>
    </div>
  </div>
  <div class="table-wrap">
    <table id="workbench-transactions-table">
      <thead>
        <tr><th>平台</th><th>群</th><th>角色</th><th>发送人</th><th>消息ID</th><th>金额</th><th>分类</th><th>汇率</th><th>人民币</th><th>刀数</th><th>原始文本</th><th>时间</th><th>状态</th><th>操作</th></tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>
</section>
<section class="panel stack">
  <div>
    <h2>治理操作</h2>
    <div class="muted">治理动作跟随上方实时窗口中的当前交易。交易修改直接落在原始账单上，组合管理继续保留在这里。</div>
  </div>
  <div class="subgrid">
    <section class="subpanel">
      <h3>交易修改</h3>
      <p class="muted">先在上方实时窗口选择一条交易。这里只修改单笔账单字段，提交前会二次确认，并记录修改人、修改时间和修改痕迹。</p>
      <form id="transaction-edit-form">
        <input type="hidden" name="transaction_id" id="transaction-edit-id" />
        <input id="transaction-edit-platform" placeholder="平台" readonly title="只读：来自当前选中的实时交易" />
        <input id="transaction-edit-chat-name" placeholder="群" readonly title="只读：来自当前选中的实时交易" />
        <input id="transaction-edit-role" placeholder="角色" readonly title="只读：角色来自群映射，不在这里单独改" />
        <input id="transaction-edit-message-id" placeholder="消息ID" readonly title="只读：用于确认你选中的原始消息" />
        <input name="sender_name" id="transaction-edit-sender-name" placeholder="发送人" required title="可改：当前账单的发送人展示名" />
        <input name="amount" id="transaction-edit-amount" placeholder="金额" required title="可改：原始金额，保持和机器人记账口径一致" />
        <input name="category" id="transaction-edit-category" placeholder="分类" required title="可改：如 xb、rmb 等分类" />
        <input name="rate" id="transaction-edit-rate" placeholder="汇率" title="可改：没有汇率时可留空" />
        <input name="rmb_value" id="transaction-edit-rmb-value" placeholder="人民币" required title="可改：后台原始人民币值。客户群保持原始负数，供应商按原始符号录入。" />
        <input name="usd_amount" id="transaction-edit-usd-amount" placeholder="刀数" title="可改：若为空，系统仍会按金额兜底显示" />
        <input name="edited_by" id="transaction-edit-edited-by" placeholder="修改人（操作人）" required title="必填：记录这次修改是谁做的" />
        <textarea class="full" name="note" id="transaction-edit-note" placeholder="修改说明（必填，记录原因和依据）" required></textarea>
        <button type="submit" id="transaction-edit-submit-btn">提交修改</button>
      </form>
      <div class="table-note muted" id="transaction-edit-hint">请先从上方实时窗口选择一条交易。</div>
    </section>
    <section class="subpanel">
      <h3>组合管理</h3>
      <div class="table-wrap">
        <table id="combos-table">
          <thead>
            <tr><th>名称</th><th>包含分组</th><th>群数量</th><th>当前余额</th></tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
      <div class="table-note muted">组合是治理视图，不再占首页首屏。</div>
      <form id="combo-form" style="margin-top: 14px;">
        <input name="name" placeholder="组合名称，如 客户总览" required />
        <input name="group_numbers" placeholder="分组号，逗号分隔，如 5,7,8" required />
        <input name="created_by" placeholder="创建人" required />
        <input name="note" placeholder="备注" />
        <button type="submit">保存组合</button>
      </form>
    </section>
  </div>
  <div id="workbench-form-status" class="muted"></div>
</section>
"""
    script = """
function money(value) {
  return Number(value || 0).toFixed(2);
}

function compactNumber(value) {
  if (value === null || value === undefined || value === '') {
    return '';
  }
  return Number(value).toFixed(2).replace(/\\.00$/, '');
}

function rateText(value) {
  if (value === null || value === undefined || value === '') {
    return '—';
  }
  return compactNumber(value);
}

function statusChip(status) {
  const normalized = status === 'settled' ? 'settled' : 'unsettled';
  const label = normalized === 'settled' ? '结算' : '实时';
  return `<span class="status-chip ${normalized}">${label}</span>`;
}

function roleText(role) {
  if (role === 'customer') return '客户';
  if (role === 'vendor') return '供应商';
  if (role === 'internal') return '内部';
  return '未归属';
}

function roleSourceText(source) {
  if (source === 'manual') return '手工指定';
  if (source === 'group_num') return '组号映射';
  return '未映射';
}

function roleCardSummaryText(block) {
  return `合计 ${money(block.total_usd_amount)} 刀 / ${money(block.total_display_rmb_amount ?? block.total_rmb_amount)} 元`;
}

function signedMoney(value) {
  const number = Number(value || 0);
  return `${number > 0 ? '+' : ''}${money(number)}`;
}

function diffClass(value) {
  return Number(value || 0) === 0 ? 'diff-safe' : 'diff-highlight';
}

function buildCardRowMap(rows) {
  const map = {};
  for (const row of (rows || [])) {
    const cardType = String(row.card_type || '').trim();
    if (!cardType) continue;
    map[cardType] = {
      card_type: cardType,
      usd_amount: Number(row.usd_amount ?? 0),
      rmb_amount: Number(row.rmb_amount ?? 0),
      display_rmb_amount: Number(row.display_rmb_amount ?? row.rmb_amount ?? 0),
    };
  }
  return map;
}

function alignRoleCardRows(customerRows, vendorRows) {
  const customerMap = buildCardRowMap(customerRows);
  const vendorMap = buildCardRowMap(vendorRows);
  const allCardTypes = Array.from(new Set([
    ...Object.keys(customerMap),
    ...Object.keys(vendorMap),
  ])).sort((a, b) => a.localeCompare(b, 'en', { sensitivity: 'base' }));

  const zeroRowFor = (cardType) => ({
    card_type: cardType,
    usd_amount: 0,
    rmb_amount: 0,
    display_rmb_amount: 0,
  });

  return {
    customerRows: allCardTypes.map((cardType) => customerMap[cardType] || zeroRowFor(cardType)),
    vendorRows: allCardTypes.map((cardType) => vendorMap[cardType] || zeroRowFor(cardType)),
  };
}

function renderRoleCardTable(tableId, rows, emptyText, options = {}) {
  const showProfit = Boolean(options.showProfit);
  const showDiff = Boolean(options.showDiff);
  const profitByCardType = options.profitByCardType || {};
  const diffKnifeByCardType = options.diffKnifeByCardType || {};
  const colspan = 3 + (showProfit ? 1 : 0) + (showDiff ? 2 : 0);
  document.querySelector(`${tableId} tbody`).innerHTML = rows.length
    ? rows.map((row) => {
      const amount = Number(row.display_rmb_amount ?? row.rmb_amount ?? 0);
      const profit = Number(profitByCardType[row.card_type] ?? 0);
      const diffKnife = Number(diffKnifeByCardType[row.card_type] ?? 0);
      return `
      <tr>
        <td>${row.card_type}</td>
        <td>${money(row.usd_amount)}</td>
        <td>${money(amount)}</td>
        ${showProfit ? `<td>${money(profit)}</td>` : ''}
        ${showDiff ? `<td><span class="${diffClass(diffKnife)}">${signedMoney(diffKnife)}</span></td><td>${signedMoney(profit)}</td>` : ''}
      </tr>
    `;
    }).join('')
    : `<tr><td colspan="${colspan}" class="muted">${emptyText}</td></tr>`;
}

function setWorkbenchStatus(text, isError = false, targetId = 'workbench-form-status') {
  const node = document.querySelector(`#${targetId}`);
  node.className = isError ? 'error' : 'muted';
  node.textContent = text;
}

function formatEditTrail(row) {
  if (!row || !row.is_edited) {
    return '';
  }
  const meta = [];
  if (row.edited_at) {
    meta.push(row.edited_at);
  }
  if (row.edited_by) {
    meta.push(row.edited_by);
  }
  return `<div class="table-note muted">已修改${meta.length ? ` · ${meta.join(' · ')}` : ''}</div>`;
}

function setTransactionEditHint(text) {
  const hint = document.querySelector('#transaction-edit-hint');
  if (hint) {
    hint.textContent = text;
  }
}

function clearTransactionEditForm(hintText) {
  document.querySelector('#transaction-edit-form').reset();
  document.querySelector('#transaction-edit-id').value = '';
  document.querySelector('#transaction-edit-platform').value = '';
  document.querySelector('#transaction-edit-chat-name').value = '';
  document.querySelector('#transaction-edit-role').value = '';
  document.querySelector('#transaction-edit-message-id').value = '';
  setTransactionEditHint(hintText);
}

function fillTransactionEditForm(row) {
  const editorNode = document.querySelector('#transaction-edit-edited-by');
  const preservedEditor = editorNode.value;
  document.querySelector('#transaction-edit-id').value = String(row.id);
  document.querySelector('#transaction-edit-platform').value = row.platform || '';
  document.querySelector('#transaction-edit-chat-name').value = row.chat_name || '';
  document.querySelector('#transaction-edit-role').value = roleText(row.business_role);
  document.querySelector('#transaction-edit-message-id').value = row.message_id || '';
  document.querySelector('#transaction-edit-sender-name').value = row.sender_name || '';
  document.querySelector('#transaction-edit-amount').value = compactNumber(row.amount ?? 0);
  document.querySelector('#transaction-edit-category').value = row.category || '';
  document.querySelector('#transaction-edit-rate').value = row.rate === null || row.rate === undefined ? '' : compactNumber(row.rate);
  document.querySelector('#transaction-edit-rmb-value').value = compactNumber(row.rmb_value ?? 0);
  document.querySelector('#transaction-edit-usd-amount').value = row.usd_amount === null || row.usd_amount === undefined ? '' : compactNumber(row.usd_amount);
  document.querySelector('#transaction-edit-note').value = '';
  editorNode.value = preservedEditor;
  setTransactionEditHint(
    `当前选中：${row.chat_name || '未命名群'} / ${row.message_id || `交易ID ${row.id}`}。提交后会保留修改痕迹和时间。`
  );
}

function updatePeriodOptions(periods, selectedId) {
  const select = document.querySelector('#period-select');
  const realtimeOption = '<option value="realtime">实时账期</option>';
  const settledOptions = periods.map((period) => `
    <option value="${period.id}">${period.id} · ${period.closed_at}</option>
  `).join('');
  select.innerHTML = `${realtimeOption}${settledOptions}`;
  select.value = selectedId ? String(selectedId) : 'realtime';
}

let currentPeriodId = null;
let currentWorkbenchSelection = 'realtime';
let currentEditingTransactionId = null;
let currentTransactionsById = new Map();

async function loadWorkbench(periodId) {
  const normalizedPeriodId = String(periodId || 'realtime').toLowerCase();
  const isRealtimeRequest = normalizedPeriodId === 'realtime';
  currentWorkbenchSelection = isRealtimeRequest ? 'realtime' : String(periodId);
  const params = new URLSearchParams();
  params.set('period_id', isRealtimeRequest ? 'realtime' : String(periodId));
  const response = await fetch(`/api/workbench?${params.toString()}`);
  const data = await response.json();
  const selected = data.selected_period;
  const summary = data.summary || {};
  const liveWindow = data.live_window || {};
  const isRealtimeView = isRealtimeRequest || !selected;

  updatePeriodOptions(data.periods || [], isRealtimeView ? 'realtime' : (selected ? selected.id : 'realtime'));
  if (!isRealtimeView && selected) {
    currentPeriodId = selected.id;
    document.querySelector('#workbench-range').textContent =
      `${selected.start_at} 至 ${selected.end_at}，关闭于 ${selected.closed_at}`;
    document.querySelector('#workbench-profit-label').textContent = '账期利润';
    document.querySelector('#workbench-customer-label').textContent = '账期客户卡金额';
    document.querySelector('#workbench-vendor-label').textContent = '账期供应商卡金额';
    document.querySelector('#workbench-role-card-title').textContent = '账期客户/供应商卡统计';
    history.replaceState({}, '', `/workbench?period_id=${selected.id}`);
    setTransactionEditHint('当前展示结算账期摘要；交易修改仍作用于上方实时窗口中的实时交易。');
  } else {
    currentPeriodId = null;
    document.querySelector('#workbench-range').textContent = (data.periods || []).length
      ? '当前显示实时工作区（基于最近一次结算后的实时交易）'
      : '暂无结算账期，当前显示实时工作区';
    document.querySelector('#workbench-profit-label').textContent = '当前实时预估利润';
    document.querySelector('#workbench-customer-label').textContent = '当前客户卡金额';
    document.querySelector('#workbench-vendor-label').textContent = '当前供应商卡金额';
    document.querySelector('#workbench-role-card-title').textContent = '当前客户/供应商卡统计';
    history.replaceState({}, '', '/workbench?period_id=realtime');
    setTransactionEditHint('当前为实时视图：请从上方实时窗口选择一条交易后再修改。');
  }

  document.querySelector('#workbench-profit').textContent = money(summary.profit);
  document.querySelector('#workbench-customer-amount').textContent = money(summary.customer_card_rmb_amount);
  document.querySelector('#workbench-vendor-amount').textContent = money(summary.vendor_card_rmb_amount);
  document.querySelector('#workbench-groups').textContent = String(summary.group_count || 0);
  const transactions = data.transactions || [];
  const customerTransactionCount = Number(
    liveWindow.customer_transaction_count ?? transactions.filter((row) => row.business_role === 'customer').length
  );
  const vendorTransactionCount = Number(
    liveWindow.vendor_transaction_count ?? transactions.filter((row) => row.business_role === 'vendor').length
  );
  document.querySelector('#workbench-customer-transactions').textContent = String(customerTransactionCount);
  document.querySelector('#workbench-vendor-transactions').textContent = String(vendorTransactionCount);
  document.querySelector('#workbench-live-range').textContent =
    liveWindow.label || '显示最近一次结算之后到现在的实时交易，用于本轮结算前回查。';
  const roleCardBreakdown = data.role_card_breakdown || {};
  const customerCards = roleCardBreakdown.customer || { rows: [], total_usd_amount: 0, total_rmb_amount: 0, total_unit_count: 0 };
  const vendorCards = roleCardBreakdown.vendor || { rows: [], total_usd_amount: 0, total_rmb_amount: 0, total_unit_count: 0 };
  const alignedRows = alignRoleCardRows(customerCards.rows || [], vendorCards.rows || []);
  const customerAmountByCardType = {};
  const customerKnifeByCardType = {};
  for (const row of alignedRows.customerRows) {
    customerAmountByCardType[row.card_type] = Number(row.display_rmb_amount ?? row.rmb_amount ?? 0);
    customerKnifeByCardType[row.card_type] = Number(row.usd_amount ?? 0);
  }
  const vendorAmountByCardType = {};
  const vendorKnifeByCardType = {};
  for (const row of alignedRows.vendorRows) {
    vendorAmountByCardType[row.card_type] = Number(row.display_rmb_amount ?? row.rmb_amount ?? 0);
    vendorKnifeByCardType[row.card_type] = Number(row.usd_amount ?? 0);
  }
  const customerDiffKnifeByCardType = {};
  const customerProfitByCardType = {};
  for (const row of alignedRows.customerRows) {
    const cardType = row.card_type;
    customerDiffKnifeByCardType[cardType] =
      Number(customerKnifeByCardType[cardType] ?? 0) - Number(vendorKnifeByCardType[cardType] ?? 0);
    customerProfitByCardType[cardType] =
      Number(customerAmountByCardType[cardType] ?? 0) - Number(vendorAmountByCardType[cardType] ?? 0);
  }
  const vendorProfitByCardType = {};
  for (const row of alignedRows.vendorRows) {
    const vendorAmount = Number(row.display_rmb_amount ?? row.rmb_amount ?? 0);
    const customerAmount = Number(customerAmountByCardType[row.card_type] ?? 0);
    vendorProfitByCardType[row.card_type] = customerAmount - vendorAmount;
  }
  document.querySelector('#workbench-customer-summary').textContent = roleCardSummaryText(customerCards);
  document.querySelector('#workbench-vendor-summary').textContent = roleCardSummaryText(vendorCards);
  renderRoleCardTable(
    '#workbench-customer-cards-table',
    alignedRows.customerRows,
    '当前口径下暂无客户卡统计',
    {
      showDiff: true,
      diffKnifeByCardType: customerDiffKnifeByCardType,
      profitByCardType: customerProfitByCardType,
    }
  );
  renderRoleCardTable(
    '#workbench-vendor-cards-table',
    alignedRows.vendorRows,
    '当前口径下暂无供应商卡统计',
    { showProfit: true, profitByCardType: vendorProfitByCardType }
  );
  currentTransactionsById = new Map(transactions.map((row) => [String(row.id), row]));
  document.querySelector('#workbench-transactions-table tbody').innerHTML = transactions.length
    ? transactions.map((row) => `
      <tr>
        <td>${row.platform}</td>
        <td>${row.chat_name}</td>
        <td>${roleText(row.business_role)}</td>
        <td>${row.sender_name}</td>
        <td class="mono">${row.message_id || ''}</td>
        <td>${money(row.amount)}</td>
        <td>${row.category}</td>
        <td>${rateText(row.rate)}</td>
        <td>${money(row.display_rmb_amount ?? row.rmb_value)}</td>
        <td>${money(row.display_usd_amount)}</td>
        <td>${row.raw}</td>
        <td>${row.created_at}</td>
        <td>${statusChip(row.period_status)}${formatEditTrail(row)}</td>
        <td><button type="button" data-action="edit-transaction" data-transaction-id="${row.id}">修改</button></td>
      </tr>
    `).join('')
    : '<tr><td colspan="14" class="muted">当前实时窗口暂无交易</td></tr>';
  document.querySelectorAll('[data-action="edit-transaction"]').forEach((button) => {
    button.addEventListener('click', () => {
      const transactionId = String(button.getAttribute('data-transaction-id') || '');
      const row = currentTransactionsById.get(transactionId);
      if (!row) {
        setWorkbenchStatus('未找到要修改的交易，请刷新后重试。', true);
        return;
      }
      currentEditingTransactionId = transactionId;
      fillTransactionEditForm(row);
      setWorkbenchStatus(`已加载交易 ${row.message_id || row.id}，请确认字段后提交修改。`);
    });
  });
  if (currentEditingTransactionId && currentTransactionsById.has(currentEditingTransactionId)) {
    fillTransactionEditForm(currentTransactionsById.get(currentEditingTransactionId));
  } else {
    currentEditingTransactionId = null;
    clearTransactionEditForm(
      isRealtimeView
        ? '请先从上方实时窗口选择一条交易。'
        : '当前展示结算账期摘要；若要修改，请从上方实时窗口选择一条实时交易。'
    );
  }

  const visibleGroupRows = (data.group_rows || []).filter((row) => Number(row.transaction_count || 0) > 0);
  document.querySelector('#workbench-groups-table tbody').innerHTML = visibleGroupRows.length
    ? visibleGroupRows.map((row) => `
    <tr>
      <td>${row.chat_name}</td>
      <td>${row.business_role || ''}</td>
      <td>${money(row.opening_balance)}</td>
      <td>${money(row.income)}</td>
      <td>${money(row.expense)}</td>
      <td>${money(row.closing_balance)}</td>
      <td>${money(row.total_usd_amount)}</td>
      <td>${row.transaction_count}</td>
    </tr>
  `).join('')
    : '<tr><td colspan="8" class="muted">当前口径下暂无有交易的群快照</td></tr>';

  document.querySelector('#workbench-cards-table tbody').innerHTML = (data.card_stats || []).map((row) => `
    <tr>
      <td>${row.card_type}</td>
      <td>${roleText(row.business_role)}</td>
      <td>${money(row.usd_amount)}</td>
      <td>${money(row.display_rmb_amount ?? row.rmb_amount)}</td>
    </tr>
  `).join('');
}

async function loadCombinations() {
  const response = await fetch('/api/group-combinations');
  const data = await response.json();
  document.querySelector('#combos-table tbody').innerHTML = (data || []).length
    ? data.map((row) => `
      <tr>
        <td>${row.label}</td>
        <td>${(row.group_numbers || []).join('+')}</td>
        <td>${row.group_count}</td>
        <td>${money(row.current_balance)}</td>
      </tr>
    `).join('')
    : '<tr><td colspan="4" class="muted">暂无组合定义</td></tr>';
}

document.querySelector('#period-select').addEventListener('change', (event) => {
  loadWorkbench(event.currentTarget.value);
});

document.querySelector('#close-period-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = Object.fromEntries(new FormData(form).entries());
  if (!String(payload.closed_by || '').trim()) {
    setWorkbenchStatus('结账人不能为空。', true, 'close-period-status');
    return;
  }
  const confirmed = window.confirm('确认一键结账吗？这会按当前实时交易执行与 /alljs 相同的结账逻辑，并给本次参与结账的群补发各自的回执。');
  if (!confirmed) {
    setWorkbenchStatus('已取消一键结账。', false, 'close-period-status');
    return;
  }
  const response = await fetch('/api/accounting-periods/settle-all', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const result = await response.json();
  if (!response.ok) {
    setWorkbenchStatus(result.error || '一键结账失败', true, 'close-period-status');
    return;
  }
  if (!result.closed) {
    setWorkbenchStatus(result.message || '当前没有可结账的实时交易', false, 'close-period-status');
    return;
  }
  setWorkbenchStatus(
    `一键结账完成，账期 ID=${result.period_id}，已排队 ${result.queued_action_count} 条群回执。`,
    false,
    'close-period-status'
  );
  form.reset();
  await loadWorkbench(result.period_id);
});

document.querySelector('#group-broadcast-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = Object.fromEntries(new FormData(form).entries());
  payload.group_num = Number(payload.group_num || 0);
  if (!String(payload.created_by || '').trim()) {
    setWorkbenchStatus('群发人不能为空。', true, 'group-broadcast-status');
    return;
  }
  if (!String(payload.message || '').trim()) {
    setWorkbenchStatus('群发内容不能为空。', true, 'group-broadcast-status');
    return;
  }
  const confirmed = window.confirm(
    `确认群发到分组 ${payload.group_num} 吗？\\n这会把消息排进统一出站队列，由该分组下所有群依次接收。`
  );
  if (!confirmed) {
    setWorkbenchStatus('已取消群发。', false, 'group-broadcast-status');
    return;
  }
  const response = await fetch('/api/group-broadcasts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const result = await response.json();
  if (!response.ok) {
    setWorkbenchStatus(result.error || '群发排队失败', true, 'group-broadcast-status');
    return;
  }
  setWorkbenchStatus(
    `群发已排队：分组 ${result.group_num}，目标 ${result.target_count} 个群，动作 ${result.queued_action_count} 条。`,
    false,
    'group-broadcast-status'
  );
  form.reset();
});

document.querySelector('#transaction-edit-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = Object.fromEntries(new FormData(form).entries());
  if (!payload.transaction_id) {
    setWorkbenchStatus('请先从上方实时窗口选择一条交易。', true);
    return;
  }
  for (const key of ['sender_name', 'category', 'edited_by', 'note']) {
    if (!String(payload[key] || '').trim()) {
      setWorkbenchStatus('发送人、分类、修改人、修改说明不能为空。', true);
      return;
    }
  }
  payload.transaction_id = Number(payload.transaction_id);
  payload.amount = Number(payload.amount || 0);
  payload.rmb_value = Number(payload.rmb_value || 0);
  payload.rate = payload.rate === '' ? null : Number(payload.rate);
  payload.usd_amount = payload.usd_amount === '' ? null : Number(payload.usd_amount);
  const messageId = document.querySelector('#transaction-edit-message-id').value || `交易ID ${payload.transaction_id}`;
  const groupName = document.querySelector('#transaction-edit-chat-name').value || '未命名群';
  const confirmed = window.confirm(
    `确认修改这条实时交易吗？\n群：${groupName}\n消息：${messageId}\n提交后会记录修改人和修改时间。`
  );
  if (!confirmed) {
    setWorkbenchStatus('已取消修改。');
    return;
  }
  const response = await fetch('/api/transactions/update', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const result = await response.json();
  if (!response.ok) {
    setWorkbenchStatus(result.error || '提交修改失败', true);
    return;
  }
  currentEditingTransactionId = String(result.transaction_id);
  setWorkbenchStatus(`交易修改已保存，ID=${result.transaction_id}`);
  await loadWorkbench(currentWorkbenchSelection);
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
  if (!response.ok) {
    setWorkbenchStatus(result.error || '保存组合失败', true);
    return;
  }
  setWorkbenchStatus(`组合已保存，ID=${result.combination_id}`);
  form.reset();
  loadCombinations();
});

const initialPeriodId = new URLSearchParams(window.location.search).get('period_id') || 'realtime';
loadWorkbench(initialPeriodId);
loadCombinations();
"""
    return _render_layout(
        title="账期工作台",
        subtitle="工作台承接关账、对账和治理动作；先看账期摘要，再做结构化明细回查。",
        active_path="/workbench",
        body=body,
        script=script,
    )


def render_role_mapping_page() -> str:
    body = """
<section class="panel stack">
  <div class="toolbar">
    <div>
      <h2>角色映射总览</h2>
      <div class="muted" id="role-mapping-range">角色映射加载中</div>
    </div>
    <div class="muted">这里专门处理群角色归类。首页、工作台和历史页只消费映射结果，不再重复堆映射表。</div>
  </div>
  <div class="cards">
    <article class="card">
      <div class="label">客户群</div>
      <div class="value" id="role-customer-count">0</div>
    </article>
    <article class="card">
      <div class="label">供应商群</div>
      <div class="value" id="role-vendor-count">0</div>
    </article>
    <article class="card">
      <div class="label">内部群</div>
      <div class="value" id="role-internal-count">0</div>
    </article>
    <article class="card">
      <div class="label">未归属群</div>
      <div class="value" id="role-unassigned-count">0</div>
    </article>
  </div>
</section>
<section class="panel">
  <div class="subgrid">
    <section class="subpanel">
      <h3>组号默认映射</h3>
      <div class="table-wrap">
        <table id="role-rule-table">
          <thead>
            <tr><th>分组号</th><th>默认角色</th></tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </section>
    <section class="subpanel">
      <h3>别名归一化</h3>
      <div class="table-wrap">
        <table id="role-alias-table">
          <thead>
            <tr><th>归一化后角色</th><th>接受的输入</th></tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </section>
  </div>
</section>
<section class="panel stack">
  <div class="toolbar">
    <div>
      <h2>当前群角色映射</h2>
      <div class="muted">手工指定优先于组号默认映射。未归属群不会进入供应商/客户利润口径。</div>
    </div>
    <div class="toolbar-actions">
      <input id="role-current-search" type="search" placeholder="按群名 / 群 Key / 平台搜索；输入 2 5、2,5、2，5 可按多个分组号汇总" autocomplete="off" />
      <button type="button" class="inline-link" id="role-current-search-clear">清空搜索</button>
      <a class="inline-link" href="/workbench">回到账期工作台</a>
    </div>
  </div>
  <div class="muted" id="role-current-filter-summary">当前群统计加载中</div>
  <div class="table-wrap">
    <table id="role-current-table">
      <thead>
        <tr><th>群</th><th>平台</th><th>分组号</th><th>设置分组号</th><th>解析角色</th><th>来源</th><th>当前余额</th></tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>
  <div class="muted" id="role-mapping-status"></div>
</section>
"""
    script = """
function money(value) {
  return Number(value || 0).toFixed(2);
}

let allCurrentRows = [];

function groupNumOptions(currentGroupNum) {
  const selectedValue = currentGroupNum === null || currentGroupNum === undefined ? '' : String(currentGroupNum);
  const options = ['<option value="">请选择</option>'];
  for (let num = 0; num <= 9; num += 1) {
    const value = String(num);
    const selected = value === selectedValue ? 'selected' : '';
    options.push(`<option value="${value}" ${selected}>${value}</option>`);
  }
  return options.join('');
}

function setRoleMappingStatus(text, isError = false) {
  const node = document.querySelector('#role-mapping-status');
  node.className = isError ? 'error' : 'muted';
  node.textContent = text;
}

function roleText(role) {
  if (role === 'customer') return '客户';
  if (role === 'vendor') return '供应商';
  if (role === 'internal') return '内部';
  return '未归属';
}

function roleSourceText(source) {
  if (source === 'manual') return '手工指定';
  if (source === 'group_num') return '组号映射';
  return '未映射';
}

function parseGroupNumKeywords(rawKeyword) {
  const normalized = String(rawKeyword || '')
    .replace(/[\\u00A0\\u1680\\u2000-\\u200A\\u202F\\u205F\\u3000]/g, ' ')
    .trim();
  if (!normalized) {
    return null;
  }
  const parts = normalized
    .split(/[\\s,，、]+/)
    .map((item) => item.trim())
    .filter(Boolean);
  if (!parts.length || !parts.every((item) => /^\\d+$/.test(item))) {
    return null;
  }
  return [...new Set(parts.map((item) => Number(item)))];
}

function currentGroupMatchesKeyword(row, rawKeyword, keyword, groupNumKeywords) {
  if (!rawKeyword) {
    return true;
  }
  if (groupNumKeywords) {
    return row.group_num !== null && row.group_num !== undefined && groupNumKeywords.includes(Number(row.group_num));
  }
  return [
    row.chat_name,
    row.group_key,
    row.platform,
  ].some((value) => String(value || '').toLowerCase().includes(keyword));
}

function renderCurrentGroupRows(rows, keyword = '') {
  const emptyText = keyword ? '没有匹配的群角色映射' : '暂无群角色映射';
  document.querySelector('#role-current-table tbody').innerHTML = rows.length
    ? rows.map((row) => `
      <tr>
        <td>${row.chat_name}</td>
        <td>${row.platform}</td>
        <td>${row.group_num ?? '—'}</td>
        <td>
          <select class="group-num-select" data-group-key="${row.group_key}" data-chat-name="${row.chat_name}" data-current-group-num="${row.group_num ?? ''}">
            ${groupNumOptions(row.group_num)}
          </select>
        </td>
        <td>${roleText(row.business_role)}</td>
        <td>${roleSourceText(row.role_source)}</td>
        <td>${money(row.current_balance)}</td>
      </tr>
    `).join('')
    : `<tr><td colspan="7" class="muted">${emptyText}</td></tr>`;
}

function renderCurrentGroupSummary(rows, rawKeyword = '', groupNumKeywords = null) {
  const totalBalance = rows.reduce((sum, row) => sum + Number(row.current_balance || 0), 0);
  const summaryText = !rawKeyword
    ? `当前共 ${rows.length} 个群，当前余额合计 ${money(totalBalance)}。支持按群名、群 Key、平台模糊搜索；输入 2,3,4 这类数字列表时按多个分组号汇总。`
    : groupNumKeywords
      ? `已按分组号 ${groupNumKeywords.join('、')} 筛到 ${rows.length} 个群，当前余额合计 ${money(totalBalance)}。`
      : `已按群组关键字“${rawKeyword}”筛到 ${rows.length} 个群，当前余额合计 ${money(totalBalance)}。`;
  document.querySelector('#role-current-filter-summary').textContent = summaryText;
}

function applyCurrentGroupFilter() {
  const input = document.querySelector('#role-current-search');
  const rawKeyword = String(input.value || '').trim();
  const keyword = rawKeyword.toLowerCase();
  const groupNumKeywords = parseGroupNumKeywords(rawKeyword);
  const filteredRows = allCurrentRows.filter((row) => currentGroupMatchesKeyword(row, rawKeyword, keyword, groupNumKeywords));
  renderCurrentGroupRows(filteredRows, rawKeyword);
  renderCurrentGroupSummary(filteredRows, rawKeyword, groupNumKeywords);
}

async function loadRoleMapping() {
  const response = await fetch('/api/role-mapping');
  const data = await response.json();
  const summary = data.summary || {};
  const counts = summary.counts_by_role || {};

  document.querySelector('#role-customer-count').textContent = String(counts.customer || 0);
  document.querySelector('#role-vendor-count').textContent = String(counts.vendor || 0);
  document.querySelector('#role-internal-count').textContent = String(counts.internal || 0);
  document.querySelector('#role-unassigned-count').textContent = String(counts.unassigned || 0);
  document.querySelector('#role-mapping-range').textContent =
    `已解析 ${summary.resolved_group_count || 0} 个群，财务口径 ${summary.financial_group_count || 0} 个，当前财务余额 ${money(summary.financial_total_balance)}，当前实时预估利润 ${money(summary.current_estimated_profit)}。`;

  const mappingRules = data.mapping_rules || [];
  document.querySelector('#role-rule-table tbody').innerHTML = mappingRules.length
    ? mappingRules.map((row) => `
      <tr>
        <td>${(row.group_nums || []).join(', ')}</td>
        <td>${roleText(row.business_role)}</td>
      </tr>
    `).join('')
    : '<tr><td colspan="2" class="muted">暂无默认映射规则</td></tr>';

  const roleAliases = data.role_aliases || [];
  document.querySelector('#role-alias-table tbody').innerHTML = roleAliases.length
    ? roleAliases.map((row) => `
      <tr>
        <td>${roleText(row.business_role)}</td>
        <td>${(row.aliases || []).join(' / ')}</td>
      </tr>
    `).join('')
    : '<tr><td colspan="2" class="muted">暂无别名规则</td></tr>';

  allCurrentRows = data.current_groups || [];
  applyCurrentGroupFilter();
}

document.querySelector('#role-current-search').addEventListener('input', () => {
  applyCurrentGroupFilter();
});

document.querySelector('#role-current-search-clear').addEventListener('click', () => {
  const input = document.querySelector('#role-current-search');
  input.value = '';
  input.focus();
  applyCurrentGroupFilter();
});

document.querySelector('#role-current-table').addEventListener('change', async (event) => {
  const select = event.target.closest('.group-num-select');
  if (!select) {
    return;
  }
  const nextValue = String(select.value || '');
  const previousValue = String(select.dataset.currentGroupNum || '');
  if (!nextValue) {
    setRoleMappingStatus('请选择要绑定的分组号。', true);
    select.value = previousValue;
    return;
  }
  if (nextValue === previousValue) {
    return;
  }

  const groupKey = String(select.dataset.groupKey || '');
  const chatName = String(select.dataset.chatName || groupKey);
  const confirmed = window.confirm(`确认将「${chatName}」分组号从 ${previousValue || '未设置'} 改为 ${nextValue} 吗？`);
  if (!confirmed) {
    select.value = previousValue;
    return;
  }

  select.disabled = true;
  const groupNum = Number(nextValue);
  try {
    const response = await fetch('/api/role-mapping/group-num', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        group_key: groupKey,
        group_num: groupNum,
      }),
    });
    const result = await response.json();
    if (!response.ok) {
      setRoleMappingStatus(result.error || '写入分组号失败。', true);
      select.value = previousValue;
      return;
    }
    setRoleMappingStatus(`已写入分组号：${groupKey} -> ${groupNum}`);
    await loadRoleMapping();
  } catch (error) {
    setRoleMappingStatus(`写入分组号失败：${error}`, true);
    select.value = previousValue;
  } finally {
    select.disabled = false;
  }
});

loadRoleMapping();
"""
    return _render_layout(
        title="角色映射",
        subtitle="把群角色、组号规则和口语别名归一化集中到一个页面，先把口径看清，再去看利润和账期。",
        active_path="/role-mapping",
        body=body,
        script=script,
    )


def render_reconciliation_page() -> str:
    body = """
<section class="panel stack">
  <div class="toolbar">
    <div>
      <h2>财务对账中心</h2>
      <div class="muted" id="reconciliation-range">按当前口径加载逐笔台账</div>
    </div>
    <div class="toolbar-actions">
      <a class="inline-link" id="reconciliation-export-detail-link" href="/api/reconciliation/export?scope=realtime&export_mode=detail">导出逐笔明细 CSV</a>
      <a class="inline-link" id="reconciliation-export-summary-link" href="/api/reconciliation/export?scope=realtime&export_mode=summary">导出汇总 CSV</a>
    </div>
  </div>
  <div class="cards">
    <article class="card">
      <div class="label">未对账笔数</div>
      <div class="value" id="reconciliation-unreconciled">0</div>
    </article>
    <article class="card">
      <div class="label">汇率公式异常</div>
      <div class="value" id="reconciliation-rate-error">0</div>
    </article>
    <article class="card">
      <div class="label">缺失汇率</div>
      <div class="value" id="reconciliation-missing-rate">0</div>
    </article>
    <article class="card">
      <div class="label">已修改未复核</div>
      <div class="value" id="reconciliation-edited">0</div>
    </article>
  </div>
</section>
<section class="panel stack">
  <div class="toolbar">
    <div>
      <h2>筛选口径</h2>
      <div class="muted">支持实时、指定账期、日期区间三种口径；可先按组合或组号汇总，再下钻到具体群；导出会沿用当前筛选。</div>
    </div>
  </div>
  <form id="reconciliation-filter-form">
    <select name="scope" id="reconciliation-scope">
      <option value="realtime">实时窗口</option>
      <option value="period">指定账期</option>
      <option value="range">日期区间</option>
    </select>
    <select name="period_id" id="reconciliation-period"></select>
    <input type="date" name="start_date" id="reconciliation-start-date" />
    <input type="date" name="end_date" id="reconciliation-end-date" />
    <select name="business_role" id="reconciliation-business-role">
      <option value="">全部角色</option>
      <option value="customer">客户</option>
      <option value="vendor">供应商</option>
      <option value="internal">内部</option>
      <option value="unassigned">未归属</option>
    </select>
    <select name="combination_id" id="reconciliation-combination">
      <option value="">全部组合</option>
    </select>
    <select name="group_num" id="reconciliation-group-num">
      <option value="">全部组号</option>
    </select>
    <select name="group_key" id="reconciliation-group-key">
      <option value="">全部群</option>
    </select>
    <select name="card_type" id="reconciliation-card-type">
      <option value="">全部卡种</option>
    </select>
    <select name="edited" id="reconciliation-edited-filter">
      <option value="all">全部修改状态</option>
      <option value="yes">只看已修改</option>
      <option value="no">只看未修改</option>
    </select>
    <select name="issue_type" id="reconciliation-issue-type">
      <option value="">全部异常</option>
      <option value="pending_reconciliation">未对账</option>
      <option value="rate_formula_error">汇率公式异常</option>
      <option value="missing_rate">缺失汇率</option>
      <option value="edited_unreviewed">已修改未复核</option>
    </select>
    <button type="submit">刷新台账</button>
  </form>
  <div class="muted" id="reconciliation-filter-status">默认先看最近一次结账之后的实时窗口，可按组合或组号汇总。</div>
</section>
<section class="panel stack">
  <div class="toolbar">
    <div>
      <h2>逐笔财务调账</h2>
      <div class="muted">用于补录 RMB 加减、额外费用或独立调账项；保存后会立刻进入逐笔台账和导出。</div>
    </div>
  </div>
  <form id="reconciliation-adjustment-form">
    <input type="hidden" name="linked_transaction_id" id="reconciliation-linked-transaction-id" />
    <input type="hidden" name="period_id" id="reconciliation-adjustment-period-id" />
    <select name="group_key" id="reconciliation-adjustment-group" required>
      <option value="">请选择群</option>
    </select>
    <input name="business_role" id="reconciliation-adjustment-role" placeholder="角色，可留空按群映射" />
    <input name="card_type" id="reconciliation-adjustment-card-type" placeholder="卡种，如 xb / rmb / fee" required />
    <input name="usd_amount" id="reconciliation-adjustment-usd-amount" placeholder="刀数，可空" />
    <input name="rate" id="reconciliation-adjustment-rate" placeholder="汇率，可空" />
    <input name="rmb_amount" id="reconciliation-adjustment-rmb-amount" placeholder="人民币，正负都可" required />
    <input name="created_by" id="reconciliation-adjustment-created-by" placeholder="创建人" required />
    <textarea class="full" name="note" id="reconciliation-adjustment-note" placeholder="调账说明（必填，写清依据和备注）" required></textarea>
    <button type="submit">保存逐笔调账</button>
  </form>
  <div class="muted" id="reconciliation-adjustment-status">可从下方逐笔台账点击“引用”快速带入一行，再补充说明后保存。</div>
</section>
<section class="panel stack">
  <div class="toolbar">
    <div>
      <h2>逐笔台账</h2>
      <div class="muted" id="reconciliation-ledger-summary">加载中</div>
    </div>
  </div>
  <div class="table-wrap">
    <table id="reconciliation-ledger-table">
      <thead>
        <tr><th>时间</th><th>来源</th><th>群</th><th>角色</th><th>卡种</th><th>刀数</th><th>汇率</th><th>应算人民币</th><th>人民币</th><th>异常</th><th>备注 / 修改痕迹</th><th>操作</th></tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>
</section>
<section class="panel stack" id="reconciliation-trace-panel">
  <div class="toolbar">
    <div>
      <h2>差额追踪</h2>
      <div class="muted" id="reconciliation-trace-status">点击上方逐笔台账里的“追踪”，直接查看这笔交易从原始消息到记账结果的只读链路。</div>
    </div>
  </div>
  <div class="subgrid">
    <section class="subpanel">
      <h3>交易摘要</h3>
      <dl class="detail-list" id="reconciliation-trace-transaction">
        <div><dt>状态</dt><dd class="muted">尚未选择交易</dd></div>
      </dl>
    </section>
    <section class="subpanel">
      <h3>链路状态</h3>
      <ul class="trace-status-list" id="reconciliation-trace-flow">
        <li><span>captured</span><span class="muted">待加载</span></li>
        <li><span>parsed</span><span class="muted">待加载</span></li>
        <li><span>posted</span><span class="muted">待加载</span></li>
        <li><span>edited</span><span class="muted">待加载</span></li>
        <li><span>flagged</span><span class="muted">待加载</span></li>
      </ul>
    </section>
    <section class="subpanel full">
      <h3>原始消息 / 解析 / 修改</h3>
      <div class="subgrid">
        <dl class="detail-list" id="reconciliation-trace-message">
          <div><dt>原始消息</dt><dd class="muted">尚未选择交易</dd></div>
        </dl>
        <dl class="detail-list" id="reconciliation-trace-parse">
          <div><dt>解析结果</dt><dd class="muted">尚未选择交易</dd></div>
        </dl>
      </div>
      <div class="table-note">
        <dl class="detail-list" id="reconciliation-trace-edit">
          <div><dt>最近修改</dt><dd class="muted">尚未选择交易</dd></div>
        </dl>
      </div>
    </section>
  </div>
</section>
"""
    script = """
function money(value) {
  return Number(value || 0).toFixed(2);
}

function compactNumber(value) {
  if (value === null || value === undefined || value === '') {
    return '';
  }
  return Number(value).toFixed(4).replace(/0+$/, '').replace(/\\.$/, '');
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function roleText(role) {
  if (role === 'customer') return '客户';
  if (role === 'vendor') return '供应商';
  if (role === 'internal') return '内部';
  return '未归属';
}

function scopeText(scope) {
  if (scope === 'period') return '指定账期';
  if (scope === 'range') return '日期区间';
  return '实时窗口';
}

function issueText(issue) {
  if (issue === 'pending_reconciliation') return '未对账';
  if (issue === 'rate_formula_error') return '汇率公式异常';
  if (issue === 'missing_rate') return '缺失汇率';
  if (issue === 'edited_unreviewed') return '已修改未复核';
  return issue;
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

function setLedgerStatus(text, isError = false) {
  const node = document.querySelector('#reconciliation-filter-status');
  node.className = isError ? 'error' : 'muted';
  node.textContent = text;
}

function setAdjustmentStatus(text, isError = false) {
  const node = document.querySelector('#reconciliation-adjustment-status');
  node.className = isError ? 'error' : 'muted';
  node.textContent = text;
}

function updateScopeControls() {
  const scope = document.querySelector('#reconciliation-scope').value;
  const periodNode = document.querySelector('#reconciliation-period');
  const startNode = document.querySelector('#reconciliation-start-date');
  const endNode = document.querySelector('#reconciliation-end-date');
  const isPeriod = scope === 'period';
  const isRange = scope === 'range';
  periodNode.disabled = !isPeriod;
  startNode.disabled = !isRange;
  endNode.disabled = !isRange;
}

function populatePeriodOptions(periods, selectedPeriodId) {
  const node = document.querySelector('#reconciliation-period');
  node.innerHTML = `<option value="">请选择账期</option>${periods.map((period) => `
    <option value="${period.id}">${period.id} · ${period.closed_at}</option>
  `).join('')}`;
  const fallbackValue = selectedPeriodId || node.dataset.pendingValue || '';
  if (fallbackValue !== null && fallbackValue !== undefined && fallbackValue !== '') {
    node.value = String(fallbackValue);
  }
  node.dataset.pendingValue = node.value || '';
}

function combinationLabel(row) {
  const name = row.name || `组合 ${row.id}`;
  const groupText = (row.group_numbers || []).join('+');
  return groupText ? `${name} · ${groupText}` : name;
}

function populateCombinationOptions(combinations, selectedValue = '') {
  const node = document.querySelector('#reconciliation-combination');
  node.innerHTML = `<option value="">全部组合</option>${combinations.map((row) => `
    <option value="${row.id}">${combinationLabel(row)}</option>
  `).join('')}`;
  const fallbackValue = selectedValue || node.dataset.pendingValue || '';
  if (fallbackValue) {
    node.value = String(fallbackValue);
  }
  node.dataset.pendingValue = node.value || '';
}

function populateGroupNumOptions(groupNums, selectedValue = '') {
  const node = document.querySelector('#reconciliation-group-num');
  node.innerHTML = `<option value="">全部组号</option>${groupNums.map((value) => `
    <option value="${value}">组 ${value}</option>
  `).join('')}`;
  const fallbackValue = selectedValue || node.dataset.pendingValue || '';
  if (fallbackValue) {
    node.value = String(fallbackValue);
  }
  node.dataset.pendingValue = node.value || '';
}

function populateGroupOptions(node, groups, selectedValue = '') {
  const placeholder = node.id === 'reconciliation-group-key'
    ? ((document.querySelector('#reconciliation-combination').value || document.querySelector('#reconciliation-group-num').value)
      ? '当前组合/组号下全部群'
      : '全部群')
    : '请选择群';
  node.innerHTML = `<option value="">${placeholder}</option>${groups.map((row) => `
    <option value="${row.group_key}">${row.chat_name || row.group_key}${row.group_num === null || row.group_num === undefined ? '' : ` · 组 ${row.group_num}`}</option>
  `).join('')}`;
  const fallbackValue = selectedValue || node.dataset.pendingValue || '';
  if (fallbackValue) {
    node.value = fallbackValue;
  }
  node.dataset.pendingValue = node.value || '';
}

function populateCardTypeOptions(cardTypes, selectedValue = '') {
  const node = document.querySelector('#reconciliation-card-type');
  node.innerHTML = `<option value="">全部卡种</option>${cardTypes.map((item) => `<option value="${item}">${item}</option>`).join('')}`;
  const fallbackValue = selectedValue || node.dataset.pendingValue || '';
  if (fallbackValue) {
    node.value = fallbackValue;
  }
  node.dataset.pendingValue = node.value || '';
}

function issueCell(row) {
  const items = row.issue_flags || [];
  if (!items.length) {
    return '<span class="muted">—</span>';
  }
  return items.map((item) => issueText(item)).join(' / ');
}

function noteCell(row) {
  const lines = [];
  if (row.source_table === 'finance_adjustment_entries' && row.note) {
    lines.push(`调账：${row.note}`);
  }
  if (row.edit_note) {
    lines.push(`修改：${row.edit_note}`);
  }
  if (row.edited_at || row.edited_by) {
    lines.push(`编辑痕迹：${row.edited_at || '未知时间'}${row.edited_by ? ` · ${row.edited_by}` : ''}`);
  }
  return lines.length ? lines.join('<br>') : '<span class="muted">—</span>';
}

function traceFlagText(flag) {
  return flag ? '已命中' : '未命中';
}

function traceFlagClass(flag) {
  return flag ? 'diff-highlight' : 'diff-safe';
}

function renderDetailList(nodeId, items, emptyTitle, emptyText) {
  const node = document.querySelector(`#${nodeId}`);
  if (!items.length) {
    node.innerHTML = `<div><dt>${escapeHtml(emptyTitle)}</dt><dd class="muted">${escapeHtml(emptyText)}</dd></div>`;
    return;
  }
  node.innerHTML = items.map((item) => `
    <div>
      <dt>${escapeHtml(item.label)}</dt>
      <dd>${item.html ?? escapeHtml(item.value ?? '—')}</dd>
    </div>
  `).join('');
}

function renderTracePlaceholder(text = '尚未选择交易') {
  renderDetailList('reconciliation-trace-transaction', [], '状态', text);
  document.querySelector('#reconciliation-trace-flow').innerHTML = ['captured', 'parsed', 'posted', 'edited', 'flagged']
    .map((item) => `<li><span>${item}</span><span class="muted">待加载</span></li>`)
    .join('');
  renderDetailList('reconciliation-trace-message', [], '原始消息', text);
  renderDetailList('reconciliation-trace-parse', [], '解析结果', text);
  renderDetailList('reconciliation-trace-edit', [], '最近修改', text);
}

function renderDifferenceTrace(payload) {
  const tx = payload.transaction || {};
  const message = payload.message;
  const parseResult = payload.parse_result;
  const latestEdit = payload.latest_edit;
  const issueFlags = payload.issue_flags || [];
  const traceStatus = payload.trace_status || {};

  renderDetailList('reconciliation-trace-transaction', [
    { label: '交易 ID', value: tx.id ?? '—' },
    { label: '群', value: tx.chat_name || tx.group_key || '—' },
    { label: '角色', value: roleText(tx.business_role) },
    { label: '卡种', value: tx.category || '—' },
    { label: '刀数', value: tx.usd_amount === null || tx.usd_amount === undefined ? '—' : money(tx.usd_amount) },
    { label: '汇率', value: tx.rate === null || tx.rate === undefined ? '—' : compactNumber(tx.rate) },
    { label: '人民币', value: tx.rmb_value === null || tx.rmb_value === undefined ? '—' : money(tx.rmb_value) },
    { label: '异常', html: issueFlags.length ? escapeHtml(issueFlags.map((item) => issueText(item)).join(' / ')) : '<span class="muted">无</span>' },
    { label: '创建时间', value: tx.created_at || '—' },
  ], '交易摘要', '暂无交易数据');

  document.querySelector('#reconciliation-trace-flow').innerHTML = [
    ['captured', '已录到原始消息'],
    ['parsed', '已形成解析结果'],
    ['posted', '已写入交易'],
    ['edited', '已被人工修改'],
    ['flagged', '已命中异常标记'],
  ].map(([key, label]) => `
    <li>
      <span>${escapeHtml(label)}</span>
      <span class="${traceFlagClass(Boolean(traceStatus[key]))}">${traceFlagText(Boolean(traceStatus[key]))}</span>
    </li>
  `).join('');

  renderDetailList('reconciliation-trace-message', message ? [
    { label: '消息 ID', value: message.message_id || '—' },
    { label: '发送人', value: message.sender_name || message.sender_id || '—' },
    { label: '收到时间', value: message.received_at || message.created_at || '—' },
    { label: '正文', html: message.text ? `<span class="mono">${escapeHtml(message.text)}</span>` : '<span class="muted">—</span>' },
  ] : [], '原始消息', '这笔交易没有关联到原始消息');

  renderDetailList('reconciliation-trace-parse', parseResult ? [
    { label: '分类', value: parseResult.classification || '—' },
    { label: '状态', value: parseResult.parse_status || '—' },
    { label: '原始文本', html: parseResult.raw_text ? `<span class="mono">${escapeHtml(parseResult.raw_text)}</span>` : '<span class="muted">—</span>' },
  ] : [], '解析结果', '这笔交易当前没有对应的 parse result');

  renderDetailList('reconciliation-trace-edit', latestEdit ? [
    { label: '编辑人', value: latestEdit.edited_by || '—' },
    { label: '编辑时间', value: latestEdit.edited_at || '—' },
    { label: '说明', value: latestEdit.note || '—' },
  ] : [], '最近修改', '这笔交易目前没有人工修改痕迹');
}

async function loadDifferenceTrace(transactionId) {
  document.querySelector('#reconciliation-trace-status').className = 'muted';
  document.querySelector('#reconciliation-trace-status').textContent = `正在加载交易 ${transactionId} 的差额追踪...`;
  const response = await fetch(`/api/reconciliation/difference-trace?transaction_id=${transactionId}`);
  const payload = await response.json();
  if (!response.ok) {
    document.querySelector('#reconciliation-trace-status').className = 'error';
    document.querySelector('#reconciliation-trace-status').textContent = payload.error || '加载差额追踪失败。';
    renderTracePlaceholder('加载失败');
    return;
  }
  document.querySelector('#reconciliation-trace-status').className = 'muted';
  document.querySelector('#reconciliation-trace-status').textContent = `已加载交易 ${transactionId} 的只读追踪链路，可直接对照原始消息、解析结果和人工修改痕迹。`;
  renderDifferenceTrace(payload);
}

function fillAdjustmentForm(row) {
  document.querySelector('#reconciliation-linked-transaction-id').value = row.row_type === 'transaction' ? String(row.row_id) : '';
  document.querySelector('#reconciliation-adjustment-period-id').value = row.period_id || '';
  document.querySelector('#reconciliation-adjustment-group').value = row.group_key || '';
  document.querySelector('#reconciliation-adjustment-role').value = row.business_role || '';
  document.querySelector('#reconciliation-adjustment-card-type').value = row.card_type || '';
  document.querySelector('#reconciliation-adjustment-usd-amount').value = row.usd_amount === null || row.usd_amount === undefined ? '' : compactNumber(row.usd_amount);
  document.querySelector('#reconciliation-adjustment-rate').value = row.rate === null || row.rate === undefined ? '' : compactNumber(row.rate);
  document.querySelector('#reconciliation-adjustment-rmb-amount').value = row.rmb_value === null || row.rmb_value === undefined ? '' : compactNumber(row.rmb_value);
  document.querySelector('#reconciliation-adjustment-note').value = '';
  setAdjustmentStatus(`已引用 ${row.chat_name || row.group_key} / ${row.card_type}，请补充调账说明后保存。`);
}

function normalizeFilterParams(params) {
  const normalized = new URLSearchParams(params);
  const scope = normalized.get('scope') || 'realtime';
  if (scope !== 'period') {
    normalized.delete('period_id');
  }
  if (scope !== 'range') {
    normalized.delete('start_date');
    normalized.delete('end_date');
  }
  if (normalized.get('combination_id')) {
    normalized.delete('group_num');
  } else if (normalized.get('group_num')) {
    normalized.delete('combination_id');
  }
  Array.from(normalized.entries()).forEach(([key, value]) => {
    if (value === '') {
      normalized.delete(key);
    }
  });
  normalized.set('scope', scope);
  return normalized;
}

function syncExportLinks(params) {
  const detailParams = new URLSearchParams(params);
  detailParams.set('export_mode', 'detail');
  document.querySelector('#reconciliation-export-detail-link').href = `/api/reconciliation/export?${detailParams.toString()}`;
  const summaryParams = new URLSearchParams(params);
  summaryParams.set('export_mode', 'summary');
  document.querySelector('#reconciliation-export-summary-link').href = `/api/reconciliation/export?${summaryParams.toString()}`;
}

function resolveGroupLabel(groups, groupKey) {
  if (!groupKey) {
    return '';
  }
  const row = (groups || []).find((item) => item.group_key === groupKey);
  return row ? (row.chat_name || row.group_key) : groupKey;
}

function filterTrailText(data) {
  const filters = data.filters || {};
  const parts = [];
  if (data.selected_combination) {
    parts.push(`组合 ${combinationLabel(data.selected_combination)}`);
  } else if (filters.group_num !== null && filters.group_num !== undefined && filters.group_num !== '') {
    parts.push(`组 ${filters.group_num}`);
  } else {
    parts.push('全部群');
  }
  if (filters.group_key) {
    parts.push(`群 ${resolveGroupLabel(data.available_groups || [], filters.group_key)}`);
  }
  return parts.join(' / ');
}

function scopeRangeText(data) {
  const scope = data.scope || 'realtime';
  if (scope === 'period') {
    return `指定账期 ${data.selected_period_id || '未选择'}`;
  }
  if (scope === 'range') {
    return `${(data.range || {}).start_date || ''} 至 ${(data.range || {}).end_date || ''}`;
  }
  return '最近一次结账之后的实时窗口';
}

function clearGroupDrilldown() {
  const node = document.querySelector('#reconciliation-group-key');
  node.value = '';
  node.dataset.pendingValue = '';
}

function renderLedgerRows(rows) {
  const tbody = document.querySelector('#reconciliation-ledger-table tbody');
  tbody.innerHTML = rows.length
    ? rows.map((row) => `
      <tr>
        <td>${row.created_at || ''}</td>
        <td>${row.row_type === 'finance_adjustment' ? '财务调账' : '原始交易'}</td>
        <td>${row.chat_name || row.group_key}</td>
        <td>${roleText(row.business_role)}</td>
        <td>${row.card_type}</td>
        <td>${money(row.usd_amount)}</td>
        <td>${row.rate === null || row.rate === undefined ? '—' : compactNumber(row.rate)}</td>
        <td>${row.expected_rmb_value === null || row.expected_rmb_value === undefined ? '—' : money(row.expected_rmb_value)}</td>
        <td>${money(row.rmb_value)}</td>
        <td>${issueCell(row)}</td>
        <td>${noteCell(row)}</td>
        <td>
          <div class="action-stack">
            <button type="button" data-action="quote-row" data-row-id="${row.row_id}" data-row-type="${row.row_type}">引用</button>
            ${row.row_type === 'transaction' ? `<button type="button" data-action="trace-row" data-row-id="${row.row_id}">追踪</button>` : ''}
          </div>
        </td>
      </tr>
    `).join('')
    : '<tr><td colspan="12" class="muted">当前筛选下暂无逐笔台账</td></tr>';
}

let latestRows = [];
let initialHydration = true;

async function loadLedger(pushUrl = false) {
  const form = document.querySelector('#reconciliation-filter-form');
  const rawParams = new URLSearchParams(new FormData(form));
  const scope = rawParams.get('scope') || 'realtime';
  if (scope === 'period' && !rawParams.get('period_id') && initialHydration && query.get('period_id')) {
    rawParams.set('period_id', query.get('period_id'));
  }
  if (!rawParams.get('combination_id') && initialHydration && query.get('combination_id')) {
    rawParams.set('combination_id', query.get('combination_id'));
  }
  if (!rawParams.get('group_num') && initialHydration && query.get('group_num')) {
    rawParams.set('group_num', query.get('group_num'));
  }
  if (!rawParams.get('group_key') && initialHydration && query.get('group_key')) {
    rawParams.set('group_key', query.get('group_key'));
  }
  if (!rawParams.get('card_type') && initialHydration && query.get('card_type')) {
    rawParams.set('card_type', query.get('card_type'));
  }
  const params = normalizeFilterParams(rawParams);
  updateScopeControls();
  syncExportLinks(params);
  const response = await fetch(`/api/reconciliation/ledger?${params.toString()}`);
  const data = await response.json();
  if (!response.ok) {
    setLedgerStatus(data.error || '加载逐笔台账失败。', true);
    return;
  }
  if (pushUrl) {
    history.replaceState({}, '', `/reconciliation?${params.toString()}`);
  }
  latestRows = data.rows || [];
  populatePeriodOptions(data.periods || [], data.selected_period_id);
  populateCombinationOptions(data.available_combinations || [], (data.filters || {}).combination_id || '');
  populateGroupNumOptions(data.available_group_nums || [], (data.filters || {}).group_num || '');
  populateGroupOptions(document.querySelector('#reconciliation-group-key'), data.available_groups || [], (data.filters || {}).group_key || '');
  populateGroupOptions(document.querySelector('#reconciliation-adjustment-group'), data.available_groups || [], document.querySelector('#reconciliation-adjustment-group').value);
  populateCardTypeOptions(data.available_card_types || [], (data.filters || {}).card_type || '');
  document.querySelector('#reconciliation-unreconciled').textContent = String((data.summary || {}).unreconciled_count || 0);
  document.querySelector('#reconciliation-rate-error').textContent = String((data.summary || {}).rate_formula_error_count || 0);
  document.querySelector('#reconciliation-missing-rate').textContent = String((data.summary || {}).missing_rate_count || 0);
  document.querySelector('#reconciliation-edited').textContent = String((data.summary || {}).edited_unreviewed_count || 0);
  document.querySelector('#reconciliation-range').textContent = `当前口径：${scopeRangeText(data)} / ${filterTrailText(data)}`;
  document.querySelector('#reconciliation-ledger-summary').textContent =
    `当前 ${latestRows.length} 行，财务口径 ${Number((data.summary || {}).financial_row_count || 0)} 行。导出会沿用 ${filterTrailText(data)}。未对账=${Number((data.summary || {}).unreconciled_count || 0)}，汇率公式异常=${Number((data.summary || {}).rate_formula_error_count || 0)}。`;
  document.querySelector('#reconciliation-adjustment-period-id').value =
    scope === 'period' && data.selected_period_id ? String(data.selected_period_id) : '';
  renderLedgerRows(latestRows);
  document.querySelectorAll('[data-action="quote-row"]').forEach((button) => {
    button.addEventListener('click', () => {
      const rowId = Number(button.getAttribute('data-row-id'));
      const rowType = button.getAttribute('data-row-type');
      const row = latestRows.find((item) => Number(item.row_id) === rowId && item.row_type === rowType);
      if (!row) {
        setAdjustmentStatus('没有找到要引用的台账行，请刷新后再试。', true);
        return;
      }
      fillAdjustmentForm(row);
    });
  });
  document.querySelectorAll('[data-action="trace-row"]').forEach((button) => {
    button.addEventListener('click', async () => {
      const transactionId = Number(button.getAttribute('data-row-id'));
      if (!transactionId) {
        document.querySelector('#reconciliation-trace-status').className = 'error';
        document.querySelector('#reconciliation-trace-status').textContent = '这行没有有效的 transaction_id，无法追踪。';
        renderTracePlaceholder('无法追踪');
        return;
      }
      await loadDifferenceTrace(transactionId);
    });
  });
  setLedgerStatus(`已加载 ${scopeText(scope)} / ${filterTrailText(data)} 下的逐笔台账。`);
  initialHydration = false;
}

document.querySelector('#reconciliation-scope').addEventListener('change', () => {
  updateScopeControls();
});

document.querySelector('#reconciliation-combination').addEventListener('change', (event) => {
  if (event.currentTarget.value) {
    const groupNumNode = document.querySelector('#reconciliation-group-num');
    groupNumNode.value = '';
    groupNumNode.dataset.pendingValue = '';
  }
  clearGroupDrilldown();
});

document.querySelector('#reconciliation-group-num').addEventListener('change', (event) => {
  if (event.currentTarget.value) {
    const combinationNode = document.querySelector('#reconciliation-combination');
    combinationNode.value = '';
    combinationNode.dataset.pendingValue = '';
  }
  clearGroupDrilldown();
});

document.querySelector('#reconciliation-filter-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  await loadLedger(true);
});

document.querySelector('#reconciliation-adjustment-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = Object.fromEntries(new FormData(form).entries());
  if (!String(payload.group_key || '').trim()) {
    setAdjustmentStatus('请选择要挂载的群。', true);
    return;
  }
  if (!String(payload.card_type || '').trim()) {
    setAdjustmentStatus('卡种不能为空。', true);
    return;
  }
  if (!String(payload.created_by || '').trim()) {
    setAdjustmentStatus('创建人不能为空。', true);
    return;
  }
  if (!String(payload.note || '').trim()) {
    setAdjustmentStatus('调账说明不能为空。', true);
    return;
  }
  const response = await fetch('/api/reconciliation/adjustments', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const result = await response.json();
  if (!response.ok) {
    setAdjustmentStatus(result.error || '保存逐笔调账失败。', true);
    return;
  }
  setAdjustmentStatus(`逐笔调账已保存，ID=${result.adjustment_id}`);
  form.reset();
  document.querySelector('#reconciliation-adjustment-period-id').value =
    document.querySelector('#reconciliation-scope').value === 'period'
      ? (document.querySelector('#reconciliation-period').value || '')
      : '';
  await loadLedger(false);
});

const query = new URLSearchParams(window.location.search);
document.querySelector('#reconciliation-scope').value = query.get('scope') || 'realtime';
document.querySelector('#reconciliation-start-date').value = query.get('start_date') || monthStart();
document.querySelector('#reconciliation-end-date').value = query.get('end_date') || localDate();
document.querySelector('#reconciliation-business-role').value = query.get('business_role') || '';
document.querySelector('#reconciliation-edited-filter').value = query.get('edited') || 'all';
document.querySelector('#reconciliation-issue-type').value = query.get('issue_type') || '';
document.querySelector('#reconciliation-period').dataset.pendingValue = query.get('period_id') || '';
document.querySelector('#reconciliation-combination').dataset.pendingValue = query.get('combination_id') || '';
document.querySelector('#reconciliation-group-num').dataset.pendingValue = query.get('group_num') || '';
document.querySelector('#reconciliation-group-key').dataset.pendingValue = query.get('group_key') || '';
document.querySelector('#reconciliation-card-type').dataset.pendingValue = query.get('card_type') || '';
updateScopeControls();
renderTracePlaceholder();
loadLedger(false);
"""
    return _render_layout(
        title="对账中心",
        subtitle="把逐笔交易、财务补录和异常标记收敛到一个页面，先查出问题，再导出台账做 A/B 核对。",
        active_path="/reconciliation",
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
    <div class="muted">按结算账期筛选，支持卡种关键字和排序切换。</div>
  </div>
  <form id="history-form">
    <input type="date" name="start_date" required />
    <input type="date" name="end_date" required />
    <input name="card_keyword" placeholder="卡种关键字，如 steam" />
    <select name="sort_by">
      <option value="usd_amount">按美元面额</option>
      <option value="rmb_amount">按人民币金额</option>
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
      <div class="label">区间客户卡金额</div>
      <div class="value" id="history-customer-rmb">0.00</div>
    </article>
    <article class="card">
      <div class="label">区间供应商卡金额</div>
      <div class="value" id="history-vendor-rmb">0.00</div>
    </article>
    <article class="card">
      <div class="label">卡种数</div>
      <div class="value" id="history-card-type-count">0</div>
    </article>
  </div>
</section>
<section class="panel">
  <div class="toolbar">
    <div>
      <h2>客户 / 供应商卡排行</h2>
      <div class="muted">区间利润按客户正数金额加上供应商负数金额计算，不把预付和欠款流水直接当利润。</div>
    </div>
  </div>
  <div class="subgrid">
    <section class="subpanel">
      <h3>客户侧</h3>
      <div class="muted" id="history-customer-summary">加载中</div>
      <div class="table-wrap">
        <table id="history-customer-cards-table">
          <thead>
            <tr><th>群</th><th>卡种</th><th>刀数</th><th>金额</th><th>覆盖账期</th></tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </section>
    <section class="subpanel">
      <h3>供应商侧</h3>
      <div class="muted" id="history-vendor-summary">加载中</div>
      <div class="table-wrap">
        <table id="history-vendor-cards-table">
          <thead>
            <tr><th>群</th><th>卡种</th><th>刀数</th><th>金额</th><th>覆盖账期</th></tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </section>
  </div>
</section>
<section class="panel">
  <h2>账期列表</h2>
  <table id="history-periods-table">
    <thead>
      <tr><th>账期</th><th>关闭时间</th><th>客户刀数</th><th>供应商刀数</th><th>供应商总成本</th><th>客户总成本</th><th>利润</th></tr>
    </thead>
    <tbody></tbody>
  </table>
</section>
<section class="panel">
  <h2>卡种排行</h2>
  <table id="history-cards-table">
    <thead>
      <tr><th>卡种</th><th>刀数</th><th>人民币金额</th><th>覆盖账期数</th><th>记录数</th></tr>
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

function roleCardSummaryText(block) {
  return `合计 ${money(block.total_usd_amount)} 刀 / ${money(block.total_display_rmb_amount ?? block.total_rmb_amount)} 元`;
}

function renderHistoryRoleCardTable(tableId, rows, emptyText) {
  document.querySelector(`${tableId} tbody`).innerHTML = rows.length
    ? rows.map((row) => `
      <tr>
        <td>${row.groups || '—'}</td>
        <td>${row.card_type}</td>
        <td>${money(row.usd_amount)}</td>
        <td>${money(row.display_rmb_amount ?? row.rmb_amount)}</td>
        <td>${row.period_count}</td>
      </tr>
    `).join('')
    : `<tr><td colspan="5" class="muted">${emptyText}</td></tr>`;
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
  document.querySelector('#history-customer-rmb').textContent = money((data.summary || {}).customer_card_rmb_amount);
  document.querySelector('#history-vendor-rmb').textContent = money((data.summary || {}).vendor_card_rmb_amount);
  document.querySelector('#history-card-type-count').textContent = String((data.summary || {}).card_type_count || 0);
  const roleCardBreakdown = data.role_card_breakdown || {};
  const customerCards = roleCardBreakdown.customer || { rows: [], total_usd_amount: 0, total_rmb_amount: 0, total_unit_count: 0 };
  const vendorCards = roleCardBreakdown.vendor || { rows: [], total_usd_amount: 0, total_rmb_amount: 0, total_unit_count: 0 };
  document.querySelector('#history-customer-summary').textContent = roleCardSummaryText(customerCards);
  document.querySelector('#history-vendor-summary').textContent = roleCardSummaryText(vendorCards);
  renderHistoryRoleCardTable('#history-customer-cards-table', data.customer_card_rankings || [], '当前区间暂无客户卡统计');
  renderHistoryRoleCardTable('#history-vendor-cards-table', data.vendor_card_rankings || [], '当前区间暂无供应商卡统计');

  document.querySelector('#history-periods-table tbody').innerHTML = (data.period_rows || []).map((row) => `
    <tr>
      <td>${row.id}</td>
      <td>${row.closed_at}</td>
      <td>${money(row.customer_card_usd_amount)}</td>
      <td>${money(row.vendor_card_usd_amount)}</td>
      <td>${money(row.vendor_card_rmb_amount)}</td>
      <td>${money(row.customer_card_rmb_amount)}</td>
      <td>${money(row.profit)}</td>
    </tr>
  `).join('');

  document.querySelector('#history-cards-table tbody').innerHTML = (data.card_rankings || []).map((row) => `
    <tr>
      <td>${row.card_type}</td>
      <td>${money(row.usd_amount)}</td>
      <td>${money(row.rmb_amount)}</td>
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
  <a href="/quotes" class="%s">报价墙</a>
  <a href="/quote-dictionary" class="%s">报价字典</a>
  <a href="/reconciliation" class="%s">对账中心</a>
  <a href="/role-mapping" class="%s">角色映射</a>
  <a href="/history" class="%s">跑账历史</a>
</nav>
""" % (
        "active" if active_path == "/" else "",
        "active" if active_path == "/workbench" else "",
        "active" if active_path == "/quotes" else "",
        "active" if active_path == "/quote-dictionary" else "",
        "active" if active_path == "/reconciliation" else "",
        "active" if active_path == "/role-mapping" else "",
        "active" if active_path == "/history" else "",
    )
    return (
        "<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
        f"<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{title}</title>"
        f"{_STYLE}</head><body><header><div class=\"hero\"><div><h1>{title}</h1>"
        f"<p>{subtitle}</p></div></div>{nav}</header><main>{body}</main><script>{script}</script></body></html>"
    )
