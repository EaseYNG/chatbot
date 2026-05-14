from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any

import aiosqlite

from backend.config import DATABASE_PATH

logger = logging.getLogger(__name__)

_connection: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    global _connection
    if _connection is None:
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        _connection = await aiosqlite.connect(DATABASE_PATH)
        _connection.row_factory = sqlite3.Row
        await _connection.execute("PRAGMA journal_mode=WAL")
        await _connection.execute("PRAGMA foreign_keys=ON")
    return _connection


async def init_db():
    db = await get_db()
    await db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id   INTEGER NOT NULL,
            user_id     INTEGER,
            title       TEXT NOT NULL DEFAULT '',
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL,
            messages    TEXT NOT NULL DEFAULT '[]',
            meta        TEXT NOT NULL DEFAULT '{}',
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_conversations_thread_id
            ON conversations(thread_id);

        CREATE INDEX IF NOT EXISTS idx_conversations_user_id
            ON conversations(user_id);

        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            token_hash  TEXT NOT NULL,
            expires_at  TEXT NOT NULL,
            revoked     INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash
            ON refresh_tokens(token_hash);
        """
    )
    await db.commit()


async def close_db():
    global _connection
    if _connection is not None:
        await _connection.close()
        _connection = None


class ConversationRow:
    """Minimal row wrapper for conversation data."""

    def __init__(self, row: sqlite3.Row | dict[str, Any]):
        if isinstance(row, sqlite3.Row):
            self._data = dict(row)
        else:
            self._data = row

    @property
    def thread_id(self) -> int:
        return self._data["thread_id"]

    @property
    def title(self) -> str:
        return self._data.get("title", "")

    @property
    def created_at(self) -> str:
        return self._data.get("created_at", "")

    @property
    def updated_at(self) -> str:
        return self._data.get("updated_at", "")

    @property
    def messages(self) -> list[dict]:
        raw = self._data.get("messages", "[]")
        if isinstance(raw, str):
            return json.loads(raw) if raw else []
        return raw if isinstance(raw, list) else []

    @property
    def meta(self) -> dict:
        raw = self._data.get("meta", "{}")
        if isinstance(raw, str):
            return json.loads(raw) if raw else {}
        return raw if isinstance(raw, dict) else {}

    def to_dict(self) -> dict:
        return {
            "thread_id": self.thread_id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": self.messages,
            "meta": self.meta,
        }
