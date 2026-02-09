<template>
  <component :is="renderContent" />
</template>

<script setup lang="ts">
import { ref, defineComponent, h, onErrorCaptured, type Component } from 'vue'

interface Props {
  /** 错误回调 */
  onError?: (error: Error, info: string) => void
  /** 降级 UI 组件 */
  fallback?: Component
  /** 是否显示错误详情 */
  showDetails?: boolean
  /** 重试按钮文字 */
  retryText?: string
}

const props = withDefaults(defineProps<Props>(), {
  showDetails: false,
  retryText: '重试',
})

const emit = defineEmits<{
  'error': [error: Error, info: string]
}>()

const error = ref<Error | null>(null)
const errorInfo = ref<string>('')

// 默认错误降级组件
const DefaultFallback = defineComponent({
  props: {
    error: { type: Object, required: true },
    retryText: { type: String, default: '重试' },
    showDetails: { type: Boolean, default: false },
  },
  emits: ['retry'],
  setup(props, { emit }) {
    return () => h('div', {
      class: 'error-fallback',
      role: 'alert',
    }, [
      h('div', { class: 'error-icon' }, '⚠️'),
      h('h3', { class: 'error-title' }, '出错了'),
      h('p', { class: 'error-message' }, props.error?.message || '未知错误'),
      props.showDetails && props.error?.stack
        ? h('pre', { class: 'error-stack' }, props.error.stack)
        : null,
      h('button', {
        class: 'error-retry-btn',
        onClick: () => emit('retry'),
      }, props.retryText),
    ])
  },
})

// 捕获子组件错误
onErrorCaptured((err, instance, info) => {
  error.value = err
  errorInfo.value = info
  props.onError?.(err, info)
  emit('error', err, info)
  // 返回 false 阻止错误继续传播
  return false
})

// 重置错误状态
const reset = () => {
  error.value = null
  errorInfo.value = ''
}

// 渲染内容
const renderContent = () => {
  if (error.value) {
    const FallbackComponent = props.fallback || DefaultFallback
    return h(FallbackComponent, {
      error: error.value,
      retryText: props.retryText,
      showDetails: props.showDetails,
      onRetry: reset,
    })
  }
  return h('template', {}, slots.default?.())
}

// 暴露方法给父组件
defineExpose({
  reset,
  error,
  errorInfo,
})
</script>

<style scoped>
.error-fallback {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  text-align: center;
  background: rgba(254, 242, 242, 0.9);
  border: 1px solid rgba(254, 202, 202, 0.5);
  border-radius: 12px;
  margin: 16px 0;
}

.error-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.error-title {
  font-size: 18px;
  font-weight: 600;
  color: #dc2626;
  margin: 0 0 8px;
}

.error-message {
  font-size: 14px;
  color: #7f1d1d;
  margin: 0 0 12px;
  max-width: 400px;
}

.error-stack {
  font-size: 12px;
  color: #9ca3af;
  background: rgba(0, 0, 0, 0.05);
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  max-width: 100%;
  max-height: 200px;
  text-align: left;
  margin: 0 0 12px;
}

.error-retry-btn {
  padding: 8px 20px;
  background: #dc2626;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.error-retry-btn:hover {
  background: #b91c1c;
}
</style>
