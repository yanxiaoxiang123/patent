/**
 * 会话管理 composable
 */

import { ref, computed } from "vue";
import api from "@/services/api";
import { ElMessage } from "element-plus";
import type { ChatSession, ChatMessage } from "@/types";
import { generateSessionTitle } from "@/utils/chat/message";

export function useChatSession() {
  const sessions = ref<ChatSession[]>([]);
  const currentSessionId = ref<number | null>(null);
  const messages = ref<ChatMessage[]>([]);
  const loading = ref(false);

  const currentSession = computed(() =>
    sessions.value.find((s) => s.id === currentSessionId.value)
  );

  /**
   * 加载所有会话
   */
  const loadSessions = async () => {
    try {
      loading.value = true;
      const data = await api.get("/ai/sessions");
      const loadedSessions: ChatSession[] = [];

      for (const s of data) {
        const lastTime = s.last_message_at || s.updated_at || s.created_at;

        loadedSessions.push({
          id: s.id,
          title: s.title || "新对话",
          messages: [],  // 不在这里加载消息，等用户点击时再按需加载
          createdAt: s.created_at ? new Date(s.created_at).getTime() : null,
          updatedAt: lastTime ? new Date(lastTime).getTime() : null,
          messageCount: typeof s.message_count === "number" ? s.message_count : 0,
        });
      }

      sessions.value = loadedSessions;
    } catch (error) {
      console.error("加载聊天记录失败:", error);
      sessions.value = [];
    } finally {
      loading.value = false;
    }
  };

  /**
   * 获取会话消息
   */
  const fetchSessionMessages = async (sessionId: number): Promise<ChatMessage[]> => {
    try {
      const data = await api.get(`/ai/sessions/${sessionId}`);

      // 获取会话关联的文档信息
      let documentInfo: any = null;
      if (data.document_id) {
        try {
          const docData = await api.get(`/documents/${data.document_id}`);
          documentInfo = docData;
        } catch (e) {
          console.warn("获取文档信息失败:", e);
        }
      }

      // 构建附件信息
      const getAttachments = (msgDocumentId: number | null): any[] => {
        if (!msgDocumentId || !documentInfo) return [];
        return [{
          id: documentInfo.id,
          name: documentInfo.title || `文档-${msgDocumentId}`,
          type: documentInfo.file_type || "docx",
          size: documentInfo.file_size || 0,
          parsed: documentInfo.status === "parsed" || documentInfo.status === "completed",
          parsedContent: documentInfo.parsed_content || null,
          parsed_content: documentInfo.parsed_content || null,
        }];
      };

      const list: ChatMessage[] = (data.messages || []).map((item: any) => ({
        role: item.role,
        content: item.content || "",
        fullContent: item.content || "",
        timestamp: item.created_at ? new Date(item.created_at) : new Date(),
        attachments: item.role === "user" ? getAttachments(item.document_id) : undefined,
      }));

      const sessionIndex = sessions.value.findIndex((s) => s.id === sessionId);
      if (sessionIndex !== -1) {
        // 根据消息内容重新生成标题
        const generatedTitle = generateSessionTitle(list);
        sessions.value[sessionIndex] = {
          ...sessions.value[sessionIndex],
          messages: list,
          messageCount: list.length,
          title: generatedTitle,
        };
      }
      return list;
    } catch (error) {
      console.error("加载会话消息失败:", error);
      ElMessage.error("加载会话消息失败，请稍后重试");
      return [];
    }
  };

  /**
   * 切换会话
   */
  const switchSession = async (sessionId: number) => {
    const session = sessions.value.find((s) => s.id === sessionId);
    if (!session) return;

    currentSessionId.value = sessionId;
    localStorage.setItem("currentSessionId", String(sessionId));

    if (!session.messages || session.messages.length === 0) {
      const list = await fetchSessionMessages(sessionId);
      messages.value = [...list];
    } else {
      messages.value = [...session.messages];
    }
  };

  /**
   * 创建新会话
   */
  const createSession = () => {
    currentSessionId.value = null;
    messages.value = [];
    localStorage.removeItem("currentSessionId");
  };

  /**
   * 删除会话
   */
  const deleteSession = async (sessionId: number) => {
    try {
      await api.delete(`/ai/sessions/${sessionId}`);

      const index = sessions.value.findIndex((s) => s.id === sessionId);
      if (index !== -1) {
        sessions.value.splice(index, 1);
      }

      if (currentSessionId.value === sessionId) {
        createSession();
      }

      if (sessions.value.length === 0) {
        localStorage.removeItem("currentSessionId");
      }

      ElMessage.success("会话已删除");
    } catch (error) {
      console.error("删除会话失败:", error);
      ElMessage.error("删除会话失败，请稍后重试");
    }
  };

  /**
   * 保存当前会话
   */
  const saveCurrentSession = () => {
    if (messages.value.length === 0) return;
    if (!currentSessionId.value) return;

    const sessionId = currentSessionId.value;
    const sessionIndex = sessions.value.findIndex((s) => s.id === sessionId);
    if (sessionIndex !== -1) {
      sessions.value[sessionIndex] = {
        ...sessions.value[sessionIndex],
        messages: [...messages.value],
        updatedAt: Date.now(),
        title: generateSessionTitle(messages.value),
        messageCount: messages.value.length,
      };
    }
  };

  /**
   * 刷新会话列表
   */
  const refreshSessions = async () => {
    await loadSessions();

    if (!currentSessionId.value && sessions.value.length > 0) {
      const first = sessions.value[0];
      currentSessionId.value = first.id;
      localStorage.setItem("currentSessionId", String(first.id));
      const index = sessions.value.findIndex((s) => s.id === first.id);
      if (index !== -1) {
        sessions.value[index] = {
          ...sessions.value[index],
          messages: [...messages.value],
          messageCount: messages.value.length,
        };
      }
    } else if (currentSessionId.value) {
      const index = sessions.value.findIndex((s) => s.id === currentSessionId.value);
      if (index !== -1) {
        sessions.value[index] = {
          ...sessions.value[index],
          messages: [...messages.value],
          messageCount: messages.value.length,
          updatedAt: Date.now(),
        };
      }
    }
  };

  return {
    sessions,
    currentSessionId,
    currentSession,
    messages,
    loading,
    loadSessions,
    fetchSessionMessages,
    switchSession,
    createSession,
    deleteSession,
    saveCurrentSession,
    refreshSessions,
  };
}
