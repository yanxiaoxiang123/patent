<template>
  <div class="message-actions" role="toolbar" aria-label="消息操作">
    <!-- 主要操作按钮 -->
    <div class="action-group">
      <el-tooltip content="复制内容" placement="top">
        <el-button
          text
          size="small"
          class="action-btn"
          aria-label="复制消息内容"
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
          text
          size="small"
          class="action-btn"
          aria-label="重新生成回答"
          @click="$emit('regenerate')"
        >
          <template #icon>
            <RedoOutlined />
          </template>
          <span class="action-text">重新生成</span>
        </el-button>
      </el-tooltip>
    </div>

    <!-- 更多操作下拉菜单 -->
    <el-dropdown
      trigger="click"
      aria-label="更多操作"
      @command="handleMoreAction"
    >
      <el-button
        text
        size="small"
        class="action-btn more-btn"
        aria-haspopup="true"
      >
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
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>

  <!-- 复制成功提示 -->
  <Transition name="fade">
    <div
      v-if="showCopySuccess"
      class="copy-success-tip"
      role="status"
      aria-live="polite"
    >
      <CheckCircleOutlined />
      已复制到剪贴板
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { ElMessage } from "element-plus";
import {
  CopyOutlined,
  RedoOutlined,
  MoreOutlined,
  StarOutlined,
  FlagOutlined,
  CheckCircleOutlined,
} from "@ant-design/icons-vue";

const emit = defineEmits<{
  copy: [content: string];
  regenerate: [];
  quote: [content: string];
}>();

const showCopySuccess = ref(false);

const handleCopy = () => {
  // 通知父组件处理复制
  emit("copy", "");
};

const handleMoreAction = (command: string) => {
  switch (command) {
    case "collect":
      ElMessage.success("已收藏");
      break;
    case "report":
      ElMessage.info("举报功能开发中");
      break;
  }
};

// 父组件调用此方法显示复制成功
const showCopySuccessTip = () => {
  showCopySuccess.value = true;
  setTimeout(() => {
    showCopySuccess.value = false;
  }, 2000);
};

defineExpose({
  showCopySuccessTip,
});
</script>

<style scoped>
.message-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid var(--border-light);
}

.action-group {
  display: flex;
  align-items: center;
  gap: 2px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  font-size: 12px;
  color: var(--text-muted);
  border-radius: var(--radius-sm);
  transition: all 0.15s ease;
}

.action-btn:hover {
  color: var(--primary-color);
  background: rgba(37, 99, 235, 0.04);
}

.action-text {
  font-size: 12px;
}

.more-btn {
  padding: 4px 6px;
}

.copy-success-tip {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  padding: 8px 16px;
  background: var(--text-primary);
  color: #fff;
  font-size: 13px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  gap: 6px;
  animation: fadeIn 0.2s ease;
  z-index: 10;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 640px) {
  .action-text {
    display: none;
  }

  .message-actions {
    justify-content: flex-end;
  }
}
</style>
