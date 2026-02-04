from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import asyncio
import httpx
from sse_starlette.sse import EventSourceResponse
import os
from sqlalchemy import select, func
from app.utils.database import AsyncSessionLocal
from app.models import ChatSession as ChatSessionModel, ChatMessage as ChatMessageModel
from app.services.rule_retriever import get_rule_retriever

router = APIRouter()


def _trim_to_strict_report(template_id: Optional[int], text: str) -> str:
    """修剪报告到指定起始标记"""
    if not template_id or not isinstance(text, str):
        return text
    start_marker = None
    if template_id == 1:
        start_marker = "① 案件类型判定"
    elif template_id == 3:
        start_marker = "① 通用规则预审（A–F）"
    if not start_marker:
        return text
    idx = text.find(start_marker)
    if idx < 0:
        return text
    return text[idx:].strip()


# Ollama 配置（支持多实例轮询与失败回退）
_env_urls = os.getenv("OLLAMA_URLS", "").strip()
if not _env_urls:
    _fallback_single = os.getenv("OLLAMA_URL", "http://localhost:11434").strip()
    OLLAMA_URLS: List[str] = [_fallback_single]
else:
    OLLAMA_URLS = [u.strip() for u in _env_urls.split(",") if u.strip()]
if not OLLAMA_URLS:
    OLLAMA_URLS = ["http://localhost:11434"]
_rr_index = 0
_rr_lock = asyncio.Lock()

async def _pick_ollama_url() -> str:
    global _rr_index
    async with _rr_lock:
        url = OLLAMA_URLS[_rr_index % len(OLLAMA_URLS)]
        _rr_index += 1
        return url

def _next_url(current: str) -> str:
    if len(OLLAMA_URLS) <= 1:
        return current
    try:
        idx = OLLAMA_URLS.index(current)
    except ValueError:
        return OLLAMA_URLS[0]
    return OLLAMA_URLS[(idx + 1) % len(OLLAMA_URLS)]

async def _warm_one(base: str, model: str):
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            await client.post(
                f"{base}/api/generate",
                json={
                    "model": model,
                    "prompt": ".",
                    "system": "",
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "top_p": 1.0,
                        "max_tokens": 1,
                        "keep_alive": "24h"
                    }
                }
            )
    except Exception:
        return

@router.post("/warm")
async def warm_models(model: str = "qwen3:8b"):
    tasks = [asyncio.create_task(_warm_one(u, model)) for u in OLLAMA_URLS]
    await asyncio.gather(*tasks, return_exceptions=True)
    return {"warmed": OLLAMA_URLS, "model": model}

class ChatMessage(BaseModel):
    role: str  # user, assistant, system
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    stream: bool = True
    model: str = "qwen3:8b"
    max_tokens: int = 40960
    temperature: float = 0.7
    passthrough: bool = False
    template_id: Optional[int] = None
    session_id: Optional[int] = None
    document_id: Optional[int] = None

class ChatResponse(BaseModel):
    response: str
    model: str
    usage: Dict[str, int]

PATENT_SYSTEM_PROMPTS = {
    "beginner": """你是一个专业的专利 AI 助手，专门为专利初学者提供咨询服务。你的回答必须严格限制在专利领域范围内。

回答原则：
- 使用简单易懂的语言，避免过于专业的术语
- 详细解释专利概念和流程
- 提供实用的操作建议
- 耐心回答基础问题

服务范围：
1. 专利基础知识普及
2. 申请流程指导
3. 文件准备建议
4. 常见问题解答

严禁回答非专利相关的问题。如果用户询问非专利内容，请礼貌地引导回专利话题。""",

    "intermediate": """你是一个专业的专利 AI 助手，专门为有一定专利知识的用户提供咨询服务。你的回答必须严格限制在专利领域范围内。

回答原则：
- 使用专业但不过于技术化的语言
- 提供深入的技术分析
- 引用相关法律法规和案例
- 给出专业的操作建议

服务范围：
1. 专利撰写和审查
2. 专利检索策略
3. 侵权风险评估
4. 维权策略制定
5. 专利价值评估

严禁回答非专利相关的问题。如果用户询问非专利内容，请礼貌地引导回专利话题。""",

    "expert": """你是一个专业的专利 AI 助手，专门为专利从业者提供高级咨询服务。你的回答必须严格限制在专利领域范围内。

回答原则：
- 使用专业的专利术语和表达
- 提供深入的技术分析和法理分析
- 引用具体的法条、案例和判例
- 给出专家级的操作建议

服务范围：
1. 复杂专利申请策略
2. 高级检索和分析
3. 专利诉讼支持
4. 专利组合管理
5. 国际专利事务

严禁回答非专利相关的问题。如果用户询问非专利内容，请礼貌地引导回专利话题。"""
}

