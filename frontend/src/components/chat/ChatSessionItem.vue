<template>
  <div
    :class="['session-item', { active: isActive }]"
    @click="handleClick"
  >
    <div class="session-item-main">
      <div class="session-item-title">
        <span class="session-item-title-text">{{ session.title }}</span>
        <Button
          type="text"
          size="small"
          class="session-delete-btn"
          @click.stop="handleDelete"
        >
          <template #icon>
            <DeleteOutlined />
          </template>
        </Button>
      </div>
      <div class="session-item-meta">
        <span class="session-time">{{ formattedTime }}</span>
        <span class="session-count">{{ session.messageCount }} 条消息</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Button } from "ant-design-vue";
import { DeleteOutlined } from "@ant-design/icons-vue";
import type { ChatSession } from "@/types";
import { formatTime } from "@/utils/chat/message";

interface Props {
  session: ChatSession;
  isActive?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  isActive: false,
});

const emit = defineEmits<{
  click: [sessionId: number];
  delete: [sessionId: number];
}>();

const formattedTime = computed(() => {
  if (props.session.updatedAt) {
    return formatTime(props.session.updatedAt);
  }
  if (props.session.createdAt) {
    return formatTime(props.session.createdAt);
  }
  return "刚刚";
});

const handleClick = () => {
  emit("click", props.session.id);
};

const handleDelete = () => {
  emit("delete", props.session.id);
};
</script>

<style scoped>
.session-item {
  padding: 8px 8px 6px;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 4px;
  transition:
    background 0.16s ease,
    box-shadow 0.16s ease;
}

.session-item:hover {
  background: #f3f4f6;
}

.session-item.active {
  background: #111827;
  color: #f9fafb;
}

.session-item-main {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.session-item-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
}

.session-item-title-text {
  font-size: 14px;
  font-weight: 500;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-delete-btn {
  opacity: 0;
  transition: opacity 0.16s ease;
  padding: 2px;
  min-height: 20px;
  width: 20px;
}

.session-item:hover .session-delete-btn {
  opacity: 1;
}

.session-item.active .session-delete-btn {
  color: #f9fafb;
  opacity: 0.7;
}

.session-item-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: #9ca3af;
}

.session-item.active .session-item-meta {
  color: #d1d5db;
}

.session-time {
  font-weight: 400;
}

.session-count {
  font-weight: 500;
}
</style>
