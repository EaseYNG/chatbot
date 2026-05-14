from __future__ import annotations

import asyncio

from backend.tools import get_all_tools
from backend.memory import HistoryManager, CheckpointerProvider
from backend.agent import ChatBot
from backend.multi_agent import MultiAgentService

_history_manager = None
_checkpointer_provider = None
_chatbot = None
_multi_agent_service = None

_history_manager_lock = asyncio.Lock()
_chatbot_lock = asyncio.Lock()
_multi_agent_lock = asyncio.Lock()


async def get_history_manager() -> HistoryManager:
    global _history_manager
    if _history_manager is None:
        async with _history_manager_lock:
            if _history_manager is None:
                _history_manager = HistoryManager()
                await _history_manager._ensure_max_id()
    return _history_manager


def get_checkpointer_provider() -> CheckpointerProvider:
    global _checkpointer_provider
    if _checkpointer_provider is None:
        _checkpointer_provider = CheckpointerProvider()
    return _checkpointer_provider


async def get_chatbot() -> ChatBot:
    global _chatbot
    if _chatbot is None:
        async with _chatbot_lock:
            if _chatbot is None:
                checkpointer = await get_checkpointer_provider().get_async()
                _chatbot = ChatBot(
                    tools=get_all_tools(),
                    history_manager=await get_history_manager(),
                    checkpointer=checkpointer,
                )
    return _chatbot


async def get_multi_agent_service() -> MultiAgentService:
    global _multi_agent_service
    if _multi_agent_service is None:
        async with _multi_agent_lock:
            if _multi_agent_service is None:
                checkpointer = await get_checkpointer_provider().get_async()
                _multi_agent_service = MultiAgentService(
                    history_manager=await get_history_manager(),
                    checkpointer=checkpointer,
                )
    return _multi_agent_service
