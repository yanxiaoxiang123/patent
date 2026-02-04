/**
 * 本地存储 composable
 */

import { ref, watch, onMounted } from "vue";
import type { Ref } from "vue";

export function useLocalStorage<T>(key: string, defaultValue: T) {
  const value: Ref<T> = ref(defaultValue) as Ref<T>;

  /**
   * 从 localStorage 加载
   */
  const load = () => {
    try {
      const saved = localStorage.getItem(key);
      if (saved) {
        value.value = JSON.parse(saved);
      }
    } catch (error) {
      console.error(`Failed to load ${key}:`, error);
    }
  };

  /**
   * 保存到 localStorage
   */
  const save = () => {
    try {
      localStorage.setItem(key, JSON.stringify(value.value));
    } catch (error) {
      console.error(`Failed to save ${key}:`, error);
    }
  };

  /**
   * 清除 localStorage
   */
  const clear = () => {
    try {
      localStorage.removeItem(key);
      value.value = defaultValue;
    } catch (error) {
      console.error(`Failed to clear ${key}:`, error);
    }
  };

  // 监听变化自动保存
  watch(value, save, { deep: true });

  // 初始化加载
  onMounted(load);

  return { value, load, save, clear };
}
