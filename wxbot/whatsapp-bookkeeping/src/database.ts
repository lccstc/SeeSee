// ============================================================
// Bookkeeping - SQLite Database Layer
// Lightweight, per-group isolation, persistent
// ============================================================

import Database from "better-sqlite3";
import { resolve } from "path";
import { mkdirSync } from "fs";
import type { LedgerSyncEvent, SyncOutboxEvent } from "./sync.js";

export interface TransactionRecord {
  id: number;
  groupId: string;
  senderId: string;
  inputSign: number;
  amount: number;
  category: string;
  rate: number | null;
  rmbValue: number;
  raw: string;
  createdAt: string;
  ngnRate?: number | null;
}

export interface BalanceSummary {
  total: number;
  count: number;
  byCategory: Record<string, { count: number; totalRmb: number }>;
}

export class BookkeepingDB {
  private db: InstanceType<typeof Database>;

  constructor(dbPath: string) {
    const dir = resolve(dbPath, "..");
    mkdirSync(dir, { recursive: true });
    this.db = new Database(dbPath);
    this.db.pragma("journal_mode = WAL");
    this.db.pragma("busy_timeout = 5000");
    this.init();
  }

  private init() {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS transactions (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id   TEXT NOT NULL,
        sender_id  TEXT NOT NULL,
        input_sign INTEGER NOT NULL,
        amount     REAL NOT NULL,
        category   TEXT NOT NULL,
        rate       REAL,
        rmb_value  REAL NOT NULL,
        raw        TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        deleted    INTEGER NOT NULL DEFAULT 0,
        settled  INTEGER NOT NULL DEFAULT 0
      );

      CREATE TABLE IF NOT EXISTS settlements (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id     TEXT NOT NULL,
        settle_date  TEXT NOT NULL,
        total_rmb    REAL NOT NULL,
        detail       TEXT NOT NULL,
        settled_at   TEXT NOT NULL DEFAULT (datetime('now')),
        settled_by   TEXT NOT NULL
      );

      CREATE TABLE IF NOT EXISTS groups (
        group_id   TEXT PRIMARY KEY,
        group_num  INTEGER,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
      );

      CREATE TABLE IF NOT EXISTS settings (
        key        TEXT PRIMARY KEY,
        value      TEXT,
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
      );

      CREATE INDEX IF NOT EXISTS idx_tx_group ON transactions(group_id, deleted);
      CREATE INDEX IF NOT EXISTS idx_tx_group_date ON transactions(group_id, created_at, deleted);
      CREATE INDEX IF NOT EXISTS idx_tx_settled ON transactions(group_id, settled, deleted);
      CREATE INDEX IF NOT EXISTS idx_groups_num ON groups(group_num);

      CREATE TABLE IF NOT EXISTS whitelist (
        phone TEXT PRIMARY KEY,
        added_by TEXT NOT NULL,
        added_at TEXT NOT NULL DEFAULT (datetime('now')),
        note TEXT
      );

      CREATE TABLE IF NOT EXISTS bindings (
        whatsapp_jid TEXT PRIMARY KEY,
        phone TEXT NOT NULL,
        bound_at TEXT NOT NULL DEFAULT (datetime('now'))
      );

      CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id TEXT NOT NULL,
        sender_id TEXT NOT NULL,
        message TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        rate REAL,
        rmb_value REAL NOT NULL,
        ngn_value REAL,
        duration_minutes INTEGER NOT NULL DEFAULT 0,
        remind_at TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        sent INTEGER NOT NULL DEFAULT 0
      );

      CREATE TABLE IF NOT EXISTS sync_outbox (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT NOT NULL UNIQUE,
        event_type TEXT NOT NULL,
        schema_version INTEGER NOT NULL DEFAULT 1,
        platform TEXT NOT NULL,
        source_machine TEXT NOT NULL,
        occurred_at TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        attempt_count INTEGER NOT NULL DEFAULT 0,
        available_at TEXT NOT NULL DEFAULT (datetime('now')),
        last_error TEXT,
        last_response_code INTEGER,
        sent_at TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
      );