IPC_SYSTEM_PROMPT = """你是一个专业的专利分类专家，专门为用户提供国际专利分类（IPC）分析服务。

回答原则：
- 严格基于用户提供的技术内容给出 IPC 分类建议
- 仅输出 IPC 分类相关结论与理由，不输出新颖性/创造性/实用性、撰写建议、风险提示等可专利性或审核内容
- 分类号格式必须正确（如：G06F 16/953）
"""

def _build_ollama_prompt(messages: List[ChatMessage]) -> str:
    parts = []
    for msg in messages:
        role = msg.role.upper()
        parts.append(f"{role}: {msg.content}\n")
    return "\n".join(parts)


async def get_ollama_response_stream(
    messages: List[ChatMessage],
    model: str = "qwen3:8b",
    is_strict_template: bool = False,
    think: bool = True,
    max_tokens: int = 40960,
    prefer_chat: bool = False,
    force_system_prepend: bool = False,  # 强制将 system prompt 合并到用户消息
):
    system_parts = [msg.content for msg in messages if msg.role == "system"]
    system_prompt = "\n\n".join(system_parts) if system_parts else ""
    conversation_messages = [msg for msg in messages if msg.role != "system"]

    # 如果 force_system_prepend 为 True，将 system prompt 合并到第一个用户消息
    if force_system_prepend and system_prompt:
        first_user_msg = conversation_messages[0] if conversation_messages else None
        if first_user_msg and first_user_msg.role == "user":
            # 在用户消息前面加上 system prompt
            combined_content = f"""【系统指令】
{system_prompt}

【用户输入】
{first_user_msg.content}"""
            conversation_messages[0] = ChatMessage(role="user", content=combined_content)
            # 清空 system_prompt，因为已经合并到用户消息了
            system_prompt = ""

    prompt = _build_ollama_prompt(conversation_messages)
    
    # 严格模板使用更低的温度和更确定性的参数
    temperature = 0.3 if is_strict_template else 0.7
    top_p = 0.8 if is_strict_template else 0.9
    
    try:
        base = await _pick_ollama_url()
        async with httpx.AsyncClient(timeout=300.0) as client:
            try:
                api_path = "/api/chat" if prefer_chat else "/api/generate"
                payload = (
                    {
                        "model": model,
                        "messages": [{"role": m.role, "content": m.content} for m in messages],
                        "think": True,
                        "stream": True,
                        "options": {
                            "temperature": temperature,
                            "top_p": top_p,
                            "num_ctx": 32768,  # 显式设置上下文窗口
                            "max_tokens": max_tokens,
                            "keep_alive": "24h",
                            "repeat_penalty": 1.1 if is_strict_template else 1.0,
                        },
                    }
                    if prefer_chat
                    else {
                        "model": model,
                        "prompt": prompt,
                        "system": system_prompt,
                        "think": True,
                        "stream": True,
                        "options": {
                            "temperature": temperature,
                            "top_p": top_p,
                            "num_ctx": 32768,  # 显式设置上下文窗口
                            "max_tokens": max_tokens,
                            "keep_alive": "24h",
                            "repeat_penalty": 1.1 if is_strict_template else 1.0,
                        },
                    }
                )
                # 调试日志：打印发送给 Ollama 的 system prompt
                print(f"[DEBUG] get_ollama_response_stream: prefer_chat={prefer_chat}")
                print(f"[DEBUG] system_prompt长度={len(system_prompt)}, prompt长度={len(prompt)}")
                print(f"[DEBUG] messages数量={len(messages)}, is_strict_template={is_strict_template}")

                # 打印完整的 payload 结构（用于调试）
                if prefer_chat:
                    msg_preview = [{"role": m.role, "content": m.content[:50]+"..." if len(m.content) > 50 else m.content} for m in messages]
                    print(f"[DEBUG] messages 预览: {msg_preview}")
                else:
                    print(f"[DEBUG] system 内容长度: {len(system_prompt)}")
                    print(f"--- SYSTEM CONTENT START ---")
                    print(system_prompt)
                    print(f"--- SYSTEM CONTENT END ---")
                    print(f"[DEBUG] prompt 内容长度: {len(prompt)}")
                    print(f"--- PROMPT CONTENT START ---")
                    print(prompt)
                    print(f"--- PROMPT CONTENT END ---")

                async with client.stream("POST", f"{base}{api_path}", json=payload) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        raise Exception(f"Ollama API 错误: {response.status_code} - {error_text.decode('utf-8', errors='ignore')}")

                    try:
                        async for line in response.aiter_lines():
                            if not line or not line.strip():
                                continue
                            try:
                                data = json.loads(line)
                            except json.JSONDecodeError:
                                continue

                            if prefer_chat:
                                message = data.get("message", {})
                                if message.get("thinking"):
                                    yield {"choices": [{"delta": {"thinking": message.get("thinking")}}]}
                                if message.get("content"):
                                    yield {"choices": [{"delta": {"content": message.get("content")}}]}
                            else:
                                if "thinking" in data:
                                    thinking = data.get("thinking")
                                    if thinking:
                                        yield {"choices": [{"delta": {"thinking": thinking}}]}
                                if "response" in data:
                                    content = data["response"]
                                    if content:
                                        yield {"choices": [{"delta": {"content": content}}]}

                            if data.get("done"):
                                break
                    except asyncio.CancelledError:
                        return
            except (httpx.ConnectError, httpx.ReadTimeout):
                fallback = _next_url(base)
                api_path = "/api/chat" if prefer_chat else "/api/generate"
                payload = (
                    {
                        "model": model,
                        "messages": [{"role": m.role, "content": m.content} for m in messages],
                        "think": True,
                        "stream": True,
                        "options": {
                            "temperature": temperature,
                            "top_p": top_p,
                            "num_ctx": 32768,
                            "max_tokens": min(max_tokens, 4000),
                            "keep_alive": "24h",
                            "repeat_penalty": 1.1 if is_strict_template else 1.0,
                        },
                    }
                    if prefer_chat
                    else {
                        "model": model,
                        "prompt": prompt,
                        "system": system_prompt,
                        "think": True,
                        "stream": True,
                        "options": {
                            "temperature": temperature,
                            "top_p": top_p,
                            "num_ctx": 32768,
                            "max_tokens": min(max_tokens, 4000),
                            "keep_alive": "24h",
                            "repeat_penalty": 1.1 if is_strict_template else 1.0,
                        },
                    }
                )
                async with client.stream("POST", f"{fallback}{api_path}", json=payload) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        raise Exception(f"Ollama API 错误: {response.status_code} - {error_text.decode('utf-8', errors='ignore')}")
                    try:
                        async for line in response.aiter_lines():
                            if not line or not line.strip():
                                continue
                            try:
                                data = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            if prefer_chat:
                                message = data.get("message", {})
                                if message.get("thinking"):
                                    yield {"choices": [{"delta": {"thinking": message.get("thinking")}}]}
                                if message.get("content"):
                                    yield {"choices": [{"delta": {"content": message.get("content")}}]}
                            else:
                                if "thinking" in data:
                                    thinking = data.get("thinking")
                                    if thinking:
                                        yield {"choices": [{"delta": {"thinking": thinking}}]}
                                if "response" in data:
                                    content = data["response"]
                                    if content:
                                        yield {"choices": [{"delta": {"content": content}}]}
                            if data.get("done"):
                                break
                    except asyncio.CancelledError:
                        return
    except httpx.ConnectError:
        raise Exception("无法连接到 Ollama 服务，请确保服务正在运行")
    except Exception as e:
        raise Exception(f"Ollama API 调用失败: {str(e)}")


