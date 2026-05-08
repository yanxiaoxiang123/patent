/**
 * SSE 流式响应 composable
 * 处理 Fetch API + SSE 流解析，暴露 thinking/content 累积和流状态
 * 内置 50ms 批量更新节流，避免每个 chunk 触发 Vue 响应式重渲染
 */
import { ref } from "vue";

const BATCH_INTERVAL_MS = 50;

export interface SSEStreamOptions {
  apiUrl?: string;
  model?: string;
}

export function useSSEStream() {
  const currentThinking = ref("");
  const currentAnswer = ref("");
  const isLoading = ref(false);
  const currentController = ref<AbortController | null>(null);

  function normalizeAiErrorMessage(rawMessage: unknown): string {
    const text = String(rawMessage || "").trim();
    if (!text) return "抱歉，AI 服务暂时不可用，请稍后重试。";
    if (
      text.includes("Ollama API 调用失败") ||
      text.includes("Ollama API 错误") ||
      text.includes("502")
    ) {
      return "抱歉，AI 服务暂时不可用，请稍后重试。";
    }
    if (text.includes("模型配置或请求参数错误")) {
      return "抱歉，模型配置或请求参数错误，请联系管理员检查模型配置。";
    }
    if (text.includes("无法连接到 Ollama 服务")) {
      return "抱歉，无法连接 AI 服务，请稍后重试。";
    }
    return text;
  }

  /**
   * 批量更新 reactive refs，每 BATCH_INTERVAL_MS 毫秒最多一次
   * 避免每个 SSE chunk 都触发 Vue 响应式 → 数百次 Markdown 重渲染
   */
  function createBatchUpdater(refObj: { value: string }, accumKey: string) {
    let pending = "";
    let timer: ReturnType<typeof setTimeout> | null = null;

    return {
      append(text: string) {
        pending += text;
        if (!timer) {
          timer = setTimeout(() => {
            refObj.value += pending;
            pending = "";
            timer = null;
          }, BATCH_INTERVAL_MS);
        }
      },
      flush() {
        if (timer) {
          clearTimeout(timer);
          timer = null;
        }
        if (pending) {
          refObj.value += pending;
          pending = "";
        }
      },
    };
  }

  async function startStream(
    body: Record<string, unknown>,
    options: { apiUrl?: string; model?: string } = {}
  ): Promise<{ thinking: string; answer: string }> {
    isLoading.value = true;
    currentThinking.value = "";
    currentAnswer.value = "";

    const thinkingBatcher = createBatchUpdater(currentThinking, "thinking");
    const answerBatcher = createBatchUpdater(currentAnswer, "answer");

    const apiUrl = options.apiUrl || "/api/ai/chat";
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "text/event-stream, application/json;q=0.9, */*;q=0.8",
      "Cache-Control": "no-cache",
    };
    const token = localStorage.getItem("token");
    if (token) headers.Authorization = `Bearer ${token}`;

    const controller = new AbortController();
    currentController.value = controller;

    const response = await fetch(apiUrl, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`AI 服务响应失败: ${response.status}`);
    }

    if (response.body) {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let currentEvent = "message";
      let currentData = "";
      let streamError = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        while (buffer.includes("\n")) {
          const newlineIndex = buffer.indexOf("\n");
          const line = buffer.substring(0, newlineIndex);
          buffer = buffer.substring(newlineIndex + 1);

          if (line.trim() === "") {
            if (currentData === "[DONE]") break;

            if (currentData) {
              try {
                const parsed = JSON.parse(currentData);
                if (parsed?.choices?.[0]?.delta) {
                  const delta = parsed.choices[0].delta;
                  if (currentEvent === "error") {
                    streamError = normalizeAiErrorMessage(delta.content);
                  } else {
                    if (delta.thinking) thinkingBatcher.append(delta.thinking);
                    if (delta.content) answerBatcher.append(delta.content);
                  }
                }
              } catch {
                // 忽略非 JSON 片段
              }
            }
            currentEvent = "message";
            currentData = "";
            continue;
          }

          if (line.startsWith("event:")) {
            currentEvent = line.slice(6).trim();
          } else if (line.startsWith("data:")) {
            currentData = line.slice(5);
          }
        }
      }

      // flush 最后一次批量未提交的内容
      thinkingBatcher.flush();
      answerBatcher.flush();

      if (streamError) {
        currentThinking.value = "";
        currentAnswer.value = streamError;
      }
    }

    return {
      thinking: currentThinking.value,
      answer: currentAnswer.value,
    };
  }

  function abort() {
    if (currentController.value) {
      currentController.value.abort();
      currentController.value = null;
    }
  }

  function reset() {
    isLoading.value = false;
    currentThinking.value = "";
    currentAnswer.value = "";
    currentController.value = null;
  }

  return {
    currentThinking,
    currentAnswer,
    isLoading,
    currentController,
    startStream,
    abort,
    reset,
    normalizeAiErrorMessage,
  };
}