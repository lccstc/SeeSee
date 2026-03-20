#!/usr/bin/env node
// ============================================================
// WhatsApp Bookkeeping - Main Entry Point
// Standalone WhatsApp bookkeeping bot
// ============================================================

import { BookkeepingDB } from "./database.js";
import { WhatsAppClient, WhatsAppMessage } from "./whatsapp.js";
import { CommandHandler } from "./commands.js";
import { parseTransaction, looksLikeTransaction, formatConfirmation } from "./parser.js";
import { loadConfig } from "./config.js";
import { OutboxSyncWorker, createLedgerSyncEvent } from "./sync.js";
import { getSyncChatName } from "./chat-context.js";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import pino from "pino";

// ES module equivalent of __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ============================================================
// Initialize
// ============================================================

const config = loadConfig();
const logger = pino({
  level: config.logLevel,
});

// Initialize database
const dbPath = resolve(__dirname, "../data/bookkeeping.db");
const db = new BookkeepingDB(dbPath);

// Ensure master accounts are whitelisted
const masterPhones = config.masterPhones && config.masterPhones.length > 0 ? config.masterPhones : [config.masterPhone];
for (const phone of masterPhones) {
  db.addToWhitelist(phone, "system", "Master account");
}

// Initialize WhatsApp client
const whatsapp = new WhatsAppClient({
  authDir: config.whatsapp.authDir,
  logLevel: config.logLevel,
  printQR: true,
});

// Initialize command handler
const commandHandler = new CommandHandler(db, whatsapp, config);
const syncWorker =
  config.sync?.enabled && config.sync.endpoint && config.sync.token
    ? new OutboxSyncWorker({
        endpoint: config.sync.endpoint,
        token: config.sync.token,
        batchSize: config.sync.batchSize,
        requestTimeoutMs: config.sync.requestTimeoutMs,
        flushIntervalMs: config.sync.flushIntervalMs,
        store: db,
      })
    : null;

function queueSyncEvent(eventType: string, payload: Record<string, unknown>): void {
  if (!config.sync?.enabled || !syncWorker) {
    return;
  }
  db.enqueueSyncEvent(
    createLedgerSyncEvent({
      eventType,
      sourceMachine: config.sync.sourceMachine,
      payload,
    })
  );
}

// Store last transaction for timer feature (per group+sender)
const lastTransactionMap = new Map<string, {
  groupId: string;
  senderId: string;
  message: string;
  amount: number;
  category: string;
  rate: number | null;
  rmbValue: number;
  ngnValue: number | null;
  timestamp: number;
}>();

// Store active reminder timers (for restore on restart)
const activeTimers = new Map<number, NodeJS.Timeout>();

// Reminder check interval (every 30 seconds) - kept as fallback
const REMINDER_CHECK_INTERVAL = 30000;

// ============================================================
// Reminder Timer Functions
// ============================================================

/**
 * Send reminder immediately and mark as sent
 */
async function sendReminderImmediately(
  reminder: any,
  db: BookkeepingDB,
  whatsapp: WhatsAppClient
): Promise<void> {
  await sendWithRetry(reminder, db, whatsapp);
}

/**
 * Schedule a reminder timer
 */
function scheduleReminder(
  reminder: { id: number; remindAt: string },
  db: BookkeepingDB,
  whatsapp: WhatsAppClient
): void {
  // Get full reminder data from database
  const fullReminder = db.getReminderById(reminder.id);
  if (!fullReminder) {
    console.log(`[Reminder] id=${reminder.id} not found in database`);
    return;
  }

  // Parse remindAt as UTC time (format: "YYYY-MM-DD HH:mm:ss.SSS")
  const parts = reminder.remindAt.split(/[- :]/);
  const remindTime = Date.UTC(
    parseInt(parts[0]),  // year
    parseInt(parts[1]) - 1,  // month (0-indexed)
    parseInt(parts[2]),  // day
    parseInt(parts[3]),  // hour
    parseInt(parts[4]),  // minute
    parseInt(parts[5]),  // second
    parts[6] ? parseInt(parts[6]) : 0  // millisecond
  );

  const now = Date.now();
  const delay = remindTime - now;

  if (delay <= 0) {
    // Already due, send immediately
    console.log(`[Reminder] id=${reminder.id} already due, sending immediately`);
    sendReminderImmediately(fullReminder, db, whatsapp);
    return;
  }

  const timeout = setTimeout(async () => {
    console.log(`[Reminder] Timer triggered for id=${reminder.id}`);
    await sendReminderImmediately(fullReminder, db, whatsapp);
    activeTimers.delete(reminder.id);
  }, delay);

  activeTimers.set(reminder.id, timeout);
  console.log(`[Reminder] Scheduled id=${reminder.id} in ${delay}ms (${Math.round(delay/1000)}s)`);
}

