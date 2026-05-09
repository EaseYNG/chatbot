import os
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from backend.config import CHECKPOINT_DB


class CheckpointerProvider:
    """SqliteSaver / AsyncSqliteSaver 封装，确保 Agent 状态持久化"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CheckpointerProvider, cls).__new__(cls)
            cls._instance._async_cm = None
            cls._instance._async_memory = None
            cls._instance._sync_cm = None
            cls._instance._sync_memory = None
        return cls._instance

    async def get_async(self) -> AsyncSqliteSaver:
        if self._async_memory is None:
            # 确保目录存在
            os.makedirs(os.path.dirname(CHECKPOINT_DB), exist_ok=True)
            self._async_cm = AsyncSqliteSaver.from_conn_string(CHECKPOINT_DB)
            self._async_memory = await self._async_cm.__aenter__()
        return self._async_memory

    def get_sync(self) -> SqliteSaver:
        if self._sync_memory is None:
            # 确保目录存在
            os.makedirs(os.path.dirname(CHECKPOINT_DB), exist_ok=True)
            self._sync_cm = SqliteSaver.from_conn_string(CHECKPOINT_DB)
            self._sync_memory = self._sync_cm.__enter__()
        return self._sync_memory

    async def close(self):
        if self._async_memory is not None:
            await self._async_cm.__aexit__(None, None, None)
            self._async_memory = None
        if self._sync_memory is not None:
            self._sync_cm.__exit__(None, None, None)
            self._sync_memory = None
