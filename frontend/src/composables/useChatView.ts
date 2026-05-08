/**
 * 主视图逻辑 composable
 * 抽离 sendMessage、generateAIResponse、scrollToBottom、事件处理等核心逻辑
 */
import { ref, watch, nextTick, h, type Ref } from "vue";
import { ElMessage } from "element-plus";
import { useClipboard } from "./useCopyToClipboard";
import type { ChatSession, ChatMessage, FileAttachment } from "@/types";
import type { TemplateInfo } from "@/types";

interface UseChatViewOptions {
  // 消息列表
  messages: Ref<ChatMessage[]>;
  // 上传文件
  uploadedFiles: Ref<FileAttachment[]>;
  attachmentItems: Ref<any[]>;
  // 输入框
  inputMessage: Ref<string>;
  // 当前后端会话 ID
  currentBackendSessionId: Ref<number | null>;
  // AI 模型
  model: Ref<string>;
  // 流式状态（来自 useSSEStream）
  isLoading: Ref<boolean>;
  currentAnswer: Ref<string>;
  currentThinking: Ref<string>;
  currentController: Ref<AbortController | null>;
  // 流式思考过程展开状态（来自 useThinking）
  streamingThinkingExpanded: Ref<boolean>;
  // SSE composable
  startStream: (body: Record<string, unknown>) => Promise<{ thinking: string; answer: string }>;
  abort: () => void;
  resetStream: () => void;
  normalizeAiErrorMessage: (msg: unknown) => string;
  // 会话 composable
  sessions: Ref<ChatSession[]>;
  currentSessionId: Ref<number | null>;
  createSession: () => void;
  deleteSession: (id: number, e: Event) => Promise<void>;
  renameSession: (id: number, title: string) => Promise<void>;
  switchSession: (id: number) => Promise<void>;
  refreshSessions: () => Promise<void>;
  // 模板选择 composable
  activeTemplateId: Ref<number | null>;
  isStrictTemplate: (id: number | null) => boolean;
  isIPCTemplate: (id: number | null) => boolean;
  buildMessageContent: (templateId: number | null, hasText: boolean, userText?: string) => string;
  buildDisplayContent: (
    templateId: number | null,
    hasText: boolean,
    hasAttachments: boolean,
    messageContent: string,
  ) => string;
  getTemplateById: (id: number | string) => TemplateInfo | undefined;
  selectTemplate: (id: number) => void;
  clearTemplateSelection: () => void;
  placeholderPromptsItems: Ref<{ key: string; label: string; description: string }[]>;
  placeholderPromptsStyles: Record<string, any>;
  // 滚动回调（由主组件从 MessageList 子组件传入）
  scrollToBottom: () => void;
}

