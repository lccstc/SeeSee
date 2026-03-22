# WhatsApp V1 Removal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `wxbot/whatsapp-bookkeeping` 与当前有效文档中的 V1 本地记账和 `/api/sync/events` 兼容语义完整清除，只保留 WhatsApp 的 V2 薄适配层。

**Architecture:** 保留 `index/core-api/whatsapp/chat-context/config` 五个 V2 适配层文件，删除旧本地记账内核、旧同步链路、旧测试和旧依赖，同时把文档与构建策略一起收敛为 V2-only。构建前先清空 `dist`，确保编译产物不会继续泄漏旧模块。

**Tech Stack:** TypeScript, Node.js, Baileys, npm, Python docs/tooling

---

## File Structure

- Modify: `wxbot/whatsapp-bookkeeping/src/core-api.test.ts`
  责任：增加 V1 清除约束测试
- Modify: `wxbot/whatsapp-bookkeeping/src/config.ts`
  责任：删除 `sync` 配置结构
- Modify: `wxbot/whatsapp-bookkeeping/package.json`
  责任：删除 V1 依赖并增加 build 前清理
- Modify: `wxbot/whatsapp-bookkeeping/package-lock.json`
  责任：同步依赖收敛
- Modify: `wxbot/whatsapp-bookkeeping/README.md`
  责任：改为 V2-only 说明
- Delete: `wxbot/whatsapp-bookkeeping/src/commands.ts`
- Delete: `wxbot/whatsapp-bookkeeping/src/database.ts`
- Delete: `wxbot/whatsapp-bookkeeping/src/parser.ts`
- Delete: `wxbot/whatsapp-bookkeeping/src/sync.ts`
- Delete: `wxbot/whatsapp-bookkeeping/src/sync-status.ts`
- Delete: `wxbot/whatsapp-bookkeeping/src/sync-status.test.ts`
- Delete: `wxbot/whatsapp-bookkeeping/src/sync.test.ts`
- Delete: `wxbot/whatsapp-bookkeeping/tests/commands-bind.test.mjs`
- Delete: `wxbot/whatsapp-bookkeeping/tests/commands-set-group.test.mjs`
- Modify: `docs/superpowers/plans/2026-03-22-phase2-5-ingestion-alignment-and-mock-replay.md`
  责任：加 superseded note，避免继续按 V1 兼容导入推进
- Modify: `wxbot/bookkeeping-platform/docs/高中生想接盘3.md`
  责任：删除或降级仍把 `/api/sync/events` 写成当前入口的说明

### Task 1: 用失败测试锁定 V1 必须消失

**Files:**
- Modify: `wxbot/whatsapp-bookkeeping/src/core-api.test.ts`
- Test: `wxbot/whatsapp-bookkeeping/src/core-api.test.ts`

- [ ] **Step 1: 写失败测试，锁定配置、README 与源码边界**

覆盖点：

- `src/config.ts` 不再定义 `sync`
- `README.md` 不再出现 `/api/sync/events`、`sync_outbox`、`sync.enabled`
- `src/index.ts` 只保留 V2 主链路

- [ ] **Step 2: 运行测试确认红灯**

Run: `npm test`
Expected: FAIL，指出 README / config 仍包含 V1 语义

### Task 2: 删除 V1 源码、测试与依赖

**Files:**
- Modify: `wxbot/whatsapp-bookkeeping/src/config.ts`
- Modify: `wxbot/whatsapp-bookkeeping/package.json`
- Modify: `wxbot/whatsapp-bookkeeping/package-lock.json`
- Delete: `wxbot/whatsapp-bookkeeping/src/commands.ts`
- Delete: `wxbot/whatsapp-bookkeeping/src/database.ts`
- Delete: `wxbot/whatsapp-bookkeeping/src/parser.ts`
- Delete: `wxbot/whatsapp-bookkeeping/src/sync.ts`
- Delete: `wxbot/whatsapp-bookkeeping/src/sync-status.ts`
- Delete: `wxbot/whatsapp-bookkeeping/src/sync-status.test.ts`
- Delete: `wxbot/whatsapp-bookkeeping/src/sync.test.ts`
- Delete: `wxbot/whatsapp-bookkeeping/tests/commands-bind.test.mjs`
- Delete: `wxbot/whatsapp-bookkeeping/tests/commands-set-group.test.mjs`
- Test: `wxbot/whatsapp-bookkeeping/src/core-api.test.ts`

- [ ] **Step 1: 做最小配置收敛**

最小实现要求：

- 删除 `Config.sync`
- 保留 `coreApi`
- 保留现有 V2 入口配置读取

- [ ] **Step 2: 删除 V1 源码与旧测试**

最小实现要求：

- 旧本地记账内核文件直接删除
- 旧同步链路文件直接删除
- 旧测试直接删除

- [ ] **Step 3: 删除旧依赖并增加 build 前清理**

最小实现要求：

- 移除 `better-sqlite3`
- 移除 `@types/better-sqlite3`
- `npm run build` 之前清理 `dist`

- [ ] **Step 4: 重新运行测试**

Run: `npm test`
Expected: PASS，仅保留 V2 相关测试

### Task 3: 清理 README 与当前有效文档

**Files:**
- Modify: `wxbot/whatsapp-bookkeeping/README.md`
- Modify: `docs/superpowers/plans/2026-03-22-phase2-5-ingestion-alignment-and-mock-replay.md`
- Modify: `wxbot/bookkeeping-platform/docs/高中生想接盘3.md`
- Test: `wxbot/whatsapp-bookkeeping/src/core-api.test.ts`

- [ ] **Step 1: 删除 README 中的 V1 指导**

最小实现要求：

- 不再出现 `/api/sync/events`
- 不再出现 `sync_outbox`
- 不再出现 `sync.enabled`
- 只保留 `coreApi` 和 V2 真机验证方式

- [ ] **Step 2: 清理仍把 V1 写成当前要求的文档**

最小实现要求：

- 当前有效计划文档加 superseded / retired 说明
- 非历史归档文档不再把 V1 写成当前入口

- [ ] **Step 3: 重跑测试确认绿灯**

Run: `npm test`
Expected: PASS

### Task 4: 清理构建产物并做最终验证

**Files:**
- Modify: `wxbot/whatsapp-bookkeeping/package.json`
- Test: `wxbot/whatsapp-bookkeeping`

- [ ] **Step 1: 清空旧 dist 并重新构建**

Run: `npm run build`
Expected: PASS，`dist` 中不再保留已删除模块

- [ ] **Step 2: 做仓库级搜索验证**

Run: `rg -n "/api/sync/events|sync_outbox|createLedgerSyncEvent|OutboxSyncWorker|sync\\.enabled" docs wxbot/whatsapp-bookkeeping wxbot/bookkeeping-platform`
Expected: 只剩历史退役记录，不再出现在活跃源码、活跃 README 和现行执行文档中

- [ ] **Step 3: 做最终回归**

Run:

```bash
cd "/Users/lcc/SeeSee/wxbot/whatsapp-bookkeeping"
npm test
npm run build
```

Expected:

- 所有 WhatsApp 测试通过
- 构建通过
- V2 运行面保持完整
