<template>
  <div class="patent-chat">
    <!-- 侧边栏背景遮罩 -->
    <Transition name="fade">
      <div v-if="showSidebar" class="sidebar-backdrop" @click="showSidebar = false" />
    </Transition>

    <!-- 聊天记录侧边栏 -->
    <Transition name="slide">
      <SessionSidebar
        v-if="showSidebar"
        :items="conversationsItems"
        :active-key="activeConversationKey"
        :menu="conversationMenu"
        @close="showSidebar = false"
        @add-session="createNewSessionAndHideSidebar"
        @active-change="onConversationActiveChange"
      />
    </Transition>

    <div class="chat-layout">
      <!-- 主聊天区域 -->
      <div class="chat-main-area">
        <ChatTopBar
          :show-sidebar="showSidebar"
          :is-admin="isAdmin"
          @toggle-sidebar="showSidebar = !showSidebar"
          @go-admin="$router.push('/admin/users')"
        />

        <div class="chat-content-wrapper">
          <!-- 空状态欢迎页 -->
          <WelcomePlaceholder
            v-if="messages.length === 0 && !isLoading"
            :items="placeholderPromptsItems"
            :styles="placeholderPromptsStyles"
            @item-click="onPromptsItemClick"
          />

          <!-- 消息列表 -->
          <MessageList
            ref="messageListRef"
            :messages="messages"
            :is-loading="isLoading"
            :streaming-answer="currentAnswer"
            :streaming-thinking="currentThinking"
            @toggle-thinking="toggleThinking"
            @toggle-streaming-thinking="toggleStreamingThinking"
            @copy="handleCopy"
            @regenerate="regenerateResponse"
            @preview="handlePreview"
          />
        </div>

        <!-- 输入框区域 -->
        <ChatSender
          v-model="inputMessage"
          :loading="isLoading"
          :uploaded-files="uploadedFiles"
          :attachment-items="attachmentItems"
          @submit="onSenderSubmit"
          @update:model-value="(v) => (inputMessage = v)"
          @attachments-change="handleAttachmentsChange"
          @attachment-remove="handleAttachmentRemove"
          @attachment-custom-request="handleAttachmentCustomRequest"
        />

        <div class="page-disclaimer">内容由 AI 生成，请仔细甄别</div>

        <!-- 设置对话框 -->
        <SettingsDialog
          v-model="showSettings"
          :settings="settings"
        />

        <!-- 重命名会话对话框 -->
        <RenameDialog
          v-model="showRenameDialog"
          :title="renameDialogTitle"
          @confirm="confirmRename"
        />

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
import { ref, reactive, watch, onMounted, onUnmounted, computed } from "vue";
import { useAuthStore } from "@/stores/auth";
import { useThinking } from "@/composables/useThinking";
import { useChatSession } from "@/composables/useChatSession";
import { useFileUpload } from "@/composables/useFileUpload";
import { useSSEStream } from "@/composables/useSSEStream";
import { useTemplateSelector } from "@/composables/useTemplateSelector";
import { useChatView } from "@/composables/useChatView";
import ChatTopBar from "@/components/chat/ChatTopBar.vue";
import SessionSidebar from "@/components/chat/SessionSidebar.vue";
import MessageList from "@/components/chat/MessageList.vue";
import WelcomePlaceholder from "@/components/chat/WelcomePlaceholder.vue";
import ChatSender from "@/components/chat/ChatSender.vue";
import SettingsDialog from "@/components/chat/SettingsDialog.vue";
import RenameDialog from "@/components/chat/RenameDialog.vue";
import ContentPreviewDialog from "@/components/common/ContentPreviewDialog.vue";

const AI_MODEL_STORAGE_KEY = "patent_ai_model";

// Auth store
const authStore = useAuthStore();
authStore.initUser();
const isAdmin = computed(() => authStore.isAdmin);

// 子组件 ref
const messageListRef = ref<InstanceType<typeof MessageList> | null>(null);

// Composables
const {
  toggleThinking,
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
  switchSession,
  refreshSessions,
} = useChatSession();

const {
  uploadedFiles,
  attachmentItems,
  handleAttachmentCustomRequest,
  handleAttachmentRemove,
  handleAttachmentsChange,
  loadUploadedFiles,
} = useFileUpload();

const {
  currentThinking,
  currentAnswer,
  isLoading,
  startStream,
  abort,
  reset: resetStream,
  normalizeAiErrorMessage,
} = useSSEStream();

const {
  activeTemplateId,
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

// 本地状态
const showSidebar = ref(false);
const inputMessage = ref("");
const showSettings = ref(false);
const settings = reactive({
  model: localStorage.getItem(AI_MODEL_STORAGE_KEY) || "qwen3:8b",
});

// useChatView — 抽离核心业务逻辑
const {
  previewDialogVisible,
  previewTitle,
  previewContent,
  showRenameDialog,
  renameDialogTitle,
  conversationsItems,
  activeConversationKey,
  conversationMenu,
  onPromptsItemClick,
  onSenderSubmit,
  sendMessage,
  generateAIResponse,
  regenerateResponse,
  handleCopy,
  handlePreview,
  confirmRename,
  createNewSessionAndHideSidebar,
  onConversationActiveChange,
  setup: setupChatView,
  cleanup: cleanupChatView,
} = useChatView({
  messages,
  uploadedFiles,
  attachmentItems,
  inputMessage,
  currentBackendSessionId: ref(null),
  model: computed(() => settings.model),
  isLoading,
  currentAnswer,
  currentThinking,
  currentController: ref(null),
  streamingThinkingExpanded,
  startStream,
  abort,
  resetStream,
  normalizeAiErrorMessage,
  sessions: chatSessions,
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
  scrollToBottom: () => messageListRef.value?.scrollToBottom(),
});

// Watchers
watch(
  () => settings.model,
  (model) => {
    localStorage.setItem(AI_MODEL_STORAGE_KEY, model || "qwen3:8b");
  },
);

// Life cycle
onMounted(async () => {
  inputMessage.value = "";
  clearTemplateSelection();
  await loadSessions();
  loadUploadedFiles();
  setupChatView();
});

onUnmounted(() => {
  cleanupChatView();
});
</script>

<style scoped>
.patent-chat {
  min-height: 100vh;
  background: var(--bg-secondary);
  font-family: var(--font-body);
}

.chat-layout {
  display: flex;
  height: 100vh;
}

.chat-main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
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

.page-disclaimer {
  text-align: center;
  font-size: 11px;
  color: var(--text-muted);
  padding: 8px 0;
  font-family: var(--font-body);
  letter-spacing: 0.3px;
}

/* 侧边栏背景遮罩 */
.sidebar-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(44, 36, 32, 0.2);
  backdrop-filter: blur(3px);
  z-index: 1000;
}

/* 滑入滑出动画 */
.slide-enter-active {
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-leave-active {
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(-100%);
}

/* 淡入淡出动画 */
.fade-enter-active {
  transition: opacity 0.25s ease;
}

.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .chat-layout {
    flex-direction: column;
  }
}
</style>