export function useChatView(options: UseChatViewOptions) {
  const {
    messages,
    uploadedFiles,
    attachmentItems,
    inputMessage,
    currentBackendSessionId,
    model,
    isLoading,
    currentAnswer,
    currentThinking,
    currentController,
    streamingThinkingExpanded,
    startStream,
    abort,
    resetStream,
    normalizeAiErrorMessage,
    sessions,
    currentSessionId,
    createSession,
    deleteSession,
    renameSession,
    switchSession,
    refreshSessions,
    activeTemplateId,
    isStrictTemplate,
    isIPCTemplate,
    buildMessageContent,
    buildDisplayContent,
    getTemplateById,
    selectTemplate,
    clearTemplateSelection,
    placeholderPromptsItems,
    placeholderPromptsStyles,
    scrollToBottom,
  } = options;

  const { copy } = useClipboard();

  // 本地滚动用响应式（流式响应时由外部 watch 触发滚动）
  const currentResponse = ref("");

  // 预览弹窗状态（由主组件管理，这里仅返回操作函数）
  const previewDialogVisible = ref(false);
  const previewTitle = ref("");
  const previewContent = ref("");

  // 重命名弹窗状态
  const showRenameDialog = ref(false);
  const renameDialogTitle = ref("");
  const renameDialogSessionKey = ref<string | null>(null);

  // --- 对话菜单 ---
  function conversationMenu(conversation: { key: string }) {
    return {
      items: [
        { key: "rename", label: "重命名" },
        { key: "delete", label: "删除" },
      ],
      onClick: ({ key, domEvent }: { key: string; domEvent: Event }) => {
        if (key === "delete") {
          deleteSession(Number(conversation.key), domEvent);
        } else if (key === "rename") {
          const session = sessions.value.find((s) => String(s.id) === conversation.key);
          if (session) {
            renameDialogSessionKey.value = conversation.key;
            renameDialogTitle.value = session.title || "新对话";
            showRenameDialog.value = true;
          }
        }
      },
    };
  }

  // --- 模板提示点击 ---
  function onPromptsItemClick(info: any) {
    const key = info?.data?.key;
    const template = getTemplateById(key);
    if (template) {
      selectTemplate(template.id);
      inputMessage.value =
        template.id === 1 || template.id === 3 ? "" : template.prompt || "";
      sendMessage();
      return;
    }
    const desc = info?.data?.description;
    if (typeof desc === "string" && desc.trim()) {
      onSenderSubmit(desc.trim());
    }
  }

  // --- 发送消息 ---
  function onSenderSubmit(nextContent: string) {
    if (typeof nextContent === "string") inputMessage.value = nextContent;
    sendMessage();
  }

  function onSenderChange(value: string) {
    inputMessage.value = value || "";
  }

  async function sendMessage() {
    if (isLoading.value) return;

    const isAttachmentsReady = uploadedFiles.value.every((f) => f.parsed && !f.error);
    const isAttachmentsParsing = uploadedFiles.value.some((f) => !f.parsed && !f.error);

    if (!isAttachmentsReady) {
      ElMessage.warning(
        isAttachmentsParsing
          ? "文件解析中，请等待解析完成后再发送"
          : "存在解析失败的文件，请移除后再发送",
      );
      return;
    }

    const trimmed = inputMessage.value.trim();
    const hasText = !!trimmed;
    const hasAttachments = uploadedFiles.value.length > 0;
    if (!hasText && !hasAttachments) return;

    const templateId = activeTemplateId.value;
    const messageContent = buildMessageContent(templateId, hasText, trimmed);
    const displayContent = buildDisplayContent(
      templateId,
      hasText,
      hasAttachments,
      messageContent,
    );
    const attachments = hasAttachments ? [...uploadedFiles.value] : null;

    messages.value.push({
      role: "user",
      content: displayContent,
      fullContent: messageContent,
      timestamp: new Date(),
      attachments,
      templateId: templateId != null ? Number(templateId) : null,
    });

    nextTick(() => {
      inputMessage.value = "";
    });

    uploadedFiles.value = [];
    attachmentItems.value = [];

    const documentId =
      attachments && attachments.length > 0 ? attachments[0]?.id || null : null;

    await generateAIResponse(
      messageContent,
      attachments,
      {
        templateId: templateId != null ? Number(templateId) : null,
        documentId,
      },
    );

    clearTemplateSelection();
  }

  // --- 生成 AI 响应 ---
  async function generateAIResponse(
    message: string,
    attachments: FileAttachment[] | null,
    options: { templateId?: number | null; documentId?: number | null } = {},
  ) {
    const { templateId = null, documentId = null } = options;
    currentResponse.value = "";

    try {
      const isIPC = isIPCTemplate(templateId);
      const strict = isStrictTemplate(templateId);

      let userMessage = message;
      if (attachments && attachments.length > 0) {
        attachments.forEach((file) => {
          userMessage += `\n文档：${file.name} (${file.type})\n`;
          const parsedContent = file.parsedContent || (file as any).parsed_content;
          if (isIPC && parsedContent?.first_page_content) {
            userMessage += `文档第一页内容：\n${parsedContent.first_page_content.slice(0, 6000)}...\n`;
          } else if (parsedContent?.structured) {
            if (parsedContent.structured.title)
              userMessage += `标题：${parsedContent.structured.title}\n`;
            if (parsedContent.structured.abstract)
              userMessage += `摘要：${parsedContent.structured.abstract}\n`;
          }
        });
      }

      const contextMessages =
        isIPC || strict
          ? []
          : messages.value
              .filter((m) => m.role === "user" || m.role === "assistant")
              .map((m) => {
                const content = m.content || "";
                return { role: m.role, content };
              });

      const body: Record<string, unknown> = {
        messages: strict
          ? [...contextMessages, { role: "user", content: userMessage }]
          : [...contextMessages, { role: "user", content: userMessage }],
        stream: true,
        model: model.value || "qwen3:8b",
        passthrough: false,
      };

      if (strict) body.template_id = Number(templateId);
      if (currentBackendSessionId.value) body.session_id = currentBackendSessionId.value;
      if (documentId) body.document_id = documentId;

      const result = await startStream(body);

      currentResponse.value = result.thinking + "\n\n" + result.answer;

      messages.value.push({
        role: "assistant",
        content: result.answer || "抱歉，没有收到有效的响应。",
        thinking: result.thinking,
        timestamp: new Date(),
        thinkingExpanded: streamingThinkingExpanded.value,
      });

      nextTick(() => scrollToBottom());
      await refreshSessions();
    } catch (error: any) {
      console.error("生成 AI 响应失败:", error);
      if (error?.name === "AbortError") {
        if ((currentAnswer.value || "").trim().length > 0)
          messages.value.push({
            role: "assistant",
            content: currentAnswer.value,
            thinking: currentThinking.value,
            timestamp: new Date(),
            thinkingExpanded: streamingThinkingExpanded.value,
          });
      } else {
        const errorMessage = normalizeAiErrorMessage(error?.message);
        ElMessage.error(errorMessage);
        messages.value.push({
          role: "assistant",
          content: errorMessage,
          timestamp: new Date(),
        });
      }
    } finally {
      resetStream();
    }
  }

  // --- 重新生成 ---
  async function regenerateResponse(index: number) {
    const prev = messages.value[index - 1];
    if (typeof (prev?.fullContent || prev?.content) === "string") {
      messages.value.splice(index);
      await generateAIResponse(
        prev.fullContent || prev.content,
        prev.attachments,
        { templateId: prev.templateId },
      );
    }
  }

  // --- 复制 ---
  async function handleCopy(_content: string, content: string) {
    const text = (content || "").trim();
    if (!text) {
      ElMessage.warning("没有可复制的内容");
      return;
    }
    await copy(text);
  }

  // --- 预览 ---
  function handlePreview(file: FileAttachment) {
    const content = file.parsedContent || (file as any).parsed_content;
    if (!content) {
      ElMessage.warning("文档解析内容为空");
      return;
    }
    if (content.text) {
      previewContent.value = content.text;
    } else if (content.structured) {
      const { structured } = content;
      const parts: string[] = [];
      if (structured.title?.trim()) parts.push(`【标题】\n${structured.title}`);
      if (structured.abstract?.trim())
        parts.push(`【摘要】\n${structured.abstract}`);
      if (structured.claims?.length > 0) {
        const claimsText = structured.claims
          .map((c: any) => `${c.number}. ${c.content}`)
          .join("\n\n");
        parts.push(`【权利要求】\n${claimsText}`);
      }
      if (structured.description?.trim())
        parts.push(`【说明书正文】\n${structured.description}`);
      if (parts.length > 0) {
        previewContent.value = parts.join("\n\n");
      } else {
        previewContent.value = "文档解析内容为空，请重新上传或检查文档格式。";
      }
    } else if (typeof content === "string") {
      previewContent.value = content;
    } else {
      previewContent.value = "文档解析内容为空，请重新上传或检查文档格式。";
    }
    previewTitle.value = file.name;
    previewDialogVisible.value = true;
  }

  // --- 重命名确认 ---
  async function confirmRename() {
    if (renameDialogSessionKey.value && renameDialogTitle.value.trim()) {
      await renameSession(
        Number(renameDialogSessionKey.value),
        renameDialogTitle.value.trim(),
      );
    }
    showRenameDialog.value = false;
  }

  // --- 新建会话并关闭侧边栏 ---
  function createNewSessionAndHideSidebar() {
    createSession();
    inputMessage.value = "";
    uploadedFiles.value = [];
    attachmentItems.value = [];
  }

  // --- 切换会话 ---
  async function onConversationActiveChange(key: string) {
    if (key) {
      await switchSession(Number(key));
    }
  }

  // --- 渲染发送按钮 ---
  function renderSenderActions(
    _ori: unknown,
    { components }: { components: { LoadingButton: unknown; SendButton: unknown } },
  ) {
    if (isLoading.value) return h(components.LoadingButton);
    const hasText = !!inputMessage.value.trim();
    const hasFiles = uploadedFiles.value.length > 0;
    const ready = uploadedFiles.value.every((f) => f.parsed && !f.error);
    const disabled = isLoading.value || (!hasText && !hasFiles) || !ready;
    return h(components.SendButton, { disabled });
  }

  // --- 流式响应滚动 ---
  watch(currentResponse, () => {
    nextTick(() => scrollToBottom());
  });

  // --- 停止加载点击处理器 ---
  function stopLoadingClickHandler(e: MouseEvent) {
    if (e.target && isLoading.value && currentController.value) {
      const el = (e.target as HTMLElement).closest?.(
        ".ant-sender-actions-btn-loading-icon, .ant-sender-send-button, .send-btn",
      );
      if (el) {
        abort();
        isLoading.value = false;
      }
    }
  }

  // --- setup / cleanup ---
  let removeClickListener: (() => void) | null = null;

  function setup() {
    removeClickListener = () =>
      document.removeEventListener("click", stopLoadingClickHandler, true);
    document.addEventListener("click", stopLoadingClickHandler, true);
  }

  function cleanup() {
    removeClickListener?.();
  }

  return {
    // ref
    currentResponse,
    previewDialogVisible,
    previewTitle,
    previewContent,
    showRenameDialog,
    renameDialogTitle,
    renameDialogSessionKey,
    // composable state (re-export for binding)
    placeholderPromptsItems,
    placeholderPromptsStyles,
    // computed
    conversationsItems: computed(() =>
      (Array.isArray(sessions.value) ? sessions.value : []).map((session) => {
        const time = session.updatedAt || session.createdAt || Date.now();
        return {
          key: String(session.id),
          timestamp: typeof time === "number" ? time : undefined,
          label: session.title || "新对话",
        };
      }),
    ),
    activeConversationKey: computed(() =>
      currentSessionId.value == null ? undefined : String(currentSessionId.value),
    ),
    // methods
    conversationMenu,
    onPromptsItemClick,
    onSenderSubmit,
    onSenderChange,
    sendMessage,
    generateAIResponse,
    regenerateResponse,
    handleCopy,
    handlePreview,
    confirmRename,
    createNewSessionAndHideSidebar,
    onConversationActiveChange,
    renderSenderActions,
    setup,
    cleanup,
  };
}