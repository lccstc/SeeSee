// ============================================================
// Bookkeeping - WhatsApp Connection Layer
// Based on @whiskeysockets/baileys
// ============================================================

import makeWASocket, {
  DisconnectReason,
  useMultiFileAuthState,
  WASocket,
  makeCacheableSignalKeyStore,
  Browsers,
  fetchLatestBaileysVersion,
} from "@whiskeysockets/baileys";
import { Boom as BoomType } from "@hapi/boom";
import pino from "pino";
import qrcode from "qrcode-terminal";

export interface WhatsAppMessage {
  from: string;  // Sender JID or phone number
  fromMe: boolean;
  chatId: string;  // Group JID or user JID
  chatName: string;
  content: string;
  timestamp: number;
  messageId: string;
  participant?: string;  // For group messages
}

export interface WhatsAppConfig {
  authDir: string;
  logLevel: "debug" | "info" | "warn" | "error";
  printQR: boolean;
}

export type MessageHandler = (msg: WhatsAppMessage) => Promise<void>;
export type ConnectionHandler = (connected: boolean) => void;

export class WhatsAppClient {
  private socket: WASocket | null = null;
  private config: WhatsAppConfig;
  private messageHandlers: MessageHandler[] = [];
  private connectionHandlers: ConnectionHandler[] = [];
  private logger: pino.Logger;
  private isConnected = false;
  private hasShownSyncMessage = false;  // Track if we've shown the sync message
  private ownJid: string | null = null;  // Store our own JID
  private groupNameCache = new Map<string, string>();

  constructor(config: WhatsAppConfig) {
    this.config = config;
    this.logger = pino({
      level: config.logLevel || 'error',
    });
  }

  /**
   * Initialize and connect to WhatsApp
   */
  async connect(): Promise<void> {
    const { state, saveCreds } = await useMultiFileAuthState(this.config.authDir);

    // Fetch latest WhatsApp Web version
    const { version } = await fetchLatestBaileysVersion();

    this.socket = makeWASocket({
      auth: {
        creds: state.creds,
        keys: makeCacheableSignalKeyStore(state.keys, this.logger),
      },
      version,
      logger: this.logger,
      browser: Browsers.ubuntu("Chrome"),
      markOnlineOnConnect: true,
      syncFullHistory: false,
    });

    // Save credentials when updated
    this.socket.ev.on("creds.update", saveCreds);

    // Handle connection updates
    this.socket.ev.on("connection.update", async (update) => {
      const { connection, lastDisconnect, qr } = update;

      if (qr) {
        // Display QR code in terminal
        console.log("\n=== Please scan WhatsApp QR code ===");
        qrcode.generate(qr, { small: true }, (ascii) => {
          console.log(ascii);
          console.log("Open WhatsApp → Linked Devices → Scan QR Code\n");
        });
      }

      if (connection === "close") {
        this.isConnected = false;
        this.notifyConnectionChange(false);

        const reason = (lastDisconnect?.error as BoomType)?.output?.statusCode;
        const shouldReconnect = reason !== DisconnectReason.loggedOut;

        if (shouldReconnect) {
          setTimeout(() => this.connect(), 5000);
        }
      } else if (connection === "open") {
        this.isConnected = true;
        // Get our own JID
        this.ownJid = this.socket?.user?.id || null;
        this.notifyConnectionChange(true);
        console.log("\n✅ WhatsApp connected successfully!\n");
        console.log("🎉 Bookkeeping feature is now available in groups!");
        console.log("Type /bal to check balance, or send +100rmb to record a transaction\n");
      }
    });

    // Handle incoming messages
    this.socket.ev.on("messages.upsert", async ({ messages, type }) => {
      if (type !== "notify") return;

      for (const msg of messages) {
        if (!msg.message?.conversation && !msg.message?.extendedTextMessage) continue;

        const content = msg.message.conversation || msg.message.extendedTextMessage?.text;
        if (!content) continue;

        const isGroup = msg.key.remoteJid?.endsWith("@g.us");
        const chatId = msg.key.remoteJid || "";
        const chatName = await this.resolveChatName(chatId, !!isGroup);

        // Try to get real phone number from participantAlt first, then participant
        let from = "";
        if (isGroup) {
          // Try participantAlt (real phone JID) first, then participant
          if ((msg.key as any).participantAlt) {
            from = (msg.key as any).participantAlt;
          } else if (msg.key.participant) {
            from = msg.key.participant;
          } else {
            from = msg.key.remoteJid || "";
          }
        } else {
          from = msg.key.remoteJid || "";
        }

        const whatsappMessage: WhatsAppMessage = {
          from: from,
          fromMe: !!msg.key.fromMe,
          chatId,
          chatName,
          content: content.trim(),
          timestamp: Number(msg.messageTimestamp) || Date.now(),
          messageId: msg.key.id || "",
          participant: isGroup ? msg.key.participant || "" : undefined,
        };

        await this.notifyMessageReceived(whatsappMessage);
      }
    });
  }

  /**
   * Send a text message
   */
  async sendMessage(to: string, text: string): Promise<boolean> {
    if (!this.socket) {
      this.logger.error("Socket not initialized");
      return false;
    }

    try {
      await this.socket.sendMessage(to, { text });
      this.logger.debug(`Message sent to ${to}: ${text.substring(0, 50)}...`);
      return true;
    } catch (error) {
      this.logger.error(`Failed to send message to ${to}: ${error}`);
      return false;
    }
  }

  /**
   * Register message handler
   */
  onMessage(handler: MessageHandler): void {
    this.messageHandlers.push(handler);
  }

  /**
   * Register connection handler
   */
  onConnectionChange(handler: ConnectionHandler): void {
    this.connectionHandlers.push(handler);
  }

  /**
   * Check if connected
   */
  isSocketConnected(): boolean {
    return this.isConnected && this.socket !== null;
  }

  /**
   * Get our own JID
   */
  getOwnJid(): string | null {
    return this.ownJid;
  }

  /**
   * Disconnect from WhatsApp
   */
  async disconnect(): Promise<void> {
    if (this.socket) {
      this.socket.end(undefined);
      this.socket = null;
      this.isConnected = false;
    }
  }

  // ---- Private methods ----

  private async notifyMessageReceived(msg: WhatsAppMessage): Promise<void> {
    for (const handler of this.messageHandlers) {
      try {
        await handler(msg);
      } catch (error) {
        this.logger.error(`Message handler error: ${error}`);
      }
    }
  }

  private async resolveChatName(chatId: string, isGroup: boolean): Promise<string> {
    if (!chatId || !isGroup) {
      return chatId;
    }

    const cached = this.groupNameCache.get(chatId);
    if (cached) {
      return cached;
    }

    if (!this.socket) {
      return chatId;
    }

    try {
      const metadata = await this.socket.groupMetadata(chatId);
      const chatName = metadata.subject?.trim() || chatId;
      this.groupNameCache.set(chatId, chatName);
      return chatName;
    } catch (error) {
      this.logger.debug(`Failed to resolve group name for ${chatId}: ${error}`);
      return chatId;
    }
  }

  private notifyConnectionChange(connected: boolean): void {
    for (const handler of this.connectionHandlers) {
      try {
        handler(connected);
      } catch (error) {
        this.logger.error(`Connection handler error: ${error}`);
      }
    }
  }
}
