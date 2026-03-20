// ============================================================
// Bookkeeping - Command Handler
// ============================================================

import { BookkeepingDB } from "./database.js";
import { WhatsAppClient } from "./whatsapp.js";
import { Config } from "./config.js";
import { createLedgerSyncEvent } from "./sync.js";
import { getSyncChatName } from "./chat-context.js";

export class CommandHandler {
  private db: BookkeepingDB;
  private whatsapp: WhatsAppClient;
  private config: Config;
  private lastUndoGroupId: string | null = null;

  constructor(
    db: BookkeepingDB,
    whatsapp: WhatsAppClient,
    config: Config
  ) {
    this.db = db;
    this.whatsapp = whatsapp;
    this.config = config;
  }

  /**
   * Check if group is in group 2 (NGN display group)
   */
  private isGroup2(groupId: string): boolean {
    const groupNum = this.db.getGroupNumber(groupId);
    return groupNum === 2;
  }

  /**
   * Get current group number for display
   */
  private getGroupNumDisplay(groupId: string): string {
    const groupNum = this.db.getGroupNumber(groupId);
    return groupNum !== null ? `Group ${groupNum}` : "Ungrouped";
  }

  /**
   * Convert RMB to NGN using transaction's recorded ngn_rate
   */
  private convertToNgn(rmbValue: number, ngnRate: number | null): number | null {
    if (ngnRate === null || ngnRate === 0) return null;
    return rmbValue * ngnRate;
  }

  /**
   * Handle a command (e.g., /bal, /history, /undo)
   */
  async handleCommand(
    cmd: string,
    groupId: string,
    senderPhone: string,
    observedSenderId?: string,
    chatName?: string
  ): Promise<void> {
    const parts = cmd.slice(1).split(" "); // Remove "/" and split
    const commandName = parts[0].toLowerCase();
    const args = parts.slice(1).join(" ");

    switch (commandName) {
      case "bal":
        await this.handleBalance(groupId);
        break;
      case "history":
        await this.handleHistory(groupId, args);
        break;
      case "undo":
        await this.handleUndo(groupId, senderPhone);
        break;
      case "clear":
        await this.handleClear(groupId, senderPhone);
        break;
      case "adduser":
        await this.handleAddUser(groupId, senderPhone, args);
        break;
      case "rmuser":
        await this.handleRemoveUser(groupId, senderPhone, args);
        break;
      case "users":
        await this.handleUsers(groupId, senderPhone);
        break;
      case "bkstats":
        await this.handleStats(groupId, senderPhone);
        break;
      case "export":
        await this.handleExport(groupId, senderPhone);
        break;
      case "bind":
        await this.handleBind(groupId, senderPhone, args, observedSenderId);
        break;
      case "js":
        await this.handleSettle(groupId, senderPhone);
        break;
      case "alljs":
        await this.handleAllSettle(groupId, senderPhone);
        break;
      case "settlements":
        await this.handleSettlements(groupId, senderPhone, args);
        break;
      case "mx":
        await this.handleMingxi(groupId, senderPhone, args);
        break;
      case "set":
        await this.handleSetGroup(groupId, senderPhone, args, chatName);
        break;
      case "diy":
        await this.handleDiySend(groupId, senderPhone, args);
        break;
      case "ngn":
        await this.handleNgnRate(groupId, senderPhone, args);
        break;
      default:
        // Unknown command, ignore
        break;
    }
  }

  private async reply(to: string, text: string): Promise<void> {
    await this.whatsapp.sendMessage(to, text);
  }

  private isMaster(senderPhone: string): boolean {
    // Check masterPhones array first, then fall back to legacy masterPhone
    if (this.config.masterPhones && this.config.masterPhones.length > 0) {
      return this.config.masterPhones.includes(senderPhone);
    }
    return senderPhone === this.config.masterPhone;
  }

  // ---- Command Handlers ----

