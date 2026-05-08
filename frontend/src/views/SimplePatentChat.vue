<template>
  <div class="patent-chat">
    <!-- 侧边栏背景遮罩 -->
    <Transition name="fade">
      <div
        v-if="showSidebar"
        class="sidebar-backdrop"
        @click="showSidebar = false"
      />
    </Transition>

    <!-- 聊天记录侧边栏 -->
    <Transition name="slide">
      <div v-if="showSidebar" class="session-sidebar ax-menu">
        <div class="sidebar-header">
          <div class="sidebar-title">聊天记录</div>
          <Button
            type="text"
            size="small"
            class="sidebar-close-btn"
            @click="showSidebar = false"
          >
            <template #icon>
              <CloseOutlined />
            </template>
          </Button>
        </div>

        <Button
          type="link"
          class="sidebar-add-btn"
          @click="createNewSessionAndHideSidebar"
        >
          <template #icon>
            <PlusOutlined />
          </template>
          新建会话
        </Button>

        <Conversations
          v-if="conversationsItems.length > 0"
          class="ax-conversations"
          :items="conversationsItems"
          :active-key="activeConversationKey"
          :menu="conversationMenu"
          @active-change="onConversationActiveChange"
        />

        <div v-else class="empty-sessions">
          <el-icon size="32" color="#d1d5db"><Files /></el-icon>
          <p>暂无聊天记录</p>
        </div>
      </div>
    </Transition>

    <div class="chat-layout">
      <!-- 主聊天区域 -->
      <div class="chat-main-area">
        <div class="chat-top-bar">
          <div class="chat-top-bar-left">
            <!-- 侧边栏切换按钮 -->
            <div v-if="!showSidebar" class="sidebar-toggle">
              <el-tooltip content="显示聊天记录" placement="bottom">
                <el-button
                  type="default"
                  size="small"
                  circle
                  @click="showSidebar = true"
                >
                  <el-icon><Files /></el-icon>
                </el-button>
              </el-tooltip>
            </div>

            <div class="chat-brand">
              <img class="chat-logo-dot" :src="chatLogoSrc" alt="" />
              <div class="chat-brand-text">
                <div class="chat-brand-title">专利 AI 助手</div>
              </div>
            </div>
          </div>
          <div class="chat-actions">
            <el-button
              v-if="isAdmin"
              type="default"
              size="small"
              @click="$router.push('/admin/users')"
            >
              用户管理
            </el-button>
          </div>
        </div>

        <div class="chat-content-wrapper">
          <!-- 空状态欢迎页 -->
          <div
            v-if="messages.length === 0 && !isLoading"
            class="ax-placeholder"
          >
            <Welcome
              variant="borderless"
              title="今天有什么可以帮到你？"
              description="上传专利文档或直接提问，我会给出结构化建议。"
            />
            <Prompts
              title="模板示例"
              wrap
              class="ax-prompts ax-prompts-placeholder"
              :items="placeholderPromptsItems"
              :styles="placeholderPromptsStyles"
              @item-click="onPromptsItemClick"
            />
          </div>

          <!-- 消息列表 -->
          <div ref="bubbleListRef" class="ax-messages">
            <TransitionGroup
              name="message-list"
              tag="div"
              class="messages-wrapper"
            >
              <div
                v-for="(message, index) in messages"
                :key="message.id || index"
                class="message-item-wrapper"
              >
                <!-- 用户消息 -->
                <MessageBubble
                  v-if="message.role === 'user'"
                  role="user"
                  :content="message.content"
                  :timestamp="message.timestamp"
                  :attachments="message.attachments"
                  @preview="handlePreview"
                />

                <!-- AI 消息 -->
                <MessageBubble
                  v-else
                  role="ai"
                  :content="message.content"
                  :timestamp="message.timestamp"
                  :thinking-content="message.thinking"
                  :thinking-expanded="
                    message.thinkingExpanded ?? isThinkingVisible(index)
                  "
                  :show-actions="true"
                  :attachments="message.attachments"
                  @toggle-thinking="toggleThinking(index)"
                  @copy="handleCopy($event, message.content)"
                  @regenerate="regenerateResponse(index)"
                  @preview="handlePreview"
                />
              </div>
            </TransitionGroup>

            <!-- 流式响应 -->
            <div
              v-if="isLoading"
              class="streaming-message message-item-wrapper"
            >
              <MessageBubble
                role="ai"
                :content="currentAnswer"
                :is-streaming="true"
                :thinking-content="currentThinking"
                @toggle-thinking="toggleStreamingThinking"
              />
            </div>
          </div>
        </div>

        <!-- 输入框区域 -->
        <Sender
          :value="inputMessage"
          :loading="isLoading"
          :disabled="isLoading"
          :actions="renderSenderActions"
          class="ax-sender"
          @submit="onSenderSubmit"
          @change="onSenderChange"
        >
          <template #prefix>
            <Badge :dot="uploadedFiles.length > 0 && !attachmentsOpen">
              <Button type="text" @click="attachmentsOpen = !attachmentsOpen">
                <template #icon>
                  <PaperClipOutlined />
                </template>
              </Button>
            </Badge>
          </template>

          <template #header>
            <Sender.Header
              title="附件"
              :open="attachmentsOpen"
              :styles="{ content: { padding: 0 } }"
              @open-change="(open) => (attachmentsOpen = open)"
            >
              <Attachments
                :before-upload="beforeAntdUpload"
                :custom-request="handleAttachmentCustomRequest"
                :items="attachmentItems"
                accept=".doc,.docx,.pdf"
                :multiple="true"
                :on-remove="handleAttachmentRemove"
                @change="handleAttachmentsChange"
              >
                <template #placeholder="type">
                  <Flex
                    v-if="type && type.type === 'inline'"
                    align="center"
                    justify="center"
                    vertical
                    gap="2"
                    class="ax-attachments-inline"
                  >
                    <Typography.Text style="font-size: 30px; line: 1">
                      <CloudUploadOutlined />
                    </Typography.Text>
                    <Typography.Title
                      :level="5"
                      style="margin: 0; font-size: 14px; line: 1.5"
                    >
                      上传文档
                    </Typography.Title>
                    <Typography.Text type="secondary">
                      点击或拖拽文件到此处上传（.doc/.docx/.pdf，≤20MB）
                    </Typography.Text>
                  </Flex>
                  <Typography.Text v-if="type && type.type === 'drop'">
                    松开即可上传
                  </Typography.Text>
                </template>
              </Attachments>
            </Sender.Header>
          </template>
        </Sender>

        <div class="page-disclaimer">内容由 AI 生成，请仔细甄别</div>

        <!-- 设置对话框 -->
        <el-dialog v-model="showSettings" title="设置" width="400px">
          <el-form :model="settings" label-width="100px">
            <el-form-item label="AI 模型">
              <el-select v-model="settings.model">
                <el-option label="Qwen3-8b (快速)" value="qwen3:8b" />
                <el-option label="Qwen3-72b (专业)" value="qwen3:72b" />
              </el-select>
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="showSettings = false">关闭</el-button>
          </template>
        </el-dialog>

        <!-- 重命名会话对话框 -->
        <el-dialog v-model="showRenameDialog" title="重命名会话" width="400px" @keyup.enter="confirmRename">
          <el-input v-model="renameDialogTitle" placeholder="请输入新的会话标题" />
          <template #footer>
            <el-button @click="showRenameDialog = false">取消</el-button>
            <el-button type="primary" @click="confirmRename" :disabled="!renameDialogTitle.trim()">确定</el-button>
          </template>
        </el-dialog>

        <!-- 预览对话框 -->
        <ContentPreviewDialog
          v-model="previewDialogVisible"
          :title="previewTitle"
          :content="previewContent"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, h, nextTick, watch, onMounted, computed } from "vue";