async def get_ollama_response(
    messages: List[ChatMessage],
    model: str = "qwen3:8b",
    is_strict_template: bool = False,
    think: bool = True,
    max_tokens: int = 40960,
    prefer_chat: bool = False,
) -> str:
    system_parts = [msg.content for msg in messages if msg.role == "system"]
    system_prompt = "\n\n".join(system_parts) if system_parts else ""
    conversation_messages = [msg for msg in messages if msg.role != "system"]
    prompt = _build_ollama_prompt(conversation_messages)
    temperature = 0.3 if is_strict_template else 0.7
    top_p = 0.8 if is_strict_template else 0.9
    repeat_penalty = 1.1 if is_strict_template else 1.0
    try:
        base = await _pick_ollama_url()
        async with httpx.AsyncClient(timeout=300.0) as client:
            try:
                api_path = "/api/chat" if prefer_chat else "/api/generate"
                payload = (
                    {
                        "model": model,
                        "messages": [{"role": m.role, "content": m.content} for m in messages],
                        "think": True,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "top_p": top_p,
                            "num_ctx": 32768,
                            "repeat_penalty": repeat_penalty,
                            "max_tokens": max_tokens,
                            "keep_alive": "24h",
                        },
                    }
                    if prefer_chat
                    else {
                        "model": model,
                        "prompt": prompt,
                        "system": system_prompt,
                        "think": True,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "top_p": top_p,
                            "num_ctx": 32768,
                            "repeat_penalty": repeat_penalty,
                            "max_tokens": max_tokens,
                            "keep_alive": "24h",
                        },
                    }
                )
                response = await client.post(f"{base}{api_path}", json=payload)
            except (httpx.ConnectError, httpx.ReadTimeout):
                fallback = _next_url(base)
                response = await client.post(f"{fallback}{api_path}", json=payload)

            if response.status_code != 200:
                raise Exception(f"Ollama API 错误: {response.status_code} - {response.text}")

            data = response.json()
            if prefer_chat:
                message = data.get("message", {})
                return message.get("content", "")
            return data.get("response", "")

    except Exception as e:
        raise Exception(f"Ollama API 调用失败: {str(e)}")


