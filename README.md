# IPRS - Intelligent Patent Review System

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.x-4FC08D.svg)](https://vuejs.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

AI-powered patent document review platform that helps patent agents improve review efficiency and document quality through automated formal checks, logic analysis, and interactive editing.

## Features

- **Document Parsing** -- Upload and parse `.docx` and `.pdf` patent documents with intelligent text segmentation
- **AI Formal Review** -- Automated typo detection, format validation, and compliance checks powered by Ollama (Qwen3)
- **Rule-Based Review Agents** -- Four specialized review templates: general case, patent guidance, project case, and IPC classification
- **Real-Time Streaming** -- SSE-based streaming responses with thinking process visualization, auto-reconnect, and mid-generation stop with partial result preservation
- **Interactive Chat** -- Multi-session chat interface with message persistence, document context, and markdown rendering
- **User Management** -- JWT authentication with server-side token revocation, token versioning, and admin panel for user administration
- **Rate Limiting** -- Redis-backed request throttling with configurable limits

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python / FastAPI / SQLAlchemy (async) |
| Frontend | Vue 3 / TypeScript / Element Plus / Vite |
| AI Engine | Ollama (local LLM) with adapter pattern |
| Database | MySQL with aiomysql async driver |
| Cache | Redis (rate limiting) |
| Deployment | Nginx / Uvicorn / Systemd |

## Architecture

```
frontend (Vue 3)                  backend (FastAPI)
     │                                  │
     │  SSE /api/ai/chat               │
     ├─────────────────────────────────►│
     │  REST /api/auth/*                │
     │  REST /api/documents/*           │
     │  REST /api/admin/*               │
     │                                  │
     │                          ┌───────┴───────┐
     │                          │  AI Adapter   │
     │                          ├───────────────┤
     │                          │  Ollama       │
     │                          │  (local LLM)  │
     │                          └───────────────┘
     │                          ┌───────┴───────┐
     │                          │  Rule Loader  │
     │                          │  (JSON rules) │
     │                          └───────────────┘
     │                                  │
     ▼                                  ▼
  Browser                      MySQL + Redis
```

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/             # Auth, Chat, Documents, Admin routes
│   │   ├── core/            # Config, security, middleware, Redis client
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # AI adapter, document parser, rule retriever
│   │   ├── prompts/rules/   # Patent review rule templates (JSON)
│   │   └── utils/           # Database, password hashing, seed users
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # Chat, message-bubble, common UI
│   │   ├── composables/     # Vue composables (chat, scroll, upload, etc.)
│   │   ├── services/        # API client, auth, documents, admin
│   │   ├── stores/          # Pinia stores (auth, chat, documents)
│   │   ├── views/           # Login, AdminUsers, SimplePatentChat
│   │   └── utils/           # Chat utilities, patent prompt templates
│   └── package.json
├── deploy/                  # Nginx config, systemd, supervisor, nohup scripts
├── docs/                    # Documentation and migration scripts
└── pic/                     # Static images
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- [Ollama](https://ollama.com) with a model installed (e.g., `ollama pull qwen3:8b`)

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your database credentials and secrets

# Start development server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at `http://localhost:8000/docs`

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The dev server runs at `http://localhost:5173` and proxies API requests to the backend.

## Configuration

Copy `backend/.env.example` to `backend/.env` and configure:

| Variable | Description | Required |
|----------|-------------|----------|
| `TOKEN_SECRET` | Secret key for JWT signing (min 32 chars) | Yes |
| `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` | Database connection | Yes |
| `OLLAMA_URL` | Ollama server URL | No (default: `http://localhost:11434`) |
| `OLLAMA_URLS` | Ollama server URLs (comma-separated) | No |
| `OLLAMA_MODEL` | Model name | No (default: `qwen3:8b`) |
| `OLLAMA_KEEP_ALIVE` | Model keep-alive duration | No (default: `5m`) |
| `REDIS_HOST` / `REDIS_PORT` | Redis for rate limiting | Optional |
| `CORS_ORIGINS` | Allowed CORS origins (JSON array) | No |
| `RATE_LIMIT_MAX` | Requests per minute | No (default: 100) |
| `DATABASE_URL` | Database connection string | Yes (if DB_* not set) |

## API Overview

| Endpoint | Description |
|----------|-------------|
| `POST /api/auth/login` | User login |
| `POST /api/auth/logout` | User logout (server-side token revocation) |
| `GET /api/auth/me` | Current user info |
| `POST /api/documents/upload` | Upload patent document |
| `GET /api/documents` | List user documents |
| `GET /api/documents/{id}` | Get document details |
| `POST /api/ai/chat` | Send chat message (SSE streaming) |
| `POST /api/ai/persist-partial` | Save partial AI response after user stop |
| `GET /api/ai/sessions` | List chat sessions |
| `GET /api/admin/users` | Admin: list users |
| `POST /api/admin/users` | Admin: create user |
| `POST /api/auth/users/{id}/force-logout` | Admin: force-logout user |

## Review Agents

The system includes four rule-based review agents defined as JSON templates:

| ID | Name | Purpose |
|----|------|---------|
| 1 | General Case Review | Standard patent case review |
| 2 | Patent Guidance | Patent audit guidance |
| 3 | Project Case Review | Special project case review |
| 5 | IPC Classification | IPC classification guidance |

Rules are loaded from `backend/app/prompts/rules/` and injected into the system prompt before sending to the LLM.

## Deploying

Example deployment files are provided in `deploy/`:

- **Nginx**: `deploy/nginx_iprs_site.conf` -- reverse proxy configuration
- **Systemd**: `deploy/systemd/` -- service unit files for backend and frontend
- **Supervisor**: `deploy/supervisor_iprs_backend.conf`
- **Shell scripts**: `deploy/nohup/` -- start/stop/status scripts

Typical production setup:

```
Nginx :80 → Frontend (static files)
Nginx /api → Uvicorn :8000 (backend)
```

## Performance Optimizations

### Frontend

- **SSE rAF Rendering**: `requestAnimationFrame` batch updates replace fixed 50ms `setTimeout`, syncing with browser paint frames for smoother streaming output
- **SSE Auto-Reconnect**: Exponential backoff retry (up to 3 attempts) on network interruption, accumulated content preserved across reconnects
- **Abort Preservation**: User-initiated stop flushes batcher buffers and persists partial AI response to both frontend state and backend database
- **Code Splitting**: `SimplePatentChat.vue` reduced 1204→1042 lines via extraction of `useSSEStream`, `useTemplateSelector`, and `ContentPreviewDialog`
- **Conversation History**: N+1 query eliminated -- backend JOINs document info in batch, frontend no longer makes extra API call per session
- **No Message Limit**: Removed the `.slice(-12)` constraint, full conversation history sent to AI

### Backend

- **Ollama Streaming**: Per-chunk read timeout (30s) prevents hanging connections; `keep_alive` reduced 24h→5m (OLLAMA_KEEP_ALIVE env)
- **Database Pool**: `pool_size` 5→10, `pool_timeout` 30s added; Redis `max_connections`=10
- **Dead Code**: Removed `ai_adapter.py`, duplicate `format_rules_as_prompt` (~230 lines), unused frontend components (~2,500 lines)
- **Error Visibility**: `logger.exception()` replaces flat `logger.error()` for chat persistence failures, including full stack traces
- **Multi-URL Ollama**: Configurable `OLLAMA_URLS` for failover; removed localhost fallback to avoid wasted retries

## Security Hardening

- **JWT Token Revocation**: Server-side logout via Redis JTI blacklist -- tokens are truly invalidated on logout, not just cleared client-side
- **Short-Lived Tokens**: Token expiry reduced from 24h to 2h, minimizing window of exposure if a token is leaked
- **Token Versioning**: `token_version` column on users table; admin can force-logout any user by incrementing their version, instantly invalidating all active tokens
- **Secret Strength Enforcement**: `TOKEN_SECRET` must be ≥32 characters at startup; app refuses to start with weak secrets
- **Seed Password Security**: `init_tables.py` generates random 16-char passwords with bcrypt hashing instead of hardcoded SHA256 hashes of known passwords
- **Upload Header Fix**: Removed manual `Content-Type: multipart/form-data` override that stripped the `boundary` parameter, causing failures with strict WAFs

## Recent Fixes

- **Login Redirect**: `window.location.href` → `router.push('/chat')` for proper SPA routing
- **Hardcoded System Prompt**: Removed from frontend, unified in backend `PATENT_SYSTEM_PROMPTS`
- **Session Rename UI**: Native `prompt()` replaced with Element Plus Dialog + Input
- **Watch Performance**: `watch(messages, {deep:true})` → `watch(() => messages.length)` to avoid deep traversal
- **JSON Parse Safety**: Dedicated try-catch for localStorage parsing with auto-cleanup on corruption
- **File Upload**: Variable naming `isLt20M` → `isLt20MB`; `hasattr` → `getattr` for file.size

## Initial Setup

Run `python init_tables.py` to create tables and seed users. **Passwords are randomly generated** and printed to the console once -- record them immediately. Change passwords after first login.

## Contributing

Contributions are welcome. Please open an issue to discuss proposed changes before submitting a pull request.

## License

MIT License

Copyright (c) 2025 IPRS Contributors
