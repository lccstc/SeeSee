export function getSyncChatName(chatId: string, chatName?: string | null): string {
  const normalized = chatName?.trim();
  return normalized ? normalized : chatId;
}
