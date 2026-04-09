# SeeSee 项目上下文

## 项目性质
礼品卡中介报价撮合与总账系统，涉及钱、报价、消息、机器人和数据库。
**不是学习 demo，是真实运营系统。**

## 架构
- 双监听 + Core 核心驱动：WeChat 适配层 + WhatsApp 适配层 + 统一 Core runtime
- Core 是唯一业务核心：`POST /api/core/messages` 是正式消息入口
- 监听器只做：接收消息 → 归一化 → 送入 Core → 执行 Core 返回的动作
- 当前最重要子系统：报价墙（稳定采集、稳定解析、稳定展示、稳定追溯）

## 核心原则
- 当前主路线：群固定模板 + 报价字典 + 异常区人工补洞，**不是万能正则扩张**
- 报价字典是运营工具，不只是技术配置
- 任何可能导致错误价格上墙的改动属于高风险

## 约定
- 业务逻辑放 `bookkeeping_core/`，页面层只做展示
- 路由在 `bookkeeping_web/app.py`，页面在 `pages.py`
- 测试用 `unittest`：`python -m unittest`
- PostgreSQL 是正式 DB；SQLite 不是正式事实源
- 先说影响范围和风险，再动手

## 禁止事项
- 不动 PostgreSQL schema 和账务数据
- 不把未来自动化描述成已实现能力
- 不把 AI 当主解析链路
- 不在报价解析、高风险区域做未经验证的大改
- 不忽视异常区、模板、字典的运营优先级

## 最短启动路径
```bash
# Core
cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform
BOOKKEEPING_CORE_TOKEN='test-token-123456' \
BOOKKEEPING_DB_DSN='postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping' \
BOOKKEEPING_MASTER_USERS='+84389225210' \
QUOTE_ADMIN_PASSWORD='119110' \
PYTHONPATH='/Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform' \
./.venv/bin/python reporting_server.py --host 127.0.0.1 --port 8765

# WeChat 监听器
cd /Users/newlcc/SeeSee/repo/wxbot/bookkeeping-platform && python -m wechat_adapter.main

# WhatsApp 监听器
cd /Users/newlcc/SeeSee/repo/wxbot/whatsapp-bookkeeping && npm start

## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- After modifying code files in this session, run `python3 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"` to keep the graph current
