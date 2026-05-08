import { ref } from "vue";
import { ElMessage } from "element-plus";

interface UseClipboardOptions {
  /** 成功消息 */
  successMessage?: string;
  /** 失败消息 */
  errorMessage?: string;
  /** 成功后自动隐藏的延迟时间（毫秒） */
  duration?: number;
}

export function useClipboard(options: UseClipboardOptions = {}) {
  const {
    successMessage = "已复制到剪贴板",
    errorMessage = "复制失败，请手动选择复制",
    duration = 2000,
  } = options;

  const copied = ref(false);
  const error = ref<Error | null>(null);

  // 使用现代 Clipboard API
  const copy = async (text: string): Promise<boolean> => {
    if (!text) {
      ElMessage.warning("没有可复制的内容");
      return false;
    }

    try {
      // 优先使用 Clipboard API
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        // 降级方案：使用传统的复制方法
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }

      copied.value = true;
      error.value = null;

      // 显示成功消息
      ElMessage.success(successMessage);

      // 重置状态
      setTimeout(() => {
        copied.value = false;
      }, duration);

      return true;
    } catch (err) {
      error.value = err as Error;
      copied.value = false;

      // 显示错误消息
      ElMessage.error(errorMessage);

      return false;
    }
  };

  // 复制 HTML 内容
  const copyHtml = async (html: string, text?: string): Promise<boolean> => {
    try {
      if (navigator.clipboard && navigator.clipboard.write) {
        const blobHtml = new Blob([html], { type: "text/html" });
        const blobText = new Blob([text || html], { type: "text/plain" });
        const data = [
          new ClipboardItem({
            "text/html": blobHtml,
            "text/plain": blobText,
          }),
        ];

        await navigator.clipboard.write(data);
      } else {
        // 降级方案
        return copy(text || html);
      }

      copied.value = true;
      ElMessage.success(successMessage);

      setTimeout(() => {
        copied.value = false;
      }, duration);

      return true;
    } catch (err) {
      error.value = err as Error;
      ElMessage.error(errorMessage);
      return false;
    }
  };

  // 复制文件（用于下载）
  const copyFile = async (file: File): Promise<boolean> => {
    try {
      if (navigator.clipboard && navigator.clipboard.write) {
        const blob = new Blob([file], { type: file.type });
        const data = [
          new ClipboardItem({
            [file.type]: blob,
          }),
        ];

        await navigator.clipboard.write(data);
      }

      copied.value = true;
      ElMessage.success("文件引用已复制");

      setTimeout(() => {
        copied.value = false;
      }, duration);

      return true;
    } catch (err) {
      error.value = err as Error;
      ElMessage.error("复制失败");
      return false;
    }
  };

  return {
    copied,
    error,
    copy,
    copyHtml,
    copyFile,
  };
}
