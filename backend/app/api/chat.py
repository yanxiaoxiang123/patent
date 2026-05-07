"""聊天 API 模块"""
import json
import httpx
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, status
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel, Field

from app.services.ollama import (
    ChatMessage,
    ChatRequest as ServiceChatRequest,
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
    persist_chat,
    get_user_sessions,
    get_session_messages,
    delete_session,
)
from app.services.rule_retriever import get_rule_retriever
from app.core.security import parse_auth_header, TokenPayload
from app.core.config import OLLAMA_MODEL, OLLAMA_URLS

router = APIRouter(tags=["专利AI对话"])

# SSE 响应头
SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}


# ===================== Pydantic Models =====================

class ChatRequest(BaseModel):
    """聊天请求验证"""
    messages: list = Field(..., min_length=1, description="消息列表不能为空")
    stream: bool = True
    model: str = Field(default=OLLAMA_MODEL, pattern=r"^[\w:-]+$", description="模型名称格式不正确")
    max_tokens: int = Field(default=40960, ge=100, le=40960, description="max_tokens 范围: 100-40960")
    passthrough: bool = False
    template_id: Optional[int] = Field(default=None, ge=1, le=100, description="模板ID无效")
    session_id: Optional[int] = Field(default=None, ge=1, description="会话ID无效")
    document_id: Optional[int] = Field(default=None, ge=1, description="文档ID无效")


# ===================== 认证 =====================

def get_user_id_from_request(request: Request) -> Optional[int]:
    """从请求中获取用户 ID"""
    token_payload: Optional[TokenPayload] = parse_auth_header(request.headers.get("Authorization"))
    if token_payload:
        return token_payload.user_id
    return None


# ===================== 消息构建 =====================

def get_msg_attr(msg, attr: str, default):
    """安全获取消息属性（兼容字典和 ChatMessage 对象）"""
    if isinstance(msg, dict):
        return msg.get(attr, default)
    return getattr(msg, attr, default)

def build_system_messages(messages: list, user_message: str) -> list:
    """构建系统消息"""
    system_contents = [get_msg_attr(m, "content", "") for m in messages if get_msg_attr(m, "role", "") == "system"]
    system_joined = "\n\n".join(system_contents)
    ipc_mode = is_ipc_mode(system_joined, user_message)
    result = []

    for msg in messages:
        role = get_msg_attr(msg, "role", "user")
        content = get_msg_attr(msg, "content", "")

        if role == "system":
            if ipc_mode:
                result.append(ChatMessage(role="system", content=content))
            else:
                result.append(ChatMessage(
                    role="system",
                    content=PATENT_SYSTEM_PROMPTS["intermediate"] if "专利" not in content else content
                ))
        elif role == "user" and not any(get_msg_attr(m, "role", "") == "user" for m in result):
            result.append(ChatMessage(
                role="user",
                content=content if ipc_mode else f"用户问题：{content}\n\n请专门从专利角度回答这个问题。"
            ))
        else:
            result.append(ChatMessage(role=role, content=content))

    if not any(m.role == "system" for m in result):
        result.insert(0, ChatMessage(
            role="system",
            content=IPC_SYSTEM_PROMPT if ipc_mode else PATENT_SYSTEM_PROMPTS["intermediate"]
        ))

    return result


# ===================== 规则加载 =====================

async def load_strict_template(template_id: int) -> Optional[str]:
    """加载严格模板"""
    if template_id not in [1, 2, 3, 5]:
        return None
    rule_retriever = get_rule_retriever()
    return rule_retriever.get_system_prompt(template_id=template_id, case_type=None)


# ===================== 流式响应 =====================