def validate_patent_relevance(content: str) -> bool:
    patent_keywords = [
        "专利", "发明", "实用新型", "外观设计", "申请", "审查", "权利要求",
        "说明书", "附图", "摘要", "优先权", "新颖性", "创造性", "实用性",
        "侵权", "维权", "许可", "转让", "检索", "分析", "评估", "撰写",
        "专利局", "知识产权", "专有技术", "技术秘密", "ipc", "国际专利分类", "分类号"
    ]

    content_lower = content.lower()
    return any(keyword in content_lower for keyword in patent_keywords)

DEFAULT_CHAT_USER_ID = 1


def get_user_id_from_request(request: Request) -> Optional[int]:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1].strip()
    prefix = "simple_token_"
    if not token.startswith(prefix):
        return None
    payload = token[len(prefix):]
    if not payload:
        return None
    user_id_str = payload.split("_", 1)[0]
    try:
        return int(user_id_str)
    except ValueError:
        return None


async def persist_chat(request: ChatRequest, user_message: str, assistant_message: str, user_id: Optional[int]):
    try:
        async with AsyncSessionLocal() as session:
            effective_user_id = user_id or DEFAULT_CHAT_USER_ID
            chat_session = None
            if request.session_id:
                chat_session = await session.get(ChatSessionModel, request.session_id)
            if chat_session is None:
                title = user_message[:50] if user_message else "对话会话"
                chat_session = ChatSessionModel(
                    user_id=effective_user_id,
                    title=title,
                    model=request.model,
                    document_id=request.document_id,
                )
                session.add(chat_session)
                await session.flush()
            result = await session.execute(
                select(func.count(ChatMessageModel.id)).where(ChatMessageModel.session_id == chat_session.id)
            )
            base_index = result.scalar() or 0
            user_msg = ChatMessageModel(
                session_id=chat_session.id,
                user_id=effective_user_id,
                role="user",
                content=user_message,
                model=request.model,
                document_id=request.document_id,
                message_index=base_index + 1,
            )
            assistant_msg = ChatMessageModel(
                session_id=chat_session.id,
                role="assistant",
                content=assistant_message,
                model=request.model,
                document_id=request.document_id,
                message_index=base_index + 2,
            )
            session.add_all([user_msg, assistant_msg])
            chat_session.last_message_at = func.now()
            await session.commit()
    except Exception as e:
        print(f"chat log error: {e}")


