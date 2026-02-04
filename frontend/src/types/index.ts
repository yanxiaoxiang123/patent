// 用户相关类型
export interface User {
  id: number;
  username: string;
  role: "user" | "admin";
  created_at: string;
  updated_at: string;
}

export interface LoginForm {
  username: string;
  password: string;
}

export interface RegisterForm {
  username: string;
  password: string;
  confirmPassword: string;
}

// 文档相关类型
export interface DocumentItem {
  id: number;
  user_id: number;
  title: string;
  file_type: "doc" | "docx" | "pdf";
  file_size: number;
  status:
    | "uploaded"
    | "parsing"
    | "parsed"
    | "reviewing"
    | "completed"
    | "error";
  parsed_content?: ParsedContent;
  created_at: string;
  updated_at: string;
}

export interface ParsedContent {
  raw_content: string;
  structured: StructuredContent;
  sections: SectionsInfo;
}

export interface StructuredContent {
  title: string;
  abstract: string;
  claims: ClaimItem[];
  description: string;
}

export interface ClaimItem {
  number: number;
  content: string;
}

export interface SectionsInfo {
  has_title: boolean;
  has_abstract: boolean;
  has_claims: boolean;
  claims_count: number;
  has_description: boolean;
  content_length: number;
  parsing_quality: "excellent" | "good" | "fair" | "poor";
}

export interface DocumentListParams {
  page?: number;
  size?: number;
  status?: DocumentItem["status"];
  search?: string;
}

export interface DocumentListResponse {
  documents: DocumentItem[];
  total: number;
  page: number;
  size: number;
}

export interface DocumentParseResponse {
  document_id: number;
  status: DocumentItem["status"];
  parsed_content?: ParsedContent;
  message: string;
}

// 审核相关类型
export interface ReviewRequest {
  document_id: number;
  check_type: "formal" | "logic";
}

export interface FormalCheckResult {
  errors: ErrorItem[];
  summary: string;
}

export interface ErrorItem {
  location: string;
  original: string;
  suggestion: string;
  error_type: "错别字" | "标点" | "格式";
  severity: "high" | "medium" | "low";
}

export interface LogicCheckResult {
  claims_analysis: string;
  supportability_issues: string[];
  recommendations: string[];
  overall_score: number;
}

// API 响应类型
export interface ApiResponse<T = any> {
  message: string;
  data?: T;
  code?: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  size: number;
}

// 聊天相关类型
export interface ChatMessage {
  id?: number;
  role: "user" | "assistant" | "system";
  content: string;
  fullContent?: string;
  timestamp: Date;
  attachments?: FileAttachment[];
  templateId?: number;
}

export interface ChatSession {
  id: number;
  title: string;
  messages: ChatMessage[];
  createdAt: number | null;
  updatedAt: number | null;
  messageCount: number;
}

export interface FileAttachment {
  id: number;
  uid?: string;
  name: string;
  type: string;
  parsed: boolean;
  parsedContent?: ParsedContent | null;
  parsed_content?: ParsedContent | null;
  error: boolean;
  parsingThinkingSteps?: Array<{
    step: string;
    status: "pending" | "completed" | "error";
  }>;
}

export interface StreamOptions {
  messages: any[];
  onChunk: (chunk: string) => void;
  onComplete: (content: string) => void;
  onError?: (error: Error) => void;
}

export interface TemplateInfo {
  id: number;
  title: string;
  icon: string;
  description: string;
  prompt: string;
}
