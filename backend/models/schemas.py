from pydantic import BaseModel
from typing import Optional


class MessageDict(BaseModel):
    role: str
    content: Optional[str] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


class ChatRequest(BaseModel):
    thread_id: Optional[int] = None
    message: str
    system_message: str = "You are a helpful assistant."


class ConversationMeta(BaseModel):
    thread_id: int
    title: str
    created_at: str = ""
    updated_at: str = ""
    message_count: int = 0


class ConversationDetail(BaseModel):
    thread_id: int
    title: str
    messages: list[MessageDict]
