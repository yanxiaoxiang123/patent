/**
 * 消息处理工具
 */

import type { ChatMessage } from "@/types";
import { splitThinking } from "./thinking";

/**
 * 生成会话标题
 */
export function generateSessionTitle(messages: ChatMessage[]): string {
  if (messages.length === 0) return "新对话";

  const userMessage = messages.find((msg) => msg.role === "user");
  if (userMessage) {
    // 如果有附件，显示"已解析文档"
    const attachments = userMessage.attachments;
    if (attachments && attachments.length > 0) {
      return "已解析文档";
    }

    const content = userMessage.content || "";
    const fullContent = userMessage.fullContent || "";

    // 检查是否是上传文档后的审核会话
    const isUploadedDoc =
      !content ||
      content === "" ||
      content === "（已上传文档，按模板审核）" ||
      content.length < 5;

    // 检查 fullContent 是否包含文档内容片段
    const hasDocContent =
      fullContent &&
      (fullContent.includes("文档：") ||
        fullContent.includes("标题：") ||
        fullContent.includes("摘要：") ||
        fullContent.includes("权利要求"));

    if (isUploadedDoc || hasDocContent) {
      return "已解析文档";
    }

    return content.length > 20 ? content.substring(0, 20) + "..." : content;
  }

  return "新对话";
}

/**
 * 构建消息历史（用于发送给 AI）
 */
export function buildMessageHistory(
  messages: ChatMessage[],
  limit: number = 10,
): Array<{ role: string; content: string }> {
  const conversationMessages = messages.filter(
    (m) => m.role === "user" || m.role === "assistant",
  );

  const limitedMessages = conversationMessages.slice(-limit);

  return limitedMessages.map((m) => {
    const original =
      "fullContent" in m && typeof m.fullContent === "string"
        ? m.fullContent
        : typeof m.content === "string"
          ? m.content
          : "";

    if (m.role === "assistant") {
      // 只保留答案部分，去掉思考过程
      const parts = splitThinking(original);
      return {
        role: "assistant" as const,
        content: parts.answer || original,
      };
    }

    return {
      role: "user" as const,
      content: original,
    };
  });
}

/**
 * 格式化时间
 */
export function formatTime(timestamp: Date | number | string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days === 0) {
    return "今天";
  } else if (days === 1) {
    return "昨天";
  } else if (days < 7) {
    return `${days}天前`;
  } else {
    return date.toLocaleDateString();
  }
}
