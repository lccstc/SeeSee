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
  .table-wrap {
    overflow-x: auto;
  }
  .status-chip {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 72px;
    padding: 4px 10px;
    border-radius: 999px;
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
    border-radius: 18px;
    text-decoration: none;
    background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(237, 243, 240, 0.92));
    border: 1px solid rgba(15, 109, 96, 0.14);
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
    border-radius: 18px;
    background: rgba(255,255,255,0.58);
    border: 1px solid rgba(15, 109, 96, 0.12);
  }
  .table-note {
    margin-top: 8px;
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
    border-radius: 999px;
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
        <td><button type="button" data-action="quote-row" data-row-id="${row.row_id}" data-row-type="${row.row_type}">引用</button></td>
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
  <a href="/reconciliation" class="%s">对账中心</a>
  <a href="/role-mapping" class="%s">角色映射</a>
  <a href="/history" class="%s">跑账历史</a>
</nav>
""" % (
        "active" if active_path == "/" else "",
        "active" if active_path == "/workbench" else "",
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