import { ElMessage } from "element-plus";
import { Files } from "@element-plus/icons-vue";
import { Badge, Button, Flex, Typography } from "ant-design-vue";
import {
  CloudUploadOutlined,
  CloseOutlined,
  PaperClipOutlined,
  PlusOutlined,
} from "@ant-design/icons-vue";
import {
  Attachments,
  Conversations,
  Prompts,
  Sender,
  Welcome,
} from "ant-design-x-vue";
import chatLogoSrc from "../../../pic/0.png";
import { useAuthStore } from "@/stores/auth";
import { useThinking } from "@/composables/useThinking";
import { useChatSession } from "@/composables/useChatSession";
import { useFileUpload } from "@/composables/useFileUpload";
import { useClipboard } from "@/composables/useCopyToClipboard";
import { useSSEStream } from "@/composables/useSSEStream";
import { useTemplateSelector } from "@/composables/useTemplateSelector";
import MessageBubble from "@/components/message-bubble/index.vue";
import ContentPreviewDialog from "@/components/common/ContentPreviewDialog.vue";

const UPLOADED_FILES_STORAGE_KEY = "patent_uploaded_files";
const AI_MODEL_STORAGE_KEY = "patent_ai_model";

// Composables
const {
  toggleThinking,
  isThinkingVisible,
  streamingThinkingExpanded,
  toggleStreamingThinking,
} = useThinking();
const {
  sessions: chatSessions,
  currentSessionId,
  messages,
  loadSessions,
  createSession,
  deleteSession,
  renameSession,
  refreshSessions,
  switchSession,
} = useChatSession();
const {
  uploadedFiles,
  attachmentItems,
  isAttachmentsReady,
  isAttachmentsParsing,
  handleAttachmentCustomRequest,
  handleAttachmentRemove,
  handleAttachmentsChange,
  loadUploadedFiles,
} = useFileUpload();
const { copy } = useClipboard();
const {
  currentThinking,
  currentAnswer,
  isLoading,
  currentController,
  startStream,
  abort,
  reset: resetStream,
  normalizeAiErrorMessage,
} = useSSEStream();
const {
  activeTemplateId,
  templates: patentTemplates,
  primaryTemplates,
  secondaryTemplates,
  placeholderPromptsItems,
  placeholderPromptsStyles,
  getTemplateById,
  isStrictTemplate,
  isIPCTemplate,
  buildMessageContent,
  buildDisplayContent,
  selectTemplate,
  clearSelection: clearTemplateSelection,
} = useTemplateSelector();

