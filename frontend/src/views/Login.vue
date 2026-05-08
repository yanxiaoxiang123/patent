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
      router.push("/chat");
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
  font-family: var(--font-body);
}

.login-card {
  width: 380px;
  max-width: 100%;
  padding: 36px;
  border-radius: var(--radius-xl);
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-lg);
  animation: fadeSlideIn 0.4s ease;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h2 {
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
  font-family: var(--font-display);
}

.login-header p {
  font-size: 13px;
  color: var(--text-secondary);
}

.login-form {
  margin-top: 8px;
}

.login-card :deep(.el-form-item__label) {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  padding-bottom: 8px;
}

.login-card :deep(.el-input__wrapper) {
  padding: 2px 14px;
  border-radius: var(--radius-md);
  box-shadow: none;
  border: 1px solid var(--border-color);
  background-color: var(--bg-secondary);
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.login-card :deep(.el-input__wrapper:hover) {
  border-color: var(--border-accent);
}

.login-card :deep(.el-input__wrapper.is-focus) {
  border-color: var(--primary-color);
  background-color: var(--bg-primary);
  box-shadow: 0 0 0 3px rgba(201, 123, 93, 0.12);
}

.login-card :deep(.el-input__inner) {
  font-size: 14px;
}

.login-button {
  width: 100%;
  margin-top: 12px;
  height: 44px;
  border-radius: var(--radius-md);
  font-weight: 600;
  font-size: 14px;
  border: none;
  background: linear-gradient(135deg, var(--primary-color), var(--accent));
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(201, 123, 93, 0.25);
}

.login-card :deep(.login-button.el-button--primary:hover) {
  background: linear-gradient(135deg, var(--primary-hover), var(--accent));
  box-shadow: 0 4px 12px rgba(201, 123, 93, 0.35);
}

.login-card :deep(.el-button.is-loading) {
  opacity: 0.9;
}

@keyframes fadeSlideIn {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 640px) {
  .login-page {
    padding: 24px 16px;
  }

  .login-card {
    width: 100%;
    padding: 28px 20px;
    border-radius: var(--radius-lg);
  }
}
</style>
