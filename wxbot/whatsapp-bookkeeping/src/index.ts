#!/usr/bin/env node

import pino from "pino";
import { pathToFileURL } from "node:url";

import type { CoreApiClient, NormalizedMessageEnvelope } from "./core-api.js";
import type { WhatsAppMessage, WhatsAppClient } from "./whatsapp.js";

type CoreApiConfigSource = {
  coreApi: {
    endpoint: string;
    token: string;
    requestTimeoutMs: number;
  };
  sync?: {
    token?: string;
  };
};

type SelfMessageTracker = {
  recordText(chatId: string, text: string): void;
  shouldIgnore(msg: WhatsAppMessage): boolean;
};

const SELF_MESSAGE_TTL_MS = 2 * 60 * 1000;
const MAX_TRACKED_SELF_MESSAGES = 200;

export function normalizeMessage(msg: WhatsAppMessage): NormalizedMessageEnvelope {
  return {
    platform: "whatsapp",
    message_id: msg.messageId,
    chat_id: msg.chatId,
    chat_name: msg.chatName || msg.chatId,
    is_group: msg.chatId.endsWith("@g.us"),
    sender_id: msg.from || msg.participant || "",
    sender_name: msg.from || msg.participant || "",
    sender_kind: msg.fromMe ? "self" : "user",
    content_type: msg.content ? "text" : undefined,
    text: msg.content?.trim() || undefined,
    from_self: msg.fromMe,
    received_at: new Date(normalizeTimestamp(msg.timestamp)).toISOString(),
  };
}

export function createSelfMessageTracker(now: () => number = () => Date.now()): SelfMessageTracker {
  let recentTexts: Array<{ chatId: string; text: string; expiresAt: number }> = [];

  const pruneExpired = () => {
    const current = now();
    recentTexts = recentTexts.filter((item) => item.expiresAt > current);
    if (recentTexts.length > MAX_TRACKED_SELF_MESSAGES) {
      recentTexts = recentTexts.slice(-MAX_TRACKED_SELF_MESSAGES);
    }
  };

  return {
    recordText(chatId: string, text: string): void {
      const normalizedText = normalizeTrackedText(text);
      if (!chatId || !normalizedText) {
        return;
      }
      pruneExpired();
      recentTexts.push({
        chatId,
        text: normalizedText,
        expiresAt: now() + SELF_MESSAGE_TTL_MS,
      });
    },
    shouldIgnore(msg: WhatsAppMessage): boolean {
      if (!msg.fromMe) {
        return false;
      }

      const normalizedText = normalizeTrackedText(msg.content);
      if (!normalizedText) {
        return false;
      }

      pruneExpired();
      const matchedIndex = recentTexts.findIndex(
        (item) => item.chatId === msg.chatId && item.text === normalizedText
      );
      if (matchedIndex === -1) {
        return false;
      }

      recentTexts.splice(matchedIndex, 1);
      return true;
    },
  };
}

export function shouldIgnoreSelfMessage(msg: WhatsAppMessage, tracker?: SelfMessageTracker): boolean {
  if (!msg.fromMe) {
    return false;
  }
  return tracker ? tracker.shouldIgnore(msg) : true;
}

export async function createCoreApiClient(
  configSource?: CoreApiConfigSource
): Promise<CoreApiClient> {
  const { CoreApiClient } = await import(resolveLocalModule("core-api"));
  const config = configSource ?? (await import(resolveLocalModule("config"))).loadConfig();
  const endpoint = config.coreApi.endpoint.trim();
  const token = config.coreApi.token.trim();

  if (!endpoint) {
    throw new Error("coreApi.endpoint is required");
  }

  if (!token) {
    throw new Error("coreApi.token is required");
  }

  return new CoreApiClient({
    endpoint,
    token,
    requestTimeoutMs: config.coreApi.requestTimeoutMs,
  });
}

async function main(): Promise<void> {
  try {
    const [{ loadConfig }, { WhatsAppClient }, { executeCoreActions }] = await Promise.all([
      import(resolveLocalModule("config")),
      import(resolveLocalModule("whatsapp")),
      import(resolveLocalModule("core-api")),
    ]);

    const config = loadConfig();
    const logger = pino({ level: config.logLevel });
    const whatsapp = new WhatsAppClient({
      authDir: config.whatsapp.authDir,
      logLevel: config.logLevel,
      printQR: true,
    });
    const coreApiClient = await createCoreApiClient(config);
    const selfMessageTracker = createSelfMessageTracker();
    const actionSender = {
      sendMessage: async (to: string, text: string): Promise<boolean> => {
        const sent = await whatsapp.sendMessage(to, text);
        if (sent) {
          selfMessageTracker.recordText(to, text);
        }
        return sent;
      },
      sendFile: async (to: string, filePath: string, caption?: string): Promise<boolean> =>
        whatsapp.sendFile(to, filePath, caption),
    };

    const handleIncomingMessage = async (msg: WhatsAppMessage): Promise<void> => {
      if (shouldIgnoreSelfMessage(msg, selfMessageTracker)) {
        return;
      }

      const text = msg.content?.trim();
      if (!text) {
        return;
      }

      try {
        const actions = await coreApiClient.sendEnvelope(normalizeMessage(msg));
        await executeCoreActions(actions, actionSender);
      } catch (error) {
        logger.error({ error }, "Failed to process WhatsApp message");
      }
    };

    whatsapp.onMessage(handleIncomingMessage);
    whatsapp.onConnectionChange((connected: boolean) => {
      logger.info({ connected }, connected ? "WhatsApp connected" : "WhatsApp disconnected");
    });

    await whatsapp.connect();

    process.once("SIGINT", () => {
      void shutdown(whatsapp);
    });
    process.once("SIGTERM", () => {
      void shutdown(whatsapp);
    });
  } catch (error) {
    pino().error({ error }, "Startup failed");
    process.exit(1);
  }
}

async function shutdown(whatsapp: WhatsAppClient): Promise<void> {
  await whatsapp.disconnect();
  process.exit(0);
}

function normalizeTimestamp(timestamp: number): number {
  return timestamp < 1_000_000_000_000 ? timestamp * 1000 : timestamp;
}

function normalizeTrackedText(text: string | undefined): string {
  return (text || "").replace(/\r\n/g, "\n").trim();
}

function resolveLocalModule(name: "config" | "core-api" | "whatsapp"): string {
  return import.meta.url.endsWith(".ts") || import.meta.url.includes("/src/")
    ? `./${name}.ts`
    : `./${name}.js`;
}

if (process.argv[1] && pathToFileURL(process.argv[1]).href === import.meta.url) {
  void main();
}
