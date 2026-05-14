from __future__ import annotations

from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver

from backend.config import DEFAULT_SYSTEM_PROMPT
from backend.agent.llm_factory import build_chat_llm
from backend.memory.history_manager import HistoryManager


class ChatBot:
    """LangChain Agent 封装，支持异步/同步双模式"""

    def __init__(
        self,
        tools: list,
        history_manager: HistoryManager,
        checkpointer: MemorySaver,
    ):
        self.history_manager = history_manager
        llm = build_chat_llm(streaming=True)
        self._agent = create_agent(model=llm, tools=tools, checkpointer=checkpointer)

    async def _build_messages(self, chat_id: int, sys_msg: str, user_msg: str) -> list:
        history = await self.history_manager.get(chat_id)
        return (
            [{"role": "system", "content": sys_msg}]
            + history
            + [{"role": "user", "content": user_msg}]
        )

    def chat_sync(self, chat_id: int, user_msg: str, sys_msg: str = DEFAULT_SYSTEM_PROMPT) -> dict:
        raise RuntimeError(
            "chat_sync is no longer supported because HistoryManager requires async. "
            "Use chat() instead."
        )

    async def chat(self, chat_id: int, user_msg: str, sys_msg: str = DEFAULT_SYSTEM_PROMPT) -> dict:
        input_list = await self._build_messages(chat_id, sys_msg, user_msg)
        return await self._agent.ainvoke(
            {"messages": input_list},
            {"configurable": {"thread_id": chat_id}},
        )

    async def stream_events(self, chat_id: int, user_msg: str, sys_msg: str = DEFAULT_SYSTEM_PROMPT):
        input_list = await self._build_messages(chat_id, sys_msg, user_msg)
        async for event in self._agent.astream_events(
            {"messages": input_list},
            {"configurable": {"thread_id": chat_id}},
            version="v2",
        ):
            yield event

    async def get_agent_state(self, chat_id: int) -> dict | None:
        state = await self._agent.aget_state({"configurable": {"thread_id": chat_id}})
        return state.values if state else None

    async def restore_state(self, chat_id: int, messages: list[dict]):
        state = await self._agent.aget_state({"configurable": {"thread_id": chat_id}})
        if state and state.values.get("messages"):
            return
        if messages:
            await self._agent.aupdate_state(
                {"configurable": {"thread_id": chat_id}},
                {"messages": messages},
            )
