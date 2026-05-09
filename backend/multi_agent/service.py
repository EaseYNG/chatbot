from __future__ import annotations

import json
from typing import AsyncIterator

from backend.config import DEFAULT_SYSTEM_PROMPT
from backend.memory.history_manager import HistoryManager
from backend.multi_agent.enums import ExecutionMode
from backend.multi_agent.graph import MultiAgentGraph


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _chunk_text(text: str, size: int = 24) -> list[str]:
    if not text:
        return []
    return [text[index : index + size] for index in range(0, len(text), size)]


class MultiAgentService:
    def __init__(self, history_manager: HistoryManager):
        self.history_manager = history_manager
        self.graph = MultiAgentGraph(history_manager=history_manager)

    async def stream_chat(
        self,
        *,
        chat_id: int,
        user_msg: str,
        sys_msg: str = DEFAULT_SYSTEM_PROMPT,
        mode_hint: str | None = None,
        agent_hint: str | None = None,
        return_trace: bool = True,
    ) -> AsyncIterator[str]:
        attempt = 0
        requested_mode = mode_hint

        while True:
            state = self.graph.initial_state(
                thread_id=chat_id,
                user_input=user_msg,
                system_message=sys_msg,
                mode_hint=requested_mode,
                agent_hint=agent_hint,
                retry_count=attempt,
            )
            final_state = await self.graph.run(state)

            if return_trace:
                for item in final_state.get("trace", []):
                    event_type = item.pop("type", "trace")
                    yield _sse(event_type, item)

            if final_state.get("quality_passed", False):
                break

            attempt += 1
            downgraded = self._downgrade_mode(final_state.get("execution_mode"))
            if attempt > final_state.get("max_retries", 0) or downgraded is None:
                break

            yield _sse(
                "warning",
                {
                    "message": "Quality check failed, retrying with a simpler execution mode.",
                    "retry_count": attempt,
                    "next_mode": downgraded,
                },
            )
            requested_mode = downgraded

        final_answer = final_state.get("final_answer", "")
        for chunk in _chunk_text(final_answer):
            yield _sse("token", {"content": chunk})

        meta = {
            "run_id": final_state.get("run_id"),
            "execution_mode": final_state.get("execution_mode"),
            "selected_agent": final_state.get("selected_agent"),
            "quality_score": final_state.get("quality_score"),
            "intent": final_state.get("intent"),
            "plan_steps": final_state.get("plan_steps", []),
            "trace": final_state.get("trace", []) if return_trace else [],
        }
        messages = self._build_serialized_messages(user_msg=user_msg, answer=final_answer)
        self.history_manager.save_conversation(chat_id, messages=messages, meta=meta)

        yield _sse("done", {"thread_id": chat_id, "mode": final_state.get("execution_mode")})

    def _build_serialized_messages(self, *, user_msg: str, answer: str) -> list[dict]:
        messages = [{"role": "human", "content": user_msg}]
        if answer:
            messages.append({"role": "ai", "content": answer})
        return messages

    def _downgrade_mode(self, current_mode: str | None) -> str | None:
        if current_mode == ExecutionMode.WORKFLOW.value:
            return ExecutionMode.PLAN_EXECUTE.value
        if current_mode == ExecutionMode.PLAN_EXECUTE.value:
            return ExecutionMode.REACT.value
        return None