/**
 * Restore pending reminders on startup
 * Wait for WhatsApp to be connected before sending
 */
async function restoreReminders(
  db: BookkeepingDB,
  whatsapp: WhatsAppClient
): Promise<void> {
  const pending = db.getPendingReminders();
  console.log(`[Reminder] Restoring ${pending.length} pending reminders`);

  if (pending.length === 0) {
    return;
  }

  // Wait for WhatsApp connection before sending
  let retries = 0;
  while (!whatsapp.isSocketConnected() && retries < 30) {
    await new Promise(resolve => setTimeout(resolve, 1000));
    retries++;
  }

  if (!whatsapp.isSocketConnected()) {
    console.log('[Reminder] WhatsApp not connected, will retry later');
    return;
  }

  // Send overdue reminders
  for (const r of pending) {
    const remindTime = new Date(r.remindAt.replace(' ', 'T') + 'Z').getTime();
    const now = Date.now();
    const delay = remindTime - now;

    if (delay <= 0) {
      // Already due, send immediately with retry
      console.log(`[Reminder] id=${r.id} already due, sending immediately`);
      await sendWithRetry(r, db, whatsapp);
    } else {
      // Schedule for later
      scheduleReminder(r, db, whatsapp);
    }
  }
}

/**
 * Send reminder with retry logic
 */
async function sendWithRetry(
  reminder: any,
  db: BookkeepingDB,
  whatsapp: WhatsAppClient,
  maxRetries = 3
): Promise<void> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      let reminderMsg = `⏰ Payment Reminder!\n📋 ${reminder.message}`;
      if (reminder.ngnValue) {
        const ngnSign = reminder.ngnValue >= 0 ? "+" : "-";
        reminderMsg += ` = ${ngnSign}₦${Math.abs(Math.floor(reminder.ngnValue))}`;
      }
      reminderMsg += `\n⏱️ ${reminder.durationMinutes} minutes elapsed`;

      const sent = await whatsapp.sendMessage(reminder.groupId, reminderMsg);
      console.log(`[Reminder] Send result: ${sent ? 'SUCCESS' : 'FAILED'} for id=${reminder.id} (attempt ${i+1}/${maxRetries})`);

      if (sent) {
        db.markReminderSent(reminder.id);
        console.log(`[Reminder] id=${reminder.id} marked as completed`);
        return;
      }
    } catch (error) {
      logger.error(`[Reminder] Attempt ${i+1}/${maxRetries} failed for id=${reminder.id}: ${error}`);
    }

    if (i < maxRetries - 1) {
      await new Promise(resolve => setTimeout(resolve, 2000 * (i + 1)));
    }
  }

  console.log(`[Reminder] Failed to send id=${reminder.id} after ${maxRetries} attempts`);
}

// ============================================================
// Message Handler
// ============================================================

