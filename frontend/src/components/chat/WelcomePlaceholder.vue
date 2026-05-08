<template>
  <div class="ax-placeholder">
    <Welcome
      variant="borderless"
      title="今天有什么可以帮到你？"
      description="上传专利文档或直接提问，我会给出结构化建议。"
    />
    <Prompts
      title="模板示例"
      wrap
      class="ax-prompts ax-prompts-placeholder"
      :items="items"
      :styles="styles"
      @item-click="emit('item-click', $event)"
    />
  </div>
</template>

<script setup lang="ts">
import { Welcome, Prompts } from "ant-design-x-vue";

interface PromptItem {
  key: string;
  label: string;
  description: string;
}

interface Props {
  items: PromptItem[];
  styles?: Record<string, any>;
}

withDefaults(defineProps<Props>(), {
  items: () => [],
  styles: () => ({ list: { width: "100%" }, item: { flex: 1 } }),
});

const emit = defineEmits<{
  "item-click": [info: any];
}>();
</script>

<style scoped>
.ax-placeholder {
  max-width: 720px;
  margin: 0 auto;
  padding: 48px 24px 0;
  width: 100%;
  animation: fadeSlideIn 0.4s ease;
}

.ax-prompts {
  max-width: 720px;
  margin: 24px auto 0;
  padding: 0 24px;
}

.ax-prompts :deep(.ax-prompts-item) {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
  transition: all 0.2s ease;
  cursor: pointer;
}

.ax-prompts :deep(.ax-prompts-item:hover) {
  border-color: var(--primary-light);
  box-shadow: 0 4px 16px rgba(201, 123, 93, 0.12);
  transform: translateY(-2px);
}

.ax-prompts :deep(.ax-prompts-item-title) {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.ax-prompts :deep(.ax-prompts-item-description) {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}

@keyframes fadeSlideIn {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
