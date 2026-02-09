import { ref, watch, nextTick, type Ref } from 'vue'

interface UseChatScrollOptions {
  /** 是否在消息变化时自动滚动到底部 */
  autoScroll?: boolean
  /** 是否在流式响应时保持滚动 */
  keepStreaming?: boolean
  /** 滚动行为的平滑度 */
  behavior?: ScrollBehavior
}

export function useChatScroll(
  containerRef: Ref<HTMLElement | null>,
  options: UseChatScrollOptions = {}
) {
  const {
    autoScroll = true,
    keepStreaming = true,
    behavior = 'smooth',
  } = options

  const isAutoScrolling = ref(false)
  const scrollTop = ref(0)
  const scrollHeight = ref(0)

  // 获取容器元素
  const getContainer = (): HTMLElement | null => {
    if (containerRef.value) return containerRef.value

    // 尝试查找默认容器
    const defaultContainer = document.querySelector('.ax-messages, .messages-container')
    return defaultContainer as HTMLElement | null
  }

  // 滚动到底部
  const scrollToBottom = (scrollBehavior: ScrollBehavior = behavior) => {
    nextTick(() => {
      const container = getContainer()
      if (!container) return

      // 如果用户已经滚动到上方，不要自动滚动
      if (!isAutoScrolling.value && keepStreaming) {
        const { scrollTop: top, scrollHeight: height, clientHeight } = container
        const isAtBottom = height - top - clientHeight < 100

        if (!isAtBottom) {
          // 用户不在底部，可能是自己在滚动
          return
        }
      }

      container.scrollTo({
        top: container.scrollHeight,
        behavior: scrollBehavior,
      })
    })
  }

  // 滚动到指定位置
  const scrollTo = (top: number, scrollBehavior: ScrollBehavior = behavior) => {
    nextTick(() => {
      const container = getContainer()
      if (!container) return

      container.scrollTo({
        top,
        behavior: scrollBehavior,
      })
    })
  }

  // 滚动到指定消息
  const scrollToMessage = (messageIndex: number) => {
    nextTick(() => {
      const container = getContainer()
      if (!container) return

      const messageElements = container.querySelectorAll('[data-message-index]')
      const targetElement = messageElements[messageIndex] as HTMLElement

      if (targetElement) {
        targetElement.scrollIntoView({
          behavior: behavior,
          block: 'center',
        })
      }
    })
  }

  // 检查是否在底部
  const isAtBottom = (): boolean => {
    const container = getContainer()
    if (!container) return true

    const { scrollTop: top, scrollHeight: height, clientHeight } = container
    return height - top - clientHeight < 50
  }

  // 设置用户滚动状态
  const setUserScrolling = (scrolling: boolean) => {
    isAutoScrolling.value = !scrolling
  }

  // 监听滚动事件
  const setupScrollListener = () => {
    const container = getContainer()
    if (!container) return

    const handleScroll = () => {
      scrollTop.value = container.scrollTop
      scrollHeight.value = container.scrollHeight

      // 检测用户是否主动滚动
      const atBottom = isAtBottom()
      if (!atBottom && keepStreaming) {
        isAutoScrolling.value = false
      }
    }

    container.addEventListener('scroll', handleScroll, { passive: true })

    return () => {
      container.removeEventListener('scroll', handleScroll)
    }
  }

  return {
    scrollToBottom,
    scrollTo,
    scrollToMessage,
    isAtBottom,
    setUserScrolling,
    setupScrollListener,
    scrollTop,
    scrollHeight,
  }
}
