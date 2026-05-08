<template>
  <div class="message-attachments" role="list" aria-label="附件列表">
    <div
      v-for="file in attachments"
      :key="file.id"
      class="attachment-card"
      :class="{ 'has-error': file.error }"
      role="listitem"
    >
      <div class="attachment-header">
        <component
          :is="getFileIcon(file.name)"
          class="attachment-icon"
          :class="getFileIconClass(file.name)"
          aria-hidden="true"
        />
        <div class="attachment-info">
          <span class="attachment-name">{{ file.name }}</span>
          <span class="attachment-type">{{ getFileType(file.name) }}</span>
        </div>
        <el-tag
          :type="file.error ? 'danger' : file.parsed ? 'success' : 'warning'"
          size="small"
          role="status"
          aria-live="polite"
        >
          {{ file.error ? "解析失败" : file.parsed ? "已解析" : "解析中" }}
        </el-tag>
      </div>
      <div v-if="file.parsed && canPreview(file)" class="attachment-preview">
        <el-button
          type="primary"
          text
          size="small"
          :aria-label="`预览文件 ${file.name}`"
          @click="$emit('preview', file)"
        >
          <template #icon>
            <EyeOutlined />
          </template>
          预览内容
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  FileOutlined,
  FilePdfOutlined,
  FileWordOutlined,
  EyeOutlined,
} from "@ant-design/icons-vue";
import type { FileAttachment } from "@/types";

interface Props {
  attachments: FileAttachment[];
}

const props = defineProps<Props>();

defineEmits<{
  preview: [file: FileAttachment];
}>();

const getFileIcon = (filename: string) => {
  const ext = filename.split(".").pop()?.toLowerCase();
  if (ext === "pdf") return FilePdfOutlined;
  if (["doc", "docx"].includes(ext || "")) return FileWordOutlined;
  return FileOutlined;
};

const getFileIconClass = (filename: string) => {
  const ext = filename.split(".").pop()?.toLowerCase();
  if (ext === "pdf") return "icon-pdf";
  if (["doc", "docx"].includes(ext || "")) return "icon-word";
  return "icon-default";
};

const getFileType = (filename: string) => {
  const ext = filename.split(".").pop()?.toLowerCase();
  const types: Record<string, string> = {
    pdf: "PDF",
    doc: "DOC",
    docx: "DOCX",
  };
  return types[ext || ""] || "文档";
};

const canPreview = (file: FileAttachment) => {
  return !!(file.parsedContent || file.parsed_content);
};
</script>

<style scoped>
.message-attachments {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.attachment-card {
  padding: 12px 14px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  transition: all 0.18s ease;
}

.attachment-card:hover {
  border-color: var(--primary-light);
  box-shadow: var(--shadow-sm);
}

.attachment-card.has-error {
  border-color: #fca5a5;
  background: #fef2f2;
}

.attachment-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.attachment-icon {
  font-size: 22px;
  color: var(--text-muted);
}

.attachment-icon.icon-pdf {
  color: #dc2626;
}

.attachment-icon.icon-word {
  color: var(--primary-color);
}

.attachment-info {
  flex: 1;
  min-width: 0;
}

.attachment-name {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attachment-type {
  font-size: 11px;
  color: var(--text-muted);
}

.attachment-preview {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed var(--border-color);
}

.attachment-preview :deep(.el-button--text) {
  color: var(--primary-color);
}

.attachment-preview :deep(.el-button--text:hover) {
  color: var(--primary-hover);
}
</style>
