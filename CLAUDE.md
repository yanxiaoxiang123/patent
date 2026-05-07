# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

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

# Development server with auto-reload
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Or
python app/main.py

# Production server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2

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

# Production build
npm run build

# Type check
npm run type-check

# Lint and fix
npm run lint
```

### Database
```bash
mysql -u root -p -D iprs
# Tables auto-create on FastAPI startup via SQLAlchemy models
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
│   ├── config.py        # App configuration, environment variables
│   ├── security.py      # Token parsing, password hashing
│   ├── middleware.py    # Rate limiting, request size limit, security headers
│   └── redis_client.py  # Redis connection for rate limiting
├── models/              # SQLAlchemy models (user, document, chat, review)
├── schemas/             # Pydantic schemas for request/response validation
├── services/
│   ├── document_parser.py   # .docx (python-docx), .pdf (pdfplumber) parsing
│   ├── ollama.py            # Ollama API client with streaming support
│   ├── ai_adapter.py        # Ollama/Coze adapter pattern
│   ├── chat_persistence.py  # Chat session/message persistence
│   └── rule_retriever.py    # Rule retrieval for patent audit
├── prompts/
│   └── rules/
│       └── loader.py        # Patent audit rule templates loader
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
├── stores/               # Pinia stores (auth.ts, documents.ts, chat.ts)
├── composables/           # Vue composables (useChatSession, useThinking, etc.)
├── router/
│   └── simple.ts        # Vue Router configuration
├── types/               # TypeScript interfaces
├── utils/
│   ├── chat/            # Chat utilities (thinking.ts, message.ts)
│   └── patentPrompts.ts # Patent-specific prompt templates
└── main.ts              # Vue app entry, router, pinia, UI library setup
```

## Authentication

- **Token-based**: Simple token stored in localStorage (`simple_token_{user_id}_{username}`)
- **Required env var**: `TOKEN_SECRET` must be set in backend/.env
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
- **Config file**: `app/core/config.py:54-55`

## Key Patterns

### SSE Streaming Response
```python
# app/api/chat.py uses sse_starlette.sse.EventSourceResponse
async def stream_generator():
    async for chunk in ollama_stream():
        yield f"{json.dumps(chunk)}\n\n"
    yield "[DONE]\n\n"
return EventSourceResponse(stream_generator(), headers=sse_headers)
```

### Middleware Stack
- Rate limiting (Redis-based, 100 requests/minute general, 5/minute for login)
- Request body size limit (10MB)
- Security headers

### Document Parsing
- **Supported**: `.docx` (python-docx), `.pdf` (pdfplumber)
- **Status flow**: `uploaded` → `parsing` → `parsed` | `error`

## Database Tables

| Table | Purpose |
|-------|---------|
| `users` | id, username, password_hash, role, created_at |
| `documents` | id, user_id, title, file_path, file_type, parsed_content JSON, status |
| `chat_sessions` | id, user_id, title, model, document_id, last_message_at, created_at |
| `chat_messages` | id, session_id, user_id, role, content, model, document_id, message_index |
| `review_records` | id, document_id, review_type, model_version, result_json, score, error_count |

## Test Accounts

| Username | Password | Role |
|----------|----------|------|
| admin | (set in .env) | admin |
| lizhuanyuan | (set in .env) | user |

## Key Configuration (.env)

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

# Optional
DEBUG=true
CORS_ORIGINS=["http://localhost:5173"]
RATE_LIMIT_MAX=100
RATE_LIMIT_LOGIN_MAX=5
```

## Ports

| Port | Service |
|------|---------|
| 8000 | Backend (Uvicorn) |
| 5173 | Frontend dev (Vite) |
| 11434 | Ollama |
| 3306 | MySQL |
| 6379 | Redis |

## Review Agents (审核智能体)

The four audit agents are **rule-based**, not traditional agent frameworks:

| template_id | Name | Rule File | Purpose |
|-------------|------|-----------|---------|
| 1 | 普通案例审核 | `general_case_rules.json` | Standard patent case review |
| 2 | 专利审核指导 | `patent_guidance_rules.json` | Patent audit guidance |
| 3 | 专案案例审核 | `project_case_rules.json` | Special project case review |
| 5 | IPC 分类指导 | `ipc_classification_rules.json` | IPC classification guidance |

### Implementation Flow
```
JSON Rules → prompts/rules/loader.py → services/rule_retriever.py → api/chat.py → SSE → Frontend
```

### Review Flow
1. User uploads patent document
2. `document_parser.py` extracts text from .docx/.pdf
3. User selects template_id (audit type)
4. `rule_retriever.get_system_prompt()` loads and formats rules
5. Ollama generates structured audit report via SSE streaming
6. `trim_to_strict_report()` extracts the structured report portion