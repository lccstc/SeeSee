from __future__ import annotations


_STYLE = """
<style>
  :root {
    color-scheme: dark;
    --bg: #05080b;
    --bg-deep: #0a0f14;
    --bg-mesh: rgba(243, 165, 47, 0.08);
    --panel: rgba(13, 19, 25, 0.96);
    --panel-strong: #111820;
    --panel-soft: #161e27;
    --ink: #e6dcc4;
    --ink-soft: #c3b99f;
    --muted: #8f8a79;
    --line: rgba(243, 165, 47, 0.16);
    --line-strong: rgba(243, 165, 47, 0.26);
    --accent: #f3a52f;
    --accent-strong: #ffc14d;
    --accent-soft: rgba(243, 165, 47, 0.12);
    --accent-wash: rgba(243, 165, 47, 0.08);
    --gold: #ffc14d;
    --gold-soft: rgba(255, 193, 77, 0.14);
    --warn: #ff6b4a;
    --warn-soft: rgba(255, 107, 74, 0.12);
    --ok: #32c48d;
    --ok-soft: rgba(50, 196, 141, 0.16);
    --info: #76a9ff;
    --info-soft: rgba(118, 169, 255, 0.14);
    --shadow: 0 26px 60px rgba(0, 0, 0, 0.34);
    --shadow-soft: 0 12px 26px rgba(0, 0, 0, 0.22);
    --radius-lg: 22px;
    --radius-md: 16px;
    --radius-sm: 10px;
    --sans: "Avenir Next Condensed", "DIN Alternate", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    --serif: "Songti SC", "STSong", "Noto Serif CJK SC", serif;
    --mono: "SFMono-Regular", "Menlo", monospace;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: var(--sans);
    color: var(--ink);
    background: var(--bg);
    background-image:
      radial-gradient(circle at top left, rgba(243, 165, 47, 0.08), transparent 22%),
      radial-gradient(circle at top right, rgba(80, 104, 125, 0.12), transparent 28%),
      linear-gradient(180deg, #071017 0%, #05080b 48%, #030507 100%);
    min-height: 100vh;
  }
  body::before {
    content: "";
    inset: 0;
    pointer-events: none;
    position: fixed;
    background-image:
      linear-gradient(rgba(243, 165, 47, 0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(243, 165, 47, 0.03) 1px, transparent 1px);
    background-size: 26px 26px;
    opacity: 0.7;
    mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.72), transparent 88%);
  }
  a { color: inherit; }
  .app-shell {
    margin: 0 auto;
    max-width: 1520px;
  }
  header {
    padding: 24px 28px 14px;
  }
  .hero {
    display: flex;
    flex-direction: column;
    gap: 22px;
    position: relative;
    flex-wrap: wrap;
  }
  .hero::after {
    content: "";
    position: absolute;
    right: 0;
    top: 8px;
    width: 200px;
    height: 200px;
    border-radius: 999px;
    background:
      radial-gradient(circle at center, rgba(243, 165, 47, 0.16), rgba(243, 165, 47, 0.02) 58%, transparent 70%);
    filter: blur(10px);
    pointer-events: none;
  }
  .hero-copy {
    max-width: 900px;
    position: relative;
    z-index: 1;
  }
  .hero-kicker {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 8px 14px;
    border-radius: 999px;
    background: rgba(17, 24, 32, 0.9);
    border: 1px solid rgba(243, 165, 47, 0.18);
    color: var(--accent-strong);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
  }
  .hero h1 {
    margin: 14px 0 0;
    font-family: var(--sans);
    font-size: clamp(34px, 4.6vw, 52px);
    font-weight: 700;
    letter-spacing: 0.08em;
    line-height: 0.98;
    text-transform: uppercase;
  }
  .hero p {
    margin: 14px 0 0;
    color: var(--muted);
    max-width: 780px;
    line-height: 1.72;
    font-size: 15px;
  }
  .nav-scroll {
    overflow-x: auto;
    padding-bottom: 4px;
  }
  nav {
    display: flex;
    gap: 12px;
    flex-wrap: nowrap;
    margin-top: 0;
    min-width: max-content;
  }
  nav a {
    text-decoration: none;
    padding: 12px 16px;
    border-radius: 999px;
    background: rgba(17, 24, 32, 0.82);
    border: 1px solid rgba(243, 165, 47, 0.1);
    color: var(--ink-soft);
    box-shadow: inset 0 1px 0 rgba(255, 193, 77, 0.06);
    transition: transform 160ms ease, border-color 160ms ease, background 160ms ease, color 160ms ease;
  }
  nav a:hover {
    transform: translateY(-1px);
    border-color: rgba(243, 165, 47, 0.24);
    background: rgba(18, 26, 34, 0.98);
  }
  nav a.active {
    background: linear-gradient(135deg, #3a2a0a, #6b4a12 42%, #f3a52f);
    color: #120f08;
    border-color: transparent;
    box-shadow: 0 10px 24px rgba(243, 165, 47, 0.14);
  }
  main {
    display: grid;
    gap: 20px;
    padding: 6px 28px 40px;
  }
  .panel {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: var(--radius-lg);
    padding: 24px;
    box-shadow: var(--shadow);
    backdrop-filter: blur(10px);
    position: relative;
    overflow: hidden;
  }
  .panel::before {
    content: "";
    position: absolute;
    inset: 0 0 auto;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(243, 165, 47, 0.35), transparent);
  }
  .panel h2, .panel h3 {
    margin: 0 0 12px;
  }
  .panel h2 {
    font-family: var(--sans);
    font-size: 25px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }
  .panel h3 {
    font-size: 16px;
    font-weight: 700;
  }
  .panel-heading {
    display: flex;
    align-items: end;
    justify-content: space-between;
    gap: 18px;
    flex-wrap: wrap;
    margin-bottom: 18px;
  }
  .section-kicker {
    color: var(--gold);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
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
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
  }
  .card {
    padding: 18px;
    border-radius: var(--radius-md);
    background: linear-gradient(180deg, rgba(17, 24, 32, 0.98), rgba(12, 17, 23, 0.96));
    border: 1px solid rgba(243, 165, 47, 0.12);
    box-shadow: var(--shadow-soft);
  }
  .card .label {
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 10px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }
  .card .value {
    font-size: 30px;
    font-weight: 700;
    letter-spacing: -0.04em;
  }
  .stack {
    display: grid;
    gap: 20px;
  }
  .toolbar {
    display: flex;
    gap: 16px;
    justify-content: space-between;
    align-items: end;
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
    padding: 12px 14px;
    border-radius: 14px;
    border: 1px solid rgba(243, 165, 47, 0.14);
    background: rgba(9, 13, 18, 0.92);
    color: var(--ink);
    transition: border-color 160ms ease, box-shadow 160ms ease, background 160ms ease;
  }
  input::placeholder, textarea::placeholder {
    color: rgba(195, 185, 159, 0.58);
  }
  input:focus, textarea:focus, select:focus {
    border-color: rgba(243, 165, 47, 0.48);
    box-shadow: 0 0 0 4px rgba(243, 165, 47, 0.12);
    outline: none;
  }
  textarea {
    min-height: 88px;
    resize: vertical;
  }
  button {
    border: 1px solid transparent;
    border-radius: 14px;
    padding: 12px 16px;
    background: linear-gradient(135deg, #50350d, #87611d 44%, #f3a52f);
    color: #120f08;
    cursor: pointer;
    font-weight: 700;
    letter-spacing: 0.01em;
    transition: transform 160ms ease, box-shadow 160ms ease, opacity 160ms ease;
    box-shadow: 0 10px 22px rgba(243, 165, 47, 0.16);
  }
  button:hover {
    transform: translateY(-1px);
  }
  button:focus-visible {
    outline: none;
    box-shadow: 0 0 0 4px rgba(31, 92, 79, 0.16);
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }
  th, td {
    text-align: left;
    padding: 14px 10px;
    border-bottom: 1px solid rgba(243, 165, 47, 0.08);
    vertical-align: top;
  }
  th {
    color: var(--muted);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
  }
  .table-wrap {
    overflow-x: auto;
    border-radius: 18px;
    border: 1px solid rgba(243, 165, 47, 0.08);
    background: rgba(8, 12, 16, 0.78);
  }
  .table-primary {
    font-weight: 700;
    line-height: 1.35;
  }
  .table-secondary {
    color: var(--muted);
    display: block;
    font-size: 12px;
    line-height: 1.45;
    margin-top: 3px;
  }
  .table-num {
    font-feature-settings: "tnum";
    font-variant-numeric: tabular-nums;
    font-weight: 700;
  }
  .signed-pos {
    color: var(--ok);
  }
  .signed-neg {
    color: var(--warn);
  }
  .signed-neutral {
    color: var(--ink-soft);
  }
  .status-chip {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 78px;
    padding: 5px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
  }
  .status-chip.settled {
    background: var(--accent-soft);
    color: var(--accent-strong);
  }
  .status-chip.unsettled {
    background: var(--gold-soft);
    color: var(--gold);
  }
  .pill-muted {
    display: inline-flex;
    align-items: center;
    padding: 5px 10px;
    border-radius: 999px;
    background: rgba(255, 193, 77, 0.09);
    color: var(--ink-soft);
    font-size: 12px;
    font-weight: 600;
  }
  .mono {
    font-family: var(--mono);
    font-size: 12px;
  }
  .dashboard-hero {
    padding: 28px;
  }
  .dashboard-brief {
    max-width: 420px;
    padding: 14px 16px;
    border-radius: 18px;
    background: linear-gradient(135deg, rgba(15, 21, 27, 0.98), rgba(26, 36, 46, 0.92));
    color: var(--ink);
    box-shadow: 0 18px 34px rgba(0, 0, 0, 0.24);
    border: 1px solid rgba(243, 165, 47, 0.12);
  }
  .dashboard-brief strong {
    display: block;
    margin-bottom: 6px;
    font-size: 12px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }
  .dashboard-summary-grid {
    display: grid;
    grid-template-columns: 1.35fr 1.15fr repeat(3, minmax(0, 0.85fr));
    gap: 16px;
  }
  .stat-card {
    position: relative;
    overflow: hidden;
  }
  .stat-card::after {
    content: "";
    position: absolute;
    inset: auto -12% -44% auto;
    width: 150px;
    height: 150px;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(164, 107, 45, 0.2), transparent 65%);
  }
  .stat-card.primary {
    background: linear-gradient(145deg, #0f141a, #16202a 72%);
    color: #f7f1e8;
    border-color: rgba(243, 165, 47, 0.16);
  }
  .stat-card.primary .label,
  .stat-card.primary .table-secondary {
    color: rgba(247, 241, 232, 0.74);
  }
  .stat-card.primary .value {
    color: #fffdf8;
  }
  .stat-card.secondary {
    background: linear-gradient(180deg, rgba(19, 27, 35, 0.96), rgba(11, 16, 21, 0.94));
  }
  .stat-card .table-secondary {
    max-width: 260px;
  }
  .subgrid {
    display: grid;
    gap: 18px;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .subpanel {
    padding: 18px;
    border-radius: 22px;
    background:
      linear-gradient(180deg, rgba(16, 22, 29, 0.98), rgba(11, 16, 22, 0.92));
    border: 1px solid rgba(243, 165, 47, 0.1);
    box-shadow: var(--shadow-soft);
  }
  .ops-grid {
    display: grid;
    gap: 20px;
    grid-template-columns: 1.2fr 0.8fr;
  }
  .recon-hero-grid {
    display: grid;
    gap: 18px;
    grid-template-columns: 1.05fr 0.95fr;
  }
  .terminal-note {
    display: grid;
    gap: 10px;
    padding: 18px;
    border-radius: 18px;
    background: linear-gradient(145deg, rgba(17, 24, 32, 0.98), rgba(10, 15, 20, 0.94));
    border: 1px solid rgba(243, 165, 47, 0.12);
    box-shadow: var(--shadow-soft);
  }
  .terminal-note strong {
    color: var(--accent-strong);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
  }
  .terminal-note p {
    margin: 0;
    color: var(--ink-soft);
    line-height: 1.68;
  }
  .terminal-note ul {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 8px;
  }
  .terminal-note li {
    color: var(--muted);
    font-size: 13px;
  }
  .recon-filter-form {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
  .recon-adjust-form {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .recon-ledger-panel .table-wrap,
  .trace-terminal .subpanel {
    background: rgba(8, 12, 16, 0.9);
  }
  .trace-terminal .trace-status-list li {
    background: rgba(9, 13, 18, 0.92);
    border-color: rgba(243, 165, 47, 0.08);
  }
  .recon-alert {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 7px 10px;
    border-radius: 999px;
    background: rgba(243, 165, 47, 0.1);
    color: var(--accent-strong);
    font-size: 12px;
    font-weight: 700;
  }
  .panel-config {
    box-shadow: inset 0 0 0 1px rgba(118, 169, 255, 0.06), var(--shadow);
  }
  .panel-assist {
    box-shadow: inset 0 0 0 1px rgba(50, 196, 141, 0.05), var(--shadow);
  }
  .panel-risk {
    box-shadow: inset 0 0 0 1px rgba(255, 107, 74, 0.08), var(--shadow);
  }
  .subpanel-header {
    align-items: baseline;
    display: flex;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 10px;
  }
  .ledger-panel .table-wrap,
  .quote-board-shell .table-wrap {
    background: rgba(8, 12, 16, 0.88);
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
  .action-row {
    display: inline-flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  .action-ghost,
  .action-danger {
    width: auto;
    box-shadow: none;
    padding: 8px 12px;
    font-size: 12px;
  }
  .action-ghost {
    background: rgba(243, 165, 47, 0.1);
    border-color: rgba(243, 165, 47, 0.16);
    color: var(--accent-strong);
  }
  .action-danger {
    background: rgba(166, 63, 44, 0.14);
    border-color: rgba(166, 63, 44, 0.16);
    color: var(--warn);
  }
  .entry-grid {
    display: grid;
    gap: 16px;
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
  .entry-card {
    display: grid;
    gap: 10px;
    padding: 22px;
    border-radius: 24px;
    text-decoration: none;
    background:
      linear-gradient(165deg, rgba(16, 23, 30, 0.98), rgba(10, 15, 20, 0.92));
    border: 1px solid rgba(243, 165, 47, 0.1);
    box-shadow: var(--shadow-soft);
    transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
  }
  .entry-card:hover {
    transform: translateY(-2px);
    border-color: rgba(243, 165, 47, 0.2);
    box-shadow: 0 22px 44px rgba(0, 0, 0, 0.22);
  }
  .entry-card .entry-tag {
    color: var(--gold);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }
  .entry-card strong {
    font-size: 20px;
    line-height: 1.2;
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
    padding: 10px 12px;
    border-radius: 14px;
    background: rgba(255, 252, 247, 0.88);
    border: 1px solid rgba(23, 53, 47, 0.08);
  }
  .table-note {
    margin-top: 8px;
  }
  .quote-stack {
    display: grid;
    gap: 18px;
  }
  .quote-hero {
    padding: 26px;
  }
  .quote-hero-grid {
    display: grid;
    grid-template-columns: 1.3fr 0.95fr;
    gap: 18px;
    margin-bottom: 18px;
  }
  .quote-command {
    display: grid;
    gap: 14px;
    padding: 18px;
    border-radius: 22px;
    background: linear-gradient(145deg, rgba(16, 23, 30, 0.98), rgba(10, 15, 20, 0.94));
    border: 1px solid rgba(243, 165, 47, 0.1);
  }
  .quote-command p {
    margin: 0;
    line-height: 1.7;
    color: var(--ink-soft);
  }
  .quote-insight-list {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }
  .quote-insight-list span {
    display: inline-flex;
    align-items: center;
    padding: 7px 10px;
    border-radius: 999px;
    background: rgba(243, 165, 47, 0.09);
    color: var(--accent-strong);
    font-size: 12px;
    font-weight: 600;
  }
  .quote-metrics {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
  }
  .quote-metric {
    padding: 18px;
    border-radius: 20px;
    background:
      linear-gradient(180deg, rgba(17, 24, 32, 0.98), rgba(10, 15, 20, 0.94));
    border: 1px solid rgba(243, 165, 47, 0.1);
    box-shadow: var(--shadow-soft);
  }
  .quote-metric .label {
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 8px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }
  .quote-metric .value {
    font-size: 30px;
    font-weight: 700;
    letter-spacing: -0.05em;
  }
  .quote-filter-grid {
    display: grid;
    grid-template-columns: 1.6fr repeat(3, 1fr) 0.9fr 0.9fr auto auto;
    gap: 10px;
    padding: 16px;
    border-radius: 22px;
    background: rgba(10, 15, 20, 0.88);
    border: 1px solid rgba(243, 165, 47, 0.08);
  }
  .quote-filter-grid input,
  .quote-filter-grid select,
  .quote-filter-grid button {
    border-radius: 14px;
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
    padding: 6px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
  }
  .quote-status-chip.live {
    background: var(--ok-soft);
    color: var(--ok);
  }
  .quote-status-chip.watch {
    background: var(--gold-soft);
    color: var(--gold);
  }
  .quote-status-chip.stale {
    background: var(--warn-soft);
    color: var(--warn);
  }
  .quote-status-chip.blocked {
    background: rgba(94, 33, 23, 0.26);
    color: var(--warn);
  }
  .quote-status-chip.pending {
    background: rgba(49, 95, 141, 0.12);
    color: var(--info);
  }
  .quote-change-chip {
    display: inline-flex;
    align-items: center;
    padding: 6px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
  }
  .quote-change-chip.new {
    background: var(--info-soft);
    color: var(--info);
  }
  .quote-change-chip.up {
    background: var(--ok-soft);
    color: var(--ok);
  }
  .quote-change-chip.down {
    background: var(--warn-soft);
    color: var(--warn);
  }
  .quote-change-chip.flat {
    background: rgba(255, 193, 77, 0.09);
    color: var(--muted);
  }
  .quote-note {
    color: var(--muted);
    font-size: 12px;
    line-height: 1.55;
    white-space: normal;
  }
  .quote-age {
    color: var(--ink-soft);
    font-weight: 600;
  }
  .quote-age.stale {
    color: var(--warn);
    font-weight: 700;
  }
  .quote-link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: auto;
    padding: 12px 14px;
    border-radius: 14px;
    background: rgba(243, 165, 47, 0.1);
    color: var(--accent-strong);
    text-decoration: none;
    border: 1px solid rgba(243, 165, 47, 0.14);
    box-shadow: none;
  }
  .quote-source-detail {
    color: var(--muted);
    display: block;
    font-size: 12px;
    margin-top: 4px;
    line-height: 1.45;
  }
  .quote-template-help {
    background: rgba(10, 15, 20, 0.84);
    border: 1px solid rgba(243, 165, 47, 0.08);
    border-radius: 18px;
    padding: 12px;
  }
  .quote-template-help strong {
    display: block;
    margin-bottom: 6px;
  }
  .quote-desk-layout {
    display: grid;
    gap: 14px;
    grid-template-columns: minmax(220px, 0.68fr) minmax(0, 1.32fr);
    align-items: start;
  }
  .quote-desk-rail,
  .quote-desk-main,
  .quote-desk-form,
  .quote-desk-flow {
    display: grid;
    gap: 12px;
  }
  .quote-desk-note {
    display: grid;
    gap: 8px;
    padding: 14px;
    border-radius: 18px;
    background: linear-gradient(180deg, rgba(12, 18, 24, 0.94), rgba(8, 12, 16, 0.9));
    border: 1px solid rgba(243, 165, 47, 0.08);
  }
  .quote-desk-note strong,
  .quote-desk-note h3 {
    margin: 0;
    font-size: 13px;
    color: var(--ink);
  }
  .quote-desk-note ul {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 6px;
  }
  .quote-desk-note li {
    color: var(--muted);
    font-size: 12px;
    line-height: 1.55;
  }
  .quote-desk-preset {
    display: grid;
    gap: 6px;
    padding: 10px 12px;
    border-radius: 14px;
    background: rgba(6, 10, 14, 0.88);
    border: 1px solid rgba(243, 165, 47, 0.08);
  }
  .quote-desk-preset strong {
    font-size: 12px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }
  .quote-desk-preset .muted {
    font-size: 12px;
    line-height: 1.55;
  }
  .quote-desk-block {
    display: grid;
    gap: 12px;
    padding: 14px;
    border-radius: 18px;
    background: rgba(10, 15, 20, 0.88);
    border: 1px solid rgba(243, 165, 47, 0.08);
  }
  .quote-desk-block-head {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    align-items: baseline;
    flex-wrap: wrap;
  }
  .quote-desk-block-head h3 {
    margin: 0;
  }
  .quote-desk-grid {
    display: grid;
    gap: 10px;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .quote-desk-grid-3 {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .quote-desk-grid-4 {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
  .quote-desk-field {
    display: grid;
    gap: 6px;
    min-width: 0;
  }
  .quote-desk-field span {
    color: var(--muted);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }
  .quote-desk-field.full {
    grid-column: 1 / -1;
  }
  .quote-desk-actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
  .quote-desk-actions button {
    width: auto;
    flex: 1 1 180px;
  }
  .quote-desk-inline {
    display: grid;
    gap: 10px;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .quote-desk-inline .quote-desk-note {
    height: 100%;
  }
  .quote-desk-table-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 10px;
    flex-wrap: wrap;
  }
  .quote-modal-backdrop {
    align-items: center;
    background: rgba(3, 6, 10, 0.76);
    backdrop-filter: blur(8px);
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
    background: linear-gradient(180deg, rgba(18, 24, 31, 0.98), rgba(11, 16, 22, 0.98));
    border: 1px solid rgba(243, 165, 47, 0.14);
    border-radius: 24px;
    box-shadow: 0 26px 68px rgba(0, 0, 0, 0.42);
    display: flex;
    flex-direction: column;
    max-height: 86vh;
    max-width: 980px;
    overflow: hidden;
    padding: 22px;
    width: min(980px, 100%);
  }
  .quote-modal-wide {
    max-width: 1440px;
    width: min(1440px, 96vw);
    max-height: 94vh;
  }
  .quote-modal h2 {
    font-size: 17px;
    letter-spacing: 0.04em;
  }
  .quote-modal h3 {
    font-size: 13px;
  }
  .quote-modal .panel {
    padding: 14px;
    border-radius: 16px;
  }
  .quote-modal .muted {
    font-size: 11px;
    line-height: 1.45;
  }
  .quote-modal input,
  .quote-modal textarea,
  .quote-modal select {
    padding: 8px 10px;
    border-radius: 10px;
    font-size: 12px;
  }
  .quote-modal textarea {
    min-height: 160px;
  }
  .quote-modal button {
    width: auto;
    flex: 0 0 auto;
    padding: 8px 10px;
    border-radius: 10px;
    font-size: 12px;
    box-shadow: none;
  }
  .quote-modal-header {
    align-items: start;
    display: flex;
    gap: 12px;
    justify-content: space-between;
    margin-bottom: 8px;
  }
  .quote-modal-header-copy {
    display: grid;
    gap: 4px;
    min-width: 0;
  }
  .quote-modal-header h2 {
    margin: 0;
  }
  .quote-modal-close {
    width: auto;
  }
  .quote-harvest-modebar {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
    padding: 6px 0 8px;
    border-bottom: 1px solid rgba(243, 165, 47, 0.08);
    margin-bottom: 4px;
  }
  .quote-modal-body {
    padding: 8px 0;
    flex: 1 1 auto;
    min-height: 0;
    overflow: auto;
  }
  .quote-modal-wide .quote-modal-body {
    overflow: hidden;
  }
  .quote-modal-footer {
    display: flex;
    gap: 8px;
    justify-content: space-between;
    align-items: center;
    padding-top: 10px;
    margin-top: 8px;
    border-top: 1px solid rgba(243, 165, 47, 0.12);
    flex: 0 0 auto;
  }
  .quote-modal-actions {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
  }
  .quote-modal-actions input {
    min-width: 140px;
  }
  .quote-modal-save {
    background: linear-gradient(135deg, #18483d, #1f6e5b 44%, #32c48d);
    color: #05120d;
    box-shadow: 0 10px 24px rgba(50, 196, 141, 0.18);
  }
  .exc-card {
    border: 1px solid rgba(255, 107, 74, 0.14);
    border-radius: 18px;
    padding: 14px;
    background: linear-gradient(180deg, rgba(22, 17, 18, 0.96), rgba(13, 16, 20, 0.96));
    box-shadow: inset 0 0 0 1px rgba(255, 107, 74, 0.04), var(--shadow-soft);
  }
  .exc-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    margin-bottom: 10px;
    flex-wrap: wrap;
  }
  .exc-card-meta {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
  }
  .exc-card-actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
  .exc-card-brief {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 8px;
    font-size: 12px;
    color: var(--muted);
    flex-wrap: wrap;
  }
  .exc-lines {
    display: grid;
    gap: 8px;
  }
  .exc-line {
    padding: 8px 10px;
    border-radius: 12px;
    border: 1px solid rgba(243, 165, 47, 0.1);
    background: rgba(8, 12, 16, 0.86);
    font-family: var(--mono);
    font-size: 13px;
    color: var(--ink-soft);
  }
  .quote-harvest-grid {
    display: grid;
    grid-template-columns: minmax(300px, 0.86fr) minmax(520px, 1.14fr);
    gap: 10px;
    align-items: stretch;
    height: min(72vh, 820px);
    min-height: 0;
  }
  .quote-harvest-workflow {
    display: grid;
    grid-template-columns: minmax(300px, 0.82fr) minmax(360px, 0.98fr) minmax(320px, 0.92fr);
    gap: 12px;
    align-items: stretch;
    height: min(70vh, 780px);
    min-height: 0;
  }
  .quote-harvest-side {
    margin: 0;
    min-height: 0;
  }
  .quote-harvest-side.primary {
    display: flex;
    flex-direction: column;
    gap: 12px;
    height: 100%;
    overflow: hidden;
  }
  .quote-harvest-side-shell {
    display: flex;
    flex-direction: column;
    gap: 12px;
    flex: 1 1 auto;
    min-height: 0;
    overflow: hidden;
  }
  .quote-harvest-side-header {
    display: grid;
    gap: 12px;
    flex: 0 0 auto;
    padding-bottom: 2px;
  }
  .quote-harvest-lines {
    display: flex;
    flex-direction: column;
    gap: 8px;
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
    padding-right: 4px;
    padding-bottom: 8px;
    overscroll-behavior: contain;
  }
  .quote-harvest-stack {
    display: flex;
    flex-direction: column;
    gap: 12px;
    height: 100%;
    min-height: 0;
  }
  .quote-harvest-column {
    display: flex;
    flex-direction: column;
    gap: 12px;
    height: 100%;
    min-height: 0;
  }
  .quote-harvest-column-scroll {
    display: flex;
    flex-direction: column;
    gap: 12px;
    height: 100%;
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
    padding-right: 4px;
  }
  .quote-harvest-preview-col {
    min-width: 0;
  }
  .quote-harvest-workbench {
    display: grid;
    grid-template-columns: minmax(300px, 0.8fr) minmax(680px, 1.2fr);
    gap: 8px;
    align-items: stretch;
    height: min(78vh, 940px);
    min-height: 0;
    overflow: hidden;
  }
  .quote-harvest-workspace {
    display: flex;
    flex-direction: column;
    gap: 10px;
    height: 100%;
    min-height: 0;
    overflow: hidden;
  }
  .quote-harvest-workspace-scroll {
    display: flex;
    flex-direction: column;
    gap: 10px;
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
    padding-right: 4px;
    padding-bottom: 10px;
    overscroll-behavior: contain;
  }
  .quote-harvest-pane-tabs {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
  .quote-harvest-modebar .quote-harvest-pane-tabs {
    width: 100%;
  }
  .quote-harvest-pane-tab {
    width: auto;
    flex: 0 0 auto;
    padding: 7px 12px;
    border-radius: 999px;
    border: 1px solid rgba(243, 165, 47, 0.12);
    background: rgba(8, 12, 16, 0.84);
    color: var(--ink-soft);
    box-shadow: none;
  }
  .quote-harvest-pane-tab.active {
    background: linear-gradient(135deg, #3a2a0a, #6b4a12 42%, #f3a52f);
    color: #120f08;
    border-color: transparent;
  }
  .quote-harvest-modebar .quote-harvest-pane-tab {
    min-width: 140px;
    justify-content: center;
  }
  .quote-harvest-step-compact {
    display: grid;
    gap: 6px;
    padding: 10px;
    border-radius: 12px;
    border: 1px solid rgba(243, 165, 47, 0.1);
    background: rgba(8, 12, 16, 0.84);
    flex: 0 0 auto;
  }
  .quote-harvest-edit-pane {
    display: flex;
    flex-direction: column;
    gap: 8px;
    flex: 1 1 auto;
    min-height: 0;
    overflow: hidden;
  }
  .quote-harvest-fixed-section {
    flex: 0 0 auto;
    min-height: 0;
  }
  .quote-harvest-rows-section {
    display: flex;
    flex-direction: column;
    gap: 8px;
    flex: 1 1 auto;
    min-height: 0;
    overflow: hidden;
  }
  .quote-harvest-rows-scroll {
    display: flex;
    flex-direction: column;
    gap: 8px;
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
    padding-right: 4px;
    padding-bottom: 6px;
    overscroll-behavior: contain;
  }
  .quote-harvest-lines > div {
    padding: 6px 8px;
  }
  .quote-modal th,
  .quote-modal td {
    padding: 10px 8px;
  }
  .quote-harvest-scroll {
    height: 100%;
    overflow-y: auto;
    overflow-x: hidden;
    padding-right: 4px;
  }
  .quote-result-lines {
    display: flex;
    flex-direction: column;
    gap: 8px;
    flex: 1 1 auto;
    min-height: 0;
    overflow: auto;
  }
  .diff-highlight {
    color: var(--warn);
    font-weight: 700;
  }
  .diff-safe {
    color: var(--ok);
    font-weight: 700;
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
    border-radius: 14px;
    background: linear-gradient(135deg, #50350d, #87611d 44%, #f3a52f);
    color: #120f08;
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
  #quote-board-table tbody tr,
  #latest-transactions-table tbody tr {
    transition: background 140ms ease;
  }
  #quote-board-table tbody tr:hover,
  #latest-transactions-table tbody tr:hover {
    background: rgba(243, 165, 47, 0.05);
  }
  @media (max-width: 980px) {
    .hero h1 {
      font-size: 38px;
    }
    .dashboard-summary-grid,
    .quote-hero-grid {
      grid-template-columns: 1fr;
    }
    .cards {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .quote-metrics,
    .quote-filter-grid,
    .recon-filter-form,
    .recon-adjust-form {
      grid-template-columns: 1fr;
    }
    .entry-grid,
    .subgrid,
    .ops-grid,
    .recon-hero-grid,
    .quote-harvest-grid,
    .quote-desk-layout,
    .quote-desk-inline {
      grid-template-columns: 1fr;
    }
    .quote-harvest-workflow {
      grid-template-columns: 1fr;
      height: auto;
    }
    .quote-harvest-workbench {
      grid-template-columns: 1fr;
      height: auto;
    }
    form {
      grid-template-columns: 1fr;
    }
    .full {
      grid-column: auto;
    }
    .quote-modal-wide .quote-modal-body {
      overflow: auto;
    }
    .quote-harvest-grid {
      height: auto;
    }
    .quote-harvest-column,
    .quote-harvest-column-scroll {
      height: auto;
    }
    .quote-harvest-side.primary,
    .quote-harvest-stack,
    .quote-harvest-scroll,
    .quote-harvest-lines,
    .quote-harvest-scroll,
    .quote-result-lines {
      height: auto;
      max-height: none;
    }
    .quote-desk-grid-3,
    .quote-desk-grid-4 {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }
  @media (max-width: 1280px) {
    .quote-harvest-workflow {
      grid-template-columns: minmax(300px, 0.92fr) minmax(360px, 1.08fr);
      height: auto;
    }
    .quote-harvest-workbench {
      grid-template-columns: 1fr;
      height: auto;
    }
    .quote-harvest-preview-col {
      grid-column: 1 / -1;
    }
  }
  @media (max-width: 640px) {
    header, main {
      padding-left: 16px;
      padding-right: 16px;
    }
    .panel {
      padding: 18px;
      border-radius: 22px;
    }
    .cards {
      grid-template-columns: 1fr;
    }
    nav {
      gap: 10px;
    }
    nav a {
      padding: 10px 13px;
    }
    .quote-modal,
    .quote-modal-wide {
      padding: 16px;
      max-height: 96vh;
    }
    .quote-modal-footer {
      align-items: stretch;
    }
    .quote-modal-actions {
      width: 100%;
    }
    .quote-desk-grid,
    .quote-desk-grid-3,
    .quote-desk-grid-4 {
      grid-template-columns: 1fr;
    }
  }
</style>
"""