@router.post("/chat")
async def chat_completion(chat_request: ChatRequest, request: Request):
    print(f"[DEBUG] chat_completion 被调用!")
    try:
        template_id = getattr(chat_request, "template_id", None)
        print(f"[DEBUG] template_id={template_id}, type={type(template_id)}")
        strict_system_prompt = None

        # 必须使用 RAG 动态规则（从 rules 文件加载）
        if template_id in [1, 3]:
            rule_retriever = get_rule_retriever()
            strict_system_prompt = rule_retriever.get_system_prompt(
                template_id=template_id,
                case_type=None  # 让 AI 自己判断案件类型
            )
            if not strict_system_prompt:
                raise HTTPException(
                    status_code=500,
                    detail=f"加载审核规则失败：template_id={template_id}，请检查 rules 文件是否存在且格式正确"
                )
            print(f"[DEBUG] 已加载 rules 规则，template_id={template_id}")

            # 以下是之前的回退逻辑，已注释不再使用
            # if template_id == 1:
            #     strict_system_prompt = GENERAL_CASE_AUDIT_SYSTEM_PROMPT
            # elif template_id == 3:
            #     strict_system_prompt = PROJECT_CASE_AUDIT_SYSTEM_PROMPT

        sse_headers = {
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }

        passthrough = getattr(chat_request, "passthrough", False) or strict_system_prompt is not None
        passthrough_messages = chat_request.messages
        if strict_system_prompt:
            first_user = next((m for m in chat_request.messages if m.role == "user"), None)
            user_payload = first_user.content if first_user else ""
            passthrough_messages = [
                ChatMessage(role="system", content=strict_system_prompt),
                ChatMessage(role="user", content=user_payload),
            ]
            print(f"[DEBUG] strict_system_prompt 已设置，passthrough_messages 数量: {len(passthrough_messages)}")
            print(f"[DEBUG] passthrough_messages[0].role: {passthrough_messages[0].role}, content长度: {len(passthrough_messages[0].content)}")
        else:
            print(f"[DEBUG] strict_system_prompt 为 None，template_id={template_id}")

        if passthrough:
            user_message = ""
            for msg in passthrough_messages:
                if msg.role == "user":
                    user_message = msg.content
                    break

            user_id = get_user_id_from_request(request)

            if chat_request.stream:
                async def stream_generator():
                    assistant_text = ""
                    try:
                        # 禁用所有校验逻辑，直接流式输出
                        # 使用 prefer_chat=False（/api/generate 端点），因为它的 system 字段更明确
                        async for chunk in get_ollama_response_stream(
                            passthrough_messages,
                            chat_request.model,
                            is_strict_template=False,
                            think=True,
                            max_tokens=chat_request.max_tokens,
                            prefer_chat=False,  # 使用 /api/generate 端点，system 作为独立字段
                            force_system_prepend=True,  # 备用：将 system prompt 合并到用户消息
                        ):
                            try:
                                delta = chunk.get("choices", [])[0].get("delta", {})
                                content = delta.get("content", "")
                            except Exception:
                                content = ""
                            if content:
                                assistant_text += content
                            yield f"{json.dumps(chunk)}\n\n"

                        await persist_chat(chat_request, user_message, assistant_text, user_id)
                        # if is_strict:
                        #     trimmed = _trim_to_strict_report(template_id, assistant_text.strip())
                        #     assistant_text = trimmed
                        #
                        # if is_strict and not _format_ok(template_id, assistant_text):
                        #     if template_id == 1:
                        #         required_outline = "① 案件类型判定；② 通用规则预审（A–F）；③ 分类型审核清单；④ 结论与建议"
                        #     elif template_id == 3:
                        #         required_outline = "① 通用规则预审（A–F）；② 领域审查；③ 格式审查（专案硬指标）；④ 内容审查（含新颖性/创造性）；结论与建议"
                        #     else:
                        #         required_outline = ""
                        #     repair_user = (
                        #         "你刚才的输出没有严格遵循"最终输出格式"。"
                        #         "请在不新增事实/不编造内容的前提下，将原输出重排为最终输出格式，并补齐缺失章节。"
                        #         "只输出最终报告正文"
                        #         "必须使用模板中的章节标题原样输出。\n"
                        #         f"必须包含章节顺序：{required_outline}\n\n"
                        #         f"【原输出】\n{assistant_text}"
                        #     )
                        #     yield f"{json.dumps({'iprs': {'replace': True}, 'choices': [{'delta': {'content': ''}}]})}\n\n"
                        #     assistant_text = ""
                        #     async for rchunk in get_ollama_response_stream(
                        #         [
                        #             ChatMessage(role="system", content=strict_system_prompt),
                        #             ChatMessage(role="user", content=repair_user),
                        #         ],
                        #         chat_request.model,
                        #         is_strict_template=True,
                        #         think=False,
                        #         max_tokens=chat_request.max_tokens,
                        #         prefer_chat=True,
                        #     ):
                        #         try:
                        #             rdelta = rchunk.get("choices", [])[0].get("delta", {})
                        #             rcontent = rdelta.get("content", "")
                        #         except Exception:
                        #             rcontent = ""
                        #         if rcontent:
                        #             assistant_text += rcontent
                        #         yield f"{json.dumps(rchunk)}\n\n"
                        #     assistant_text = _trim_to_strict_report(template_id, assistant_text.strip())

                        await persist_chat(chat_request, user_message, assistant_text, user_id)
                        yield "[DONE]\n\n"
                    except Exception as e:
                        error_chunk = {
                            "choices": [{
                                "delta": {
                                    "content": f"抱歉，AI 服务暂时不可用：{str(e)}"
                                }
                            }]
                        }
                        yield f"{json.dumps(error_chunk)}\n\n"
                        yield "[DONE]\n\n"

                return EventSourceResponse(stream_generator(), headers=sse_headers)

            # 禁用校验，直接返回结果
            response = await get_ollama_response(
                passthrough_messages,
                chat_request.model,
                is_strict_template=False,
                think=True,
                max_tokens=chat_request.max_tokens,
                prefer_chat=True,  # 使用 /api/chat 端点
            )
            if strict_system_prompt is not None:
                response = _trim_to_strict_report(template_id, (response or "").strip())
            await persist_chat(chat_request, user_message, response, user_id)
            return ChatResponse(
                response=response,
                model=chat_request.model,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            )

        user_message = ""
        for msg in chat_request.messages:
            if msg.role == "user":
                user_message = msg.content
                break

        if not validate_patent_relevance(user_message):
            error_response = {
                "choices": [{
                    "delta": {
                        "content": "抱歉，我是专门的专利 AI 助手，只能回答与专利相关的问题。请您询问专利申请、审查、检索、维权等相关内容，我将很乐意为您提供专业帮助。"
                    }
                }]
            }

            async def error_stream():
                yield f"{json.dumps(error_response)}\n\n"
                yield "[DONE]\n\n"

            return EventSourceResponse(error_stream(), headers=sse_headers)

        system_contents = [m.content for m in chat_request.messages if m.role == "system"]
        system_joined = "\n\n".join(system_contents) if system_contents else ""
        system_joined_lower = system_joined.lower()
        user_message_lower = (user_message or "").lower()
        is_ipc_mode = (
            ("专利分类专家" in system_joined)
            or ("国际专利分类" in system_joined)
            or ("ipc分类" in system_joined_lower)
            or ("ipc 分类" in system_joined_lower)
            or ("只做 ipc 分类" in system_joined_lower)
            or ("ipc" in user_message_lower)
        )

        system_messages = []
        user_found = False

        for msg in chat_request.messages:
            if msg.role == "system":
                if is_ipc_mode:
                    system_messages.append(msg)
                else:
                    if "专利" not in msg.content:
                        system_messages.append(ChatMessage(
                            role="system",
                            content=PATENT_SYSTEM_PROMPTS["intermediate"]
                        ))
                    else:
                        system_messages.append(msg)
            elif msg.role == "user" and not user_found:
                user_found = True
                if is_ipc_mode:
                    system_messages.append(msg)
                else:
                    patent_context = f"用户问题：{msg.content}\n\n请专门从专利角度回答这个问题。"
                    system_messages.append(ChatMessage(role="user", content=patent_context))
            else:
                system_messages.append(msg)

        if not any(msg.role == "system" for msg in system_messages):
            system_messages.insert(0, ChatMessage(
                role="system",
                content=IPC_SYSTEM_PROMPT if is_ipc_mode else PATENT_SYSTEM_PROMPTS["intermediate"]
            ))

        user_id = get_user_id_from_request(request)

        if chat_request.stream:
            async def stream_generator():
                assistant_text = ""
                try:
                    async for chunk in get_ollama_response_stream(system_messages, chat_request.model):
                        try:
                            delta = chunk.get("choices", [])[0].get("delta", {}).get("content", "")
                        except Exception:
                            delta = ""
                        if delta:
                            assistant_text += delta
                        yield f"{json.dumps(chunk)}\n\n"
                    await persist_chat(chat_request, user_message, assistant_text, user_id)
                    yield "[DONE]\n\n"
                except Exception as e:
                    error_chunk = {
                        "choices": [{
                            "delta": {
                                "content": f"抱歉，AI 服务暂时不可用：{str(e)}"
                            }
                        }]
                    }
                    yield f"{json.dumps(error_chunk)}\n\n"
                    yield "[DONE]\n\n"

            return EventSourceResponse(stream_generator(), headers=sse_headers)

        else:
            response = await get_ollama_response(system_messages, chat_request.model)
            await persist_chat(chat_request, user_message, response, user_id)
            return ChatResponse(
                response=response,
                model=chat_request.model,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"对话处理失败: {str(e)}"
        )

