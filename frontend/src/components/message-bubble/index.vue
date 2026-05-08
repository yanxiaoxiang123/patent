<template>
  <div
    class="message-bubble"
    :class="[`role-${role}`, { 'is-streaming': isStreaming }]"
    role="article"
    :aria-label="`${role === 'ai' ? 'AI' : '用户'}消息`"
  >
    <!-- 头像 -->
    <div class="bubble-avatar">
      <div v-if="role === 'ai'" class="avatar ai-avatar">
        <RobotOutlined />
      </div>
      <div v-else class="avatar user-avatar">
        <UserOutlined />
      </div>
    </div>

    <!-- 气泡内容 -->
    <div class="bubble-content">
      <!-- 头部信息 -->
      <MessageHeader :role="role" :timestamp="timestamp" />

      <!-- 思考过程 -->
      <MessageThinking
        v-if="thinkingContent && role === 'ai'"
        :thinking-content="thinkingContent"
        :is-streaming="isStreaming"
        @toggle="emit('toggle-thinking')"
      />

      <!-- 主要内容 -->
      <MessageContent
        :content="content"
        :is-streaming="isStreaming"
        :has-thinking="!!thinkingContent"
        :custom-id="`content-${messageId}`"
      />

      <!-- 附件 -->
      <MessageAttachments
        v-if="attachments && attachments.length > 0"
        :attachments="attachments"
        @preview="emit('preview', $event)"
      />

      <!-- 操作按钮 -->
      <MessageActions
        v-if="showActions && role === 'ai' && !isStreaming"
        @copy="handleCopy"
        @regenerate="emit('regenerate')"
        @quote="emit('quote', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { UserOutlined, RobotOutlined } from "@ant-design/icons-vue";
import MessageHeader from "./MessageHeader.vue";
import MessageThinking from "./MessageThinking.vue";
import MessageContent from "./MessageContent.vue";
import MessageAttachments from "./MessageAttachments.vue";
import MessageActions from "./MessageActions.vue";
import type { FileAttachment } from "@/types";

interface Props {
  role: "user" | "ai" | "assistant";
  content: string;
  timestamp?: Date | string;
  isStreaming?: boolean;
  thinkingContent?: string;
  answerContent?: string;
  attachments?: FileAttachment[];
  messageId?: string | number;
  showActions?: boolean;
  thinkingExpanded?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  role: "user",
  content: "",
  timestamp: () => new Date(),
  isStreaming: false,
  showActions: true,
  messageId: () => Date.now(),
});

const emit = defineEmits<{
  "toggle-thinking": [];
  copy: [content: string];
  regenerate: [];
  quote: [content: string];
  preview: [file: FileAttachment];
}>();

const handleCopy = async () => {
  emit("copy", props.content);
};
</script>

<style scoped>
.message-bubble {
  display: flex;
  gap: 14px;
  padding: 12px 20px;
  max-width: 100%;
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
  position: relative;
}

.message-bubble.role-ai {
  justify-content: flex-start;
}

.message-bubble.role-user {
  flex-direction: row-reverse;
  justify-content: flex-end;
}

.bubble-avatar {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  position: relative;
}

.avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  transition: transform 0.2s ease;
}

.ai-avatar {
  background: var(--primary-pale);
  color: var(--primary-color);
  border: 1.5px solid var(--primary-light);
}

.user-avatar {
  background: linear-gradient(135deg, var(--primary-color), var(--accent));
  color: #fff;
  box-shadow: 0 2px 8px rgba(201, 123, 93, 0.3);
}

.message-bubble:hover .avatar {
  transform: scale(1.05);
}

.bubble-content {
  flex: 1;
  min-width: 0;
  max-width: calc(100% - 50px);
  position: relative;
}

.message-bubble.role-user .bubble-content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

@media (min-width: 768px) {
  .message-bubble {
    padding: 16px 24px;
  }

  .bubble-avatar {
    width: 40px;
    height: 40px;
  }

  .bubble-content {
    max-width: calc(100% - 220px);
  }
}

@media (min-width: 1024px) {
  .bubble-content {
    max-width: 580px;
  }
}
</style>
