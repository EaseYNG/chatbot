from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from backend.memory.database import ConversationRow, get_db

logger = logging.getLogger(__name__)


class HistoryManager:
    """Manages conversation history persistence via SQLite.

    Data model mirrors the original JSON schema but stored relationally.
    """

    def __init__(self):
        self.current_id = 1
        self._max_id_loaded = False

    async def _ensure_max_id(self):
        if self._max_id_loaded:
            return
        db = await get_db()
        row = await db.execute_fetchall("SELECT COALESCE(MAX(thread_id), 0) AS mid FROM conversations")
        if row:
            self.current_id = row[0]["mid"] + 1
        self._max_id_loaded = True

    async def load(self) -> list[dict]:
        db = await get_db()
        rows = await db.execute_fetchall(
            "SELECT thread_id, title, created_at, updated_at, messages, meta "
            "FROM conversations ORDER BY updated_at DESC"
        )
        return [ConversationRow(r).to_dict() for r in rows]

    async def add(self, chat_id: int, msgs: list, meta: dict | None = None):
        msg_list = []
        for msg in msgs:
            one = msg.model_dump() if hasattr(msg, "model_dump") else msg
            if one.get("type") == "system":
                continue
            if one.get("type") == "tool":
                msg_list.append({
                    "role": "tool",
                    "tool_call_id": one.get("tool_call_id"),
                    "name": one.get("name"),
                    "content": one["content"],
                })
            elif one.get("type") == "ai":
                entry = {"role": "ai", "content": one["content"]}
                if one.get("tool_calls"):
                    entry["tool_calls"] = one["tool_calls"]
                msg_list.append(entry)
            else:
                msg_list.append({"role": one["type"], "content": one["content"]})
        await self.save_conversation(chat_id, messages=msg_list, meta=meta)

    async def save_conversation(
        self,
        chat_id: int,
        messages: list[dict],
        meta: dict | None = None,
        user_id: int | None = None,
    ):
        await self._ensure_max_id()
        now = datetime.now(timezone.utc).isoformat()

        first_user = next(
            (m["content"] for m in messages if m.get("role") in ("human", "user")),
            None,
        )
        title = (
            (first_user[:30] + "...")
            if first_user and len(first_user) > 30
            else (first_user or "New Chat")
        )

        db = await get_db()
        existing = await db.execute_fetchall(
            "SELECT id FROM conversations WHERE thread_id = ? LIMIT 1",
            (chat_id,),
        )

        if existing:
            await db.execute(
                "UPDATE conversations SET messages = ?, meta = ?, updated_at = ? WHERE thread_id = ?",
                (
                    json.dumps(messages, ensure_ascii=False),
                    json.dumps(meta or {}, ensure_ascii=False) if meta is not None else None,
                    now,
                    chat_id,
                ),
            )
        else:
            await db.execute(
                "INSERT INTO conversations (thread_id, user_id, title, created_at, updated_at, messages, meta) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    chat_id,
                    user_id,
                    title,
                    now,
                    now,
                    json.dumps(messages, ensure_ascii=False),
                    json.dumps(meta or {}, ensure_ascii=False),
                ),
            )
            if chat_id >= self.current_id:
                self.current_id = chat_id + 1
        await db.commit()

    async def get(self, chat_id: int) -> list[dict]:
        db = await get_db()
        rows = await db.execute_fetchall(
            "SELECT messages FROM conversations WHERE thread_id = ? LIMIT 1",
            (chat_id,),
        )
        if not rows:
            return []
        return ConversationRow(rows[0]).messages

    async def get_conversation(self, chat_id: int, user_id: int | None = None) -> dict | None:
        db = await get_db()
        if user_id is not None:
            rows = await db.execute_fetchall(
                "SELECT thread_id, title, created_at, updated_at, messages, meta "
                "FROM conversations WHERE thread_id = ? AND (user_id = ? OR user_id IS NULL) LIMIT 1",
                (chat_id, user_id),
            )
        else:
            rows = await db.execute_fetchall(
                "SELECT thread_id, title, created_at, updated_at, messages, meta "
                "FROM conversations WHERE thread_id = ? LIMIT 1",
                (chat_id,),
            )
        if not rows:
            return None
        return ConversationRow(rows[0]).to_dict()

    async def list_all(self, user_id: int | None = None) -> list[dict]:
        db = await get_db()
        if user_id is not None:
            rows = await db.execute_fetchall(
                "SELECT thread_id, title, created_at, updated_at, messages "
                "FROM conversations WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,),
            )
        else:
            rows = await db.execute_fetchall(
                "SELECT thread_id, title, created_at, updated_at, messages "
                "FROM conversations ORDER BY updated_at DESC"
            )
        result = []
        for r in rows:
            cr = ConversationRow(r)
            result.append({
                "thread_id": cr.thread_id,
                "title": cr.title,
                "created_at": cr.created_at,
                "updated_at": cr.updated_at,
                "message_count": len(cr.messages),
            })
        return result

    async def remove(self, chat_id: int) -> bool:
        db = await get_db()
        cursor = await db.execute(
            "DELETE FROM conversations WHERE thread_id = ?",
            (chat_id,),
        )
        await db.commit()
        return cursor.rowcount > 0
