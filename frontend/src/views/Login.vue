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
      const response = await authStore.login({
        username: form.username,
        password: form.password,
      });
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
  background: var(--bg-secondary);
  color-scheme: light;
  font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
}

.login-card {
  width: 360px;
  max-width: 100%;
  padding: 32px;
  border-radius: var(--radius-lg);
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-md);
}

.login-header {
  text-align: center;
  margin-bottom: 28px;
}

.login-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.login-header p {
  font-size: 13px;
  color: var(--text-secondary);
}

.login-form {
  margin-top: 4px;
}

.login-card :deep(.el-form-item__label) {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  padding-bottom: 6px;
}

.login-card :deep(.el-input__wrapper) {
  padding: 2px 12px;
  border-radius: var(--radius-sm);
  box-shadow: none;
  border: 1px solid var(--border-color);
  background-color: var(--bg-secondary);
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.login-card :deep(.el-input__wrapper:hover) {
  border-color: var(--text-muted);
}

.login-card :deep(.el-input__wrapper.is-focus) {
  border-color: var(--primary-color);
  background-color: var(--bg-primary);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.login-card :deep(.el-input__inner) {
  font-size: 14px;
}

.login-button {
  width: 100%;
  margin-top: 8px;
  height: 40px;
  border-radius: var(--radius-sm);
  font-weight: 500;
  font-size: 14px;
  border: none;
  background: var(--primary-color);
  transition: background-color 0.2s ease;
}

.login-card :deep(.login-button.el-button--primary:hover) {
  background: var(--primary-hover);
}

.login-card :deep(.el-button.is-loading) {
  opacity: 0.9;
}

@media (max-width: 640px) {
  .login-page {
    padding: 24px 16px;
  }

  .login-card {
    width: 100%;
    padding: 28px 20px;
    border-radius: var(--radius-md);
  }
}
</style>
