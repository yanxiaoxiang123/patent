import api from "./api";
import type {
  User,
  UserListParams,
  UserListResponse,
  CreateUserPayload,
  UpdateUserPayload,
} from "@/types";

export const listUsers = async (
  params?: UserListParams
): Promise<UserListResponse> => {
  return await api.get("/admin/users", { params });
};

export const getUser = async (userId: number): Promise<{ data: User }> => {
  return await api.get(`/admin/users/${userId}`);
};

export const createUser = async (
  payload: CreateUserPayload
): Promise<{ message: string }> => {
  return await api.post("/admin/users", payload);
};

export const updateUser = async (
  userId: number,
  payload: UpdateUserPayload
): Promise<{ message: string }> => {
  return await api.put(`/admin/users/${userId}`, payload);
};

export const deleteUser = async (
  userId: number
): Promise<{ message: string }> => {
  return await api.delete(`/admin/users/${userId}`);
};

export const toggleUserStatus = async (
  userId: number
): Promise<{ message: string }> => {
  return await api.patch(`/admin/users/${userId}/toggle-status`);
};

export const resetUserPassword = async (
  userId: number,
  newPassword: string
): Promise<{ message: string }> => {
  return await api.post(`/admin/users/${userId}/reset-password`, {
    new_password: newPassword,
  });
};