async def create_stream_generator(
    messages: list,
    model: str,
    chat_request: ChatRequest,
    user_id: Optional[int],
    strict_system_prompt: Optional[str] = None
):
    """创建流式响应生成器"""
    assistant_text = ""
    try:
        # messages 是从前端传来的字典列表，需要转换为 ChatMessage 对象
        if strict_system_prompt:
            first_msg = messages[0] if messages else {}
            first_content = first_msg.get("content", "") if isinstance(first_msg, dict) else str(first_msg)
            service_messages = [
                ChatMessage(role="system", content=strict_system_prompt),
                ChatMessage(role="user", content=first_content),
            ]
        else:
            user_msg = next((m for m in messages if isinstance(m, dict) and m.get("role") == "user"), {})
            user_content = user_msg.get("content", "") if isinstance(user_msg, dict) else ""
            service_messages = build_system_messages(messages, user_content)

        async for chunk in get_ollama_response_stream(service_messages, model, prefer_chat=True):
            content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
            thinking = chunk.get("choices", [{}])[0].get("delta", {}).get("thinking", "")
            if content:
                assistant_text += content

            # 构建 SSE 格式 - 使用 json.dumps 确保有效的 JSON
            sse_data = {
                "choices": [{
                    "delta": {
                        "content": content,
                        "thinking": thinking
                    }
                }]
            }
            yield {"event": "message", "data": json.dumps(sse_data, ensure_ascii=False), "id": "", "retry": None}

        # 获取用户消息用于持久化
        if strict_system_prompt:
            user_message = messages[0].get("content", "") if messages and isinstance(messages[0], dict) else ""
        else:
            user_message = user_msg.get("content", "") if isinstance(user_msg, dict) else ""

        # 转换为 ChatMessage 对象列表
        chat_messages = []
        for m in messages:
            if isinstance(m, dict):
                chat_messages.append(ChatMessage(role=m.get("role", "user"), content=m.get("content", "")))

        await persist_chat(
            ServiceChatRequest(
                messages=chat_messages,
                model=model,
                session_id=chat_request.session_id,
                document_id=chat_request.document_id,
            ),
            user_message,
            assistant_text,
            user_id
        )

        # 发送完成信号
        yield {"event": "done", "data": "[DONE]", "id": "", "retry": None}

    except Exception as e:
        err_msg = str(e)
        if "模型配置或请求参数错误" in err_msg:
            user_msg = "抱歉，模型配置或请求参数错误，请联系管理员检查模型配置。"
        elif "无法连接到 Ollama 服务" in err_msg:
            user_msg = "抱歉，无法连接 AI 服务，请稍后重试。"
        else:
            user_msg = "抱歉，AI 服务暂时不可用，请稍后重试。"
        error_data = {"choices": [{"delta": {"content": user_msg}}]}
        yield {"event": "error", "data": json.dumps(error_data, ensure_ascii=False), "id": "", "retry": None}
        yield {"event": "done", "data": "[DONE]", "id": "", "retry": None}


async def create_patent_error_stream():
    """创建专利相关性错误流"""
    error = {"choices": [{"delta": {"content": "抱歉，我是专门的专利 AI 助手，只能回答与专利相关的问题。"}}]}
    yield {"event": "message", "data": json.dumps(error, ensure_ascii=False), "id": "", "retry": None}
    yield {"event": "done", "data": "[DONE]", "id": "", "retry": None}


# ===================== 测试端点 =====================

@router.get("/test-ollama")
async def test_ollama_connection():
    """测试 Ollama 连接（调试用）"""
    last_error = None
    for ollama_url in OLLAMA_URLS:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                tags_resp = await client.get(f"{ollama_url}/api/tags")
                tags_data = tags_resp.json()

                chat_resp = await client.post(
                    f"{ollama_url}/api/chat",
                    json={
                        "model": OLLAMA_MODEL,
                        "messages": [{"role": "user", "content": "你好"}],
                        "stream": False,
                    }
                )
                chat_data = chat_resp.json()

                return {
                    "status": "ok",
                    "ollama_url": ollama_url,
                    "models": tags_data.get("models", []),
                    "chat_test": "success" if "message" in chat_data else chat_data,
                }
        except Exception as e:
            last_error = e

    return {
        "status": "error",
        "ollama_url": OLLAMA_URLS[0],
        "error": str(last_error) if last_error else "unknown error",
    }


# ===================== 聊天处理 =====================

async def handle_passthrough_chat(
    chat_request: ChatRequest,
    user_id: Optional[int],
    strict_system_prompt: Optional[str]
) -> ChatResponse:
    """处理 passthrough 模式聊天"""
    service_messages = [
        ChatMessage(role="system", content=strict_system_prompt) if strict_system_prompt else None,
        ChatMessage(role="user", content=chat_request.messages[0].get("content", "") if chat_request.messages else ""),
    ]
    service_messages = [m for m in service_messages if m]

    response = await get_ollama_response(service_messages, chat_request.model, prefer_chat=True)
    if strict_system_prompt:
        response = trim_to_strict_report(chat_request.template_id, response.strip())

    user_message = chat_request.messages[0].get("content", "") if chat_request.messages else ""
    await persist_chat(
        ServiceChatRequest(messages=service_messages, model=chat_request.model),
        user_message,
        response,
        user_id
    )

    return ChatResponse(
        response=response,
        model=chat_request.model,
        usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    )


