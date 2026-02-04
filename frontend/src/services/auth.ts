import api from "./api";
import type { LoginForm, User, ApiResponse } from "@/types";

export const login = async (
  form: LoginForm,
): Promise<{ access_token: string; user: User }> => {
  const response = await api.post("/auth/login", form);
  return response;
};

export const logout = async (): Promise<void> => {
  await api.post("/auth/logout");
};

export const getCurrentUser = async (): Promise<User> => {
  const response = await api.get("/auth/me");
  return response;
};

export const register = async (
  form: LoginForm & { confirmPassword: string },
): Promise<User> => {
  const response = await api.post("/auth/register", form);
  return response;
};

export const changePassword = async (data: {
  oldPassword: string;
  newPassword: string;
}): Promise<void> => {
  await api.post("/auth/change-password", data);
};
