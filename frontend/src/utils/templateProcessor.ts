/**
 * Template Processing Utility
 *
 * Unified handling for all patent templates (1, 2, 3, 5)
 * All templates use template_id parameter and clear conversation history
 */

export type TemplateId = 1 | 2 | 3 | 5;

// All strict templates that use template_id parameter
const STRICT_TEMPLATES: TemplateId[] = [1, 2, 3, 5];

/**
 * Check if template is a strict template (uses template_id + empty message)
 */
export function isStrictTemplate(
  templateId: number | null,
): templateId is TemplateId {
  return (
    templateId !== null && STRICT_TEMPLATES.includes(templateId as TemplateId)
  );
}

/**
 * Check if template is IPC classification template
 */
export function isIPCTemplate(templateId: number | null): templateId is 5 {
  return templateId === 5;
}

/**
 * Get message content for the template
 * - Strict templates (1,2,3,5): empty message when no text input
 * - IPC template: special IPC classification prompt
 * - Free chat: default guidance message
 */
export function getMessageContent(
  templateId: number | null,
  hasText: boolean,
  userPrompt?: string,
): string {
  if (hasText) {
    return userPrompt || "";
  }

  if (isIPCTemplate(templateId)) {
    return "请根据我上传的专利文档内容，帮我进行 IPC 分类，并说明每个分类号的含义和选择理由。";
  }

  if (isStrictTemplate(templateId)) {
    return ""; // Templates 1, 2, 3, 5 use empty message
  }

  return "请根据我刚刚上传的专利文档，先给出整体概览、关键创新点和主要风险点的审核意见。";
}

/**
 * Determine if context messages should be cleared for this template
 */
export function shouldClearContextMessages(templateId: number | null): boolean {
  return isStrictTemplate(templateId);
}

/**
 * Determine if template_id should be included in the request
 */
export function shouldUseTemplateId(
  templateId: number | null,
): templateId is TemplateId {
  return isStrictTemplate(templateId);
}

/**
 * Build the request body for AI chat
 */
export interface AIRequestBody {
  messages: Array<{ role: string; content: string }>;
  stream: boolean;
  model: string;
  passthrough: boolean;
  template_id?: TemplateId;
  session_id?: string | null;
  document_id?: string | null;
}

export interface Message {
  role: "user" | "assistant" | "system";
  content: string;
}

export function buildRequestBody(
  templateId: number | null,
  userMessage: string,
  contextMessages: Message[],
  backendSessionId: string | null = null,
  documentId: string | null = null,
): AIRequestBody {
  const useStrictTemplate = isStrictTemplate(templateId);

  const messages = useStrictTemplate
    ? [...contextMessages, { role: "user", content: userMessage }]
    : [
        { role: "system", content: "你是一个专业的专利审核助手" },
        ...contextMessages,
        { role: "user", content: userMessage },
      ];

  return {
    messages,
    stream: true,
    model: "qwen3:8b",
    passthrough: false,
    ...(shouldUseTemplateId(templateId) && {
      template_id: templateId as TemplateId,
    }),
    ...(backendSessionId && { session_id: backendSessionId }),
    ...(documentId && { document_id: documentId }),
  };
}
