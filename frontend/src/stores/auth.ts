import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { login as loginApi, logout as logoutApi } from "@/services/auth";
import type { User, LoginForm } from "@/types";

export const useAuthStore = defineStore("auth", () => {
  const user = ref<User | null>(null);
  const token = ref<string | null>(localStorage.getItem("token"));

  // 计算属性
  const isAuthenticated = computed(() => !!token.value);
  const userRole = computed(() => user.value?.role || "user");
  const isAdmin = computed(() => userRole.value === "admin");

  // 登录
  const login = async (form: LoginForm) => {
    const response = await loginApi(form);
    const { access_token, user: userData } = response;

    token.value = access_token;
    user.value = userData;

    // 保存到本地存储
    localStorage.setItem("token", access_token);
    localStorage.setItem("user", JSON.stringify(userData));

    return response;
  };

  // 登出
  const logout = async () => {
    try {
      await logoutApi();
    } finally {
      token.value = null;
      user.value = null;

      // 清除本地存储
      localStorage.removeItem("token");
      localStorage.removeItem("user");
    }
  };

  // 初始化用户信息
  const initUser = () => {
    try {
      const savedUser = localStorage.getItem("user");
      if (savedUser && savedUser !== "undefined") {
        user.value = JSON.parse(savedUser);
      }
    } catch {
      console.warn("用户数据缓存已损坏，已自动清除");
      localStorage.removeItem("user");
    }
  };

  // 检查认证状态
  const checkAuth = async () => {
    if (!token.value) {
      return false;
    }
    return true;
  };

  // 更新用户信息
  const updateUser = (userData: Partial<User>) => {
    if (user.value) {
      user.value = { ...user.value, ...userData };
      localStorage.setItem("user", JSON.stringify(user.value));
    }
  };

  return {
    user,
    token,
    isAuthenticated,
    userRole,
    isAdmin,
    login,
    logout,
    initUser,
    checkAuth,
    updateUser,
  };
});
