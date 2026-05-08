import api from "./api";
import type { LoginForm, User, ApiResponse } from "@/types";

export const login = async (
  form: LoginForm,
): Promise<{ access_token: string; user: User }> => {
  const response = (await api.post("/auth/login", form)) as unknown as {
    access_token: string;
    user: User;
  };
  return response;
};

export const logout = async (): Promise<void> => {
  await api.post("/auth/logout");
};
