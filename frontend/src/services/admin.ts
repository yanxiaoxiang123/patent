import api from "./api";
import type { User } from "@/types";

export const listUsers = async (): Promise<{ data: User[] }> => {
  return await api.get("/admin/users");
};

export const createUser = async (payload: {
  username: string;
  password: string;
  email?: string;
  full_name?: string;
}): Promise<{ message: string }> => {
  return await api.post("/admin/users", payload);
};

export const deleteUser = async (
  userId: number,
): Promise<{ message: string }> => {
  return await api.delete(`/admin/users/${userId}`);
};
