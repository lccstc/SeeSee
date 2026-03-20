# WhatsApp Bookkeeping 项目进度报告

**生成时间**: 2026-02-21
**项目位置**: `/Users/lcc/whatsapp-bookkeeping/`
**状态**: ✅ 功能完整，正常运行

---

## 📌 项目概述

独立的 WhatsApp 群组记账机器人，完全脱离 OpenClaw 框架，零 AI 开销。

### 核心功能
- ✅ 交易记录（`+100rmb`、`-50rg 5.3` 等格式）
- ✅ 余额查询（`/bal`，显示 NGN 汇率）
- ✅ 交易历史（`/history`）
- ✅ 类目明细（`/mx`，按类目 + 汇率统计刀数）
- ✅ 扎帐功能（`/js`）
- ✅ 扎帐历史（`/settlements`）
- ✅ 群组分组（`/set`，0-9 分组）
- ✅ 群发消息（`/diy`）
- ✅ NGN 汇率设置（`/ngn`）
- ✅ 撤销交易（`/undo`）
- ✅ 白名单管理
- ✅ 用户绑定（`/bind`）

---

## 📂 项目结构

```
/Users/lcc/whatsapp-bookkeeping/
├── src/                        # 源代码目录
│   ├── index.ts                # 主入口文件
│   ├── parser.ts               # 交易解析器（正则匹配）
│   ├── parser.test.ts          # 解析器测试
│   ├── database.ts             # SQLite 数据库层
│   ├── commands.ts             # 命令处理器
│   ├── whatsapp.ts             # WhatsApp 连接层（Baileys）
│   └── config.ts               # 配置管理
├── data/
│   └── bookkeeping.db          # SQLite 数据库
├── auth/                       # WhatsApp 会话数据（已配对）
├── config.json                 # 配置文件
├── package.json                # 依赖配置
├── tsconfig.json               # TypeScript 配置
├── README.md                   # 使用说明
├── PROJECT_STATUS.md           # 项目进度（本文件）
└── dist/                       # 编译后的 JS 文件
    └── *.js                    # 已编译完成
```

---

## ✅ 已完成的工作

### 1. 项目创建
- [x] 创建项目目录结构
- [x] 配置 package.json
- [x] 配置 tsconfig.json
- [x] 安装依赖（Baileys, better-sqlite3, pino, qrcode-terminal）

### 2. 代码迁移与重写
- [x] 复制 `parser.ts` - 交易解析器（100% 复用）
- [x] 复制 `database.ts` - 数据库层（持续更新）
- [x] 重写 `commands.ts` - 命令处理器（适配独立运行）
- [x] 新建 `whatsapp.ts` - WhatsApp 连接层（基于 Baileys）
- [x] 新建 `index.ts` - 主入口文件
- [x] 新建 `config.ts` - 配置管理

### 3. 数据迁移
- [x] 复制 `bookkeeping.db` 到 `data/` 目录
- [x] 复制 WhatsApp 认证数据到 `auth/`

### 4. 功能修复与优化
- [x] 修复 ES 模块 `__dirname` 问题
- [x] 修复 pino 日志依赖问题
- [x] 添加二维码显示功能
- [x] 简化日志输出

### 5. WhatsApp 连接优化
- [x] 支持 LID 模式（使用 `participantAlt` 获取真实号码）
- [x] 修复 `fromMe` 判断问题
- [x] 添加机器人自身 JID 获取

### 6. 新增功能（2026-02-21 更新）
- [x] 汇率验证（0-10 范围限制）
- [x] 交易后实时显示余额
- [x] 扎帐功能（`/js`）
- [x] 扎帐历史（`/settlements`）
- [x] 类目明细（`/mx`，按类目 + 汇率统计刀数）
- [x] 群组分组（`/set 数字`）
- [x] 群发消息（`/diy`）
- [x] NGN 汇率设置（`/ngn`）
- [x] 系统统计增强（`/bkstats`，含分组统计）
- [x] 时间显示修正为越南时间（UTC+7）
- [x] 过滤零金额条目（`/mx` 不显示完全对冲的账目）