// State
const showSidebar = ref(false);
const inputMessage = ref("");
const currentResponse = ref("");
const attachmentsOpen = ref(false);
const showSettings = ref(false);
const showRenameDialog = ref(false);
const renameDialogTitle = ref("");
const renameDialogSessionKey = ref<string | null>(null);
const previewDialogVisible = ref(false);
const previewTitle = ref("");
const previewContent = ref("");
const bubbleListRef = ref(null);
const currentBackendSessionId = ref(null);
const authStore = useAuthStore();
authStore.initUser();
const isAdmin = computed(() => authStore.isAdmin);

const settings = reactive({
  model: localStorage.getItem(AI_MODEL_STORAGE_KEY) || "qwen3:8b",
});

// Watchers — 用 messages.length 浅监听替代 deep:true，避免大量消息时深度遍历
watch(
  () => messages.value.length,
  () => {
    nextTick(() => scrollToBottom());
  },
);
// 流式响应时也触发滚动
watch(currentResponse, () => {
  nextTick(() => scrollToBottom());
});
watch(
  uploadedFiles,
  (list) => {
    try {
      const plain = list.map((file) => ({
        id: file.id,
        name: file.name,
        type: file.type,
        parsed: !!file.parsed,
        parsedContent: file.parsedContent || file.parsed_content || null,
        error: !!file.error,
        parsingThinkingSteps: file.parsingThinkingSteps || [],
      }));
      localStorage.setItem(UPLOADED_FILES_STORAGE_KEY, JSON.stringify(plain));
    } catch (e) {
      console.error("保存上传文件状态失败:", e);
    }
  },
  { deep: true },
);
watch(
  () => settings.model,
  (model) => {
    localStorage.setItem(AI_MODEL_STORAGE_KEY, model || "qwen3:8b");
  },
);