  private async handleBalance(groupId: string): Promise<void> {
    const bal = this.db.getBalance(groupId);
    const ngnRate = this.db.getNgnRate();
    const groupNumDisplay = this.getGroupNumDisplay(groupId);
    const isGrp2 = this.isGroup2(groupId);
    let msg: string;

    if (bal.count === 0) {
      msg = `📊 Current Balance: 0.00\n📝 No transactions\n📋 Group: ${groupNumDisplay}`;
    } else {
      const sign = bal.total >= 0 ? "+" : "-";
      msg = `📊 Balance: ${sign}${Math.abs(bal.total).toFixed(2)}\n📋 Group: ${groupNumDisplay}\n`;

      // Get unsettled transactions for detail
      const categories = this.db.getCategoryMingxi(groupId);
      if (categories.length > 0) {
        // Count unsettled transactions
        let unsettledCount = 0;
        for (const cat of categories) {
          for (const rateGroup of cat.rateGroups) {
            unsettledCount += rateGroup.count;
          }
        }
        msg += `📝 Unsettled: ${unsettledCount}\n`;

        // Show category subtotals with amount (amount/quantity, not value)
        msg += "\nDetails:\n";
        let grandTotalAmount = 0;  // Total amount
        for (const cat of categories) {
          let catTotalAmount = 0;  // Category total amount
          for (const rateGroup of cat.rateGroups) {
            catTotalAmount += rateGroup.totalAmount;
          }
          const amtSign = catTotalAmount >= 0 ? "+" : "-";
          msg += `${cat.category.toUpperCase()}: ${amtSign}${Math.abs(catTotalAmount).toFixed(0)}\n`;
          grandTotalAmount += catTotalAmount;
        }
        // Add grand total
        const grandSign = grandTotalAmount >= 0 ? "+" : "-";
        msg += `────────\n`;
        msg += `Total: ${grandSign}${Math.abs(grandTotalAmount).toFixed(0)}\n`;
      } else {
        // All transactions are settled
        msg += `✅ All transactions settled\n`;
      }
    }

    // Add NGN rate if set (only for group 2)
    if (ngnRate && isGrp2) {
      msg += `\n🥛₦ ${ngnRate}`;
    }

    await this.reply(groupId, msg.trimEnd());
  }

