<template>
  <Sender
    :value="modelValue"
    :loading="loading"
    :disabled="loading"
    :actions="renderActions"
    class="ax-sender"
    @submit="emit('submit', $event)"
    @change="emit('update:modelValue', $event)"
  >
    <template #prefix>
      <Badge :dot="uploadCount > 0 && !attachmentsOpen">
        <Button type="text" @click="attachmentsOpen = !attachmentsOpen">
          <template #icon>
            <PaperClipOutlined />
          </template>
        </Button>
      </Badge>
    </template>

    <template #header>
      <Sender.Header
        title="附件"
        :open="attachmentsOpen"
        :styles="{ content: { padding: 0 } }"
        @open-change="(open) => (attachmentsOpen = open)"
      >
        <Attachments
          :before-upload="beforeUpload"
          :custom-request="customRequest"
          :items="attachmentItems"
          accept=".doc,.docx,.pdf"
          :multiple="true"
          :on-remove="onRemove"
          @change="onChange"
        >
          <template #placeholder="type">
            <Flex
              v-if="type && type.type === 'inline'"
              align="center"
              justify="center"
              vertical
              gap="2"
              class="ax-attachments-inline"
            >
              <Typography.Text style="font-size: 30px; line-height: 1">
                <CloudUploadOutlined />
              </Typography.Text>
              <Typography.Title
                :level="5"
                style="margin: 0; font-size: 14px; line-height: 1.5"
              >
                上传文档
              </Typography.Title>
              <Typography.Text type="secondary">
                点击或拖拽文件到此处上传（.doc/.docx/.pdf，≤20MB）
              </Typography.Text>
            </Flex>
            <Typography.Text v-if="type && type.type === 'drop'">
              松开即可上传
            </Typography.Text>
          </template>
        </Attachments>
      </Sender.Header>
    </template>
  </Sender>
</template>

<script setup lang="ts">
import { ref, computed, h } from "vue";
import { Badge, Button, Flex, Typography } from "ant-design-vue";
import { CloudUploadOutlined, PaperClipOutlined } from "@ant-design/icons-vue";
import { Attachments, Sender } from "ant-design-x-vue";
import { ElMessage } from "element-plus";
import type { FileAttachment } from "@/types";

interface Props {
  modelValue: string;
  loading: boolean;
  uploadedFiles: FileAttachment[];
  attachmentItems: any[];
}

const props = defineProps<Props>();

const emit = defineEmits<{
  "update:modelValue": [value: string];
  submit: [value: string];
  "attachments-change": [info: any];
  "attachment-remove": [file: any];
  "attachment-custom-request": [options: any];
}>();

const attachmentsOpen = ref(false);

const uploadCount = computed(() => props.uploadedFiles.length);

function beforeUpload(file: File) {
  const isValidType = [
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/pdf",
  ].includes(file.type);
  const isLt20MB = file.size / 1024 / 1024 < 20;
  if (!isValidType) {
    ElMessage.error("只能上传 .doc/.docx/.pdf 格式的文件!");
    return false;
  }
  if (!isLt20MB) {
    ElMessage.error("文件大小不能超过 20MB!");
    return false;
  }
  return true;
}

function customRequest(options: any) {
  emit("attachment-custom-request", options);
}

function onRemove(file: any) {
  emit("attachment-remove", file);
  return true;
}

function onChange(info: any) {
  emit("attachments-change", info);
}

function renderActions(
  _ori: unknown,
  { components }: { components: { LoadingButton: any; SendButton: any } },
) {
  return h(components.SendButton, { disabled: props.loading });
}
</script>

<style scoped>
.ax-sender {
  width: calc(100% - 48px);
  max-width: 680px;
  margin: 0 auto;
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--border-color);
  flex-shrink: 0;
  margin-bottom: 10px;
  transition:
    box-shadow 0.2s ease,
    border-color 0.2s ease;
}

.ax-sender:focus-within {
  box-shadow: 0 4px 20px rgba(201, 123, 93, 0.15);
  border-color: var(--primary-light);
}

.ax-sender :deep(.ant-btn-text) {
  color: var(--text-secondary);
}

.ax-sender :deep(.ant-btn-text:hover) {
  color: var(--primary-color);
  background: var(--primary-pale);
}

.ax-attachments-inline {
  padding: 24px;
  text-align: center;
}

.ax-attachments-inline :deep(.ant-typography) {
  color: var(--text-secondary);
}

.ax-attachments-inline :deep(.ant-typography-secondary) {
  color: var(--text-muted);
}
</style>