// Computed
const conversationsItems = computed(() =>
  (Array.isArray(chatSessions.value) ? chatSessions.value : []).map(
    (session) => {
      const time = session.updatedAt || session.createdAt || Date.now();
      return {
        key: String(session.id),
        timestamp: typeof time === "number" ? time : undefined,
        label: session.title || "新对话",
      };
    },
  ),
);
const activeConversationKey = computed(() =>
  currentSessionId.value === null || currentSessionId.value === undefined
    ? undefined
    : String(currentSessionId.value),
);
const hasSendableContent = computed(
  () =>
    !!inputMessage.value.trim() ||
    (uploadedFiles.value.length > 0 && isAttachmentsReady.value),
);
const isSendDisabled = computed(
  () =>
    isLoading.value || !hasSendableContent.value || !isAttachmentsReady.value,
);

// Methods
const conversationMenu = (conversation) => ({
  items: [
    { key: "rename", label: "重命名" },
    { key: "delete", label: "删除" },
  ],
  onClick: ({ key, domEvent }) => {
    if (key === "delete") {
      deleteSession(Number(conversation.key), domEvent);
    } else if (key === "rename") {
      const session = chatSessions.value.find(
        (s) => String(s.id) === conversation.key,
      );
      if (session) {
        renameDialogSessionKey.value = conversation.key;
        renameDialogTitle.value = session.title || "新对话";
        showRenameDialog.value = true;
      }
    }
  },
});

const onPromptsItemClick = (info) => {
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
  if (typeof desc === "string" && desc.trim()) onSenderSubmit(desc.trim());
};

const onSenderSubmit = (nextContent) => {
  if (typeof nextContent === "string") inputMessage.value = nextContent;
  sendMessage();
};
const onSenderChange = (value) => {
  inputMessage.value = value || "";
};

const renderSenderActions = (_ori, { components }) => {
  if (isLoading.value) return h(components.LoadingButton);
  return h(components.SendButton, { disabled: isSendDisabled.value });
};