### 7. NGN 双币种显示（分组 2 专属）
- [x] 数据库添加 `ngn_rate` 字段，记录交易时的汇率
- [x] 交易后反馈显示人民币 + NGN 双币种（`¥` / `₦`）
- [x] `/bal` 命令优化：显示未扎帐交易刀数概要
- [x] `/mx` 命令：显示详细双币种明细
- [x] 扎帐后显示"所有交易已扎帐"提示
- [x] 修复扎帐金额双重负号问题

---

## 🔧 当前配置

### config.json
```json
{
  "whatsapp": {
    "authDir": "./auth"
  },
  "masterPhone": "+84389225210",
  "logLevel": "info"
}
```

### package.json 关键依赖
- `@whiskeysockets/baileys@^7.0.0-rc.9` - WhatsApp 连接
- `better-sqlite3@^11.0.0` - 数据库
- `pino@^9.0.0` - 日志
- `qrcode-terminal@^0.12.0` - 二维码显示

### 数据库表结构
- `transactions` - 交易记录（含 `settled`、`ngn_rate` 字段）
- `settlements` - 扎帐记录
- `groups` - 群组分组（0-9）
- `settings` - 系统设置（NGN 汇率等）
- `whitelist` - 白名单用户
- `bindings` - WhatsApp ID 绑定

---

## 🚀 快速启动

```bash
cd ~/whatsapp-bookkeeping
npm start
```

### 启动后预期输出
```
✅ WhatsApp 连接成功！

🎉 现在可以在群组中使用记账功能了！
输入 /bal 查看余额，或发送 +100rmb 记录交易
```

---

## 📱 支持的命令

| 命令 | 说明 | 权限 |
|------|------|------|
| `/bal` | 查看当前余额（显示未扎帐刀数明细） | 所有人 |
| `/history [limit]` | 查看交易历史 | 所有人 |
| `/mx` | 查看所有类目明细（双币种，分组 2） | 所有人 |
| `/mx rg` | 查看指定类目明细 | 所有人 |
| `/js` | 扎帐（结算未扎帐交易） | 白名单 |
| `/settlements [10]` | 查看扎帐历史 | 所有人 |
| `/set 数字` | 设置群组分组（0-9） | 管理员 |
| `/diy 数字 内容` | 群发消息 | 管理员 |
| `/ngn 数字` | 设置 NGN 汇率 | 管理员 |
| `/undo` | 撤销最后一笔交易 | 白名单 |
| `/clear` | 清空记录 | 管理员 |
| `/adduser +手机号` | 添加白名单 | 管理员 |
| `/rmuser +手机号` | 移除白名单 | 管理员 |
| `/users` | 查看白名单 | 管理员 |
| `/bind +手机号` | 绑定 WhatsApp ID | 白名单 |
| `/export` | 导出数据 | 管理员 |
| `/bkstats` | 系统统计 | 管理员 |

---

## 💡 交易格式

支持多种输入格式：

| 格式 | 示例 | 说明 |
|------|------|------|
| 符号在前 | `+100rmb` | 收入 100 元 |
| 符号在前 + 汇率 | `-50rg 5.3` | 支出 50 RG × 5.3 |
| 类别在前 | `rmb+100` | 收入 100 元 |
| 类别在前 + 汇率 | `rg-25 5.3` | 支出 25 RG × 5.3 |

### 类别说明
- **rmb**: 人民币（正数类别，保持符号）
- **rg/sp/gs/xb/it/st/ft/mx/gg/dg/ae/lulu/dk/ebay/rb**: 负数类别（符号反转）

### 汇率说明
- 非 RMB 交易必须提供汇率
- 汇率必须在 0-10 之间，超过会报错
- 示例：`+25rg 4.0` = 25 刀 × 4.0 = 100 元

---

## 📊 分组 2 双币种显示

### 交易后反馈（分组 2）
```
✅ +25 RG ×5 = -¥125.00 (-₦24275)
📊 余额：+100.00
N 194.2
```

### /bal 命令（分组 2）
```
📊 余额：-2860.00
📋 群组：分组 2
📝 未扎帐：5 笔

明细:
IT:
  ×4.9: 400
  ×5: 100
RG:
  ×5: 25

N 195
```

