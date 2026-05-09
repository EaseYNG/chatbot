from backend.config import HISTORY_FILE
from backend.tools import get_all_tools
from backend.memory import HistoryManager, CheckpointerProvider
from backend.agent import ChatBot
from backend.multi_agent import MultiAgentService


_history_manager = None
_checkpointer_provider = None
_chatbot = None
_multi_agent_service = None


def get_history_manager() -> HistoryManager:
    global _history_manager
    if _history_manager is None:
        _history_manager = HistoryManager(file_path=HISTORY_FILE)
    return _history_manager


def get_checkpointer_provider() -> CheckpointerProvider:
    global _checkpointer_provider
    if _checkpointer_provider is None:
        _checkpointer_provider = CheckpointerProvider()
    return _checkpointer_provider


async def get_chatbot() -> ChatBot:
    global _chatbot
    if _chatbot is None:
        checkpointer = await get_checkpointer_provider().get_async()
        _chatbot = ChatBot(
            tools=get_all_tools(),
            history_manager=get_history_manager(),
            checkpointer=checkpointer,
        )
    return _chatbot


async def get_multi_agent_service() -> MultiAgentService:
    global _multi_agent_service
    if _multi_agent_service is None:
        checkpointer = await get_checkpointer_provider().get_async()
        _multi_agent_service = MultiAgentService(
            history_manager=get_history_manager(),
            checkpointer=checkpointer,
        )
    return _multi_agent_service
