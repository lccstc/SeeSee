import { randomUUID } from "node:crypto";

export interface LedgerSyncEvent {
  eventId: string;
  eventType: string;
  schemaVersion: number;
  platform: string;
  sourceMachine: string;
  occurredAt: string;
  payload: Record<string, unknown>;
}

export interface SyncOutboxEvent {
  id: number;
  eventId: string;
  eventType: string;
  schemaVersion: number;
  platform: string;
  sourceMachine: string;
  occurredAt: string;
  payloadJson: string;
}

export interface SyncOutboxStore {
  listPendingSyncEvents(limit: number): SyncOutboxEvent[];
  markSyncEventsSent(ids: number[], responseCode: number): void;
  markSyncEventsFailed(ids: number[], error: string): void;
}

export interface SyncWorkerOptions {
  endpoint: string;
  token: string;
  batchSize: number;
  requestTimeoutMs: number;
  store: SyncOutboxStore;
  flushIntervalMs?: number;
}

export function createLedgerSyncEvent(params: {
  eventType: string;
  sourceMachine: string;
  payload: Record<string, unknown>;
  occurredAt?: string;
}): LedgerSyncEvent {
  return {
    eventId: randomUUID(),
    eventType: params.eventType,
    schemaVersion: 1,
    platform: "whatsapp",
    sourceMachine: params.sourceMachine,
    occurredAt: params.occurredAt ?? new Date().toISOString(),
    payload: params.payload,
  };
}

export class OutboxSyncWorker {
  private readonly endpoint: string;
  private readonly token: string;
  private readonly batchSize: number;
  private readonly requestTimeoutMs: number;
  private readonly store: SyncOutboxStore;
  private readonly flushIntervalMs: number;
  private timer: NodeJS.Timeout | null;
  private flushing: boolean;

  constructor(options: SyncWorkerOptions) {
    this.endpoint = options.endpoint;
    this.token = options.token;
    this.batchSize = options.batchSize;
    this.requestTimeoutMs = options.requestTimeoutMs;
    this.store = options.store;
    this.flushIntervalMs = options.flushIntervalMs ?? 1000;
    this.timer = null;
    this.flushing = false;
  }

  start(): void {
    if (this.timer) {
      return;
    }
    this.timer = setInterval(() => {
      void this.flushOnce();
    }, this.flushIntervalMs);
  }

  stop(): void {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  async flushOnce(): Promise<void> {
    if (this.flushing) {
      return;
    }

    const events = this.store.listPendingSyncEvents(this.batchSize);
    if (events.length === 0) {
      return;
    }

    this.flushing = true;
    try {
      const response = await this.postEvents(events);
      const ids = events.map((item) => item.id);
      if (response.ok) {
        this.store.markSyncEventsSent(ids, response.status);
        return;
      }

      const body = await response.text();
      this.store.markSyncEventsFailed(ids, `HTTP ${response.status}: ${body}`.trim());
    } catch (error) {
      const ids = events.map((item) => item.id);
      const message = error instanceof Error ? error.message : String(error);
      this.store.markSyncEventsFailed(ids, message);
    } finally {
      this.flushing = false;
    }
  }

  private async postEvents(events: SyncOutboxEvent[]): Promise<Response> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.requestTimeoutMs);
    try {
      return await fetch(this.endpoint, {
        method: "POST",
        headers: {
          "content-type": "application/json",
          authorization: `Bearer ${this.token}`,
        },
        body: JSON.stringify({
          events: events.map((event) => ({
            event_id: event.eventId,
            event_type: event.eventType,
            schema_version: event.schemaVersion,
            platform: event.platform,
            source_machine: event.sourceMachine,
            occurred_at: event.occurredAt,
            payload: JSON.parse(event.payloadJson),
          })),
        }),
        signal: controller.signal,
      });
    } finally {
      clearTimeout(timeout);
    }
  }
}
