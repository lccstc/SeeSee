# 启动顺序 README

这份文档只覆盖当前这套实际运行方式：

- 双入口：`WhatsApp`、`WeChat`
- 单核心：`bookkeeping-platform/reporting_server.py`
- 适配层职责：只收发消息，不做业务结算

## 启动顺序

必须按下面顺序启动：

1. 先启动 PostgreSQL
2. 再启动总账核心 `reporting_server.py`
3. 再启动 `WhatsApp` 薄适配层
4. 最后启动 `WeChat` 薄适配层

不要反过来启动。  
适配层启动时如果连不上 core，`web` 群发和异步出站队列就不会正常消费。

## 第一步：启动总账核心

目录：

```bash
cd "/Users/lcc/SeeSee/wxbot/bookkeeping-platform"
```

启动命令：

```bash
BOOKKEEPING_CORE_TOKEN="test-token-123456" \
BOOKKEEPING_DB_DSN="postgresql:///bookkeeping?user=lcc" \
BOOKKEEPING_MASTER_USERS="+84389225210" \
PYTHONPATH="/Users/lcc/SeeSee/wxbot/bookkeeping-platform" \
"/Users/lcc/SeeSee/wxbot/bookkeeping-platform/.venv/bin/python" \
"/Users/lcc/SeeSee/wxbot/bookkeeping-platform/reporting_server.py" \
  --host 127.0.0.1 \
  --port 8765 \
  --db "postgresql:///bookkeeping?user=lcc"
```

启动后先确认：

- `http://127.0.0.1:8765/` 能打开
- `http://127.0.0.1:8765/workbench` 能打开

## 第二步：启动 WhatsApp 薄适配层

目录：

```bash
cd "/Users/lcc/SeeSee/wxbot/whatsapp-bookkeeping"
```

先检查配置文件：

文件：`/Users/lcc/SeeSee/wxbot/whatsapp-bookkeeping/config.json`

最少要确认这几个字段：

```json
{
  "whatsapp": {
    "authDir": "./auth"
  },
  "logLevel": "info",
  "coreApi": {
    "endpoint": "http://127.0.0.1:8765",
    "token": "test-token-123456",
    "requestTimeoutMs": 5000
  }
}
```

如果刚改过 TypeScript 代码，先重新编译：

```bash
npm run build
```

启动：

```bash
node dist/index.js
```

也可以用：

```bash
npm start
```

说明：

- `WhatsApp` 这层现在会同时处理同步返回动作和异步 `outbound_actions` 队列
- `web` 群发发不出去，优先检查这层是不是没有重启到最新代码
- 同一时间只能保留一个 `node dist/index.js` 实例

## 第三步：启动 WeChat 薄适配层

目录：

```bash
cd "/Users/lcc/SeeSee/wxbot/bookkeeping-platform"
```

先检查配置文件：

文件：`/Users/lcc/SeeSee/wxbot/bookkeeping-platform/config.wechat.json`

重点确认：

- `core_api.endpoint` 指向你的 core，例如 `http://127.0.0.1:8765`
- `core_api.token` 和 `BOOKKEEPING_CORE_TOKEN` 完全一致
- `listen_chats`、`master_users` 已按你的实际群和管理员配置好

启动：

```bash
python -m wechat_adapter.main
```

如果你机器上是指定 Python 路径启动，就用你自己的 Python 可执行文件替换上面这条。

## 推荐重启顺序

如果只是改了 Python 核心：

1. 停 `reporting_server.py`
2. 启 `reporting_server.py`

如果改了 WhatsApp 适配层：

1. 在 `whatsapp-bookkeeping` 下执行 `npm run build`
2. 停掉旧的 `node dist/index.js`
3. 重新启动 `node dist/index.js`

如果改了 WeChat 适配层：

1. 停掉旧的 `python -m wechat_adapter.main`
2. 重新启动 `python -m wechat_adapter.main`

如果不确定影响范围，直接按完整顺序重启：

1. 停 `WhatsApp`
2. 停 `WeChat`
3. 停 `reporting_server.py`
4. 启 `reporting_server.py`
5. 启 `WhatsApp`
6. 启 `WeChat`

## 当前功能说明

### Web 一键结账

- `web` 一键结账现在是直接调用 core 关账
- 不再模拟往群里发送 `/alljs`
- 所以不会再把结账回执扩散到其它群

### Web 群发

- `web` 群发等价于让 core 写入异步出站队列
- 真正发消息的是 `WhatsApp` / `WeChat` 薄适配层
- 所以 core 启了但适配层没启动时，群发会入队，但不会发出

## 常见问题

### 1. `web` 可以操作，但群发没发出去

优先检查：

1. `reporting_server.py` 是否启动
2. `WhatsApp` 或 `WeChat` 薄适配层是否启动
3. 适配层里的 token 是否和 core 一致
4. 是否同时开了多个适配层实例导致冲突

### 2. WhatsApp 扫码后又掉线

常见原因：

- 同时开了多个 `node dist/index.js`
- 老进程没停干净
- `auth` 目录状态损坏

### 3. WeChat 能收消息，但 web 群发不落地

优先检查：

- `config.wechat.json` 里的 `core_api.endpoint`
- `config.wechat.json` 里的 `core_api.token`
- `reporting_server.py` 是否已经重启到最新代码

## 最短启动版

你平时只需要记住这三步：

1. 先启动 core：`reporting_server.py`
2. 再启动 WhatsApp：`node dist/index.js`
3. 最后启动 WeChat：`python -m wechat_adapter.main`
