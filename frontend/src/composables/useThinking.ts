/**
 * 思考过程处理 composable
 */

import { ref, computed } from "vue";
import type { Ref, ComputedRef } from "vue";
import { splitThinking, hasThinkingStructure } from "@/utils/chat/thinking";
import type { ThinkingParts } from "@/utils/chat/thinking";

export function useThinking() {
  // 思考过程展开状态（按消息索引）
  const thinkingExpanded = ref<Record<number, boolean>>({});
  
  // 流式响应中的思考过程展开状态
  const streamingThinkingExpanded = ref(true);

  /**
   * 切换思考过程展开状态
   */
  const toggleThinking = (index: number) => {
    thinkingExpanded.value = {
      ...thinkingExpanded.value,
      [index]: !thinkingExpanded.value[index],
    };
  };

  /**
   * 检查思考过程是否展开
   */
  const isThinkingVisible = (index: number): boolean => {
    return !!thinkingExpanded.value[index];
  };

  /**
   * 切换流式响应思考过程展开状态
   */
  const toggleStreamingThinking = () => {
    streamingThinkingExpanded.value = !streamingThinkingExpanded.value;
  };

  /**
   * 重置所有展开状态
   */
  const resetThinkingStates = () => {
    thinkingExpanded.value = {};
    streamingThinkingExpanded.value = true;
  };

  return {
    thinkingExpanded,
    streamingThinkingExpanded,
    toggleThinking,
    isThinkingVisible,
    toggleStreamingThinking,
    resetThinkingStates,
    splitThinking,
    hasThinkingStructure,
  };
}
