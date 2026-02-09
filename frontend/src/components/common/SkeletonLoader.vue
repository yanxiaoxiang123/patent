<template>
  <div class="skeleton-loader" :class="{ 'is-active': active }">
    <!-- 头像骨架 -->
    <div v-if="showAvatar" class="skeleton-avatar">
      <div class="skeleton-circle" />
    </div>

    <div class="skeleton-content">
      <!-- 用户名骨架 -->
      <div v-if="showHeader" class="skeleton-header">
        <div class="skeleton-line skeleton-title" :style="{ width: titleWidth }" />
      </div>

      <!-- 内容骨架 -->
      <div class="skeleton-body">
        <div
          v-for="(row, index) in rows"
          :key="index"
          class="skeleton-row"
          :class="{ 'skeleton-paragraph': row.type === 'paragraph' }"
        >
          <div
            v-if="row.lines"
            v-for="(line, lineIndex) in row.lines"
            :key="lineIndex"
            class="skeleton-line"
            :style="{
              width: line.width || (lineIndex === row.lines!.length - 1 ? '60%' : '100%'),
              height: line.height || '14px',
            }"
          />
        </div>
      </div>

      <!-- 附件骨架 -->
      <div v-if="showAttachments" class="skeleton-attachments">
        <div class="skeleton-attachment">
          <div class="skeleton-rect" />
          <div class="skeleton-line" style="width: 40%" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface SkeletonRow {
  type?: 'line' | 'paragraph'
  lines?: Array<{
    width?: string
    height?: string
  }>
}

interface Props {
  /** 是否激活动画 */
  active?: boolean
  /** 显示头像 */
  showAvatar?: boolean
  /** 显示头部（用户名等） */
  showHeader?: boolean
  /** 标题宽度 */
  titleWidth?: string
  /** 显示附件 */
  showAttachments?: boolean
  /** 行配置 */
  rows?: SkeletonRow[]
}

const props = withDefaults(defineProps<Props>(), {
  active: true,
  showAvatar: true,
  showHeader: true,
  titleWidth: '120px',
  showAttachments: false,
  rows: () => [
    { type: 'paragraph', lines: [{ width: '100%' }, { width: '85%' }, { width: '70%' }] },
  ],
})
</script>

<style scoped>
.skeleton-loader {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  max-width: 720px;
  margin: 0 auto;
}

.skeleton-content {
  flex: 1;
  min-width: 0;
}

.skeleton-avatar {
  flex-shrink: 0;
}

.skeleton-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(
    90deg,
    rgba(229, 231, 235, 0.4) 0%,
    rgba(229, 231, 235, 0.8) 50%,
    rgba(229, 231, 235, 0.4) 100%
  );
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite ease-in-out;
}

.skeleton-rect {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: linear-gradient(
    90deg,
    rgba(229, 231, 235, 0.4) 0%,
    rgba(229, 231, 235, 0.8) 50%,
    rgba(229, 231, 235, 0.4) 100%
  );
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite ease-in-out;
}

.skeleton-header {
  margin-bottom: 8px;
}

.skeleton-title {
  height: 16px;
  border-radius: 4px;
}

.skeleton-row {
  margin-bottom: 8px;
}

.skeleton-row:last-child {
  margin-bottom: 0;
}

.skeleton-line {
  height: 14px;
  border-radius: 4px;
  background: linear-gradient(
    90deg,
    rgba(229, 231, 235, 0.4) 0%,
    rgba(229, 231, 235, 0.8) 50%,
    rgba(229, 231, 235, 0.4) 100%
  );
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite ease-in-out;
}

.skeleton-attachments {
  margin-top: 14px;
  padding: 10px 12px;
  background: rgba(248, 250, 252, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 10px;
}

.skeleton-attachment {
  display: flex;
  align-items: center;
  gap: 10px;
}

.skeleton-attachment .skeleton-line {
  height: 14px;
  width: 60%;
  margin-top: 0;
}

.skeleton-loader.is-active .skeleton-line,
.skeleton-loader.is-active .skeleton-circle,
.skeleton-loader.is-active .skeleton-rect {
  animation: skeleton-loading 1.5s infinite ease-in-out;
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
    opacity: 0.6;
  }
  100% {
    background-position: -200% 0;
    opacity: 1;
  }
}
</style>
