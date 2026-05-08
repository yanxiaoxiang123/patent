<template>
  <div class="session-sidebar ax-menu">
    <div class="sidebar-header">
      <div class="sidebar-title">聊天记录</div>
      <Button type="text" size="small" class="sidebar-close-btn" @click="emit('close')">
        <template #icon>
          <CloseOutlined />
        </template>
      </Button>
    </div>

    <Button type="link" class="sidebar-add-btn" @click="emit('add-session')">
      <template #icon>
        <PlusOutlined />
      </template>
      新建会话
    </Button>

    <Conversations
      v-if="items.length > 0"
      class="ax-conversations"
      :items="items"
      :active-key="activeKey"
      :menu="menu"
      @active-change="onActiveChange"
    />

    <div v-else class="empty-sessions">
      <el-icon size="32" color="#d1d5db"><Files /></el-icon>
      <p>暂无聊天记录</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Files } from "@element-plus/icons-vue";
import { Button } from "ant-design-vue";
import { CloseOutlined, PlusOutlined } from "@ant-design/icons-vue";
import { Conversations } from "ant-design-x-vue";

interface ConversationItem {
  key: string;
  label: string;
  timestamp?: number;
}

interface Props {
  items: ConversationItem[];
  activeKey?: string;
  menu: (conversation: ConversationItem) => {
    items: { key: string; label: string }[];
    onClick: (payload: { key: string; domEvent: Event }) => void;
  };
}

defineProps<Props>();

const emit = defineEmits<{
  close: [];
  "add-session": [];
  "active-change": [key: string];
}>();

function onActiveChange(key: string) {
  emit("active-change", key);
}
</script>

<style scoped>
.session-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: 280px;
  height: 100vh;
  background: var(--bg-primary);
  border-right: 1px solid var(--border-color);
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 1001;
}

.sidebar-header {
  padding: 12px;
  border-bottom: 1px solid var(--border-light);
  display: flex;
  align-items: center;
}

.sidebar-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
}

.sidebar-add-btn {
  color: var(--primary-color);
  font-weight: 500;
  font-size: 13px;
}

.sidebar-add-btn:hover {
  background: rgba(37, 99, 235, 0.04);
}

.empty-sessions {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px;
  color: var(--text-muted);
}

.empty-sessions p {
  margin-top: 12px;
  font-size: 13px;
}

.ax-conversations {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.ax-conversations :deep(.ax-conversations-item) {
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  margin-bottom: 2px;
  transition: background 0.15s ease;
  cursor: pointer;
}

.ax-conversations :deep(.ax-conversations-item:hover) {
  background: var(--bg-tertiary);
}

.ax-conversations :deep(.ax-conversations-item.active) {
  background: rgba(37, 99, 235, 0.08);
}

.ax-conversations :deep(.ax-conversations-item-title) {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ax-conversations :deep(.ax-conversations-item.active .ax-conversations-item-title) {
  color: var(--primary-color);
  font-weight: 600;
}

.ax-conversations :deep(.ax-conversations-item-meta) {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
}

.ax-conversations :deep(.ax-conversations-item.active .ax-conversations-item-meta) {
  color: var(--text-secondary);
}

.ax-conversations :deep(.ax-conversations-menu) {
  border-radius: var(--radius-sm);
}

.ax-conversations :deep(.ax-conversations-menu-item) {
  font-size: 13px;
  padding: 6px 12px;
}
</style>