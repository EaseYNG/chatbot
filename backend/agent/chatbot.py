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

    def _build_messages(self, chat_id: int, sys_msg: str, user_msg: str) -> list:
        history = self.history_manager.get(chat_id)
        return (
            [{"role": "system", "content": sys_msg}]
            + history
            + [{"role": "user", "content": user_msg}]
        )

    def chat_sync(self, chat_id: int, user_msg: str, sys_msg: str = DEFAULT_SYSTEM_PROMPT) -> dict:
        input_list = self._build_messages(chat_id, sys_msg, user_msg)
        return self._agent.invoke(
            {"messages": input_list},
            {"configurable": {"thread_id": chat_id}},
        )

    async def chat(self, chat_id: int, user_msg: str, sys_msg: str = DEFAULT_SYSTEM_PROMPT) -> dict:
        input_list = self._build_messages(chat_id, sys_msg, user_msg)
        return await self._agent.ainvoke(
            {"messages": input_list},
            {"configurable": {"thread_id": chat_id}},
        )

    async def stream_events(self, chat_id: int, user_msg: str, sys_msg: str = DEFAULT_SYSTEM_PROMPT):
        input_list = self._build_messages(chat_id, sys_msg, user_msg)
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
        """恢复 MemorySaver 检查点状态（重放历史消息但不触发 LLM 调用）。
        当前 MemorySaver 模式下，状态会在下次 chat() 调用时自动重建。
        迁移到 SqliteSaver/PostgresSaver 后此方法将直接恢复持久化状态。"""
        pass
