<template>
  <el-dialog
    v-model="visible"
    title="重命名会话"
    width="400px"
    @keyup.enter="handleConfirm"
  >
    <el-input
      v-model="localTitle"
      placeholder="请输入新的会话标题"
      @keyup.enter="handleConfirm"
    />
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button
        type="primary"
        :disabled="!localTitle.trim()"
        @click="handleConfirm"
      >
        确定
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";

interface Props {
  modelValue: boolean;
  title: string;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  confirm: [title: string];
}>();

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit("update:modelValue", val),
});

const localTitle = ref(props.title);
watch(() => props.title, (val) => { localTitle.value = val; });

function handleConfirm() {
  if (localTitle.value.trim()) {
    emit("confirm", localTitle.value.trim());
    visible.value = false;
  }
}
</script>