async def handle_regular_chat(
    chat_request: ChatRequest,
    user_id: Optional[int]
) -> ChatResponse:
    """处理普通聊天"""
    user_message = next((m for m in chat_request.messages if m.get("role") == "user"), {}).get("content", "")
    service_messages = build_system_messages(chat_request.messages, user_message)
    response = await get_ollama_response(service_messages, chat_request.model)

    await persist_chat(
        ServiceChatRequest(messages=service_messages, model=chat_request.model),
        user_message,
        response,
        user_id
    )

    return ChatResponse(
        response=response,
        model=chat_request.model,
        usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    )


# ===================== 主 API =====================

@router.post("/chat")
async def chat_completion(chat_request: ChatRequest, request: Request):
    """聊天完成 API"""
    user_id = get_user_id_from_request(request)

    # 加载严格模板
    strict_system_prompt = None
    if chat_request.template_id in [1, 2, 3, 5]:
        strict_system_prompt = await load_strict_template(chat_request.template_id)
        if not strict_system_prompt:
            raise HTTPException(
                status_code=500,
                detail=f"加载审核规则失败：template_id={chat_request.template_id}"
            )

    passthrough = chat_request.passthrough or strict_system_prompt is not None

    # Passthrough 模式
    if passthrough:
        if chat_request.stream:
            return EventSourceResponse(
                create_stream_generator(
                    chat_request.messages,
                    chat_request.model,
                    chat_request,
                    user_id,
                    strict_system_prompt
                ),
                headers=SSE_HEADERS
            )
        return await handle_passthrough_chat(chat_request, user_id, strict_system_prompt)

    # 专利相关性检查
    user_message = next((m for m in chat_request.messages if m.get("role") == "user"), {}).get("content", "")
    if not validate_patent_relevance(user_message):
        return EventSourceResponse(create_patent_error_stream(), headers=SSE_HEADERS)

    # 普通聊天
    if chat_request.stream:
        return EventSourceResponse(
            create_stream_generator(
                chat_request.messages,
                chat_request.model,
                chat_request,
                user_id
            ),
            headers=SSE_HEADERS
        )

    return await handle_regular_chat(chat_request, user_id)


# ===================== 会话管理 =====================

@router.get("/sessions")
async def list_sessions(request: Request):
    """获取会话列表"""
    user_id = get_user_id_from_request(request)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    return await get_user_sessions(user_id)


@router.get("/sessions/{session_id}")
async def get_session(session_id: int, request: Request):
    """获取会话消息"""
    if session_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的会话ID")

    user_id = get_user_id_from_request(request)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")

    result = await get_session_messages(session_id, user_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    return result


@router.delete("/sessions/{session_id}")
async def remove_session(session_id: int, request: Request):
    """删除会话"""
    if session_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的会话ID")

    user_id = get_user_id_from_request(request)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")

    success = await delete_session(session_id, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    return {"message": "会话已删除"}


# ===================== 模型管理 =====================

@router.get("/models")
async def list_models():
    """获取可用模型列表"""
    import httpx
    try:
        from app.core.config import OLLAMA_URL
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            if response.status_code == 200:
                return {"models": [
                    {"id": m["name"], "name": m["name"], "size": m.get("size", 0)}
                    for m in response.json().get("models", [])
                ]}
    except Exception:
        pass
    return {"models": [{"id": OLLAMA_MODEL, "name": OLLAMA_MODEL, "size": 0}]}


@router.get("/status")
async def get_ai_status():
    """获取 AI 服务状态"""
    import httpx
    try:
        from app.core.config import OLLAMA_URL
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            if response.status_code == 200:
                return {
                    "status": "online",
                    "models": [m["name"] for m in response.json().get("models", [])],
                    "message": "AI 服务正常运行"
                }
            return {"status": "error", "models": [], "message": "AI 服务响应异常"}
    except Exception as e:
        return {"status": "offline", "models": [], "message": f"AI 服务离线: {str(e)}"}
