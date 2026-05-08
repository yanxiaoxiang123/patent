<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts"></script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,500;8..60,600&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

:root {
  /* Warm Terracotta Palette */
  --primary-color: #C97B5D;
  --primary-hover: #A85D3E;
  --primary-light: #E8C4B4;
  --primary-pale: #FDF6F2;
  --accent: #8B5A3C;

  /* Backgrounds */
  --bg-primary: #FDFBF8;
  --bg-secondary: #F7F3EE;
  --bg-tertiary: #EDE8E2;
  --bg-hover: #E8E0D8;

  /* Text */
  --text-primary: #2C2420;
  --text-secondary: #5C524A;
  --text-muted: #8B8279;

  /* Borders & Shadows */
  --border-color: #E0D8D0;
  --border-light: #EDE8E2;
  --border-accent: #D4C4B8;
  --shadow-sm: 0 1px 3px rgba(44, 36, 32, 0.06);
  --shadow-md: 0 4px 12px rgba(44, 36, 32, 0.08);
  --shadow-lg: 0 8px 28px rgba(44, 36, 32, 0.12);

  /* Border Radius */
  --radius-sm: 6px;
  --radius-md: 12px;
  --radius-lg: 18px;
  --radius-xl: 24px;
  --radius-full: 9999px;

  /* Typography */
  --font-display: 'Source Serif 4', Georgia, serif;
  --font-body: 'IBM Plex Sans', -apple-system, sans-serif;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: var(--font-body);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height: 100vh;
  background-color: var(--bg-secondary);
  color: var(--text-primary);
}

/* Global Element Plus Button Overrides */
.el-button {
  font-family: var(--font-body);
  font-weight: 500;
  border-radius: var(--radius-md) !important;
  transition: all 0.18s ease !important;
}

.el-button--primary {
  background: linear-gradient(135deg, var(--primary-color), var(--accent)) !important;
  border: none !important;
  box-shadow: 0 2px 8px rgba(201, 123, 93, 0.25) !important;
}

.el-button--primary:hover {
  background: linear-gradient(135deg, var(--primary-hover), var(--accent)) !important;
  box-shadow: 0 4px 12px rgba(201, 123, 93, 0.35) !important;
  transform: translateY(-1px);
}

.el-button--default {
  border-color: var(--border-color) !important;
  background: var(--bg-primary) !important;
  color: var(--text-primary) !important;
}

.el-button--default:hover {
  border-color: var(--primary-light) !important;
  color: var(--primary-color) !important;
  background: var(--primary-pale) !important;
}

.el-button--danger {
  background: #dc2626 !important;
  border: none !important;
}

.el-button--danger:hover {
  background: #b91c1c !important;
}

.el-button--warning {
  background: #f59e0b !important;
  border: none !important;
  color: #fff !important;
}

.el-button--warning:hover {
  background: #d97706 !important;
}

.el-button--success {
  background: #16a34a !important;
  border: none !important;
}

.el-button--success:hover {
  background: #15803d !important;
}

.el-button--small {
  padding: 6px 14px !important;
  font-size: 12px !important;
}

.el-button--small.is-circle {
  padding: 6px !important;
}

.el-button--text {
  color: var(--text-secondary) !important;
}

.el-button--text:hover {
  color: var(--primary-color) !important;
  background: var(--primary-pale) !important;
}

/* Element Plus Input Overrides */
.el-input__wrapper {
  border-radius: var(--radius-md) !important;
  box-shadow: none !important;
  border: 1px solid var(--border-color) !important;
  background: var(--bg-secondary) !important;
  transition: all 0.18s ease !important;
}

.el-input__wrapper:hover {
  border-color: var(--border-accent) !important;
}

.el-input__wrapper.is-focus {
  border-color: var(--primary-color) !important;
  background: var(--bg-primary) !important;
  box-shadow: 0 0 0 3px rgba(201, 123, 93, 0.12) !important;
}

.el-input__inner {
  font-family: var(--font-body) !important;
}

/* Element Plus Select Overrides */
.el-select__wrapper {
  border-radius: var(--radius-md) !important;
  box-shadow: none !important;
  border: 1px solid var(--border-color) !important;
  background: var(--bg-secondary) !important;
}

