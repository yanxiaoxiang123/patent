<template>
  <div class="patent-chat">
    <!-- 侧边栏切换按钮 -->
    <div v-if="!showSidebar" class="sidebar-toggle">
      <el-tooltip content="显示聊天记录" placement="right">
        <el-button type="default" size="small" circle @click="showSidebar = true">
          <el-icon><Files /></el-icon>
        </el-button>
      </el-tooltip>
    </div>

    <div class="chat-layout">
      <!-- 聊天记录侧边栏 -->
      <div v-show="showSidebar" class="session-sidebar ax-menu">
        <div class="sidebar-header">
          <div class="sidebar-actions">
            <div class="sidebar-title">聊天记录</div>
            <Button type="text" size="small" class="sidebar-close-btn" @click="showSidebar = false">
              <template #icon>
                <CloseOutlined />
              </template>
            </Button>
          </div>
        </div>

        <Button type="link" class="sidebar-add-btn" @click="createNewSessionAndHideSidebar">
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

      <!-- 主聊天区域 -->
      <div class="chat-main-area">
        <div class="chat-top-bar">
          <div class="chat-brand">
            <img class="chat-logo-dot" src="/0.png" alt="" />
            <div class="chat-brand-text">
              <div class="chat-brand-title">专利 AI 助手</div>
            </div>
          </div>
          <div class="chat-actions">
            <el-button v-if="isAdmin" type="default" size="small" @click="$router.push('/admin/users')">
              用户管理
            </el-button>
          </div>
        </div>

        <div class="chat-content-wrapper">
          <!-- 空状态欢迎页 -->
          <div v-if="messages.length === 0 && !isLoading" class="ax-placeholder">
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
            <TransitionGroup name="message-list" tag="div" class="messages-wrapper">
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
                  :thinking-expanded="message.thinkingExpanded ?? isThinkingVisible(index)"
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
            <div v-if="isLoading" class="streaming-message message-item-wrapper">
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
                  <Flex v-if="type && type.type === 'inline'" align="center" justify="center" vertical gap="2" class="ax-attachments-inline">
                    <Typography.Text style="font-size: 30px; line: 1">
                      <CloudUploadOutlined />
                    </Typography.Text>
                    <Typography.Title :level="5" style="margin: 0; font-size: 14px; line: 1.5">
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

        <!-- 预览对话框 -->
        <el-dialog v-model="previewDialogVisible" :title="previewTitle" width="600px">
          <div class="preview-content">
            <pre>{{ previewContent }}</pre>
          </div>
          <template #footer>
            <el-button @click="previewDialogVisible = false">关闭</el-button>
          </template>
        </el-dialog>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, h, nextTick, watch, onMounted, computed } from "vue";
import { ElMessage } from "element-plus";
import { Files } from "@element-plus/icons-vue";
import { Badge, Button, Flex, Typography } from "ant-design-vue";
import { CloudUploadOutlined, CloseOutlined, PaperClipOutlined, PlusOutlined } from "@ant-design/icons-vue";
import { Attachments, Conversations, Prompts, Sender, Welcome } from "ant-design-x-vue";
import { useAuthStore } from "@/stores/auth";
import { useThinking } from "@/composables/useThinking";
import { useChatSession } from "@/composables/useChatSession";
import { useFileUpload } from "@/composables/useFileUpload";
import { useClipboard } from "@/composables/useCopyToClipboard";
import MessageBubble from "@/components/message-bubble/index.vue";

const UPLOADED_FILES_STORAGE_KEY = "patent_uploaded_files";

// Composables
const { toggleThinking, isThinkingVisible, streamingThinkingExpanded, toggleStreamingThinking } = useThinking();
const { sessions: chatSessions, currentSessionId, messages, loadSessions, createSession, deleteSession, refreshSessions, switchSession } = useChatSession();
const { uploadedFiles, attachmentItems, isAttachmentsReady, isAttachmentsParsing, handleAttachmentCustomRequest, handleAttachmentRemove, handleAttachmentsChange, loadUploadedFiles } = useFileUpload();
const { copy } = useClipboard();

