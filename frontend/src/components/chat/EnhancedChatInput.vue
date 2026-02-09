<template>
  <div class="enhanced-chat-input">
    <!-- 快捷键提示 -->
    <div v-if="showShortcutsHint" class="input-shortcuts-hint">
      <span class="shortcut-item">
        <kbd>Enter</kbd> 发送
      </span>
      <span class="shortcut-item">
        <kbd>Ctrl</kbd>+<kbd>Enter</kbd> 换行
      </span>
    </div>

    <!-- 文件上传进度区域 -->
    <div v-if="uploadingFiles.length > 0" class="upload-progress-area">
      <div
        v-for="file in uploadingFiles"
        :key="file.uid"
        class="upload-progress-item"
      >
        <div class="upload-file-info">
          <FileOutlined class="file-icon" :class="getFileIconClass(file.name)" />
          <span class="upload-file-name">{{ file.name }}</span>
          <span class="upload-file-size">{{ formatFileSize(file.size) }}</span>
        </div>
        <div class="upload-progress-bar">
          <div
            class="upload-progress-fill"
            :style="{ width: `${file.progress || 0}%` }"
          />
        </div>
        <span class="upload-progress-text">{{ file.progressText || '上传中...' }}</span>
      </div>
    </div>

    <!-- 解析进度区域 -->
    <div v-if="parsingFiles.length > 0" class="parsing-progress-area">
      <div
        v-for="file in parsingFiles"
        :key="file.id"
        class="parsing-progress-item"
      >
        <div class="parsing-file-info">
          <FileSearchOutlined class="file-icon" />
          <span class="parsing-file-name">{{ file.name }}</span>
        </div>
        <div class="parsing-steps">
          <div
            v-for="(step, index) in file.parsingThinkingSteps"
            :key="index"
            class="parsing-step"
          >
            <span
              class="step-dot"
              :class="{
                completed: step.status === 'completed',
                error: step.status === 'error',
                pending: step.status === 'pending'
              }"
            >
              <CheckOutlined v-if="step.status === 'completed'" />
              <CloseOutlined v-else-if="step.status === 'error'" />
              <LoadingOutlined v-else-if="step.status === 'loading'" />
              <span v-else>{{ index + 1 }}</span>
            </span>
            <span class="step-text" :class="{ active: step.status === 'loading' }">
              {{ step.step }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 附件区域 -->
    <div v-if="attachments.length > 0" class="attachments-area">
      <div
        v-for="attachment in attachments"
        :key="attachment.id || attachment.uid"
        class="attachment-item"
        :class="{ 'has-error': attachment.error }"
      >
        <div class="attachment-main">
          <component
            :is="getFileIcon(attachment.name)"
            class="attachment-icon"
            :class="getFileIconClass(attachment.name)"
          />
          <div class="attachment-info">
            <span class="attachment-name">{{ attachment.name }}</span>
            <span class="attachment-meta">
              {{ getFileType(attachment.name) }} · {{ formatFileSize(attachment.size || 0) }}
            </span>
          </div>
          <el-tag
            :type="attachment.error ? 'danger' : attachment.parsed ? 'success' : 'warning'"
            size="small"
            class="attachment-status"
          >
            {{
              attachment.error
                ? '解析失败'
                : attachment.parsed
                  ? '已解析'
                  : '解析中'
            }}
          </el-tag>
          <el-button
            type="text"
            size="small"
            class="attachment-remove"
            @click="handleRemove(attachment)"
          >
            <CloseOutlined />
          </el-button>
        </div>
        <!-- 解析步骤 -->
        <div v-if="attachment.parsingThinkingSteps && attachment.parsingThinkingSteps.length > 0" class="attachment-steps">
          <div
            v-for="(step, idx) in attachment.parsingThinkingSteps"
            :key="idx"
            class="attachment-step"
          >
            <span
              class="step-dot"
              :class="{
                completed: step.status === 'completed',
                error: step.status === 'error'
              }"
            >
              <CheckOutlined v-if="step.status === 'completed'" />
              <CloseOutlined v-else-if="step.status === 'error'" />
              <span v-else>{{ idx + 1 }}</span>
            </span>
            <span class="step-text">{{ step.step }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入框主体 -->
    <div
      class="input-wrapper"
      :class="{
        'has-attachments': attachments.length > 0,
        'is-focused': isFocused,
        'is-disabled': disabled || isLoading
      }"
    >
      <!-- 附件按钮 -->
      <div class="input-prefix">
        <el-dropdown
          trigger="click"
          placement="top-start"
          @command="handleFileCommand"
        >
          <el-badge :dot="true" :hidden="!canAttach">
            <el-button type="text" class="attach-btn" :disabled="disabled || isLoading">
              <template #icon>
                <PaperClipOutlined />
              </template>
            </el-button>
          </el-badge>
          <template #dropdown>
            <el-dropdown-menu class="attach-dropdown">
              <el-dropdown-item command="upload" :disabled="disabled || isLoading">
                <UploadOutlined class="dropdown-icon" />
                上传文档
                <span class="dropdown-hint">.doc/.docx/.pdf</span>
              </el-dropdown-item>
              <el-dropdown-item command="document" divided :disabled="!hasParsedDocuments">
                <FileTextOutlined class="dropdown-icon" />
                我的文档库
                <span class="dropdown-hint">选择已解析文档</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <input
          ref="fileInputRef"
          type="file"
          accept=".doc,.docx,.pdf"
          multiple
          style="display: none"
          @change="handleFileSelect"
        />
      </div>

      <!-- 文本输入框 -->
      <textarea
        ref="textareaRef"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled || isLoading"
        class="input-textarea"
        :class="{ 'has-content': modelValue.length > 0 }"
        @input="handleInput"
        @keydown="handleKeydown"
        @focus="isFocused = true"
        @blur="handleBlur"
        @paste="handlePaste"
      />

      <!-- 发送按钮 -->
      <div class="input-suffix">
        <div v-if="isLoading" class="loading-indicator">
          <span class="loading-dot"></span>
          <span class="loading-dot"></span>
          <span class="loading-dot"></span>
        </div>
        <el-button
          type="primary"
          class="send-btn"
          :class="{ 'is-sending': isLoading }"
          :disabled="!canSend || disabled"
          @click="handleSend"
        >
          <template #icon>
            <SendOutlined v-if="!isLoading" />
            <LoadingOutlined v-else />
          </template>
          <span v-if="!isLoading" class="send-text">发送</span>
          <span v-else class="sending-text">思考中</span>
        </el-button>
      </div>
    </div>

    <!-- 输入框底部提示 -->
    <div class="input-footer">
      <div class="footer-left">
        <span class="input-hint">按 <kbd class="hint-kbd">Enter</kbd> 发送，<kbd class="hint-kbd">Ctrl+Enter</kbd> 换行</span>
      </div>
      <div class="footer-right">
        <span v-if="modelValue.length > 0" class="char-count">{{ modelValue.length }} 字</span>
        <span class="disclaimer">内容由 AI 生成，请仔细甄别</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue';
