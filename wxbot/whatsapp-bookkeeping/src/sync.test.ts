import assert from "node:assert/strict";
import test from "node:test";

import { OutboxSyncWorker, type SyncOutboxEvent, type SyncOutboxStore } from "./sync.ts";

class FakeStore implements SyncOutboxStore {
  public sentCalls: Array<{ ids: number[]; responseCode: number }> = [];
  public failedCalls: Array<{ ids: number[]; error: string }> = [];
  private readonly events: SyncOutboxEvent[];

  constructor(events: SyncOutboxEvent[]) {
    this.events = events;
  }

  listPendingSyncEvents(limit: number): SyncOutboxEvent[] {
    return this.events.slice(0, limit);
  }

  markSyncEventsSent(ids: number[], responseCode: number): void {
    this.sentCalls.push({ ids, responseCode });
  }

  markSyncEventsFailed(ids: number[], error: string): void {
    this.failedCalls.push({ ids, error });
  }
}

test("flushOnce posts pending events and marks them sent", async () => {
  const receivedBodies: string[] = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (async (input, init) => {
    assert.equal(String(input), "https://ledger.example.com/api/sync/events");
    assert.equal(init?.headers?.authorization, "Bearer sync-token");
    receivedBodies.push(String(init?.body ?? ""));
    return new Response(JSON.stringify({ accepted: 1, duplicates: 0 }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  }) as typeof fetch;

  const store = new FakeStore([
    {
      id: 1,
      eventId: "evt-1",
      eventType: "transaction.created",
      schemaVersion: 1,
      platform: "whatsapp",
      sourceMachine: "wa-node-01",
      occurredAt: "2026-03-20T10:15:30Z",
      payloadJson: JSON.stringify({ amount: 100 }),
    },
  ]);
  const worker = new OutboxSyncWorker({
    endpoint: "https://ledger.example.com/api/sync/events",
    token: "sync-token",
    batchSize: 10,
    requestTimeoutMs: 2000,
    store,
  });

  try {
    await worker.flushOnce();
  } finally {
    globalThis.fetch = originalFetch;
  }

  assert.equal(receivedBodies.length, 1);
  const body = JSON.parse(receivedBodies[0]);
  assert.equal(body.events.length, 1);
  assert.equal(body.events[0].event_id, "evt-1");
  assert.deepEqual(store.sentCalls, [{ ids: [1], responseCode: 200 }]);
  assert.equal(store.failedCalls.length, 0);
});

test("flushOnce records failure when remote rejects the request", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (async () => {
    return new Response(JSON.stringify({ error: "Unauthorized" }), {
      status: 401,
      headers: { "content-type": "application/json" },
    });
  }) as typeof fetch;

  const store = new FakeStore([
    {
      id: 2,
      eventId: "evt-2",
      eventType: "group.set",
      schemaVersion: 1,
      platform: "whatsapp",
      sourceMachine: "wa-node-01",
      occurredAt: "2026-03-20T10:20:00Z",
      payloadJson: JSON.stringify({ group_num: 7 }),
    },
  ]);
  const worker = new OutboxSyncWorker({
    endpoint: "https://ledger.example.com/api/sync/events",
    token: "bad-token",
    batchSize: 10,
    requestTimeoutMs: 2000,
    store,
  });

  try {
    await worker.flushOnce();
  } finally {
    globalThis.fetch = originalFetch;
  }

  assert.equal(store.sentCalls.length, 0);
  assert.equal(store.failedCalls.length, 1);
  assert.deepEqual(store.failedCalls[0].ids, [2]);
  assert.match(store.failedCalls[0].error, /401/);
});