### /mx 命令（分组 2）
```
📊 明细:
💰 余额：-2860.00
N 195
IT:
  ×4.9: 400 = -¥1960.00 (-₦382200)
  ×5: 100 = -¥500.00 (-₦97500)

✅ 所有交易已扎帐
```

### 货币符号
- **人民币 (CNY)**: `¥`
- **尼日利亚奈拉 (NGN)**: `₦`

### 汇率记录逻辑
- 每笔交易记录**交易发生时**的 NGN 汇率
- 账单显示使用**交易时的汇率**，不受后续汇率变更影响
- 10 点汇率 194 时的交易永远显示 194 的 NGN 金额
- 12 点汇率改为 196 后，新交易显示 196，老交易仍显示 194

---

## 🔍 当前运行状态

- **WhatsApp 账号**: 85257001980
- **连接状态**: ✅ 已连接
- **数据库**: bookkeeping.db（已有历史数据）
- **认证数据**: auth/ 目录（已配对）
- **分组功能**: ✅ 已启用（0-9）
- **NGN 汇率**: ✅ 可设置（`/ngn` 命令）
- **双币种显示**: ✅ 分组 2 专属功能

---

## 📋 数据库迁移

如需添加新表或字段，运行：

```bash
# 添加 groups 表
sqlite3 data/bookkeeping.db "CREATE TABLE IF NOT EXISTS groups (group_id TEXT PRIMARY KEY, group_num INTEGER, created_at TEXT NOT NULL DEFAULT (datetime('now'))); CREATE INDEX IF NOT EXISTS idx_groups_num ON groups(group_num);"

# 添加 settings 表
sqlite3 data/bookkeeping.db "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT, updated_at TEXT NOT NULL DEFAULT (datetime('now'))); INSERT OR IGNORE INTO settings (key, value) VALUES ('ngn_rate', '');"

# 添加 settled 字段到 transactions
sqlite3 data/bookkeeping.db "ALTER TABLE transactions ADD COLUMN settled INTEGER NOT NULL DEFAULT 0;"

# 添加 ngn_rate 字段到 transactions（2026-02-21）
sqlite3 data/bookkeeping.db "ALTER TABLE transactions ADD COLUMN ngn_rate REAL;"
```

---

## 🛠️ 开发命令

```bash
# 开发模式（直接运行 TypeScript）
npm run dev

# 生产模式（运行编译后的 JS）
npm start

# 构建
npm run build

# 测试
npm test
```

---

## 📝 已知问题与注意事项

### LID 模式
- WhatsApp 使用 LID（Lifted ID）模式，用户 JID 为 `xxxxx@lid` 格式
- 通过 `participantAlt` 字段获取真实电话号码
- 白名单中需要存储真实号码或 LID 号码

### 群发功能
- `/diy 数字 内容` 会发送到指定分组的所有群组
- 不包括当前发送命令的群组

### NGN 汇率
- 通过 `/ngn 数字` 设置（如 `/ngn 194.2`）
- 显示在所有余额信息下方，格式为 `N 194.2`

### 分组 2 双币种
- 只有分组 2 的群组显示双币种（`¥` + `₦`）
- 其他分组保持只显示人民币

### 扎帐逻辑
- 扎帐不会改变余额，只是标记交易为"已扎帐"状态
- `/bal` 和 `/mx` 的明细只显示**未结算**交易
- 扎帐后显示"所有交易已扎帐"提示

---

## 📌 后续待办事项（可选）

- [ ] 添加大额交易计时器功能（`/time` 命令）
- [ ] 添加 Web 管理界面
- [ ] 添加定时备份功能
- [ ] 添加多账号支持
- [ ] 添加交易日志导出到 CSV

---

## 📞 与 OpenClaw 的关系

### 当前状态
- OpenClaw 仍安装在全局 (`npm list -g openclaw`)
- 原 `~/.openclaw/` 目录保持不变（作为备份）

### 卸载 OpenClaw（可选）
```bash
npm uninstall -g openclaw
```

**注意**: 卸载 OpenClaw 不会影响本项目运行。

---

**报告完成时间**: 2026-02-21
**项目状态**: ✅ 可投入使用，功能完整
