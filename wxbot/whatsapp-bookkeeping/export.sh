#!/bin/bash
# 导出项目核心数据和代码用于迁移

echo "开始打包 WhatsApp Bookkeeping 项目..."

# 生成带有时间戳的文件名
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
TAR_FILE="whatsapp-migration-${TIMESTAMP}.tar.gz"

# 需要打包的目录和文件（排除没必要的大文件）
tar --exclude='node_modules' \
    --exclude='dist' \
    --exclude='.git' \
    --exclude='*.db-shm' \
    --exclude='*.db-wal' \
    -czf "${TAR_FILE}" \
    .

echo "=================================================="
echo "打包成功！"
echo "已生成迁移包：${TAR_FILE}"
echo "请将此文件发送到您的生产机（如公司的 Mac mini 或服务器）。"
echo "=================================================="
