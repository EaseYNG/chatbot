from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from backend.agent import ChatBot
from backend.api.dependencies import get_chatbot, get_history_manager, get_multi_agent_service
from backend.auth import get_current_user
from backend.memory.history_manager import HistoryManager
from backend.middleware.rate_limit import rate_limit
from backend.models.schemas import ChatRequest, ConversationDetail, ConversationMeta
from backend.multi_agent import MultiAgentService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat")
async def stream_chat(
    req: ChatRequest,
    user: dict = Depends(get_current_user),
    _rl: None = Depends(rate_limit),
    service: MultiAgentService = Depends(get_multi_agent_service),
    history: HistoryManager = Depends(get_history_manager),
):
    thread_id = req.thread_id if req.thread_id else history.current_id

    return StreamingResponse(
        service.stream_chat(
            chat_id=thread_id,
            user_msg=req.message,
            sys_msg=req.system_message,
            mode_hint=req.mode_hint,
            agent_hint=req.agent_hint,
            return_trace=req.return_trace,
            user_id=user["id"],
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversations", response_model=list[ConversationMeta])
async def list_conversations(
    user: dict = Depends(get_current_user),
    history: HistoryManager = Depends(get_history_manager),
):
    return await history.list_all(user_id=user["id"])


async def _get_user_conversation(
    chat_id: int,
    user_id: int,
    history: HistoryManager,
) -> dict:
    conv = await history.get_conversation(chat_id, user_id=user_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.get("/conversations/{chat_id}", response_model=ConversationDetail)
async def get_conversation(
    chat_id: int,
    user: dict = Depends(get_current_user),
    history: HistoryManager = Depends(get_history_manager),
    chatbot: ChatBot = Depends(get_chatbot),
):
    conv = await _get_user_conversation(chat_id, user["id"], history)

    messages = conv.get("messages", [])
    if messages:
        try:
            await chatbot.restore_state(chat_id, messages)
        except Exception:
            logger.warning("Failed to restore state for chat_id=%d", chat_id, exc_info=True)

    return ConversationDetail(
        thread_id=conv["thread_id"],
        title=conv.get("title", ""),
        messages=messages,
        meta=conv.get("meta", {}),
    )


@router.delete("/conversations/{chat_id}")
async def delete_conversation(
    chat_id: int,
    user: dict = Depends(get_current_user),
    history: HistoryManager = Depends(get_history_manager),
):
    conv = await history.get_conversation(chat_id, user_id=user["id"])
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await history.remove(chat_id)
    return {"detail": "deleted"}
