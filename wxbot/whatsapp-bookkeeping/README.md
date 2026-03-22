# WhatsApp Bookkeeping

WhatsApp 侧现在只保留 V2 薄适配层职责：

- 接收 WhatsApp 消息
- 归一化成 `NormalizedMessageEnvelope`
- 调用 Python 总账中心 `POST /api/core/messages`
- 执行返回的 `send_text` / `send_file` 动作

本仓库不再维护任何 V1 本地记账、SQLite 账本或兼容同步链路。

## 安装与运行

```bash
npm install
npm test
npm run build
npm start
```

## 配置

编辑 `config.json`：

```json
{
  "whatsapp": {
    "authDir": "./auth"
  },
  "masterPhone": "+84389225210",
  "masterPhones": ["+84389225210", "+85257006866"],
  "logLevel": "info",
  "coreApi": {
    "endpoint": "https://your-domain.com",
    "token": "replace-with-core-token",
    "requestTimeoutMs": 5000
  }
}
```

配置说明：

- `whatsapp.authDir`：WhatsApp 多文件认证目录
- `masterPhone`：兼容旧配置保留字段
- `masterPhones`：多管理员列表
- `logLevel`：日志级别
- `coreApi.endpoint`：总账中心根地址，运行时会自动请求 `POST /api/core/messages`
- `coreApi.token`：总账中心 Bearer Token
- `coreApi.requestTimeoutMs`：单次请求超时时间

## V2 运行链路

当前唯一支持的运行链路：

```text
WhatsApp message
  -> normalizeMessage()
  -> POST /api/core/messages
  -> CoreAction[]
  -> sendMessage / sendFile
```

返回动作目前支持：

- `send_text`
- `send_file`

## 真机验证

1. 在总账中心启动 `bookkeeping-platform`
2. 确认总账中心可访问，且 `coreApi.token` 与服务端 Bearer Token 一致
3. 启动本适配器并保持登录态
4. 在测试群发送一条简单消息，例如 `+100rmb`
5. 验证总账中心出现对应入账或返回动作

## 首次使用

1. 运行 `npm start`
2. 终端会显示二维码
3. 用 WhatsApp 扫码登录
4. 登录后适配器会开始监听消息并转发到 V2 总账入口

## 回归验证

```bash
npm test
npm run build
```
