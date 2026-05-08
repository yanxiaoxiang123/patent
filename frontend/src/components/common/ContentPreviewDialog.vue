<template>
  <el-dialog
    v-model="visible"
    :title="title"
    width="600px"
    @close="handleClose"
  >
    <div class="preview-content">
      <pre>{{ content }}</pre>
    </div>
    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { ElMessage } from "element-plus";
import type { FileAttachment } from "@/types";

interface Props {
  modelValue: boolean;
  title?: string;
  content?: string;
}

const props = withDefaults(defineProps<Props>(), {
  title: "",
  content: "",
});

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
}>();

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit("update:modelValue", value),
});

const handleClose = () => {
  emit("update:modelValue", false);
};

defineExpose({});
</script>

<style scoped>
.preview-content {
  max-height: 500px;
  overflow-y: auto;
  padding: 16px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
}

.preview-content pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: "JetBrains Mono", "Fira Code", "Courier New", monospace;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-primary);
  margin: 0;
}
</style>