// State
const showSidebar = ref(false);
const inputMessage = ref("");
const isLoading = ref(false);
const currentResponse = ref("");
const currentThinking = ref("");
const currentAnswer = ref("");
const currentController = ref(null);
const attachmentsOpen = ref(false);
const showSettings = ref(false);
const previewDialogVisible = ref(false);
const previewTitle = ref("");
const previewContent = ref("");
const currentTemplateId = ref(null);
const bubbleListRef = ref(null);
const currentBackendSessionId = ref(null);
const authStore = useAuthStore();
authStore.initUser();
const isAdmin = computed(() => authStore.isAdmin);

// Templates
const patentTemplates = ref([
  { id: 1, title: "普通案例审核", icon: "Document", description: "对上传的普通案例进行审核并给出建议", prompt: "" },
  { id: 3, title: "专案案例审核", icon: "EditPen", description: "对上传的专案案例进行审核并输出报告", prompt: "" },
  { id: 2, title: "专利审核指导", icon: "EditPen", description: "学习专利申请文件的审核技巧", prompt: "根据我刚刚上传的文件，帮我进行专利审核" },
  { id: 5, title: "IPC 分类指导", icon: "Shield", description: "根据技术方案选择合适的专利 IPC 分类号", prompt: "我有一个专利申请书，请帮我分析应该归入哪些 IPC 分类号，并说明每个分类号的含义和选择理由。" },
]);

const settings = reactive({ model: "qwen3:8b" });

// Watchers
watch(messages, () => { nextTick(() => scrollToBottom()); }, { deep: true });
watch(currentResponse, () => { nextTick(() => scrollToBottom()); });
watch(uploadedFiles, (list) => {
  try {
    const plain = list.map((file) => ({ id: file.id, name: file.name, type: file.type, parsed: !!file.parsed, parsedContent: file.parsedContent || file.parsed_content || null, error: !!file.error, parsingThinkingSteps: file.parsingThinkingSteps || [] }));
    localStorage.setItem(UPLOADED_FILES_STORAGE_KEY, JSON.stringify(plain));
  } catch (e) { console.error("保存上传文件状态失败:", e); }
}, { deep: true });

// Computed
const primaryTemplates = computed(() => (Array.isArray(patentTemplates.value) ? patentTemplates.value : []).slice(0, 3));
const secondaryTemplates = computed(() => (Array.isArray(patentTemplates.value) ? patentTemplates.value : []).slice(3));
const placeholderPromptsItems = computed(() => [...primaryTemplates.value, ...secondaryTemplates.value].map((t) => ({ key: String(t.id), label: t.title, description: t.description || "" })));
const placeholderPromptsStyles = { list: { width: "100%" }, item: { flex: 1 } };
const conversationsItems = computed(() => (Array.isArray(chatSessions.value) ? chatSessions.value : []).map((session) => {
  const time = session.updatedAt || session.createdAt || Date.now();
  return { key: String(session.id), timestamp: typeof time === "number" ? time : undefined, label: session.title || "新对话" };
}));
const activeConversationKey = computed(() => currentSessionId.value === null || currentSessionId.value === undefined ? undefined : String(currentSessionId.value));
const hasSendableContent = computed(() => !!inputMessage.value.trim() || (uploadedFiles.value.length > 0 && isAttachmentsReady.value));
const isSendDisabled = computed(() => isLoading.value || !hasSendableContent.value || !isAttachmentsReady.value);

// Methods
const conversationMenu = (conversation) => ({
  items: [{ key: "delete", label: "删除" }],
  onClick: ({ key, domEvent }) => { if (key === "delete") deleteSession(Number(conversation.key), domEvent); },
});

const onPromptsItemClick = (info) => {
  const key = info?.data?.key;
  const template = (patentTemplates.value || []).find((t) => String(t.id) === String(key));
  if (template) { currentTemplateId.value = Number(template.id); inputMessage.value = template.id === 1 || template.id === 3 ? "" : template.prompt || ""; sendMessage(); return; }
  const desc = info?.data?.description;
  if (typeof desc === "string" && desc.trim()) onSenderSubmit(desc.trim());
};

