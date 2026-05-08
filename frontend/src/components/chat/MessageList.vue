<template>
  <div ref="listRef" class="ax-messages">
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
          @preview="emit('preview', $event)"
        />

        <!-- AI 消息 -->
        <MessageBubble
          v-else
          role="ai"
          :content="message.content"
          :timestamp="message.timestamp"
          :thinking-content="message.thinking"
          :thinking-expanded="message.thinkingExpanded ?? false"
          :show-actions="true"
          :attachments="message.attachments"
          @toggle-thinking="emit('toggle-thinking', index)"
          @copy="emit('copy', $event, message.content)"
          @regenerate="emit('regenerate', index)"
          @preview="emit('preview', $event)"
        />
      </div>
    </TransitionGroup>

    <!-- 流式响应 -->
    <div v-if="isLoading" class="streaming-message message-item-wrapper">
      <MessageBubble
        role="ai"
        :content="streamingAnswer"
        :is-streaming="true"
        :thinking-content="streamingThinking"
        @toggle-thinking="emit('toggle-streaming-thinking')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import MessageBubble from "@/components/message-bubble/index.vue";
import { useChatScroll } from "@/composables/useChatScroll";
import type { ChatMessage, FileAttachment } from "@/types";

interface Props {
  messages: ChatMessage[];
  isLoading: boolean;
  streamingAnswer: string;
  streamingThinking: string;
}

defineProps<Props>();

const emit = defineEmits<{
  "toggle-thinking": [index: number];
  "toggle-streaming-thinking": [];
  copy: [event: string, content: string];
  regenerate: [index: number];
  preview: [file: FileAttachment];
}>();

const listRef = ref<HTMLElement | null>(null);

// 必须在 useChatScroll 调用之后才能 defineExpose scrollToBottom
const { scrollToBottom } = useChatScroll(listRef);

defineExpose({ listRef, scrollToBottom });
</script>

<style scoped>
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
</style>