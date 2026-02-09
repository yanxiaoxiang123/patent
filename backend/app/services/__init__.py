"""服务模块"""
from app.services.ollama import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    PATENT_SYSTEM_PROMPTS,
    IPC_SYSTEM_PROMPT,
    get_ollama_response_stream,
    get_ollama_response,
    validate_patent_relevance,
    is_ipc_mode,
    trim_to_strict_report,
)
from app.services.chat_persistence import (
    ChatPersistenceService,
    persist_chat,
    get_user_sessions,
    get_session_messages,
    delete_session,
)

__all__ = [
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "PATENT_SYSTEM_PROMPTS",
    "IPC_SYSTEM_PROMPT",
    "get_ollama_response_stream",
    "get_ollama_response",
    "validate_patent_relevance",
    "is_ipc_mode",
    "trim_to_strict_report",
    "ChatPersistenceService",
    "persist_chat",
    "get_user_sessions",
    "get_session_messages",
    "delete_session",
]