def render_dashboard_page() -> str:
    body = """
<section class="panel stack dashboard-hero">
  <div class="panel-heading">
    <div>
      <div class="section-kicker">Ledger Terminal</div>
      <h2>总账主屏</h2>
      <div class="muted" id="dashboard-range">口径加载中</div>
    </div>
    <div class="dashboard-brief">
      <strong>主屏口径</strong>
      先看实时余额、已实现利润和当前窗口预估，再决定今天是进账期工作台、对账台，还是先处理异常与映射。
    </div>
  </div>
  <div class="dashboard-summary-grid">
    <article class="card stat-card primary">
      <div class="label">当前总余额</div>
      <div class="value" id="summary-total-balance">0.00</div>
      <span class="table-secondary">实时群余额合并后的当前视角，不掺入历史已关账期。</span>
    </article>
    <article class="card stat-card secondary">
      <div class="label">当前实时预估利润</div>
      <div class="value" id="summary-estimated-profit">0.00</div>
      <span class="table-secondary">主屏只看当前窗口的结构化交易和卡面差额。</span>
    </article>
    <article class="card stat-card">
      <div class="label">今日已实现利润</div>
      <div class="value" id="summary-profit">0.00</div>
      <span class="table-secondary">只算今天已经结算的账期。</span>
    </article>
    <article class="card stat-card">
      <div class="label">实时账期总计刀数</div>
      <div class="value" id="summary-vendor-usd">0.00</div>
      <span class="table-secondary">当前窗口内已识别刀数。</span>
    </article>
    <article class="card stat-card">
      <div class="label">未归属 / 待处理群数</div>
      <div class="value" id="summary-unassigned">0</div>
      <span class="table-secondary">用于判断是否需要先做治理。</span>
    </article>
  </div>
</section>
<section class="panel stack">
  <div class="panel-heading">
    <div>
      <div class="section-kicker">Live Book</div>
      <h2>实时卡面</h2>
      <div class="muted">把客户侧和供应商侧放在同一个主屏里对照，快速看出缺口、利润和偏移。</div>
    </div>
  </div>
  <div class="subgrid">
    <section class="subpanel">
      <div class="subpanel-header">
        <h3>客户侧</h3>
        <span class="pill-muted" id="dashboard-current-customer-summary">加载中</span>
      </div>
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
      <div class="subpanel-header">
        <h3>供应商侧</h3>
        <span class="pill-muted" id="dashboard-current-vendor-summary">加载中</span>
      </div>
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
<section class="panel stack ledger-panel">
  <div class="panel-heading">
    <div>
      <div class="section-kicker">Execution Tape</div>
      <h2>最新入账流</h2>
      <div class="muted">按时间带看最近识别到的结构化交易，用来确认采集、解析和账期状态有没有跑偏。</div>
    </div>
    <div class="muted">主屏只做观察，不在这里直接改账。</div>
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
    <div class="section-kicker">Desk Routes</div>
    <h2>工作面入口</h2>
    <div class="muted">主屏只负责给信号，真正的关账、对账、治理和复盘都应该进入对应工作面处理。</div>
  </div>
  <div class="entry-grid">
    <a class="entry-card" href="/workbench">
      <span class="entry-tag">Main</span>
      <strong>账期工作面</strong>
      <span>承接关账、账期回查、群快照和实时治理，是日常操作的主工作面。</span>
    </a>
    <a class="entry-card" href="/reconciliation">
      <span class="entry-tag">Finance</span>
      <strong>对账工作面</strong>
      <span>逐笔核对汇率、RMB 加减、修改痕迹和财务补录，用来做最终账务确认。</span>
    </a>
    <a class="entry-card" href="/role-mapping">
      <span class="entry-tag">Governance</span>
      <strong>映射治理台</strong>
      <span>集中处理群角色、组号规则和别名归一化，先把口径统一，再谈利润和报价。</span>
    </a>
    <a class="entry-card" href="/history">
      <span class="entry-tag">Review</span>
      <strong>历史回放台</strong>
      <span>按账期和时间区间复盘利润、卡种结构和趋势变化，用来做复盘和校正。</span>
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

function signedClass(value) {
  const number = Number(value || 0);
  if (number > 0) return 'signed-pos';
  if (number < 0) return 'signed-neg';
  return 'signed-neutral';
}

function moneySpan(value, options = {}) {
  const number = Number(value || 0);
  const classes = ['table-num'];
  if (options.signed) {
    classes.push(signedClass(number));
  }
  const text = options.showPlus ? signedMoney(number) : money(number);
  return `<span class="${classes.join(' ')}">${text}</span>`;
}

function diffClass(value) {
  return signedClass(value);
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
        <td><span class="table-primary">${row.chat_name}</span><span class="table-secondary">${row.chat_id || row.group_key || '—'}</span></td>
        <td><span class="pill-muted">${roleText(row.business_role)}</span></td>
        <td><span class="table-primary">${row.sender_name || '—'}</span><span class="table-secondary">${row.sender_id || '—'}</span></td>
        <td><span class="table-primary">${row.category}</span><span class="table-secondary">${row.message_id || '—'}</span></td>
        <td><span class="table-num">${rateText(row.rate)}</span></td>
        <td><span class="table-num">${money(row.display_usd_amount)}</span></td>
        <td><span class="table-num">${money(row.display_rmb_amount ?? row.rmb_value)}</span></td>
        <td><span class="table-primary">${row.created_at}</span><span class="table-secondary">${row.is_edited ? '已修改' : '原始识别'}</span></td>
        <td>${statusChip(row.period_status)}</td>
      </tr>
    `).join('')
    : '<tr><td colspan="9" class="muted">暂无最近识别交易</td></tr>';
}

loadDashboard();
"""
    return _render_layout(
        title="Ledger Terminal",
        subtitle="先看实时口径、风险信号和账期状态，再决定今天进入哪个工作面。",
        active_path="/",
        body=body,
        script=script,
    )


