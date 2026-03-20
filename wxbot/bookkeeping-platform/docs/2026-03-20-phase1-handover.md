# 2026-03-20 一期总账中心交接文档

## 1. 这次工作的背景

本轮工作的起点不是单纯做一个数据库，而是围绕用户当前的真实业务痛点展开：

- 现有系统以 `WhatsApp` 和 `WeChat` 作为入口。
- 系统本质上是一个“通过聊天入口做插件式记账”的业务系统。
- 用户想把这套系统做成结构化系统，而不是继续依赖人工在表格里抄账、算账、汇总。
- 用户后续想在统一数据库上继续做 Web 后台，支持标准化操作。
- 用户明确说过：未来想要的数据不止账单，还包括卡片分类、卡片价格、客户群、供应商群、客户编组、价格筛选、消息采集、后续对账等。

用户的长期目标不是“改造某个机器人”，而是：

**把业务从人工表格中解放出来，先做一个总账中心，再逐步扩成完整后台系统。**

## 2. 用户原始需求和逐步澄清后的真实需求

### 2.1 最开始提出的需求

用户最初提出：

- 现有项目使用 `WhatsApp` 和 `WeChat` 当入口。
- 使用插件进行记账。
- 想调查两个入口对“数据存储模式”是否一致。
- 想设计一个新的数据库，统一存储两个入口采集来的信息。
- 后续基于这个数据库建设后台系统，后台通过 Web 页面做标准化操作。
- 想管理的数据不只账单，还包括卡片分类、卡片价格等。

### 2.2 对业务目标的进一步澄清

随着讨论推进，用户逐步明确了几件更关键的事：

1. 用户真正最在意的不是“命令文本”，而是命令最终形成的“账单结果”。
2. 用户并不想一开始做很复杂的 ERP，而是想先替代人工维护的账单表。
3. 用户说得最明确的一句话是：

   **“我其实也不是很理解是否是正确的，但是我的一个想法就是先把我们的业务从人工表格上解放出来。”**

4. 财务反馈的核心痛点是：
   - 当前每个群的余额要手工去看
   - 范围是“前一天扎账时间到今天扎账时间”
   - 现在的表很笨，需要每个群进去输入做了多少
   - 其实只要系统给出“每个客户群内余额”和“每个供应商群内余额”就行

### 2.3 由财务反馈反推出来的真实一期目标

从财务反馈中得到的关键业务洞察：

- 财务最在意的是：
  - 哪个群是多少
  - 这个群这一期发生了什么
  - 扎账前后余额有没有问题
- 真正的核心对象不是“聊天消息”，而是“账期结果”
- 账期边界不是自然日，也不是固定时间，而是：

  **按每次实际扎账切分**

- 现有人工表是按群抄写和汇总的，因此后台的一期首页应该围绕“群”来展开，而不是围绕“消息”展开。

## 3. 代码库现状调研结论

本次调研只看了 `wxbot` 目录里的两套主系统。

### 3.1 `whatsapp-bookkeeping`

路径：

- [/Users/lcc/SeeSee/wxbot/whatsapp-bookkeeping](/Users/lcc/SeeSee/wxbot/whatsapp-bookkeeping)

结论：

- 这是单入口思路。
- 技术栈是 TypeScript + SQLite。
- 存的是已经形成的记账结果、群组、白名单、绑定、提醒等。
- 典型数据库文件是：
  - [/Users/lcc/SeeSee/wxbot/whatsapp-bookkeeping/data/bookkeeping.db](/Users/lcc/SeeSee/wxbot/whatsapp-bookkeeping/data/bookkeeping.db)
- 这套实现并没有形成真正的“统一总库”，更像是单入口专用账本。

### 3.2 `bookkeeping-platform`

路径：

- [/Users/lcc/SeeSee/wxbot/bookkeeping-platform](/Users/lcc/SeeSee/wxbot/bookkeeping-platform)

结论：

- 这是更接近统一核心的方向。
- 技术栈是 Python + SQLite。
- `wechat_adapter` 只负责接入，`bookkeeping_core` 提供统一业务逻辑。
- 说明 WeChat 这边已经开始往“统一核心 + 多入口接入”演进。
- 但数据库层仍然偏运行时账本，离“总账中心”还有距离。

### 3.3 关于“两边存储模式是否一致”的调研结论

答案是：

- **不完全一致**
- 但 **WeChat 新平台已经明显比旧 WhatsApp 实现更接近统一核心**