const onSenderSubmit = (nextContent) => { if (typeof nextContent === "string") inputMessage.value = nextContent; sendMessage(); };
const onSenderChange = (value) => { inputMessage.value = value || ""; };

const renderSenderActions = (_ori, { components }) => {
  if (isLoading.value) return h(components.LoadingButton);
  return h(components.SendButton, { disabled: isSendDisabled.value });
};

const sendMessage = async () => {
  if (isLoading.value) return;
  if (!isAttachmentsReady.value) { ElMessage.warning(isAttachmentsParsing.value ? "文件解析中，请等待解析完成后再发送" : "存在解析失败的文件，请移除后再发送"); return; }
  const trimmed = inputMessage.value.trim();
  const hasText = !!trimmed;
  const hasAttachments = uploadedFiles.value.length > 0;
  if (!hasText && !hasAttachments) return;

  const isIPC = Number(currentTemplateId.value) === 5;
  const isStrictAudit = Number(currentTemplateId.value) === 1 || Number(currentTemplateId.value) === 3;
  const isPureAttachment = !hasText && hasAttachments;

  const messageContent = hasText ? trimmed : isIPC ? "请根据我上传的专利文档内容，帮我进行 IPC 分类，并说明每个分类号的含义和选择理由。" : isStrictAudit ? "" : "请根据我刚刚上传的专利文档，先给出整体概览、关键创新点和主要风险点的审核意见。";
  const displayContent = isPureAttachment && isStrictAudit ? "（已上传文档，按模板审核）" : messageContent;
  const attachments = hasAttachments ? [...uploadedFiles.value] : null;

  messages.value.push({ role: "user", content: displayContent, fullContent: messageContent, timestamp: new Date(), attachments, templateId: currentTemplateId.value != null ? Number(currentTemplateId.value) : null });
  inputMessage.value = "";
  uploadedFiles.value = [];
  attachmentsOpen.value = false;
  attachmentItems.value = [];

  // 获取第一个附件的 document_id
  const documentId = attachments && attachments.length > 0 ? (attachments[0]?.id || null) : null;
  await generateAIResponse(messageContent, attachments, currentTemplateId.value != null ? { templateId: Number(currentTemplateId.value), documentId } : isPureAttachment ? { forceAudit: true, documentId } : { documentId });
  currentTemplateId.value = null;
};

