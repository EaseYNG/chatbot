from typing import Optional

from pydantic import BaseModel, Field


class MessageDict(BaseModel):
    role: str
    content: Optional[str] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


class ChatRequest(BaseModel):
    thread_id: Optional[int] = None
    message: str = Field(min_length=1, max_length=16000)
    system_message: str = Field(default="You are a helpful assistant.", max_length=4000)
    mode_hint: Optional[str] = None
    agent_hint: Optional[str] = None
    return_trace: bool = True


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
    meta: dict = Field(default_factory=dict)
