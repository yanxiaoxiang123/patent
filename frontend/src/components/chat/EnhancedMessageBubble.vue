<template>
  <div class="enhanced-message-bubble" :class="[`role-${role}`, { 'is-streaming': isStreaming }]">
    <!-- 头像 -->
    <div class="bubble-avatar">
      <div v-if="role === 'ai'" class="avatar ai-avatar">
        <RobotOutlined />
      </div>
      <div v-else class="avatar user-avatar">
        <UserOutlined />
      </div>
    </div>

    <!-- 气泡内容 -->
    <div class="bubble-content">
      <!-- 角色标签 -->
      <div class="bubble-header">
        <span class="role-label">{{ role === 'ai' ? '专利 AI 助手' : '我' }}</span>
        <span class="message-time">{{ formattedTime }}</span>
      </div>

      <!-- 思考过程 -->
      <div v-if="thinkingContent" class="thinking-section">
        <div
          class="thinking-toggle"
          :class="{ expanded: thinkingExpanded }"
          @click="toggleThinking"
        >
          <div class="thinking-toggle-header">
            <BulbOutlined class="thinking-icon" />
            <span class="thinking-title">思考过程</span>
            <DownOutlined class="toggle-arrow" />
          </div>
        </div>
        <Transition name="thinking-slide">
          <div v-if="thinkingExpanded" class="thinking-panel">
            <MarkdownRender
              :custom-id="`thinking-${messageId}`"
              :content="thinkingContent"
              class="thinking-content"
            />
          </div>
        </Transition>
      </div>

      <!-- 主要内容 -->
      <div class="message-body" :class="{ 'is-streaming': isStreaming }">
        <!-- 流式加载指示器 -->
        <div v-if="isStreaming && !answerContent" class="streaming-indicator">
          <div class="streaming-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <span class="streaming-text">AI 正在思考</span>
        </div>

        <!-- 思考过程中的部分回答 -->
        <div v-if="thinkingContent && answerContent && isStreaming" class="streaming-answer">
          <MarkdownRender
            :custom-id="`streaming-answer-${messageId}`"
            :content="answerContent"
          />
        </div>

        <!-- 最终内容 -->
        <MarkdownRender
          v-if="!isStreaming || answerContent"
          :custom-id="`content-${messageId}`"
          :content="displayContent"
        />

        <!-- 光标动画 -->
        <span v-if="isStreaming" class="typing-cursor">|</span>
      </div>

      <!-- 附件 -->
      <div v-if="attachments && attachments.length > 0" class="attachments-section">
        <div
          v-for="file in attachments"
          :key="file.id"
          class="attachment-card"
        >
          <div class="attachment-header">
            <component
              :is="getFileIcon(file.name)"
              class="attachment-icon"
              :class="getFileIconClass(file.name)"
            />
            <div class="attachment-info">
              <span class="attachment-name">{{ file.name }}</span>
              <span class="attachment-type">{{ getFileType(file.name) }}</span>
            </div>
            <el-tag
              :type="file.error ? 'danger' : file.parsed ? 'success' : 'warning'"
              size="small"
            >
              {{ file.error ? '解析失败' : file.parsed ? '已解析' : '解析中' }}
            </el-tag>
          </div>
          <div v-if="file.parsed && canPreview(file)" class="attachment-preview">
            <el-button
              type="primary"
              text
              size="small"
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

      <!-- 操作按钮 -->
      <div v-if="showActions && !isStreaming" class="bubble-actions">
        <div class="action-group">
          <el-tooltip content="复制内容" placement="top">
            <el-button
              type="text"
              size="small"
              class="action-btn"
              @click="handleCopy"
            >
              <template #icon>
                <CopyOutlined />
              </template>
              <span class="action-text">复制</span>
            </el-button>
          </el-tooltip>
          <el-tooltip content="重新生成" placement="top">
            <el-button
              v-if="role === 'ai'"
              type="text"
              size="small"
              class="action-btn"
              @click="$emit('regenerate')"
            >
              <template #icon>
                <RedoOutlined />
              </template>
              <span class="action-text">重新生成</span>
            </el-button>
          </el-tooltip>
          <el-tooltip content="引用回复" placement="top">
            <el-button
              type="text"
              size="small"
              class="action-btn"
              @click="handleQuote"
            >
              <template #icon>
                <CommentOutlined />
              </template>
              <span class="action-text">引用</span>
            </el-button>
          </el-tooltip>
        </div>

        <!-- 更多操作 -->
        <el-dropdown trigger="click" @command="handleMoreAction">
          <el-button type="text" size="small" class="action-btn more-btn">
            <template #icon>
              <MoreOutlined />
            </template>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="collect">
                <StarOutlined style="margin-right: 8px" />
                收藏
              </el-dropdown-item>
              <el-dropdown-item command="report">
                <FlagOutlined style="margin-right: 8px" />
                举报
              </el-dropdown-item>
              <el-dropdown-item divided command="delete" v-if="role !== 'ai'">
                <DeleteOutlined style="margin-right: 8px" />
                删除
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>

      <!-- 复制成功提示 -->
      <Transition name="fade">
        <div v-if="showCopySuccess" class="copy-success-tip">
          <CheckCircleOutlined />
          已复制到剪贴板
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import {
  UserOutlined,
  RobotOutlined,
  BulbOutlined,
  DownOutlined,
  CopyOutlined,
  RedoOutlined,
  CommentOutlined,
  MoreOutlined,
  StarOutlined,
  FlagOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  EyeOutlined,
  FileOutlined,
  FilePdfOutlined,
  FileWordOutlined,
} from '@ant-design/icons-vue';
import MarkdownRender from 'markstream-vue';
import { ElMessage } from 'element-plus';
import type { FileAttachment } from '@/types';