const generateAIResponse = async (message, attachments, options = {}) => {
  isLoading.value = true;
  currentResponse.value = "";
  const { templateId = null, documentId = null } = options;

  try {
    const isIPC = Number(templateId) === 5;
    const isStrictTemplate = Number(templateId) === 1 || Number(templateId) === 3;

    let userMessage = message;
    if (attachments && attachments.length > 0) {
      attachments.forEach((file) => {
        userMessage += `\n文档：${file.name} (${file.type})\n`;
        const parsedContent = file.parsedContent || file.parsed_content;
        if (isIPC && parsedContent?.first_page_content) {
          userMessage += `文档第一页内容：\n${parsedContent.first_page_content.slice(0, 6000)}...\n`;
        } else if (parsedContent?.structured) {
          if (parsedContent.structured.title) userMessage += `标题：${parsedContent.structured.title}\n`;
          if (parsedContent.structured.abstract) userMessage += `摘要：${parsedContent.structured.abstract}\n`;
        }
      });
    }

    const contextMessages = isIPC || isStrictTemplate ? [] : messages.value.filter((m) => m.role === "user" || m.role === "assistant").slice(-12).map((m) => {
      const content = m.content || "";
      return { role: m.role, content };
    });

    const apiUrl = "/api/ai/chat";
    const headers = { "Content-Type": "application/json", Accept: "text/event-stream, application/json;q=0.9, */*;q=0.8", "Cache-Control": "no-cache" };
    const token = localStorage.getItem("token");
    if (token) headers.Authorization = `Bearer ${token}`;

    const body = {
      messages: isStrictTemplate ? [...contextMessages, { role: "user", content: userMessage }] : [{ role: "system", content: "你是一个专业的专利审核助手" }, ...contextMessages, { role: "user", content: userMessage }],
      stream: true,
      model: "qwen3:8b",
      passthrough: false,
    };
    if (isStrictTemplate) body.template_id = Number(templateId);
    if (currentBackendSessionId.value) body.session_id = currentBackendSessionId.value;
    if (documentId) body.document_id = documentId;

    const controller = new AbortController();
    currentController.value = controller;
    const response = await fetch(apiUrl, { method: "POST", headers, body: JSON.stringify(body), signal: controller.signal });

    if (!response.ok) throw new Error(`AI 服务响应失败: ${response.status}`);

    if (response.body) {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let currentEvent = "message";
      let currentData = "";
      currentThinking.value = "";
      currentAnswer.value = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        // 处理 SSE 格式：多行组成一个事件
        while (buffer.includes("\n")) {
          const newlineIndex = buffer.indexOf("\n");
          const line = buffer.substring(0, newlineIndex);
          buffer = buffer.substring(newlineIndex + 1);

          // 空行表示事件结束
          if (line.trim() === "") {
            if (currentData === "[DONE]") break;

            if (currentData) {
              try {
                const parsed = JSON.parse(currentData);
                if (parsed?.choices?.[0]?.delta) {
                  const delta = parsed.choices[0].delta;
                  if (delta.thinking) currentThinking.value += delta.thinking;
                  if (delta.content) currentAnswer.value += delta.content;
                }
              } catch {}
            }
            currentEvent = "message";
            currentData = "";
            continue;
          }

          // 解析 SSE 行
          if (line.startsWith("event:")) {
            currentEvent = line.slice(6).trim();
          } else if (line.startsWith("data:")) {
            currentData = line.slice(5);
          }
        }
      }
    }

    // 组装完整响应
    currentResponse.value = currentThinking.value + "\n\n" + currentAnswer.value;

    messages.value.push({
      role: "assistant",
      content: currentAnswer.value || "抱歉，没有收到有效的响应。",
      thinking: currentThinking.value,
      timestamp: new Date(),
      thinkingExpanded: streamingThinkingExpanded,
    });
    nextTick(() => scrollToBottom());
    await refreshSessions();
  } catch (error) {
    console.error("生成 AI 响应失败:", error);
    if (error?.name === "AbortError") {
      if ((currentAnswer.value || "").trim().length > 0) messages.value.push({
        role: "assistant",
        content: currentAnswer.value,
        thinking: currentThinking.value,
        timestamp: new Date(),
        thinkingExpanded: streamingThinkingExpanded,
      });
    } else {
      ElMessage.error("AI 响应失败，请稍后重试");
      messages.value.push({ role: "assistant", content: "抱歉，我暂时无法回答您的问题。请稍后重试或联系技术支持。", timestamp: new Date() });
    }
  } finally {
    isLoading.value = false;
    currentResponse.value = "";
    currentThinking.value = "";
    currentAnswer.value = "";
    currentController.value = null;
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
  if (!text) { ElMessage.warning("没有可复制的内容"); return; }
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
    if (structured.abstract?.trim()) parts.push(`【摘要】\n${structured.abstract}`);
    if (structured.claims?.length > 0) {
      const claimsText = structured.claims.map((c) => `${c.number}. ${c.content}`).join('\n\n');
      parts.push(`【权利要求】\n${claimsText}`);
    }
    if (structured.description?.trim()) parts.push(`【说明书正文】\n${structured.description}`);
    if (parts.length > 0) {
      previewContent.value = parts.join('\n\n');
    } else {
      previewContent.value = "文档解析内容为空，请重新上传或检查文档格式。";
    }
  }
  // 兜底显示 JSON
  else if (typeof content === 'string') {
    previewContent.value = content;
  } else {
    previewContent.value = "文档解析内容为空，请重新上传或检查文档格式。";
  }
  previewTitle.value = file.name;
  previewDialogVisible.value = true;
};
const regenerateResponse = async (index) => {
  const prev = messages.value[index - 1];
  if (typeof (prev?.fullContent || prev?.content) === "string") {
    messages.value.splice(index);
    await generateAIResponse(prev.fullContent || prev.content, prev.attachments, { templateId: prev.templateId });
  }
};

