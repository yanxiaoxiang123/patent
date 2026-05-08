<template>
  <el-dialog v-model="visible" title="设置" width="400px">
    <el-form :model="localSettings" label-width="100px">
      <el-form-item label="AI 模型">
        <el-select v-model="localSettings.model">
          <el-option label="Qwen3-8b (快速)" value="qwen3:8b" />
          <el-option label="Qwen3-72b (专业)" value="qwen3:72b" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface Settings {
  model: string;
}

interface Props {
  modelValue: boolean;
  settings: Settings;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
}>();

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit("update:modelValue", val),
});

const localSettings = computed(() => props.settings);
</script>
