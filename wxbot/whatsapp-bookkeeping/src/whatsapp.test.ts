import assert from "node:assert/strict";
import test from "node:test";

import { WhatsAppClient } from "./whatsapp.ts";

test("resolveChatName refreshes stale cached group names from live metadata", async () => {
  const client = new WhatsAppClient({
    authDir: "/tmp/wa-test-auth",
    logLevel: "error",
    printQR: false,
  });
  const runtime = client as any;

  runtime.groupNameCache.set("120363400000000000@g.us", "旧群名");
  runtime.socket = {
    groupMetadata: async () => ({ subject: "新群名" }),
  };

  const chatName = await runtime.resolveChatName("120363400000000000@g.us", true);

  assert.equal(chatName, "新群名");
  assert.equal(runtime.groupNameCache.get("120363400000000000@g.us"), "新群名");
});

test("resolveChatName falls back to cached name when metadata lookup fails", async () => {
  const client = new WhatsAppClient({
    authDir: "/tmp/wa-test-auth",
    logLevel: "error",
    printQR: false,
  });
  const runtime = client as any;

  runtime.groupNameCache.set("120363400000000001@g.us", "缓存群名");
  runtime.socket = {
    groupMetadata: async () => {
      throw new Error("metadata unavailable");
    },
  };

  const chatName = await runtime.resolveChatName("120363400000000001@g.us", true);

  assert.equal(chatName, "缓存群名");
});
