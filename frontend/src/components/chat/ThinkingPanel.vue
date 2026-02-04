<template>
  <div class="thinking-panel">
    <div class="thinking-toggle" @click="handleToggle">
      <DownOutlined :class="['thinking-toggle-icon', { expanded: expanded }]" />
      <span class="thinking-toggle-text">
        {{ expanded ? "隐藏思考过程" : "查看思考过程" }}
      </span>
    </div>
    <div v-if="expanded" class="thinking-content">
      <slot name="content">
        <p v-if="!content" class="empty-thinking">暂无思考过程</p>
        <div v-else v-html="content"></div>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { DownOutlined } from "@ant-design/icons-vue";

interface Props {
  content?: string;
  expanded?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  content: "",
  expanded: false,
});

const emit = defineEmits<{
  toggle: [];
}>();

const handleToggle = () => {
  emit("toggle");
};
</script>

<style scoped>
.thinking-panel {
  margin: 8px 0;
}

.thinking-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(59, 130, 246, 0.08);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 13px;
  color: #3b82f6;
  font-weight: 500;
}

.thinking-toggle:hover {
  background: rgba(59, 130, 246, 0.12);
  border-color: rgba(59, 130, 246, 0.3);
  transform: translateY(-1px);
}

.thinking-toggle-icon {
  font-size: 12px;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.thinking-toggle-icon.expanded {
  transform: rotate(180deg);
}

.thinking-toggle-text {
  user-select: none;
}

.thinking-content {
  margin-top: 12px;
  padding: 16px;
  background: rgba(248, 250, 252, 0.8);
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.7;
  color: #475569;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.empty-thinking {
  color: #94a3b8;
  font-style: italic;
  margin: 0;
}

.thinking-content :deep(p) {
  margin: 0.5em 0;
}

.thinking-content :deep(p:first-child) {
  margin-top: 0;
}

.thinking-content :deep(p:last-child) {
  margin-bottom: 0;
}
</style>
