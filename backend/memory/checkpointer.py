from langgraph.checkpoint.memory import MemorySaver


class CheckpointerProvider:
    """MemorySaver 单例封装，确保 Agent 使用同一检查点实例"""

    def __init__(self):
        self._memory = MemorySaver()

    def get(self) -> MemorySaver:
        return self._memory