.el-select__wrapper:hover {
  border-color: var(--border-accent) !important;
}

.el-select__wrapper.is-focused {
  border-color: var(--primary-color) !important;
  box-shadow: 0 0 0 3px rgba(201, 123, 93, 0.12) !important;
}

/* Element Plus Dialog Overrides */
.el-dialog {
  border-radius: var(--radius-xl) !important;
  overflow: hidden;
}

.el-dialog__header {
  font-family: var(--font-display) !important;
  padding: 20px 24px 16px !important;
  border-bottom: 1px solid var(--border-light) !important;
}

.el-dialog__title {
  font-size: 16px !important;
  font-weight: 600 !important;
  color: var(--text-primary) !important;
}

.el-dialog__body {
  padding: 20px 24px !important;
}

.el-dialog__footer {
  padding: 16px 24px 20px !important;
  border-top: 1px solid var(--border-light) !important;
}

/* Element Plus Tag Overrides */
.el-tag {
  border-radius: var(--radius-full) !important;
  font-family: var(--font-body) !important;
}

/* Element Plus Table Overrides */
.el-table {
  border-radius: var(--radius-lg) !important;
  overflow: hidden;
}

.el-table th {
  background: var(--bg-tertiary) !important;
  font-weight: 600 !important;
  color: var(--text-primary) !important;
}

.el-table td {
  border-bottom: 1px solid var(--border-light) !important;
}

/* Element Plus Pagination */
.el-pagination {
  font-family: var(--font-body) !important;
}

/* Element Plus Dropdown */
.el-dropdown-menu {
  border-radius: var(--radius-md) !important;
  box-shadow: var(--shadow-lg) !important;
  border: 1px solid var(--border-color) !important;
}

.el-dropdown-menu__item {
  font-family: var(--font-body) !important;
}

/* Ant Design Vue Overrides */
.ant-btn {
  font-family: var(--font-body) !important;
  border-radius: var(--radius-md) !important;
  transition: all 0.18s ease !important;
}

.ant-btn-primary {
  background: linear-gradient(135deg, var(--primary-color), var(--accent)) !important;
  border: none !important;
  box-shadow: 0 2px 8px rgba(201, 123, 93, 0.25) !important;
}

.ant-btn-primary:hover {
  background: linear-gradient(135deg, var(--primary-hover), var(--accent)) !important;
  box-shadow: 0 4px 12px rgba(201, 123, 93, 0.35) !important;
}

.ant-btn-default {
  border-color: var(--border-color) !important;
  background: var(--bg-primary) !important;
  color: var(--text-primary) !important;
}

.ant-btn-default:hover {
  border-color: var(--primary-light) !important;
  color: var(--primary-color) !important;
  background: var(--primary-pale) !important;
}

.ant-btn-text {
  color: var(--text-secondary) !important;
}

.ant-btn-text:hover {
  color: var(--primary-color) !important;
  background: var(--primary-pale) !important;
}

.ant-btn-circle {
  border-radius: 50% !important;
}

/* Ant Design Badge */
.ant-badge-status-dot {
  background: var(--primary-color) !important;
}

/* Ant Design Typography */
.ant-typography {
  color: var(--text-primary) !important;
}

.ant-typography-secondary {
  color: var(--text-secondary) !important;
}

/* Ant Design Flex */
.ant-flex {
  font-family: var(--font-body) !important;
}

/* ant-design-x-vue Sender Component */
.ax-sender {
  font-family: var(--font-body) !important;
}

/* ant-design-x-vue Conversations */
.ax-conversations-item {
  font-family: var(--font-body) !important;
}

/* ant-design-x-vue Prompts */
.ax-prompts-item {
  font-family: var(--font-body) !important;
}

/* ant-design-x-vue Attachments */
.ax-attachments {
  font-family: var(--font-body) !important;
}

.ax-attachments :deep(.ant-upload-drag) {
  border-color: var(--border-color) !important;
  background: var(--bg-primary) !important;
}

.ax-attachments :deep(.ant-upload-drag:hover) {
  border-color: var(--primary-light) !important;
}

/* Ant Design Icons */
.anticon {
  color: var(--text-secondary);
}

/* Element Plus Icons */
.el-icon {
  color: var(--text-secondary);
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--border-accent);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}
</style>
