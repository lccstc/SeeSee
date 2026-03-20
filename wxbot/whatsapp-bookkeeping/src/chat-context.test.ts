import test from "node:test";
import assert from "node:assert/strict";

import { getSyncChatName } from "./chat-context.ts";

test("getSyncChatName prefers the resolved group name", () => {
  assert.equal(getSyncChatName("120363424645412524@g.us", "测试群"), "测试群");
});

test("getSyncChatName falls back to chat id when group name is missing", () => {
  assert.equal(getSyncChatName("120363424645412524@g.us", ""), "120363424645412524@g.us");
});
