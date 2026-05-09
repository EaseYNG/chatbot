from functools import lru_cache
from backend.config import HISTORY_FILE
from backend.tools import get_all_tools
from backend.memory import HistoryManager, CheckpointerProvider
from backend.agent import ChatBot


@lru_cache()
def get_history_manager() -> HistoryManager:
    return HistoryManager(file_path=HISTORY_FILE)


@lru_cache()
def get_checkpointer_provider() -> CheckpointerProvider:
    return CheckpointerProvider()


@lru_cache()
def get_chatbot() -> ChatBot:
    return ChatBot(
        tools=get_all_tools(),
        history_manager=get_history_manager(),
        checkpointer=get_checkpointer_provider().get(),
    )
