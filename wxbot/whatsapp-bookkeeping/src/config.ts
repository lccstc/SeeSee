// ============================================================
// Bookkeeping - Configuration Management
// ============================================================

import { readFileSync, writeFileSync, existsSync } from "fs";
import os from "node:os";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

// ES module equivalent of __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export interface Config {
  whatsapp: {
    authDir: string;  // Path to WhatsApp auth data
  };
  masterPhone: string;  // Master account phone number (legacy, kept for backward compatibility)
  masterPhones?: string[];  // Multiple master accounts (optional)
  logLevel: "debug" | "info" | "warn" | "error";
  sync?: {
    enabled: boolean;
    endpoint: string;
    token: string;
    sourceMachine: string;
    flushIntervalMs: number;
    batchSize: number;
    requestTimeoutMs: number;
  };
}

const defaultConfig: Config = {
  whatsapp: {
    authDir: resolve(__dirname, "../auth"),
  },
  masterPhone: "+84389225210",
  logLevel: "info",
  sync: {
    enabled: false,
    endpoint: "",
    token: "",
    sourceMachine: os.hostname() || "whatsapp-node",
    flushIntervalMs: 1000,
    batchSize: 20,
    requestTimeoutMs: 5000,
  },
};

let _config: Config | null = null;

export function loadConfig(configPath?: string): Config {
  if (_config) return _config;

  const path = configPath ?? resolve(__dirname, "../config.json");

  if (existsSync(path)) {
    const data = readFileSync(path, "utf-8");
    const parsed = JSON.parse(data);
    _config = {
      ...defaultConfig,
      ...parsed,
      sync: {
        ...defaultConfig.sync,
        ...(parsed.sync ?? {}),
      },
    };
  } else {
    // Create default config file
    writeFileSync(path, JSON.stringify(defaultConfig, null, 2));
    _config = { ...defaultConfig };
  }

  return _config!;
}

export function getConfig(): Config {
  if (!_config) {
    return loadConfig();
  }
  return _config;
}
