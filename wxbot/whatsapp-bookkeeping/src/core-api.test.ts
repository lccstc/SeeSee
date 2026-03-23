import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import * as ts from "typescript";

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const runtimeIndexUrl = new URL("./index.ts", import.meta.url);

const envelope = {
  platform: "whatsapp",
  message_id: "msg-123",
  chat_id: "120363424645412524@g.us",
  chat_name: "测试群",
  is_group: true,
  sender_id: "85270765166@s.whatsapp.net",
  sender_name: "85270765166",
  sender_kind: "user",
  content_type: "text",
  text: "+100rmb",
  from_self: false,
  received_at: "2026-03-21T10:00:00.000Z",
};

test("sendEnvelope posts the normalized envelope directly to the Python core API", async () => {
  const originalFetch = globalThis.fetch;
  const received: {
    input: RequestInfo | URL;
    init?: RequestInit;
  }[] = [];

  globalThis.fetch = (async (input, init) => {
    received.push({ input, init });
    return new Response(JSON.stringify({ actions: [] }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  }) as typeof fetch;

  try {
    const { CoreApiClient } = await import("./core-api.ts");
    const client = new CoreApiClient({
      endpoint: "https://python.example.com",
      token: "sync-token",
      requestTimeoutMs: 1500,
    });

    const result = await client.sendEnvelope(envelope);

    assert.deepEqual(result, []);
  } finally {
    globalThis.fetch = originalFetch;
  }

  assert.equal(received.length, 1);
  assert.equal(String(received[0].input), "https://python.example.com/api/core/messages");
  assert.equal(received[0].init?.method, "POST");

  const headers = new Headers(received[0].init?.headers);
  assert.equal(headers.get("authorization"), "Bearer sync-token");
  assert.equal(headers.get("content-type"), "application/json");

  const body = JSON.parse(String(received[0].init?.body ?? ""));
  assert.deepEqual(body, envelope);
});

test("executeCoreActions dispatches send_text and send_file", async () => {
  const { executeCoreActions } = await import("./core-api.ts");

  const calls: Array<{ method: string; args: unknown[] }> = [];
  const adapter = {
    sendMessage: async (chatId: string, text: string) => {
      calls.push({ method: "sendMessage", args: [chatId, text] });
      return true;
    },
    sendFile: async (chatId: string, filePath: string, caption?: string) => {
      calls.push({ method: "sendFile", args: [chatId, filePath, caption] });
      return true;
    },
  };

  const results = await executeCoreActions(
    [
      { id: 11, action_type: "send_text", chat_id: "g-1", text: "hello" },
      { id: 12, action_type: "send_file", chat_id: "g-2", file_path: "/tmp/report.pdf", caption: "report" },
    ],
    adapter
  );

  assert.deepEqual(calls, [
    { method: "sendMessage", args: ["g-1", "hello"] },
    { method: "sendFile", args: ["g-2", "/tmp/report.pdf", "report"] },
  ]);
  assert.deepEqual(results, [
    { id: 11, success: true },
    { id: 12, success: true },
  ]);
});

test("ackOutboundActions posts adapter delivery results back to core", async () => {
  const originalFetch = globalThis.fetch;
  const received: {
    input: RequestInfo | URL;
    init?: RequestInit;
  }[] = [];

  globalThis.fetch = (async (input, init) => {
    received.push({ input, init });
    return new Response(JSON.stringify({ updated: 2 }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  }) as typeof fetch;

  try {
    const { CoreApiClient } = await import("./core-api.ts");
    const client = new CoreApiClient({
      endpoint: "https://python.example.com",
      token: "sync-token",
      requestTimeoutMs: 1500,
    });

    const updated = await client.ackOutboundActions([
      { id: 11, success: true },
      { id: 12, success: false },
    ]);

    assert.equal(updated, 2);
  } finally {
    globalThis.fetch = originalFetch;
  }

  assert.equal(received.length, 1);
  assert.equal(String(received[0].input), "https://python.example.com/api/core/actions/ack");
  assert.equal(received[0].init?.method, "POST");
  assert.deepEqual(JSON.parse(String(received[0].init?.body ?? "")), {
    items: [
      { id: 11, success: true },
      { id: 12, success: false },
    ],
  });
});

test("flushCoreOutboundActions fetches queued web actions and acknowledges delivery", async () => {
  const { flushCoreOutboundActions } = await import(runtimeIndexUrl.href);

  let ackedItems: Array<{ id: number; success: boolean }> = [];
  const flushed = await flushCoreOutboundActions(
    {
      fetchOutboundActions: async () => [
        { id: 21, action_type: "send_text", chat_id: "g-1", text: "群发通知" },
      ],
      ackOutboundActions: async (items) => {
        ackedItems = items;
        return items.length;
      },
    } as any,
    {
      sendMessage: async () => true,
      sendFile: async () => true,
    },
    {
      warn: () => undefined,
    } as any
  );

  assert.equal(flushed, 1);
  assert.deepEqual(ackedItems, [
    { id: 21, success: true },
  ]);
});

test("index.ts no longer keeps the old parser/commands/database/sync main chain", () => {
  const source = readFileSync(resolve(projectRoot, "src/index.ts"), "utf8");
  const file = ts.createSourceFile("index.ts", source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  const staticImports = file.statements
    .filter(ts.isImportDeclaration)
    .filter((node) => !node.importClause?.isTypeOnly)
    .map((node) => String((node.moduleSpecifier as ts.StringLiteral).text));

  assert.ok(!staticImports.includes("./parser.js"));
  assert.ok(!staticImports.includes("./commands.js"));
  assert.ok(!staticImports.includes("./database.js"));
  assert.ok(!staticImports.includes("./sync.js"));
});

test("index.ts no longer declares legacy sync config source fields", () => {
  const source = readFileSync(resolve(projectRoot, "src/index.ts"), "utf8");

  assert.ok(!source.includes("sync?: {"));
});

test("config.ts no longer defines the legacy sync configuration", () => {
  const source = readFileSync(resolve(projectRoot, "src/config.ts"), "utf8");

  assert.ok(!source.includes("sync?: {"));
  assert.ok(!source.includes("sync: {"));
  assert.ok(!source.includes("flushIntervalMs"));
  assert.ok(!source.includes("sourceMachine"));
  assert.ok(!source.includes("masterPhone"));
  assert.ok(!source.includes("masterPhones"));
});

test("package.json no longer depends on the legacy SQLite stack", () => {
  const packageJson = JSON.parse(readFileSync(resolve(projectRoot, "package.json"), "utf8")) as {
    dependencies?: Record<string, string>;
    devDependencies?: Record<string, string>;
  };

  assert.equal(packageJson.dependencies?.["better-sqlite3"], undefined);
  assert.equal(packageJson.devDependencies?.["@types/better-sqlite3"], undefined);
});

test("README only documents the V2 core API path", () => {
  const readme = readFileSync(resolve(projectRoot, "README.md"), "utf8");
  const configJson = readFileSync(resolve(projectRoot, "config.json"), "utf8");

  assert.ok(!readme.includes("/api/sync/events"));
  assert.ok(!readme.includes("sync_outbox"));
  assert.ok(!readme.includes("sync.enabled"));
  assert.ok(!readme.includes("masterPhone"));
  assert.ok(!readme.includes("masterPhones"));
  assert.ok(!configJson.includes("masterPhone"));
  assert.ok(!configJson.includes("masterPhones"));
});

test("normalizeMessage maps the canonical sender and Unix seconds timestamp at runtime", async () => {
  const { normalizeMessage } = await import(runtimeIndexUrl.href);

  const message = normalizeMessage({
    from: "217944491602115@lid",
    fromMe: false,
    chatId: "120363424645412524@g.us",
    chatName: "测试群",
    content: "+100rmb",
    timestamp: 1710000000,
    messageId: "msg-123",
    participant: "99999999999@s.whatsapp.net",
  });

  assert.equal(message.sender_id, "217944491602115@lid");
  assert.equal(message.sender_name, "217944491602115@lid");
  assert.equal(message.sender_kind, "user");
  assert.equal(message.received_at, new Date(1710000000 * 1000).toISOString());
});

test("normalizeMessage prefers provided sender display name over raw sender id", async () => {
  const { normalizeMessage } = await import(runtimeIndexUrl.href);

  const message = normalizeMessage({
    from: "243563921170506@lid",
    fromMe: false,
    chatId: "120363424645412524@g.us",
    chatName: "测试群",
    content: "+50xb5",
    timestamp: 1710000000,
    messageId: "msg-display-name",
    participant: "243563921170506@lid",
    senderName: "虎游堂-神在ι",
  } as any);

  assert.equal(message.sender_id, "243563921170506@lid");
  assert.equal(message.sender_name, "虎游堂-神在ι");
});

test("isValidCoreEnvelope rejects envelopes missing required runtime identifiers", async () => {
  const { isValidCoreEnvelope } = await import(runtimeIndexUrl.href);

  assert.equal(
    isValidCoreEnvelope({
      ...envelope,
      message_id: "",
    }),
    false
  );
  assert.equal(
    isValidCoreEnvelope({
      ...envelope,
      sender_id: "",
    }),
    false
  );
  assert.equal(isValidCoreEnvelope(envelope), true);
});

test("shouldIgnoreSelfMessage keeps manual self-authored commands for runtime", async () => {
  const { createSelfMessageTracker, shouldIgnoreSelfMessage } = await import(runtimeIndexUrl.href);
  const tracker = createSelfMessageTracker();

  assert.equal(
    shouldIgnoreSelfMessage({
      from: "unexpected-jid",
      fromMe: true,
      chatId: "120363424645412524@g.us",
      chatName: "测试群",
      content: "/bal",
      timestamp: 1710000000,
      messageId: "msg-123",
    }, tracker),
    false
  );
});

test("shouldIgnoreSelfMessage ignores bot-authored replies that were just sent by this process", async () => {
  const { createSelfMessageTracker, shouldIgnoreSelfMessage } = await import(runtimeIndexUrl.href);
  const tracker = createSelfMessageTracker();

  tracker.recordText("120363424645412524@g.us", "Balance: +100.00");

  assert.equal(
    shouldIgnoreSelfMessage({
      from: "unexpected-jid",
      fromMe: true,
      chatId: "120363424645412524@g.us",
      chatName: "测试群",
      content: "Balance: +100.00",
      timestamp: 1710000000,
      messageId: "msg-124",
    }, tracker),
    true
  );

  assert.equal(
    shouldIgnoreSelfMessage({
      from: "unexpected-jid",
      fromMe: true,
      chatId: "120363424645412524@g.us",
      chatName: "测试群",
      content: "Balance: +100.00",
      timestamp: 1710000001,
      messageId: "msg-125",
    }, tracker),
    false
  );
});

test("createCoreApiClient rejects missing coreApi token even if sync token exists", async () => {
  const { createCoreApiClient } = await import(runtimeIndexUrl.href);

  await assert.rejects(
    () =>
      createCoreApiClient({
        coreApi: {
          endpoint: "https://python.example.com",
          token: "",
          requestTimeoutMs: 1500,
        },
      } as any),
    /coreApi\.token is required/
  );
});

test("createCoreApiClient uses the configured core token at runtime", async () => {
  const originalFetch = globalThis.fetch;
  const received: Array<{ input: RequestInfo | URL; init?: RequestInit }> = [];
  globalThis.fetch = (async (input, init) => {
    received.push({ input, init });
    return new Response(JSON.stringify({ actions: [] }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  }) as typeof fetch;

  try {
    const { createCoreApiClient } = await import(runtimeIndexUrl.href);
    const client = await createCoreApiClient({
      coreApi: {
        endpoint: "https://python.example.com",
        token: "core-token",
        requestTimeoutMs: 1500,
      },
    } as any);

    await client.sendEnvelope(envelope);
  } finally {
    globalThis.fetch = originalFetch;
  }

  assert.equal(received.length, 1);
  const headers = new Headers(received[0].init?.headers);
  assert.equal(headers.get("authorization"), "Bearer core-token");
});

test("sendEnvelope rejects unknown actions from the core API", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (async () => {
    return new Response(JSON.stringify({ actions: [{ action_type: "nope", chat_id: "g-1" }] }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  }) as typeof fetch;

  try {
    const { CoreApiClient } = await import("./core-api.ts");
    const client = new CoreApiClient({
      endpoint: "https://python.example.com",
      token: "sync-token",
      requestTimeoutMs: 1500,
    });

    await assert.rejects(
      () =>
        client.sendEnvelope({
          platform: "whatsapp",
          message_id: "msg-123",
          chat_id: "g-1",
          chat_name: "group",
          is_group: true,
          sender_id: "user-1",
          sender_name: "user-1",
        }),
      /Unknown core action/
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("sendEnvelope rejects actions missing required fields", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (async () => {
    return new Response(JSON.stringify({ actions: [{ action_type: "send_file", chat_id: "g-1" }] }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  }) as typeof fetch;

  try {
    const { CoreApiClient } = await import("./core-api.ts");
    const client = new CoreApiClient({
      endpoint: "https://python.example.com",
      token: "sync-token",
      requestTimeoutMs: 1500,
    });

    await assert.rejects(
      () =>
        client.sendEnvelope({
          platform: "whatsapp",
          message_id: "msg-123",
          chat_id: "g-1",
          chat_name: "group",
          is_group: true,
          sender_id: "user-1",
          sender_name: "user-1",
        }),
      /Invalid core action payload: send_file/
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("executeCoreActions rejects invalid action payloads", async () => {
  const { executeCoreActions } = await import("./core-api.ts");

  await assert.rejects(
    () =>
      executeCoreActions(
        [
          {
            action_type: "send_file",
            chat_id: "g-1",
          } as any,
        ],
        {
          sendMessage: async () => true,
          sendFile: async () => true,
        }
      ),
    /Invalid core action payload: send_file/
  );
});
