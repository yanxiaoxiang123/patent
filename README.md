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
- **Real-Time Streaming** -- SSE-based streaming responses with thinking process visualization
- **Interactive Chat** -- Multi-session chat interface with message persistence, document context, and markdown rendering
- **User Management** -- Token-based authentication with admin panel for user administration
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
| `TOKEN_SECRET` | Secret key for JWT token signing | Yes |
| `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` | Database connection | Yes |
| `OLLAMA_URL` | Ollama server URL | No (default: `http://localhost:11434`) |
| `OLLAMA_MODEL` | Model name | No (default: `qwen3:8b`) |
| `REDIS_HOST` / `REDIS_PORT` | Redis for rate limiting | Optional |
| `CORS_ORIGINS` | Allowed CORS origins (JSON array) | No |
| `RATE_LIMIT_MAX` | Requests per minute | No (default: 100) |

## API Overview

| Endpoint | Description |
|----------|-------------|
| `POST /api/auth/login` | User login |
| `POST /api/auth/logout` | User logout |
| `GET /api/auth/me` | Current user info |
| `POST /api/documents/upload` | Upload patent document |
| `GET /api/documents` | List user documents |
| `GET /api/documents/{id}` | Get document details |
| `POST /api/ai/chat` | Send chat message (SSE streaming) |
| `GET /api/ai/sessions` | List chat sessions |
| `GET /api/admin/users` | Admin: list users |
| `POST /api/admin/users` | Admin: create user |

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

## Contributing

Contributions are welcome. Please open an issue to discuss proposed changes before submitting a pull request.

## License

MIT License

Copyright (c) 2025 IPRS Contributors
