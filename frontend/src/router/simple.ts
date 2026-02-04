import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: "/login",
    },
    {
      path: "/login",
      name: "Login",
      component: () => import("@/views/Login.vue"),
      meta: {
        title: "登录",
      },
    },
    {
      path: "/chat",
      name: "PatentChat",
      component: () => import("@/views/SimplePatentChat.vue"),
      meta: {
        title: "专利 AI 助手",
        requiresAuth: true,
      },
    },
    {
      path: "/admin/users",
      name: "AdminUsers",
      component: () => import("@/views/AdminUsers.vue"),
      meta: {
        title: "用户管理",
        requiresAuth: true,
        requiresAdmin: true,
      },
    },
    {
      path: "/:pathMatch(.*)*",
      redirect: "/login",
    },
  ],
});

const isLoggedIn = () => {
  return !!localStorage.getItem("token");
};

router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = `${to.meta.title} - 专利 AI 助手`;
  }

  if (to.path === "/login") {
    if (isLoggedIn()) {
      next("/chat");
    } else {
      next();
    }
    return;
  }

  if (to.meta.requiresAuth && !isLoggedIn()) {
    next("/login");
    return;
  }

  if (to.meta.requiresAdmin) {
    const auth = useAuthStore();
    auth.initUser();
    if (!auth.isAdmin) {
      next("/chat");
      return;
    }
  }

  next();
});

export default router;
