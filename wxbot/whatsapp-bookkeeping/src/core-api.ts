export interface NormalizedMessageEnvelope {
  platform: "whatsapp";
  message_id: string;
  chat_id: string;
  chat_name: string;
  is_group: boolean;
  sender_id: string;
  sender_name: string;
  sender_kind?: string;
  content_type?: string;
  text?: string;
  from_self?: boolean;
  received_at?: string;
}

export interface SendTextAction {
  id?: number;
  action_type: "send_text";
  chat_id: string;
  text: string;
}

export interface SendFileAction {
  id?: number;
  action_type: "send_file";
  chat_id: string;
  file_path: string;
  caption?: string;
}

export type CoreAction = SendTextAction | SendFileAction;

export interface CoreApiClientOptions {
  endpoint: string;
  token: string;
  requestTimeoutMs: number;
  fetchImpl?: typeof fetch;
}

export interface CoreApiResponse {
  actions: CoreAction[];
}

export interface OutboundActionAckItem {
  id: number;
  success: boolean;
}

export interface CoreActionSender {
  sendMessage(to: string, text: string): Promise<boolean> | boolean;
  sendFile(to: string, filePath: string, caption?: string): Promise<boolean> | boolean;
}

const ACTION_SEND_TIMEOUT_MS = 15_000;

export class CoreApiClient {
  private readonly endpoint: string;
  private readonly token: string;
  private readonly requestTimeoutMs: number;
  private readonly fetchImpl: typeof fetch;

  constructor(options: CoreApiClientOptions) {
    this.endpoint = options.endpoint;
    this.token = options.token;
    this.requestTimeoutMs = options.requestTimeoutMs;
    this.fetchImpl = options.fetchImpl ?? fetch;
  }

  async sendEnvelope(envelope: NormalizedMessageEnvelope): Promise<CoreAction[]> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.requestTimeoutMs);
    const url = new URL("/api/core/messages", this.endpoint);

    try {
      const response = await this.fetchImpl(url, {
        method: "POST",
        headers: {
          "content-type": "application/json",
          authorization: `Bearer ${this.token}`,
        },
        body: JSON.stringify(envelope),
        signal: controller.signal,
      });

      if (!response.ok) {
        const errorBody = await safeReadText(response);
        throw new Error(`Core API HTTP ${response.status}: ${errorBody || response.statusText}`.trim());
      }

      const data = (await response.json()) as Partial<CoreApiResponse> | null;
      if (!data || !Array.isArray(data.actions)) {
        throw new Error("Core API response missing actions");
      }

      return data.actions.map(validateCoreAction);
    } catch (error) {
      if (isAbortError(error)) {
        throw new Error(`Core API request timed out after ${this.requestTimeoutMs}ms`);
      }

      throw error instanceof Error ? error : new Error(String(error));
    } finally {
      clearTimeout(timeout);
    }
  }

  async fetchOutboundActions(): Promise<CoreAction[]> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.requestTimeoutMs);
    const url = new URL("/api/core/actions", this.endpoint);

    try {
      const response = await this.fetchImpl(url, {
        method: "POST",
        headers: {
          "content-type": "application/json",
          authorization: `Bearer ${this.token}`,
        },
        body: JSON.stringify({}),
        signal: controller.signal,
      });

      if (!response.ok) {
        const errorBody = await safeReadText(response);
        throw new Error(`Core API HTTP ${response.status}: ${errorBody || response.statusText}`.trim());
      }

      const data = (await response.json()) as Partial<CoreApiResponse> | null;
      if (!data || !Array.isArray(data.actions)) {
        throw new Error("Core API response missing actions");
      }

      return data.actions.map(validateCoreAction);
    } catch (error) {
      if (isAbortError(error)) {
        throw new Error(`Core API request timed out after ${this.requestTimeoutMs}ms`);
      }

      throw error instanceof Error ? error : new Error(String(error));
    } finally {
      clearTimeout(timeout);
    }
  }

  async ackOutboundActions(items: OutboundActionAckItem[]): Promise<number> {
    if (!items.length) {
      return 0;
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.requestTimeoutMs);
    const url = new URL("/api/core/actions/ack", this.endpoint);

    try {
      const response = await this.fetchImpl(url, {
        method: "POST",
        headers: {
          "content-type": "application/json",
          authorization: `Bearer ${this.token}`,
        },
        body: JSON.stringify({ items }),
        signal: controller.signal,
      });

      if (!response.ok) {
        const errorBody = await safeReadText(response);
        throw new Error(`Core API HTTP ${response.status}: ${errorBody || response.statusText}`.trim());
      }

      const data = (await response.json()) as { updated?: unknown } | null;
      return typeof data?.updated === "number" ? data.updated : 0;
    } catch (error) {
      if (isAbortError(error)) {
        throw new Error(`Core API request timed out after ${this.requestTimeoutMs}ms`);
      }

      throw error instanceof Error ? error : new Error(String(error));
    } finally {
      clearTimeout(timeout);
    }
  }
}

