<template>
  <div class="message-header">
    <span class="role-label">{{ role === 'ai' ? '专利 AI 助手' : '我' }}</span>
    <span class="message-time">{{ formattedTime }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  role: 'user' | 'ai' | 'assistant'
  timestamp?: Date | string
}

const props = withDefaults(defineProps<Props>(), {
  timestamp: () => new Date(),
})

const formattedTime = computed(() => {
  const date = props.timestamp instanceof Date
    ? props.timestamp
    : new Date(props.timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })
})
</script>

<style scoped>
.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.role-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}

.message-time {
  font-size: 11px;
  color: var(--text-muted);
}
</style>
