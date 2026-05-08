import api from "./api";
import type { LoginForm, User } from "@/types";

export const login = async (
  form: LoginForm,
): Promise<{ access_token: string; user: User }> => {
  const response = await api.post("/auth/login", form);
  // 后端返回 ApiResponse 包装: { success, data: { access_token, user } }
  return response.data;
};

export const logout = async (): Promise<void> => {
  await api.post("/auth/logout");
};
