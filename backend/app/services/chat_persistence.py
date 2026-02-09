"""聊天持久化服务模块"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatSession as ChatSessionModel, ChatMessage as ChatMessageModel
from app.utils.database import AsyncSessionLocal
from app.services.ollama import ChatRequest

logger = logging.getLogger(__name__)

DEFAULT_CHAT_USER_ID = 1


class ChatPersistenceService:
    """聊天持久化服务"""

    def __init__(self, user_id: Optional[int] = None):
        self.user_id = user_id or DEFAULT_CHAT_USER_ID

    async def create_session(
        self,
        session: AsyncSession,
        title: str,
        model: str,
        document_id: Optional[int] = None,
        session_id: Optional[int] = None
    ) -> ChatSessionModel:
        """创建或获取会话"""
        if session_id:
            existing = await session.get(ChatSessionModel, session_id)
            if existing and existing.user_id == self.user_id:
                return existing
            if existing:
                logger.warning(
                    "会话归属不匹配，已忽略: session_id=%s, request_user_id=%s, owner_user_id=%s",
                    session_id,
                    self.user_id,
                    existing.user_id,
                )

        chat_session = ChatSessionModel(
            user_id=self.user_id,
            title=title[:50] if title else "对话会话",
            model=model,
            document_id=document_id,
        )
        session.add(chat_session)
        await session.flush()
        return chat_session

    async def get_next_message_index(self, session: AsyncSession, session_id: int) -> int:
        """获取下一条消息的索引"""
        result = await session.execute(
            select(func.count(ChatMessageModel.id)).where(ChatMessageModel.session_id == session_id)
        )
        return (result.scalar() or 0) + 1

    async def save_messages(
        self,
        session: AsyncSession,
        session_id: int,
        user_message: str,
        assistant_message: str,
        model: str,
        document_id: Optional[int] = None
    ) -> None:
        """保存用户和助手消息"""
        base_index = await self.get_next_message_index(session, session_id)

        user_msg = ChatMessageModel(
            session_id=session_id,
            user_id=self.user_id,
            role="user",
            content=user_message,
            model=model,
            document_id=document_id,
            message_index=base_index,
        )
        assistant_msg = ChatMessageModel(
            session_id=session_id,
            user_id=self.user_id,
            role="assistant",
            content=assistant_message,
            model=model,
            document_id=document_id,
            message_index=base_index + 1,
        )
        session.add_all([user_msg, assistant_msg])

        # 更新会话最后消息时间
        await session.execute(
            select(ChatSessionModel).where(ChatSessionModel.id == session_id)
        )

    async def persist(
        self,
        chat_request: ChatRequest,
        user_message: str,
        assistant_message: str,
        user_id: Optional[int] = None
    ) -> None:
        """持久化聊天记录"""
        effective_user_id = user_id or self.user_id
        try:
            async with AsyncSessionLocal() as session:
                chat_session = await self.create_session(
                    session,
                    user_message,
                    chat_request.model,
                    chat_request.document_id,
                    chat_request.session_id
                )

                await self.save_messages(
                    session,
                    chat_session.id,
                    user_message,
                    assistant_message,
                    chat_request.model,
                    chat_request.document_id
                )

                chat_session.last_message_at = func.now()
                await session.commit()
        except Exception as e:
            logger.error(f"保存聊天记录失败: {e}")
            # 静默忽略保存失败，不影响用户响应


# ===================== 便捷函数 =====================

async def persist_chat(
    chat_request: ChatRequest,
    user_message: str,
    assistant_message: str,
    user_id: Optional[int] = None
) -> None:
    """便捷函数：持久化聊天记录"""
    service = ChatPersistenceService(user_id)
    await service.persist(chat_request, user_message, assistant_message, user_id)


async def get_user_sessions(user_id: int) -> List[Dict[str, Any]]:
    """获取用户会话列表"""
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
                if row.ChatSession.last_message_at else None,
                "created_at": row.ChatSession.created_at.isoformat()
                if row.ChatSession.created_at else None,
                "updated_at": row.ChatSession.updated_at.isoformat()
                if row.ChatSession.updated_at else None,
                "message_count": row.message_count,
            }
            for row in rows
        ]


async def get_session_messages(session_id: int, user_id: int) -> Dict[str, Any]:
    """获取会话消息"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ChatSessionModel).where(
                ChatSessionModel.id == session_id,
                ChatSessionModel.user_id == user_id,
            )
        )
        chat_session = result.scalar_one_or_none()
        if chat_session is None:
            return {}

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


async def delete_session(session_id: int, user_id: int) -> bool:
    """删除会话"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ChatSessionModel).where(
                ChatSessionModel.id == session_id,
                ChatSessionModel.user_id == user_id,
            )
        )
        chat_session = result.scalar_one_or_none()
        if chat_session is None:
            return False

        await session.delete(chat_session)
        await session.commit()
        return True
