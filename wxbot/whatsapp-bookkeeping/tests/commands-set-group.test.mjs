import test from "node:test";
import assert from "node:assert/strict";

import { CommandHandler } from "../dist/commands.js";

test("/set should enqueue the resolved group name in sync payload", async () => {
  const db = {
    isWhitelisted(phone) {
      return phone === "+84389225210";
    },
    setGroupNumber(groupId, groupNum) {
      this.setGroupNumberCalls.push({ groupId, groupNum });
      return true;
    },
    setGroupNumberCalls: [],
    enqueueSyncEventCalls: [],
    enqueueSyncEvent(event) {
      this.enqueueSyncEventCalls.push(event);
    },
  };
  const whatsapp = {
    messages: [],
    async sendMessage(to, text) {
      this.messages.push({ to, text });
      return true;
    },
  };
  const config = {
    masterPhone: "+84389225210",
    masterPhones: ["+84389225210"],
    logLevel: "info",
    sync: {
      enabled: true,
      sourceMachine: "wa-dev-mac",
    },
  };

  const handler = new CommandHandler(db, whatsapp, config);

  await handler.handleCommand(
    "/set 7",
    "120363424645412524@g.us",
    "+84389225210",
    "217944491602115@lid",
    "测试群",
  );

  assert.deepEqual(db.setGroupNumberCalls, [
    {
      groupId: "120363424645412524@g.us",
      groupNum: 7,
    },
  ]);
  assert.equal(db.enqueueSyncEventCalls.length, 1);
  assert.equal(db.enqueueSyncEventCalls[0].payload.chat_name, "测试群");
});