// Mounted
onMounted(async () => {
  inputMessage.value = "";
  currentTemplateId.value = null;
  await loadSessions();
  loadUploadedFiles();
  document.addEventListener("click", stopLoadingClickHandler, true);
});

const stopLoadingClickHandler = (e) => {
  if (e.target && isLoading.value && currentController.value) {
    const el = e.target.closest?.(".ant-sender-actions-btn-loading-icon, .ant-sender-send-button, .send-btn");
    if (el) { currentController.value.abort(); currentController.value = null; isLoading.value = false; }
  }
};
</script>

<style scoped>
.patent-chat {
  min-height: 100vh;
  background: radial-gradient(circle at top, #ffffff 0, #f5f5f7 55%, #e5e7eb 100%);
  font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
}

.chat-layout { display: flex; height: 100vh; }

.sidebar-toggle {
  position: fixed; top: 20px; left: 20px; z-index: 1001;
  background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(10px);
  border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 12px;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.1);
}

.session-sidebar {
  width: 260px; background: rgba(255, 255, 255, 0.9); border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.3); padding: 12px;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12); margin: 80px 16px 40px 20px;
}

.sidebar-header { padding: 16px 16px 12px; border-bottom: 1px solid rgba(148, 163, 184, 0.15); }
.sidebar-title { font-size: 15px; font-weight: 600; color: #374151; }
.sidebar-actions { display: flex; justify-content: space-between; align-items: center; }
.sidebar-add-btn { width: calc(100% - 24px); margin: 0 12px 16px; background: rgba(22, 119, 255, 0.06); border: 1px solid rgba(22, 119, 255, 0.2); }
.empty-sessions { display: flex; flex-direction: column; align-items: center; padding: 32px; color: #9ca3af; }
.empty-sessions p { margin-top: 12px; font-size: 14px; }

.chat-main-area { flex: 1; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
.chat-top-bar { height: 68px; display: flex; align-items: center; justify-content: space-between; padding: 16px 32px 8px; max-width: 1120px; margin: 0 auto; }
.chat-brand { display: flex; align-items: center; gap: 12px; }
.chat-logo-dot { width: 26px; height: 26px; border-radius: 999px; }
.chat-brand-title { font-size: 18px; font-weight: 600; letter-spacing: 0.06em; color: #111827; }

.chat-content-wrapper { flex: 1; display: flex; flex-direction: column; min-height: 0; overflow: hidden; position: relative; }
.ax-placeholder { max-width: 720px; margin: 0 auto; padding: 24px 20px 0; width: 100%; }
.ax-prompts { max-width: 720px; margin: 12px auto 0; padding: 0 20px; }

.ax-messages { flex: 1; overflow-y: auto; padding: 24px 0 24px; scroll-behavior: smooth; }
.messages-wrapper { max-width: 720px; margin: 0 auto; padding: 0 20px; }
.message-item-wrapper { margin-bottom: 16px; }
.streaming-message { max-width: 720px; margin: 0 auto; padding: 0 20px; margin-bottom: 16px; }

.page-disclaimer { text-align: center; font-size: 12px; color: #9ca3af; padding: 8px 0; }

.ax-sender { width: calc(100% - 40px); max-width: 720px; margin: 0 auto; background: rgba(249, 250, 251, 0.98); border-radius: 12px; box-shadow: 0 2px 16px rgba(0, 0, 0, 0.08); border: 1px solid rgba(0, 0, 0, 0.06); flex-shrink: 0; }

.ax-attachments-inline { padding: 24px; text-align: center; }

@keyframes messageIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.message-list-enter-active { transition: all 0.3s ease; }
.message-list-leave-active { transition: all 0.2s ease; }
.message-list-enter-from { opacity: 0; transform: translateY(20px); }
.message-list-leave-to { opacity: 0; transform: translateY(-20px); }

@media (max-width: 768px) {
  .session-sidebar { width: calc(100% - 32px); height: 50vh; max-height: 400px; position: fixed; left: 16px; top: 60px; border-radius: 12px; }
  .chat-layout { flex-direction: column; }
  .sidebar-toggle { top: 16px; left: 12px; }
}
</style>
