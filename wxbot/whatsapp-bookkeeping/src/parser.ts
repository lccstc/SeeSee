// ============================================================
// Bookkeeping - Message Parser
// Pure regex-based, zero LLM dependency, deterministic
// Supports multiple formats: +100rmb, 100rmb+, rmb+100, etc.
// ============================================================

/**
 * Negative categories: sign is REVERSED.
 * +25rg 5.3 => actually -132.5 (expense)
 * -25rg 5.3 => actually +132.5 (reversal)
 */
export const NEGATIVE_CATEGORIES = new Set([
  "rg", "sp", "gs", "xb", "it", "st", "ft", "mx",
  "gg", "dg", "ae", "lulu", "dk", "ebay", "rb",
  "uber", "xc", "cvs", "ymx", "psn", "chime", "ks", "tt", "nike", "nd", "cash", "ps",
]);

/** Positive categories: sign is kept as-is */
export const POSITIVE_CATEGORIES = new Set(["rmb"]);

/** All known categories */
export const ALL_CATEGORIES = new Set([...NEGATIVE_CATEGORIES, ...POSITIVE_CATEGORIES]);

export interface ParsedTransaction {
  /** Original sign from message: 1 for +, -1 for - */
  inputSign: 1 | -1;
  /** Face value / amount number */
  amount: number;
  /** Category code, lowercase. "rmb" if pure RMB */
  category: string;
  /** Exchange rate (null for rmb) */
  rate: number | null;
  /** Final RMB equivalent with correct sign applied */
  rmbValue: number;
  /** Original raw message text */
  raw: string;
}

// ============================================================
// Multiple regex patterns for different input formats
// ============================================================

// Pattern 1: +100rmb, -50sp 4.8 (sign before amount, optional category after, optional rate after category)
const PATTERN1 = /^([+-])(\d+(?:\.\d+)?)\s*([a-zA-Z]+)?\s*(\d+(?:\.\d+)?)?$/;

// Pattern 2: 100rmb+, 25rg- (amount first, sign after category)
const PATTERN2 = /^(\d+(?:\.\d+)?)\s*([a-zA-Z]+)?\s*([+-])(\d+(?:\.\d+)?)?$/;

// Pattern 3: rmb+100, rg-25 5.3 (category first, then sign+amount)
const PATTERN3 = /^([a-zA-Z]+)?\s*([+-])(\d+(?:\.\d+)?)\s*(\d+(?:\.\d+)?)?$/;

/**
 * Try to parse a transaction with multiple pattern attempts.
 */
export function parseTransaction(text: string): ParsedTransaction | null {
  const trimmed = text.trim();

  // Try pattern 1: +100rmb, -50sp 4.8
  let match = trimmed.match(PATTERN1);
  if (match) {
    const [, signStr, amountStr, catRaw, rateStr] = match;
    return parseMatch1(signStr, amountStr, catRaw, rateStr, trimmed);
  }

  // Try pattern 2: 100rmb+ (amount first, sign after category)
  match = trimmed.match(PATTERN2);
  if (match) {
    const [, amountStr, catRaw, signStr, rateStr] = match;
    return parseMatch2(amountStr, catRaw, signStr, rateStr, trimmed);
  }

  // Try pattern 3: rmb+100 (category first)
  match = trimmed.match(PATTERN3);
  if (match) {
    const [, catRaw, signStr, amountStr, rateStr] = match;
    return parseMatch3(catRaw, signStr, amountStr, rateStr, trimmed);
  }

  return null;
}

function parseMatch1(
  signStr: string,
  amountStr: string,
  catRaw: string | undefined,
  rateStr: string | undefined,
  raw: string
): ParsedTransaction | null {
  const inputSign: 1 | -1 = signStr === "+" ? 1 : -1;
  const amount = parseFloat(amountStr);
  const category = catRaw ? catRaw.toLowerCase() : "rmb";
  const rate = rateStr ? parseFloat(rateStr) : null;

  if (!ALL_CATEGORIES.has(category)) return null;

  return computeValue(inputSign, amount, category, rate, raw);
}

function parseMatch2(
  amountStr: string,
  catRaw: string | undefined,
  signStr: string,
  rateStr: string | undefined,
  raw: string
): ParsedTransaction | null {
  const amount = parseFloat(amountStr);
  // If there's a second number after sign, it's the rate
  const rate = rateStr ? parseFloat(rateStr) : null;

  // If category is present, use it; otherwise default to rmb
  const category = catRaw ? catRaw.toLowerCase() : "rmb";

  // For pattern like "100rmb+", the sign is at the end
  const inputSign: 1 | -1 = signStr === "+" ? 1 : -1;

  if (!ALL_CATEGORIES.has(category)) return null;

  return computeValue(inputSign, amount, category, rate, raw);
}

function parseMatch3(
  catRaw: string | undefined,
  signStr: string,
  amountStr: string,
  rateStr: string | undefined,
  raw: string
): ParsedTransaction | null {
  // Category comes first (e.g., "rmb+100" or "rg-25 5.3")
  const category = catRaw ? catRaw.toLowerCase() : "rmb";
  const inputSign: 1 | -1 = signStr === "+" ? 1 : -1;
  const amount = parseFloat(amountStr);
  const rate = rateStr ? parseFloat(rateStr) : null;

  if (!ALL_CATEGORIES.has(category)) return null;

  return computeValue(inputSign, amount, category, rate, raw);
}

function computeValue(
  inputSign: 1 | -1,
  amount: number,
  category: string,
  rate: number | null,
  raw: string
): ParsedTransaction | null {
  // RMB doesn't use rate
  if (category === "rmb") {
    if (rate !== null) return null; // RMB shouldn't have rate
    const rmbValue = inputSign * amount;
    return { inputSign, amount, category, rate: null, rmbValue, raw };
  }

  // Non-rmb requires rate
  if (rate === null || rate <= 0) return null;

  const baseValue = amount * rate;
  const isNegCat = NEGATIVE_CATEGORIES.has(category);

  // For negative categories, reverse the sign
  const effectiveSign = isNegCat ? -inputSign : inputSign;
  const rmbValue = effectiveSign * baseValue;

  return { inputSign, amount, category, rate, rmbValue, raw };
}

/**
 * Check if a message looks like it could be a bookkeeping entry.
 * Fast pre-check before full parse.
 */
export function looksLikeTransaction(text: string): boolean {
  const t = text.trim();
  // Must start with +/-, or contain category + sign, or sign after number
  return (
    (t.length >= 2 && (t[0] === "+" || t[0] === "-")) || // +100rmb
    /\d+[a-zA-Z][+-]/.test(t) || // 100rmb+, 25rg-
    (/^[a-zA-Z]+[+-]\d/.test(t)) // rmb+100, rg-25
  );
}

/**
 * Format a transaction for confirmation reply.
 */
export function formatConfirmation(tx: ParsedTransaction): string {
  const sign = tx.rmbValue >= 0 ? "+" : "";
  const rmbFormatted = `${sign}${tx.rmbValue.toFixed(2)}`;

  if (tx.category === "rmb") {
    return `✅ ${rmbFormatted}`;
  }

  const inputSign = tx.inputSign === 1 ? "+" : "-";
  return `✅ ${inputSign}${tx.amount} ${tx.category.toUpperCase()} ×${tx.rate} = ${rmbFormatted}`;
}
