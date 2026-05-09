import api from "./api";
import type {
  User,
  UserListParams,
  UserListResponse,
  CreateUserPayload,
  UpdateUserPayload,
} from "@/types";

export const listUsers = async (
  params?: UserListParams,
): Promise<UserListResponse> => {
  return await api.get("/admin/users", { params });
};

export const getUser = async (userId: number): Promise<{ data: User }> => {
  return await api.get(`/admin/users/${userId}`);
};

export const createUser = async (
  payload: CreateUserPayload,
): Promise<{ message: string }> => {
  return await api.post("/admin/users", payload);
};

export const updateUser = async (
  userId: number,
  payload: UpdateUserPayload,
): Promise<{ message: string }> => {
  return await api.put(`/admin/users/${userId}`, payload);
};

export const deleteUser = async (
  userId: number,
): Promise<{ message: string }> => {
  return await api.delete(`/admin/users/${userId}`);
};

export const toggleUserStatus = async (
  userId: number,
): Promise<{ message: string }> => {
  return await api.patch(`/admin/users/${userId}/toggle-status`);
};

export const resetUserPassword = async (
  userId: number,
  newPassword: string,
): Promise<{ message: string }> => {
  return await api.post(`/admin/users/${userId}/reset-password`, {
    new_password: newPassword,
  });
};

// ===================== Batch Operations =====================

export const batchDeleteUsers = async (
  userIds: number[],
): Promise<{ message: string; deleted_count: number; failed_users?: { user_id: number; reason: string }[] }> => {
  return await api.post("/admin/users/batch-delete", { user_ids: userIds });
};

export const batchToggleStatus = async (
  userIds: number[],
  enable: boolean,
): Promise<{ message: string; updated_count: number; failed_users?: { user_id: number; reason: string }[] }> => {
  return await api.post("/admin/users/batch-toggle-status", { user_ids: userIds, enable });
};

export const batchResetPassword = async (
  userIds: number[],
  newPassword: string,
): Promise<{ message: string; updated_count: number; failed_users?: { user_id: number; reason: string }[] }> => {
  return await api.post("/admin/users/batch-reset-password", { user_ids: userIds, password: newPassword });
};

// ===================== User Statistics =====================

export interface UserStats {
  user_id: number;
  username: string;
  document_count: number;
  session_count: number;
  recent_session_count?: number;
  recent_token_count?: number;
}

export const getUserStats = async (userId: number): Promise<UserStats> => {
  return await api.get(`/admin/users/${userId}/stats`);
};

// ===================== Login History =====================

export interface LoginHistoryRecord {
  id: number;
  user_id: number;
  ip_address: string | null;
  user_agent: string | null;
  login_status: string;
  fail_reason: string | null;
  created_at: string;
}

export interface LoginHistoryResponse {
  data: LoginHistoryRecord[];
  meta: {
    total: number;
    page: number;
    size: number;
    pages: number;
  };
}

export const getLoginHistory = async (
  userId: number,
  page = 1,
  size = 20,
): Promise<LoginHistoryResponse> => {
  return await api.get(`/admin/users/${userId}/login-history`, { params: { page, size } });
};

// ===================== Audit Logs =====================

export interface AuditLogRecord {
  id: number;
  operator_id: number;
  operator_username: string;
  target_user_id: number | null;
  target_username: string | null;
  action: string;
  detail: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

export interface AuditLogResponse {
  data: AuditLogRecord[];
  meta: {
    total: number;
    page: number;
    size: number;
    pages: number;
  };
}

export interface AuditLogParams {
  page?: number;
  size?: number;
  operator_id?: number;
  action?: string;
  start_date?: string;
  end_date?: string;
}

export const getAuditLogs = async (params?: AuditLogParams): Promise<AuditLogResponse> => {
  return await api.get("/admin/audit-logs", { params });
};

// ===================== Export =====================

export const exportUsers = (params?: { search?: string; role?: string; activity_status?: string }): string => {
  const queryParams = new URLSearchParams();
  if (params?.search) queryParams.set("search", params.search);
  if (params?.role) queryParams.set("role", params.role);
  if (params?.activity_status) queryParams.set("activity_status", params.activity_status);
  return `/api/admin/users/export${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
};

export const exportAuditLogs = (params?: { operator_id?: number; action?: string; start_date?: string; end_date?: string }): string => {
  const queryParams = new URLSearchParams();
  if (params?.operator_id) queryParams.set("operator_id", String(params.operator_id));
  if (params?.action) queryParams.set("action", params.action);
  if (params?.start_date) queryParams.set("start_date", params.start_date);
  if (params?.end_date) queryParams.set("end_date", params.end_date);
  return `/api/admin/audit-logs/export${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
};
