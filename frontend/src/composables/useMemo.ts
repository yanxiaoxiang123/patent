import { ref, shallowRef, computed, watch, type Ref, type ComputedRef } from 'vue'

/**
 * 简单 memo 实现 - 缓存计算结果
 * @param fn 需要缓存的函数
 * @param deps 依赖数组
 * @returns 缓存的计算值
 */
export function useMemoized<T>(
  fn: () => T,
  deps: Ref<any>[] | ComputedRef<any>[]
): ComputedRef<T> {
  const cache = ref<T | null>(null)
  const lastDeps = ref<any[]>([])

  const value = computed(() => {
    const currentDeps = deps.map(d => d.value)

    // 检查依赖是否变化
    const hasChanged = lastDeps.value.length !== currentDeps.length ||
      lastDeps.value.some((dep, index) => dep !== currentDeps[index])

    if (hasChanged || cache.value === null) {
      cache.value = fn()
      lastDeps.value = currentDeps
    }

    return cache.value!
  })

  return value
}

/**
 * 节流函数
 * @param fn 需要节流的函数
 * @param delay 延迟时间（毫秒）
 */
export function useThrottle<T extends (...args: any[]) => any>(
  fn: T,
  delay: number = 300
): T {
  let lastCall = 0
  let timeoutId: ReturnType<typeof setTimeout> | null = null

  return ((...args: any[]) => {
    const now = Date.now()
    const remaining = delay - (now - lastCall)

    if (remaining <= 0 || remaining > delay) {
      if (timeoutId) {
        clearTimeout(timeoutId)
        timeoutId = null
      }
      lastCall = now
      return fn(...args)
    } else if (!timeoutId) {
      timeoutId = setTimeout(() => {
        lastCall = Date.now()
        timeoutId = null
        fn(...args)
      }, remaining)
    }
  }) as T
}

/**
 * 防抖函数
 * @param fn 需要防抖的函数
 * @param delay 延迟时间（毫秒）
 */
export function useDebounced<T extends (...args: any[]) => any>(
  fn: T,
  delay: number = 300
): T {
  let timeoutId: ReturnType<typeof setTimeout> | null = null

  return ((...args: any[]) => {
    if (timeoutId) {
      clearTimeout(timeoutId)
    }

    timeoutId = setTimeout(() => {
      timeoutId = null
      fn(...args)
    }, delay)
  }) as T
}

/**
 * 缓存大型对象（使用 shallowRef 避免深层响应式）
 */
export function useCached<T>(value: T): { cached: ComputedRef<T>, update: (newValue: T) => void } {
  const cache = shallowRef(value)

  return {
    cached: computed(() => cache.value),
    update: (newValue: T) => {
      cache.value = newValue
    },
  }
}

/**
 * 延迟执行 - 等待所有依赖稳定后再执行
 */
export function useDeferred<T>(
  fn: () => T,
  deps: Ref<any>[],
  options: { wait?: number } = {}
): { value: ComputedRef<T>, ready: Ref<boolean> } {
  const { wait = 0 } = options
  const ready = ref(false)
  const cache = ref<T | null>(null)

  let timeoutId: ReturnType<typeof setTimeout> | null = null

  watch(
    () => deps.map(d => d.value),
    (newDeps, oldDeps) => {
      // 依赖变化，重置 ready 状态
      if (timeoutId) {
        clearTimeout(timeoutId)
      }

      ready.value = false

      timeoutId = setTimeout(() => {
        cache.value = fn()
        ready.value = true
        timeoutId = null
      }, wait)
    },
    { immediate: true, deep: true }
  )

  return {
    value: computed(() => cache.value as T),
    ready,
  }
}

/**
 * 记忆化搜索结果
 */
export function useMemoizedSearch<T>(
  items: Ref<T[]>,
  searchFn: (query: string, items: T[]) => T[],
  options: { maxCacheSize?: number } = {}
) {
  const { maxCacheSize = 100 } = options
  const cache = ref<Map<string, T[]>>(new Map())

  const search = (query: string): T[] => {
    if (!query.trim()) {
      return items.value
    }

    // 检查缓存
    if (cache.value.has(query)) {
      return cache.value.get(query)!
    }

    // 执行搜索
    const results = searchFn(query, items.value)

    // 更新缓存
    if (cache.value.size >= maxCacheSize) {
      // 删除最旧的缓存项
      const firstKey = cache.value.keys().next().value
      cache.value.delete(firstKey)
    }
    cache.value.set(query, results)

    return results
  }

  const clearCache = () => {
    cache.value.clear()
  }

  return {
    search,
    clearCache,
  }
}
