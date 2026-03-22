import test from "node:test";
import assert from "node:assert/strict";

import { resolveChatName } from "./chat-context.ts";

test("resolveChatName prefers the resolved group name", () => {
  assert.equal(resolveChatName("120363424645412524@g.us", "测试群"), "测试群");
});

test("resolveChatName falls back to chat id when group name is missing", () => {
  assert.equal(resolveChatName("120363424645412524@g.us", ""), "120363424645412524@g.us");
});