@router.get("/sessions")
async def list_chat_sessions(request: Request):
    user_id = get_user_id_from_request(request)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录"
        )

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(
                ChatSessionModel,
                func.count(ChatMessageModel.id).label("message_count"),
            )
            .outerjoin(
                ChatMessageModel,
                ChatMessageModel.session_id == ChatSessionModel.id,
            )
            .where(ChatSessionModel.user_id == user_id)
            .group_by(ChatSessionModel.id)
            .order_by(
                ChatSessionModel.last_message_at.desc(),
                ChatSessionModel.created_at.desc(),
            )
        )
        rows = result.all()

        return [
            {
                "id": row.ChatSession.id,
                "title": row.ChatSession.title,
                "model": row.ChatSession.model,
                "document_id": row.ChatSession.document_id,
                "last_message_at": row.ChatSession.last_message_at.isoformat()
                if row.ChatSession.last_message_at
                else None,
                "created_at": row.ChatSession.created_at.isoformat()
                if row.ChatSession.created_at
                else None,
                "updated_at": row.ChatSession.updated_at.isoformat()
                if row.ChatSession.updated_at
                else None,
                "message_count": row.message_count,
            }
            for row in rows
        ]


@router.get("/sessions/{session_id}")
async def get_chat_session_messages(session_id: int, request: Request):
    user_id = get_user_id_from_request(request)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录"
        )

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ChatSessionModel).where(
                ChatSessionModel.id == session_id,
                ChatSessionModel.user_id == user_id,
            )
        )
        chat_session = result.scalar_one_or_none()
        if chat_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在",
            )

        msg_result = await session.execute(
            select(ChatMessageModel)
            .where(ChatMessageModel.session_id == chat_session.id)
            .order_by(ChatMessageModel.message_index.asc(), ChatMessageModel.id.asc())
        )
        messages = msg_result.scalars().all()

        return {
            "id": chat_session.id,
            "title": chat_session.title,
            "model": chat_session.model,
            "document_id": chat_session.document_id,
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "model": m.model,
                    "document_id": m.document_id,
                    "message_index": m.message_index,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in messages
            ],
        }


