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
import MarkdownRender from "markstream-vue";

interface Props {
  content: string;
  isStreaming?: boolean;
  hasThinking?: boolean;
  customId?: string;
}

const props = withDefaults(defineProps<Props>(), {
  isStreaming: false,
  hasThinking: false,
  customId: "",
});
</script>

<style scoped>
.message-content {
  position: relative;
  line-height: 1.75;
  font-size: 14.5px;
  color: var(--text-primary);
  word-wrap: break-word;
  background: var(--bg-primary);
  padding: 14px 18px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
  transition: box-shadow 0.2s ease;
}

.message-content:hover {
  box-shadow: var(--shadow-md);
}

.message-content.is-streaming {
  padding-right: 24px;
  background: linear-gradient(135deg, var(--bg-primary), var(--primary-pale));
}

.message-content.has-thinking {
  border-top-left-radius: 4px;
}

.markdown-content {
  color: var(--text-primary);
  font-family: var(--font-body);
}

.markdown-content :deep(p) {
  margin-bottom: 12px;
}

.markdown-content :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-content :deep(code) {
  background: var(--bg-tertiary);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  font-family: "JetBrains Mono", "Fira Code", monospace;
}

.markdown-content :deep(pre) {
  background: var(--bg-tertiary);
  padding: 12px 16px;
  border-radius: var(--radius-md);
  overflow-x: auto;
  margin: 12px 0;
}

.markdown-content :deep(pre code) {
  background: none;
  padding: 0;
}

.typing-cursor {
  display: inline-block;
  margin-left: 2px;
  color: var(--primary-color);
  animation: cursorBlink 0.8s infinite;
  font-weight: 300;
}

@keyframes cursorBlink {
  0%,
  50% {
    opacity: 1;
  }
  51%,
  100% {
    opacity: 0;
  }
}
</style>
