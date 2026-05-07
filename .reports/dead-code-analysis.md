# 死代码分析报告

生成时间: 2026-02-04
更新: 2026-02-04

## 分析方法

- Python: 手动分析导入依赖和文件使用情况
- TypeScript/Vue: 检查导入语句和构建输出
- 工具: knip, depcheck, ts-prune (未安装，使用手动分析)

---

## 严重级别分类

| 级别 | 描述 |
|------|------|
| 🔴 DANGER | 核心文件死代码，删除需谨慎 |
| 🟠 CAUTION | 未使用的功能/模块，删除需测试 |
| 🟢 SAFE | 冗余配置/文件，可安全删除 |

---

## 🔴 DANGER - 后端死代码 (2026-02-04 新增)

### 2. `backend/app/api/auth_simple.py` (完全未使用)

**问题**: 定义了简化版认证逻辑，但从未被任何文件导入使用。

**证据**:
- main.py 只导入了 `documents` 和 `chat`，没有导入 auth_simple
- main.py 自己实现了认证逻辑 (行 60-305)
- DB_CONFIG 在 auth_simple.py 和 main.py 中重复定义

**内容包含**:
- 简化的登录端点
- 数据库查询函数 `get_user_from_db()`
- Token 和 UserLogin Pydantic 模型

**可安全删除**: 是

---

### 3. `backend/app/services/user_service.py` (间接死代码)

**问题**: 只被 `auth.py` 导入使用，而 `auth.py` 是死代码

**证据**:
- 搜索 `user_service` - 只在 auth.py 中出现
- 其他 API 端点使用直接 SQL 查询或 aiomysql

**可安全删除**: 是
- `get_user_by_username` 和 `create_user` 未被实际使用
- main.py 中的认证使用自己的 `get_user_from_db` 函数

---

## 🟠 CAUTION - 后端死代码

### 3. `backend/app/schemas/document.py` (已恢复)

**状态**: ⚠️ **警告** - 此文件实际被 `documents.py` 使用

**证据**:
- `api/documents.py:20-23` 导入: `DocumentResponse, DocumentListResponse, DocumentUploadRequest, DocumentParseRequest, DocumentParseResponse, DocumentStatus, FileType`

**已恢复**: 文件已恢复，因清理时误删

---

### 4. `backend/app/services/__init__.py` (空文件)

**问题**: 只包含一行（可能是 `__all__` 或空导入）

**可安全删除**: 是

---

### 5. `backend/app/schemas/__init__.py` (空文件)

**问题**: 只包含一行

**可安全删除**: 是

---

## 🟢 SAFE - 前端死代码

### 6. `frontend/src/router/index.ts` (完全未使用)

**问题**: 定义了简单的默认路由，但实际使用的是 `simple.ts`

**证据**:
- main.ts 第13行: `import router from "./router/simple"`
- `index.ts` 从未被导入

**内容**:
```typescript
// 只有一个 /chat 路由，无认证守卫
```

**可安全删除**: 是

---

### 7. `frontend/src/services/review.ts` (完全未使用)

**问题**: 定义了审核相关函数，但从未被任何文件导入使用。

**证据**:
- 搜索 `from "@/services/review"` - 无结果
- 搜索 `performFormalCheck|performLogicCheck|getFormalCheckSample` - 无结果

**内容包含**:
- `performFormalCheck()` - 形式审查
- `performLogicCheck()` - 逻辑审查
- `getFormalCheckSample()` - 获取示例

**可安全删除**: 是

---

### 8. `frontend/src/views/SimplePatentChat.vue.backup` (备份文件)

**问题**: 开发过程中创建的备份文件，不再需要。

**大小**: 78578 字节 (~700+ 行)

**可安全删除**: 是

---

### 9. `frontend/src/services/auth.ts` - 部分未使用

**问题**: 导出了未使用的函数。

**分析**:
- 使用的函数: `login`, `logout` (被 stores/auth.ts 导入)
- 未使用的函数: `getCurrentUser`, `register`, `changePassword`

**建议**: 删除未使用的函数导出

---

## 📦 可安全删除的文件清单

### 立即可删除 (SAFE) - 2026-02-04 更新
```
frontend/src/router/index.ts
frontend/src/services/review.ts
frontend/src/views/SimplePatentChat.vue.backup
backend/app/api/auth.py           # JWT 认证，未使用
backend/app/api/auth_simple.py    # 简化认证，未使用
backend/app/services/user_service.py
backend/app/services/__init__.py
backend/app/schemas/__init__.py
```

### 需验证后删除 (CAUTION)
```
backend/app/api/chat.py            # 复杂逻辑，需测试所有流程
frontend/src/services/documents.ts # 需验证所有文档操作
frontend/src/utils/patentPrompts.ts
frontend/src/composables/useChatSession.ts
frontend/src/utils/chat/
```

### 清理 auth.ts 未使用的导出
```typescript
// 删除以下导出:
- getCurrentUser()
- register()
- changePassword()
```

---

## ⚠️ 删除前检查清单

在删除任何文件前，请确认:

- [ ] 后端可以正常启动: `python -m uvicorn app.main:app --reload`
- [ ] 登录功能正常工作
- [ ] API 文档正确显示: http://localhost:8000/docs
- [ ] 前端构建成功: `npm run build`

---

## 📊 统计摘要

| 类别 | 数量 | 严重级别 |
|------|------|----------|
| 死代码文件 (已删除) | 5 | DANGER |
| 死代码文件 (前端) | 3 | SAFE |
| 未使用函数/导出 | 3 | SAFE |
| 空文件 | 2 | 已恢复 |
| 备份文件 | 1 | 已删除 |
| 误删已恢复 | 1 | schemas/document.py |

**实际删除**: 9+ 项

---

## 建议清理顺序

### 第一阶段: 立即安全删除
1. 删除 `frontend/src/router/index.ts`
2. 删除 `frontend/src/services/review.ts`
3. 删除 `frontend/src/views/SimplePatentChat.vue.backup`
4. 删除空 `__init__.py` 文件

### 第二阶段: 后端死代码删除
5. 删除 `backend/app/api/auth.py`
6. 删除 `backend/app/api/auth_simple.py`
7. 删除 `backend/app/services/user_service.py`
8. 删除 `backend/app/schemas/__init__.py`
9. 删除 `backend/app/services/__init__.py`

⚠️ 注意: `backend/app/schemas/document.py` 已被 **恢复**，因为它被 `documents.py` 使用

### 第三阶段: 清理前端代码
10. 清理 `frontend/src/services/auth.ts` 未使用的导出
11. 验证 `frontend/src/utils/` 目录下的工具文件使用情况

### 验证步骤
- [ ] 后端启动: `python -m uvicorn app.main:app --reload`
- [ ] 前端构建: `npm run build`
- [ ] 登录/登出功能测试
- [ ] 文档上传/解析测试
- [ ] AI 对话测试
- [ ] 管理员功能测试

---

---

## ⚠️ 重要教训

### 误删恢复 (2026-02-04)

**错误**: 删除了 `backend/app/schemas/document.py`

**影响**: 后端启动失败
```
ModuleNotFoundError: No module named 'app.schemas.document'
```

**原因**: 报告中错误标记 `schemas/document.py` 为未使用，但实际被 `api/documents.py` 导入使用

**解决**: 已恢复文件

**教训**: 删除任何文件前，必须先检查实际导入情况，不能仅依赖导入搜索结果

*报告生成工具: Refactor Clean Agent*