def render_quotes_page() -> str:
    body = """
<section class="panel stack quote-hero">
  <div class="panel-heading">
    <div>
      <div class="section-kicker">Quote Terminal</div>
      <h2>报价主屏</h2>
      <div class="muted" id="quote-board-range">当前客人报价加载中</div>
    </div>
    <div class="toolbar-actions">
      <button type="button" id="quote-refresh-btn">刷新</button>
      <a class="quote-link" href="#quote-exceptions">转到风险池</a>
    </div>
  </div>
  <div class="quote-hero-grid">
    <div class="quote-command">
      <p>主屏只做一件事：先看当前最高价，再判断是继续收、切换来源群，还是进入模板治理和异常处理。价格、变动、来源、时效必须一眼扫出来。</p>
      <div class="quote-insight-list">
        <span>主屏按精确 SKU 取最高价</span>
        <span>超时与禁收单独警示</span>
        <span>风险池保持近手可达</span>
      </div>
    </div>
    <div class="quote-metrics">
      <article class="quote-metric">
        <div class="label">当前可用</div>
        <div class="value" id="quote-live-count">0</div>
      </article>
      <article class="quote-metric">
        <div class="label">有效来源群</div>
        <div class="value" id="quote-source-count">0</div>
      </article>
      <article class="quote-metric">
        <div class="label">待处理异常</div>
        <div class="value" id="quote-exception-count">0</div>
      </article>
    </div>
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
  <div class="muted" id="quote-filter-status">主屏按精确 SKU 显示当前最高价；离散面额与区间分开，点“深度”看同 SKU 其余来源。</div>
  <div class="quote-board-shell">
    <div class="table-wrap">
    <table id="quote-board-table" class="quote-table">
      <thead>
        <tr><th>卡种</th><th>国家 / 币种</th><th>面额 / 条件</th><th>形态</th><th>主价</th><th>组实时</th><th>来源台</th><th>信号时刻</th><th>时效</th><th>状态</th><th>限制</th><th>动作</th></tr>
      </thead>
      <tbody></tbody>
    </table>
    </div>
  </div>
</section>
<div class="ops-grid">
<section class="panel stack panel-config" id="quote-profile-panel">
  <div class="toolbar">
    <div>
      <div class="section-kicker">Parsing Desk</div>
      <h2>群模板配置台</h2>
      <div class="muted">这里不是“填配置”，而是给一个群定稳定口径。先认群，再定默认值，再选最接近的模板。</div>
    </div>
  </div>
  <div class="quote-desk-note">
    <strong>最短路径</strong>
    <ul>
      <li>先填平台、群 ID、群名，锁定这个群是谁。</li>
      <li>再填默认卡种、币种、形态、倍数和超时，补齐群里省略信息。</li>
      <li>最后选最接近的模板，不够再补高级配置。</li>
    </ul>
  </div>
  <form id="quote-profile-form" class="quote-desk-form">
    <section class="quote-desk-block">
      <div class="quote-desk-block-head">
        <h3>群信息</h3>
        <div class="muted">先认这个群，后面异常才能一键回填到这里。</div>
      </div>
      <div class="quote-desk-grid quote-desk-grid-3">
        <label class="quote-desk-field">
          <span>平台</span>
          <input name="platform" placeholder="如 whatsapp" />
        </label>
        <label class="quote-desk-field">
          <span>群 ID / chat_id</span>
          <input name="chat_id" placeholder="必填" required />
        </label>
        <label class="quote-desk-field">
          <span>群名</span>
          <input name="chat_name" placeholder="给运营看的名字" />
        </label>
      </div>
    </section>
    <section class="quote-desk-block">
      <div class="quote-desk-block-head">
        <h3>默认口径</h3>
        <div class="muted">这些值会补齐群里省略写法，减少短句掉进异常池。</div>
      </div>
      <div class="quote-desk-grid quote-desk-grid-4">
        <label class="quote-desk-field">
          <span>默认卡种</span>
          <input name="default_card_type" placeholder="如 Apple" />
        </label>
        <label class="quote-desk-field">
          <span>默认国家 / 币种</span>
          <input name="default_country_or_currency" placeholder="如 USD" />
        </label>
        <label class="quote-desk-field">
          <span>默认形态</span>
          <input name="default_form_factor" placeholder="如 横白 / 竖卡 / 代码" />
        </label>
        <label class="quote-desk-field">
          <span>默认倍数</span>
          <input name="default_multiplier" placeholder="可空，如 50X" />
        </label>
        <label class="quote-desk-field">
          <span>超时分钟</span>
          <input name="stale_after_minutes" placeholder="如 30" />
        </label>
      </div>
    </section>
    <section class="quote-desk-block">
      <div class="quote-desk-block-head">
        <h3>解析模板</h3>
        <div class="muted">先选模板，再决定是否需要高级配置。</div>
      </div>
      <div class="quote-desk-grid">
        <label class="quote-desk-field">
          <span>模板名</span>
          <input name="parser_template" placeholder="如 apple_modifier_sheet" list="quote-template-options" />
        </label>
        <label class="quote-desk-field full">
          <span>高级模板配置</span>
          <textarea name="template_config" placeholder="默认模板不够时再填，没把握先留空"></textarea>
        </label>
      </div>
      <datalist id="quote-template-options">
        <option value="sectioned_group_sheet"></option>
        <option value="group_fixed_sheet"></option>
        <option value="apple_modifier_sheet"></option>
        <option value="section_sheet"></option>
        <option value="simple_sheet"></option>
        <option value="supermarket-card"></option>
      </datalist>
    </section>
    <section class="quote-desk-block">
      <div class="quote-desk-block-head">
        <h3>常用模板参考</h3>
        <div class="muted">只保留最常用三类，避免把这块做成说明文档。</div>
      </div>
      <div class="quote-desk-grid quote-desk-grid-3">
        <div class="quote-desk-preset">
          <strong>group_fixed_sheet</strong>
          <div class="muted">固定群表，适合整齐报价和形态差价。</div>
        </div>
        <div class="quote-desk-preset">
          <strong>apple_modifier_sheet</strong>
          <div class="muted">Apple 群专用，先基准价，再按修饰词派生。</div>
        </div>
        <div class="quote-desk-preset">
          <strong>supermarket-card</strong>
          <div class="muted">超市卡混合群，多个品牌混在一条原文里时用。</div>
        </div>
      </div>
    </section>
    <div class="quote-desk-actions">
      <button type="submit">保存模板</button>
      <button type="button" id="quote-profile-clear">清空表单</button>
    </div>
  </form>
  <div class="muted" id="quote-profile-prefill-status">可从风险池把当前异常一键带入配置台，补成稳定模板。</div>
  <div class="quote-desk-table-head">
    <h3>当前已生效模板</h3>
    <div class="muted">这里看已经进入主线解析的群口径，支持继续编辑或删除。</div>
  </div>
  <div class="table-wrap">
    <table id="quote-profile-table" class="quote-table">
      <thead>
        <tr><th>平台</th><th>群ID</th><th>群名</th><th>默认卡种</th><th>默认币种</th><th>默认形态</th><th>默认倍数</th><th>模板</th><th>超时</th><th>备注</th><th>操作</th></tr>
      </thead>
      <tbody><tr><td colspan="11" class="muted">暂无模板配置</td></tr></tbody>
    </table>
  </div>
</section>
<section class="panel stack panel-assist" id="quote-inquiry-panel">
  <div class="toolbar">
    <div>
      <div class="section-kicker">Relay Desk</div>
      <h2>短回复接力台</h2>
      <div class="muted">这块只处理一种情况: 客人先问完整需求，群里下一条只回一个裸价。先把上下文挂住，再等短回复回主屏。</div>
    </div>
  </div>
  <div class="quote-desk-note">
    <strong>最短路径</strong>
    <ul>
      <li>只在“客人先问完整需求，群里下一条只回裸价”时使用。</li>
      <li>先定客人群，再挂卡种、国家、面额、形态这几个上下文。</li>
      <li>创建后，系统会在有效期内等下一条短回复来接力。</li>
    </ul>
  </div>
  <form id="quote-inquiry-form" class="quote-desk-form">
    <section class="quote-desk-block">
      <div class="quote-desk-block-head">
        <h3>客人群</h3>
        <div class="muted">短回复最后会回到这个群。</div>
      </div>
      <div class="quote-desk-grid">
        <label class="quote-desk-field">
          <span>回复客人群 ID / chat_id</span>
          <input name="chat_id" placeholder="必填" required />
        </label>
        <label class="quote-desk-field">
          <span>回复客人群名</span>
          <input name="chat_name" placeholder="方便识别，可空" />
        </label>
      </div>
    </section>
    <section class="quote-desk-block">
      <div class="quote-desk-block-head">
        <h3>询价上下文</h3>
        <div class="muted">这些值就是下一条裸价要补回主屏的上下文。</div>
      </div>
      <div class="quote-desk-grid quote-desk-grid-4">
        <label class="quote-desk-field">
          <span>卡种</span>
          <input name="card_type" placeholder="如 Apple" required />
        </label>
        <label class="quote-desk-field">
          <span>国家 / 币种</span>
          <input name="country_or_currency" placeholder="如 UK" required />
        </label>
        <label class="quote-desk-field">
          <span>面额</span>
          <input name="amount_range" placeholder="如 10" required />
        </label>
        <label class="quote-desk-field">
          <span>形态</span>
          <input name="form_factor" placeholder="如 不限 / 代码" />
        </label>
        <label class="quote-desk-field">
          <span>倍数</span>
          <input name="multiplier" placeholder="可空" />
        </label>
        <label class="quote-desk-field full">
          <span>原始询价</span>
          <input name="prompt_text" placeholder="如 Apple UK 10 现在什么价" />
        </label>
      </div>
    </section>
    <div class="quote-desk-actions">
      <button type="submit">创建上下文</button>
    </div>
  </form>
  <div class="quote-desk-table-head">
    <h3>当前有效上下文</h3>
    <div class="muted">只有在有效期内的上下文才会接住下一条裸价。</div>
  </div>
  <div class="table-wrap">
    <table id="quote-inquiry-table" class="quote-table">
      <thead>
        <tr><th>状态</th><th>客人群</th><th>卡种</th><th>国家 / 币种</th><th>面额</th><th>形态</th><th>有效到</th><th>来源询价</th></tr>
      </thead>
      <tbody><tr><td colspan="8" class="muted">暂无短回复上下文</td></tr></tbody>
    </table>
  </div>
</section>
</div>
<section class="panel stack panel-risk" id="quote-exceptions">
  <div class="toolbar">
    <div>
      <div class="section-kicker">Risk Pool</div>
      <h2>异常风险池</h2>
      <div class="muted" id="quote-exception-range">默认只看待处理异常，每页 10 条；已处理异常可切换查看。这里是人工补洞入口，不是主解析链路。</div>
    </div>
    <div class="toolbar-actions">
      <button type="button" id="quote-exception-toggle">查看已处理</button>
      <button type="button" id="quote-exception-prev">上一页</button>
      <button type="button" id="quote-exception-next">下一页</button>
    </div>
  </div>
  <div class="muted" id="quote-exception-page-status">第 1 页</div>
  <div id="quote-exception-cards" style="display:flex;flex-direction:column;gap:12px;padding:4px 0;"></div>
</section>
<div class="quote-modal-backdrop" id="quote-ranking-modal" aria-hidden="true">
  <div class="quote-modal" role="dialog" aria-modal="true" aria-labelledby="quote-ranking-title">
    <div class="quote-modal-header">
      <div>
        <h2>同 SKU 深度屏</h2>
        <div class="muted" id="quote-ranking-title">点击主屏任意一行查看同 SKU 的来源深度。</div>
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
<div class="quote-modal-backdrop" id="quote-harvest-modal" aria-hidden="true">
  <div class="quote-modal quote-modal-wide" role="dialog" aria-modal="true">
    <div class="quote-modal-header">
      <div class="quote-modal-header-copy">
        <h2>异常整理台</h2>
        <div class="muted" id="quote-harvest-subtitle">默认先用标准模板整理；复杂混合原文可切换到分段收割，逐段预览并保存。</div>
      </div>
      <button class="quote-modal-close" type="button" id="quote-harvest-close">关闭</button>
    </div>
    <div id="quote-harvest-modes" class="quote-harvest-modebar"></div>
    <div id="quote-harvest-body" class="quote-modal-body">
      <div class="muted">加载中...</div>
    </div>
    <div class="quote-modal-footer">
      <div id="quote-harvest-summary" class="muted" style="font-size:13px;"></div>
      <div class="quote-modal-actions">
        <input type="password" id="quote-harvest-admin-password" placeholder="管理口令" style="min-width:180px;" />
        <button type="button" id="quote-harvest-preview">生成预览</button>
        <button type="button" id="quote-harvest-cancel">取消</button>
        <button type="button" class="quote-modal-save" id="quote-harvest-save">保存模板</button>
      </div>
    </div>
  </div>
</div>
<div class="quote-modal-backdrop" id="quote-profile-edit-modal" aria-hidden="true">
  <div class="quote-modal" role="dialog" aria-modal="true">
    <div class="quote-modal-header">
      <div>
        <h2>编辑模板</h2>
        <div class="muted" id="quote-profile-edit-subtitle">直接编辑当前群模板并保存。</div>
      </div>
      <button class="quote-modal-close" type="button" id="quote-profile-edit-close">关闭</button>
    </div>
    <div id="quote-profile-edit-body" class="quote-modal-body">
      <div class="muted">加载中...</div>
    </div>
    <div class="quote-modal-footer">
      <div id="quote-profile-edit-summary" class="muted" style="font-size:13px;"></div>
      <div class="quote-modal-actions">
        <button type="button" id="quote-profile-edit-cancel">取消</button>
        <button type="button" class="quote-modal-save" id="quote-profile-edit-save">保存模板</button>
      </div>
    </div>
  </div>
</div>
"""
    script = """
const QUOTE_STALE_MINUTES = 30;
let _quoteProfileEditState = null;

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
  actions.push(`<button type="button" data-quote-exception-harvest="${row.id}">人工整理</button>`);
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
let quoteExceptionState = {
  limit: 10,
  offset: 0,
  total: 0,
  openTotal: 0,
  handledTotal: 0,
  hasPrev: false,
  hasNext: false,
  resolutionStatus: 'open',
};

function currentQuoteFilters() {
  const form = document.querySelector('#quote-filter-form');
  return Object.fromEntries(new FormData(form).entries());
}

function renderQuoteBoard(rows, loadError = '') {
  const filteredRows = rows.filter((row) => quoteRowMatches(row, currentQuoteFilters()));
  document.querySelector('#quote-live-count').textContent = String(filteredRows.length);
  document.querySelector('#quote-source-count').textContent = String(new Set(filteredRows.map((row) => quoteSourceText(row))).size);
  if (loadError) {
    document.querySelector('#quote-board-range').textContent = `报价墙加载失败: ${loadError}`;
    document.querySelector('#quote-filter-status').textContent = '主屏渲染已降级；其他工作面不受影响，点“刷新”可重试。';
    document.querySelector('#quote-board-table tbody').innerHTML = `<tr><td colspan="12" class="muted">报价墙加载失败: ${textValue(loadError, '未知错误')}</td></tr>`;
    bindQuoteRankingButtons();
    bindQuoteDeleteButtons();
    return;
  }
  document.querySelector('#quote-board-range').textContent = filteredRows.length
    ? `主屏已加载 ${filteredRows.length} 个 SKU 的当前最高价，最新信号时刻 ${latestQuoteTime(filteredRows) || '—'}。`
    : '当前主屏没有可用报价。';
  document.querySelector('#quote-filter-status').textContent = filteredRows.length
    ? `当前显示的是每个精确 SKU 的主屏最高价；离散面额和区间分开，变动列展示该来源群最新一笔是涨还是跌。`
    : '没有匹配的报价。';
  document.querySelector('#quote-board-table tbody').innerHTML = filteredRows.length
    ? filteredRows.map((row) => `
      <tr>
        <td><span class="table-primary">${textValue(row.card_type)}</span><span class="table-secondary">${textValue(row.parser_template || row.parser_version || '标准解析')}</span></td>
        <td><span class="table-primary">${quoteCountryText(row)}</span><span class="table-secondary">${textValue(row.country_or_currency || row.currency || row.region || '标准地区')}</span></td>
        <td><span class="table-primary">${quoteAmountText(row)}</span><span class="table-secondary">${textValue(row.multiplier ? `倍数 ${row.multiplier}` : row.source_line || '精确 SKU')}</span></td>
        <td><span class="table-primary">${quoteFormFactorText(row.form_factor || row.quote_form_factor)}</span></td>
        <td><span class="table-num">${compactNumber(row.price ?? row.rate ?? row.quote_price ?? '')}</span></td>
        <td><span class="quote-change-chip ${quoteChangeClass(row.change_status)}">${quoteChangeText(row)}</span></td>
        <td><span class="table-primary">${quoteSourceText(row)}</span><span class="quote-source-detail">${textValue(row.source_name || row.sender_id)} / ${quoteSourceDetailText(row)}</span></td>
        <td><span class="table-primary">${formatQuoteTime(row.updated_at || row.effective_at || row.created_at || row.message_time || row.received_at)}</span><span class="table-secondary">${textValue(row.message_id || '—')}</span></td>
        <td class="${quoteAgeClass(row)}">${quoteAgeText(row.effective_at || row.message_time || row.created_at || row.updated_at || row.received_at)}</td>
        <td><span class="quote-status-chip ${quoteDisplayStatusClass(row)}">${quoteDisplayStatusText(row)}</span></td>
        <td class="quote-note">${quoteRestrictionText(row)}</td>
        <td><div class="action-row"><button type="button" class="action-ghost" data-quote-ranking-id="${row.id}">深度</button><button type="button" class="action-danger quote-delete-btn" data-quote-delete-id="${row.id}">删除</button></div></td>
      </tr>
    `).join('')
    : '<tr><td colspan="12" class="muted">暂无可用报价</td></tr>';
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
  document.querySelector('#quote-ranking-table tbody').innerHTML = '<tr><td colspan="7" class="muted">正在加载同 SKU 来源深度</td></tr>';
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
    : '<tr><td colspan="7" class="muted">没有同 SKU 来源深度数据</td></tr>';
}

function closeQuoteRankingModal() {
  document.querySelector('#quote-ranking-modal').classList.remove('open');
  document.querySelector('#quote-ranking-modal').setAttribute('aria-hidden', 'true');
}

function renderQuoteProfiles(rows, loadError = '') {
  allQuoteProfiles = rows || [];
  if (loadError) {
    document.querySelector('#quote-profile-table tbody').innerHTML =
      `<tr><td colspan="11" class="muted">模板列表加载失败: ${textValue(loadError, '未知错误')}</td></tr>`;
    return;
  }
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
        <td><button type="button" data-quote-profile-edit="${escapeHtml(String(row.id || ''))}">编辑模板</button> <button type="button" data-quote-profile-delete="${escapeHtml(String(row.id || ''))}" style="color:#c0392b;border-color:#c0392b">删除模板</button></td>
      </tr>
    `).join('')
    : '<tr><td colspan="11" class="muted">暂无模板配置</td></tr>';
  bindQuoteProfileButtons();
}

function quoteRowsForProfile(row) {
  return (allQuoteRows || []).filter((item) =>
    String(item.platform || '') === String(row.platform || '')
    && (
      String(item.source_group_key || '') === String(row.source_group_key || '')
      || String(item.chat_id || '') === String(row.chat_id || '')
    )
  );
}

function parseGroupParserConfig(rawConfig) {
  const text = String(rawConfig || '').trim();
  if (!text) return null;
  try {
    const parsed = JSON.parse(text);
    if (String(parsed.version || '') !== 'group-parser-v1' || !Array.isArray(parsed.sections)) {
      return null;
    }
    return parsed;
  } catch (error) {
    return null;
  }
}

function groupParserSectionCards(row) {
  const parsed = parseGroupParserConfig(row.template_config || '');
  if (!parsed) return [];
  return parsed.sections.map((section, index) => {
    const defaults = section.defaults || {};
    const quoteLines = Array.isArray(section.lines) ? section.lines.filter((item) => item.kind === 'quote') : [];
    const firstPattern = quoteLines.length ? String(quoteLines[0].pattern || '').trim() : '';
    return {
      index,
      label: String(section.label || defaults.card_type || `骨架${index + 1}`).trim() || `骨架${index + 1}`,
      priority: Number(section.priority || (index + 1) * 10),
      quote_count: quoteLines.length,
      country_or_currency: String(defaults.country_or_currency || '').trim(),
      form_factor: String(defaults.form_factor || '').trim() || '不限',
      first_pattern: firstPattern,
    };
  });
}

function groupParserConfigToFixedTemplate(row) {
  const rawConfig = String(row.template_config || '').trim();
  if (!rawConfig) return '';
  const parsed = parseGroupParserConfig(rawConfig);
  if (!parsed) return rawConfig;
  const latestRows = quoteRowsForProfile(row);
  const lines = [];
  const sections = parsed.sections.slice();
  sections.forEach((section, sectionIndex) => {
    const defaults = section.defaults || {};
    const defaultCountry = String(defaults.country_or_currency || '').trim();
    const defaultForm = String(defaults.form_factor || '').trim() || '不限';
    const defaultCard = String(defaults.card_type || section.label || '').trim() || '未知';
    if (lines.length) lines.push('');
    lines.push(`# 骨架 ${sectionIndex + 1} / ${sections.length}`);
    lines.push('[默认]');
    if (defaultCountry) lines.push(`国家 / 币种=${defaultCountry}`);
    lines.push(`形态=${defaultForm}`);
    lines.push('');
    lines.push(`[${defaultCard}]`);
    const quoteLines = Array.isArray(section.lines) ? section.lines.filter((item) => item.kind === 'quote') : [];
    for (const line of quoteLines) {
      const outputs = line.outputs || {};
      const amountRange = String(outputs.amount_range || '').trim();
      const country = String(outputs.country_or_currency || '').trim();
      const formFactor = String(outputs.form_factor || defaultForm).trim() || defaultForm;
      const cardType = String(outputs.card_type || defaultCard).trim() || defaultCard;
      const latest = latestRows.find((quoteRow) =>
        String(quoteRow.card_type || '') === cardType
        && String(quoteRow.country_or_currency || '') === country
        && normalizeFormFactorText(quoteRow.form_factor || '') === normalizeFormFactorText(formFactor)
        && String(quoteRow.amount_range || '') === amountRange
      );
      const priceText = latest ? compactNumber(latest.price) : '?';
      const label = amountRange || country || '未知';
      lines.push(`${label}=${priceText}`);
    }
  });
  return lines.join('\\n').trim();
}

function fixedTemplateToGroupParserConfig(templateText, existingConfigText) {
  let existing;
  try {
    existing = JSON.parse(String(existingConfigText || ''));
  } catch (error) {
    throw new Error('当前模板不是有效 JSON，不能用固定格式编辑。');
  }
  if (String(existing.version || '') !== 'group-parser-v1' || !Array.isArray(existing.sections)) {
    throw new Error('当前模板不是 group-parser-v1，暂不支持固定格式编辑。');
  }

  const blocks = [];
  let pendingDefaults = { country_or_currency: '', form_factor: '不限' };
  let activeDefaults = { ...pendingDefaults };
  let currentCard = null;
  for (const rawLine of String(templateText || '').split('\\n')) {
    const line = normalizeQuoteLineForUi(rawLine);
    if (!line) continue;
    if (/^#\\s*骨架\\s+\\d+/i.test(line) || /^\\/\\//.test(line)) continue;
    const blockMatch = line.match(/^\\[(.+)\\]$/);
    if (blockMatch) {
      const blockName = String(blockMatch[1] || '').trim();
      if (blockName === '默认') {
        currentCard = null;
        pendingDefaults = { ...activeDefaults };
        continue;
      }
      currentCard = {
        card_type: blockName,
        defaults: { ...pendingDefaults },
        quotes: [],
      };
      activeDefaults = { ...currentCard.defaults };
      blocks.push(currentCard);
      continue;
    }
    if (!currentCard) {
      const separator = line.includes('=') ? '=' : (line.includes(':') ? ':' : '');
      if (!separator) continue;
      const [rawKey, rawValue] = line.split(separator, 2);
      const key = String(rawKey || '').replace(/\\s+/g, '').toLowerCase();
      const value = String(rawValue || '').trim();
      if (key === '国家/币种' || key === '国家/币种'.replace(/\\s+/g, '').toLowerCase() || key === 'country/currency') {
        pendingDefaults.country_or_currency = value;
      } else if (key === '形态') {
        pendingDefaults.form_factor = value || '不限';
      }
      continue;
    }
    const separator = line.includes('=') ? '=' : (line.includes(':') ? ':' : '');
    if (!separator) continue;
    const [label, price] = line.split(separator, 2);
    currentCard.quotes.push({
      label: String(label || '').trim(),
      price_text: String(price || '').trim(),
    });
  }

  const existingSections = existing.sections.filter((section) => section && section.enabled !== false);
  if (blocks.length !== existingSections.length) {
    throw new Error(`固定格式里有 ${blocks.length} 段，但当前模板有 ${existingSections.length} 套骨架；请先在异常区重建，不要直接改这里。`);
  }

  const nextConfig = {
    ...existing,
    sections: existing.sections.map((section, index) => {
      const block = blocks[index];
      const quoteLines = Array.isArray(section.lines) ? section.lines.filter((item) => item.kind === 'quote') : [];
      if (block.quotes.length !== quoteLines.length) {
        throw new Error(`第 ${index + 1} 套骨架报价行数量不一致；这里暂时只支持修改现有模板，不支持增删行。`);
      }
      const nextDefaults = {
        ...(section.defaults || {}),
        card_type: block.card_type || section.defaults?.card_type || '',
        country_or_currency: block.defaults.country_or_currency || section.defaults?.country_or_currency || '',
        form_factor: block.defaults.form_factor || section.defaults?.form_factor || '不限',
      };
      let quoteCursor = 0;
      const nextLines = (section.lines || []).map((line) => {
        if (line.kind !== 'quote') return line;
        const quote = block.quotes[quoteCursor++];
        const label = String(quote.label || '').trim();
        const normalizedLabel = label.replace(/\\s+/g, '');
        const looksAmount = /^[0-9]+(?:[\\/-][0-9]+)*$/.test(normalizedLabel);
        return {
          ...line,
          outputs: {
            ...(line.outputs || {}),
            card_type: block.card_type || line.outputs?.card_type || nextDefaults.card_type,
            country_or_currency: looksAmount ? (nextDefaults.country_or_currency || line.outputs?.country_or_currency || '') : label,
            form_factor: nextDefaults.form_factor || line.outputs?.form_factor || '不限',
            amount_range: looksAmount ? label : (line.outputs?.amount_range || '不限'),
          },
        };
      });
      return {
        ...section,
        label: block.card_type || section.label,
        defaults: nextDefaults,
        lines: nextLines,
      };
    }),
  };
  return JSON.stringify(nextConfig);
}

function bindQuoteProfileButtons() {
  document.querySelectorAll('[data-quote-profile-edit]').forEach((button) => {
    button.addEventListener('click', () => {
      const targetId = String(button.dataset.quoteProfileEdit || '');
      const row = allQuoteProfiles.find((item) => String(item.id || '') === targetId);
      if (row) {
        openQuoteProfileEditModal(row);
      }
    });
  });
  document.querySelectorAll('[data-quote-profile-delete]').forEach((button) => {
    button.addEventListener('click', async () => {
      const targetId = String(button.dataset.quoteProfileDelete || '');
      const row = allQuoteProfiles.find((item) => String(item.id || '') === targetId);
      if (!row) return;
      if (!confirm(`确定删除模板？\\n${row.chat_name || row.chat_id || '未知群'} / ${row.chat_id || ''}`)) {
        return;
      }
      const adminPassword = prompt('请输入报价管理密码，确认删除模板');
      if (adminPassword === null) return;
      const resp = await fetch('/api/quotes/group-profiles/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: Number(targetId),
          admin_password: adminPassword,
        }),
      });
      const data = await resp.json();
      if (data.error) {
        alert(`删除失败: ${data.error}`);
        return;
      }
      if (!data.deleted) {
        alert('删除失败: 没找到这条模板');
        return;
      }
      if (_quoteProfileEditState && String(_quoteProfileEditState.id || '') === targetId) {
        closeQuoteProfileEditModal();
      }
      await loadQuotesData();
      alert('模板已删除。');
    });
  });
}

function closeQuoteProfileEditModal() {
  const modal = document.querySelector('#quote-profile-edit-modal');
  modal.classList.remove('open');
  modal.setAttribute('aria-hidden', 'true');
  _quoteProfileEditState = null;
}

function openQuoteProfileEditModal(row) {
  const fixedTemplateText = groupParserConfigToFixedTemplate(row);
  _quoteProfileEditState = {
    id: row.id || '',
    platform: row.platform || 'whatsapp',
    chat_id: row.chat_id || '',
    chat_name: row.chat_name || row.chat_id || '',
    default_card_type: row.default_card_type || '',
    default_country_or_currency: row.default_country_or_currency || '',
    default_form_factor: row.default_form_factor || '不限',
    default_multiplier: row.default_multiplier || '',
    parser_template: row.parser_template || '',
    stale_after_minutes: String(row.stale_after_minutes || '30'),
    note: row.note || '',
    template_config: row.template_config || '',
    fixed_template_text: fixedTemplateText,
    profile_id: row.id || '',
  };
  const modal = document.querySelector('#quote-profile-edit-modal');
  modal.classList.add('open');
  modal.setAttribute('aria-hidden', 'false');
  document.querySelector('#quote-profile-edit-subtitle').textContent =
    `${row.chat_name || row.chat_id || '未知群'} / ${row.chat_id || ''} / 当前共有 ${safeSectionCount(row.template_config)} 套骨架`;
  renderQuoteProfileEditModal();
}

function safeSectionCount(templateConfigText) {
  try {
    const parsed = JSON.parse(String(templateConfigText || ''));
    return Array.isArray(parsed.sections) ? parsed.sections.length : 0;
  } catch (error) {
    return 0;
  }
}

function renderQuoteProfileEditModal() {
  if (!_quoteProfileEditState) return;
  const body = document.querySelector('#quote-profile-edit-body');
  const currentRow = allQuoteProfiles.find((item) => String(item.id || '') === String(_quoteProfileEditState.id || '')) || {};
  const sectionCards = groupParserSectionCards(currentRow);
  const sectionCardsHtml = sectionCards.length
    ? `
      <div style="grid-column:1 / -1;">
        <div class="muted" style="margin-bottom:8px;">当前群专用解析器共有 ${sectionCards.length} 套骨架，按优先级从低到高展示。你现在编辑的是这一整个群模板，不是单独某一条报价。</div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px;">
          ${sectionCards.map((card) => `
            <div style="border:1px solid #d8e2f0;border-radius:8px;padding:10px;background:#f8fbff;">
              <div style="font-weight:700;">骨架 ${card.index + 1}</div>
              <div class="muted" style="margin-top:4px;">卡种: ${escapeHtml(card.label)}</div>
              <div class="muted">默认: ${escapeHtml(card.country_or_currency || '—')} / ${escapeHtml(card.form_factor || '不限')}</div>
              <div class="muted">报价行: ${card.quote_count} 条 / 优先级 ${card.priority}</div>
              <div style="margin-top:6px;font-family:monospace;font-size:12px;white-space:pre-wrap;">${escapeHtml(card.first_pattern || '暂无报价 pattern')}</div>
            </div>
          `).join('')}
        </div>
      </div>
    `
    : '';
  body.innerHTML = `
    <div class="quote-filter-grid" style="grid-template-columns:repeat(2,minmax(0,1fr));display:grid;gap:10px;">
      <input data-profile-edit-field="platform" value="${escapeHtml(_quoteProfileEditState.platform)}" placeholder="平台" />
      <input data-profile-edit-field="chat_id" value="${escapeHtml(_quoteProfileEditState.chat_id)}" placeholder="群ID / chat_id" />
      <input data-profile-edit-field="chat_name" value="${escapeHtml(_quoteProfileEditState.chat_name)}" placeholder="群名" />
      <input data-profile-edit-field="default_card_type" value="${escapeHtml(_quoteProfileEditState.default_card_type)}" placeholder="默认卡种" />
      <input data-profile-edit-field="default_country_or_currency" value="${escapeHtml(_quoteProfileEditState.default_country_or_currency)}" placeholder="默认国家 / 币种" />
      <input data-profile-edit-field="default_form_factor" value="${escapeHtml(_quoteProfileEditState.default_form_factor)}" placeholder="默认形态" />
      <input data-profile-edit-field="default_multiplier" value="${escapeHtml(_quoteProfileEditState.default_multiplier)}" placeholder="默认倍数" />
      <input data-profile-edit-field="parser_template" value="${escapeHtml(_quoteProfileEditState.parser_template)}" placeholder="模板类型" />
      <input data-profile-edit-field="stale_after_minutes" value="${escapeHtml(_quoteProfileEditState.stale_after_minutes)}" placeholder="超时分钟" />
      <input data-profile-edit-field="note" value="${escapeHtml(_quoteProfileEditState.note)}" placeholder="备注" />
      ${sectionCardsHtml}
      <textarea data-profile-edit-field="fixed_template_text" style="grid-column:1 / -1;min-height:320px;font-family:monospace;" placeholder="固定格式模板">${escapeHtml(_quoteProfileEditState.fixed_template_text)}</textarea>
      <details style="grid-column:1 / -1;">
        <summary class="muted" style="cursor:pointer;">查看原始模板 JSON</summary>
        <textarea data-profile-edit-field="template_config" style="margin-top:8px;min-height:220px;font-family:monospace;">${escapeHtml(_quoteProfileEditState.template_config)}</textarea>
      </details>
    </div>
  `;
  document.querySelector('#quote-profile-edit-summary').textContent = '固定格式优先；按“骨架 1 / N、骨架 2 / N”顺序编辑已有模板。这里只适合改已有骨架的卡种、国家/币种、形态和面额标签，不适合增删骨架。';
  document.querySelectorAll('[data-profile-edit-field]').forEach((node) => {
    node.addEventListener('input', (event) => {
      _quoteProfileEditState[event.target.dataset.profileEditField] = event.target.value;
    });
  });
}

function renderQuoteInquiries(rows, loadError = '') {
  allQuoteInquiries = rows || [];
  if (loadError) {
    document.querySelector('#quote-inquiry-table tbody').innerHTML =
      `<tr><td colspan="8" class="muted">短回复上下文加载失败: ${textValue(loadError, '未知错误')}</td></tr>`;
    return;
  }
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

function quoteExceptionHarvestStatus(row) {
  const status = String(row.resolution_status || row.status || 'open').toLowerCase();
  const note = String(row.resolution_note || '');
  if (note.includes('result_saved')) {
    return '已整理，模板待应用';
  }
  if (note.includes('harvested') && note.includes('replayed=true')) {
    return '已整理，候选重放已生成';
  }
  if (note.includes('harvested') && note.includes('replayed=false')) {
    return '已整理，未生成候选重放';
  }
  if (status === 'open') {
    return '待整理';
  }
  if (status === 'ignored') {
    return '已忽略';
  }
  return quoteStatusText(status);
}

function quoteSnapshotDecisionLabel(decision) {
  const normalized = String(decision || 'unresolved');
  if (normalized === 'full_snapshot') return '整版快照';
  if (normalized === 'delta_update') return '局部更新';
  return '未决';
}

function quoteSnapshotSummary(row) {
  const snapshot = row && row.snapshot_decision ? row.snapshot_decision : {};
  const systemHypothesis = quoteSnapshotDecisionLabel(snapshot.system_hypothesis || 'unresolved');
  const resolvedDecision = quoteSnapshotDecisionLabel(snapshot.resolved_decision || 'unresolved');
  const confirmedBy = textValue(snapshot.confirmed_by || '');
  const confirmedAt = textValue(snapshot.confirmed_at || '');
  let summary = `系统候选：${systemHypothesis} ｜ 当前决策：${resolvedDecision}`;
  if (snapshot.resolved_decision && snapshot.resolved_decision !== 'unresolved') {
    summary += confirmedBy !== '—'
      ? ` ｜ 确认人：${confirmedBy}`
      : '';
    summary += confirmedAt !== '—'
      ? ` ｜ 确认时间：${confirmedAt}`
      : '';
  }
  summary += ' ｜ 仅记录语义，未改动报价墙。';
  return summary;
}

function displayQuoteResolutionNote(note) {
  const text = String(note || '');
  const lines = text.split('\\n');
  if (lines[0] && lines[0].startsWith('quote_exception_suppression:')) {
    lines.shift();
  }
  return lines.join('\\n').trim();
}

function bindQuoteExceptionPagination() {
  const prevButton = document.querySelector('#quote-exception-prev');
  const nextButton = document.querySelector('#quote-exception-next');
  const toggleButton = document.querySelector('#quote-exception-toggle');
  prevButton.disabled = !quoteExceptionState.hasPrev;
  nextButton.disabled = !quoteExceptionState.hasNext;
  toggleButton.textContent = quoteExceptionState.resolutionStatus === 'open' ? '查看已处理' : '只看待处理';
  prevButton.onclick = async () => {
    if (!quoteExceptionState.hasPrev) return;
    quoteExceptionState.offset = Math.max(0, quoteExceptionState.offset - quoteExceptionState.limit);
    await loadQuotesData();
  };
  nextButton.onclick = async () => {
    if (!quoteExceptionState.hasNext) return;
    quoteExceptionState.offset += quoteExceptionState.limit;
    await loadQuotesData();
  };
  toggleButton.onclick = async () => {
    quoteExceptionState.resolutionStatus = quoteExceptionState.resolutionStatus === 'open' ? 'all' : 'open';
    quoteExceptionState.offset = 0;
    await loadQuotesData();
  };
}

function renderQuoteExceptions(payload) {
  if (payload?._load_error) {
    quoteExceptionState = {
      ...quoteExceptionState,
      hasPrev: false,
      hasNext: false,
    };
    document.querySelector('#quote-exception-count').textContent = '0';
    document.querySelector('#quote-exception-range').textContent = `异常区加载失败: ${payload._load_error}`;
    document.querySelector('#quote-exception-page-status').textContent = '异常区暂不可用';
    document.querySelector('#quote-exception-cards').innerHTML =
      `<div class="muted" style="padding:12px;">异常区加载失败: ${textValue(payload._load_error, '未知错误')}</div>`;
    bindQuoteExceptionPagination();
    return;
  }
  const rows = Array.isArray(payload?.rows) ? payload.rows : [];
  quoteExceptionState = {
    ...quoteExceptionState,
    limit: Number(payload?.limit || quoteExceptionState.limit || 10),
    offset: Number(payload?.offset || 0),
    total: Number(payload?.total || 0),
    openTotal: Number(payload?.open_total || 0),
    handledTotal: Number(payload?.handled_total || 0),
    hasPrev: Boolean(payload?.has_prev),
    hasNext: Boolean(payload?.has_next),
    resolutionStatus: String(payload?.resolution_status || quoteExceptionState.resolutionStatus || 'open'),
  };
  document.querySelector('#quote-exception-count').textContent = String(quoteExceptionState.openTotal);
  const pageStart = rows.length ? quoteExceptionState.offset + 1 : 0;
  const pageEnd = quoteExceptionState.offset + rows.length;
  document.querySelector('#quote-exception-range').textContent = quoteExceptionState.openTotal
    ? `待处理总数 ${quoteExceptionState.openTotal} 条；已处理 ${quoteExceptionState.handledTotal} 条。`
    : '当前没有待处理异常。';
  document.querySelector('#quote-exception-page-status').textContent = rows.length
    ? `当前显示 ${pageStart}-${pageEnd} / ${quoteExceptionState.total}（${quoteExceptionState.resolutionStatus === 'open' ? '待处理' : '全部'}）`
    : `当前没有${quoteExceptionState.resolutionStatus === 'open' ? '待处理' : ''}异常。`;
  const container = document.querySelector('#quote-exception-cards');
  if (!rows.length) {
    container.innerHTML = `<div class="muted" style="padding:12px;">当前没有${quoteExceptionState.resolutionStatus === 'open' ? '待处理' : ''}异常。</div>`;
    bindQuoteExceptionPagination();
    return;
  }
  const renderExceptionCard = (row) => {
    const status = String(row.resolution_status || row.status || 'open').toLowerCase();
    const sourceLines = String(row.source_line || '').split('\\n').filter(Boolean);
    const linesHtml = sourceLines.map((line, idx) => {
      const escaped = line.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      return `<div class="exc-line" data-exc-id="${row.id}" data-line-idx="${idx}">${escaped}</div>`;
    }).join('');
    const note = displayQuoteResolutionNote(row.resolution_note);
    const noteHtml = note ? `<div class="muted" style="font-size:12px;margin-top:4px;white-space:pre-wrap;">${textValue(note)}</div>` : '';
    const snapshotHtml = row.quote_document_id
      ? `<div class="muted" style="font-size:12px;margin-top:6px;">${quoteSnapshotSummary(row)}</div>`
      : '';
    const snapshotActions = row.quote_document_id
      ? `
          <button type="button" class="action-ghost" data-quote-snapshot-confirm="${row.id}" data-quote-snapshot-decision="full_snapshot">确认整版</button>
          <button type="button" class="action-ghost" data-quote-snapshot-confirm="${row.id}" data-quote-snapshot-decision="delta_update">确认局部</button>
        `
      : '';
    return `<div class="exc-card" data-exc-row-id="${row.id}">
      <div class="exc-card-header">
        <div>
          <strong>${textValue(row.source_group_name || row.chat_name || row.source_group_key)}</strong>
          <div class="exc-card-meta">
            <span class="muted">${textValue(row.sender_id)}</span>
            <span class="muted">${formatQuoteTime(row.message_time || row.created_at)}</span>
            <span class="quote-status-chip ${quoteStatusClass(status)}">${quoteStatusText(status)}</span>
          </div>
        </div>
        <div class="exc-card-actions">
          ${snapshotActions}
          <button type="button" class="action-ghost" data-quote-exception-harvest="${row.id}">人工整理</button>
          <button type="button" class="action-danger" data-quote-exception-ignore="${row.id}">忽略</button>
        </div>
      </div>
      <div class="exc-card-brief">
        <span>${quoteExceptionHarvestStatus(row)}</span>
        <span>${textValue(row.suggested_action || '直接把右侧整理成最终正确结果；不确定的不要上墙。')}</span>
      </div>
      <div class="exc-lines">${linesHtml}</div>
      ${snapshotHtml}
      ${noteHtml}
    </div>`;
  };
  container.innerHTML = rows.map((row) => renderExceptionCard(row)).join('');
  bindQuoteExceptionButtons();
  bindQuoteExceptionPagination();
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
  document.querySelectorAll('[data-quote-exception-harvest]').forEach((button) => {
    button.addEventListener('click', () => {
      const row = allQuoteExceptions.find((item) => String(item.id) === String(button.dataset.quoteExceptionHarvest));
      if (row) openQuoteHarvestModal(row);
    });
  });
  document.querySelectorAll('[data-quote-snapshot-confirm]').forEach((button) => {
    button.addEventListener('click', async () => {
      const row = allQuoteExceptions.find((item) => String(item.id) === String(button.dataset.quoteSnapshotConfirm));
      if (!row || !row.quote_document_id) return;
      const adminPassword = window.prompt('输入报价管理员密码以记录快照判定');
      if (!adminPassword) return;
      const response = await fetch('/api/quotes/snapshot-decision/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          quote_document_id: Number(row.quote_document_id),
          resolved_decision: String(button.dataset.quoteSnapshotDecision || ''),
          admin_password: adminPassword,
        }),
      });
      const payload = await response.json();
      if (!response.ok) {
        alert(payload.error || '快照判定记录失败');
        return;
      }
      alert(payload.status_text || '快照判定已记录，未改动报价墙。');
      await loadQuotesData();
    });
  });
}

// ---------------------------------------------------------------------------
// Quote Harvest Modal
// ---------------------------------------------------------------------------
let _quoteHarvestState = null;
let _quoteHarvestPreviewToken = 0;

function escapeHtml(value) {
  return String(value || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function normalizeQuoteLineForUi(line) {
  let text = String(line || '');
  text = text
    .replace(/（/g, '(')
    .replace(/）/g, ')')
    .replace(/＝/g, '=')
    .replace(/：/g, ':')
    .replace(/\u3000/g, ' ');
  text = text.replace(/\\s*=\\s*/g, '=');
  text = text.replace(/\\s*:\\s*/g, ':');
  text = text.replace(/ {2,}/g, ' ');
  return text.trim();
}

function isQuoteCandidateLine(line) {
  const normalized = normalizeQuoteLineForUi(line);
  if (!normalized || !/\\d/.test(normalized)) return false;
  const lowered = normalized.toLowerCase();
  if (lowered.includes('wechat') || lowered.includes('whatsapp') || lowered.includes('recommend friends')) return false;
  return /[=:￥¥]/.test(normalized) || normalized.includes('收') || lowered.includes('ask') || normalized.includes('暂停') || lowered.includes('task');
}

function quoteHarvestRawLooksComplex(rawLines) {
  const meaningfulLines = (rawLines || []).filter((item) => item.normalized);
  const separatorCount = meaningfulLines.filter((item) => /={3,}|-{3,}|【.+】|快卡|不限购/.test(item.normalized)).length;
  const quoteLineCount = meaningfulLines.filter((item) => item.quoteCandidate).length;
  const countryTokens = ['英国', '德国', '荷兰', '法国', '西班牙', '芬兰', '爱尔兰', '比利时', '意大利', '奥地利', '墨西哥', '南非', '巴西', 'CAD', 'GBP', 'USD'];
  const seenCountries = new Set();
  meaningfulLines.forEach((item) => {
    countryTokens.forEach((token) => {
      if (item.normalized.includes(token)) seenCountries.add(token);
    });
  });
  return separatorCount >= 2 || seenCountries.size >= 3 || (separatorCount >= 1 && quoteLineCount >= 5);
}

function quoteHarvestPreviewSuggestsHarvest(preview, previewError = '') {
  const errors = [...(Array.isArray(preview?.errors) ? preview.errors : [])];
  if (previewError) errors.push(previewError);
  const unmatchedCount = errors.filter((item) => String(item).includes('原文里还有未吸收的报价行')).length;
  const missingCardTitleCount = errors.filter((item) => String(item).includes('没在原文里找到卡种标题')).length;
  return unmatchedCount >= 3 || missingCardTitleCount >= 2;
}

function quoteHarvestSuggestionActive() {
  return Boolean(_quoteHarvestState && (_quoteHarvestState.suggestedByRaw || _quoteHarvestState.suggestedByPreview));
}

function closeQuoteHarvestModal() {
  const modal = document.querySelector('#quote-harvest-modal');
  modal.classList.remove('open');
  modal.setAttribute('aria-hidden', 'true');
  _quoteHarvestState = null;
  document.querySelector('#quote-harvest-admin-password').value = '';
}

function currentHarvestProfile(row) {
  return allQuoteProfiles.find((item) =>
    String(item.platform || 'whatsapp') === sourcePlatform(row)
    && String(item.chat_id || '') === String(row.chat_id || '')
  ) || null;
}

function createHarvestRow() {
  return {
    source_line_index: '',
    amount: '',
    price: '',
    country_or_currency: '',
    form_factor: '',
  };
}

function currentResultState() {
  return _quoteHarvestState?.result || null;
}

function currentSectionHarvestState() {
  return _quoteHarvestState?.harvest || null;
}

function rememberHarvestScroll() {
  const harvest = currentSectionHarvestState();
  if (!harvest) return;
  const node = document.querySelector('#quote-harvest-lines');
  if (!node) return;
  harvest.scrollTop = node.scrollTop || 0;
}

function restoreHarvestScroll() {
  const harvest = currentSectionHarvestState();
  if (!harvest) return;
  const node = document.querySelector('#quote-harvest-lines');
  if (!node) return;
  const targetIndex = harvest.scrollAnchorIndex;
  const targetTop = Number(harvest.scrollTop || 0);
  window.requestAnimationFrame(() => {
    const latestNode = document.querySelector('#quote-harvest-lines');
    if (!latestNode) return;
    latestNode.scrollTop = targetTop;
    if (targetIndex === null || targetIndex === undefined || targetIndex === '') return;
    const targetLine = latestNode.querySelector(`[data-harvest-line="${Number(targetIndex)}"]`);
    if (targetLine) {
      targetLine.scrollIntoView({ block: 'center' });
    }
  });
}

function openQuoteHarvestModal(row) {
  const profile = currentHarvestProfile(row);
  const sharedResultState = {
    highlightedIndexes: [],
    editorText: '',
    editorDirty: false,
    preview: null,
    previewLoading: false,
    previewError: '',
  };
  const rawLines = String(row.raw_text || row.source_line || '').split('\\n').map((line, index) => ({
    index,
    raw: line,
    normalized: normalizeQuoteLineForUi(line),
    quoteCandidate: isQuoteCandidateLine(line),
  }));
  _quoteHarvestState = {
    row,
    rawLines,
    mode: String(profile?.parser_template || '') === 'supermarket-card' ? 'supermarket' : 'result',
    suggestedByRaw: quoteHarvestRawLooksComplex(rawLines),
    suggestedByPreview: false,
    result: sharedResultState,
    supermarket: sharedResultState,
    harvest: {
      activePane: 'edit',
      sectionStart: null,
      sectionEnd: null,
      defaults: {
        section_label: '',
        priority: '100',
        card_type: profile?.default_card_type || '',
        form_factor: profile?.default_form_factor || '不限',
        country_or_currency: profile?.default_country_or_currency || '',
      },
      rows: [],
      ignoredLineIndexes: [],
      activeRowIndex: null,
      preview: null,
      previewLoading: false,
      previewError: '',
      previewDirty: false,
      savedSections: 0,
      remainingLines: [],
      restrictionLinesAttached: [],
      handledLineIndexes: [],
      confirmedPreviewRows: [],
      lastSaveResult: null,
      completed: false,
      scrollTop: 0,
      scrollAnchorIndex: null,
    },
  };
  const modal = document.querySelector('#quote-harvest-modal');
  modal.classList.add('open');
  modal.setAttribute('aria-hidden', 'false');
  renderQuoteHarvestModal();
  requestQuoteResultPreview();
}

function setQuoteHarvestMode(mode) {
  if (!_quoteHarvestState || !_quoteHarvestState[mode]) return;
  _quoteHarvestState.mode = mode;
  renderQuoteHarvestModal();
  if ((mode === 'result' || mode === 'supermarket') && !currentResultState().preview && !currentResultState().previewLoading) {
    requestQuoteResultPreview();
  }
}

function harvestSelectedIndexes() {
  const harvest = currentSectionHarvestState();
  if (!harvest || harvest.sectionStart === null || harvest.sectionEnd === null) {
    return new Set();
  }
  const indexes = new Set();
  const start = Math.min(harvest.sectionStart, harvest.sectionEnd);
  const end = Math.max(harvest.sectionStart, harvest.sectionEnd);
  for (let i = start; i <= end; i++) indexes.add(i);
  return indexes;
}

function harvestBoundIndexSet() {
  const bound = new Set();
  for (const row of currentSectionHarvestState()?.rows || []) {
    if (row.source_line_index !== '' && row.source_line_index !== null && row.source_line_index !== undefined) {
      bound.add(Number(row.source_line_index));
    }
  }
  return bound;
}

function indexesForRemainingLines(rawLines, remainingLines) {
  const counts = new Map();
  for (const line of remainingLines || []) {
    const normalized = normalizeQuoteLineForUi(line);
    if (!normalized) continue;
    counts.set(normalized, (counts.get(normalized) || 0) + 1);
  }
  const indexes = new Set();
  for (const item of rawLines || []) {
    const count = counts.get(item.normalized) || 0;
    if (!item.normalized || count <= 0) continue;
    indexes.add(item.index);
    counts.set(item.normalized, count - 1);
  }
  return indexes;
}

function handledIndexesForRemainingLines(rawLines, remainingLines) {
  const remainingIndexes = indexesForRemainingLines(rawLines, remainingLines);
  const handled = [];
  for (const item of rawLines || []) {
    if (!item.normalized) continue;
    if (!remainingIndexes.has(item.index)) handled.push(item.index);
  }
  return handled;
}

function renderHarvestPreviewRowsTable(rows, emptyText) {
  const rowsHtml = Array.isArray(rows) && rows.length
    ? rows.map((item) => `
      <tr>
        <td>${textValue(item.card_type)}</td>
        <td>${textValue(item.country_or_currency)}</td>
        <td>${textValue(item.amount)}</td>
        <td>${quoteFormFactorText(item.form_factor)}</td>
        <td>${textValue(item.price)}</td>
      </tr>
    `).join('')
    : `<tr><td colspan="5" class="muted">${escapeHtml(emptyText)}</td></tr>`;
  return `
    <div class="table-wrap">
      <table class="quote-table">
        <thead><tr><th>卡种</th><th>国家 / 币种</th><th>面额</th><th>形态</th><th>价格</th></tr></thead>
        <tbody>${rowsHtml}</tbody>
      </table>
    </div>
  `;
}

function selectedHarvestItems() {
  const selectedIndexes = harvestSelectedIndexes();
  return (_quoteHarvestState?.rawLines || []).filter((item) => selectedIndexes.has(item.index));
}

function candidateHarvestQuoteItems() {
  const harvest = currentSectionHarvestState();
  const selected = selectedHarvestItems().filter((item) => item.normalized);
  const ignored = new Set((harvest?.ignoredLineIndexes || []).map((value) => Number(value)));
  const fromPreview = Array.isArray(harvest?.preview?.quote_candidates) && harvest.preview.quote_candidates.length
    ? harvest.preview.quote_candidates
        .map((item) => Number(item.source_line_index))
        .filter((index) => selected.some((line) => line.index === index) && !ignored.has(index))
        .map((index) => selected.find((line) => line.index === index))
        .filter(Boolean)
    : [];
  if (fromPreview.length) return fromPreview;
  return selected.filter((item) => item.quoteCandidate && !ignored.has(item.index));
}

function selectedRestrictionItems() {
  const harvest = currentSectionHarvestState();
  const selected = selectedHarvestItems().filter((item) => item.normalized);
  const ignored = new Set((harvest?.ignoredLineIndexes || []).map((value) => Number(value)));
  const fromPreview = Array.isArray(harvest?.preview?.restriction_candidates) && harvest.preview.restriction_candidates.length
    ? harvest.preview.restriction_candidates
        .map((item) => Number(item.source_line_index))
        .filter((index) => selected.some((line) => line.index === index) && !ignored.has(index))
        .map((index) => selected.find((line) => line.index === index))
        .filter(Boolean)
    : [];
  return fromPreview.length ? fromPreview : [];
}

function suggestHarvestSectionLabel() {
  const selected = selectedHarvestItems();
  const first = selected.find((item) => item.normalized && !/^\\d/.test(item.normalized));
  if (!first) return '';
  return first.normalized
    .replace(/^[=#\\s【】-]+/, '')
    .replace(/[=#\\s【】-]+$/g, '')
    .slice(0, 24);
}

function seedHarvestRowsFromSelection() {
  const harvest = currentSectionHarvestState();
  if (!harvest) return;
  const quoteItems = candidateHarvestQuoteItems();
  const existingIndexes = new Set((harvest.rows || [])
    .map((row) => row.source_line_index)
    .filter((value) => value !== '' && value !== null && value !== undefined)
    .map((value) => Number(value)));
  const nextRows = quoteItems
    .filter((item) => !existingIndexes.has(item.index))
    .map((item) => ({
      ...createHarvestRow(),
      source_line_index: item.index,
    }));
  if (!nextRows.length && harvest.rows.length) return;
  if (!harvest.rows.length) {
    harvest.rows = quoteItems.map((item) => ({
      ...createHarvestRow(),
      source_line_index: item.index,
    }));
  } else {
    harvest.rows.push(...nextRows);
  }
  harvest.activeRowIndex = harvest.rows.length ? 0 : null;
  markSectionHarvestDirty();
}

function translateHarvestError(error) {
  const text = String(error || '');
  if (!text) return '';
  if (text === 'missing_default_card_type') return '第 2 步还没填卡种。';
  if (text === 'missing_default_form_factor') return '第 2 步还没填形态。';
  if (text === 'no_quote_rows') return '第 3 步还没有报价行。先用“按选区自动生成报价行”，再补面额和价格。';
  if (/^row_\\d+_missing_source_line$/.test(text)) return '有报价行还没绑定原文。';
  if (/^row_\\d+_missing_amount_or_price$/.test(text)) return '有报价行还没填完面额或价格。';
  if (/^row_\\d+_source_out_of_section$/.test(text)) return '有报价行绑定到了选区外，请重新绑定。';
  if (/^row_\\d+_missing_fixed_fields$/.test(text)) return '段级固定信息还没补齐，请检查卡种、国家/币种、形态。';
  const duplicateMatch = text.match(/^duplicate_source_line_(\\d+)$/);
  if (duplicateMatch) return `原文第 ${Number(duplicateMatch[1]) + 1} 行被重复绑定了。`;
  return text;
}

function translateHarvestUnhandledReason(reason) {
  const text = String(reason || '');
  if (text === 'price_like_line_unhandled') return '像报价的原文还没录入到报价表。';
  return text;
}

function markSectionHarvestDirty() {
  const harvest = currentSectionHarvestState();
  if (!harvest) return;
  harvest.preview = null;
  harvest.previewError = '';
  harvest.previewDirty = true;
}

function markQuoteHarvestPreviewStale(mode) {
  const summary = document.querySelector('#quote-harvest-summary');
  const saveButton = document.querySelector('#quote-harvest-save');
  if (saveButton) saveButton.disabled = true;
  if (!summary) return;
  summary.textContent = mode === 'harvest'
    ? '内容已修改，请先重新预览这一段。'
    : '内容已修改，请重新生成预览。';
}

function harvestPayload() {
  const harvest = currentSectionHarvestState();
  if (!_quoteHarvestState || !harvest) return null;
  if (harvest.sectionStart === null || harvest.sectionEnd === null) return null;
  return {
    exception_id: _quoteHarvestState.row.id,
    section_start_line: Math.min(harvest.sectionStart, harvest.sectionEnd),
    section_end_line: Math.max(harvest.sectionStart, harvest.sectionEnd),
    defaults: harvest.defaults,
    rows: harvest.rows.map((row) => ({
      source_line_index: row.source_line_index,
      amount: row.amount,
      price: row.price,
      country_or_currency: row.country_or_currency,
      form_factor: row.form_factor,
    })),
    ignored_line_indexes: harvest.ignoredLineIndexes,
  };
}

async function requestQuoteHarvestPreview() {
  const harvest = currentSectionHarvestState();
  const payload = harvestPayload();
  if (!_quoteHarvestState || !harvest || !payload) {
    alert('请先选择一段 section');
    return;
  }
  const token = ++_quoteHarvestPreviewToken;
  harvest.previewLoading = true;
  harvest.previewError = '';
  renderQuoteHarvestModal();
  try {
    const resp = await fetch('/api/quotes/exceptions/harvest-preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await resp.json();
    if (!_quoteHarvestState || token !== _quoteHarvestPreviewToken) return;
    if (data.error) {
      harvest.preview = null;
      harvest.previewError = data.error;
    } else {
      harvest.preview = data;
      harvest.previewError = '';
      harvest.previewDirty = false;
      harvest.activePane = 'preview';
    }
  } catch (error) {
    if (_quoteHarvestState && token === _quoteHarvestPreviewToken) {
      harvest.preview = null;
      harvest.previewError = error.message;
    }
  } finally {
    if (_quoteHarvestState && token === _quoteHarvestPreviewToken) {
      harvest.previewLoading = false;
      if (_quoteHarvestState.mode === 'harvest') {
        renderQuoteHarvestModal();
      }
    }
  }
}

async function requestQuoteResultPreview() {
  const result = currentResultState();
  if (!_quoteHarvestState || !result) return;
  const token = ++_quoteHarvestPreviewToken;
  result.previewLoading = true;
  result.previewError = '';
  renderQuoteHarvestModal();
  try {
    const resp = await fetch('/api/quotes/exceptions/result-preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        exception_id: _quoteHarvestState.row.id,
        result_template_text: result.editorText || '',
        mode: _quoteHarvestState.mode || 'result',
      }),
    });
    const data = await resp.json();
    if (!_quoteHarvestState || token !== _quoteHarvestPreviewToken) return;
    if (data.error) {
      result.preview = null;
      result.previewError = data.error;
      _quoteHarvestState.suggestedByPreview = quoteHarvestPreviewSuggestsHarvest(null, data.error);
    } else {
      result.preview = data;
      result.previewError = '';
      _quoteHarvestState.suggestedByPreview = quoteHarvestPreviewSuggestsHarvest(data, '');
      if (!result.editorDirty || !String(result.editorText || '').trim()) {
        result.editorText = String(data.result_template_text || '');
      }
    }
  } catch (error) {
    if (_quoteHarvestState && token === _quoteHarvestPreviewToken) {
      result.preview = null;
      result.previewError = error.message;
      _quoteHarvestState.suggestedByPreview = quoteHarvestPreviewSuggestsHarvest(null, error.message);
    }
  } finally {
    if (_quoteHarvestState && token === _quoteHarvestPreviewToken) {
      result.previewLoading = false;
      if (_quoteHarvestState.mode === 'result' || _quoteHarvestState.mode === 'supermarket') {
        renderQuoteHarvestModal();
      }
    }
  }
}

function renderQuoteHarvestTabs() {
  const mode = _quoteHarvestState?.mode || 'result';
  const buttonStyle = (active) => `width:auto;flex:0 0 auto;padding:7px 12px;border-radius:999px;border:1px solid ${active ? 'rgba(243,165,47,0.22)' : 'rgba(243,165,47,0.12)'};background:${active ? 'linear-gradient(135deg,#3a2a0a,#6b4a12 42%,#f3a52f)' : 'rgba(10,15,20,0.92)'};color:${active ? '#120f08' : 'var(--ink-soft)'};font-weight:${active ? '700' : '600'};cursor:pointer;box-shadow:${active ? '0 6px 14px rgba(243,165,47,0.14)' : 'none'};font-size:13px;`;
  return `
    <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
      <button type="button" data-quote-harvest-mode="result" style="${buttonStyle(mode === 'result')}">标准模板整理</button>
      <button type="button" data-quote-harvest-mode="supermarket" style="${buttonStyle(mode === 'supermarket')}">超市卡</button>
      <button type="button" data-quote-harvest-mode="harvest" style="${buttonStyle(mode === 'harvest')}">分段收割</button>
      <span class="muted" style="font-size:12px;">标准模板整理保留主流程；超市卡适合超长混合报价；分段收割继续逐段整理。</span>
    </div>
  `;
}

function renderQuoteResultPane() {
  const result = currentResultState();
  const isSupermarketMode = _quoteHarvestState?.mode === 'supermarket';
  const preview = result?.preview;
  const highlightedIndexes = new Set((result?.highlightedIndexes || []).map((value) => Number(value)));
  const linesHtml = (_quoteHarvestState?.rawLines || []).map((item) => {
    const highlighted = highlightedIndexes.has(item.index);
    return `<div data-result-line="${item.index}" style="border:1px solid ${highlighted ? 'rgba(118,169,255,0.36)' : 'rgba(243,165,47,0.1)'};background:${highlighted ? 'rgba(118,169,255,0.12)' : 'rgba(8,12,16,0.84)'};border-radius:12px;padding:8px;cursor:pointer;">
      <div style="font-size:12px;color:var(--muted);margin-bottom:4px;">#${item.index + 1}</div>
      <div style="white-space:pre-wrap;font-family:monospace;font-size:13px;">${escapeHtml(item.normalized || item.raw || ' ')}</div>
    </div>`;
  }).join('');
  const previewRowsHtml = Array.isArray(preview?.preview_rows) && preview.preview_rows.length
    ? preview.preview_rows.map((item) => `
      <tr>
        <td>${textValue(item.card_type)}</td>
        <td>${textValue(item.country_or_currency)}</td>
        <td>${textValue(item.amount)}</td>
        <td>${quoteFormFactorText(item.form_factor)}</td>
        <td>${textValue(item.price)}</td>
      </tr>
    `).join('')
    : '<tr><td colspan="5" class="muted">暂无预览报价</td></tr>';
  const ignoredHtml = Array.isArray(preview?.notes) && preview.notes.length
    ? preview.notes.map((item) => `<div style="font-family:monospace;font-size:12px;white-space:pre-wrap;">${escapeHtml(item)}</div>`).join('')
    : '<div class="muted">未上墙的非价格文本会自动忽略。</div>';
  const warningsHtml = Array.isArray(preview?.warnings) && preview.warnings.length
    ? preview.warnings.map((item) => `<div style="font-size:12px;color:var(--gold);">${escapeHtml(item)}</div>`).join('')
    : '<div class="muted">暂无警告</div>';
  const errorsHtml = Array.isArray(preview?.errors) && preview.errors.length
    ? preview.errors.map((item) => `<div style="font-size:12px;color:var(--warn);">${escapeHtml(item)}</div>`).join('')
    : '<div class="muted">当前没有校验错误</div>';
  const suggestionHtml = quoteHarvestSuggestionActive()
    ? `<div style="border:1px solid rgba(243,165,47,0.16);background:linear-gradient(180deg,rgba(44,31,10,0.96),rgba(18,16,14,0.96));border-radius:14px;padding:10px 12px;">
        <div style="font-weight:700;color:var(--gold);margin-bottom:4px;">这条原文更适合分段收割</div>
        <div class="muted" style="font-size:12px;">当前原文包含多段或多国家结构；标准模板区仍可保留给主流单国家消息，复杂消息建议按段预览并保存。</div>
        <div style="margin-top:8px;"><button type="button" id="quote-harvest-switch-button">切换到分段收割</button></div>
      </div>`
    : '';
  return `
    ${suggestionHtml}
    <div class="quote-harvest-grid">
      <section class="panel quote-harvest-side primary">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
          <strong>原文区</strong>
          <div class="muted" style="font-size:12px;">点击行可高亮参考，不参与保存。</div>
        </div>
        <div class="quote-result-lines">${linesHtml}</div>
      </section>
      <section class="panel quote-harvest-side primary">
        <strong>${isSupermarketMode ? '超市卡模板区' : '结果模板区'}</strong>
        <div class="muted" style="font-size:12px;">${isSupermarketMode ? '适合超长、多卡种、多国家的混合报价。右侧写法不变，但保存时不受 3 套骨架上限。' : '只适合整洁单国家原文。固定块格式：只写 [默认] 和卡种块；默认里只填 国家 / 币种、形态；报价统一写成 50=5.3、10-195=5.25、100/150=5.43 这种格式。'}</div>
        <textarea id="quote-harvest-editor" style="min-height:280px;font-family:monospace;">${escapeHtml(result?.editorText || '')}</textarea>
        <div class="muted" style="font-size:12px;">示例：<br>[默认]<br>国家 / 币种=USD<br>形态=横白卡<br><br>[Apple]<br>50=5.3<br>10-195=5.25<br>100/150=5.43<br>200-450=5.44<br>300/400/500=5.45</div>
        <div><strong style="font-size:12px;">预览区</strong></div>
        <div>${result?.previewLoading ? '<div class="muted">预览计算中...</div>' : (result?.previewError ? `<div style="color:#c62828;">${escapeHtml(result.previewError)}</div>` : '')}</div>
        <div class="table-wrap">
          <table class="quote-table">
            <thead><tr><th>卡种</th><th>国家 / 币种</th><th>面额</th><th>形态</th><th>价格</th></tr></thead>
            <tbody>${previewRowsHtml}</tbody>
          </table>
        </div>
        <div>
          <strong style="font-size:12px;">自动忽略文本</strong>
          <div style="font-size:12px;white-space:pre-wrap;">${ignoredHtml}</div>
        </div>
        <div>
          <strong style="font-size:12px;">警告</strong>
          <div style="font-size:12px;white-space:pre-wrap;">${warningsHtml}</div>
        </div>
        <div>
          <strong style="font-size:12px;color:#c62828;">错误</strong>
          <div style="font-size:12px;white-space:pre-wrap;">${errorsHtml}</div>
        </div>
      </section>
    </div>
  `;
}

function renderQuoteSectionHarvestPane() {
  const harvest = currentSectionHarvestState();
  const preview = harvest?.preview;
  const activePane = harvest?.activePane || 'edit';
  const selectedIndexes = harvestSelectedIndexes();
  const boundIndexes = harvestBoundIndexSet();
  const ignoredIndexes = new Set((harvest?.ignoredLineIndexes || []).map((value) => Number(value)));
  const remainingIndexes = indexesForRemainingLines(_quoteHarvestState?.rawLines || [], harvest?.remainingLines || []);
  const handledIndexes = new Set((harvest?.handledLineIndexes || []).map((value) => Number(value)));
  const quoteCandidateIndexes = new Set((preview?.quote_candidates || []).map((item) => Number(item.source_line_index)));
  const restrictionCandidateIndexes = new Set((preview?.restriction_candidates || []).map((item) => Number(item.source_line_index)));
  const literalIndexes = new Set((preview?.non_quote_literals || []).map((item) => Number(item.source_line_index)));
  const linesHtml = (_quoteHarvestState?.rawLines || []).map((item) => {
    const selected = selectedIndexes.has(item.index);
    const bound = boundIndexes.has(item.index);
    const ignored = ignoredIndexes.has(item.index);
    const handled = handledIndexes.has(item.index);
    const remaining = remainingIndexes.has(item.index);
    let label = '普通文本';
    let badgeColor = 'rgba(143,138,121,0.18)';
    if (bound) {
      label = '已绑定';
      badgeColor = 'rgba(50,196,141,0.16)';
    } else if (ignored) {
      label = '已忽略';
      badgeColor = 'rgba(143,138,121,0.14)';
    } else if (selected) {
      label = '当前选区';
      badgeColor = 'rgba(118,169,255,0.18)';
    } else if (handled) {
      label = '已处理';
      badgeColor = 'rgba(50,196,141,0.14)';
    } else if (remaining) {
      label = '待处理';
      badgeColor = 'rgba(243,165,47,0.16)';
    } else if (restrictionCandidateIndexes.has(item.index)) {
      label = '说明';
      badgeColor = 'rgba(243,165,47,0.16)';
    } else if (quoteCandidateIndexes.has(item.index) || item.quoteCandidate) {
      label = '报价候选';
      badgeColor = 'rgba(118,169,255,0.18)';
    } else if (literalIndexes.has(item.index)) {
      label = '普通文本';
      badgeColor = 'rgba(143,138,121,0.18)';
    }
    const background = selected ? 'rgba(118,169,255,0.12)' : (handled ? 'rgba(50,196,141,0.08)' : 'rgba(8,12,16,0.84)');
    const border = selected ? 'rgba(118,169,255,0.36)' : (handled ? 'rgba(50,196,141,0.24)' : 'rgba(243,165,47,0.1)');
    return `<div data-harvest-line="${item.index}" style="border:1px solid ${border};background:${background};border-radius:12px;padding:8px;cursor:pointer;">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
        <strong style="font-size:12px;color:var(--muted);">#${item.index + 1}</strong>
        <span style="font-size:11px;padding:2px 6px;border-radius:999px;background:${badgeColor};color:var(--ink-soft);">${label}</span>
      </div>
      <div style="white-space:pre-wrap;font-family:monospace;font-size:13px;margin:6px 0 8px 0;">${escapeHtml(item.normalized || item.raw || ' ')}</div>
      <div style="display:flex;justify-content:flex-end;">
        <button type="button" data-harvest-ignore="${item.index}" style="font-size:11px;" ${selected ? '' : 'disabled'}>${ignored ? '取消忽略' : '忽略此行'}</button>
      </div>
    </div>`;
  }).join('');
  const quoteItems = candidateHarvestQuoteItems();
  const restrictionItems = selectedRestrictionItems();
  const selectedItems = selectedHarvestItems();
  const selectionSummary = selectedItems.length
    ? `已选第 ${Math.min(...selectedItems.map((item) => item.index)) + 1} - ${Math.max(...selectedItems.map((item) => item.index)) + 1} 行，共 ${selectedItems.length} 行`
    : '还没选 section';
  const rowsHtml = harvest?.rows?.length
    ? harvest.rows.map((row, idx) => `
      <div style="border:1px solid ${idx === harvest.activeRowIndex ? 'rgba(118,169,255,0.36)' : 'rgba(243,165,47,0.1)'};border-radius:12px;padding:10px;background:${idx === harvest.activeRowIndex ? 'rgba(118,169,255,0.12)' : 'rgba(8,12,16,0.84)'};">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:8px;">
          <strong>报价 ${idx + 1}</strong>
          <div style="display:flex;gap:8px;align-items:center;">
            <button type="button" data-harvest-bind-row="${idx}" style="font-size:12px;">${row.source_line_index === '' ? '去左边绑定原文' : `已绑第 ${Number(row.source_line_index) + 1} 行`}</button>
            <button type="button" data-harvest-delete-row="${idx}" style="color:#c0392b;font-size:12px;">删除</button>
          </div>
        </div>
        <div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;">
          <input data-harvest-row-field="${idx}:amount" value="${escapeHtml(row.amount)}" placeholder="面额，如 20-250" />
          <input data-harvest-row-field="${idx}:price" value="${escapeHtml(row.price)}" placeholder="价格，如 6.0" />
          <input data-harvest-row-field="${idx}:country_or_currency" value="${escapeHtml(row.country_or_currency)}" placeholder="国家覆盖，可空，大多数不用填" />
          <input data-harvest-row-field="${idx}:form_factor" value="${escapeHtml(row.form_factor)}" placeholder="形态覆盖，可空，大多数不用填" />
        </div>
      </div>
    `).join('')
    : '<div class="muted">第 3 步还没有报价行。先点“按选区自动生成报价行”，再补面额和价格。</div>';
  const confirmedPreviewRows = Array.isArray(harvest?.confirmedPreviewRows) ? harvest.confirmedPreviewRows : [];
  const currentPreviewRows = Array.isArray(preview?.preview_rows) ? preview.preview_rows : [];
  const combinedPreviewRows = [...confirmedPreviewRows, ...currentPreviewRows];
  const hasDraftRows = Array.isArray(harvest?.rows) && harvest.rows.some((row) =>
    String(row.source_line_index ?? '').trim() !== ''
    && String(row.amount || '').trim()
    && String(row.price || '').trim()
  );
  const staleNoQuoteRows = Boolean(
    hasDraftRows
    && Array.isArray(preview?.errors)
    && preview.errors.some((item) => String(item || '') === 'no_quote_rows')
  );
  const remainingHtml = Array.isArray(harvest?.remainingLines) && harvest.remainingLines.length
    ? harvest.remainingLines.map((line) => `<div style="font-size:12px;color:var(--gold);">${escapeHtml(line)}</div>`).join('')
    : '<div class="muted">没有剩余待处理行。</div>';
  const unhandledHtml = Array.isArray(preview?.unhandled_lines) && preview.unhandled_lines.length
    ? preview.unhandled_lines.map((item) => `<div style="color:var(--warn);">#${Number(item.source_line_index) + 1} ${escapeHtml(item.line)} (${escapeHtml(translateHarvestUnhandledReason(item.reason))})</div>`).join('')
    : '<div class="muted">当前选区没有未处理风险行。</div>';
  const errorHtml = staleNoQuoteRows
    ? '<div class="muted">当前已经录入了报价行，但预览结果已过期。请点“生成预览”重新计算。</div>'
    : harvest?.previewError
    ? `<div style="color:var(--warn);">${escapeHtml(harvest.previewError)}</div>`
    : (Array.isArray(preview?.errors) && preview.errors.length
      ? preview.errors.map((item) => `<div style="color:var(--warn);">${escapeHtml(translateHarvestError(item))}</div>`).join('')
      : (harvest?.previewDirty && hasDraftRows
        ? '<div class="muted">当前已经录入了报价行，请点“生成预览”重新计算。</div>'
        : '<div class="muted">先框一段、录入报价，再点“预览这一段”。</div>'));
  const latestText = preview
    ? (preview.is_latest_for_group ? '当前是该群最新消息：保存这一段时只推进本次选区；只有整条整理完成后才会按最新原文统一回放上墙。' : '当前不是该群最新消息：保存这一段后仅追加模板。')
    : '同一条异常可连续分段整理；每次只保存当前选中的 section。';
  const editPaneHtml = `
    <div class="quote-harvest-workspace-scroll quote-harvest-edit-pane">
      <div class="quote-harvest-step-compact">
        <strong>第 1 步：先选这一段</strong>
        <div class="muted" style="font-size:12px;">选区里识别到 ${quoteItems.length} 条报价候选，${restrictionItems.length} 条说明行。</div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <button type="button" id="quote-harvest-seed-rows" ${!quoteItems.length ? 'disabled' : ''}>按选区自动生成报价行</button>
          <button type="button" id="quote-harvest-add-row">手动新增一行</button>
        </div>
      </div>
      <section class="panel stack quote-harvest-side quote-harvest-fixed-section">
        <strong>第 2 步：补这一段的固定信息</strong>
        <div class="quote-filter-grid" style="grid-template-columns:repeat(2,minmax(0,1fr));">
          <input data-harvest-default="section_label" value="${escapeHtml(harvest?.defaults?.section_label || '')}" placeholder="段名，如 UK快卡" />
          <input data-harvest-default="card_type" value="${escapeHtml(harvest?.defaults?.card_type || '')}" placeholder="卡种，如 Apple" />
          <input data-harvest-default="country_or_currency" value="${escapeHtml(harvest?.defaults?.country_or_currency || '')}" placeholder="只有整段同一国家 / 币种才填" />
          <input data-harvest-default="form_factor" value="${escapeHtml(harvest?.defaults?.form_factor || '')}" placeholder="整段共用形态，如 横白卡" />
        </div>
        <div class="muted" style="font-size:12px;">这里只填这一整段都一样的东西。例子：UK快卡 这种整段同一币种时可以填 GBP；欧盟国家 这种每行国家都不同，就把“国家 / 币种”留空，不要忽略。卡种一般要填，形态如果整段都一样就填。</div>
      </section>
      <section class="panel stack quote-harvest-side quote-harvest-rows-section">
        <strong>第 3 步：确认报价行</strong>
        <div class="muted" style="font-size:12px;">先用“按选区自动生成报价行”，再把每行的面额和价格补上。国家覆盖、形态覆盖只有少数情况才需要填。</div>
        <div class="quote-harvest-rows-scroll">${rowsHtml}</div>
      </section>
    </div>
  `;
  const previewPaneHtml = `
    <div class="quote-harvest-workspace-scroll">
      <section class="panel stack quote-harvest-side">
        <strong>预览区</strong>
        <div class="muted" style="font-size:12px;">${latestText}</div>
        <div>${harvest?.previewLoading ? '<div class="muted">预览计算中...</div>' : errorHtml}</div>
        <div>
          <strong style="font-size:12px;">已确认结果</strong>
          <div class="muted" style="font-size:12px;">前面已经保存过的 section 会累计显示在这里，方便你继续核对整条原文。</div>
          ${renderHarvestPreviewRowsTable(confirmedPreviewRows, '前面还没有已确认结果。')}
        </div>
        <div>
          <strong style="font-size:12px;">本次预览结果</strong>
          ${renderHarvestPreviewRowsTable(currentPreviewRows, '当前这一段还没有预览报价。')}
        </div>
        <div>
          <strong style="font-size:12px;">累计预览结果</strong>
          <div class="muted" style="font-size:12px;">最终保存前，看这里是否和整条原文想要上墙的结果一致。</div>
          ${renderHarvestPreviewRowsTable(combinedPreviewRows, '累计预览结果为空。')}
        </div>
        <div>
          <strong style="font-size:12px;">剩余待处理行</strong>
          <div style="font-size:12px;white-space:pre-wrap;">${remainingHtml}</div>
        </div>
        <div>
          <strong style="font-size:12px;">当前选区风险行</strong>
          <div style="font-size:12px;white-space:pre-wrap;">${unhandledHtml}</div>
        </div>
      </section>
    </div>
  `;
  return `
    <div class="quote-harvest-workbench">
      <section class="panel quote-harvest-side primary" style="align-self:start;">
        <div class="quote-harvest-side-shell">
          <div class="quote-harvest-side-header">
            <strong>原文区</strong>
            <div style="border:1px solid rgba(243,165,47,0.1);border-radius:12px;padding:10px;background:rgba(8,12,16,0.84);">
              <div style="font-size:12px;color:var(--muted);margin-bottom:4px;">当前选取</div>
              <div style="font-size:14px;font-weight:600;">${selectionSummary}</div>
            </div>
            <div class="muted" style="font-size:12px;">先在左边点出这一段。第一次点击定开始行，第二次点击定结束行；如果要重选，直接再点新的开始行。</div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;">
              <button type="button" id="quote-harvest-clear-section">清空 section</button>
              <button type="button" id="quote-harvest-clear-ignore">清空忽略</button>
            </div>
          </div>
          <div id="quote-harvest-lines" class="quote-harvest-lines">${linesHtml}</div>
        </div>
      </section>
      <section class="panel quote-harvest-workspace">
        <div class="panel-heading" style="margin-bottom:0;">
          <div>
            <div class="section-kicker">Harvest Workspace</div>
            <h3 style="margin:6px 0 0;">录入与预览分开操作</h3>
          </div>
          <div class="quote-harvest-pane-tabs">
            <button type="button" class="quote-harvest-pane-tab ${activePane === 'edit' ? 'active' : ''}" data-harvest-pane="edit">录入</button>
            <button type="button" class="quote-harvest-pane-tab ${activePane === 'preview' ? 'active' : ''}" data-harvest-pane="preview">预览</button>
          </div>
        </div>
        ${activePane === 'preview' ? previewPaneHtml : editPaneHtml}
      </section>
    </div>
  `;
}

function bindResultPaneEvents() {
  const result = currentResultState();
  const editor = document.querySelector('#quote-harvest-editor');
  if (editor) {
    editor.addEventListener('input', (event) => {
      result.editorText = event.target.value;
      result.editorDirty = true;
      result.preview = null;
      result.previewError = '';
      markQuoteHarvestPreviewStale('result');
    });
  }
  const switchButton = document.querySelector('#quote-harvest-switch-button');
  if (switchButton) {
    switchButton.addEventListener('click', () => setQuoteHarvestMode('harvest'));
  }
  document.querySelectorAll('[data-result-line]').forEach((node) => {
    node.addEventListener('click', () => {
      const index = Number(node.dataset.resultLine);
      const current = new Set((result.highlightedIndexes || []).map((item) => Number(item)));
      if (current.has(index)) current.delete(index);
      else current.add(index);
      result.highlightedIndexes = Array.from(current.values()).sort((a, b) => a - b);
      renderQuoteHarvestModal();
    });
  });
}

function bindSectionHarvestEvents() {
  const harvest = currentSectionHarvestState();
  document.querySelectorAll('[data-harvest-pane]').forEach((button) => {
    button.addEventListener('click', () => {
      harvest.activePane = button.dataset.harvestPane || 'edit';
      renderQuoteHarvestModal();
    });
  });
  document.querySelector('#quote-harvest-clear-section')?.addEventListener('click', () => {
    harvest.sectionStart = null;
    harvest.sectionEnd = null;
    harvest.ignoredLineIndexes = [];
    harvest.rows = harvest.rows.map((row) => ({ ...row, source_line_index: '' }));
    harvest.activeRowIndex = null;
    markSectionHarvestDirty();
    renderQuoteHarvestModal();
  });
  document.querySelector('#quote-harvest-clear-ignore')?.addEventListener('click', () => {
    harvest.ignoredLineIndexes = [];
    markSectionHarvestDirty();
    renderQuoteHarvestModal();
  });
  document.querySelector('#quote-harvest-add-row')?.addEventListener('click', () => {
    harvest.rows.push(createHarvestRow());
    harvest.activeRowIndex = harvest.rows.length - 1;
    markSectionHarvestDirty();
    renderQuoteHarvestModal();
  });
  document.querySelector('#quote-harvest-seed-rows')?.addEventListener('click', () => {
    seedHarvestRowsFromSelection();
    renderQuoteHarvestModal();
  });
  document.querySelectorAll('[data-harvest-default]').forEach((input) => {
    input.addEventListener('input', () => {
      harvest.defaults[input.dataset.harvestDefault] = input.value;
      markSectionHarvestDirty();
      markQuoteHarvestPreviewStale('harvest');
    });
  });
  document.querySelectorAll('[data-harvest-row-field]').forEach((input) => {
    input.addEventListener('input', () => {
      const [rowIndex, field] = input.dataset.harvestRowField.split(':');
      harvest.rows[Number(rowIndex)][field] = input.value;
      markSectionHarvestDirty();
      markQuoteHarvestPreviewStale('harvest');
    });
  });
  document.querySelectorAll('[data-harvest-bind-row]').forEach((button) => {
    button.addEventListener('click', () => {
      harvest.activeRowIndex = Number(button.dataset.harvestBindRow);
      renderQuoteHarvestModal();
    });
  });
  document.querySelectorAll('[data-harvest-delete-row]').forEach((button) => {
    button.addEventListener('click', () => {
      const index = Number(button.dataset.harvestDeleteRow);
      harvest.rows.splice(index, 1);
      harvest.activeRowIndex = null;
      markSectionHarvestDirty();
      renderQuoteHarvestModal();
    });
  });
  document.querySelectorAll('[data-harvest-line]').forEach((lineNode) => {
    lineNode.addEventListener('click', () => {
      const index = Number(lineNode.dataset.harvestLine);
      harvest.scrollAnchorIndex = index;
      if (harvest.activeRowIndex !== null) {
        const selected = harvestSelectedIndexes();
        if (!selected.has(index)) return;
        harvest.rows[harvest.activeRowIndex].source_line_index = index;
        harvest.activeRowIndex = null;
        markSectionHarvestDirty();
        renderQuoteHarvestModal();
        return;
      }
      if (harvest.sectionStart === null || (harvest.sectionStart !== null && harvest.sectionEnd !== null && harvest.sectionStart !== harvest.sectionEnd)) {
        harvest.sectionStart = index;
        harvest.sectionEnd = index;
      } else if (harvest.sectionStart === harvest.sectionEnd && index !== harvest.sectionStart) {
        harvest.sectionEnd = index;
      } else {
        harvest.sectionStart = index;
        harvest.sectionEnd = index;
      }
      if (!String(harvest.defaults.section_label || '').trim()) {
        harvest.defaults.section_label = suggestHarvestSectionLabel();
      }
      const lower = Math.min(harvest.sectionStart, harvest.sectionEnd);
      const upper = Math.max(harvest.sectionStart, harvest.sectionEnd);
      harvest.ignoredLineIndexes = harvest.ignoredLineIndexes.filter((value) => Number(value) >= lower && Number(value) <= upper);
      harvest.rows = harvest.rows.map((row) => {
        const lineIndex = Number(row.source_line_index);
        if (row.source_line_index === '' || (lineIndex >= lower && lineIndex <= upper)) return row;
        return { ...row, source_line_index: '' };
      });
      markSectionHarvestDirty();
      renderQuoteHarvestModal();
    });
  });
  document.querySelectorAll('[data-harvest-ignore]').forEach((button) => {
    button.addEventListener('click', (event) => {
      event.stopPropagation();
      const index = Number(button.dataset.harvestIgnore);
      harvest.scrollAnchorIndex = index;
      const selected = harvestSelectedIndexes();
      if (!selected.has(index)) return;
      const ignoredIndexes = new Set(harvest.ignoredLineIndexes.map((value) => Number(value)));
      if (ignoredIndexes.has(index)) {
        harvest.ignoredLineIndexes = harvest.ignoredLineIndexes.filter((value) => Number(value) !== index);
      } else {
        harvest.ignoredLineIndexes.push(index);
      }
      markSectionHarvestDirty();
      renderQuoteHarvestModal();
    });
  });
}

function renderQuoteHarvestModal() {
  if (!_quoteHarvestState) return;
  if (_quoteHarvestState.mode === 'harvest') {
    rememberHarvestScroll();
  }
  const body = document.querySelector('#quote-harvest-body');
  const modebar = document.querySelector('#quote-harvest-modes');
  const summary = document.querySelector('#quote-harvest-summary');
  const previewButton = document.querySelector('#quote-harvest-preview');
  const saveButton = document.querySelector('#quote-harvest-save');
  const subtitle = document.querySelector('#quote-harvest-subtitle');
  const result = currentResultState();
  const harvest = currentSectionHarvestState();
  subtitle.textContent = _quoteHarvestState.mode === 'harvest'
    ? `${textValue(_quoteHarvestState.row.chat_name || _quoteHarvestState.row.source_group_key)} / ${formatQuoteTime(_quoteHarvestState.row.message_time || _quoteHarvestState.row.created_at)} / 分段收割：每次只预览并保存当前 section`
    : (_quoteHarvestState.mode === 'supermarket'
      ? `${textValue(_quoteHarvestState.row.chat_name || _quoteHarvestState.row.source_group_key)} / ${formatQuoteTime(_quoteHarvestState.row.message_time || _quoteHarvestState.row.created_at)} / 超市卡：超长混合报价可保存为不限套数骨架`
      : `${textValue(_quoteHarvestState.row.chat_name || _quoteHarvestState.row.source_group_key)} / ${formatQuoteTime(_quoteHarvestState.row.message_time || _quoteHarvestState.row.created_at)} / 标准模板整理：主流单国家优先`);
  modebar.innerHTML = renderQuoteHarvestTabs();
  body.innerHTML = `
    <div class="stack" style="gap:12px;">
      ${_quoteHarvestState.mode === 'harvest' ? renderQuoteSectionHarvestPane() : renderQuoteResultPane()}
    </div>
  `;
  body.scrollTop = 0;
  document.querySelectorAll('[data-quote-harvest-mode]').forEach((button) => {
    button.addEventListener('click', () => setQuoteHarvestMode(button.dataset.quoteHarvestMode));
  });
  if (_quoteHarvestState.mode === 'harvest') {
    bindSectionHarvestEvents();
    restoreHarvestScroll();
    const remainingCount = Array.isArray(harvest.remainingLines) ? harvest.remainingLines.length : 0;
    const replayRows = Number(harvest?.lastSaveResult?.replay?.rows || 0);
    const replayed = Boolean(harvest?.lastSaveResult?.replay?.replayed);
    summary.textContent = harvest.completed
      ? (replayed
        ? `已保存 ${harvest.savedSections} 段；该消息已整理完成，已生成 ${replayRows} 条候选重放，未改动报价墙。如发现漏段，可继续补一段并重放。`
        : `已保存 ${harvest.savedSections} 段；模板已整理完成，但这条不是最新消息，未生成候选重放，也未改动报价墙。如发现漏段，仍可继续补一段。`)
      : `已保存 ${harvest.savedSections} 段；剩余 ${remainingCount} 行待处理。`;
    previewButton.textContent = harvest.completed ? '继续预览这一段' : '预览这一段';
    saveButton.textContent = harvest.completed
      ? (replayed ? '继续补一段并生成候选重放' : '继续补一段')
      : '保存这一段并继续';
    previewButton.disabled = harvest.previewLoading;
    saveButton.disabled = harvest.previewLoading || !Boolean(harvest.preview?.can_save);
  } else {
    bindResultPaneEvents();
    summary.textContent = result.preview
      ? (result.preview.can_save ? `预览通过：将保存 ${result.preview.derived_sections?.length || 0} 套${_quoteHarvestState.mode === 'supermarket' ? '超市卡' : '群'}骨架。` : '修正右侧结果模板后，再点“生成预览”。')
      : (_quoteHarvestState.mode === 'supermarket'
        ? '超长混合报价可走超市卡；填写方式和标准模板整理一致，但保存时不受 3 套骨架上限。'
        : '主流单国家消息优先走标准模板整理；复杂消息可切到分段收割。');
    previewButton.textContent = '生成预览';
    saveButton.textContent = _quoteHarvestState.mode === 'supermarket' ? '保存超市卡模板' : '保存模板';
    previewButton.disabled = result.previewLoading;
    saveButton.disabled = result.previewLoading || !Boolean(result.preview?.can_save);
  }
}

document.querySelector('#quote-harvest-close').addEventListener('click', closeQuoteHarvestModal);
document.querySelector('#quote-harvest-cancel').addEventListener('click', closeQuoteHarvestModal);
document.querySelector('#quote-harvest-modal').addEventListener('click', (event) => {
  if (event.target === event.currentTarget) {
    closeQuoteHarvestModal();
  }
});
document.querySelector('#quote-harvest-preview').addEventListener('click', async () => {
  if (!_quoteHarvestState) return;
  if (_quoteHarvestState.mode === 'harvest') {
    await requestQuoteHarvestPreview();
    return;
  }
  await requestQuoteResultPreview();
});
document.querySelector('#quote-harvest-save').addEventListener('click', async () => {
  if (!_quoteHarvestState) return;
  const adminPassword = document.querySelector('#quote-harvest-admin-password').value;
  if (_quoteHarvestState.mode === 'harvest') {
    const harvest = currentSectionHarvestState();
    const payload = harvestPayload();
    if (!payload) {
      alert('请先选择一段 section');
      return;
    }
    const resp = await fetch('/api/quotes/exceptions/harvest-save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...payload,
        admin_password: adminPassword,
      }),
    });
    const data = await resp.json();
    if (data.error) {
      alert(`保存失败: ${data.error}`);
      return;
    }
    const savedIndexSet = new Set((harvest.handledLineIndexes || []).map((value) => Number(value)));
    for (const index of (data.saved_line_indexes || [])) {
      savedIndexSet.add(Number(index));
    }
    harvest.savedSections += 1;
    harvest.confirmedPreviewRows = [
      ...(Array.isArray(harvest.confirmedPreviewRows) ? harvest.confirmedPreviewRows : []),
      ...(Array.isArray(data.preview_rows) ? data.preview_rows : []),
    ];
    harvest.remainingLines = Array.isArray(data.remaining_lines) ? data.remaining_lines : [];
    harvest.restrictionLinesAttached = Array.isArray(data.restriction_lines_attached) ? data.restriction_lines_attached : [];
    harvest.handledLineIndexes = Array.from(savedIndexSet.values()).sort((a, b) => a - b);
    harvest.lastSaveResult = data;
    harvest.sectionStart = null;
    harvest.sectionEnd = null;
    harvest.rows = [];
    harvest.ignoredLineIndexes = [];
    harvest.activeRowIndex = null;
    harvest.preview = null;
    harvest.previewError = '';
    harvest.completed = Boolean(data.resolved_fully);
    renderQuoteHarvestModal();
    await loadQuotesData();
    if (data.resolved_fully) {
      const replayed = Boolean(data.replay?.replayed);
      const replayRows = Number(data.replay?.rows || 0);
      alert(replayed
        ? `这一条异常已整理完成，已生成 ${replayRows} 条候选重放，未改动报价墙。如发现漏段，还可以继续补一段并重放。`
        : '这一条异常已整理完成，模板已保存；但这条不是该群最新消息，所以没有生成候选重放，也未改动报价墙。如发现漏段，仍可继续补一段。');
    } else {
      alert('这一段已保存，可继续整理剩余内容。');
    }
    return;
  }
  const result = currentResultState();
  const resp = await fetch('/api/quotes/exceptions/result-save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      exception_id: _quoteHarvestState.row.id,
      result_template_text: result.editorText || '',
      mode: _quoteHarvestState.mode || 'result',
      admin_password: adminPassword,
    }),
  });
  const data = await resp.json();
  if (data.error) {
    alert(`保存失败: ${data.error}`);
    return;
  }
  alert(_quoteHarvestState.mode === 'supermarket' ? '超市卡模板已保存；本次默认不立即上墙。' : '模板已保存；本次默认不立即上墙。');
  closeQuoteHarvestModal();
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
  const exceptionParams = new URLSearchParams({
    limit: String(quoteExceptionState.limit || 10),
    offset: String(quoteExceptionState.offset || 0),
    resolution_status: quoteExceptionState.resolutionStatus || 'open',
  });
  const fetchQuotePayload = async (url, fallback, label) => {
    try {
      const response = await fetch(url);
      const rawText = await response.text();
      let payload = {};
      if (rawText) {
        try {
          payload = JSON.parse(rawText);
        } catch (error) {
          throw new Error(`${label} 返回了非 JSON 内容`);
        }
      }
      if (!response.ok) {
        throw new Error(payload?.error || `${label} 请求失败 (${response.status})`);
      }
      return (payload && typeof payload === 'object') ? payload : fallback;
    } catch (error) {
      console.error(`${label} 加载失败`, error);
      return {
        ...fallback,
        _load_error: error?.message || String(error || `${label} 加载失败`),
      };
    }
  };
  const [boardPayload, exceptionPayload, profilePayload, inquiryPayload] = await Promise.all([
    fetchQuotePayload('/api/quotes/board', { rows: [], total: 0 }, '报价主屏'),
    fetchQuotePayload(`/api/quotes/exceptions?${exceptionParams.toString()}`, { rows: [], total: 0 }, '异常风险池'),
    fetchQuotePayload('/api/quotes/group-profiles', { rows: [], total: 0 }, '群模板配置台'),
    fetchQuotePayload('/api/quotes/inquiries', { rows: [], total: 0 }, '短回复接力台'),
  ]);
  if (
    !exceptionPayload?._load_error
    && Array.isArray(exceptionPayload.rows)
    && exceptionPayload.rows.length === 0
    && Number(exceptionPayload.offset || 0) > 0
    && !exceptionPayload.has_next
  ) {
    quoteExceptionState.offset = Math.max(
      0,
      Number(exceptionPayload.offset || 0) - Number(exceptionPayload.limit || quoteExceptionState.limit || 10),
    );
    return loadQuotesData();
  }
  allQuoteRows = Array.isArray(boardPayload.rows) ? boardPayload.rows : [];
  allQuoteExceptions = Array.isArray(exceptionPayload.rows) ? exceptionPayload.rows : [];
  renderQuoteBoard(allQuoteRows, boardPayload._load_error || '');
  renderQuoteExceptions(exceptionPayload);
  renderQuoteProfiles(Array.isArray(profilePayload.rows) ? profilePayload.rows : [], profilePayload._load_error || '');
  renderQuoteInquiries(Array.isArray(inquiryPayload.rows) ? inquiryPayload.rows : [], inquiryPayload._load_error || '');
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
  document.querySelector('#quote-profile-prefill-status').textContent = '可从风险池一键带入群模板草稿。';
});

document.querySelector('#quote-profile-edit-close').addEventListener('click', closeQuoteProfileEditModal);
document.querySelector('#quote-profile-edit-cancel').addEventListener('click', closeQuoteProfileEditModal);
document.querySelector('#quote-profile-edit-modal').addEventListener('click', (event) => {
  if (event.target === event.currentTarget) {
    closeQuoteProfileEditModal();
  }
});
document.querySelector('#quote-profile-edit-save').addEventListener('click', async () => {
  if (!_quoteProfileEditState) return;
  let templateConfig = _quoteProfileEditState.template_config || '';
  if (['group-parser', 'supermarket-card'].includes(String(_quoteProfileEditState.parser_template || ''))) {
    try {
      templateConfig = fixedTemplateToGroupParserConfig(
        _quoteProfileEditState.fixed_template_text || '',
        _quoteProfileEditState.template_config || '',
      );
    } catch (error) {
      alert(`保存失败: ${error.message}`);
      return;
    }
  }
  const payload = {
    platform: _quoteProfileEditState.platform || 'whatsapp',
    chat_id: _quoteProfileEditState.chat_id || '',
    chat_name: _quoteProfileEditState.chat_name || _quoteProfileEditState.chat_id || '',
    default_card_type: _quoteProfileEditState.default_card_type || '',
    default_country_or_currency: _quoteProfileEditState.default_country_or_currency || '',
    default_form_factor: _quoteProfileEditState.default_form_factor || '不限',
    default_multiplier: _quoteProfileEditState.default_multiplier || '',
    parser_template: _quoteProfileEditState.parser_template || '',
    stale_after_minutes: _quoteProfileEditState.stale_after_minutes || '30',
    note: _quoteProfileEditState.note || '',
    template_config: templateConfig,
  };
  const resp = await fetch('/api/quotes/group-profiles', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await resp.json();
  if (data.error) {
    alert(`保存失败: ${data.error}`);
    return;
  }
  closeQuoteProfileEditModal();
  await loadQuotesData();
});
document.querySelector('#quote-profile-edit-save').insertAdjacentHTML('beforebegin', '<button type="button" id="quote-profile-edit-delete" style="color:#c0392b;border-color:#c0392b">删除模板</button>');
document.querySelector('#quote-profile-edit-delete').addEventListener('click', async () => {
  if (!_quoteProfileEditState) return;
  if (!confirm(`确定删除模板？\\n${_quoteProfileEditState.chat_name || _quoteProfileEditState.chat_id || '未知群'} / ${_quoteProfileEditState.chat_id || ''}`)) {
    return;
  }
  const adminPassword = prompt('请输入报价管理密码，确认删除模板');
  if (adminPassword === null) return;
  const resp = await fetch('/api/quotes/group-profiles/delete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      id: Number(_quoteProfileEditState.profile_id || _quoteProfileEditState.id || 0),
      admin_password: adminPassword,
    }),
  });
  const data = await resp.json();
  if (data.error) {
    alert(`删除失败: ${data.error}`);
    return;
  }
  if (!data.deleted) {
    alert('删除失败: 没找到这条模板');
    return;
  }
  closeQuoteProfileEditModal();
  await loadQuotesData();
  alert('模板已删除。');
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
        title="Quote Terminal",
        subtitle="先看主屏最高价，再下钻来源群、模板配置和异常处理链。",
        active_path="/quotes",
        body=body,
        script=script,
    )


def render_quote_dictionary_page() -> str:
    body = """
