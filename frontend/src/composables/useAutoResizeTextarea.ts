import { ref, watch, type Ref, type ComputedRef } from "vue";

interface UseAutoResizeTextareaOptions {
  /** 最大高度（像素） */
  maxRows?: number;
  /** 最小行数 */
  minRows?: number;
  /** 行高（像素） */
  lineHeight?: number;
}

export function useAutoResizeTextarea(
  textareaRef: Ref<HTMLTextAreaElement | null>,
  contentRef: Ref<string> | ComputedRef<string>,
  options: UseAutoResizeTextareaOptions = {},
) {
  const { maxRows = 8, minRows = 1, lineHeight = 24 } = options;

  const lineHeightNumber = lineHeight;

  const getComputedHeight = (rows: number): number => {
    return rows * lineHeightNumber;
  };

  const resize = () => {
    const textarea = textareaRef.value;
    if (!textarea) return;

    // 重置高度以获取正确的scrollHeight
    textarea.style.height = "auto";

    // 计算行数
    const content = textarea.value || textarea.placeholder || "";
    const lines = content.split("\n").length;
    const rows = Math.max(minRows, Math.min(lines, maxRows));

    // 计算高度
    const newHeight = getComputedHeight(rows);
    textarea.style.height = `${Math.max(newHeight, getComputedHeight(minRows))}px`;

    // 如果内容超过最大行数，启用滚动
    const hasOverflow = textarea.scrollHeight > newHeight;
    textarea.style.overflowY = hasOverflow ? "auto" : "hidden";
  };

  // 监听内容变化
  if ("value" in contentRef) {
    watch(
      () => (contentRef as Ref<string>).value,
      () => resize(),
      { flush: "post" },
    );
  }

  // 初始化
  const init = () => {
    nextTick(() => {
      resize();
    });
  };

  return {
    resize,
    init,
    getComputedHeight,
  };
}

// 便捷函数：手动输入处理
export function useTextareaInput(
  textareaRef: Ref<HTMLTextAreaElement | null>,
  emit: (event: "update:modelValue", value: string) => void,
) {
  const handleInput = (event: Event) => {
    const target = event.target as HTMLTextAreaElement;
    emit("update:modelValue", target.value);
  };

  const handleKeydown = (
    event: KeyboardEvent,
    options?: {
      onEnter?: () => void;
      onCtrlEnter?: () => void;
      onShiftEnter?: () => void;
    },
  ) => {
    const { onEnter, onCtrlEnter, onShiftEnter } = options || {};

    if (event.key === "Enter") {
      if (event.shiftKey) {
        // Shift + Enter: 允许换行
        onShiftEnter?.();
      } else if (event.ctrlKey) {
        // Ctrl + Enter: 换行
        event.preventDefault();
        onCtrlEnter?.();
      } else {
        // Enter: 发送
        event.preventDefault();
        onEnter?.();
      }
    }
  };

  const handlePaste = (
    event: ClipboardEvent,
    handleFiles?: (files: File[]) => void,
  ) => {
    const items = event.clipboardData?.items;
    if (!items) return;

    const files: File[] = [];
    for (const item of items) {
      if (item.type.startsWith("image/") || item.type.includes("document")) {
        const file = item.getAsFile();
        if (file) files.push(file);
      }
    }

    if (files.length > 0 && handleFiles) {
      handleFiles(files);
    }
  };

  return {
    handleInput,
    handleKeydown,
    handlePaste,
  };
}
