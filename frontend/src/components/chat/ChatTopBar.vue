<template>
  <div class="chat-top-bar">
    <div class="chat-top-bar-left">
      <!-- 侧边栏切换按钮 -->
      <div v-if="!showSidebar" class="sidebar-toggle">
        <el-tooltip content="显示聊天记录" placement="bottom">
          <el-button type="default" size="small" circle @click="emit('toggle-sidebar')">
            <el-icon><Files /></el-icon>
          </el-button>
        </el-tooltip>
      </div>

      <div class="chat-brand">
        <div class="chat-brand-text">
          <div class="chat-brand-title">专利 AI 助手</div>
        </div>
      </div>
    </div>

    <div class="chat-actions">
      <el-button
        v-if="isAdmin"
        type="default"
        size="small"
        @click="emit('go-admin')"
      >
        用户管理
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Files } from "@element-plus/icons-vue";

interface Props {
  showSidebar: boolean;
  isAdmin: boolean;
}

defineProps<Props>();

const emit = defineEmits<{
  "toggle-sidebar": [];
  "go-admin": [];
}>();
</script>

<style scoped>
.chat-top-bar {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 24px;
  max-width: 100%;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-light);
}

.chat-top-bar-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.sidebar-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.chat-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.chat-logo-dot {
  width: 24px;
  height: 24px;
  border-radius: 6px;
}

.chat-brand-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0;
}

@media (max-width: 768px) {
  .chat-top-bar {
    padding: 0 16px;
  }

  .chat-top-bar-left {
    gap: 10px;
  }
}
</style>