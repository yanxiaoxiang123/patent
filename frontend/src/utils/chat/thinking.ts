/**
 * 思考内容处理工具
 */

export interface ThinkingParts {
  thinking: string | null;
  answer: string;
  hasThinking: boolean;
}

export interface SplitOptions {
  allowPartial?: boolean;
}

/**
 * 检查内容是否包含思考过程结构
 */
export function hasThinkingStructure(
  content: string | null | undefined,
): boolean {
  if (!content || typeof content !== "string") return false;

  const thinkingLabels = [
    "思考过程（简要分析）：",
    "思考过程（简要分析）:",
    "思考过程：",
    "思考过程:",
  ];
  const answerLabels = ["最终回答：", "最终回答:"];

  const hasThinking = thinkingLabels.some((label) => content.includes(label));
  const hasAnswer = answerLabels.some((label) => content.includes(label));

  return hasThinking && hasAnswer;
}

/**
 * 分割思考过程和最终回答
 */
export function splitThinking(
  content: string | null | undefined,
  options: SplitOptions = {},
): ThinkingParts {
  if (!content || typeof content !== "string") {
    return {
      thinking: null,
      answer: content || "",
      hasThinking: false,
    };
  }

  const thinkingLabels = [
    "思考过程（简要分析）：",
    "思考过程（简要分析）:",
    "思考过程：",
    "思考过程:",
  ];
  const answerLabels = ["最终回答：", "最终回答:"];

  let thinkingLabel = "";
  let thinkingIndex = -1;
  for (const label of thinkingLabels) {
    const idx = content.indexOf(label);
    if (idx !== -1) {
      thinkingLabel = label;
      thinkingIndex = idx;
      break;
    }
  }

  if (thinkingIndex === -1) {
    return {
      thinking: null,
      answer: content,
      hasThinking: false,
    };
  }

  let answerLabel = "";
  let answerIndex = -1;
  for (const label of answerLabels) {
    const idx = content.indexOf(label, thinkingIndex + thinkingLabel.length);
    if (idx !== -1) {
      answerLabel = label;
      answerIndex = idx;
      break;
    }
  }

  if (answerIndex === -1) {
    if (!options.allowPartial) {
      return {
        thinking: null,
        answer: content,
        hasThinking: false,
      };
    }

    const thinkingOnlyBody = content
      .slice(thinkingIndex + thinkingLabel.length)
      .trim();
    if (!thinkingOnlyBody) {
      return {
        thinking: null,
        answer: content,
        hasThinking: false,
      };
    }

    return {
      thinking: `思考过程：\n${thinkingOnlyBody}`,
      answer: "",
      hasThinking: true,
    };
  }

  const thinkingBody = content
    .slice(thinkingIndex + thinkingLabel.length, answerIndex)
    .trim();
  const answerBody = content.slice(answerIndex + answerLabel.length).trim();

  if (!thinkingBody && !answerBody) {
    return {
      thinking: null,
      answer: content,
      hasThinking: false,
    };
  }

  return {
    thinking: thinkingBody ? `思考过程：\n${thinkingBody}` : null,
    answer: answerBody || "",
    hasThinking: !!thinkingBody,
  };
}

/**
 * 确保内容包含思考过程结构（如果需要）
 */
export function ensureThinkingStructure(
  content: string,
  options: any = {},
): string {
  if (!content || typeof content !== "string") return content || "";
  if (hasThinkingStructure(content)) return content;
  return content;
}
