# Mac 到 Windows 文件传输指南（SSH/SCP）

本文档用于记录并复用 `Mac -> Windows` 的局域网文件传输流程。

## 1. 适用场景

- 两台设备在同一局域网（同一 Wi-Fi/同一路由器）
- Mac 作为发送端
- Windows 作为接收端
- 通过 SSH + SCP 传输整个项目目录

## 2. Windows 端一次性配置（管理员 PowerShell）

```powershell
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic
New-NetFirewallRule -Name sshd -DisplayName "OpenSSH Server (sshd)" -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 -Profile Any
```

查看 Windows IP：

```powershell
ipconfig
```

查看登录用户名（用于 SSH）：

```powershell
whoami
```

例如输出：`robet\\lccst`

## 3. Mac 端连通性测试

先测试 22 端口是否可达：

```bash
nc -vz "192.168.100.96" 22
```

测试 SSH 登录（示例用户 `wx_ssh`）：

```bash
ssh "wx_ssh@192.168.100.96"
```

首次连接出现指纹提示时输入：`yes`

## 4. 传输命令（SCP）

把 Mac 本地目录传到 Windows 桌面：

```bash
scp -r "/Users/lcc/macwechat" "wx_ssh@192.168.100.96:/C:/Users/wx_ssh/Desktop/"
```

### 常用模板

```bash
scp -r "<Mac源目录>" "<Windows用户>@<WindowsIP>:/C:/Users/<Windows用户>/Desktop/"
```

## 5. 可选：使用 rsync（显示更详细进度）

```bash
rsync -avz --progress -e ssh "/Users/lcc/macwechat/" "wx_ssh@192.168.100.96:/C:/Users/wx_ssh/Desktop/macwechat/"
```

## 6. 常见问题排查

### 6.1 `Operation timed out`

原因通常是网络不通、`sshd` 未启动或防火墙未放行。

排查：

1. Windows 执行 `Get-Service sshd`
2. Windows 执行 `netstat -ano | findstr :22`，确认 `LISTENING`
3. Mac 执行 `nc -vz <WindowsIP> 22`

### 6.2 `Permission denied (publickey,password,keyboard-interactive)`

原因通常是用户名格式或认证方式不匹配。

排查：

1. Windows `whoami` 确认真实用户名
2. 先用 `ssh` 单独登录测试，再跑 `scp`
3. 必要时检查 `C:\ProgramData\ssh\sshd_config` 中：
   - `PasswordAuthentication yes`

修改后重启：

```powershell
Restart-Service sshd
```

## 7. 安全建议

- 建议专门创建传输账号（如 `wx_ssh`），最小权限使用。
- 密码不要在聊天或文档中明文保存。
- 若密码已泄露，立即修改。
- 后续可升级为 SSH 密钥登录，减少密码输入并提升安全性。

## 8. 传输后检查清单

1. 目录结构是否完整
2. 是否包含隐藏文件（如 `.env`）
3. 新机器是否重新安装依赖（不要直接复用跨平台虚拟环境/构建产物）

