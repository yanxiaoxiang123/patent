"""Ollama AI 服务模块"""
import asyncio
import json
from typing import List, Optional, AsyncGenerator, Dict, Any
import httpx
from pydantic import BaseModel

from app.core.config import OLLAMA_URL


# ===================== Pydantic Models =====================

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


# ===================== System Prompts =====================

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


# ===================== 工具函数 =====================

def build_ollama_prompt(messages: List[ChatMessage]) -> str:
    """构建 Ollama prompt"""
    parts = []
    for msg in messages:
        role = msg.role.upper()
        parts.append(f"{role}: {msg.content}\n")
    return "\n".join(parts)


def get_temperature(is_strict_template: bool) -> tuple:
    """获取温度参数"""
    return (0.3, 0.8) if is_strict_template else (0.7, 0.9)


def validate_patent_relevance(content: str) -> bool:
    """验证是否与专利相关"""
    patent_keywords = [
        "专利", "发明", "实用新型", "外观设计", "申请", "审查", "权利要求",
        "说明书", "附图", "摘要", "优先权", "新颖性", "创造性", "实用性",
        "侵权", "维权", "许可", "转让", "检索", "分析", "评估", "撰写",
        "专利局", "知识产权", "专有技术", "技术秘密", "ipc", "国际专利分类", "分类号"
    ]
    content_lower = content.lower()
    return any(keyword in content_lower for keyword in patent_keywords)


def is_ipc_mode(system_content: str, user_message: str) -> bool:
    """判断是否为 IPC 分类模式"""
    system_lower = system_content.lower()
    user_lower = user_message.lower()
    return (
        ("专利分类专家" in system_content)
        or ("国际专利分类" in system_content)
        or ("ipc分类" in system_lower)
        or ("ipc 分类" in system_lower)
        or ("只做 ipc 分类" in system_lower)
        or ("ipc" in user_lower)
    )


def trim_to_strict_report(template_id: Optional[int], text: str) -> str:
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


# ===================== 流式响应生成器 =====================

async def _stream_response(
    client: httpx.AsyncClient,
    base: str,
    api_path: str,
    payload: Dict[str, Any],
    prefer_chat: bool
) -> AsyncGenerator[Dict[str, Any], None]:
    """流式响应生成器"""
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
                    # /api/chat 格式: {"message": {"role": "...", "content": "...", "thinking": "..."}}
                    message = data.get("message", {})
                    thinking = message.get("thinking", "") or data.get("thinking", "")
                    content = message.get("content", "")
                    if thinking:
                        yield {"choices": [{"delta": {"thinking": thinking}}]}
                    if content:
                        yield {"choices": [{"delta": {"content": content}}]}
                else:
                    # /api/generate 格式: {"response": "...", "thinking": "..."}
                    thinking = data.get("thinking", "")
                    content = data.get("response", "")
                    if thinking:
                        yield {"choices": [{"delta": {"thinking": thinking}}]}
                    if content:
                        yield {"choices": [{"delta": {"content": content}}]}

                if data.get("done"):
                    break
        except asyncio.CancelledError:
            return


def _build_payload(
    messages: List[ChatMessage],
    model: str,
    system_prompt: str,
    prompt: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
    is_strict_template: bool,
    prefer_chat: bool,
    reduced_max_tokens: bool = False
) -> Dict[str, Any]:
    """构建请求负载"""
    final_max_tokens = min(max_tokens, 4000) if reduced_max_tokens else max_tokens
    repeat_penalty = 1.1 if is_strict_template else 1.0

    options = {
        "temperature": temperature,
        "top_p": top_p,
        "num_ctx": 32768,
        "max_tokens": final_max_tokens,
        "keep_alive": "24h",
        "repeat_penalty": repeat_penalty,
    }

    if prefer_chat:
        return {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "think": True,
            "stream": True,
            "options": options,
        }
    else:
        return {
            "model": model,
            "prompt": prompt,
            "system": system_prompt,
            "think": True,
            "stream": True,
            "options": options,
        }


# ===================== 主服务函数 =====================

async def get_ollama_response_stream(
    messages: List[ChatMessage],
    model: str = "qwen3:8b",
    is_strict_template: bool = False,
    max_tokens: int = 40960,
    prefer_chat: bool = False,
) -> AsyncGenerator[Dict[str, Any], None]:
    """获取 Ollama 流式响应"""
    system_parts = [msg.content for msg in messages if msg.role == "system"]
    system_prompt = "\n\n".join(system_parts) if system_parts else ""
    conversation_messages = [msg for msg in messages if msg.role != "system"]
    prompt = build_ollama_prompt(conversation_messages)

    temperature, top_p = get_temperature(is_strict_template)

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            payload = _build_payload(
                messages, model, system_prompt, prompt,
                temperature, top_p, max_tokens, is_strict_template, prefer_chat
            )
            api_path = "/api/chat" if prefer_chat else "/api/generate"

            try:
                async for chunk in _stream_response(client, OLLAMA_URL, api_path, payload, prefer_chat):
                    yield chunk
            except (httpx.ConnectError, httpx.ReadTimeout):
                # 失败回退（当前单实例不做处理）
                payload = _build_payload(
                    messages, model, system_prompt, prompt,
                    temperature, top_p, max_tokens, is_strict_template, prefer_chat, reduced_max_tokens=True
                )
                async for chunk in _stream_response(client, OLLAMA_URL, api_path, payload, prefer_chat):
                    yield chunk

    except httpx.ConnectError:
        raise Exception("无法连接到 Ollama 服务，请确保服务正在运行")
    except Exception as e:
        raise Exception(f"Ollama API 调用失败: {str(e)}")


async def get_ollama_response(
    messages: List[ChatMessage],
    model: str = "qwen3:8b",
    is_strict_template: bool = False,
    max_tokens: int = 40960,
    prefer_chat: bool = False,
) -> str:
    """获取 Ollama 非流式响应"""
    system_parts = [msg.content for msg in messages if msg.role == "system"]
    system_prompt = "\n\n".join(system_parts) if system_parts else ""
    conversation_messages = [msg for msg in messages if msg.role != "system"]
    prompt = build_ollama_prompt(conversation_messages)

    temperature, top_p = get_temperature(is_strict_template)
    repeat_penalty = 1.1 if is_strict_template else 1.0

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            api_path = "/api/chat" if prefer_chat else "/api/generate"

            if prefer_chat:
                payload = {
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
            else:
                payload = {
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

            try:
                response = await client.post(f"{OLLAMA_URL}{api_path}", json=payload)
            except (httpx.ConnectError, httpx.ReadTimeout):
                response = await client.post(f"{OLLAMA_URL}{api_path}", json=payload)

            if response.status_code != 200:
                raise Exception(f"Ollama API 错误: {response.status_code} - {response.text}")

            data = response.json()
            if prefer_chat:
                message = data.get("message", {})
                return message.get("content", "")
            return data.get("response", "")

    except Exception as e:
        raise Exception(f"Ollama API 调用失败: {str(e)}")
