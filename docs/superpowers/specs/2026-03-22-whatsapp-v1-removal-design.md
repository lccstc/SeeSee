# 2026-03-22 WhatsApp V1 完整清除设计

## 0. 目标

把 `wxbot/whatsapp-bookkeeping` 收敛成纯 V2 薄适配层，确保后续项目推进不再引用、维护、测试任何 V1 本地记账或 `/api/sync/events` 兼容链路。

## 1. 当前问题

虽然 WhatsApp 运行入口已经走 V2：

- `src/index.ts` 只做消息归一化、调用 `coreApi.sendEnvelope()`、执行 `CoreAction`
- `src/core-api.ts` 固定请求 `POST /api/core/messages`

但仓库里仍保留一整套 V1 遗留：

- 本地记账内核：`src/commands.ts`、`src/database.ts`、`src/parser.ts`
- 旧同步链路：`src/sync.ts`、`src/sync-status.ts`
- 旧测试：`src/sync*.test.ts`、`tests/commands-*.test.mjs`
- 旧文档与旧计划：仍指导 `/api/sync/events`、`sync_outbox`、兼容导入

这些内容会在后续 grep、改测试、改文档时持续制造错误上下文，导致团队继续为 V1 付维护成本。

## 2. 设计决策

### 2.1 保留的 WhatsApp 运行面

清理后仅保留以下 V2 薄适配层文件：

- `src/index.ts`
- `src/core-api.ts`
- `src/whatsapp.ts`
- `src/chat-context.ts`
- `src/config.ts`
- 与上述文件直接相关的测试

这些文件共同构成唯一允许的 WhatsApp 运行链路：

```text
WhatsApp message
  -> normalizeMessage()
  -> POST /api/core/messages
  -> CoreAction[]
  -> sendMessage / sendFile
```

### 2.2 删除的 V1 代码与测试

直接删除以下文件，不做 `legacy/` 归档：

- `src/commands.ts`
- `src/database.ts`
- `src/parser.ts`
- `src/sync.ts`
- `src/sync-status.ts`
- `src/sync-status.test.ts`
- `src/sync.test.ts`
- `tests/commands-bind.test.mjs`
- `tests/commands-set-group.test.mjs`

理由：

- 这些文件不再属于运行主链路
- 继续保留只会让未来计划、测试和文档继续围绕它们旋转
- 归档到 `legacy/` 仍会被 grep 命中，不符合“完整清除”

### 2.3 配置与依赖收敛

配置层只保留 `coreApi`：

- 删除 `Config.sync`
- README 与示例配置不再出现 `sync.endpoint`、`sync_outbox`、`/api/sync/events`

依赖层同步收敛：

- 删除不再需要的 `better-sqlite3`
- 删除不再需要的 `@types/better-sqlite3`

### 2.4 构建产物处理

`tsc` 默认不会清理旧 `dist` 文件。若仅删除源码，不清理 `dist`，旧 `commands.js`、`sync.js` 仍会残留。

因此构建策略改为：

- `npm run build` 前先清空 `dist`
- 再执行 `tsc`

这样可以确保编译产物与源码边界一致，不再泄漏 V1 旧文件。

### 2.5 文档与计划清理

以下内容必须同步收敛：

- `wxbot/whatsapp-bookkeeping/README.md`
- 当前仍把 `/api/sync/events` 或兼容导入写成现行要求的 `docs/superpowers` 文档
- 仓库内其他仍会误导后续实现的说明文档

处理原则：

- 当前有效文档：改成“V2-only”
- 历史计划：增加 superseded / retired 说明，避免再被当成执行依据
- 纯历史清理记录可以保留事实，但不能再表述成当前要求

## 3. 非目标

本轮不做：

- 重新设计 WhatsApp 适配层协议
- 调整 `bookkeeping-platform` 的核心运行时合同
- WeChat 侧重构
- 新增额外功能或补历史迁移脚本

## 4. 验证标准

完成后应满足：

1. `wxbot/whatsapp-bookkeeping` 活跃源码不再包含 V1 本地记账或 `/api/sync/events` 兼容链路
2. WhatsApp README 与当前有效计划文档不再指导 `sync_outbox` 或 `/api/sync/events`
3. `npm test` 与 `npm run build` 在 WhatsApp 仓库通过
4. 仓库级搜索中，活跃代码与活跃文档不再把 V1 写成当前支持路径
5. WhatsApp 运行入口仍能明确指向 `POST /api/core/messages`