<section class="panel stack">
  <div class="toolbar">
    <div>
      <div class="section-kicker">Dictionary Desk</div>
      <h2>标准映射台</h2>
      <div class="muted">维护国家/币种、卡种和形态别名；群级别名优先于全局别名。这里定义一条口语最终映射到什么标准值。</div>
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
    使用说明：1) 表格会显示“内置 + 自定义”映射。2) 点“编辑/复制到表单”可回填。3) 只有“自定义”支持停用；内置项请用同名自定义覆盖。
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
  document.querySelector('#dict-prefill-status').textContent = '已从风险池带入字典草稿，确认标准值后输入管理口令保存。';
}
loadDictionary();
"""
    return _render_layout(
        title="Dictionary Desk",
        subtitle="把群里的叫法压到统一标准值，避免模板、异常和主屏口径分叉。",
        active_path="/quote-dictionary",
        body=body,
        script=script,
    )


def render_workbench_page() -> str:
    body = """
<section class="panel stack">
  <div class="panel-heading">
    <div>
      <div class="section-kicker">Workbench Terminal</div>
      <h2>账期工作面</h2>
      <div class="muted" id="workbench-range">请选择一个账期</div>
    </div>
    <div class="terminal-note" style="max-width:420px;">
      <strong>Desk Logic</strong>
      <p>这个工作面承接结账、广播、实时回查和交易治理。先选口径，再决定是结账、群发，还是直接处理实时交易。</p>
    </div>
  </div>
  <div class="recon-hero-grid">
    <div class="cards">
      <article class="card stat-card primary">
        <div class="label" id="workbench-profit-label">账期利润</div>
        <div class="value" id="workbench-profit">0.00</div>
        <span class="table-secondary">当前账期或实时窗口下的核心利润口径。</span>
      </article>
      <article class="card stat-card">
        <div class="label" id="workbench-customer-label">账期客户卡金额</div>
        <div class="value" id="workbench-customer-amount">0.00</div>
        <span class="table-secondary">客户侧金额合计，用来和供应商侧对照。</span>
      </article>
      <article class="card stat-card">
        <div class="label" id="workbench-vendor-label">账期供应商卡金额</div>
        <div class="value" id="workbench-vendor-amount">0.00</div>
        <span class="table-secondary">供应商侧金额合计，不直接等同利润。</span>
      </article>
      <article class="card stat-card">
        <div class="label">群数量</div>
        <div class="value" id="workbench-groups">0</div>
        <span class="table-secondary">当前工作面口径下命中的活跃群。</span>
      </article>
      <article class="card stat-card">
        <div class="label">客户交易</div>
        <div class="value" id="workbench-customer-transactions">0</div>
        <span class="table-secondary">客户侧交易笔数。</span>
      </article>
      <article class="card stat-card">
        <div class="label">供应商交易</div>
        <div class="value" id="workbench-vendor-transactions">0</div>
        <span class="table-secondary">供应商侧交易笔数。</span>
      </article>
    </div>
    <aside class="terminal-note">
      <strong>Period Selector</strong>
      <p>你可以在这里切换实时窗口和已结账期。实时窗口用于今天的操作，已结账期用于回放和对照。</p>
      <label>
        <span class="muted">账期</span>
        <select id="period-select"></select>
      </label>
    </aside>
  </div>
