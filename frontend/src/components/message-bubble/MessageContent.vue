<template>
  <div
    class="message-content"
    :class="{ 'is-streaming': isStreaming, 'has-thinking': hasThinking }"
  >
    <!-- Markdown 内容 -->
    <MarkdownRender
      :custom-id="customId"
      :content="content"
      class="markdown-content"
    />

    <!-- 光标动画 -->
    <span v-if="isStreaming" class="typing-cursor" aria-hidden="true">|</span>
  </div>
</template>

<script setup lang="ts">
import MarkdownRender from 'markstream-vue'

interface Props {
  content: string
  isStreaming?: boolean
  hasThinking?: boolean
  customId?: string
}

const props = withDefaults(defineProps<Props>(), {
  isStreaming: false,
  hasThinking: false,
  customId: '',
})
</script>

<style scoped>
.message-content {
  position: relative;
  line-height: 1.7;
  font-size: 14px;
  color: var(--text-primary);
  word-wrap: break-word;
  background: var(--bg-primary);
  padding: 12px 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
}

.message-content.is-streaming {
  padding-right: 20px;
}

.markdown-content {
  color: var(--text-primary);
}

.typing-cursor {
  display: inline-block;
  margin-left: 2px;
  color: var(--primary-color);
  animation: cursorBlink 1s infinite;
}

@keyframes cursorBlink {
  0%, 50% {
    opacity: 1;
  }
  51%, 100% {
    opacity: 0;
  }
}
</style>
