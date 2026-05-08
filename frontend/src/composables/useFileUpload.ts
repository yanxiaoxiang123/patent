/**
 * 文件上传 composable
 */

import { ref, computed } from "vue";
import { ElMessage } from "element-plus";
import type { FileAttachment } from "@/types";
import { uploadDocument, parseDocument } from "@/services/documents";

const UPLOADED_FILES_STORAGE_KEY = "patent_uploaded_files";

export function useFileUpload() {
  const uploadedFiles = ref<FileAttachment[]>([]);
  const attachmentItems = ref<any[]>([]);

  const isAttachmentsReady = computed(() => {
    if (uploadedFiles.value.length === 0) return true;
    return uploadedFiles.value.every((file) => file.parsed && !file.error);
  });

  const isAttachmentsParsing = computed(() => {
    return uploadedFiles.value.some((file) => !file.parsed && !file.error);
  });

  /**
   * 文件上传前验证
   */
  const beforeUpload = (file: File): boolean => {
    const isValidType = [
      "application/msword",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "application/pdf",
    ].includes(file.type);
    const isLt20M = file.size / 1024 / 1024 < 20;

    if (!isValidType) {
      ElMessage.error("只能上传 .doc/.docx/.pdf 格式的文件!");
      return false;
    }
    if (!isLt20M) {
      ElMessage.error("文件大小不能超过 20MB!");
      return false;
    }

    return true;
  };

  /**
   * 自定义上传请求
   */
  const handleAttachmentCustomRequest = async (options: any) => {
    const { file, onError, onSuccess } = options || {};
    const uid = file?.uid ? String(file.uid) : String(Date.now());
    const rawFile = file instanceof File ? file : file?.originFileObj;

    if (!rawFile || !beforeUpload(rawFile)) {
      if (onError) onError(new Error("invalid file"));
      return;
    }

    const formData = new FormData();
    formData.append("file", rawFile);
    formData.append("title", rawFile.name);

    try {
      const uploaded = await uploadDocument(formData);

      const fileItem: FileAttachment = {
        uid,
        id: uploaded.id,
        name: uploaded.title || rawFile.name,
        type: uploaded.file_type,
        parsed: uploaded.status === "parsed" && !!uploaded.parsed_content,
        parsedContent: uploaded.parsed_content || null,
        error: false,
        parsingThinkingSteps: [
          { step: "文件上传成功，开始解析", status: "completed" },
          { step: "提取文件内容", status: "pending" },
          { step: "结构化内容分析", status: "pending" },
          { step: "解析完成", status: "pending" },
        ],
      };

      uploadedFiles.value.push(fileItem);

      attachmentItems.value = attachmentItems.value.map((item) => {
        if (String(item.uid) !== String(uid)) return item;
        return {
          ...item,
          status: "done",
          docId: uploaded.id,
          description: fileItem.parsed ? "已解析" : "解析中...",
        };
      });

      if (!fileItem.parsed) {
        try {
          const parsedResult = await parseDocument(uploaded.id);
          if (fileItem.parsingThinkingSteps) {
            fileItem.parsingThinkingSteps[1].status = "completed";
            fileItem.parsingThinkingSteps[2].status = "completed";
          }
          if (
            parsedResult?.status === "parsed" &&
            parsedResult.parsed_content
          ) {
            fileItem.parsed = true;
            fileItem.parsedContent = parsedResult.parsed_content;
            fileItem.error = false;
            if (fileItem.parsingThinkingSteps) {
              fileItem.parsingThinkingSteps[3].status = "completed";
            }
          } else {
            fileItem.error = true;
            if (fileItem.parsingThinkingSteps) {
              fileItem.parsingThinkingSteps[3].status = "error";
            }
          }
        } catch (parseError) {
          console.error("解析文档失败:", parseError);
          fileItem.error = true;
          if (fileItem.parsingThinkingSteps) {
            fileItem.parsingThinkingSteps[3].status = "error";
          }
          ElMessage.error("文档解析失败，请检查文件内容或稍后重试");
        }

        const index = uploadedFiles.value.findIndex(
          (f) => f.id === fileItem.id,
        );
        if (index !== -1) {
          uploadedFiles.value[index] = {
            ...uploadedFiles.value[index],
            parsed: !!fileItem.parsed,
            parsedContent: fileItem.parsedContent,
            error: !!fileItem.error,
            parsingThinkingSteps: fileItem.parsingThinkingSteps,
          };
        }

        attachmentItems.value = attachmentItems.value.map((item) => {
          if (String(item.uid) !== String(uid)) return item;
          return {
            ...item,
            status: fileItem.error ? "error" : "done",
            description: fileItem.error
              ? "解析失败"
              : fileItem.parsed
                ? "已解析"
                : "解析中...",
          };
        });
      }

      if (onSuccess) {
        onSuccess(uploaded, rawFile);
      }

      if (fileItem.parsed) {
        ElMessage.success("文件上传并解析成功");
      } else {
        ElMessage.success("文件上传成功，解析任务已启动");
      }
    } catch (error) {
      console.error("文件上传失败:", error);
      ElMessage.error("文件上传失败，请稍后重试");
      attachmentItems.value = attachmentItems.value.map((item) => {
        if (String(item.uid) !== String(uid)) return item;
        return {
          ...item,
          status: "error",
          description: "上传失败",
        };
      });
      if (onError) {
        onError(error);
      }
    }
  };

  /**
   * 移除附件
   */
  const handleAttachmentRemove = (file: any) => {
    const uid = file?.uid;
    if (!uid) return true;

    attachmentItems.value = attachmentItems.value.filter(
      (f) => String(f.uid) !== String(uid),
    );

    const index = uploadedFiles.value.findIndex(
      (f) => String(f.id) === String(uid) || String(f.uid) === String(uid),
    );
    if (index !== -1) {
      uploadedFiles.value.splice(index, 1);
    }

    return true;
  };

  /**
   * 附件变化处理
   */
  const handleAttachmentsChange = (info: any) => {
    const list = Array.isArray(info?.fileList) ? info.fileList : [];
    attachmentItems.value = list.map((item) => {
      const matched = uploadedFiles.value.find(
        (f) =>
          String(f.id) === String(item.docId) ||
          String(f.id) === String(item.response?.id) ||
          String(f.uid) === String(item.uid),
      );
      if (!matched) return item;
      return {
        ...item,
        docId: matched.id,
        description: matched.error
          ? "解析失败"
          : matched.parsed
            ? "已解析"
            : "解析中...",
        status: matched.error ? "error" : "done",
      };
    });
  };

  /**
   * 清空已上传文件
   */
  const clearUploadedFiles = () => {
    uploadedFiles.value = [];
    attachmentItems.value = [];
  };

  /**
   * 从 localStorage 加载上传文件状态
   */
  const loadUploadedFiles = () => {
    try {
      const stored = localStorage.getItem(UPLOADED_FILES_STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed)) {
          uploadedFiles.value = parsed.map((item) => ({
            id: item.id,
            name: item.name,
            type: item.type,
            parsed: !!item.parsed,
            parsedContent: item.parsedContent || item.parsed_content || null,
            error: !!item.error,
            parsingThinkingSteps: item.parsingThinkingSteps || [],
          }));
        }
      }

      attachmentItems.value = uploadedFiles.value.map((file) => ({
        uid: String(file.id),
        name: file.name,
        status: file.error ? "error" : "done",
        description: file.error
          ? "解析失败"
          : file.parsed
            ? "已解析"
            : "解析中...",
        docId: file.id,
      }));
    } catch (e) {
      console.error("恢复上传文件状态失败:", e);
    }
  };

  /**
   * 保存上传文件状态到 localStorage
   */
  const saveUploadedFiles = () => {
    try {
      const plain = uploadedFiles.value.map((file) => ({
        id: file.id,
        name: file.name,
        type: file.type,
        parsed: !!file.parsed,
        parsedContent: file.parsedContent || file.parsed_content || null,
        error: !!file.error,
        parsingThinkingSteps: file.parsingThinkingSteps || [],
      }));
      localStorage.setItem(UPLOADED_FILES_STORAGE_KEY, JSON.stringify(plain));
    } catch (e) {
      console.error("保存上传文件状态失败:", e);
    }
  };

  return {
    uploadedFiles,
    attachmentItems,
    isAttachmentsReady,
    isAttachmentsParsing,
    beforeUpload,
    handleAttachmentCustomRequest,
    handleAttachmentRemove,
    handleAttachmentsChange,
    clearUploadedFiles,
    loadUploadedFiles,
    saveUploadedFiles,
  };
}
