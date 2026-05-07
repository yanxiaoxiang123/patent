import importlib.util
import asyncio
import sys
from pathlib import Path

import httpx
import pytest


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

OLLAMA_PATH = BACKEND_DIR / "app" / "services" / "ollama.py"
OLLAMA_SPEC = importlib.util.spec_from_file_location("test_ollama_module", OLLAMA_PATH)
ollama = importlib.util.module_from_spec(OLLAMA_SPEC)
assert OLLAMA_SPEC.loader is not None
OLLAMA_SPEC.loader.exec_module(ollama)

ChatMessage = ollama.ChatMessage
get_ollama_response = ollama.get_ollama_response


def test_get_ollama_response_falls_back_to_next_base_url_on_connect_error(monkeypatch):
    attempted_urls = []

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"message": {"content": "fallback ok"}}

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json):
            attempted_urls.append(url)
            if url.startswith("http://bad-host:11434"):
                raise httpx.ConnectError("boom")
            return FakeResponse()

    monkeypatch.setattr(ollama, "OLLAMA_URLS", ["http://bad-host:11434", "http://127.0.0.1:11434"])
    monkeypatch.setattr(ollama.httpx, "AsyncClient", FakeAsyncClient)

    result = asyncio.run(
        get_ollama_response(
            [ChatMessage(role="user", content="你好")],
            model="qwen3:8b",
            prefer_chat=True,
        )
    )

    assert result == "fallback ok"
    assert attempted_urls == [
        "http://bad-host:11434/api/chat",
        "http://127.0.0.1:11434/api/chat",
    ]


def test_get_ollama_base_urls_appends_local_fallbacks(monkeypatch):
    monkeypatch.setattr(ollama, "OLLAMA_URLS", ["http://fake-ollama-host.example.com:11434"])

    assert ollama.get_ollama_base_urls() == [
        "http://fake-ollama-host.example.com:11434",
        "http://localhost:11434",
        "http://127.0.0.1:11434",
    ]
