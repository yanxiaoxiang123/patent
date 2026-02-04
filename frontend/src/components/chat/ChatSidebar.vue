<template>
  <div v-show="visible" class="session-sidebar ax-menu">
    <div class="sidebar-header">
      <div class="sidebar-actions">
        <div class="sidebar-title">聊天记录</div>
        <Button
          type="text"
          size="small"
          class="sidebar-close-btn"
          @click="handleClose"
        >
          <template #icon>
            <CloseOutlined />
          </template>
        </Button>
      </div>
    </div>

    <Button type="link" class="sidebar-add-btn" @click="handleNewSession">
      <template #icon>
        <PlusOutlined />
      </template>
      新建会话
    </Button>

    <div v-if="sessions.length > 0" class="session-list">
      <ChatSessionItem
        v-for="session in sessions"
        :key="session.id"
        :session="session"
        :is-active="session.id === currentSessionId"
        @click="handleSessionClick"
        @delete="handleSessionDelete"
      />
    </div>

    <div v-else class="empty-sessions">
      <el-icon size="32" color="#d1d5db">
        <Files />
      </el-icon>
      <p>暂无聊天记录</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button } from "ant-design-vue";
import { CloseOutlined, PlusOutlined } from "@ant-design/icons-vue";
import { Files } from "@element-plus/icons-vue";
import ChatSessionItem from "./ChatSessionItem.vue";
import type { ChatSession } from "@/types";

interface Props {
  visible?: boolean;
  sessions?: ChatSession[];
  currentSessionId?: number | null;
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  sessions: () => [],
  currentSessionId: null,
});

const emit = defineEmits<{
  close: [];
  newSession: [];
  sessionClick: [sessionId: number];
  sessionDelete: [sessionId: number];
}>();

const handleClose = () => {
  emit("close");
};

const handleNewSession = () => {
  emit("newSession");
};

const handleSessionClick = (sessionId: number) => {
  emit("sessionClick", sessionId);
};

const handleSessionDelete = (sessionId: number) => {
  emit("sessionDelete", sessionId);
};
</script>

<style scoped>
.session-sidebar {
  width: 280px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
  margin: 80px 16px 40px 20px;
  backdrop-filter: blur(20px);
  box-shadow: 0 8px 32px rgba(15, 23, 42, 0.12);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.session-sidebar:hover {
  box-shadow: 0 12px 48px rgba(15, 23, 42, 0.18);
  transform: translateY(-2px);
}

.sidebar-header {
  padding: 16px 16px 12px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.15);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(248, 250, 252, 0.9);
  backdrop-filter: blur(12px);
  border-radius: 16px 16px 0 0;
}

.sidebar-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #374151;
}

.sidebar-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  width: 100%;
  justify-content: space-between;
}

.sidebar-close-btn {
  min-width: auto;
  padding: 4px;
}

.sidebar-add-btn {
  margin: 8px 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.sidebar-add-btn:hover {
  background: rgba(59, 130, 246, 0.08);
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  margin-right: 4px;
}

.session-list::-webkit-scrollbar {
  width: 4px;
}

.session-list::-webkit-scrollbar-track {
  background: transparent;
}

.session-list::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.3);
  border-radius: 2px;
}

.session-list::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.5);
}

.empty-sessions {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  text-align: center;
  color: #9ca3af;
  flex: 1;
}

.empty-sessions p {
  margin-top: 12px;
  font-size: 14px;
}
</style>
