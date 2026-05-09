import json
from typing import AsyncIterator
from backend.agent.chatbot import ChatBot
from backend.memory.history_manager import HistoryManager


async def chat_stream_generator(
    chatbot: ChatBot,
    chat_id: int,
    user_msg: str,
    sys_msg: str,
    history_manager: HistoryManager,
) -> AsyncIterator[str]:
    """SSE 流式生成器

    从 agent.astream_events(v2) 读取事件，转换为 SSE 文本行；
    流结束后自动将完整消息列表持久化。
    """
    try:
        async for event in chatbot.stream_events(chat_id, user_msg, sys_msg):
            kind = event.get("event")

            if kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    payload = {"content": chunk.content}
                    yield _sse("token", payload)

            elif kind == "on_tool_start":
                name = event.get("name", "unknown")
                tool_input = event.get("data", {}).get("input", {})
                # 序列化 tool_input 中的复杂对象
                if hasattr(tool_input, "model_dump"):
                    tool_input = tool_input.model_dump()
                elif not isinstance(tool_input, dict):
                    tool_input = str(tool_input)
                yield _sse("tool_start", {"tool_name": name, "tool_input": tool_input})

            elif kind == "on_tool_end":
                name = event.get("name", "unknown")
                output = event.get("data", {}).get("output", "")
                # ToolMessage 的 content
                if hasattr(output, "content"):
                    output = output.content
                elif not isinstance(output, str):
                    output = str(output)
                yield _sse("tool_end", {"tool_name": name, "tool_output": output})

        # 流结束：从 Agent 获取完整状态并持久化
        state = await chatbot.get_agent_state(chat_id)
        if state and "messages" in state:
            history_manager.add(chat_id, state["messages"])
            history_manager.update()

        yield _sse("done", {"thread_id": chat_id})

    except Exception as e:
        yield _sse("error", {"message": str(e)})


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