const sendMessage = async () => {
  if (isLoading.value) return;
  if (!isAttachmentsReady.value) {
    ElMessage.warning(
      isAttachmentsParsing.value
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
  const displayContent = buildDisplayContent(templateId, hasText, hasAttachments, messageContent);
  const attachments = hasAttachments ? [...uploadedFiles.value] : null;

  messages.value.push({
    role: "user",
    content: displayContent,
    fullContent: messageContent,
    timestamp: new Date(),
    attachments,
    templateId: templateId != null ? Number(templateId) : null,
  });
  inputMessage.value = "";
  uploadedFiles.value = [];
  attachmentsOpen.value = false;
  attachmentItems.value = [];

  const documentId =
    attachments && attachments.length > 0 ? attachments[0]?.id || null : null;
  await generateAIResponse(
    messageContent,
    attachments,
    templateId != null
      ? { templateId: Number(templateId), documentId }
      : { documentId },
  );
  clearTemplateSelection();
};

const generateAIResponse = async (message, attachments, options = {}) => {
  const { templateId = null, documentId = null } = options;
  currentResponse.value = "";

  try {
    const isIPC = isIPCTemplate(templateId);
    const strict = isStrictTemplate(templateId);

    let userMessage = message;
    if (attachments && attachments.length > 0) {
      attachments.forEach((file) => {
        userMessage += `\n文档：${file.name} (${file.type})\n`;
        const parsedContent = file.parsedContent || file.parsed_content;
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

    const body = {
      messages: strict
        ? [...contextMessages, { role: "user", content: userMessage }]
        : [
            ...contextMessages,
            { role: "user", content: userMessage },
          ],
      stream: true,
      model: settings.model || "qwen3:8b",
      passthrough: false,
    };
    if (strict) body.template_id = Number(templateId);
    if (currentBackendSessionId.value)
      body.session_id = currentBackendSessionId.value;
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
  } catch (error) {
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
};

const createNewSessionAndHideSidebar = () => {
  createSession();
  inputMessage.value = "";
  uploadedFiles.value = [];
  attachmentItems.value = [];
  showSidebar.value = false;
};
const onConversationActiveChange = async (key) => {
  if (key) {
    await switchSession(Number(key));
    showSidebar.value = false;
  }
};
const scrollToBottom = () => {
  nextTick(() => {
    const el = bubbleListRef.value;
    if (el) el.scrollTop = el.scrollHeight;
  });
};
const handleCopy = async (_content, content) => {
  const text = (content || "").trim();
  if (!text) {
    ElMessage.warning("没有可复制的内容");
    return;
  }
  await copy(text);
};
const handlePreview = (file) => {
  const content = file.parsedContent || file.parsed_content;
  if (!content) {
    ElMessage.warning("文档解析内容为空");
    return;
  }
  // 优先显示 text 内容
  if (content.text) {
    previewContent.value = content.text;
  }
  // 否则显示 structured 中的非空字段
  else if (content.structured) {
    const { structured } = content;
    const parts = [];
    if (structured.title?.trim()) parts.push(`【标题】\n${structured.title}`);
    if (structured.abstract?.trim())
      parts.push(`【摘要】\n${structured.abstract}`);
    if (structured.claims?.length > 0) {
      const claimsText = structured.claims
        .map((c) => `${c.number}. ${c.content}`)
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
  }
  // 兜底显示 JSON
  else if (typeof content === "string") {
    previewContent.value = content;
  } else {
    previewContent.value = "文档解析内容为空，请重新上传或检查文档格式。";
  }
  previewTitle.value = file.name;
  previewDialogVisible.value = true;
};
const confirmRename = async () => {
  if (renameDialogSessionKey.value && renameDialogTitle.value.trim()) {
    await renameSession(Number(renameDialogSessionKey.value), renameDialogTitle.value.trim());
  }
  showRenameDialog.value = false;
};

const regenerateResponse = async (index) => {
  const prev = messages.value[index - 1];
  if (typeof (prev?.fullContent || prev?.content) === "string") {
    messages.value.splice(index);
    await generateAIResponse(
      prev.fullContent || prev.content,
      prev.attachments,
      { templateId: prev.templateId },
    );
  }
};

// Mounted
onMounted(async () => {
  inputMessage.value = "";
  clearTemplateSelection();
  await loadSessions();
  loadUploadedFiles();
  document.addEventListener("click", stopLoadingClickHandler, true);
});

const stopLoadingClickHandler = (e) => {
  if (e.target && isLoading.value && currentController.value) {
    const el = e.target.closest?.(
      ".ant-sender-actions-btn-loading-icon, .ant-sender-send-button, .send-btn",
    );
    if (el) {
      abort();
      isLoading.value = false;
    }
  }
};
</script>

<style scoped>
.patent-chat {
  min-height: 100vh;
  background: var(--bg-secondary);
  font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
}

.chat-layout {
  display: flex;
  height: 100vh;
}

.sidebar-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* 侧边栏背景遮罩 */
.sidebar-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.3);
  backdrop-filter: blur(2px);
  z-index: 1000;
}

/* 侧边栏 */
.session-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: 280px;
  height: 100vh;
  background: var(--bg-primary);
  border-right: 1px solid var(--border-color);
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 1001;
}

.sidebar-header {
  padding: 12px;
  border-bottom: 1px solid var(--border-light);
  display: flex;
  align-items: center;
}
.sidebar-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
}
.sidebar-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}
.sidebar-add-btn {
  color: var(--primary-color);
  font-weight: 500;
  font-size: 13px;
}
.sidebar-add-btn:hover {
  background: rgba(37, 99, 235, 0.04);
}
.empty-sessions {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px;
  color: var(--text-muted);
}
.empty-sessions p {
  margin-top: 12px;
  font-size: 13px;
}

.chat-main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}
.chat-top-bar {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 24px;
  max-width: 100%;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-light);
}
.chat-top-bar-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}
.chat-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.chat-logo-dot {
  width: 24px;
  height: 24px;
  border-radius: 6px;
}
.chat-brand-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0;
}

