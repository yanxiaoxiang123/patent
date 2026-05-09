import api from "./api";
import type {
  DocumentItem,
  DocumentListParams,
  DocumentListResponse,
  DocumentParseResponse,
} from "@/types";

export const getDocuments = async (
  params: DocumentListParams = {},
): Promise<DocumentListResponse> => {
  const response = (await api.get("/documents", {
    params,
  })) as unknown as DocumentListResponse;
  return response;
};

export const getDocument = async (id: number): Promise<DocumentItem> => {
  const response = (await api.get(
    `/documents/${id}`,
  )) as unknown as DocumentItem;
  return response;
};

export const uploadDocument = async (
  formData: FormData,
): Promise<DocumentItem> => {
  // 不要手动设置 Content-Type — axios 检测到 FormData 时会自动设置
  // multipart/form-data 并附带正确的 boundary 分隔符。
  // 手动写死会丢失 boundary，导致后端/WAF 解析失败。
  // Authorization 已由 api.ts 请求拦截器统一注入。
  const response = (await api.post("/documents/upload", formData, {
    headers: {
      "Content-Type": undefined,
    },
  })) as unknown as DocumentItem;
  return response;
};

export const parseDocument = async (
  id: number,
): Promise<DocumentParseResponse> => {
  const response = (await api.post(
    `/documents/${id}/parse`,
  )) as unknown as DocumentParseResponse;
  return response;
};

export const deleteDocument = async (id: number): Promise<void> => {
  await api.delete(`/documents/${id}`);
};

export const downloadDocument = async (id: number): Promise<Blob> => {
  const response = await api.get(`/documents/${id}/download`, {
    responseType: "blob",
  });
  return response as unknown as Blob;
};

export interface ParseProgress {
  stage: string;
  percent: number;
  message: string;
  result?: {
    document_id: number;
    status: string;
    quality?: string;
  };
}

export type ParseProgressCallback = (progress: ParseProgress) => void;

let currentEventSource: EventSource | null = null;

/**
 * Parse document with SSE stream for real-time progress updates
 * Uses EventSource with token as query parameter (EventSource doesn't support custom headers)
 */
export const parseDocumentStream = (
  documentId: number,
  onProgress: ParseProgressCallback,
): EventSource => {
  // Close any existing connection
  if (currentEventSource) {
    currentEventSource.close();
  }

  const token = localStorage.getItem("token");
  // EventSource doesn't support custom headers, so we pass token as query param
  const url = token
    ? `/api/documents/${documentId}/parse/stream?token=${encodeURIComponent(token)}`
    : `/api/documents/${documentId}/parse/stream`;

  const eventSource = new EventSource(url);
  currentEventSource = eventSource;

  eventSource.addEventListener("progress", (event) => {
    try {
      const data = JSON.parse(event.data) as ParseProgress;
      onProgress(data);
    } catch (e) {
      console.error("Failed to parse progress event:", e);
    }
  });

  eventSource.addEventListener("done", () => {
    eventSource.close();
    currentEventSource = null;
  });

  eventSource.addEventListener("error", (event) => {
    console.error("SSE error:", event);
    eventSource.close();
    currentEventSource = null;
  });

  return eventSource;
};

/**
 * Close the current SSE connection
 */
export const closeParseDocumentStream = (): void => {
  if (currentEventSource) {
    currentEventSource.close();
    currentEventSource = null;
  }
};
