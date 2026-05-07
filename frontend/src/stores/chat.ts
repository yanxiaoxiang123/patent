/**
 * 聊天状态管理 Store
 */

import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type { ChatMessage, ChatSession, FileAttachment, TemplateInfo } from "@/types";
import { generateSessionTitle } from "@/utils/chat/message";

export const useChatStore = defineStore("chat", () => {
  // ========== State ==========
  
  // 会话相关
  const sessions = ref<ChatSession[]>([]);
  const currentSessionId = ref<number | null>(null);
  const messages = ref<ChatMessage[]>([]);
  
  // 文件上传
  const uploadedFiles = ref<FileAttachment[]>([]);
  
  // UI 状态
  const showSidebar = ref(false);
  const isLoading = ref(false);
  const currentResponse = ref("");
  const currentTemplateId = ref<number | null>(null);
  
  // 设置
  const settings = ref({
    model: "qwen3:8b",
  });
  
  // 专利模板
  const templates = ref<TemplateInfo[]>([
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
  ]);

  // ========== Getters ==========
  
  const currentSession = computed(() => 
    sessions.value.find(s => s.id === currentSessionId.value)
  );
  
  const hasAttachments = computed(() => uploadedFiles.value.length > 0);
  
  const isAttachmentsReady = computed(() => {
    if (uploadedFiles.value.length === 0) return true;
    return uploadedFiles.value.every(file => file.parsed && !file.error);
  });
  
  const primaryTemplates = computed(() => templates.value.slice(0, 3));
  const secondaryTemplates = computed(() => templates.value.slice(3));

  // ========== Actions ==========
  
  /**
   * 添加消息
   */
  const addMessage = (message: ChatMessage) => {
    messages.value.push(message);
    saveToStorage();
  };
  
  /**
   * 更新最后一条消息
   */
  const updateLastMessage = (content: string) => {
    if (messages.value.length > 0) {
      const lastMsg = messages.value[messages.value.length - 1];
      lastMsg.content = content;
    }
  };
  
  /**
   * 清空消息
   */
  const clearMessages = () => {
    messages.value = [];
    currentResponse.value = "";
  };
  
  /**
   * 设置当前会话
   */
  const setCurrentSession = (sessionId: number | null) => {
    currentSessionId.value = sessionId;
    if (sessionId) {
      localStorage.setItem("currentSessionId", String(sessionId));
    } else {
      localStorage.removeItem("currentSessionId");
    }
  };
  
  /**
   * 添加上传文件
   */
  const addUploadedFile = (file: FileAttachment) => {
    uploadedFiles.value.push(file);
    saveToStorage();
  };
  
  /**
   * 更新上传文件
   */
  const updateUploadedFile = (fileId: number, updates: Partial<FileAttachment>) => {
    const index = uploadedFiles.value.findIndex(f => f.id === fileId);
    if (index !== -1) {
      uploadedFiles.value[index] = {
        ...uploadedFiles.value[index],
        ...updates,
      };
      saveToStorage();
    }
  };
  
  /**
   * 移除上传文件
   */
  const removeUploadedFile = (fileId: number | string) => {
    const index = uploadedFiles.value.findIndex(
      f => f.id === fileId || f.uid === String(fileId)
    );
    if (index !== -1) {
      uploadedFiles.value.splice(index, 1);
      saveToStorage();
    }
  };
  
  /**
   * 清空上传文件
   */
  const clearUploadedFiles = () => {
    uploadedFiles.value = [];
    saveToStorage();
  };
  
  /**
   * 保存当前会话
   */
  const saveCurrentSession = () => {
    if (messages.value.length === 0 || !currentSessionId.value) return;
    
    const sessionIndex = sessions.value.findIndex(s => s.id === currentSessionId.value);
    if (sessionIndex !== -1) {
      sessions.value[sessionIndex] = {
        ...sessions.value[sessionIndex],
        messages: [...messages.value],
        updatedAt: Date.now(),
        title: generateSessionTitle(messages.value),
        messageCount: messages.value.length,
      };
      saveToStorage();
    }
  };

  /**
   * 持久化到 localStorage
   */
  const saveToStorage = () => {
    try {
      // 保存会话 ID
      if (currentSessionId.value) {
        localStorage.setItem("currentSessionId", String(currentSessionId.value));
      }
      
      // 保存上传文件
      const fileData = uploadedFiles.value.map(file => ({
        id: file.id,
        name: file.name,
        type: file.type,
        parsed: !!file.parsed,
        parsedContent: file.parsedContent || file.parsed_content || null,
        error: !!file.error,
        parsingThinkingSteps: file.parsingThinkingSteps || [],
      }));
      localStorage.setItem("patent_uploaded_files", JSON.stringify(fileData));
    } catch {
      // 静默处理 localStorage 写入失败
    }
  };

  /**
   * 从 localStorage 加载
   */
  const loadFromStorage = () => {
    try {
      // 加载会话 ID
      const savedId = localStorage.getItem("currentSessionId");
      if (savedId) {
        currentSessionId.value = Number(savedId);
      }

      // 加载上传文件
      const savedFiles = localStorage.getItem("patent_uploaded_files");
      if (savedFiles) {
        const parsed = JSON.parse(savedFiles);
        if (Array.isArray(parsed)) {
          uploadedFiles.value = parsed;
        }
      }
    } catch {
      // 静默处理 localStorage 读取失败
    }
  };
  
  /**
   * 重置所有状态
   */
  const reset = () => {
    sessions.value = [];
    currentSessionId.value = null;
    messages.value = [];
    uploadedFiles.value = [];
    showSidebar.value = false;
    isLoading.value = false;
    currentResponse.value = "";
    currentTemplateId.value = null;
    
    localStorage.removeItem("currentSessionId");
    localStorage.removeItem("patent_uploaded_files");
  };
  
  return {
    // State
    sessions,
    currentSessionId,
    messages,
    uploadedFiles,
    showSidebar,
    isLoading,
    currentResponse,
    currentTemplateId,
    settings,
    templates,
    
    // Getters
    currentSession,
    hasAttachments,
    isAttachmentsReady,
    primaryTemplates,
    secondaryTemplates,
    
    // Actions
    addMessage,
    updateLastMessage,
    clearMessages,
    setCurrentSession,
    addUploadedFile,
    updateUploadedFile,
    removeUploadedFile,
    clearUploadedFiles,
    saveCurrentSession,
    saveToStorage,
    loadFromStorage,
    reset,
  };
});
