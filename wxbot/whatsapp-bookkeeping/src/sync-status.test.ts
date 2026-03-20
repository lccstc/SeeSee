import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import test from "node:test";

import { BookkeepingDB } from "./database.ts";
import { createLedgerSyncEvent } from "./sync.ts";
import { formatSyncStatusReport } from "./sync-status.ts";

test("getSyncStatusSummary reports pending retry, last failure, and last success", () => {
  const tempDir = mkdtempSync(join(tmpdir(), "wa-sync-status-"));
  const db = new BookkeepingDB(join(tempDir, "bookkeeping.db"));

  try {
    const failedId = db.enqueueSyncEvent(
      createLedgerSyncEvent({
        eventType: "transaction.created",
        sourceMachine: "wa-test-01",
        occurredAt: "2026-03-20T09:00:00Z",
        payload: { amount: 100 },
      })
    );
    const sentId = db.enqueueSyncEvent(
      createLedgerSyncEvent({
        eventType: "group.set",
        sourceMachine: "wa-test-01",
        occurredAt: "2026-03-20T09:01:00Z",
        payload: { group_num: 3 },
      })
    );

    db.markSyncEventsFailed([failedId], "HTTP 401: Unauthorized");
    db.markSyncEventsSent([sentId], 200);

    const summary = db.getSyncStatusSummary();
    assert.equal(summary.pendingCount, 1);
    assert.equal(summary.retryingCount, 1);
    assert.equal(summary.lastError, "HTTP 401: Unauthorized");
    assert.ok(summary.lastFailedAt);
    assert.ok(summary.lastSentAt);
  } finally {
    db.close();
    rmSync(tempDir, { recursive: true, force: true });
  }
});

test("formatSyncStatusReport renders a compact Chinese summary", () => {
  const report = formatSyncStatusReport({
    pendingCount: 2,
    retryingCount: 1,
    lastError: "HTTP 401: Unauthorized",
    lastFailedAt: "2026-03-20 10:00:00",
    lastSentAt: "2026-03-20 10:05:00",
  });

  assert.match(report, /待发送：2/);
  assert.match(report, /重试中：1/);
  assert.match(report, /最近失败：2026-03-20 10:00:00/);
  assert.match(report, /HTTP 401: Unauthorized/);
  assert.match(report, /最近成功：2026-03-20 10:05:00/);
});
