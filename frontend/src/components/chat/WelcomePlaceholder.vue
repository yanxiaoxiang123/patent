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
  max-width: 640px;
  margin: 0 auto;
  padding: 32px 20px 0;
  width: 100%;
}

.ax-prompts {
  max-width: 640px;
  margin: 16px auto 0;
  padding: 0 20px;
}
</style>