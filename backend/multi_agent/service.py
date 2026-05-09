from __future__ import annotations

import json
import logging
from typing import AsyncIterator

from backend.config import DEFAULT_SYSTEM_PROMPT
from backend.memory.history_manager import HistoryManager
from backend.multi_agent.enums import ExecutionMode
from backend.multi_agent.graph import MultiAgentGraph

logger = logging.getLogger(__name__)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


class MultiAgentService:
    def __init__(self, history_manager: HistoryManager, checkpointer=None):
        self.history_manager = history_manager
        self.graph = MultiAgentGraph(
            history_manager=history_manager, checkpointer=checkpointer
        )

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
        try:
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
                
                config = {"configurable": {"thread_id": chat_id}}
                final_state = state
                yielded_traces = set()

                # 使用 astream_events 来捕获流式输出和状态更新
                async for event in self.graph.graph.astream_events(
                    state, config, version="v2"
                ):
                    kind = event.get("event")
                    
                    # 1. 捕获最终答案的 token (来自 output 节点，带有 output_synthesis 标签)
                    if kind == "on_chat_model_stream":
                        tags = event.get("tags", [])
                        if "output_synthesis" in tags:
                            content = event["data"]["chunk"].content
                            if content:
                                yield _sse("token", {"content": content})

                    # 2. 捕获状态更新中的 trace
                    elif kind == "on_chain_update":
                        # 状态更新时，提取新增的 trace
                        # astream_events 的 on_chain_update output 包含该步骤产生的 delta
                        new_trace = event["data"].get("output", {}).get("trace", [])
                        if return_trace and new_trace:
                            for item in new_trace:
                                # 使用 id 或内容摘要来避免重复 yield (因为 trace 是 Annotated add)
                                # 在 astream_events 中通常只给 delta，但以防万一
                                trace_key = json.dumps(item, sort_keys=True)
                                if trace_key not in yielded_traces:
                                    yielded_traces.add(trace_key)
                                    payload = dict(item)
                                    event_type = payload.pop("type", "trace")
                                    yield _sse(event_type, payload)

                    # 3. 捕获整个 Graph 结束时的状态
                    elif kind == "on_chain_end" and event.get("name") == "LangGraph":
                        final_state = event["data"]["output"]

                # 检查质量
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

            # 保存历史
            final_answer = final_state.get("final_answer", "")
            meta = {
                "run_id": final_state.get("run_id"),
                "execution_mode": final_state.get("execution_mode"),
                "selected_agent": final_state.get("selected_agent"),
                "quality_score": final_state.get("quality_score"),
                "intent": final_state.get("intent"),
                "plan_steps": final_state.get("plan_steps", []),
                "trace": final_state.get("trace", []) if return_trace else [],
            }
            messages = self._build_serialized_messages(
                chat_id=chat_id, user_msg=user_msg, answer=final_answer
            )
            self.history_manager.save_conversation(chat_id, messages=messages, meta=meta)

            yield _sse("done", {"thread_id": chat_id, "mode": final_state.get("execution_mode")})
        except Exception as e:
            logger.error("Error in stream_chat: %s", str(e), exc_info=True)
            yield _sse("error", {"message": str(e)})

    def _build_serialized_messages(
        self, *, chat_id: int, user_msg: str, answer: str
    ) -> list[dict]:
        history = self.history_manager.get(chat_id)
        messages = list(history)  # Clone existing history
        messages.append({"role": "human", "content": user_msg})
        if answer:
            messages.append({"role": "ai", "content": answer})
        return messages

    def _downgrade_mode(self, current_mode: str | None) -> str | None:
        if current_mode == ExecutionMode.WORKFLOW.value:
            return ExecutionMode.PLAN_EXECUTE.value
        if current_mode == ExecutionMode.PLAN_EXECUTE.value:
            return ExecutionMode.REACT.value
        return None