具体看：

- WhatsApp 旧库结构更偏单入口本地账本
- WeChat 新核心已经有这些统一字段和概念：
  - `platform`
  - `group_key`
  - `chat_id`
  - `chat_name`
  - `sender_name`
  - `message_id`
  - `identity_bindings`
  - `admins`

所以本次实现没有另起一个全新工程，而是选择：

**在 `bookkeeping-platform` 这个统一核心方向上继续加一期能力**

## 4. 基础业务结论

### 4.1 不要先追求“完整经营系统”

本次讨论后，已经明确：

- 第一阶段不要追求复杂后台
- 第一阶段不要追求完整对账
- 第一阶段不要追求卡片价格中心全部做完
- 第一阶段先替代人工账表

### 4.2 群是最小业务单位

财务最关心的是：

- 每个群当前余额
- 每个群一个账期内的收款
- 每个群一个账期内的使用
- 每个群账期结束时的余额

### 4.3 账期边界规则

用户明确确认：

- 账期边界按“每次实际扎账”切分
- 不是自然日
- 不是固定扎账时刻

### 4.4 客户/供应商不能简单按平台判断

用户明确说明：

- 之前曾说过 “WeChat 大多是客户、WhatsApp 大多是供应商”
- 但这不是绝对规则
- 真正更可靠的是系统内部的 `/set` 分组号

### 4.5 分组号也不是固定业务标签

这点非常关键，用户后面又补充了更细的信息：

- 分组号不是永远固定映射成“客户/供应商”
- 实际上用户希望把每个数字分组看成一个“模块”
- 后台要支持自由组合，例如：
  - `1+3+4`
  - `5+7`
- 未来财务看账，很多时候是按“分组组合口径”来看，而不是按单一数字组直接看

这意味着一期系统必须支持两层：

1. 基础分组：每个群有一个基础分组号
2. 组合视图：多个基础分组号可以组成一个业务汇总口径

## 5. 最终收敛出的一期目标

本轮讨论最终收敛出的一期目标是：

### 5.1 一期真正要解决的问题

**把现在依赖人工维护的账单表，改成系统自动生成。**

### 5.2 一期系统应该先做到

- 统一收集 `WhatsApp` 和 `WeChat` 的记账相关结果
- 以“每次实际扎账”为账期边界自动汇总
- 自动产出财务最关心的内容：
  - 每个群当前余额
  - 每个群本账期收款合计
  - 每个群本账期使用合计
  - 每个群账期结束余额
  - 按组合分组汇总后的总余额
- 支持人工修正
- 支持多人协同
- 导入历史数据

### 5.3 一期暂时不正式做

- 完整对账模型
- 价格筛选中心
- 复杂消息识别
- 客户/供应商自动识别
- 完整权限系统
- 正式 PostgreSQL 运行时切换

## 6. 用户关于部署和数据库的关键信息

讨论中用户补充了部署条件：

- 一台 `M2 8GB Mac`，原本想作为中心库候选
- 一台较弱的 WeChat 设备，只适合做轻接入
- 当前和模型交互的机器是 `M4 24GB Mac Air`
- 用户后来表示：独立服务器暂时可以先放在这台 `M4` 上，后面再迁移

所以本次给出的建议是：

- 接入节点可以轻量
- 中心总库和后台更适合放在 `M4`
- 长期目标库选 `PostgreSQL`

但是为了快速把一期业务跑起来，这次实际落地仍然先在现有统一核心上继续使用了 SQLite 运行时。

## 7. 本次实际实现了什么

本轮不是只做了文档或方案，而是已经在代码里做了一版可运行的一期最小实现。

### 7.1 实现原则

因为代码库里已经有统一核心雏形，所以本次没有新建一个完全独立的系统，而是选择：

**在 `bookkeeping-platform` 上扩展一期能力**

路径主要集中在：

- [/Users/lcc/SeeSee/wxbot/bookkeeping-platform/bookkeeping_core/database.py](/Users/lcc/SeeSee/wxbot/bookkeeping-platform/bookkeeping_core/database.py)
- [/Users/lcc/SeeSee/wxbot/bookkeeping-platform/bookkeeping_core/reporting.py](/Users/lcc/SeeSee/wxbot/bookkeeping-platform/bookkeeping_core/reporting.py)
- [/Users/lcc/SeeSee/wxbot/bookkeeping-platform/bookkeeping_core/importers.py](/Users/lcc/SeeSee/wxbot/bookkeeping-platform/bookkeeping_core/importers.py)
- [/Users/lcc/SeeSee/wxbot/bookkeeping-platform/bookkeeping_web/app.py](/Users/lcc/SeeSee/wxbot/bookkeeping-platform/bookkeeping_web/app.py)