  private async handleHistory(groupId: string, args: string): Promise<void> {
    let records;

    if (args && /^\d+$/.test(args)) {
      records = this.db.getHistory(groupId, parseInt(args, 10));
    } else if (args && args.length <= 10) {
      records = this.db.getHistoryByCategory(groupId, args.toLowerCase());
    } else {
      records = this.db.getHistory(groupId, 20);
    }

    if (records.length === 0) {
      await this.reply(groupId, "📝 No transactions");
      return;
    }

    const sorted = [...records].reverse();
    let msg = `📝 Last ${sorted.length} transactions:\n`;

    for (const r of sorted) {
      const sign = r.rmbValue >= 0 ? "+" : "-";
      // Database time is UTC, convert to Vietnam time (UTC+7)
      const dateParts = r.createdAt.split(/[- :]/);
      const month = parseInt(dateParts[1]) - 1;  // JS months are 0-indexed
      const day = parseInt(dateParts[2]);
      const hour = parseInt(dateParts[3]) + 7;  // Add 7 hours for Vietnam
      const minute = parseInt(dateParts[4]);

      // Handle hour overflow
      let finalHour = hour;
      let finalDay = day;
      if (finalHour >= 24) {
        finalHour -= 24;
        finalDay += 1;
      }

      const time = `${String(month + 1).padStart(2, '0')}-${String(finalDay).padStart(2, '0')} ${String(finalHour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;

      if (r.category === "rmb") {
        msg += `${time} | ${sign}${r.rmbValue.toFixed(2)}\n`;
      } else {
        const iSign = r.inputSign > 0 ? "+" : "-";
        msg += `${time} | ${iSign}${r.amount}${r.category.toUpperCase()} ×${r.rate} = ${sign}${r.rmbValue.toFixed(2)}\n`;
      }
    }

    await this.reply(groupId, msg.trimEnd());
  }

  private async handleUndo(groupId: string, senderPhone: string): Promise<void> {
    if (!this.isMaster(senderPhone) && !this.db.isWhitelisted(senderPhone)) {
      await this.reply(groupId, "❌ Permission denied");
      return;
    }

    if (this.lastUndoGroupId === groupId) {
      await this.reply(groupId, "⚠️ Consecutive undo blocked\nPlease record a new transaction first");
      return;
    }

    const deleted = this.db.undoLast(groupId);
    if (!deleted) {
      await this.reply(groupId, "❌ No transaction to undo");
      return;
    }

    this.lastUndoGroupId = groupId;
    this.queueSyncEvent("transaction.deleted", {
      group_id: groupId,
      source_transaction_id: deleted.id,
    });
    const sign = deleted.rmbValue >= 0 ? "+" : "-";
    await this.reply(groupId, `↩️ Undone: ${deleted.raw} (${sign}${deleted.rmbValue.toFixed(2)})\n⚠️ To continue undoing, please record a new transaction first`);
  }

  private async handleClear(groupId: string, senderPhone: string): Promise<void> {
    if (!this.isMaster(senderPhone)) {
      await this.reply(groupId, "❌ Admin only");
      return;
    }

    const sourceTransactionIds = this.db.getActiveTransactionIds(groupId);
    const count = this.db.clearGroup(groupId);
    if (sourceTransactionIds.length > 0) {
      this.queueSyncEvent("transactions.cleared", {
        group_id: groupId,
        source_transaction_ids: sourceTransactionIds,
      });
    }
    await this.reply(groupId, `🗑️ Cleared ${count} transactions`);
  }

  private async handleAddUser(groupId: string, senderPhone: string, args: string): Promise<void> {
    if (!this.isMaster(senderPhone)) {
      await this.reply(groupId, "❌ Admin only");
      return;
    }

    const phone = args.trim();
    if (!phone || !phone.startsWith("+")) {
      await this.reply(groupId, "❌ Format: /adduser +countryCodePhone");
      return;
    }

    this.db.addToWhitelist(phone, senderPhone);
    await this.reply(groupId, `✅ Added to whitelist: ${phone}`);
  }

  private async handleRemoveUser(groupId: string, senderPhone: string, args: string): Promise<void> {
    if (!this.isMaster(senderPhone)) {
      await this.reply(groupId, "❌ Admin only");
      return;
    }

    const phone = args.trim();
    if (!phone) {
      await this.reply(groupId, "❌ Format: /rmuser +countryCodePhone");
      return;
    }

    // Check if phone is any of the master phones
    const masterPhones = this.config.masterPhones && this.config.masterPhones.length > 0
      ? this.config.masterPhones
      : [this.config.masterPhone];
    if (masterPhones.includes(phone)) {
      await this.reply(groupId, "❌ Cannot remove admin");
      return;
    }

    const ok = this.db.removeFromWhitelist(phone);
    await this.reply(groupId, ok ? `✅ Removed: ${phone}` : `❌ Not found: ${phone}`);
  }

  private async handleUsers(groupId: string, senderPhone: string): Promise<void> {
    if (!this.isMaster(senderPhone)) {
      await this.reply(groupId, "❌ Admin only");
      return;
    }

    const list = this.db.getWhitelist();
    if (list.length === 0) {
      await this.reply(groupId, "📋 Whitelist is empty");
      return;
    }

    let msg = `📋 Whitelist (${list.length} users):\n`;
    for (const u of list) {
      msg += `  ${u.phone}${u.note ? ` (${u.note})` : ""}\n`;
    }

    await this.reply(groupId, msg.trimEnd());
  }

  private async handleStats(groupId: string, senderPhone: string): Promise<void> {
    if (!this.isMaster(senderPhone)) {
      await this.reply(groupId, "❌ Admin only");
      return;
    }

    const groups = this.db.getGroupCount();
    const txCount = this.db.getTotalTransactionCount();
    const wlCount = this.db.getWhitelist().length;
    const groupStats = this.db.getGroupNumberStats();

    let msg = `📈 Bookkeeping Stats\n`;
    msg += `Groups: ${groups}\n`;
    msg += `Transactions: ${txCount}\n`;
    msg += `Whitelist: ${wlCount} users\n`;
    msg += `\n📊 Group Stats:\n`;

    for (let i = 0; i <= 9; i++) {
      if (groupStats[i] > 0) {
        msg += `  Group ${i}: ${groupStats[i]} groups\n`;
      }
    }

    await this.reply(groupId, msg.trimEnd());
  }

  private async handleExport(groupId: string, senderPhone: string): Promise<void> {
    if (!this.isMaster(senderPhone)) {
      await this.reply(groupId, "❌ Admin only");
      return;
    }

    const csv = this.db.exportGroupCSV(groupId);
    if (!csv || csv.split("\n").length <= 1) {
      await this.reply(groupId, "❌ No data to export");
      return;
    }

    await this.reply(groupId, csv);
  }

  private async handleBind(
    groupId: string,
    senderPhone: string,
    args: string,
    observedSenderId?: string
  ): Promise<void> {
    const phone = args.trim();
    if (!phone || !phone.startsWith("+")) {
      await this.reply(groupId, "❌ Format: /bind +countryCodePhone\nEx: /bind +84389225210");
      return;
    }

    if (!this.db.isWhitelisted(phone) && !this.isMaster(phone)) {
      await this.reply(groupId, "❌ Phone not in whitelist, contact admin to add");
      return;
    }

    const whatsappJid =
      observedSenderId && observedSenderId.includes("@")
        ? observedSenderId
        : senderPhone.includes("@")
          ? senderPhone
          : `${phone}@s.whatsapp.net`;
    this.db.bindUser(whatsappJid, phone);
    await this.reply(groupId, `✅ Binding successful!\nWhatsApp ID bound to ${phone}\nYou can now record transactions in this group`);
  }

  /**
   * Handle settlement
   * /js - settle all unsettled transactions since last settlement
   */
  private async handleSettle(groupId: string, senderPhone: string): Promise<void> {
    // Only master or whitelisted users can settle
    if (!this.isMaster(senderPhone) && !this.db.isWhitelisted(senderPhone)) {
      await this.reply(groupId, "❌ Permission denied");
      return;
    }

    // Get all unsettled transactions for this group
    const txs = this.db.getUnsettledTransactions(groupId);
    if (txs.length === 0) {
      await this.reply(groupId, "✅ No unsettled transactions");
      return;
    }

    const result = this.db.settleTransactions(groupId, txs, senderPhone);
    this.queueSyncEvent("settlement.created", {
      group_id: groupId,
      group_num: this.db.getGroupNumber(groupId),
      source_transaction_ids: txs.map((tx) => tx.id),
      settled_by: senderPhone,
      settled_at: new Date().toISOString(),
      total_rmb: result.totalRmb,
      detail: result.detail,
    });

    const sign = result.totalRmb >= 0 ? "+" : "-";
    await this.reply(groupId,
      `✅ Settlement successful!\n` +
      `📊 Transactions: ${txs.length}\n` +
      `💰 Total: ${sign}${Math.abs(result.totalRmb).toFixed(2)}\n` +
      `📝 Details: ${result.detail}`
    );
  }

  /**
   * Handle all-settlement (batch settle all groups)
   * /alljs - settle all unsettled transactions across all groups
   */
  private async handleAllSettle(groupId: string, senderPhone: string): Promise<void> {
    // Master or whitelisted users can use all-settlement
    if (!this.isMaster(senderPhone) && !this.db.isWhitelisted(senderPhone)) {
      await this.reply(groupId, "❌ Permission denied");
      return;
    }

    // Get all groups with unsettled transactions
    const groupIds = this.db.getGroupsWithUnsettledTransactions();
    if (groupIds.length === 0) {
      await this.reply(groupId, "✅ No unsettled transactions in any group");
      return;
    }

    // Send start notification to command group
    await this.reply(groupId, `🚀 Starting batch settlement...\n📊 ${groupIds.length} groups to settle`);

    // Settle each group
    let totalGroups = 0;
    let totalTxs = 0;
    let totalRmb = 0;
    const details: string[] = [];

    for (const gid of groupIds) {
      const txs = this.db.getUnsettledTransactions(gid);
      if (txs.length === 0) continue;

      // Get balance before settlement for this group
      const bal = this.db.getBalance(gid);

      const result = this.db.settleTransactions(gid, txs, senderPhone);
      this.queueSyncEvent("settlement.created", {
        group_id: gid,
        group_num: this.db.getGroupNumber(gid),
        source_transaction_ids: txs.map((tx) => tx.id),
        settled_by: senderPhone,
        settled_at: new Date().toISOString(),
        total_rmb: result.totalRmb,
        detail: result.detail,
      });
      totalGroups++;
      totalTxs += txs.length;
      totalRmb += result.totalRmb;
      details.push(`${gid.slice(0, 20)}...: ${txs.length} txs ${result.totalRmb >= 0 ? "+" : ""}${result.totalRmb.toFixed(2)}`);

      // Send settlement message to the group itself
      const groupMsg =
        `✅ Happy transaction!\n` +
        `📊 Balance: ${bal.total >= 0 ? "+" : ""}${bal.total.toFixed(2)}`;
      await this.reply(gid, groupMsg);
    }

    // Send summary report to command group
    const sign = totalRmb >= 0 ? "+" : "-";
    await this.reply(groupId,
      `✅ Batch settlement complete!\n` +
      `━━━━━━━━━━━━━━\n` +
      `📊 Groups: ${totalGroups}\n` +
      `📝 Transactions: ${totalTxs}\n` +
      `💰 Total: ${sign}${Math.abs(totalRmb).toFixed(2)}\n` +
      `━━━━━━━━━━━━━━\n` +
      details.join("\n")
    );
  }

  /**
   * Show settlement history
   */
  private async handleSettlements(groupId: string, senderPhone: string, args: string): Promise<void> {
    const limit = args && /^\d+$/.test(args) ? parseInt(args, 10) : 10;
    const records = this.db.getSettlements(groupId, limit);

    if (records.length === 0) {
      await this.reply(groupId, "📝 No settlement records");
      return;
    }

    let msg = `📋 Last ${records.length} settlement records:\n`;
    for (const r of records) {
      const sign = r.totalRmb >= 0 ? "+" : "-";
      const time = r.settledAt.substring(11, 16);  // HH:mm
      msg += `${time} | ${sign}${r.totalRmb.toFixed(2)} (${r.settledBy})\n`;
    }

    await this.reply(groupId, msg.trimEnd());
  }

  /**
   * Show category detail
   * /mx - show all categories summary with rate breakdown
   * /mx rg - show transactions for specific category grouped by rate
   */
  private async handleMingxi(groupId: string, senderPhone: string, args: string): Promise<void> {
    const bal = this.db.getBalance(groupId);
    const ngnRate = this.db.getNgnRate();
    const isGrp2 = this.isGroup2(groupId);

    if (!args || args.trim() === "") {
      // Show all categories with rate breakdown
      const categories = this.db.getCategoryMingxi(groupId);

      const balSign = bal.total >= 0 ? "+" : "";
      let msg = `📊 Details:\n💰 Balance: ${balSign}${bal.total.toFixed(2)}`;

      // Add NGN rate if set (only for group 2)
      if (ngnRate && isGrp2) {
        msg += `\n🥛₦ ${ngnRate}`;
      }

      if (categories.length === 0) {
        if (bal.count === 0) {
          msg += "\n📝 No transactions";
        } else {
          msg += "\n✅ All transactions settled";
        }
        await this.reply(groupId, msg.trimEnd());
        return;
      }

      msg += "\n";

      let grandTotalAmount = 0;  // Total net amount (excluding RMB)
      let grandTotalRmb = 0;     // Total RMB (excluding RMB category)

      for (const cat of categories) {
        msg += `${cat.category.toUpperCase()}:\n`;

        let catTotalAmount = 0;
        let catTotalRmb = 0;

        for (const rateGroup of cat.rateGroups) {
          const rmbSign = rateGroup.totalRmb >= 0 ? "+" : "-";
          if (rateGroup.rate === null || cat.category === "rmb") {
            msg += `  ${rateGroup.count} txs ${rmbSign}${Math.abs(rateGroup.totalRmb).toFixed(2)}\n`;
            // RMB category: only add to cat total, not grand total
            catTotalRmb += rateGroup.totalRmb;
          } else {
            // Non-RMB category: totalAmount is already signed from DB
            catTotalAmount += rateGroup.totalAmount;
            catTotalRmb += rateGroup.totalRmb;

            if (isGrp2 && rateGroup.totalNgn) {
              // Group 2: Show both RMB and NGN
              const ngnSign = rateGroup.totalNgn >= 0 ? "+" : "-";
              const absNgn = Math.abs(rateGroup.totalNgn).toFixed(0);
              msg += `  ×${rateGroup.rate}: ${rateGroup.totalAmount.toFixed(0)} = ${rmbSign}¥${Math.abs(rateGroup.totalRmb).toFixed(2)} (${ngnSign}₦${absNgn})\n`;
            } else {
              // Other groups: Show RMB
              msg += `  ×${rateGroup.rate}: ${rateGroup.totalAmount.toFixed(0)} = ${rmbSign}¥${Math.abs(rateGroup.totalRmb).toFixed(2)}\n`;
            }
          }
        }

        // Add subtotal for this category
        msg += `────────\n`;
        if (cat.category === "rmb") {
          // RMB category: only show RMB amount
          const rmbSign = catTotalRmb >= 0 ? "+" : "-";
          msg += `  Subtotal: ${rmbSign}${Math.abs(catTotalRmb).toFixed(2)}\n`;
        } else {
          // Non-RMB category: show net amount and RMB
          const amtSign = catTotalAmount >= 0 ? "+" : "-";
          const rmbSign = catTotalRmb >= 0 ? "+" : "-";
          msg += `  Subtotal: ${amtSign}${Math.abs(catTotalAmount).toFixed(0)} = ${rmbSign}¥${Math.abs(catTotalRmb).toFixed(2)}\n`;
          // Add to grand total (excluding RMB category)
          grandTotalAmount += catTotalAmount;
          grandTotalRmb += catTotalRmb;
        }
      }

      // Add grand total
      msg += `==========\n`;
      const grandAmtSign = grandTotalAmount >= 0 ? "+" : "-";
      const grandRmbSign = grandTotalRmb >= 0 ? "+" : "-";
      msg += `Total: ${grandAmtSign}${Math.abs(grandTotalAmount).toFixed(0)} = ${grandRmbSign}¥${Math.abs(grandTotalRmb).toFixed(2)}`;

      await this.reply(groupId, msg.trimEnd());
      return;
    }

    // Show specific category with rate breakdown
    const category = args.trim().toLowerCase();
    const categories = this.db.getCategoryMingxi(groupId);
    const catData = categories.find(c => c.category === category);

    if (!catData || catData.rateGroups.length === 0) {
      await this.reply(groupId, `📝 No transactions for ${category.toUpperCase()}`);
      return;
    }

    const balSign = bal.total >= 0 ? "+" : "";
    let msg = `📋 ${category.toUpperCase()}:\n💰 Balance: ${balSign}${bal.total.toFixed(2)}`;

    // Add NGN rate if set (only for group 2)
    if (ngnRate && isGrp2) {
      msg += `\n🥛₦ ${ngnRate}`;
    }
    msg += "\n";

    let netAmount = 0;  // Net amount (long - short)
    let totalRmb = 0;
    let totalNgn = 0;  // Total NGN for group 2

    for (const rateGroup of catData.rateGroups) {
      const sign = rateGroup.totalRmb >= 0 ? "+" : "";

      // totalAmount is already signed from DB
      netAmount += rateGroup.totalAmount;
      totalRmb += rateGroup.totalRmb;
      if (rateGroup.totalNgn) {
        totalNgn += rateGroup.totalNgn;
      }

      if (rateGroup.rate === null || category === "rmb") {
        msg += `  ${rateGroup.count} txs ${sign}${rateGroup.totalRmb.toFixed(2)}\n`;
      } else {
        if (isGrp2 && rateGroup.totalNgn) {
          // Group 2: Show both RMB and NGN
          const ngnSign = rateGroup.totalNgn >= 0 ? "+" : "-";
          const absNgn = Math.abs(rateGroup.totalNgn).toFixed(0);
          msg += `  ×${rateGroup.rate}: ${rateGroup.totalAmount.toFixed(0)} = ${sign}¥${Math.abs(rateGroup.totalRmb).toFixed(2)} (${ngnSign}₦${absNgn})\n`;
        } else {
          // Other groups: Show RMB
          msg += `  ×${rateGroup.rate}: ${rateGroup.totalAmount.toFixed(0)} = ${sign}${rateGroup.totalRmb.toFixed(2)}\n`;
        }
      }
    }

    // Show net summary
    const totalRmbSign = totalRmb >= 0 ? "+" : "-";
    if (category === "rmb") {
      msg += `\nTotal: ${totalRmbSign}${Math.abs(totalRmb).toFixed(2)}`;
    } else {
      const netSign = netAmount >= 0 ? "+" : "-";
      if (isGrp2) {
        // Group 2: Show both RMB and NGN in summary
        const ngnSign = totalNgn >= 0 ? "+" : "-";
        const absTotalNgn = Math.abs(totalNgn).toFixed(0);
        msg += `\nTotal: ${netSign}${netAmount.toFixed(0)} ${totalRmbSign}¥${Math.abs(totalRmb).toFixed(2)} (${ngnSign}₦${absTotalNgn})`;
      } else {
        msg += `\nTotal: ${netSign}${netAmount.toFixed(0)} ${totalRmbSign}${Math.abs(totalRmb).toFixed(2)}`;
      }
    }

    await this.reply(groupId, msg.trimEnd());
  }

  /**
   * Set group number (0-9)
   * Master or whitelisted users can set group number
   */
  private async handleSetGroup(
    groupId: string,
    senderPhone: string,
    args: string,
    chatName?: string
  ): Promise<void> {
    if (!this.isMaster(senderPhone) && !this.db.isWhitelisted(senderPhone)) {
      await this.reply(groupId, "❌ Admin only");
      return;
    }

    const num = args.trim();
    if (!/^[0-9]$/.test(num)) {
      await this.reply(groupId, "❌ Format: /set number (0-9)\nEx: /set 1");
      return;
    }

    const groupNum = parseInt(num);
    const ok = this.db.setGroupNumber(groupId, groupNum);
    if (!ok) {
      await this.reply(groupId, "❌ Failed, please retry");
      return;
    }

    this.queueSyncEvent("group.set", {
      group_id: groupId,
      group_num: groupNum,
      chat_name: getSyncChatName(groupId, chatName),
    });
    await this.reply(groupId, `✅ This group assigned to Group ${groupNum}\nOnly groups with numbers can use bookkeeping`);
  }

  /**
   * Send message to all groups with specific number
   * Master or whitelisted users can send diy messages
   */
  private async handleDiySend(groupId: string, senderPhone: string, args: string): Promise<void> {
    if (!this.isMaster(senderPhone) && !this.db.isWhitelisted(senderPhone)) {
      await this.reply(groupId, "❌ Admin only");
      return;
    }

    // Parse: /diy 1 message content (supports multi-line)
    const match = args.match(/^([0-9])\s+([\s\S]+)$/);
    if (!match) {
      await this.reply(groupId, "❌ Format: /diy number message\nEx: /diy 1 Hello everyone");
      return;
    }

    const groupNum = parseInt(match[1]);
    const message = match[2].trim();

    const groupIds = this.db.getGroupsByNumber(groupNum);
    if (groupIds.length === 0) {
      await this.reply(groupId, `❌ Group ${groupNum} has no groups`);
      return;
    }

    // Send start notification
    const totalGroups = groupIds.length;
    const estimatedTime = Math.ceil(totalGroups / 5 * 1.5);
    await this.reply(groupId,
      `🚀 Starting broadcast...\n` +
      `📊 Group: ${groupNum}\n` +
      `📋 Target: ${totalGroups} groups\n` +
      `⏱️ Est. time: ${estimatedTime}s`
    );

    // Record send results
    const results: Array<{ groupId: string; success: boolean; retries: number }> = [];
    const BATCH_SIZE = 5;      // Pause after every 5 messages
    const DELAY_MS = 1500;     // Pause 1.5 seconds
    const MAX_RETRIES = 3;     // Max 3 retries

    for (let i = 0; i < groupIds.length; i++) {
      const gid = groupIds[i];
      let success = false;
      let retries = 0;

      // Retry logic
      for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
        try {
          const ok = await this.whatsapp.sendMessage(gid, message);
          if (ok) {
            success = true;
            break;
          }
        } catch (error) {
          console.error(`[DIY] Failed to send to ${gid} (attempt ${attempt + 1}/${MAX_RETRIES}): ${error}`);
        }
        retries = attempt + 1;
        await this.sleep(2000 * (attempt + 1)); // Exponential backoff: 2s, 4s, 6s
      }

      results.push({ groupId: gid, success, retries });

      // Batch delay (anti-rate-limit)
      if ((i + 1) % BATCH_SIZE === 0) {
        await this.sleep(DELAY_MS);
      }

      // Progress feedback (every 10 groups)
      if ((i + 1) % 10 === 0) {
        const current = results.filter(r => r.success).length;
        await this.reply(groupId, `📤 Progress: ${i + 1}/${totalGroups} (Success: ${current})`);
      }
    }

    // Record results
    const successCount = results.filter(r => r.success).length;
    const failCount = results.filter(r => !r.success).length;
    const retryCount = results.filter(r => r.retries > 0).length;

    // Generate failed list (for retry)
    const failedGroups = results.filter(r => !r.success).map(r => r.groupId);

    // Send final report
    let report =
      `✅ Broadcast complete!\n` +
      `━━━━━━━━━━━━━━\n` +
      `📊 Group: ${groupNum}\n` +
      `📋 Total: ${totalGroups} groups\n` +
      `✅ Success: ${successCount} groups\n` +
      (failCount > 0 ? `❌ Failed: ${failCount} groups\n` : ``) +
      (retryCount > 0 ? `🔄 Retried: ${retryCount} groups\n` : ``) +
      `━━━━━━━━━━━━━━\n` +
      `📝 Content: ${message.substring(0, 40)}${message.length > 40 ? "..." : ""}`;

    // If there are failures, append failed list
    if (failCount > 0) {
      report += `\n⚠️ Failed groups:\n`;
      failedGroups.forEach((gid, index) => {
        report += `${index + 1}. ${gid}\n`;
      });
    }

    await this.reply(groupId, report);
  }

  /**
   * Helper method: sleep for a given time
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private queueSyncEvent(eventType: string, payload: Record<string, unknown>): void {
    if (!this.config.sync?.enabled) {
      return;
    }
    this.db.enqueueSyncEvent(
      createLedgerSyncEvent({
        eventType,
        sourceMachine: this.config.sync.sourceMachine,
        payload,
      })
    );
  }

  /**
   * Clear undo lock when new transaction is recorded
   */
  clearUndoLock(groupId: string): void {
    if (this.lastUndoGroupId === groupId) {
      this.lastUndoGroupId = null;
    }
  }

  /**
   * Set NGN rate
   * Master or whitelisted users can set NGN rate
   */
  private async handleNgnRate(groupId: string, senderPhone: string, args: string): Promise<void> {
    if (!this.isMaster(senderPhone) && !this.db.isWhitelisted(senderPhone)) {
      await this.reply(groupId, "❌ Admin only");
      return;
    }

    const rate = args.trim();
    if (!rate || !/^\d+(\.\d+)?$/.test(rate)) {
      await this.reply(groupId, "❌ Format: /ngn number\nEx: /ngn 194.2");
      return;
    }

    this.db.setNgnRate(rate);
    await this.reply(groupId, `✅ NGN rate updated: 🥛₦ ${rate}`);
  }
}