@router.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: int, request: Request):
    user_id = get_user_id_from_request(request)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录",
        )

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ChatSessionModel).where(
                ChatSessionModel.id == session_id,
                ChatSessionModel.user_id == user_id,
            )
        )
        chat_session = result.scalar_one_or_none()
        if chat_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在",
            )

        await session.delete(chat_session)
        await session.commit()

        return {"message": "会话已删除"}

@router.get("/models")
async def list_models():
    """获取可用的 AI 模型列表"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")

            if response.status_code != 200:
                raise Exception(f"获取模型列表失败: {response.status_code}")

            data = response.json()
            models = []

            for model in data.get("models", []):
                models.append({
                    "id": model["name"],
                    "name": model["name"],
                    "size": model.get("size", 0),
                    "modified_at": model.get("modified_at", "")
                })

            return {"models": models}

    except Exception as e:
        # 返回默认模型列表
        return {
            "models": [
                {"id": "qwen3:8b", "name": "Qwen3-8B", "size": 0, "modified_at": ""}
            ]
        }

@router.get("/status")
async def get_ai_status():
    """获取 AI 服务状态"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")

            if response.status_code == 200:
                data = response.json()
                available_models = [model["name"] for model in data.get("models", [])]

                return {
                    "status": "online",
                    "models": available_models,
                    "message": "AI 服务正常运行"
                }
            else:
                return {
                    "status": "error",
                    "models": [],
                    "message": "AI 服务响应异常"
                }

    except Exception as e:
        return {
            "status": "offline",
            "models": [],
            "message": f"AI 服务离线: {str(e)}"
        }

 