### 7.2 数据库层新增能力

在 `database.py` 中新增和扩展了这些内容：

1. 给 `transactions` 增加了账期关联字段：
   - `settlement_id`
   - `settled_at`

2. 新增了人工修正表：
   - `manual_adjustments`

3. 新增了组合分组相关表：
   - `group_combinations`
   - `group_combination_items`

4. 增强了结算逻辑：
   - `settle_transactions(...)` 现在会把交易和实际结算记录关联起来
   - 支持传入显式 `settled_at`

5. 增强了 `add_transaction(...)`
   - 支持导入时写入历史 `created_at`
   - 支持写入导入时的 `settled`、`settlement_id` 等状态

6. 增加了老数据回填逻辑：
   - `_backfill_settlement_links()`

### 7.3 报表服务层

新增文件：

- [/Users/lcc/SeeSee/wxbot/bookkeeping-platform/bookkeeping_core/reporting.py](/Users/lcc/SeeSee/wxbot/bookkeeping-platform/bookkeeping_core/reporting.py)

新增能力：

1. `get_current_group_rows()`
   - 计算每个群当前余额
   - 会把人工修正叠加进去

2. `get_period_group_rows(settlement_id)`
   - 按“某次实际扎账”返回该账期的结果
   - 结果包含：
     - 期初余额
     - 收款
     - 使用
     - 期末余额

3. `get_combination_summary(group_numbers, label)`
   - 支持把多个分组号做成一个组合汇总

4. `list_combination_summaries()`
   - 列出已保存的组合口径

5. `build_dashboard_payload()`
   - 提供 Web 后台看板所需的整体数据

### 7.4 老 WhatsApp 数据导入

新增文件：

- [/Users/lcc/SeeSee/wxbot/bookkeeping-platform/bookkeeping_core/importers.py](/Users/lcc/SeeSee/wxbot/bookkeeping-platform/bookkeeping_core/importers.py)
- [/Users/lcc/SeeSee/wxbot/bookkeeping-platform/import_legacy.py](/Users/lcc/SeeSee/wxbot/bookkeeping-platform/import_legacy.py)

当前实现了：

- 从旧 `whatsapp-bookkeeping` 的 SQLite 库导入：
  - 群
  - 交易
  - 扎账记录

注意：

- 这次只做了 `WhatsApp` 旧库导入
- `WeChat` 历史导入还没有正式实现

### 7.5 最小 Web 后台

新增目录和文件：

- [/Users/lcc/SeeSee/wxbot/bookkeeping-platform/bookkeeping_web/__init__.py](/Users/lcc/SeeSee/wxbot/bookkeeping-platform/bookkeeping_web/__init__.py)
- [/Users/lcc/SeeSee/wxbot/bookkeeping-platform/bookkeeping_web/app.py](/Users/lcc/SeeSee/wxbot/bookkeeping-platform/bookkeeping_web/app.py)
- [/Users/lcc/SeeSee/wxbot/bookkeeping-platform/reporting_server.py](/Users/lcc/SeeSee/wxbot/bookkeeping-platform/reporting_server.py)

当前这个最小 Web 后台支持：

1. 查看当前群余额
2. 查看最近账期结果
3. 提交人工修正
4. 新建组合分组

这个后台是标准库 WSGI 版本，目的不是最终 UI，而是先把一期能力跑通。

### 7.6 PostgreSQL schema 草案

新增文件：

- [/Users/lcc/SeeSee/wxbot/bookkeeping-platform/sql/postgres_schema.sql](/Users/lcc/SeeSee/wxbot/bookkeeping-platform/sql/postgres_schema.sql)

这份文件做了什么：

- 把这次一期涉及的数据结构同步成 PostgreSQL 版本草案
- 方便后续真正切 PostgreSQL 时，不需要重新从零建模

注意：

- 当前运行时代码还没有切到 PostgreSQL
- 只是先同步了正式主库 schema 草案

## 8. 本次已经新增的测试

新增测试文件：

