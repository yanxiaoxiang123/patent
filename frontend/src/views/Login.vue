<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <h2>专利 AI 助手</h2>
        <p>请先登录后使用系统</p>
      </div>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        class="login-form"
        @keyup.enter="handleSubmit"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            autocomplete="off"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="请输入密码"
            autocomplete="off"
          />
        </el-form-item>
        <el-button
          type="primary"
          class="login-button"
          :loading="submitting"
          @click="handleSubmit"
        >
          登录
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const formRef = ref();
const submitting = ref(false);
const form = reactive({
  username: "",
  password: "",
});

const rules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
};

const isLoggedIn = () => {
  return !!authStore.token;
};

const handleSubmit = () => {
  if (!formRef.value) return;
  formRef.value.validate(async (valid) => {
    if (!valid) return;
    if (submitting.value) return;
    submitting.value = true;
    try {
      console.log("开始登录...");
      const response = await authStore.login({
        username: form.username,
        password: form.password,
      });
      console.log("登录响应:", response);
      console.log("authStore.token:", authStore.token);
      console.log("localStorage token:", localStorage.getItem("token"));
      console.log("登录成功，跳转到聊天页面");
      // 使用 location.href 强制页面跳转，确保路由守卫正确检测到登录状态
      window.location.href = "/chat";
    } catch (error) {
      ElMessage.error("用户名或密码错误");
    } finally {
      submitting.value = false;
    }
  });
};

onMounted(() => {
  authStore.initUser();
  if (isLoggedIn()) {
    router.replace("/chat");
  }
});
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 16px;
  background: radial-gradient(
    circle at top,
    #ffffff 0,
    #f5f5f7 55%,
    #e5e7eb 100%
  );
  color-scheme: light;
  font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
}

.login-card {
  width: 380px;
  max-width: 100%;
  padding: 32px 32px 28px;
  border-radius: 26px;
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(26px);
  box-shadow: 0 22px 45px rgba(15, 23, 42, 0.16);
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.login-header {
  text-align: center;
  margin-bottom: 24px;
}

.login-header h2 {
  font-size: 24px;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: #111827;
  margin-bottom: 6px;
}

.login-header p {
  font-size: 13px;
  color: #6b7280;
}

.login-form {
  margin-top: 4px;
}

.login-card :deep(.el-form-item__label) {
  font-size: 12px;
  font-weight: 500;
  color: #4b5563;
  padding-bottom: 4px;
}

.login-card :deep(.el-input__wrapper) {
  padding: 2px 12px;
  border-radius: 12px;
  box-shadow: none;
  border: 1px solid #e5e7eb;
  background-color: #f9fafb;
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    background-color 0.18s ease;
}

.login-card :deep(.el-input__wrapper.is-focus) {
  border-color: #111827;
  background-color: #ffffff;
  box-shadow: 0 0 0 1px rgba(15, 23, 42, 0.06);
}

.login-card :deep(.el-input__inner) {
  font-size: 13px;
}

.login-button {
  width: 100%;
  margin-top: 12px;
  border-radius: 999px;
  font-weight: 500;
  letter-spacing: 0.08em;
}

.login-card :deep(.login-button.el-button--primary) {
  background-color: #111827;
  border-color: #111827;
}

.login-card :deep(.login-button.el-button--primary:hover) {
  background-color: #020617;
  border-color: #020617;
}

.login-card :deep(.el-button.is-loading) {
  opacity: 0.9;
}

.login-hint {
  margin-top: 18px;
  font-size: 12px;
  color: #9ca3af;
  text-align: center;
}

.login-hint span {
  color: #4b5563;
  font-weight: 500;
}

@media (max-width: 640px) {
  .login-page {
    padding: 24px 16px;
  }

  .login-card {
    width: 100%;
    padding: 28px 22px 22px;
    border-radius: 22px;
    box-shadow: 0 18px 38px rgba(15, 23, 42, 0.16);
  }
}
</style>
