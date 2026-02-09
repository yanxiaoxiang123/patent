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
  line-height: 1.8;
  font-size: 15px;
  color: #111827;
  word-wrap: break-word;
}

.message-content.is-streaming {
  padding-right: 20px;
}

.markdown-content {
  color: #111827;
}

.typing-cursor {
  display: inline-block;
  margin-left: 2px;
  color: #111827;
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