- [/Users/lcc/SeeSee/wxbot/bookkeeping-platform/tests/test_reporting.py](/Users/lcc/SeeSee/wxbot/bookkeeping-platform/tests/test_reporting.py)
- [/Users/lcc/SeeSee/wxbot/bookkeeping-platform/tests/test_webapp.py](/Users/lcc/SeeSee/wxbot/bookkeeping-platform/tests/test_webapp.py)

测试覆盖了：

1. 按实际扎账切账期
2. 人工修正会影响账期结果
3. 分组组合汇总
4. WhatsApp 老库导入
5. Web 看板接口
6. Web 修正接口
7. 组合分组接口

## 9. 本次执行过的验证

本轮已经实际跑过：

```bash
PYTHONPATH="/Users/lcc/SeeSee/wxbot/bookkeeping-platform" python3 -m unittest discover -s "/Users/lcc/SeeSee/wxbot/bookkeeping-platform/tests" -p 'test_*.py'
```

结果：

- 7 个测试通过

还执行过：

```bash
PYTHONPATH="/Users/lcc/SeeSee/wxbot/bookkeeping-platform" python3 -m py_compile ...
```

结果：

- 新增 Python 文件语法通过

## 10. 当前存在的问题 / 用户已经明确表示还需要进一步讨论的点

用户在当前窗口最后明确指出：

**“有一些不对，有很多问题我需要和你探讨，我先不进行测试。”**

这说明：

- 当前这版实现只是“按一期理解先落了一版”
- 还没有进入用户验收阶段
- 下一个窗口的重点不是继续盲目扩功能，而是：

  **先逐条对照用户真实业务，确认这版哪些理解是对的，哪些理解偏了**

### 10.1 高概率需要重新确认的点

以下内容很可能是下一个窗口需要重点讨论的风险点：

1. 财务真正想看的“收款 / 使用 / 余额”口径，是否与当前实现完全一致
2. 当前账期结果是否应该严格围绕“扎账结果表”来构建，而不是以交易表为主推导
3. `manual_adjustments` 的修正方式是否符合财务操作习惯
4. 组合分组是“只用于看板汇总”还是未来还会影响账期口径
5. 用户到底希望“只替代人工汇总表”，还是想顺便把“结果录入方式”也一起替代
6. WeChat 历史数据导入应该怎么做，目前还没有正式实现
7. PostgreSQL 是正式目标，但当前运行时仍是 SQLite，用户是否接受这种过渡方案
8. 当前最小 Web 后台是否符合用户预期，还是只需要先导出报表

## 11. 当前可运行入口

### 11.1 启动总账中心页面

```bash
PYTHONPATH="/Users/lcc/SeeSee/wxbot/bookkeeping-platform" \
python3 "/Users/lcc/SeeSee/wxbot/bookkeeping-platform/reporting_server.py"
```

默认地址：

- `http://127.0.0.1:8765`

### 11.2 导入旧 WhatsApp 账单库

```bash
PYTHONPATH="/Users/lcc/SeeSee/wxbot/bookkeeping-platform" \
python3 "/Users/lcc/SeeSee/wxbot/bookkeeping-platform/import_legacy.py" "/path/to/old/bookkeeping.db"
```

## 12. 给下一个窗口的建议工作顺序

下一个窗口建议严格按下面顺序推进，不要直接继续写代码：

1. 先和用户逐条确认：
   - 财务现在那张手工表到底怎么用
   - 哪些列是自动算出来的
   - 哪些列是人工补进去的
   - 用户说“有一些不对”具体是哪些地方不对

2. 再复核当前一期理解是否正确：
   - 是不是应该继续围绕“自动出账表”
   - 还是应该换成“自动抄群余额 + 自动生成日报”

3. 然后按用户反馈决定是否：
   - 修正现有数据库和汇总口径
   - 保留现有实现，只调整展现方式
   - 回退部分不合适的设计

4. 如果用户认可整体方向，再进入真实数据库接入和真实数据试跑

## 13. 一句话总结

这次工作的本质不是做了一个“最终系统”，而是：

**基于用户“先把业务从人工表格里解放出来”的目标，在现有统一核心上先落了一版最小的总账中心雏形。**

它已经具备：

- 按实际扎账切账期
- 按群看余额
- 分组组合汇总
- 人工修正
- WhatsApp 老库导入
- 最小 Web 看板

但用户已经明确表示还有不少地方要继续讨论，因此下一窗口的重点应该是：

**先对齐业务口径，再决定保留哪些实现、调整哪些实现。**
