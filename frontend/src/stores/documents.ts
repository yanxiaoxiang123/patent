import { defineStore } from "pinia";
import { ref } from "vue";
import {
  getDocuments,
  getDocument,
  uploadDocument,
  parseDocument,
  deleteDocument,
} from "@/services/documents";
import type { DocumentListParams, DocumentItem } from "@/types";

export const useDocumentsStore = defineStore("documents", () => {
  const documents = ref<DocumentItem[]>([]);
  const currentDocument = ref<DocumentItem | null>(null);
  const loading = ref(false);
  const total = ref(0);

  // 获取文档列表
  const fetchDocuments = async (params: DocumentListParams = {}) => {
    loading.value = true;
    try {
      const response = await getDocuments(params);
      documents.value = response.documents;
      total.value = response.total;
      return response;
    } finally {
      loading.value = false;
    }
  };

  // 获取单个文档
  const fetchDocument = async (id: number) => {
    loading.value = true;
    try {
      const response = await getDocument(id);
      currentDocument.value = response;
      return response;
    } finally {
      loading.value = false;
    }
  };

  // 上传文档
  const uploadDoc = async (formData: FormData) => {
    loading.value = true;
    try {
      const response = await uploadDocument(formData);
      documents.value.unshift(response);
      return response;
    } finally {
      loading.value = false;
    }
  };

  // 解析文档
  const parseDoc = async (id: number) => {
    loading.value = true;
    try {
      const response = await parseDocument(id);
      if (currentDocument.value && currentDocument.value.id === id) {
        currentDocument.value = { ...currentDocument.value, ...response };
      }

      // 更新列表中的文档
      const index = documents.value.findIndex((doc) => doc.id === id);
      if (index !== -1) {
        documents.value[index] = { ...documents.value[index], ...response };
      }

      return response;
    } finally {
      loading.value = false;
    }
  };

  // 删除文档
  const deleteDoc = async (id: number) => {
    loading.value = true;
    try {
      await deleteDocument(id);
      documents.value = documents.value.filter((doc) => doc.id !== id);

      if (currentDocument.value && currentDocument.value.id === id) {
        currentDocument.value = null;
      }
    } finally {
      loading.value = false;
    }
  };

  // 清空当前文档
  const clearCurrentDocument = () => {
    currentDocument.value = null;
  };

  return {
    documents,
    currentDocument,
    loading,
    total,
    fetchDocuments,
    fetchDocument,
    uploadDoc,
    parseDoc,
    deleteDoc,
    clearCurrentDocument,
  };
});
