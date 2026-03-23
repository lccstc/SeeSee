# 最新启动手册：总账、WeChat、WhatsApp

这份文档按 2026-03-22 当前 `main` 分支的代码状态整理。

目标不是讲架构，而是让你能按步骤把系统跑起来。

## 先用一句话理解这套系统

你现在的系统可以理解成 3 个部分：

1. 总账中心
它是“大脑”和“总账本”，真正记账、算账、回消息动作都在这里做。

2. WeChat 适配器
它负责把微信消息拿出来，发给总账中心，再把总账中心返回的动作发回微信。

3. WhatsApp 适配器
它负责把 WhatsApp 消息拿出来，发给总账中心，再把总账中心返回的动作发回 WhatsApp。

所以顺序永远是：

```text
先启动总账中心
再启动 WeChat / WhatsApp 适配器
最后发消息测试
```

## 先记住 4 个最重要的事实

1. 总账中心必须先启动。
如果总账没开，WeChat 和 WhatsApp 都不知道把消息发给谁。

2. 现在正式入口只有一个：
`POST /api/core/messages`

3. WhatsApp 已经没有本地管理员配置。
`wxbot/whatsapp-bookkeeping/config.json` 里不再配置管理员。

4. 管理员权限分两层，不要混淆：
- 总账管理员：由 `BOOKKEEPING_MASTER_USERS` 或 `--master-user` 决定，影响真正的业务命令权限。
- WeChat 适配器管理员：由 `config.wechat.json` 里的 `master_users` 决定，主要影响 WeChat 适配器自己的控制命令，比如 `/groups`、`/jhqz`、`/qxqz`。

## 你需要准备什么

### 总账中心机器

当前仓库路径：

```text
/Users/lcc/SeeSee/wxbot/bookkeeping-platform
```

这台机器负责运行：

- `reporting_server.py`
- 数据库
- Web 页面

### WeChat 机器

WeChat 适配器代码在：

```text
/Users/lcc/SeeSee/wxbot/bookkeeping-platform/wechat_adapter
```

但从代码依赖看，它使用 `wxautox` 和 Windows 风格运行目录。
这意味着它通常应该跑在装了 PC 微信的 Windows 机器上。

### WhatsApp 机器

当前仓库路径：

```text
/Users/lcc/SeeSee/wxbot/whatsapp-bookkeeping
```

这边需要 Node.js 和 npm。

## 第 1 部分：启动总账中心

### 第一步：打开目录

```bash
cd "/Users/lcc/SeeSee/wxbot/bookkeeping-platform"
```

### 第二步：用现在这套测试配置启动

如果你现在就是本地联调，直接用这条：

```bash
BOOKKEEPING_CORE_TOKEN="test-token-123456" \
BOOKKEEPING_DB_DSN="postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping" \
BOOKKEEPING_MASTER_USERS="+852389225210" \
python3 "/Users/lcc/SeeSee/wxbot/bookkeeping-platform/reporting_server.py" \
  --host "0.0.0.0" \
  --port 8765 \
  --db "postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping"
```

### 这条命令每一部分是什么意思

- `BOOKKEEPING_CORE_TOKEN`
给 WeChat / WhatsApp 调用总账接口时用的令牌。两边必须和这里完全一样。

- `BOOKKEEPING_MASTER_USERS`
给总账中心设置初始管理员。这里的值会影响真正的业务权限。

- `--host "0.0.0.0"`
表示允许别的机器访问这台服务。
如果你只想本机访问，也可以用默认 `127.0.0.1`。

- `--port 8765`
总账服务端口。

- `--db "postgresql://..."`
总账正式 PostgreSQL DSN。

### 启动前必须先做的事

先把当前版本的 `sql/postgres_schema.sql` 应用到目标 PostgreSQL。

现在运行时代码只接受当前版本 schema：

- 不再自动补列
- 不再自动补历史账期
- 不再在启动时尝试升级旧库

### 第三步：确认它真的启动成功

终端里应该看到类似：

```text
Reporting center running at http://0.0.0.0:8765
```

然后你可以在浏览器打开：

