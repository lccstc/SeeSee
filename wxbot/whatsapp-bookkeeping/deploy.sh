#!/bin/bash
# 生产环境一键部署/更新脚本

echo "开始部署/更新 WhatsApp 机器人..."

# 检查是否传入了压缩包参数
if [ -z "$1" ]; then
    echo "错误: 请提供迁移压缩包的路径。"
    echo "用法: ./deploy.sh <whatsapp-migration-xxxx.tar.gz>"
    exit 1
fi

TAR_FILE="$1"

if [ ! -f "$TAR_FILE" ]; then
    echo "错误: 找不到文件 $TAR_FILE"
    exit 1
fi

# 解压文件，覆盖当前目录的内容
echo ">> 正在解压 $TAR_FILE ..."
tar -xzf "$TAR_FILE"

# 安装 Node 依赖
echo ">> 正在安装依赖包 (npm install)..."
npm install --production --silent

# 编译 TypeScript
echo ">> 正在编译代码 (npm run build)..."
npm run build

# 安装 PM2 (如果还没安装的话)
if ! command -v pm2 &> /dev/null
then
    echo ">> 正在全局安装 PM2..."
    sudo npm install -g pm2
fi

# 使用 PM2 启动或重启服务
echo ">> 正在启动/重启后台服务..."
# 检查是否已经存在同名应用
pm2 describe "whatsapp-bot" > /dev/null
if [ $? -eq 0 ]; then
    pm2 restart "whatsapp-bot"
else
    pm2 start dist/index.js --name "whatsapp-bot"
fi

# 保存 PM2 状态，使其开机自启
pm2 save

echo "=================================================="
echo "部署完成并已在后台运行！"
echo "可以使用 'pm2 logs whatsapp-bot' 查看运行日志。"
echo "=================================================="