export async function executeCoreActions(
  actions: CoreAction[],
  sender: CoreActionSender
): Promise<OutboundActionAckItem[]> {
  const results: OutboundActionAckItem[] = [];

  for (const action of actions) {
    let success = false;
    switch (action.action_type) {
      case "send_text":
        if (typeof action.chat_id !== "string" || typeof action.text !== "string") {
          throw new Error("Invalid core action payload: send_text");
        }
        try {
          success = Boolean(await withActionTimeout(sender.sendMessage(action.chat_id, action.text)));
        } catch {
          success = false;
        }
        break;
      case "send_file":
        if (typeof action.chat_id !== "string" || typeof action.file_path !== "string") {
          throw new Error("Invalid core action payload: send_file");
        }
        try {
          success = Boolean(await withActionTimeout(sender.sendFile(action.chat_id, action.file_path, action.caption)));
        } catch {
          success = false;
        }
        break;
      default:
        throw new Error(`Unknown core action: ${(action as { action_type?: unknown }).action_type}`);
    }

    if (typeof action.id === "number") {
      results.push({
        id: action.id,
        success,
      });
    }
  }

  return results;
}

async function withActionTimeout<T>(value: Promise<T> | T, timeoutMs: number = ACTION_SEND_TIMEOUT_MS): Promise<T> {
  let timer: ReturnType<typeof setTimeout> | undefined;
  try {
    return await Promise.race([
      Promise.resolve(value),
      new Promise<T>((_, reject) => {
        timer = setTimeout(() => reject(new Error(`Action send timed out after ${timeoutMs}ms`)), timeoutMs);
        timer.unref?.();
      }),
    ]);
  } finally {
    if (timer) {
      clearTimeout(timer);
    }
  }
}

async function safeReadText(response: Response): Promise<string> {
  try {
    return await response.text();
  } catch {
    return "";
  }
}

function isAbortError(error: unknown): boolean {
  return error instanceof Error && error.name === "AbortError";
}

function validateCoreAction(action: unknown): CoreAction {
  if (!isRecord(action)) {
    throw new Error("Invalid core action payload");
  }

  const actionType = action.action_type;
  if (actionType === "send_text") {
    if (typeof action.chat_id !== "string" || typeof action.text !== "string") {
      throw new Error("Invalid core action payload: send_text");
    }
    return {
      id: typeof action.id === "number" ? action.id : undefined,
      action_type: "send_text",
      chat_id: action.chat_id,
      text: action.text,
    };
  }

  if (actionType === "send_file") {
    if (typeof action.chat_id !== "string" || typeof action.file_path !== "string") {
      throw new Error("Invalid core action payload: send_file");
    }
    return {
      id: typeof action.id === "number" ? action.id : undefined,
      action_type: "send_file",
      chat_id: action.chat_id,
      file_path: action.file_path,
      caption: typeof action.caption === "string" ? action.caption : undefined,
    };
  }

  throw new Error(`Unknown core action: ${String(actionType)}`);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
