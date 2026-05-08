/**
 * 模板选择器 composable
 * 管理专利审核模板定义、选择和辅助消息构建
 */
import { ref, computed } from "vue";
import type { TemplateInfo } from "@/types";

const TEMPLATES: TemplateInfo[] = [
  {
    id: 1,
    title: "普通案例审核",
    icon: "Document",
    description: "对上传的普通案例进行审核并给出建议",
    prompt: "",
  },
  {
    id: 3,
    title: "专案案例审核",
    icon: "EditPen",
    description: "对上传的专案案例进行审核并输出报告",
    prompt: "",
  },
  {
    id: 2,
    title: "专利审核指导",
    icon: "EditPen",
    description: "学习专利申请文件的审核技巧",
    prompt: "根据我刚刚上传的文件，帮我进行专利审核",
  },
  {
    id: 5,
    title: "IPC 分类指导",
    icon: "Shield",
    description: "根据技术方案选择合适的专利 IPC 分类号",
    prompt:
      "我有一个专利申请书，请帮我分析应该归入哪些 IPC 分类号，并说明每个分类号的含义和选择理由。",
  },
];

export function useTemplateSelector() {
  const activeTemplateId = ref<number | null>(null);
  const templates = ref<TemplateInfo[]>([...TEMPLATES]);

  const primaryTemplates = computed(() => templates.value.slice(0, 3));
  const secondaryTemplates = computed(() => templates.value.slice(3));

  const placeholderPromptsItems = computed(() =>
    [...primaryTemplates.value, ...secondaryTemplates.value].map((t) => ({
      key: String(t.id),
      label: t.title,
      description: t.description || "",
    }))
  );

  const placeholderPromptsStyles = { list: { width: "100%" }, item: { flex: 1 } };

  function getTemplateById(id: number | string): TemplateInfo | undefined {
    return templates.value.find((t) => String(t.id) === String(id));
  }

  function isStrictTemplate(id: number | null): boolean {
    return id === 1 || id === 3;
  }

  function isIPCTemplate(id: number | null): boolean {
    return id === 5;
  }

  /**
   * 根据模板ID和是否有文字输入，生成要发送给AI的消息内容
   */
  function buildMessageContent(
    templateId: number | null,
    hasText: boolean,
    userText?: string
  ): string {
    if (hasText) return userText || "";

    if (isIPCTemplate(templateId)) {
      return "请根据我上传的专利文档内容，帮我进行 IPC 分类，并说明每个分类号的含义和选择理由。";
    }

    if (isStrictTemplate(templateId)) {
      return "";
    }

    return "请根据我刚刚上传的专利文档，先给出整体概览、关键创新点和主要风险点的审核意见。";
  }

  /**
   * 根据模板ID和消息内容生成显示文本（用户可见的消息气泡文本）
   */
  function buildDisplayContent(
    templateId: number | null,
    hasText: boolean,
    hasAttachments: boolean,
    messageContent: string
  ): string {
    const isPureAttachment = !hasText && hasAttachments;
    const isStrict = isStrictTemplate(templateId);

    if (isPureAttachment && isStrict) {
      return "（已上传文档，按模板审核）";
    }
    return messageContent || "请根据上传的文档给出审核建议";
  }

  function selectTemplate(id: number) {
    activeTemplateId.value = id;
  }

  function clearSelection() {
    activeTemplateId.value = null;
  }

  return {
    activeTemplateId,
    templates,
    primaryTemplates,
    secondaryTemplates,
    placeholderPromptsItems,
    placeholderPromptsStyles,
    getTemplateById,
    isStrictTemplate,
    isIPCTemplate,
    buildMessageContent,
    buildDisplayContent,
    selectTemplate,
    clearSelection,
  };
}