</section>
<div class="ops-grid">
<section class="panel stack panel-config">
  <div class="panel-heading">
    <div>
      <div class="section-kicker">Settlement Desk</div>
      <h2>结账台</h2>
      <div class="muted">直接调用后端关账服务，口径等同 `/alljs`；本次实际参与结账的群会各自收到一条结账回执。</div>
    </div>
  </div>
  <form id="close-period-form" class="recon-adjust-form">
    <input name="closed_by" placeholder="结账人备注" required />
    <button type="submit">一键结账</button>
  </form>
  <div id="close-period-status" class="muted">当前工作面只做结账入口，真正口径以后端结账结果为准。</div>
</section>
<section class="panel stack panel-assist">
  <div class="panel-heading">
    <div>
      <div class="section-kicker">Outbound Desk</div>
      <h2>出站群发台</h2>
      <div class="muted">Web 群发会进入统一出站队列，由各平台适配器依次投递到该分组下的所有群；“群发人备注”只用于审计记录。</div>
    </div>
  </div>
  <form id="group-broadcast-form" class="recon-adjust-form">
    <input name="created_by" placeholder="群发人备注" required />
    <input name="group_num" type="number" min="0" max="9" step="1" placeholder="分组号，如 1" required />
    <textarea class="full" name="message" placeholder="群发内容，等同 `/diy 1 自定义内容` 里的消息正文" required></textarea>
    <button type="submit">群发到分组</button>
  </form>
  <div id="group-broadcast-status" class="muted">广播只负责排队，不在这里判断业务结果。</div>
