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
    grid-template-columns: repeat(3, minmax(0, 1fr));
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
  .full {
    grid-column: 1 / -1;
  }
  .inline-link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 10px 14px;
    border-radius: 999px;
    background: var(--accent);
    color: white;
    text-decoration: none;
    border: 1px solid var(--accent);
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
            <tr><th>卡种</th><th>刀数</th><th>金额</th></tr>
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

function renderRoleCardTable(tableId, rows, emptyText) {
  document.querySelector(`${tableId} tbody`).innerHTML = rows.length
    ? rows.map((row) => `
      <tr>
        <td>${row.card_type}</td>
        <td>${money(row.usd_amount)}</td>
        <td>${money(row.display_rmb_amount ?? row.rmb_amount)}</td>
      </tr>
    `).join('')
    : `<tr><td colspan="3" class="muted">${emptyText}</td></tr>`;
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
  document.querySelector('#dashboard-current-customer-summary').textContent = roleCardSummaryText(currentCustomer);
  document.querySelector('#dashboard-current-vendor-summary').textContent = roleCardSummaryText(currentVendor);
  renderRoleCardTable('#dashboard-current-customer-table', currentCustomer.rows || [], '当前暂无客户卡统计');
  renderRoleCardTable('#dashboard-current-vendor-table', currentVendor.rows || [], '当前暂无供应商卡统计');
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
  <div id="close-period-status" class="muted">直接调用后端关账服务，口径等同 `/alljs`，但不会再往各个群里补发回执。</div>
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
            <tr><th>卡种</th><th>刀数</th><th>金额</th></tr>
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
        <tr><th>群名</th><th>角色</th><th>期初</th><th>收款</th><th>使用</th><th>期末</th><th>交易笔数</th></tr>
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

function renderRoleCardTable(tableId, rows, emptyText, options = {}) {
  const showProfit = Boolean(options.showProfit);
  const profitByCardType = options.profitByCardType || {};
  const colspan = showProfit ? 4 : 3;
  document.querySelector(`${tableId} tbody`).innerHTML = rows.length
    ? rows.map((row) => {
      const amount = Number(row.display_rmb_amount ?? row.rmb_amount ?? 0);
      const profit = Number(profitByCardType[row.card_type] ?? 0);
      return `
      <tr>
        <td>${row.card_type}</td>
        <td>${money(row.usd_amount)}</td>
        <td>${money(amount)}</td>
        ${showProfit ? `<td>${money(profit)}</td>` : ''}
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
  const customerAmountByCardType = {};
  for (const row of (customerCards.rows || [])) {
    customerAmountByCardType[row.card_type] = Number(row.display_rmb_amount ?? row.rmb_amount ?? 0);
  }
  const vendorProfitByCardType = {};
  for (const row of (vendorCards.rows || [])) {
    const vendorAmount = Number(row.display_rmb_amount ?? row.rmb_amount ?? 0);
    const customerAmount = Number(customerAmountByCardType[row.card_type] ?? 0);
    vendorProfitByCardType[row.card_type] = customerAmount + vendorAmount;
  }
  document.querySelector('#workbench-customer-summary').textContent = roleCardSummaryText(customerCards);
  document.querySelector('#workbench-vendor-summary').textContent = roleCardSummaryText(vendorCards);
  renderRoleCardTable('#workbench-customer-cards-table', customerCards.rows || [], '当前口径下暂无客户卡统计');
  renderRoleCardTable(
    '#workbench-vendor-cards-table',
    vendorCards.rows || [],
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
  const confirmed = window.confirm('确认一键结账吗？这会按当前实时交易执行与 /alljs 相同的结账逻辑，但不会往其它群补发回执。');
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
  setWorkbenchStatus(`一键结账完成，账期 ID=${result.period_id}`, false, 'close-period-status');
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
    <a class="inline-link" href="/workbench">回到账期工作台</a>
  </div>
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

  const currentRows = data.current_groups || [];
  document.querySelector('#role-current-table tbody').innerHTML = currentRows.length
    ? currentRows.map((row) => `
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
    : '<tr><td colspan="7" class="muted">暂无群角色映射</td></tr>';
}

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
      <tr><th>账期</th><th>关闭时间</th><th>利润</th><th>美元面额</th><th>群数量</th><th>交易笔数</th></tr>
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
      <td>${money(row.profit)}</td>
      <td>${money(row.total_usd_amount)}</td>
      <td>${row.group_count}</td>
      <td>${row.vendor_transaction_count ?? row.transaction_count}</td>
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
  <a href="/role-mapping" class="%s">角色映射</a>
  <a href="/history" class="%s">跑账历史</a>
</nav>
""" % (
        "active" if active_path == "/" else "",
        "active" if active_path == "/workbench" else "",
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
