# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

智能专利辅助审核系统 (IPRS) - AI-powered patent document review platform for patent agents.

## Development Commands

### Backend (Python/FastAPI)
```bash
cd backend

# Activate virtual environment (Windows)
.venv\Scripts\activate
# Or (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Development server with auto-reload
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest tests/ -v

# API docs: http://localhost:8000/docs
# Health check: http://localhost:8000/health
```

### Frontend (Vue 3/Vite)
```bash
cd frontend

# Install dependencies
npm install

# Development server (port 5173, proxies /api to backend:8000)
npm run dev

# Type check
npm run type-check

# Lint and fix
npm run lint

# Build for production
npm run build

# Run tests
npm run test
```

## Architecture

### Backend Structure (FastAPI)
```
backend/app/
├── main.py              # FastAPI app entry, CORS, middleware, route registration
├── api/
│   ├── auth.py          # Authentication endpoints (login, logout, user info)
│   ├── documents.py     # Document CRUD, upload, parse
│   ├── chat.py          # AI chat, SSE streaming, Ollama integration
│   └── admin.py         # User management (admin only)
├── core/
│   ├── config.py        # App configuration, environment variables (.env in backend/)
│   ├── security.py      # Token parsing, password hashing
│   ├── middleware.py    # Rate limiting, request size limit, security headers
│   └── redis_client.py  # Redis connection for rate limiting
├── models/              # SQLAlchemy models (user, document, chat, review)
├── schemas/             # Pydantic schemas for request/response validation
├── services/
│   ├── document_parser.py   # .docx (python-docx), .pdf (pdfplumber) parsing
│   ├── ollama.py            # Ollama API client with streaming support
│   ├── chat_persistence.py  # Chat session/message persistence
│   ├── rule_retriever.py    # Rule retrieval for patent audit
│   └── user_repository.py   # User data access
├── prompts/
│   └── rules/
│       ├── loader.py        # Rule JSON loader
│       └── rules/            # Patent audit rule JSON templates
│       ├── general_case_rules.json      (template_id=1)
│       ├── patent_guidance_rules.json   (template_id=2)
│       ├── project_case_rules.json      (template_id=3)
│       └── ipc_classification_rules.json (template_id=5)
└── utils/
    ├── database.py      # SQLAlchemy session management
    └── passwords.py     # Password hashing utilities
```

### Frontend Structure (Vue 3)
```
frontend/src/
├── views/               # Page components (Login, AdminUsers, SimplePatentChat)
├── components/
│   ├── chat/            # Chat-related components (ChatSidebar, EnhancedChatInput, etc.)
│   ├── message-bubble/  # Message bubble components with thinking process support
│   └── common/          # Shared components (ErrorBoundary, FilePreviewDialog, etc.)
├── services/            # API clients (api.ts, auth.ts, documents.ts, admin.ts)
├── stores/              # Pinia stores (auth.ts, documents.ts)
├── composables/        # Vue composables (useChatSession, useThinking, useSSEStream, etc.)
├── composables/         # Vue composables (useChatSession, useThinking, etc.)
├── router/
│   └── simple.ts        # Vue Router configuration
├── types/              # TypeScript interfaces
└── utils/
    ├── chat/            # Chat utilities (thinking.ts, message.ts)
    └── patentPrompts.ts # Patent-specific prompt templates
```

## Review Agent System (审核智能体)

规则模板位于 `backend/app/prompts/rules/`，通过以下流程工作：

```
JSON 规则文件 → loader.py 加载 → rule_retriever.py 格式化 → chat.py API → SSE 流式响应 → 前端展示
```

支持的审核类型：

| template_id | 名称 | 规则文件 |
|-------------|------|---------|
| 1 | 普通案例审核 | `general_case_rules.json` |
| 2 | 专利审核指导 | `patent_guidance_rules.json` |
| 3 | 专案案例审核 | `project_case_rules.json` |
| 5 | IPC 分类指导 | `ipc_classification_rules.json` |

## Authentication

- **Token-based**: Simple token stored in localStorage (`simple_token_{user_id}_{username}`)
- **Required env var**: `TOKEN_SECRET` must be set in `backend/.env`
- **Password**: SHA256 hashed via `app/core/security.py`
- **Rate limiting**: Login attempts limited via Redis (5 per minute per IP)

## API Routes

| Prefix | File | Purpose |
|--------|------|---------|
| `/api/auth/*` | `app/api/auth.py` | Login, logout, user info |
| `/api/admin/*` | `app/api/admin.py` | User management (admin only) |
| `/api/documents/*` | `app/api/documents.py` | Document upload, parse, list, delete |
| `/api/ai/*` | `app/api/chat.py` | Chat, SSE streaming, sessions, models |

## AI Integration (Ollama)

- **Default model**: `qwen3:8b`
- **Base URL**: `http://localhost:11434` (configurable via `OLLAMA_URL`)
- **Streaming**: SSE with OpenAI-compatible chunk format (`choices[0].delta.content`)
- **Thinking process**: `think: true` enabled, returned as `delta.thinking`
- **Config**: `app/core/config.py` loads from `backend/.env`

## Database Tables

| Table | Purpose |
|-------|---------|
| `users` | id, username, password_hash, role, created_at |
| `documents` | id, user_id, title, file_path, file_type, parsed_content JSON, status |
| `chat_sessions` | id, user_id, title, model, document_id, last_message_at, created_at |
| `chat_messages` | id, session_id, user_id, role, content, model, document_id, message_index |
| `review_records` | id, document_id, review_type, model_version, result_json, score, error_count |

## Key Configuration (.env)

`.env` 文件位于 `backend/.env`：

```env
# Required
TOKEN_SECRET=your-secure-secret-key

# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-db-password
DB_NAME=iprs

# Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:8b

# Redis (for rate limiting)
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Ports

| Port | Service |
|------|---------|
| 8000 | Backend (Uvicorn) |
| 5173 | Frontend dev (Vite) |
| 11434 | Ollama |
| 3306 | MySQL |
| 6379 | Redis |

## Test Accounts

| Username | Password | Role |
|----------|----------|------|
| admin | (set in .env) | admin |
| lizhuanyuan | (set in .env) | user |
