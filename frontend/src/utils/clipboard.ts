/**
 * 剪贴板工具
 */

/**
 * 复制文本到剪贴板
 */
export async function copyToClipboard(text: string): Promise<void> {
  const content = typeof text === "string" ? text : "";
  if (!content) {
    throw new Error("empty");
  }

  // 优先使用现代 Clipboard API
  if (window.isSecureContext && navigator?.clipboard?.writeText) {
    await navigator.clipboard.writeText(content);
    return;
  }

  // 降级方案：使用 textarea
  const textarea = document.createElement("textarea");
  textarea.value = content;
  textarea.setAttribute("readonly", "true");
  textarea.style.position = "fixed";
  textarea.style.left = "-9999px";
  textarea.style.top = "0";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();
  textarea.setSelectionRange(0, textarea.value.length);

  const ok = document.execCommand("copy");
  document.body.removeChild(textarea);

  if (!ok) {
    throw new Error("copy_failed");
  }
}