</section>
</div>
<section class="panel">
  <div class="panel-heading">
    <div>
      <div class="section-kicker">Role Card Spread</div>
      <h2 id="workbench-role-card-title">账期客户/供应商卡统计</h2>
      <div class="muted">利润 = 客户正数金额 + 供应商负数金额。客户余额和供应商欠款继续体现在群快照，不直接并入利润。</div>
    </div>
  </div>
  <div class="cards">
    <div class="subgrid">
      <section class="subpanel">
        <div class="subpanel-header">
          <h3>客户侧</h3>
          <span class="pill-muted" id="workbench-customer-summary">加载中</span>
        </div>
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
        <div class="subpanel-header">
          <h3>供应商侧</h3>
          <span class="pill-muted" id="workbench-vendor-summary">加载中</span>
        </div>
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
  </div>
</section>
<div class="ops-grid">
<section class="panel stack panel-config">
  <div class="panel-heading">
    <div>
      <div class="section-kicker">Group Tape</div>
      <h2>群快照</h2>
      <div class="muted">按群看期初、收款、使用、期末和交易笔数，是账期面的组级快照。</div>
    </div>
  </div>
  <div class="table-wrap">
    <table id="workbench-groups-table">
      <thead>
        <tr><th>群名</th><th>角色</th><th>期初</th><th>收款</th><th>使用</th><th>期末</th><th>刀数</th><th>交易笔数</th></tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>
