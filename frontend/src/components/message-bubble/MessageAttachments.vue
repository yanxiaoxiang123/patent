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
          {{ file.error ? '解析失败' : file.parsed ? '已解析' : '解析中' }}
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
import { FileOutlined, FilePdfOutlined, FileWordOutlined, EyeOutlined } from '@ant-design/icons-vue'
import type { FileAttachment } from '@/types'

interface Props {
  attachments: FileAttachment[]
}

const props = defineProps<Props>()

defineEmits<{
  'preview': [file: FileAttachment]
}>()

const getFileIcon = (filename: string) => {
  const ext = filename.split('.').pop()?.toLowerCase()
  if (ext === 'pdf') return FilePdfOutlined
  if (['doc', 'docx'].includes(ext || '')) return FileWordOutlined
  return FileOutlined
}

const getFileIconClass = (filename: string) => {
  const ext = filename.split('.').pop()?.toLowerCase()
  if (ext === 'pdf') return 'icon-pdf'
  if (['doc', 'docx'].includes(ext || '')) return 'icon-word'
  return 'icon-default'
}

const getFileType = (filename: string) => {
  const ext = filename.split('.').pop()?.toLowerCase()
  const types: Record<string, string> = {
    pdf: 'PDF',
    doc: 'DOC',
    docx: 'DOCX',
  }
  return types[ext || ''] || '文档'
}

const canPreview = (file: FileAttachment) => {
  return !!(file.parsedContent || file.parsed_content)
}
</script>

<style scoped>
.message-attachments {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.attachment-card {
  padding: 10px 12px;
  background: rgba(248, 250, 252, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 10px;
  transition: all 0.2s ease;
}

.attachment-card:hover {
  border-color: rgba(59, 130, 246, 0.3);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.attachment-card.has-error {
  border-color: rgba(239, 68, 68, 0.3);
  background: rgba(254, 242, 242, 0.9);
}

.attachment-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.attachment-icon {
  font-size: 22px;
  color: #6b7280;
}

.attachment-icon.icon-pdf {
  color: #ef4444;
}

.attachment-icon.icon-word {
  color: #2563eb;
}

.attachment-info {
  flex: 1;
  min-width: 0;
}

.attachment-name {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attachment-type {
  font-size: 11px;
  color: #9ca3af;
}

.attachment-preview {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #e5e7eb;
}
</style>