import {
  PaperClipOutlined,
  SendOutlined,
  LoadingOutlined,
  CloseOutlined,
  CheckOutlined,
  FileOutlined,
  FilePdfOutlined,
  FileWordOutlined,
  FileTextOutlined,
  UploadOutlined,
  FileSearchOutlined,
} from '@ant-design/icons-vue';
import { ElMessage } from 'element-plus';
import type { FileAttachment } from '@/types';

// Props
interface Props {
  modelValue: string;
  placeholder?: string;
  disabled?: boolean;
  isLoading?: boolean;
  attachments?: FileAttachment[];
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  placeholder: '输入消息...',
  disabled: false,
  isLoading: false,
  attachments: () => [],
});

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: string];
  'send': [content: string];
  'remove-attachment': [file: FileAttachment];
  'attach': [files: FileList];
}>();

// Refs
const textareaRef = ref<HTMLTextAreaElement | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null);
const isFocused = ref(false);
const showShortcutsHint = ref(false);

// Computed
const canSend = computed(() => {
  const hasText = props.modelValue.trim().length > 0;
  const hasReadyAttachments = props.attachments.length > 0 &&
    props.attachments.every(f => f.parsed || f.error);
  return hasText || hasReadyAttachments;
});

const canAttach = computed(() => !props.disabled && !props.isLoading);

const hasParsedDocuments = computed(() => {
  return props.attachments.some(f => f.parsed && f.parsedContent);
});

const uploadingFiles = computed(() => {
  return props.attachments.filter(f => !f.id);
});