.chat-content-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  position: relative;
  background: var(--bg-secondary);
}
.ax-placeholder {
  max-width: 640px;
  margin: 0 auto;
  padding: 32px 20px 0;
  width: 100%;
}
.ax-prompts {
  max-width: 640px;
  margin: 16px auto 0;
  padding: 0 20px;
}

.ax-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px 0;
  scroll-behavior: smooth;
}
.messages-wrapper {
  max-width: 640px;
  margin: 0 auto;
  padding: 0 20px;
}
.message-item-wrapper {
  margin-bottom: 12px;
}
.streaming-message {
  max-width: 640px;
  margin: 0 auto;
  padding: 0 20px;
  margin-bottom: 12px;
}

.page-disclaimer {
  text-align: center;
  font-size: 11px;
  color: var(--text-muted);
  padding: 6px 0;
}

.ax-sender {
  width: calc(100% - 32px);
  max-width: 640px;
  margin: 0 auto;
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border-color);
  flex-shrink: 0;
  margin-bottom: 8px;
}

.ax-attachments-inline {
  padding: 20px;
  text-align: center;
}

@keyframes messageIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.message-list-enter-active {
  transition: all 0.2s ease;
}
.message-list-leave-active {
  transition: all 0.15s ease;
}
.message-list-enter-from {
  opacity: 0;
  transform: translateY(12px);
}
.message-list-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}

/* 覆盖 Conversations 组件默认样式 */
.ax-conversations {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.ax-conversations :deep(.ax-conversations-item) {
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  margin-bottom: 2px;
  transition: background 0.15s ease;
  cursor: pointer;
}

.ax-conversations :deep(.ax-conversations-item:hover) {
  background: var(--bg-tertiary);
}

.ax-conversations :deep(.ax-conversations-item.active) {
  background: rgba(37, 99, 235, 0.08);
}

.ax-conversations :deep(.ax-conversations-item-title) {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ax-conversations
  :deep(.ax-conversations-item.active .ax-conversations-item-title) {
  color: var(--primary-color);
  font-weight: 600;
}

.ax-conversations :deep(.ax-conversations-item-meta) {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
}

.ax-conversations
  :deep(.ax-conversations-item.active .ax-conversations-item-meta) {
  color: var(--text-secondary);
}

.ax-conversations :deep(.ax-conversations-menu) {
  border-radius: var(--radius-sm);
}

.ax-conversations :deep(.ax-conversations-menu-item) {
  font-size: 13px;
  padding: 6px 12px;
}

/* 滑入滑出动画 */
.slide-enter-active {
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-leave-active {
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(-100%);
}

/* 淡入淡出动画 */
.fade-enter-active {
  transition: opacity 0.2s ease;
}

.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .session-sidebar {
    width: 280px;
  }
  .chat-layout {
    flex-direction: column;
  }
  .chat-top-bar {
    padding: 0 16px;
  }
  .chat-top-bar-left {
    gap: 10px;
  }
}
</style>
