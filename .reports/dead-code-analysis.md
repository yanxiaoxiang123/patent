# 死代码分析报告

生成时间: 2026-01-29

## 分析方法

- Python: 手动分析导入依赖和文件使用情况
- TypeScript/Vue: 检查导入语句和构建输出

---

## 严重级别分类

| 级别 | 描述 |
|------|------|
| 🔴 DANGER | 核心文件死代码，删除需谨慎 |
| 🟠 CAUTION | 未使用的功能/模块，删除需测试 |
| 🟢 SAFE | 冗余配置/文件，可安全删除 |

---

## 🔴 DANGER - 后端死代码

### 1. `backend/app/api/auth.py` (完全未使用)

**问题**: 定义了完整的 JWT 认证系统，但从未被任何文件导入使用。

**证据**:
- 搜索 `from app.api import auth` - 无结果
- main.py 只导入了 `documents` 和 `chat`
- main.py 中使用简单 token 认证而非 JWT

**影响**: 删除此文件不会影响系统运行，因为实际使用的是 main.py 中内联的简单认证

**内容包含**:
- JWT 令牌创建和验证
- 密码哈希 (bcrypt)
- 用户登录/注册端点
- 依赖注入的 `get_current_user`

```python
# 实际使用中，认证在 main.py:116-142 实现
# 使用简单 token 格式: simple_token_{user_id}_{username}
```

---

### 2. `backend/app/services/user_service.py` (间接死代码)

**问题**: 只被 `auth.py` 导入使用，而 `auth.py` 是死代码

**证据**:
- 搜索 `user_service` - 只在 auth.py 中出现
- 其他 API 端点使用直接 SQL 查询或 aiomysql

**可安全删除**: 是
- `get_user_by_username` 和 `create_user` 未被实际使用
- main.py 中的认证使用自己的 `get_user_from_db` 函数

---

## 🟠 CAUTION - 后端死代码

### 3. `backend/app/schemas/document.py` (未被使用)

**问题**: 定义了完整的 Pydantic models，但从未被导入

**证据**:
- 搜索 `from app.schemas` - 无结果
- main.py 和 api/ 中的请求/响应直接使用内联定义

**建议**: 这些 schemas 设计良好，可能是有意保留供将来使用
- 如果确定不使用，可考虑删除或移到 docs/ 作为 API 文档参考

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

## 📦 可安全删除的文件清单

### 立即可删除 (SAFE)
```
frontend/src/router/index.ts
backend/app/services/__init__.py
backend/app/schemas/__init__.py
backend/app/api/auth.py           # ⚠️ 确认 main.py 中的认证已覆盖所有场景
backend/app/services/user_service.py
backend/app/schemas/document.py   # ⚠️ 仅当确定不使用这些 schemas
```

### 需验证后删除 (CAUTION)
```
backend/app/schemas/              # 整个目录，确认无其他文件使用
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
| 死代码文件 | 6 | 见上表 |
| 空文件 | 2 | SAFE |
| 未使用路由 | 1 | SAFE |

---

## 建议清理顺序

1. **第一步** (安全): 删除 `frontend/src/router/index.ts`
2. **第二步** (安全): 删除空 `__init__.py` 文件
3. **第三步** (验证): 删除 `backend/app/api/auth.py` 和 `user_service.py`，测试认证功能
4. **第四步** (可选): 评估 `schemas/` 目录的用途

---

*报告生成工具: Refactor Clean Agent*