const parsingFiles = computed(() => {
  return props.attachments.filter(f => f.id && !f.parsed && !f.error);
});

// Methods
const handleInput = (e: Event) => {
  const target = e.target as HTMLTextAreaElement;
  emit('update:modelValue', target.value);
};

const handleKeydown = (e: KeyboardEvent) => {
  if (props.disabled || props.isLoading) return;

  // Ctrl + Enter: 换行
  if (e.ctrlKey && e.key === 'Enter') {
    e.preventDefault();
    const textarea = textareaRef.value;
    if (textarea) {
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const value = props.modelValue;
      const newValue = value.substring(0, start) + '\n' + value.substring(end);
      emit('update:modelValue', newValue);
      nextTick(() => {
        textarea.selectionStart = textarea.selectionEnd = start + 1;
        textarea.focus();
      });
    }
  }
  // Enter: 发送
  else if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    if (canSend.value) {
      handleSend();
    } else if (!props.modelValue.trim()) {
      ElMessage.warning('请输入消息内容');
    }
  }
};

const handleBlur = () => {
  isFocused.value = false;
  showShortcutsHint.value = false;
};

const handleSend = () => {
  if (!canSend.value || props.disabled || props.isLoading) return;
  emit('send', props.modelValue.trim());
};

const handleRemove = (file: FileAttachment) => {
  emit('remove-attachment', file);
};

const handleFileCommand = (command: string) => {
  if (command === 'upload') {
    fileInputRef.value?.click();
  } else if (command === 'document') {
    ElMessage.info('文档库功能开发中');
  }
};

const handleFileSelect = (e: Event) => {
  const target = e.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    emit('attach', target.files);
    target.value = '';
  }
};

const handlePaste = (e: ClipboardEvent) => {
  const items = e.clipboardData?.items;
  if (!items) return;

  const files: File[] = [];
  for (const item of items) {
    if (item.type.startsWith('image/') || item.type.includes('document')) {
      const file = item.getAsFile();
      if (file) files.push(file);
    }
  }

  if (files.length > 0) {
    emit('attach', files as unknown as FileList);
  }
};

const getFileIcon = (filename: string) => {
  const ext = filename.split('.').pop()?.toLowerCase();
  if (ext === 'pdf') return FilePdfOutlined;
  if (['doc', 'docx'].includes(ext || '')) return FileWordOutlined;
  return FileTextOutlined;
};

const getFileIconClass = (filename: string) => {
  const ext = filename.split('.').pop()?.toLowerCase();
  if (ext === 'pdf') return 'icon-pdf';
  if (['doc', 'docx'].includes(ext || '')) return 'icon-word';
  return 'icon-default';
};

const getFileType = (filename: string) => {
  const ext = filename.split('.').pop()?.toLowerCase();
  const types: Record<string, string> = {
    pdf: 'PDF 文档',
    doc: 'Word 文档',
    docx: 'Word 文档',
  };
  return types[ext || ''] || '文档';
};

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

// Auto-resize textarea
watch(() => props.modelValue, () => {
  nextTick(() => {
    const textarea = textareaRef.value;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }
  });
});
</script>

<style scoped>
.enhanced-chat-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.96);
  border-radius: 20px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  backdrop-filter: blur(26px);
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.18);
  overflow: hidden;
}

/* 快捷键提示 */
.input-shortcuts-hint {
  display: flex;
  gap: 16px;
  padding: 8px 16px;
  background: rgba(59, 130, 246, 0.06);
  border-bottom: 1px solid rgba(59, 130, 246, 0.1);
  font-size: 12px;
  color: #6b7280;
}

.shortcut-item kbd {
  display: inline-block;
  padding: 2px 6px;
  margin: 0 2px;
  font-size: 11px;
  font-family: inherit;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

/* 上传进度区域 */
.upload-progress-area {
  padding: 12px 16px;
  background: rgba(59, 130, 246, 0.04);
  border-bottom: 1px solid rgba(59, 130, 246, 0.1);
}

.upload-progress-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}

.upload-file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 150px;
}

.upload-file-name {
  font-size: 13px;
  color: #374151;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.upload-file-size {
  font-size: 12px;
  color: #9ca3af;
}

.upload-progress-bar {
  flex: 1;
  height: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  overflow: hidden;
}

.upload-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #2563eb);
  border-radius: 2px;
  transition: width 0.3s ease;
}