interface Props {
  role: 'user' | 'ai' | 'assistant';
  content: string;
  timestamp?: Date | string;
  isStreaming?: boolean;
  thinkingContent?: string;
  answerContent?: string;
  attachments?: FileAttachment[];
  messageId?: string | number;
  showActions?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  role: 'user',
  content: '',
  timestamp: () => new Date(),
  isStreaming: false,
  showActions: true,
  messageId: () => Date.now(),
});

const emit = defineEmits<{
  'copy': [content: string];
  'regenerate': [];
  'preview': [file: FileAttachment];
  'quote': [content: string];
  'collect': [];
  'report': [];
  'delete': [];
}>();

// State
const thinkingExpanded = ref(false);
const showCopySuccess = ref(false);

// Computed
const formattedTime = computed(() => {
  const date = props.timestamp instanceof Date
    ? props.timestamp
    : new Date(props.timestamp);
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  });
});

const displayContent = computed(() => {
  if (props.role === 'ai') {
    // 如果有思考过程，只显示回答部分
    if (props.thinkingContent) {
      return props.answerContent || '';
    }
  }
  return props.content;
});

// Methods
const toggleThinking = () => {
  thinkingExpanded.value = !thinkingExpanded.value;
};

const handleCopy = async () => {
  const text = props.answerContent || props.content;
  try {
    await navigator.clipboard.writeText(text);
    showCopySuccess.value = true;
    setTimeout(() => {
      showCopySuccess.value = false;
    }, 2000);
    emit('copy', text);
  } catch {
    ElMessage.error('复制失败，请手动选择复制');
  }
};

const handleQuote = () => {
  const text = (props.answerContent || props.content).slice(0, 200);
  emit('quote', text);
};

const handleMoreAction = (command: string) => {
  switch (command) {
    case 'collect':
      emit('collect');
      ElMessage.success('已收藏');
      break;
    case 'report':
      emit('report');
      ElMessage.info('举报功能开发中');
      break;
    case 'delete':
      emit('delete');
      ElMessage.success('已删除');
      break;
  }
};

const getFileIcon = (filename: string) => {
  const ext = filename.split('.').pop()?.toLowerCase();
  if (ext === 'pdf') return FilePdfOutlined;
  if (['doc', 'docx'].includes(ext || '')) return FileWordOutlined;
  return FileOutlined;
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
    pdf: 'PDF',
    doc: 'DOC',
    docx: 'DOCX',
  };
  return types[ext || ''] || '文档';
};