</section>
<section class="panel stack panel-assist">
  <div class="panel-heading">
    <div>
      <div class="section-kicker">Card Tape</div>
      <h2>卡种统计</h2>
      <div class="muted">按卡种和角色看账期分布，用来确认卡面结构是不是和预期一致。</div>
    </div>
  </div>
  <div class="table-wrap">
    <table id="workbench-cards-table">
      <thead>
        <tr><th>卡种</th><th>角色</th><th>刀数</th><th>人民币金额</th></tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>
</section>
</div>
<section class="panel stack ledger-panel">
  <div class="panel-heading">
    <div>
      <div class="section-kicker">Realtime Tape</div>
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
<section class="panel stack panel-risk">
  <div>
    <div class="section-kicker">Governance Desk</div>
    <h2>治理操作</h2>
    <div class="muted">治理动作跟随上方实时窗口中的当前交易。交易修改直接落在原始账单上，组合管理继续保留在这里。</div>
  </div>
  <div class="subgrid">
    <section class="subpanel">
      <div class="subpanel-header">
        <h3>交易修改</h3>
        <span class="recon-alert">直接写回原账单</span>
      </div>
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
      <div class="subpanel-header">
        <h3>组合管理</h3>
        <span class="pill-muted">治理视图</span>
      </div>
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

