/**
 * SSE 流式响应 composable
 *
 * 基于 Fetch API + ReadableStream 手动解析 SSE，支持 POST 请求体。
 *
 * 核心机制：
 * 1. **rAF 批量更新** — 用 requestAnimationFrame 替代固定 setTimeout，
 *    与浏览器渲染帧同步（~16ms @60fps），消除 50ms 定时器与帧率错位
 *    导致的「卡顿 → 突然跳出一大段」视觉问题。
 * 2. **自动重连** — 网络闪断时自动重试（指数退避，最多 3 次），
 *    已接收的内容不会丢失，重连后继续追加。
 * 3. **中断保留** — abort() 先 flush 所有 batcher，确保部分内容不丢失。
 */
import { ref } from "vue";

/** 重连配置 */
const MAX_RETRIES = 3;
const BASE_RETRY_DELAY_MS = 1000;
const MAX_RETRY_DELAY_MS = 8000;

export interface SSEStreamOptions {
  apiUrl?: string;
  model?: string;
}

export function useSSEStream() {
  const currentThinking = ref("");
  const currentAnswer = ref("");
  const isLoading = ref(false);
  const currentController = ref<AbortController | null>(null);

  // 保存 batcher 引用，以便 abort 时 flush
  let _thinkingBatcher: ReturnType<typeof createRafBatchUpdater> | null = null;
  let _answerBatcher: ReturnType<typeof createRafBatchUpdater> | null = null;

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
   * rAF 批量更新器
   *
   * 用 requestAnimationFrame 代替固定 50ms setTimeout：
   * - 每个渲染帧最多触发一次 Vue 响应式更新
   * - 在 60fps 屏幕上约 16.7ms 一帧，比固定 50ms 更流畅
   * - 自动与浏览器渲染管线对齐，避免「刷新抖动」
   * - Token 生成速率不论多快，都只在下一帧批量写入
   */
  function createRafBatchUpdater(refObj: { value: string }) {
    let pending = "";
    let rafId: number | null = null;

    return {
      append(text: string) {
        pending += text;
        if (rafId === null) {
          rafId = requestAnimationFrame(() => {
            refObj.value += pending;
            pending = "";
            rafId = null;
          });
        }
      },
      flush() {
        if (rafId !== null) {
          cancelAnimationFrame(rafId);
          rafId = null;
        }
        if (pending) {
          refObj.value += pending;
          pending = "";
        }
      },
    };
  }

  /**
   * 解析单次 fetch 响应中的 SSE 事件流
   *
   * 返回值：
   * - completed: 是否收到 [DONE]（正常结束）
   * - streamError: 后端返回的错误消息（如果有）
   */
  async function consumeStream(
    body: ReadableStream<Uint8Array>,
    thinkingBatcher: ReturnType<typeof createRafBatchUpdater>,
    answerBatcher: ReturnType<typeof createRafBatchUpdater>,
  ): Promise<{ completed: boolean; streamError: string }> {
    const reader = body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let currentEvent = "message";
    let currentData = "";
    let streamError = "";
    let completed = false;

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        while (buffer.includes("\n")) {
          const newlineIndex = buffer.indexOf("\n");
          const line = buffer.substring(0, newlineIndex);
          buffer = buffer.substring(newlineIndex + 1);

          if (line.trim() === "") {
            if (currentData === "[DONE]") {
              completed = true;
              break;
            }

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

        if (completed) break;
      }
    } finally {
      try {
        reader.releaseLock();
      } catch {
        // reader 可能已经关闭
      }
    }

    return { completed, streamError };
  }

  /**
   * 判断错误是否为可重试的网络错误（而非用户操作或服务端拒绝）
   */
  function isRetryableError(error: unknown): boolean {
    if (error instanceof DOMException && error.name === "AbortError") {
      return false;
    }
    if (error instanceof TypeError) {
      // fetch 网络错误（DNS 失败、连接重置等）
      return true;
    }
    const msg = String(error).toLowerCase();
    return (
      msg.includes("network") ||
      msg.includes("failed to fetch") ||
      msg.includes("connection") ||
      msg.includes("econnreset") ||
      msg.includes("timeout")
    );
  }

  async function startStream(
    body: Record<string, unknown>,
    options: { apiUrl?: string; model?: string } = {},
  ): Promise<{ thinking: string; answer: string }> {
    isLoading.value = true;
    currentThinking.value = "";
    currentAnswer.value = "";

    const thinkingBatcher = createRafBatchUpdater(currentThinking);
    const answerBatcher = createRafBatchUpdater(currentAnswer);

    _thinkingBatcher = thinkingBatcher;
    _answerBatcher = answerBatcher;

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

    let retryCount = 0;
    let completed = false;
    let streamError = "";

    while (!completed && retryCount <= MAX_RETRIES) {
      try {
        const response = await fetch(apiUrl, {
          method: "POST",
          headers,
          body: JSON.stringify(body),
          signal: controller.signal,
        });

        if (!response.ok) {
          // HTTP 4xx/5xx 不重试
          throw new Error(`AI 服务响应失败: ${response.status}`);
        }

        if (response.body) {
          const result = await consumeStream(
            response.body,
            thinkingBatcher,
            answerBatcher,
          );
          completed = result.completed;
          streamError = result.streamError;
        } else {
          completed = true;
        }

        // 正常结束或有错误消息，退出重试循环
        if (completed || streamError) break;

        // 流意外中断（服务器关闭连接但没发 [DONE]），尝试重连
        retryCount++;
        if (retryCount <= MAX_RETRIES) {
          const delay = Math.min(
            BASE_RETRY_DELAY_MS * Math.pow(2, retryCount - 1),
            MAX_RETRY_DELAY_MS,
          );
          console.warn(
            `SSE 流中断，${delay}ms 后重试 (${retryCount}/${MAX_RETRIES})`,
          );
          await new Promise((resolve) => setTimeout(resolve, delay));
        }
      } catch (error: unknown) {
        // 用户主动中断，直接抛出
        if (
          error instanceof DOMException &&
          error.name === "AbortError"
        ) {
          throw error;
        }

        // 可重试的网络错误
        if (isRetryableError(error) && retryCount < MAX_RETRIES) {
          retryCount++;
          const delay = Math.min(
            BASE_RETRY_DELAY_MS * Math.pow(2, retryCount - 1),
            MAX_RETRY_DELAY_MS,
          );
          console.warn(
            `SSE 网络错误，${delay}ms 后重试 (${retryCount}/${MAX_RETRIES}):`,
            error,
          );
          await new Promise((resolve) => setTimeout(resolve, delay));
          continue;
        }

        // 不可重试的错误
        throw error;
      }
    }

    // flush 最后一批未提交的内容
    thinkingBatcher.flush();
    answerBatcher.flush();

    if (streamError) {
      currentThinking.value = "";
      currentAnswer.value = streamError;
    }

    return {
      thinking: currentThinking.value,
      answer: currentAnswer.value,
    };
  }

  function abort() {
    // 先 flush batcher 中暂存的内容到 reactive refs
    // 确保中断时不丢失任何已接收但尚未刷新的文本
    _thinkingBatcher?.flush();
    _answerBatcher?.flush();

    if (currentController.value) {
      currentController.value.abort();
      currentController.value = null;
    }
  }

  function reset() {
    isLoading.value = false;
    // 不清空 currentAnswer / currentThinking
    // 由 startStream 开头统一清空
    currentController.value = null;
    _thinkingBatcher = null;
    _answerBatcher = null;
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