const canPreview = (file: FileAttachment) => {
  return !!(file.parsedContent || file.parsed_content);
};
</script>

<style scoped>
.enhanced-message-bubble {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  max-width: 720px;
  margin: 0 auto;
  animation: messageIn 0.3s ease;
}

@keyframes messageIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.enhanced-message-bubble.role-user {
  flex-direction: row-reverse;
}

.enhanced-message-bubble.is-streaming {
  background: rgba(59, 130, 246, 0.03);
}

/* 头像 */
.bubble-avatar {
  flex-shrink: 0;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.ai-avatar {
  background: linear-gradient(135deg, #0f172a 0%, #111827 100%);
  color: #f9fafb;
}

.user-avatar {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #fff;
}

/* 内容区域 */
.bubble-content {
  flex: 1;
  min-width: 0;
}

.bubble-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.role-label {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}

.message-time {
  font-size: 12px;
  color: #9ca3af;
}

/* 思考过程 */
.thinking-section {
  margin-bottom: 12px;
}

.thinking-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: rgba(59, 130, 246, 0.08);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.thinking-toggle:hover {
  background: rgba(59, 130, 246, 0.12);
  border-color: rgba(59, 130, 246, 0.3);
}

.thinking-toggle.expanded {
  background: rgba(59, 130, 246, 0.1);
}

.thinking-toggle-header {
  display: flex;
  align-items: center;
  gap: 6px;
}

.thinking-icon {
  color: #3b82f6;
  font-size: 14px;
}

.thinking-title {
  font-size: 12px;
  color: #3b82f6;
  font-weight: 500;
}

.toggle-arrow {
  font-size: 10px;
  color: #3b82f6;
  transition: transform 0.3s ease;
}

.thinking-toggle.expanded .toggle-arrow {
  transform: rotate(180deg);
}

.thinking-panel {
  margin-top: 10px;
  padding: 12px 14px;
  background: rgba(248, 250, 252, 0.9);
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: 10px;
  font-size: 13px;
  color: #64748b;
  line-height: 1.7;
}

.thinking-content {
  color: #64748b;
}

.thinking-slide-enter-active,
.thinking-slide-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.thinking-slide-enter-from,
.thinking-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 消息主体 */
.message-body {
  position: relative;
  line-height: 1.8;
  font-size: 15px;
  color: #111827;
  word-wrap: break-word;
}

.message-body.is-streaming {
  padding-right: 20px;
}

/* 流式指示器 */
.streaming-indicator {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(59, 130, 246, 0.06);
  border-radius: 8px;
  margin-bottom: 8px;
}

.streaming-dots {
  display: flex;
  gap: 3px;
}

.streaming-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #3b82f6;
  animation: streamingDot 1.4s infinite ease-in-out both;
}

.streaming-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.streaming-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes streamingDot {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.streaming-text {
  font-size: 12px;
  color: #3b82f6;
}

.streaming-answer {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #e5e7eb;
}

.typing-cursor {
  display: inline-block;
  margin-left: 2px;
  color: #111827;
  animation: cursorBlink 1s infinite;
}

@keyframes cursorBlink {
  0%, 50% {
    opacity: 1;
  }
  51%, 100% {
    opacity: 0;
  }
}

/* 附件 */
.attachments-section {
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

/* 操作按钮 */
.bubble-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid rgba(148, 163, 184, 0.1);
}

.action-group {
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  font-size: 12px;
  color: #6b7280;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.action-btn:hover {
  color: #374151;
  background: rgba(148, 163, 184, 0.1);
}

.action-text {
  font-size: 12px;
}

.more-btn {
  padding: 4px 6px;
}

/* 复制成功提示 */
.copy-success-tip {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  padding: 8px 16px;
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  font-size: 13px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
  animation: fadeIn 0.3s ease;
  z-index: 10;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式 */
@media (max-width: 640px) {
  .enhanced-message-bubble {
    padding: 12px 16px;
  }

  .action-text {
    display: none;
  }

  .bubble-actions {
    justify-content: flex-end;
  }
}
</style>