whatsapp.onMessage(async (msg: WhatsAppMessage) => {
  // Only handle group messages
  const isGroup = msg.chatId.endsWith("@g.us");
  if (!isGroup) return;

  const text = msg.content;
  if (!text) return;

  // Skip messages from self (check by comparing with our own JID)
  if (msg.fromMe && msg.from.includes(whatsapp.getOwnJid() || "")) return;

  // Extract sender phone number from JID
  let senderPhone = msg.from;
  if (msg.from.includes("@")) {
    // Try to find bound phone number
    const boundPhone = db.getBinding(msg.from);
    if (boundPhone) {
      senderPhone = boundPhone;
    } else {
      // Extract phone from JID (e.g., "85270765166@s.whatsapp.net" -> "+85270765166")
      // or LID (e.g., "217944491602115@lid" -> "+217944491602115")
      const phonePart = msg.from.split("@")[0];
      senderPhone = `+${phonePart}`;
    }
  }

  // Handle text commands (e.g., /bal, /history)
  if (text.startsWith("/")) {
    // Allow /set command even if group is not active
    if (text.startsWith("/set ") || text === "/set") {
      await commandHandler.handleCommand(text, msg.chatId, senderPhone, msg.from, msg.chatName);
      return;
    }

    // Check if group is active (has a group number assigned)
    if (!db.isGroupActive(msg.chatId)) {
      return;  // Ignore commands from inactive groups
    }

    await commandHandler.handleCommand(text, msg.chatId, senderPhone, msg.from, msg.chatName);
    return;
  }

  // Check if group is active (has a group number assigned)
  if (!db.isGroupActive(msg.chatId)) {
    return;  // Ignore messages from inactive groups
  }

  // Check for NGN auto-calculation pattern (number*number)
  // Only for group 2 and whitelisted users
  const ngnPattern = /^(\d+(\.\d+)?)\*(\d+(\.\d+)?)$/;
  const ngnMatch = text.match(ngnPattern);
  if (ngnMatch) {
    // Check if group is group 2
    const groupNum = db.getGroupNumber(msg.chatId);
    if (groupNum === 2) {
      // Check permission
      const isMaster = config.masterPhones ? config.masterPhones.includes(senderPhone) : senderPhone === config.masterPhone;
      if (db.isWhitelisted(senderPhone) || isMaster) {
        const num1 = parseFloat(ngnMatch[1]);
        const num2 = parseFloat(ngnMatch[3]);
        const ngnRateStr = db.getNgnRate();

        if (!ngnRateStr) {
          await whatsapp.sendMessage(msg.chatId, "❌ Please set NGN rate first (use /ngn command)");
        } else {
          const ngnRate = parseFloat(ngnRateStr);
          const intermediate = Math.floor(num2 * ngnRate);  // Intermediate: floor(num2 × NGN rate)
          const result = num1 * intermediate;    // Final: num1 × intermediate
          await whatsapp.sendMessage(msg.chatId, `${num1}*${intermediate}=₦${Math.floor(result)}`);
        }
        return;
      }
    }
    return;
  }

  // Check for timer pattern (XXmins), e.g., "40mins"
  // Only works after a transaction is recorded
  const timerPattern = /^(\d+)mins$/;
  const timerMatch = text.match(timerPattern);
  if (timerMatch) {
    const minutes = parseInt(timerMatch[1], 10);
    const mapKey = `${msg.chatId}_${senderPhone}`;
    const lastTx = lastTransactionMap.get(mapKey);

    console.log(`Timer request: ${minutes}mins from ${senderPhone} in ${msg.chatId}`);
    console.log(`Last transaction exists: ${!!lastTx}, within 5 min: ${lastTx ? Date.now() - lastTx.timestamp < 5 * 60 * 1000 : false}`);

    // Check if there's a recent transaction (within 5 minutes)
    if (lastTx && Date.now() - lastTx.timestamp < 5 * 60 * 1000) {
      // Use SQLite-compatible datetime format (without T and Z)
      const remindAt = new Date(Date.now() + minutes * 60 * 1000).toISOString().replace('T', ' ').replace('Z', '');
      console.log(`Creating reminder: ${remindAt}`);

      // Create reminder in database and get the ID
      const reminderId = db.createReminder({
        groupId: lastTx.groupId,
        senderId: lastTx.senderId,
        message: lastTx.message,
        amount: lastTx.amount,
        category: lastTx.category,
        rate: lastTx.rate,
        rmbValue: lastTx.rmbValue,
        ngnValue: lastTx.ngnValue,
        durationMinutes: minutes,
        remindAt,
      });

      await whatsapp.sendMessage(msg.chatId, `⏰ Timer started\nPayment will be made after: ${minutes} minutes, Thanks!`);

      // Schedule the reminder timer
      scheduleReminder({ id: reminderId, remindAt }, db, whatsapp);

      // Clear the stored transaction after timer is set
      lastTransactionMap.delete(mapKey);
    } else {
      console.log(`Timer ignored: No recent transaction found`);
    }
    return;
  }

  // Check if this looks like a transaction
  const isTx = looksLikeTransaction(text);
  if (!isTx) return;

  // Check permission - only master, whitelisted users, or bound users can record transactions
  const isMaster = config.masterPhones ? config.masterPhones.includes(senderPhone) : senderPhone === config.masterPhone;
  if (!db.isWhitelisted(senderPhone) && !isMaster) {
    return;
  }

  // Parse and record transaction
  const tx = parseTransaction(text);
  if (!tx) {
    await whatsapp.sendMessage(msg.chatId, `❌ Invalid transaction format: ${text}`);
    return;
  }

  // Validate exchange rate (must be <= 10 for non-RMB transactions)
  if (tx.category !== "rmb" && (tx.rate === null || tx.rate > 10 || tx.rate <= 0)) {
    await whatsapp.sendMessage(msg.chatId, `❌ Rate error: Rate must be between 0-10\nCurrent: ${tx.rate}`);
    return;
  }

  const txId = db.addTransaction({
    groupId: msg.chatId,
    senderId: senderPhone,
    inputSign: tx.inputSign,
    amount: tx.amount,
    category: tx.category,
    rate: tx.rate,
    rmbValue: tx.rmbValue,
    raw: tx.raw,
  });
  queueSyncEvent("transaction.created", {
    group_id: msg.chatId,
    group_num: db.getGroupNumber(msg.chatId),
    chat_name: getSyncChatName(msg.chatId, msg.chatName),
    sender_id: senderPhone,
    sender_name: senderPhone,
    source_transaction_id: txId,
    input_sign: tx.inputSign,
    amount: tx.amount,
    category: tx.category,
    rate: tx.rate,
    rmb_value: tx.rmbValue,
    raw: tx.raw,
    created_at: new Date().toISOString().slice(0, 19).replace("T", " "),
  });

  // Clear undo lock when new transaction is recorded
  commandHandler.clearUndoLock(msg.chatId);

  // Get balance after transaction
  const bal = db.getBalance(msg.chatId);
  const balSign = bal.total >= 0 ? "+" : "";
  const ngnRate = db.getNgnRate();
  const isGroup2 = db.getGroupNumber(msg.chatId) === 2;

  // Send confirmation with balance
  const confirmText = formatConfirmation(tx);
  let confirmMsg: string;

  if (isGroup2 && ngnRate) {
    // Group 2: Show both RMB and NGN
    const ngnAmount = tx.rmbValue * parseFloat(ngnRate);
    const rmbSign = tx.rmbValue >= 0 ? "+" : "-";
    const ngnSign = ngnAmount >= 0 ? "+" : "-";
    const absNgn = Math.abs(ngnAmount).toFixed(0);

    if (tx.category === "rmb") {
      confirmMsg = `✅ ${rmbSign}¥${Math.abs(tx.rmbValue).toFixed(2)} (${ngnSign}₦${absNgn})\n📊 Balance: ${balSign}${bal.total.toFixed(2)}`;
    } else {
      confirmMsg = `✅ ${tx.inputSign === 1 ? "+" : "-"}${tx.amount} ${tx.category.toUpperCase()} ×${tx.rate} = ${rmbSign}¥${Math.abs(tx.rmbValue).toFixed(2)} (${ngnSign}₦${absNgn})\n📊 Balance: ${balSign}${bal.total.toFixed(2)}`;
    }
  } else {
    // Other groups: Show RMB amount
    confirmMsg = `${confirmText}\n📊 Balance: ${balSign}${bal.total.toFixed(2)}`;
  }

  // Add NGN rate (only for group 2)
  if (ngnRate && isGroup2) {
    confirmMsg += `\n🥛₦ ${ngnRate}`;
  }
  await whatsapp.sendMessage(msg.chatId, confirmMsg);

  // Store last transaction for timer feature
  const ngnValue = isGroup2 && ngnRate ? tx.rmbValue * parseFloat(ngnRate) : null;
  const mapKey = `${msg.chatId}_${senderPhone}`;
  lastTransactionMap.set(mapKey, {
    groupId: msg.chatId,
    senderId: senderPhone,
    message: `${tx.inputSign === 1 ? "+" : "-"}${tx.amount} ${tx.category.toUpperCase()} ×${tx.rate}`,
    amount: tx.amount,
    category: tx.category,
    rate: tx.rate,
    rmbValue: tx.rmbValue,
    ngnValue,
    timestamp: Date.now(),
  });
});