- [首页](http://127.0.0.1:8765/)
- [账期工作台](http://127.0.0.1:8765/workbench)
- [历史页](http://127.0.0.1:8765/history)

只要页面能打开，就说明总账中心基本活着。

## 第 2 部分：启动 WeChat 适配器

## 先理解 WeChat 这一层在干什么

它不是总账本。
它更像“微信搬运工”：

```text
微信消息
-> WeChat 适配器
-> 总账中心 /api/core/messages
-> 总账返回动作
-> WeChat 适配器把动作发回微信
```

### 第一步：准备 `config.wechat.json`

配置文件路径：

[config.wechat.json](/Users/lcc/SeeSee/wxbot/bookkeeping-platform/config.wechat.json)

当前代码会自动从这里读取配置。

推荐你至少保证这些字段正确：

```json
{
  "listen_chats": [
    "皇家议事厅【1111】"
  ],
  "master_users": [
    "Button-Leo",
    "wxid_rxmr4d9autu622"
  ],
  "poll_interval_seconds": 1.0,
  "log_level": "INFO",
  "language": "cn",
  "export_dir": "C:\\wxbot\\bookkeeping-platform\\exports",
  "runtime_dir": "C:\\wxbot\\bookkeeping-platform\\runtime",
  "core_api": {
    "endpoint": "https://your-ngrok-or-domain",
    "token": "test-token-123456",
    "request_timeout_seconds": 5.0
  }
}
```

### 这些字段分别是什么意思

- `listen_chats`
WeChat 要监听哪些群。
群名必须和你微信里看到的名字一致。

- `master_users`
这是 WeChat 适配器自己的管理员名单。
主要用来控制 `/groups`、`/jhqz`、`/qxqz` 这种“管理监听群”的命令。

- `runtime_dir`
WeChat 运行缓存目录。

- `core_api.endpoint`
总账中心的根地址。
如果 WeChat 和总账不在同一台机器上，这里通常填你的 ngrok 地址或外网域名。

- `core_api.token`
必须和总账启动时的 `BOOKKEEPING_CORE_TOKEN` 一模一样。

### 第二步：启动 WeChat 适配器

README 里的现行命令是 Windows 形式：

```powershell
C:\Users\lccst\AppData\Local\Programs\Python\Python311\python.exe -m wechat_adapter.main
```

更一般地说，你需要在 `bookkeeping-platform` 根目录下运行：

```powershell
cd "C:\wxbot\bookkeeping-platform"
python -m wechat_adapter.main
```

如果你机器上是固定 Python 路径，也可以像 README 那样写完整路径。

### 第三步：确认 WeChat 真的连上了

正常情况下，日志会出现这些意思：

- 正在监听哪些群
- WeChat 自己的身份信息
- 当前是 `remote core mode`

其中最重要的是看到类似：

```text
WeChat adapter running in remote core mode: https://你的总账地址
```

这表示它不是本地自己记账，而是把消息发给总账中心。

### 第四步：怎么在 WeChat 里做最小测试

先在 `listen_chats` 里的一个测试群发：

```text
/set 2
```

再发一条：

```text
+100rmb
```

你要观察 3 件事：

1. WeChat 适配器日志没有报错
2. 总账中心终端没有报错
3. 总账页面或数据库里出现新的记录

### WeChat 适配器专属控制命令

这些命令属于 WeChat 适配器自己，不是总账通用命令：

- `/groups`
查看当前监听名单

- `/jhqz 群名`
激活一个新的监听群

- `/qxqz 群名`
取消一个监听群

注意：
这些命令受 `config.wechat.json` 里的 `master_users` 控制。

## 第 3 部分：启动 WhatsApp 适配器

## 先理解 WhatsApp 这一层在干什么

现在的 WhatsApp 已经是纯 V2 薄适配层了。
意思就是：

- 它不再自己保存旧账本
- 不再走旧同步接口
- 它只负责收消息、转发给总账、执行返回动作

### 第一步：打开配置文件

配置文件路径：

[config.json](/Users/lcc/SeeSee/wxbot/whatsapp-bookkeeping/config.json)

当前格式应该像这样：

```json
{
  "whatsapp": {
    "authDir": "./auth"
  },
  "logLevel": "info",
  "coreApi": {
    "endpoint": "https://your-domain.com",
    "token": "test-token-123456",
    "requestTimeoutMs": 5000
  }
}
```

### 第二步：把 `coreApi.endpoint` 配对好

你有两种常见情况：

#### 情况 A：WhatsApp 和总账在同一台机器

填：

```json
"endpoint": "http://127.0.0.1:8765"
```

#### 情况 B：WhatsApp 在别的机器，访问远端总账

填：

```json
"endpoint": "https://你的-ngrok-或外网域名"
```

### 第三步：确认 token 一样

这里：

```json
"token": "test-token-123456"
```

必须和总账启动命令里的：

```bash
BOOKKEEPING_CORE_TOKEN="test-token-123456"
```

完全一致，一个字符都不能错。

### 第四步：安装依赖

第一次跑或者依赖变了，先执行：

```bash
cd "/Users/lcc/SeeSee/wxbot/whatsapp-bookkeeping"
npm install
```

### 第五步：编译

```bash
cd "/Users/lcc/SeeSee/wxbot/whatsapp-bookkeeping"
npm run build
```

### 第六步：启动

```bash
cd "/Users/lcc/SeeSee/wxbot/whatsapp-bookkeeping"
npm start
```

### 第七步：第一次登录

第一次运行，终端会显示二维码。

你要做的是：

1. 打开手机 WhatsApp
2. 进入 Linked Devices
3. 扫终端二维码
4. 等待终端显示连接成功

认证文件会放在 `auth/` 目录里，后面通常不用反复扫码。

### 第八步：怎么做最小测试

在测试群发：

```text
+100rmb
```

或者先发：

```text
/set 2
```

如果链路通了，应该发生这些事：

1. WhatsApp 适配器没有报错
2. 总账中心收到请求
3. 总账页面或数据库里出现对应变化

## 第 4 部分：推荐的启动顺序

如果你只想“今天赶紧测通”，就严格按这个顺序：

1. 启动总账中心
2. 在浏览器打开首页，确认总账活着
3. 配好 WeChat 的 `config.wechat.json`
4. 启动 WeChat 适配器
5. 配好 WhatsApp 的 `config.json`
6. 启动 WhatsApp 适配器
7. 先在测试群发一条最简单的消息
8. 打开总账页面确认有没有写进去

## 第 5 部分：最容易搞混的 6 个点

### 1. 为什么总账必须先开

因为 WeChat 和 WhatsApp 都不是“自己记账”。
它们只是把消息交给总账。

### 2. 为什么我发消息没反应

最常见原因只有这几个：

- 总账没启动
- `endpoint` 填错
- `token` 不一致
- 群没有被监听
- 发送者没有权限

### 3. 为什么 WeChat 里有 `master_users`，WhatsApp 却没有

因为当前代码里：

- WeChat 适配器自己还保留了一层“控制监听群”的管理命令
- WhatsApp 适配器已经收缩成纯转发层，不再自己维护管理员配置

### 4. 总账管理员和 WeChat 管理员是同一个东西吗

不是完全一样。

- 总账管理员：控制真正的业务权限
- WeChat 管理员：控制 WeChat 适配器自己的监听群管理命令

### 5. WeChat 现在还需要 `db_path` 吗

不需要。

当前 WeChat 适配器只支持 remote core mode。
真正主数据库只有总账中心启动时使用的 PostgreSQL DSN。

### 6. WhatsApp 现在还会不会走旧接口

不会。

当前正式链路只走：

```text
/api/core/messages
```

## 第 6 部分：你现在最推荐直接照抄的命令

### 总账中心

```bash
cd "/Users/lcc/SeeSee/wxbot/bookkeeping-platform"

BOOKKEEPING_CORE_TOKEN="test-token-123456" \
BOOKKEEPING_DB_DSN="postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping" \
BOOKKEEPING_MASTER_USERS="+852389225210" \
python3 "/Users/lcc/SeeSee/wxbot/bookkeeping-platform/reporting_server.py" \
  --host "0.0.0.0" \
  --port 8765 \
  --db "postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping"
```

### WeChat

```powershell
cd "C:\wxbot\bookkeeping-platform"
python -m wechat_adapter.main
```

前提：
- `config.wechat.json` 已经配好
- `core_api.endpoint` 能访问总账
- `core_api.token` 和总账一致

### WhatsApp

```bash
cd "/Users/lcc/SeeSee/wxbot/whatsapp-bookkeeping"
npm install
npm run build
npm start
```

前提：
- `config.json` 已经配好
- `coreApi.endpoint` 能访问总账
- `coreApi.token` 和总账一致

## 最后一句

如果你现在只想做最小验证，不要三头一起乱开。

最稳的方式是：

1. 只开总账
2. 确认网页能打开
3. 再开一个适配器
4. 只发一条最简单的测试消息
5. 确认总账里有结果
6. 然后再开另一个适配器

这样一出问题，你马上知道是哪一层坏了。