      CREATE INDEX IF NOT EXISTS idx_sync_outbox_pending ON sync_outbox(status, available_at, id);
    `);

    // Initialize default settings
    this.db.prepare(`
      INSERT OR IGNORE INTO settings (key, value) VALUES ('ngn_rate', '')
    `).run();

    // Migration: Check if reminders table has duration_minutes column
    // If not, drop and recreate the table with the latest schema
    try {
      const tableInfo = this.db.prepare("PRAGMA table_info(reminders)").all() as Array<{ name: string }>;
      const hasDurationMinutes = tableInfo.some(col => col.name === 'duration_minutes');
      if (!hasDurationMinutes) {
        // Drop and recreate table with latest schema
        this.db.prepare(`DROP TABLE IF EXISTS reminders`).run();
        this.db.prepare(`
          CREATE TABLE reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id TEXT NOT NULL,
            sender_id TEXT NOT NULL,
            message TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            rate REAL,
            rmb_value REAL NOT NULL,
            ngn_value REAL,
            duration_minutes INTEGER NOT NULL DEFAULT 0,
            remind_at TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            sent INTEGER NOT NULL DEFAULT 0
          )
        `).run();
        console.log('Database migration: reminders table recreated with duration_minutes');
      }
    } catch (e) {
      // Table doesn't exist yet, will be created by CREATE TABLE IF NOT EXISTS
      console.log('Database: reminders table will be created on first use');
    }
  }

  // ---- Transactions ----

  addTransaction(params: {
    groupId: string;
    senderId: string;
    inputSign: number;
    amount: number;
    category: string;
    rate: number | null;
    rmbValue: number;
    raw: string;
  }): number {
    // Get current NGN rate at transaction time
    const ngnRateRow = this.db.prepare(`
      SELECT value FROM settings WHERE key = 'ngn_rate'
    `).get() as { value: string } | undefined;
    const ngnRate = ngnRateRow?.value ? parseFloat(ngnRateRow.value) : null;

    const stmt = this.db.prepare(`
      INSERT INTO transactions (group_id, sender_id, input_sign, amount, category, rate, rmb_value, raw, ngn_rate)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
    const result = stmt.run(
      params.groupId,
      params.senderId,
      params.inputSign,
      params.amount,
      params.category,
      params.rate,
      params.rmbValue,
      params.raw,
      ngnRate
    );
    return result.lastInsertRowid as number;
  }

  /**
   * Soft-delete the most recent transaction in a group.
   * Returns the deleted record or null.
   */
  undoLast(groupId: string): TransactionRecord | null {
    const row = this.db.prepare(`
      SELECT id, group_id as groupId, sender_id as senderId,
             input_sign as inputSign, amount, category, rate,
             rmb_value as rmbValue, raw, created_at as createdAt,
             ngn_rate as ngnRate
      FROM transactions
      WHERE group_id = ? AND deleted = 0
      ORDER BY id DESC LIMIT 1
    `).get(groupId) as TransactionRecord | undefined;

    if (!row) return null;

    this.db.prepare("UPDATE transactions SET deleted = 1 WHERE id = ?").run(row.id);
    return row;
  }

  /**
   * Get balance summary for a group.
   */
  getBalance(groupId: string): BalanceSummary {
    const totalRow = this.db.prepare(`
      SELECT COALESCE(SUM(rmb_value), 0) as total, COUNT(*) as count
      FROM transactions WHERE group_id = ? AND deleted = 0
    `).get(groupId) as { total: number; count: number };

    const catRows = this.db.prepare(`
      SELECT category, COUNT(*) as count, SUM(rmb_value) as totalRmb
      FROM transactions WHERE group_id = ? AND deleted = 0
      GROUP BY category ORDER BY category
    `).all(groupId) as Array<{ category: string; count: number; totalRmb: number }>;

    const byCategory: Record<string, { count: number; totalRmb: number }> = {};
    for (const row of catRows) {
      byCategory[row.category] = { count: row.count, totalRmb: row.totalRmb };
    }

    return {
      total: totalRow.total,
      count: totalRow.count,
      byCategory,
    };
  }

  /**
   * Get recent transactions for a group.
   */
  getHistory(groupId: string, limit = 20): TransactionRecord[] {
    return this.db.prepare(`
      SELECT id, group_id as groupId, sender_id as senderId,
             input_sign as inputSign, amount, category, rate,
             rmb_value as rmbValue, raw, created_at as createdAt,
             ngn_rate as ngnRate
      FROM transactions
      WHERE group_id = ? AND deleted = 0
      ORDER BY id DESC LIMIT ?
    `).all(groupId, limit) as TransactionRecord[];
  }

  /**
   * Get transactions filtered by date range.
   */
  getHistoryByDate(groupId: string, startDate: string, endDate: string): TransactionRecord[] {
    return this.db.prepare(`
      SELECT id, group_id as groupId, sender_id as senderId,
             input_sign as inputSign, amount, category, rate,
             rmb_value as rmbValue, raw, created_at as createdAt,
             ngn_rate as ngnRate
      FROM transactions
      WHERE group_id = ? AND deleted = 0
        AND created_at >= ? AND created_at <= ?
      ORDER BY id DESC
    `).all(groupId, startDate, endDate) as TransactionRecord[];
  }

  /**
   * Get transactions filtered by category.
   */
  getHistoryByCategory(groupId: string, category: string, limit = 50): TransactionRecord[] {
    return this.db.prepare(`
      SELECT id, group_id as groupId, sender_id as senderId,
             input_sign as inputSign, amount, category, rate,
             rmb_value as rmbValue, raw, created_at as createdAt,
             ngn_rate as ngnRate
      FROM transactions
      WHERE group_id = ? AND deleted = 0 AND category = ?
      ORDER BY id DESC LIMIT ?
    `).all(groupId, category, limit) as TransactionRecord[];
  }

  /**
   * Clear all transactions in a group (soft delete).
   * Returns count of cleared records.
   */
  clearGroup(groupId: string): number {
    const result = this.db.prepare(
      "UPDATE transactions SET deleted = 1 WHERE group_id = ? AND deleted = 0"
    ).run(groupId);
    return result.changes;
  }

  // ---- Whitelist ----

  isWhitelisted(phone: string): boolean {
    const row = this.db.prepare("SELECT 1 FROM whitelist WHERE phone = ?").get(phone);
    return !!row;
  }

  addToWhitelist(phone: string, addedBy: string, note?: string): boolean {
    try {
      this.db.prepare(
        "INSERT OR IGNORE INTO whitelist (phone, added_by, note) VALUES (?, ?, ?)"
      ).run(phone, addedBy, note ?? null);
      return true;
    } catch {
      return false;
    }
  }

  removeFromWhitelist(phone: string): boolean {
    const result = this.db.prepare("DELETE FROM whitelist WHERE phone = ?").run(phone);
    return result.changes > 0;
  }

  getWhitelist(): Array<{ phone: string; addedBy: string; addedAt: string; note: string | null }> {
    return this.db.prepare("SELECT phone, added_by as addedBy, added_at as addedAt, note FROM whitelist ORDER BY added_at").all() as any;
  }

  // ---- Bindings (WhatsApp ID -> Phone mapping) ----

  bindUser(whatsappJid: string, phone: string): boolean {
    try {
      this.db.prepare(`
        INSERT OR REPLACE INTO bindings (whatsapp_jid, phone, bound_at)
        VALUES (?, ?, datetime('now'))
      `).run(whatsappJid, phone);
      return true;
    } catch {
      return false;
    }
  }

  getBinding(whatsappJid: string): string | null {
    const row = this.db.prepare(
      "SELECT phone FROM bindings WHERE whatsapp_jid = ?"
    ).get(whatsappJid) as { phone: string } | undefined;
    return row?.phone ?? null;
  }

  isBound(whatsappJid: string): boolean {
    const row = this.db.prepare(
      "SELECT 1 FROM bindings WHERE whatsapp_jid = ?"
    ).get(whatsappJid);
    return !!row;
  }

  getAllBindings(): Array<{ whatsappJid: string; phone: string; boundAt: string }> {
    return this.db.prepare("SELECT whatsapp_jid as whatsappJid, phone, bound_at as boundAt FROM bindings ORDER BY bound_at").all() as any;
  }

  // ---- Settlements ----

  /**
   * Get category breakdown (breakdown by category and rate)
   * Returns: category, rate, count, total amount, total rmb, total ngn
   */
  getCategoryMingxi(groupId: string): Array<{ category: string; rateGroups: Array<{ rate: number | null; count: number; totalAmount: number; totalRmb: number; totalNgn: number | null }> }> {
    const rows = this.db.prepare(`
      SELECT category, rate, COUNT(*) as count, SUM(input_sign * amount) as totalAmount, SUM(rmb_value) as totalRmb, SUM(ngn_rate * rmb_value) as totalNgn
      FROM transactions
      WHERE group_id = ? AND deleted = 0 AND settled = 0
      GROUP BY category, rate
      ORDER BY category, rate
    `).all(groupId) as Array<{ category: string; rate: number | null; count: number; totalAmount: number; totalRmb: number; totalNgn: number | null }>;

    // Group by category
    const categoryMap: Record<string, Array<{ rate: number | null; count: number; totalAmount: number; totalRmb: number; totalNgn: number | null }>> = {};

    for (const row of rows) {
      if (!categoryMap[row.category]) {
        categoryMap[row.category] = [];
      }
      // Filter out zero RMB entries
      if (row.totalRmb === 0) continue;
      categoryMap[row.category].push({
        rate: row.rate,
        count: row.count,
        totalAmount: row.totalAmount,
        totalRmb: row.totalRmb,
        totalNgn: row.totalNgn,
      });
    }

    // Convert to array format
    return Object.entries(categoryMap).map(([category, rateGroups]) => ({
      category,
      rateGroups,
    }));
  }

  /**
   * Get all unsettled transactions for a group
   */
  getUnsettledTransactions(groupId: string): TransactionRecord[] {
    return this.db.prepare(`
      SELECT id, group_id as groupId, sender_id as senderId,
             input_sign as inputSign, amount, category, rate,
             rmb_value as rmbValue, raw, created_at as createdAt,
             ngn_rate as ngnRate
      FROM transactions
      WHERE group_id = ? AND deleted = 0 AND settled = 0
      ORDER BY id ASC
    `).all(groupId) as TransactionRecord[];
  }

  /**
   * Get all groups that have unsettled transactions
   */
  getGroupsWithUnsettledTransactions(): string[] {
    const rows = this.db.prepare(`
      SELECT DISTINCT group_id
      FROM transactions
      WHERE deleted = 0 AND settled = 0
      ORDER BY group_id
    `).all() as Array<{ group_id: string }>;
    return rows.map(r => r.group_id);
  }

  /**
   * Settle specific transactions
   */
  settleTransactions(groupId: string, txs: TransactionRecord[], settledBy: string): { totalRmb: number; detail: string } {
    if (txs.length === 0) {
      return { totalRmb: 0, detail: "" };
    }

    const totalRmb = txs.reduce((sum, t) => sum + t.rmbValue, 0);

    // Build detail string
    const detailMap: Record<string, { count: number; total: number }> = {};
    for (const t of txs) {
      if (!detailMap[t.category]) {
        detailMap[t.category] = { count: 0, total: 0 };
      }
      detailMap[t.category].count += 1;
      detailMap[t.category].total += t.rmbValue;
    }

    const detailParts = Object.entries(detailMap).map(([cat, info]) => {
      const sign = info.total >= 0 ? "+" : "-";
      return `${cat.toUpperCase()}: ${info.count} txs ${sign}${Math.abs(info.total).toFixed(2)}`;
    });
    const detail = detailParts.join("; ");

    // Mark transactions as settled
    const txIds = txs.map(t => t.id).join(",");
    this.db.prepare(`
      UPDATE transactions SET settled = 1
      WHERE id IN (${txIds})
    `).run();

    // Record settlement
    this.db.prepare(`
      INSERT INTO settlements (group_id, settle_date, total_rmb, detail, settled_by)
      VALUES (?, ?, ?, ?, ?)
    `).run(groupId, "unsettled", totalRmb, detail, settledBy);

    return { totalRmb, detail };
  }

  /**
   * Get settlement history
   */
  getSettlements(groupId: string, limit = 10): Array<{ id: number; settleDate: string; totalRmb: number; detail: string; settledAt: string; settledBy: string }> {
    return this.db.prepare(`
      SELECT id, settle_date as settleDate, total_rmb as totalRmb, detail,
             settled_at as settledAt, settled_by as settledBy
      FROM settlements
      WHERE group_id = ?
      ORDER BY id DESC LIMIT ?
    `).all(groupId, limit) as any;
  }

  // ---- Groups ----

  /**
   * Set group number (0-9)
   */
  setGroupNumber(groupId: string, groupNum: number): boolean {
    if (groupNum < 0 || groupNum > 9) return false;
    try {
      this.db.prepare(`
        INSERT OR REPLACE INTO groups (group_id, group_num)
        VALUES (?, ?)
      `).run(groupId, groupNum);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get group number
   */
  getGroupNumber(groupId: string): number | null {
    const row = this.db.prepare(
      "SELECT group_num FROM groups WHERE group_id = ?"
    ).get(groupId) as { group_num: number } | undefined;
    return row?.group_num ?? null;
  }

  /**
   * Get all group IDs for a specific group number
   */
  getGroupsByNumber(groupNum: number): string[] {
    const rows = this.db.prepare(
      "SELECT group_id FROM groups WHERE group_num = ?"
    ).all(groupNum) as Array<{ group_id: string }>;
    return rows.map(r => r.group_id);
  }

  /**
   * Get all groups
   */
  getAllGroups(): Array<{ groupId: string; groupNum: number | null }> {
    return this.db.prepare(`
      SELECT g.group_id, g.group_num
      FROM groups g
      INNER JOIN (
        SELECT DISTINCT group_id FROM transactions WHERE deleted = 0
      ) t ON g.group_id = t.group_id
      ORDER BY g.group_num, g.group_id
    `).all() as any;
  }

  /**
   * Get group count by number
   */
  getGroupNumberStats(): Record<number, number> {
    const rows = this.db.prepare(`
      SELECT group_num, COUNT(*) as cnt
      FROM groups
      WHERE group_num IS NOT NULL
      GROUP BY group_num
    `).all() as Array<{ group_num: number; cnt: number }>;

    const stats: Record<number, number> = {};
    for (let i = 0; i <= 9; i++) {
      stats[i] = 0;
    }
    for (const row of rows) {
      stats[row.group_num] = row.cnt;
    }
    return stats;
  }

  // ---- Settings (NGN rate etc) ----

  /**
   * Set NGN rate
   */
  setNgnRate(rate: string): boolean {
    try {
      this.db.prepare(`
        UPDATE settings SET value = ?, updated_at = datetime('now')
        WHERE key = 'ngn_rate'
      `).run(rate);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get NGN rate
   */
  getNgnRate(): string | null {
    const row = this.db.prepare(`
      SELECT value FROM settings WHERE key = 'ngn_rate'
    `).get() as { value: string } | undefined;
    return row?.value ?? null;
  }

  /**
   * Check if group is active (has a group number assigned)
   */
  isGroupActive(groupId: string): boolean {
    const row = this.db.prepare(
      "SELECT 1 FROM groups WHERE group_id = ? AND group_num IS NOT NULL"
    ).get(groupId);
    return !!row;
  }

  // ---- Stats ----

  getGroupCount(): number {
    const row = this.db.prepare(
      "SELECT COUNT(DISTINCT group_id) as cnt FROM transactions WHERE deleted = 0"
    ).get() as { cnt: number };
    return row.cnt;
  }

  getTotalTransactionCount(): number {
    const row = this.db.prepare(
      "SELECT COUNT(*) as cnt FROM transactions WHERE deleted = 0"
    ).get() as { cnt: number };
    return row.cnt;
  }

  // ---- Export ----

  exportGroupCSV(groupId: string): string {
    const rows = this.db.prepare(`
      SELECT id, sender_id, input_sign, amount, category, rate, rmb_value, raw, created_at
      FROM transactions
      WHERE group_id = ? AND deleted = 0
      ORDER BY id ASC
    `).all(groupId) as any[];

    const header = "id,sender,sign,amount,category,rate,rmb_value,raw,created_at";
    const lines = rows.map((r: any) =>
      `${r.id},${r.sender_id},${r.input_sign > 0 ? "+" : "-"},${r.amount},${r.category},${r.rate ?? ""},${r.rmb_value},"${r.raw}",${r.created_at}`
    );
    return [header, ...lines].join("\n");
  }

  // ---- Reminders ----

  /**
   * Create a payment reminder
   */
  createReminder(params: {
    groupId: string;
    senderId: string;
    message: string;
    amount: number;
    category: string;
    rate: number | null;
    rmbValue: number;
    ngnValue: number | null;
    durationMinutes: number;
    remindAt: string;
  }): number {
    try {
      const result = this.db.prepare(`
        INSERT INTO reminders (group_id, sender_id, message, amount, category, rate, rmb_value, ngn_value, duration_minutes, remind_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `).run(
        params.groupId,
        params.senderId,
        params.message,
        params.amount,
        params.category,
        params.rate,
        params.rmbValue,
        params.ngnValue,
        params.durationMinutes,
        params.remindAt
      );
      console.log(`Reminder created: id=${result.lastInsertRowid}, group=${params.groupId}, duration=${params.durationMinutes}min, remindAt=${params.remindAt}`);
      return result.lastInsertRowid as number;
    } catch (e) {
      console.error(`Reminder creation failed:`, e);
      throw e;
    }
  }

  /**
   * Get due reminders (not yet sent)
   */
  getDueReminders(): Array<{
    id: number;
    groupId: string;
    senderId: string;
    message: string;
    amount: number;
    category: string;
    rate: number | null;
    rmbValue: number;
    ngnValue: number | null;
    durationMinutes: number;
    remindAt: string;
  }> {
    // Use SQLite-compatible datetime format
    const now = new Date().toISOString().replace('T', ' ').replace('Z', '');
    const rows = this.db.prepare(`
      SELECT id, group_id as groupId, sender_id as senderId, message,
             amount, category, rate, rmb_value as rmbValue, ngn_value as ngnValue,
             duration_minutes as durationMinutes, remind_at as remindAt
      FROM reminders
      WHERE sent = 0 AND remind_at <= ?
      ORDER BY id ASC
    `).all(now) as any[];
    if (rows.length > 0) {
      console.log(`Found ${rows.length} due reminders: ${rows.map(r => `id=${r.id},group=${r.groupId},duration=${r.durationMinutes}min`).join('; ')}`);
    }
    return rows;
  }

  /**
   * Mark reminder as sent
   */
  markReminderSent(id: number): void {
    this.db.prepare(`
      UPDATE reminders SET sent = 1 WHERE id = ?
    `).run(id);
  }

  /**
   * Get a reminder by ID
   */
  getReminderById(id: number): {
    id: number;
    groupId: string;
    senderId: string;
    message: string;
    amount: number;
    category: string;
    rate: number | null;
    rmbValue: number;
    ngnValue: number | null;
    durationMinutes: number;
    remindAt: string;
  } | null {
    const row = this.db.prepare(`
      SELECT id, group_id as groupId, sender_id as senderId, message,
             amount, category, rate, rmb_value as rmbValue, ngn_value as ngnValue,
             duration_minutes as durationMinutes, remind_at as remindAt
      FROM reminders
      WHERE id = ?
    `).get(id) as any;

    return row ?? null;
  }

  /**
   * Get all pending reminders (for restore on startup)
   */
  getPendingReminders(): Array<{
    id: number;
    groupId: string;
    senderId: string;
    message: string;
    amount: number;
    category: string;
    rate: number | null;
    rmbValue: number;
    ngnValue: number | null;
    durationMinutes: number;
    remindAt: string;
  }> {
    const rows = this.db.prepare(`
      SELECT id, group_id as groupId, sender_id as senderId, message,
             amount, category, rate, rmb_value as rmbValue, ngn_value as ngnValue,
             duration_minutes as durationMinutes, remind_at as remindAt
      FROM reminders
      WHERE sent = 0
      ORDER BY id ASC
    `).all() as any[];

    return rows;
  }

  /**
   * Get last transaction for a user in a group
   */
  getLastTransaction(groupId: string, senderId: string): TransactionRecord | null {
    const row = this.db.prepare(`
      SELECT id, group_id as groupId, sender_id as senderId,
             input_sign as inputSign, amount, category, rate,
             rmb_value as rmbValue, raw, created_at, ngn_rate as ngnRate
      FROM transactions
      WHERE group_id = ? AND sender_id = ? AND deleted = 0
      ORDER BY id DESC LIMIT 1
    `).get(groupId, senderId) as any;
    return row ?? null;
  }

  getActiveTransactionIds(groupId: string): number[] {
    const rows = this.db.prepare(`
      SELECT id
      FROM transactions
      WHERE group_id = ? AND deleted = 0
      ORDER BY id ASC
    `).all(groupId) as Array<{ id: number }>;
    return rows.map((row) => row.id);
  }

  enqueueSyncEvent(event: LedgerSyncEvent): number {
    const result = this.db.prepare(`
      INSERT INTO sync_outbox (
        event_id, event_type, schema_version, platform, source_machine,
        occurred_at, payload_json
      ) VALUES (?, ?, ?, ?, ?, ?, ?)
    `).run(
      event.eventId,
      event.eventType,
      event.schemaVersion,
      event.platform,
      event.sourceMachine,
      event.occurredAt,
      JSON.stringify(event.payload)
    );
    return result.lastInsertRowid as number;
  }

  listPendingSyncEvents(limit: number): SyncOutboxEvent[] {
    return this.db.prepare(`
      SELECT
        id,
        event_id as eventId,
        event_type as eventType,
        schema_version as schemaVersion,
        platform,
        source_machine as sourceMachine,
        occurred_at as occurredAt,
        payload_json as payloadJson
      FROM sync_outbox
      WHERE status = 'pending' AND available_at <= datetime('now')
      ORDER BY id ASC
      LIMIT ?
    `).all(limit) as SyncOutboxEvent[];
  }

  markSyncEventsSent(ids: number[], responseCode: number): void {
    if (ids.length === 0) {
      return;
    }
    const placeholders = ids.map(() => "?").join(",");
    this.db.prepare(`
      UPDATE sync_outbox
      SET status = 'sent',
          sent_at = datetime('now'),
          last_error = NULL,
          last_response_code = ?
      WHERE id IN (${placeholders})
    `).run(responseCode, ...ids);
  }

  markSyncEventsFailed(ids: number[], error: string): void {
    if (ids.length === 0) {
      return;
    }
    const placeholders = ids.map(() => "?").join(",");
    this.db.prepare(`
      UPDATE sync_outbox
      SET attempt_count = attempt_count + 1,
          last_error = ?,
          last_response_code = NULL,
          available_at = datetime('now', '+5 seconds')
      WHERE id IN (${placeholders})
    `).run(error, ...ids);
  }

  close() {
    this.db.close();
  }
}
