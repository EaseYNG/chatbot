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

                # node name → stage key 映射，用于立即发送 stage_start
                NODE_STAGE_MAP = {
                    "init": "INIT",
                    "input": "INPUT",
                    "complexity": "COMPLEXITY",
                    "route": "ROUTING",
                    "execute_react": "EXECUTION",
                    "execute_plan": "EXECUTION",
                    "execute_workflow": "EXECUTION",
                    "output": "OUTPUT",
                    "quality": "QUALITY",
                }

                stage_labels = {
                    "INIT": "初始化",
                    "INPUT": "意图识别",
                    "COMPLEXITY": "复杂度评估",
                    "ROUTING": "执行路由",
                    "EXECUTION": "执行",
                    "OUTPUT": "输出整合",
                    "QUALITY": "质量检查",
                }

                # 使用 astream_events v2 捕获所有运行时事件
                # 事件类型参考: https://langchain-ai.github.io/langgraph/how-tos/streaming-events-from-within-tools/
                async for event in self.graph.graph.astream_events(
                    state, config, version="v2"
                ):
                    kind = event.get("event")
                    name = event.get("name", "")
                    data = event.get("data", {})

                    # ── Graph Node 启动 → stage_start ──
                    if kind == "on_chain_start":
                        stage_key = NODE_STAGE_MAP.get(name)
                        if stage_key:
                            dedup_key = f"stage_start:{stage_key}"
                            if dedup_key not in yielded_traces:
                                yielded_traces.add(dedup_key)
                                yield _sse("stage_start", {
                                    "stage": stage_key,
                                    "label": stage_labels.get(stage_key, stage_key),
                                })

                    # ── 工具调用开始 ──
                    elif kind == "on_tool_start":
                        tool_name = name
                        tool_input = data.get("input", {})
                        # 序列化 tool input 以便前端展示
                        try:
                            tool_input_str = json.dumps(tool_input, ensure_ascii=False, default=str)
                        except Exception:
                            tool_input_str = str(tool_input)
                        yield _sse("tool_start", {
                            "tool_name": tool_name,
                            "tool_input": tool_input_str,
                        })

                    # ── 工具调用结束 ──
                    elif kind == "on_tool_end":
                        tool_name = name
                        tool_output = data.get("output", "")
                        yield _sse("tool_end", {
                            "tool_name": tool_name,
                            "tool_output": str(tool_output),
                        })

                    # ── LLM token 流式输出（仅用户可见的输出内容） ──
                    elif kind == "on_chat_model_stream":
                        tags = event.get("tags", [])
                        if "output_synthesis" in tags:
                            content = data["chunk"].content
                            if content:
                                yield _sse("token", {"content": content})

                    # ── Graph Node 完成 → trace 事件 + stage_end ──
                    elif kind == "on_chain_end":
                        # 整个 Graph 结束 → 捕获最终状态
                        if name == "LangGraph":
                            final_state = data["output"]

                        # Graph Node 结束 → trace 事件 + stage_end
                        elif return_trace:
                            node_output = data.get("output", {})
                            if isinstance(node_output, dict):
                                new_trace = node_output.get("trace", [])
                                for item in new_trace:
                                    payload = dict(item)
                                    event_type = payload.pop("type", "trace")
                                    # stage_start/stage_end 已由 on_chain_start/end 实时发送
                                    if event_type in ("stage_start", "stage_end"):
                                        continue
                                    dedup_key = json.dumps(item, sort_keys=True)
                                    if dedup_key not in yielded_traces:
                                        yielded_traces.add(dedup_key)
                                        yield _sse(event_type, payload)

                            stage_key = NODE_STAGE_MAP.get(name)
                            if stage_key:
                                dedup_key = f"stage_end:{stage_key}"
                                if dedup_key not in yielded_traces:
                                    yielded_traces.add(dedup_key)
                                    yield _sse("stage_end", {
                                        "stage": stage_key,
                                        "label": stage_labels.get(stage_key, stage_key),
                                    })

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