function signedClass(value) {
  const number = Number(value || 0);
  if (number > 0) return 'signed-pos';
  if (number < 0) return 'signed-neg';
  return 'signed-neutral';
}

function moneySpan(value, options = {}) {
  const number = Number(value || 0);
  const classes = ['table-num'];
  if (options.signed) {
    classes.push(signedClass(number));
  }
  const text = options.showPlus ? signedMoney(number) : money(number);
  return `<span class="${classes.join(' ')}">${text}</span>`;
}

function diffClass(value) {
  return signedClass(value);
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
        <td>${moneySpan(row.usd_amount)}</td>
        <td>${moneySpan(amount)}</td>
        ${showProfit ? `<td>${moneySpan(profit, { signed: true })}</td>` : ''}
        ${showDiff ? `<td><span class="${diffClass(diffKnife)}">${signedMoney(diffKnife)}</span></td><td>${moneySpan(profit, { signed: true, showPlus: true })}</td>` : ''}
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

  document.querySelector('#workbench-profit').innerHTML = moneySpan(summary.profit, { signed: true });
  document.querySelector('#workbench-customer-amount').innerHTML = moneySpan(summary.customer_card_rmb_amount, { signed: true });
  document.querySelector('#workbench-vendor-amount').innerHTML = moneySpan(summary.vendor_card_rmb_amount, { signed: true });
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
        <td><span class="table-primary">${row.platform}</span></td>
        <td><span class="table-primary">${row.chat_name}</span><span class="table-secondary">${roleSourceText(row.role_source)}</span></td>
        <td><span class="pill-muted">${roleText(row.business_role)}</span></td>
        <td><span class="table-primary">${row.sender_name}</span></td>
        <td class="mono">${row.message_id || ''}</td>
        <td>${moneySpan(row.amount)}</td>
        <td><span class="table-primary">${row.category}</span></td>
        <td><span class="table-num">${rateText(row.rate)}</span></td>
        <td>${moneySpan(row.display_rmb_amount ?? row.rmb_value)}</td>
        <td>${moneySpan(row.display_usd_amount)}</td>
        <td class="quote-note">${row.raw}</td>
        <td><span class="table-primary">${row.created_at}</span></td>
        <td>${statusChip(row.period_status)}${formatEditTrail(row)}</td>
        <td><button type="button" class="action-ghost" data-action="edit-transaction" data-transaction-id="${row.id}">修改</button></td>
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
      <td><span class="table-primary">${row.chat_name}</span></td>
      <td><span class="pill-muted">${row.business_role || ''}</span></td>
      <td>${moneySpan(row.opening_balance)}</td>
      <td>${moneySpan(row.income)}</td>
      <td>${moneySpan(row.expense)}</td>
      <td>${moneySpan(row.closing_balance)}</td>
      <td>${moneySpan(row.total_usd_amount)}</td>
      <td><span class="table-num">${row.transaction_count}</span></td>
    </tr>
  `).join('')
    : '<tr><td colspan="8" class="muted">当前口径下暂无有交易的群快照</td></tr>';

  document.querySelector('#workbench-cards-table tbody').innerHTML = (data.card_stats || []).map((row) => `
    <tr>
      <td><span class="table-primary">${row.card_type}</span></td>
      <td><span class="pill-muted">${roleText(row.business_role)}</span></td>
      <td>${moneySpan(row.usd_amount)}</td>
      <td>${moneySpan(row.display_rmb_amount ?? row.rmb_amount)}</td>
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
  const submitButton = form.querySelector('button[type="submit"]');
  const submitLabel = submitButton ? submitButton.textContent : '';
  if (!String(payload.closed_by || '').trim()) {
    setWorkbenchStatus('结账人不能为空。', true, 'close-period-status');
    return;
  }
  const confirmed = window.confirm('确认一键结账吗？这会按当前实时交易执行与 /alljs 相同的结账逻辑，并给本次参与结账的群补发各自的回执。');
  if (!confirmed) {
    setWorkbenchStatus('已取消一键结账。', false, 'close-period-status');
    return;
  }
  if (submitButton) {
    submitButton.disabled = true;
    submitButton.textContent = '结账中...';
  }
  setWorkbenchStatus('一键结账提交中，请勿重复点击。', false, 'close-period-status');
  try {
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
  } finally {
    if (submitButton) {
      submitButton.disabled = false;
      submitButton.textContent = submitLabel;
    }
  }
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
        title="Workbench Terminal",
        subtitle="工作面承接结账、广播、实时回查和治理动作；先定账期，再下钻到实时带和改单台。",
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
  <div class="panel-heading">
    <div>
      <div class="section-kicker">Finance Terminal</div>
      <h2>财务对账工作面</h2>
      <div class="muted" id="reconciliation-range">按当前口径加载逐笔台账</div>
    </div>
    <div class="toolbar-actions">
      <a class="inline-link" id="reconciliation-export-detail-link" href="/api/reconciliation/export?scope=realtime&export_mode=detail">导出逐笔明细 CSV</a>
      <a class="inline-link" id="reconciliation-export-summary-link" href="/api/reconciliation/export?scope=realtime&export_mode=summary">导出汇总 CSV</a>
    </div>
  </div>
  <div class="recon-hero-grid">
    <div class="cards">
      <article class="card stat-card primary">
        <div class="label">未对账笔数</div>
        <div class="value" id="reconciliation-unreconciled">0</div>
        <span class="table-secondary">当前口径下仍需人工确认的逐笔记录。</span>
      </article>
      <article class="card stat-card">
        <div class="label">汇率公式异常</div>
        <div class="value" id="reconciliation-rate-error">0</div>
        <span class="table-secondary">应算人民币与台账结果存在公式偏差。</span>
      </article>
      <article class="card stat-card">
        <div class="label">缺失汇率</div>
        <div class="value" id="reconciliation-missing-rate">0</div>
        <span class="table-secondary">台账存在金额，但汇率链路没有补齐。</span>
      </article>
      <article class="card stat-card">
        <div class="label">已修改未复核</div>
        <div class="value" id="reconciliation-edited">0</div>
        <span class="table-secondary">已经被人工改写，但还没二次确认。</span>
      </article>
    </div>
    <aside class="terminal-note">
      <strong>Desk Logic</strong>
      <p>这个工作面不负责解释业务，只负责把逐笔台账、财务补录和追踪链路放在一个屏里，方便你快速定位差额来自哪里。</p>
      <ul>
        <li>先定口径，再下钻组合、组号和具体群。</li>
        <li>调账项进入台账后会立刻影响导出。</li>
        <li>追踪链路只读，用来验证消息、解析和修改痕迹。</li>
      </ul>
    </aside>
  </div>
</section>
<div class="ops-grid">
<section class="panel stack panel-config">
  <div class="panel-heading">
    <div>
      <div class="section-kicker">Filter Desk</div>
      <h2>筛选口径台</h2>
      <div class="muted">支持实时窗口、指定账期、日期区间三种口径；可先按组合或组号汇总，再下钻到具体群，导出默认沿用当前筛选。</div>
    </div>
  </div>
  <form id="reconciliation-filter-form" class="recon-filter-form">
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
<section class="panel stack panel-assist">
  <div class="panel-heading">
    <div>
      <div class="section-kicker">Adjustment Desk</div>
      <h2>逐笔调账台</h2>
      <div class="muted">用于补录 RMB 加减、额外费用或独立调账项；保存后会立刻进入逐笔台账和导出。</div>
    </div>
    <span class="recon-alert">保存后立即进入财务口径</span>
  </div>
  <form id="reconciliation-adjustment-form" class="recon-adjust-form">
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
</div>
<section class="panel stack ledger-panel recon-ledger-panel">
  <div class="panel-heading">
    <div>
      <div class="section-kicker">Ledger Tape</div>
      <h2>逐笔台账带</h2>
      <div class="muted" id="reconciliation-ledger-summary">加载中</div>
    </div>
  </div>
  <div class="table-wrap">
    <table id="reconciliation-ledger-table">
      <thead>
        <tr><th>时间</th><th>来源</th><th>群</th><th>角色</th><th>卡种</th><th>刀数</th><th>汇率</th><th>应算人民币</th><th>人民币</th><th>异常</th><th>备注 / 修改痕迹</th><th>动作</th></tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>
</section>
<section class="panel stack panel-risk trace-terminal" id="reconciliation-trace-panel">
  <div class="panel-heading">
    <div>
      <div class="section-kicker">Trace Chain</div>
      <h2>差额追踪链路</h2>
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
  document.querySelector('#reconciliation-trace-status').textContent = `正在加载交易 ${transactionId} 的追踪链路...`;
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
        <td><span class="table-primary">${row.created_at || '—'}</span><span class="table-secondary">${row.period_id || '实时窗口'}</span></td>
        <td><span class="table-primary">${row.row_type === 'finance_adjustment' ? '财务调账' : '原始交易'}</span><span class="table-secondary">${row.source_table || 'transactions'}</span></td>
        <td><span class="table-primary">${row.chat_name || row.group_key}</span><span class="table-secondary">${row.group_num === null || row.group_num === undefined ? '未归组' : `组 ${row.group_num}`}</span></td>
        <td><span class="pill-muted">${roleText(row.business_role)}</span></td>
        <td><span class="table-primary">${row.card_type}</span><span class="table-secondary">${row.row_type === 'finance_adjustment' ? '人工补录' : '自动入账'}</span></td>
        <td><span class="table-num">${money(row.usd_amount)}</span></td>
        <td><span class="table-num">${row.rate === null || row.rate === undefined ? '—' : compactNumber(row.rate)}</span></td>
        <td><span class="table-num">${row.expected_rmb_value === null || row.expected_rmb_value === undefined ? '—' : money(row.expected_rmb_value)}</span></td>
        <td><span class="table-num">${money(row.rmb_value)}</span></td>
        <td class="quote-note">${issueCell(row)}</td>
        <td class="quote-note">${noteCell(row)}</td>
        <td>
          <div class="action-row">
            <button type="button" class="action-ghost" data-action="quote-row" data-row-id="${row.row_id}" data-row-type="${row.row_type}">引用</button>
            ${row.row_type === 'transaction' ? `<button type="button" class="action-ghost" data-action="trace-row" data-row-id="${row.row_id}">追踪</button>` : ''}
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
    `当前 ${latestRows.length} 行，财务口径 ${Number((data.summary || {}).financial_row_count || 0)} 行。导出沿用 ${filterTrailText(data)}。未对账=${Number((data.summary || {}).unreconciled_count || 0)}，汇率公式异常=${Number((data.summary || {}).rate_formula_error_count || 0)}。`;
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
  setLedgerStatus(`已加载 ${scopeText(scope)} / ${filterTrailText(data)} 下的逐笔台账带。`);
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
        title="Finance Terminal",
        subtitle="把逐笔交易、财务补录和追踪链路压到一个工作面，先定口径，再做财务核对。",
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
  <a href="/" class="%s">总账主屏</a>
  <a href="/workbench" class="%s">账期工作面</a>
  <a href="/quotes" class="%s">报价主屏</a>
  <a href="/quote-dictionary" class="%s">标准映射台</a>
  <a href="/reconciliation" class="%s">对账工作面</a>
  <a href="/role-mapping" class="%s">映射治理台</a>
  <a href="/history" class="%s">历史回放台</a>
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
        f"{_STYLE}</head><body><div class=\"app-shell\"><header><div class=\"hero\"><div class=\"hero-copy\">"
        f"<span class=\"hero-kicker\">SeeSee Operating Terminal</span><h1>{title}</h1>"
        f"<p>{subtitle}</p></div><div class=\"nav-scroll\">{nav}</div></div></header>"
        f"<main>{body}</main></div><script>{script}</script></body></html>"
    )
