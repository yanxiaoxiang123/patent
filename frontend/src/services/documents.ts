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
  const response = (await api.post("/documents/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
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
