<template>
  <div class="chat-top-bar">
    <div class="chat-brand">
      <img class="chat-logo-dot" :src="logoSrc" alt="Logo" />
      <div class="chat-brand-text">
        <div class="chat-brand-title">{{ title }}</div>
      </div>
    </div>
    <div class="chat-actions">
      <slot name="actions">
        <el-button
          v-if="showAdminButton && isAdmin"
          type="default"
          size="small"
          @click="handleAdminClick"
        >
          用户管理
        </el-button>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title?: string;
  logoSrc?: string;
  isAdmin?: boolean;
  showAdminButton?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  title: "专利 AI 助手",
  logoSrc: "/0.png",
  isAdmin: false,
  showAdminButton: true,
});

const emit = defineEmits<{
  adminClick: [];
}>();

const handleAdminClick = () => {
  emit("adminClick");
};
</script>

<style scoped>
.chat-top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: rgba(255, 255, 255, 0.95);
  border-bottom: 1px solid rgba(226, 232, 240, 0.6);
  backdrop-filter: blur(12px);
  z-index: 10;
}

.chat-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-logo-dot {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  object-fit: cover;
}

.chat-brand-text {
  display: flex;
  flex-direction: column;
}

.chat-brand-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  letter-spacing: -0.01em;
}

.chat-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
