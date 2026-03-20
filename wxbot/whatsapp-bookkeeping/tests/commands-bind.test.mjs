import test from "node:test";
import assert from "node:assert/strict";

import { CommandHandler } from "../dist/commands.js";

test("/bind should bind the observed WhatsApp sender id instead of the canonical phone", async () => {
  const db = {
    isWhitelisted(phone) {
      return phone === "+84389225210";
    },
    bindUserCalls: [],
    bindUser(whatsappJid, phone) {
      this.bindUserCalls.push({ whatsappJid, phone });
      return true;
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
  };

  const handler = new CommandHandler(db, whatsapp, config);

  await handler.handleCommand(
    "/bind +84389225210",
    "12036340001@g.us",
    "+217944491602115",
    "217944491602115@lid",
  );

  assert.deepEqual(db.bindUserCalls, [
    {
      whatsappJid: "217944491602115@lid",
      phone: "+84389225210",
    },
  ]);
});
