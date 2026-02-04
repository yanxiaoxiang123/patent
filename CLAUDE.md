# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## Project Overview

智能专利辅助审核系统 (IPRS) - AI-powered patent document review platform for patent agents.

## Development Commands

### Backend (Python/FastAPI)
```bash
cd backend

# Activate virtual environment (Windows)
.venv/Scripts/activate
# Or (Linux/Mac)
source .venv/bin/activate

# Development server with auto-reload
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

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
# Output: frontend/dist (serve via Nginx on port 8081)

# Lint and fix
npm run lint
```

### Database
```bash
mysql -u root -p123123 -D iprs
# Tables auto-create on FastAPI startup via SQLAlchemy models
```

## Architecture

### Backend Structure (FastAPI)
```
backend/app/
├── main.py           # FastAPI app, auth endpoints, admin endpoints, CORS config
├── api/
│   ├── documents.py  # Document CRUD, upload, parse (Pydantic schemas, SQLAlchemy)
│   └── chat.py       # AI chat, SSE streaming, session persistence, Ollama integration
├── models/           # SQLAlchemy async models (user, document, chat, review)
├── schemas/          # Pydantic schemas for request/response validation
├── services/
│   ├── document_parser.py  # .docx (python-docx), .pdf (pdfplumber) parsing
│   └── ai_adapter.py       # Ollama/Coze adapter pattern (Coze not implemented)
├── prompts/
│   └── case_audit.py       # Patent audit templates (template_id=1, 3)
└── utils/
    └── database.py   # AsyncSessionLocal for SQLAlchemy sessions
```

### Frontend Structure (Vue 3)
```
frontend/src/
├── views/            # Page components (Login, AdminUsers, SimplePatentChat)
├── services/         # API clients (api.ts, auth.ts, documents.ts, review.ts, admin.ts)
├── stores/           # Pinia stores (auth.ts, documents.ts)
├── router/           # Vue Router config
├── types/            # TypeScript interfaces
└── main.ts           # Vue app entry, router, pinia setup
```

### Authentication (Simple Token)
- **Token format**: `simple_token_{user_id}_{username}` (stored in localStorage)
- **No JWT**: Lightweight token, server-side user lookup on each request
- **File**: `main.py:116-142` - token parsing and user validation
- **Password**: SHA256 hashed (or plain text for test accounts)

### API Routes
| Prefix | File | Purpose |
|--------|------|---------|
| `/api/auth/*` | `main.py:151-218` | Login, logout, user info |
| `/api/admin/*` | `main.py:236-304` | User management (admin only) |
| `/api/documents/*` | `api/documents.py` | Document upload, parse, list, delete |
| `/api/ai/*` | `api/chat.py` | Chat, SSE streaming, sessions, models |

### AI Integration (Ollama)
- **Default model**: `qwen3:8b`
- **Base URL**: `http://localhost:11434` (configurable via `OLLAMA_URLS` for failover)
- **Streaming**: SSE with OpenAI-compatible chunk format (`choices[0].delta.content`)
- **Thinking process**: `think: true` enabled, returned as `delta.thinking`
- **Multi-instance**: Round-robin load balancing via `OLLAMA_URLS` env var
- **Files**:
  - `api/chat.py:220-407` - streaming response generator
  - `prompts/case_audit.py` - audit templates (template_id=1, 3)

### Chat Persistence
- **Models**: `ChatSession`, `ChatMessage` (SQLAlchemy async)
- **Tables**: `chat_sessions`, `chat_messages`
- **File**: `api/chat.py:511-554` - persistence logic

### Document Parsing
- **Supported**: `.docx` (python-docx), `.pdf` (pdfplumber)
- **Output**: JSON with `structured` content + `sections.parsing_quality`
- **File**: `services/document_parser.py`
- **Status flow**: `uploaded` → `parsing` → `parsed` | `error`

## Database Tables

### users
```sql
users(id, username, password_hash, role, created_at)
-- role: 'admin' | 'agent' | 'user'
```

### documents
```sql
documents(id, user_id, title, file_path, file_type, parsed_content JSON, status, created_at)
-- status: 'uploaded' | 'parsing' | 'parsed' | 'error'
```

### chat_sessions / chat_messages
```sql
chat_sessions(id, user_id, title, model, document_id, last_message_at, created_at)
chat_messages(id, session_id, user_id, role, content, model, document_id, message_index, created_at)
```

### review_records
```sql
review_records(id, document_id, review_type, model_version, result_json, score, error_count, processing_time, created_at)
-- review_type: 'formal_check' | 'logic_check'
```

## Test Accounts
| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | admin |
| lizhuanyuan | 123456 | user |

## Key Configuration

### Environment Variables (.env)
```env
DATABASE_URL=mysql+aiomysql://root:123123@localhost:3306/iprs
OLLAMA_URL=http://localhost:11434
OLLAMA_URLS=http://localhost:11434  # Optional: comma-separated for failover
UPLOAD_DIR=./uploads
CORS_ORIGINS=["http://localhost:5173", "http://localhost:8081"]
MAX_FILE_SIZE=20971520
PARSE_TIMEOUT=120
DEBUG=true  # Enable auto-reload for development
```

### Startup Options
```bash
# Debug mode (auto-reload)
DEBUG=true python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

### Ports
| Port | Service |
|------|---------|
| 8000 | Backend (Uvicorn) |
| 5173 | Frontend dev (Vite) |
| 8081 | Frontend production (Nginx) |
| 11434 | Ollama |

## Important Patterns

### SSE Streaming Response
```python
# chat.py uses sse_starlette.sse.EventSourceResponse
async def stream_generator():
    async for chunk in ollama_stream():
        yield f"{json.dumps(chunk)}\n\n"
    yield "[DONE]\n\n"
return EventSourceResponse(stream_generator(), headers=sse_headers)
```

### Patent Audit Templates
- **template_id=1**: `GENERAL_CASE_AUDIT_SYSTEM_PROMPT` (案件审核)
- **template_id=3**: `PROJECT_CASE_AUDIT_SYSTEM_PROMPT` (项目审核)
- Output starts with markers like "① 案件类型判定" or "① 通用规则预审"

### Passthrough Mode
- `passthrough: true` in request skips default patent relevance validation
- Useful for custom system prompts while retaining template support

### Frontend API Client
- `services/api.ts` - Axios instance with auth interceptor
- Token automatically added to `Authorization: Bearer {token}` header
- 401 triggers logout and redirect to login

### Dependency Injection
- FastAPI `Depends()` for authentication (`get_current_user_simple`, `require_admin`)
- SQLAlchemy `Depends(get_db)` for database sessions