.upload-progress-text {
  font-size: 12px;
  color: #6b7280;
  min-width: 60px;
  text-align: right;
}

/* 解析进度区域 */
.parsing-progress-area {
  padding: 12px 16px;
  background: rgba(16, 185, 129, 0.04);
  border-bottom: 1px solid rgba(16, 185, 129, 0.1);
}

.parsing-progress-item {
  padding: 8px 0;
}

.parsing-file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.parsing-file-name {
  font-size: 13px;
  color: #374151;
}

.parsing-steps {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.parsing-step {
  display: flex;
  align-items: center;
  gap: 6px;
}

.step-dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: #9ca3af;
}

.step-dot.completed {
  background: #10b981;
  color: #fff;
}

.step-dot.error {
  background: #ef4444;
  color: #fff;
}

.step-dot.pending {
  background: #e5e7eb;
}

.step-text {
  font-size: 12px;
  color: #9ca3af;
}

.step-text.active {
  color: #3b82f6;
}

/* 附件区域 */
.attachments-area {
  padding: 12px 16px;
  background: rgba(248, 250, 252, 0.8);
  border-bottom: 1px solid rgba(148, 163, 184, 0.15);
}

.attachment-item {
  padding: 10px 12px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  margin-bottom: 8px;
  transition: all 0.2s ease;
}

.attachment-item:last-child {
  margin-bottom: 0;
}

.attachment-item.has-error {
  border-color: #fecaca;
  background: #fef2f2;
}

.attachment-main {
  display: flex;
  align-items: center;
  gap: 10px;
}

.attachment-icon {
  font-size: 20px;
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

.attachment-meta {
  font-size: 11px;
  color: #9ca3af;
}

.attachment-status {
  flex-shrink: 0;
}

.attachment-remove {
  color: #9ca3af;
  padding: 4px;
}

.attachment-remove:hover {
  color: #ef4444;
}

.attachment-steps {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed #e5e7eb;
}

/* 输入框主体 */
.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 12px 16px;
  min-height: 52px;
}

.input-wrapper.is-focused {
  border-color: rgba(59, 130, 246, 0.5);
}

.input-wrapper.is-disabled {
  opacity: 0.6;
}

.input-prefix {
  display: flex;
  align-items: center;
  padding-bottom: 4px;
}

.attach-btn {
  font-size: 18px;
  color: #6b7280;
  padding: 4px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.attach-btn:hover:not(:disabled) {
  color: #374151;
  background: #f3f4f6;
}

.attach-dropdown {
  min-width: 180px;
}

.dropdown-icon {
  margin-right: 8px;
}

.dropdown-hint {
  margin-left: auto;
  font-size: 11px;
  color: #9ca3af;
}

.input-textarea {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-size: 15px;
  line-height: 1.6;
  color: #111827;
  background: transparent;
  max-height: 200px;
  min-height: 24px;
  padding: 4px 0;
}

.input-textarea::placeholder {
  color: #9ca3af;
}

.input-textarea:disabled {
  cursor: not-allowed;
  color: #9ca3af;
}

.input-suffix {
  display: flex;
  align-items: center;
  padding-bottom: 4px;
}

/* 发送按钮 */
.send-btn {
  height: 36px;
  padding: 0 16px;
  border-radius: 10px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.send-btn:not(:disabled):hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(17, 24, 39, 0.3);
}

.send-text {
  margin-left: 4px;
}

.sending-text {
  margin-left: 4px;
}

/* 加载指示器 */
.loading-indicator {
  display: flex;
  gap: 4px;
  padding: 0 12px;
}

.loading-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #6b7280;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dot:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

/* 输入框底部 */
.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: rgba(248, 250, 252, 0.5);
  border-top: 1px solid rgba(148, 163, 184, 0.1);
  font-size: 12px;
}

.footer-left,
.footer-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.input-hint {
  color: #9ca3af;
}

.hint-kbd {
  display: inline-block;
  padding: 1px 5px;
  font-size: 10px;
  font-family: inherit;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 3px;
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.05);
}

.char-count {
  color: #6b7280;
}

.disclaimer {
  color: #9ca3af;
}

/* 响应式 */
@media (max-width: 640px) {
  .input-footer {
    flex-direction: column;
    gap: 6px;
  }

  .footer-left,
  .footer-right {
    justify-content: center;
  }
}
</style>
