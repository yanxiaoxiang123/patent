<template>
  <div class="message-thinking" :class="{ expanded: isExpanded }">
    <!-- 思考过程切换按钮 -->
    <button
      v-if="hasThinking"
      class="thinking-toggle"
      @click="toggleExpand"
    >
      <div class="thinking-toggle-header">
        <BulbOutlined class="thinking-icon" />
        <span class="thinking-title">{{ isExpanded ? '收起思考过程' : '思考过程' }}</span>
        <DownOutlined class="toggle-arrow" />
      </div>
    </button>

    <!-- 思考内容面板 -->
    <Transition name="thinking-slide">
      <div v-show="isExpanded && hasThinking" class="thinking-panel">
        <!-- 思考内容 -->
        <MarkdownRender
          :content="thinkingText"
          class="thinking-content"
        />
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { BulbOutlined, DownOutlined } from '@ant-design/icons-vue'
import MarkdownRender from 'markstream-vue'

interface Props {
  thinkingContent?: string
  answerContent?: string
  isStreaming?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  thinkingContent: '',
  answerContent: '',
  isStreaming: false,
})

const emit = defineEmits<{
  'toggle': []
}>()

// 判断是否有思考内容
const hasThinking = computed(() => {
  return !!(props.thinkingContent && props.thinkingContent.trim())
})

// 思考内容文本
const thinkingText = computed(() => {
  return props.thinkingContent || ''
})

// 展开状态 - 有思考内容时默认展开
const isExpanded = ref(true)

// 监听流式状态
watch(() => props.isStreaming, (streaming) => {
  if (streaming) {
    isExpanded.value = true
  }
})

const toggleExpand = () => {
  isExpanded.value = !isExpanded.value
  emit('toggle')
}
</script>

<style scoped>
.message-thinking {
  margin-bottom: 12px;
}

.thinking-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: rgba(59, 130, 246, 0.08);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.thinking-toggle:hover {
  background: rgba(59, 130, 246, 0.12);
  border-color: rgba(59, 130, 246, 0.3);
}

.thinking-toggle-header {
  display: flex;
  align-items: center;
  gap: 6px;
}

.thinking-icon {
  color: #3b82f6;
  font-size: 14px;
}

.thinking-title {
  font-size: 12px;
  color: #3b82f6;
  font-weight: 500;
}

.toggle-arrow {
  font-size: 10px;
  color: #3b82f6;
  transition: transform 0.3s ease;
}

.message-thinking.expanded .toggle-arrow {
  transform: rotate(180deg);
}

.thinking-panel {
  margin-top: 10px;
  padding: 12px 14px;
  background: rgba(248, 250, 252, 0.9);
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: 10px;
  font-size: 13px;
  color: #64748b;
  line-height: 1.7;
}

.thinking-content {
  color: #64748b;
}

.thinking-slide-enter-active,
.thinking-slide-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.thinking-slide-enter-from,
.thinking-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