// ============================================================
// Connection Handler
// ============================================================

whatsapp.onConnectionChange((connected) => {
  // Connection state changes are now shown in whatsapp.ts
});

// ============================================================
// Start
// ============================================================

async function main() {
  try {
    await whatsapp.connect();
    if (syncWorker) {
      syncWorker.start();
      await syncWorker.flushOnce();
    }

    // Restore pending reminders on startup
    await restoreReminders(db, whatsapp);

    // Handle graceful shutdown
    process.on("SIGINT", async () => {
      console.log("\nShutting down...");
      // Clear all active timers
      for (const timeout of activeTimers.values()) {
        clearTimeout(timeout);
      }
      activeTimers.clear();
      console.log("[Reminder] All timers cleared");
      syncWorker?.stop();
      await whatsapp.disconnect();
      db.close();
      process.exit(0);
    });

    process.on("SIGTERM", async () => {
      console.log("\nShutting down...");
      // Clear all active timers
      for (const timeout of activeTimers.values()) {
        clearTimeout(timeout);
      }
      activeTimers.clear();
      console.log("[Reminder] All timers cleared");
      syncWorker?.stop();
      await whatsapp.disconnect();
      db.close();
      process.exit(0);
    });
  } catch (error) {
    console.error(`Startup failed: ${error}`);
    process.exit(1);
  }
}

main();
