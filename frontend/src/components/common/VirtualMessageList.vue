<template>
  <div
    ref="containerRef"
    class="virtual-message-list"
    :style="{ height: `${containerHeight}px` }"
    role="log"
    aria-label="消息列表"
    aria-live="polite"
  >
    <div
      :style="{ height: `${totalSize}px`, position: 'relative' }"
      class="virtual-spacer"
    >
      <div
        v-for="virtualItem in virtualItems"
        :key="virtualItem.key"
        :style="{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: `${virtualItem.size}px`,
          transform: `translateY(${virtualItem.start}px)`,
        }"
        class="virtual-item"
        :data-index="virtualItem.index"
        :data-message-key="virtualItem.key"
      >
        <slot
          name="item"
          :item="getMessageItem(virtualItem.index)"
          :index="virtualItem.index"
        />
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="items.length === 0" class="virtual-empty">
      <slot name="empty">
        <div class="empty-content">
          <el-icon size="48" color="#d1d5db"><ChatDotRound /></el-icon>
          <p>暂无消息</p>
        </div>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ChatDotRound } from '@element-plus/icons-vue'

interface VirtualItem {
  key: string | number
  index: number
  start: number
  size: number
}

interface Props {
  /** 消息列表 */
  items: any[]
  /** 容器高度（像素） */
  containerHeight?: number
  /** 估算的项目高度（像素） */
  estimateSize?: number
  /** 预渲染的项目数量 */
  overscan?: number
  /** 键提取函数 */
  keyField?: string
}

const props = withDefaults(defineProps<Props>(), {
  containerHeight: 400,
  estimateSize: 100,
  overscan: 5,
  keyField: 'id',
})

const emit = defineEmits<{
  'scroll-to-index': [index: number]
}>()

const containerRef = ref<HTMLElement | null>(null)
const scrollTop = ref(0)

// 虚拟滚动状态
const state = ref({
  start: 0,
  end: 0,
})

// 计算虚拟项
const virtualItems = computed((): VirtualItem[] => {
  if (props.items.length === 0) return []

  const { estimateSize, overscan } = props
  const count = props.items.length

  // 计算可视范围
  let start = Math.max(0, Math.floor(scrollTop.value / estimateSize) - overscan)
  let end = Math.min(count, Math.ceil((scrollTop.value + props.containerHeight) / estimateSize) + overscan)

  // 生成虚拟项
  const items: VirtualItem[] = []
  for (let i = start; i < end; i++) {
    const key = props.items[i]?.[props.keyField] || i
    items.push({
      key,
      index: i,
      start: i * estimateSize,
      size: estimateSize,
    })
  }

  return items
})

// 总高度
const totalSize = computed(() => {
  return props.items.length * props.estimateSize
})

// 根据索引获取消息项
const getMessageItem = (index: number) => {
  return props.items[index]
}

// 滚动处理
const handleScroll = () => {
  if (!containerRef.value) return
  scrollTop.value = containerRef.value.scrollTop
}

const setupScrollListener = () => {
  containerRef.value?.addEventListener('scroll', handleScroll, { passive: true })
}

const removeScrollListener = () => {
  containerRef.value?.removeEventListener('scroll', handleScroll)
}

// 滚动到指定索引
const scrollToIndex = (index: number, behavior: ScrollBehavior = 'smooth') => {
  if (index < 0 || index >= props.items.length) return

  nextTick(() => {
    if (!containerRef.value) return

    const targetScrollTop = index * props.estimateSize
    containerRef.value.scrollTo({
      top: targetScrollTop,
      behavior,
    })

    emit('scroll-to-index', index)
  })
}

// 滚动到底部
const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
  nextTick(() => {
    if (!containerRef.value) return
    containerRef.value.scrollTo({
      top: containerRef.value.scrollHeight,
      behavior,
    })
  })
}

// 检查是否在底部
const isAtBottom = (threshold: number = 50): boolean => {
  if (!containerRef.value) return true

  const { scrollTop: top, scrollHeight: height, clientHeight } = containerRef.value
  return height - top - clientHeight < threshold
}

// 监听 items 变化
watch(
  () => props.items.length,
  () => {
    nextTick(() => {
      if (isAtBottom(100)) {
        scrollToBottom()
      }
    })
  }
)

onMounted(() => {
  setupScrollListener()
})

onUnmounted(() => {
  removeScrollListener()
})

// 暴露方法给父组件
defineExpose({
  scrollToIndex,
  scrollToBottom,
  isAtBottom,
  containerRef,
})
</script>

<style scoped>
.virtual-message-list {
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
  -webkit-overflow-scrolling: touch;
}

.virtual-spacer {
  min-height: 100%;
}

.virtual-item {
  will-change: transform;
}

.virtual-empty {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #9ca3af;
}

.empty-content p {
  margin: 0;
  font-size: 14px;
}
</style>
