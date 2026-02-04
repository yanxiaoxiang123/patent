import axios, { AxiosResponse, AxiosError } from "axios";
import { ElMessage } from "element-plus";
import { useAuthStore } from "@/stores/auth";

// 创建 axios 实例
const api = axios.create({
  baseURL: "/api",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore();
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// 响应拦截器
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data;
  },
  (error: AxiosError) => {
    const { response } = error;

    if (response) {
      const { status, data } = response;

      switch (status) {
        case 401: {
          ElMessage.error("登录已过期，请重新登录");
          const authStore = useAuthStore();
          authStore.logout();
          window.location.href = "/login";
          break;
        }
        case 403:
          ElMessage.error("没有权限访问");
          break;
        case 404:
          ElMessage.error("请求的资源不存在");
          break;
        case 500:
          ElMessage.error("服务器内部错误");
          break;
        default:
          ElMessage.error(data?.message || "请求失败");
      }
    } else if (error.code === "ECONNABORTED") {
      ElMessage.error("请求超时");
    } else {
      ElMessage.error("网络错误");
    }

    return Promise.reject(error);
  },
);

export default api;
