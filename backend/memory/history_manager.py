import json
import os
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class History(BaseModel):
    """对话历史结构体"""
    thread_id: int = Field(description="用于 checkpointer 的 thread_id")
    title: str = ""
    created_at: str = ""
    updated_at: str = ""
    messages: list = Field(default_factory=list, description="对话消息列表")
    meta: dict = Field(default_factory=dict, description="对话元信息")


class HistoryManager:
    """管理对话历史持久化（JSON 文件存储）

    数据格式: [{"thread_id": 1, "title": "...", "created_at": "...",
                "updated_at": "...", "messages": [...]}, ...]
    """

    def __init__(self, file_path: str):
        self.path = file_path
        self.history_list = self.load()
        if not self.history_list:
            self.current_id = 1
        else:
            self.current_id = max(
                (e.get("thread_id", 0) for e in self.history_list if isinstance(e, dict)),
                default=0,
            ) + 1

    def _find_index(self, chat_id: int) -> int | None:
        for i, entry in enumerate(self.history_list):
            if isinstance(entry, dict) and entry.get("thread_id") == chat_id:
                return i
        return None

    def load(self) -> list:
        try:
            if not os.path.exists(self.path) or os.path.getsize(self.path) == 0:
                return []
            with open(self.path, mode="r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                data = json.loads(content)
                if not isinstance(data, list):
                    data = []
        except Exception as e:
            print(f"Error loading history: {e}")
            data = []
        return data

    def add(self, chat_id: int, msgs: list):
        """序列化消息并覆盖写入对应对话"""
        msg_list = []
        for msg in msgs:
            one = msg.model_dump()
            if one["type"] == "system":
                continue
            if one["type"] == "tool":
                msg_list.append(
                    {
                        "role": one["type"],
                        "tool_call_id": one.get("tool_call_id"),
                        "name": one.get("name"),
                        "content": one["content"],
                    }
                )
            elif one["type"] == "ai":
                entry = {"role": one["type"], "content": one["content"]}
                tool_calls = one.get("tool_calls")
                if tool_calls:
                    entry["tool_calls"] = tool_calls
                msg_list.append(entry)
            else:
                msg_list.append({"role": one["type"], "content": one["content"]})
        self.save_conversation(chat_id, messages=msg_list)

    def save_conversation(self, chat_id: int, messages: list[dict], meta: dict | None = None):
        """覆盖写入已序列化消息，并可附带对话元信息。"""
        now = datetime.now(timezone.utc).isoformat()

        # 自动生成标题：取第一条用户消息前 30 字
        first_user = next((m["content"] for m in messages if m.get("role") in ("human", "user")), None)
        title = (first_user[:30] + "...") if (first_user and len(first_user) > 30) else (first_user or "New Chat")

        idx = self._find_index(chat_id)
        if idx is not None:
            self.history_list[idx]["messages"] = messages
            self.history_list[idx]["updated_at"] = now
            if meta is not None:
                self.history_list[idx]["meta"] = meta
            # 标题保持不变（首次生成后不覆盖）
        else:
            entry = History(
                thread_id=chat_id,
                title=title,
                created_at=now,
                updated_at=now,
                messages=messages,
                meta=meta or {},
            ).model_dump()
            self.history_list.append(entry)
            if chat_id >= self.current_id:
                self.current_id = chat_id + 1
        self.update()

    def get(self, chat_id: int) -> list[dict]:
        idx = self._find_index(chat_id)
        if idx is None:
            return []
        return self.history_list[idx].get("messages", [])

    def get_conversation(self, chat_id: int) -> dict | None:
        idx = self._find_index(chat_id)
        if idx is None:
            return None
        return self.history_list[idx]

    def list_all(self) -> list[dict]:
        """返回所有对话的元信息（不含 messages）"""
        result = []
        for entry in self.history_list:
            if isinstance(entry, dict):
                msgs = entry.get("messages", [])
                result.append(
                    {
                        "thread_id": entry.get("thread_id"),
                        "title": entry.get("title", ""),
                        "created_at": entry.get("created_at", ""),
                        "updated_at": entry.get("updated_at", ""),
                        "message_count": len(msgs),
                    }
                )
        return sorted(result, key=lambda x: x.get("updated_at", ""), reverse=True)

    def remove(self, chat_id: int) -> bool:
        idx = self._find_index(chat_id)
        if idx is not None:
            self.history_list.pop(idx)
            return True
        return False

    def update(self) -> None:
        try:
            with open(self.path, mode="w", encoding="utf-8") as f:
                json.dump(self.history_list, f, ensure_ascii=False, indent=2)
        except (OSError, json.JSONDecodeError) as e:
            print(f"Error saving history: {e}")
