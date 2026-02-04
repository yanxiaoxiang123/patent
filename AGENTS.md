# AGENTS.md - 代码助手开发指南

本文档为智能专利辅助审核系统 (IPRS) 的 AI 代码助手提供开发规范和命令参考。

## 项目架构

- **后端**: Python 3.10+ / FastAPI / SQLAlchemy (异步) / MySQL
- **前端**: Vue 3 / TypeScript / Vite / Ant Design Vue / Element Plus
- **AI**: Ollama (qwen3:8b) / SSE 流式响应

---

## 开发命令

### 后端 (Backend)

#### 启动服务
```bash
cd backend
# 激活虚拟环境 (Windows)
.venv/Scripts/activate
# 激活虚拟环境 (Linux/Mac)
source .venv/bin/activate

# 开发模式（自动重载）
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

#### 测试
```bash
# 项目当前无测试框架配置
# 推荐添加 pytest:
# pip install pytest pytest-asyncio httpx
# pytest                          # 运行所有测试
# pytest tests/test_api.py        # 运行单个测试文件
# pytest tests/test_api.py::test_login  # 运行单个测试函数
# pytest -v                       # 详细输出
# pytest --cov=app               # 测试覆盖率
```

#### 数据库
```bash
# 连接 MySQL
mysql -u root -p123123 -D iprs

# 数据库迁移（当前项目使用 SQLAlchemy 自动创建表）
# 推荐使用 Alembic 进行版本控制:
# alembic init alembic
# alembic revision --autogenerate -m "description"
# alembic upgrade head
```

### 前端 (Frontend)

#### 启动服务
```bash
cd frontend

# 安装依赖
npm install

# 开发服务器 (http://localhost:5173)
npm run dev

# 生产构建
npm run build

# 预览生产构建
npm run preview
```

#### Lint 和格式化
```bash
# Lint 检查并自动修复
npm run lint

# 手动运行 ESLint
npx eslint src --ext .vue,.js,.ts --fix

# 手动运行 Prettier（如果需要）
npx prettier --write "src/**/*.{vue,js,ts,json}"
```

#### 测试
```bash
# 项目当前无测试配置
# 推荐添加 Vitest:
# npm install -D vitest @vue/test-utils happy-dom
# npm run test              # 运行所有测试
# npm run test -- login     # 运行匹配 'login' 的测试
# npm run test:ui           # UI 模式
# npm run test:coverage     # 测试覆盖率
```

---

## 代码风格规范

### Python 后端

#### 导入顺序
```python
# 1. 标准库
import os
import json
from typing import List, Optional, Dict

# 2. 第三方库
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select

# 3. 本地模块
from app.models import User
from app.utils.database import AsyncSessionLocal
```

#### 类型注解
- **必须**: 所有函数参数和返回值使用类型注解
- **Pydantic**: API 请求/响应使用 Pydantic BaseModel
- **SQLAlchemy**: 数据库模型使用异步类型

```python
async def get_user(user_id: int) -> Optional[User]:
    """获取用户信息"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
```

#### 命名规范
- **函数/变量**: `snake_case` - `get_user_by_id`, `user_count`
- **类**: `PascalCase` - `UserLogin`, `ChatSession`
- **常量**: `UPPER_SNAKE_CASE` - `OLLAMA_URLS`, `DB_CONFIG`
- **私有**: 前缀下划线 - `_trim_to_strict_report`, `_rr_index`

#### 异步编程
- 所有数据库操作使用 `async/await`
- 使用 `AsyncSessionLocal()` 管理数据库会话
- HTTP 请求使用 `httpx.AsyncClient`

```python
async with AsyncSessionLocal() as session:
    async with session.begin():
        # 数据库操作
        pass
```

#### 错误处理
```python
# FastAPI HTTPException
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="用户不存在"
)

# 通用异常处理
try:
    result = await some_operation()
except Exception as e:
    return {"error": str(e), "status": "failed"}
```

#### 文档字符串
- 使用中文注释和文档字符串
- 关键函数添加简短说明

```python
def verify_password(plain_password: str, stored_password: str) -> bool:
    """验证密码 - 支持 SHA256 哈希和明文密码"""
    # 实现...
```

### TypeScript 前端

#### 导入顺序
```typescript
// 1. Vue 核心
import { ref, computed, onMounted } from "vue";
import { defineStore } from "pinia";

// 2. 第三方库
import { ElMessage } from "element-plus";
import axios from "axios";

// 3. 本地模块（使用 @ 别名）
import type { User, LoginForm } from "@/types";
import { login as loginApi } from "@/services/auth";
import { useAuthStore } from "@/stores/auth";
```

#### 类型定义
- **必须**: 所有 API 接口、状态、props 使用 TypeScript 类型
- **接口**: 优先使用 `interface`，工具类型使用 `type`
- **泛型**: API 响应使用泛型 `ApiResponse<T>`

```typescript
export interface User {
  id: number;
  username: string;
  role: "user" | "admin";
  created_at: string;
}

// 函数类型注解
const login = async (form: LoginForm): Promise<void> => {
  const response = await loginApi(form);
  // ...
};
```

#### 命名规范
- **组件文件**: `PascalCase` - `SimplePatentChat.vue`, `AdminUsers.vue`
- **变量/函数**: `camelCase` - `isAuthenticated`, `userRole`
- **常量**: `UPPER_SNAKE_CASE` - `API_BASE_URL`
- **类型/接口**: `PascalCase` - `User`, `LoginForm`

#### Vue 3 Composition API
- 使用 `<script setup>` 语法
- 响应式变量使用 `ref` 或 `reactive`
- Pinia stores 使用 composition 风格

```typescript
export const useAuthStore = defineStore("auth", () => {
  const user = ref<User | null>(null);
  const token = ref<string | null>(localStorage.getItem("token"));
  
  const isAuthenticated = computed(() => !!token.value);
  
  const login = async (form: LoginForm) => {
    // 实现...
  };
  
  return { user, token, isAuthenticated, login };
});
```

#### 错误处理
```typescript
// Axios 拦截器统一处理
api.interceptors.response.use(
  (response) => response.data,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      ElMessage.error("登录已过期，请重新登录");
      authStore.logout();
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);
```

---

## 开发注意事项

### 认证机制
- 使用简单 token: `simple_token_{user_id}_{username}`
- 前端存储在 `localStorage`
- 后端通过 `Authorization: Bearer {token}` 验证

### API 路由规范
- `/api/auth/*` - 认证相关
- `/api/admin/*` - 管理员功能 (需要 `require_admin` 依赖)
- `/api/documents/*` - 文档管理
- `/api/ai/*` - AI 对话功能

### 文件上传
- 支持格式: `.docx`, `.pdf`
- 最大大小: 20MB (`MAX_FILE_SIZE=20971520`)
- 解析超时: 120秒 (`PARSE_TIMEOUT=120`)

### SSE 流式响应
- 使用 `EventSourceResponse` (backend)
- 前端使用 `EventSource` API
- chunk 格式: `{"choices":[{"delta":{"content":"..."}}]}`

### 环境变量
- 后端: `backend/.env`
- 前端: 代理配置在 `vite.config.ts` (开发模式 `/api` -> `http://localhost:8000`)

---

## 提交规范

- **类型**: feat, fix, docs, style, refactor, test, chore
- **格式**: `<type>: <description>` (英文或中文皆可)
- **示例**: 
  - `feat: 添加专利审核模板支持`
  - `fix: 修复 SSE 流式响应断连问题`
  - `refactor: 优化文档解析性能`
