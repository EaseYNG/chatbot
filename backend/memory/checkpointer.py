from langgraph.checkpoint.sqlite import SqliteSaver
from backend.config import CHECKPOINT_DB


class CheckpointerProvider:
    """SqliteSaver 封装，确保 Agent 状态持久化"""

    def __init__(self):
        self._memory = SqliteSaver.from_conn_string(CHECKPOINT_DB)

    def get(self) -> SqliteSaver:
        return self._memory
