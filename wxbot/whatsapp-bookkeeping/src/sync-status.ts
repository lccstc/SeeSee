import type { SyncStatusSummary } from "./database.js";

export function formatSyncStatusReport(summary: SyncStatusSummary): string {
  const lines = [
    `待发送：${summary.pendingCount}`,
    `重试中：${summary.retryingCount}`,
  ];

  if (summary.lastFailedAt) {
    lines.push(`最近失败：${summary.lastFailedAt}`);
  }

  if (summary.lastError) {
    lines.push(`失败原因：${summary.lastError}`);
  }

  if (summary.lastSentAt) {
    lines.push(`最近成功：${summary.lastSentAt}`);
  }

  return lines.join("\n");
}
