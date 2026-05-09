from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any

from langchain.agents import create_agent
from langgraph.graph import END, START, StateGraph

from backend.agent.llm_factory import build_chat_llm
from backend.multi_agent.enums import ExecutionMode, IntentType, Stage
from backend.multi_agent.registry import AGENT_REGISTRY, get_agent_profile
from backend.multi_agent.state import OrchestratorState, validate_plan_steps
from backend.tools import get_tools_by_names

logger = logging.getLogger(__name__)


def _trace(event_type: str, **payload: Any) -> dict:
    return {"type": event_type, **payload}


def _extract_json_block(text: str) -> Any:
    text = text.strip()
    if not text:
        raise ValueError("empty response")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fence_match = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    if fence_match:
        return json.loads(fence_match.group(1).strip())

    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])

    raise ValueError("no json found")


def _extract_ai_content(result: dict) -> str:
    messages = result.get("messages", [])
    for msg in reversed(messages):
        if getattr(msg, "type", "") == "ai":
            content = getattr(msg, "content", "")
            if isinstance(content, list):
                return "\n".join(str(item) for item in content)
            return str(content)
    return ""


def _build_history_prompt(history: list[dict]) -> str:
    if not history:
        return "No previous conversation history."

    parts = []
    for item in history[-10:]:
        role = item.get("role", "unknown")
        content = item.get("content", "")
        if content:
            parts.append(f"{role}: {content}")
    return "\n".join(parts) if parts else "No previous conversation history."


class MultiAgentGraph:
    def __init__(self, *, history_manager, checkpointer=None, max_retries: int = 2):
        self.history_manager = history_manager
        self.checkpointer = checkpointer
        self.max_retries = max_retries
        self.graph = self._build_graph()

    def initial_state(
        self,
        *,
        thread_id: int,
        user_input: str,
        system_message: str,
        mode_hint: str | None = None,
        agent_hint: str | None = None,
        retry_count: int = 0,
    ) -> OrchestratorState:
        execution_mode = ExecutionMode.REACT.value
        if mode_hint:
            normalized = mode_hint.strip().upper()
            if normalized in {mode.value for mode in ExecutionMode}:
                execution_mode = normalized

        selected_agent = "general"
        if agent_hint and agent_hint in AGENT_REGISTRY:
            selected_agent = agent_hint

        return {
            "thread_id": thread_id,
            "run_id": uuid.uuid4().hex,
            "user_input": user_input,
            "system_message": system_message,
            "current_stage": Stage.INIT.value,
            "intent": IntentType.GENERAL.value,
            "complexity_score": 0,
            "execution_mode": execution_mode,
            "selected_agent": selected_agent,
            "required_tools": [],
            "plan_steps": [],
            "step_results": [],
            "warnings": [],
            "errors": [],
            "trace": [],
            "retry_count": retry_count,
            "max_retries": self.max_retries,
            "final_answer": "",
            "quality_score": 0,
            "quality_passed": False,
        }

    async def run(self, state: OrchestratorState) -> OrchestratorState:
        try:
            return await self.graph.ainvoke(
                state, {"configurable": {"thread_id": state["thread_id"]}}
            )
        except Exception as e:
            logger.error("Error running MultiAgentGraph: %s", str(e), exc_info=True)
            # 尝试返回一个包含错误信息的 state，而不是直接抛出异常
            state["errors"] = state.get("errors", []) + [{"message": str(e)}]
            state["current_stage"] = Stage.DONE.value
            state["quality_passed"] = False
            state["trace"] = state.get("trace", []) + [
                _trace("error", message=str(e))
            ]
            return state

    def _build_graph(self):
        graph = StateGraph(OrchestratorState)
        graph.add_node("init", self.init_node)
        graph.add_node("input", self.input_node)
        graph.add_node("complexity", self.complexity_node)
        graph.add_node("route", self.route_node)
        graph.add_node("execute_react", self.execute_react_node)
        graph.add_node("execute_plan", self.execute_plan_node)
        graph.add_node("execute_workflow", self.execute_workflow_node)
        graph.add_node("output", self.output_node)
        graph.add_node("quality", self.quality_node)

        graph.add_edge(START, "init")
        graph.add_edge("init", "input")
        graph.add_edge("input", "complexity")
        graph.add_edge("complexity", "route")
        graph.add_conditional_edges(
            "route",
            self.execution_router,
            {
                "execute_react": "execute_react",
                "execute_plan": "execute_plan",
                "execute_workflow": "execute_workflow",
            },
        )
        graph.add_edge("execute_react", "output")
        graph.add_edge("execute_plan", "output")
        graph.add_edge("execute_workflow", "output")
        graph.add_edge("output", "quality")
        graph.add_edge("quality", END)
        return graph.compile(checkpointer=self.checkpointer)

    def execution_router(self, state: OrchestratorState) -> str:
        mode = state.get("execution_mode", ExecutionMode.REACT.value)
        if mode == ExecutionMode.PLAN_EXECUTE.value:
            return "execute_plan"
        if mode == ExecutionMode.WORKFLOW.value:
            return "execute_workflow"
        return "execute_react"

    def init_node(self, state: OrchestratorState) -> dict:
        return {
            "current_stage": Stage.INIT.value,
            "trace": [
                _trace("stage_start", stage=Stage.INIT.value, label="初始化"),
                _trace("stage_end", stage=Stage.INIT.value, label="初始化"),
            ],
        }

    async def input_node(self, state: OrchestratorState) -> dict:
        agent_list = "\n".join(
            f"- {name}: {profile['label']} — {profile['system_prompt']}"
            for name, profile in AGENT_REGISTRY.items()
        )
        tool_names = list(get_tools_by_names(None))
        tool_list = ", ".join(getattr(t, "name", "") or t.__class__.__name__ for t in tool_names)

        llm = build_chat_llm(streaming=False)
        response = await llm.ainvoke(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a lightweight intent classifier in a multi-agent system. "
                        "Analyze the user message and return JSON only with these fields:\n"
                        '- "intent": the best agent name from the list below\n'
                        '- "required_tools": array of tool names the agent might need (empty array if none)\n'
                        "Be conservative with tools — only include them when clearly needed."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Available agents:\n{agent_list}\n\n"
                        f"Available tools: {tool_list}\n\n"
                        f"User message: {state['user_input']}"
                    ),
                },
            ]
        )
        content = str(getattr(response, "content", "") or "")

        intent = IntentType.GENERAL.value
        required_tools: list[str] = []
        try:
            data = _extract_json_block(content)
            raw_intent = str(data.get("intent", "")).strip().lower()
            if raw_intent in AGENT_REGISTRY:
                intent = raw_intent
            raw_tools = data.get("required_tools", [])
            if isinstance(raw_tools, list):
                valid_tools = {getattr(t, "name", "") or t.__class__.__name__ for t in tool_names}
                required_tools = [t for t in raw_tools if isinstance(t, str) and t in valid_tools]
        except Exception:
            pass

        return {
            "current_stage": Stage.INPUT.value,
            "intent": intent,
            "required_tools": required_tools,
            "trace": [
                _trace("stage_start", stage=Stage.INPUT.value, label="输入分析"),
                _trace("stage_end", stage=Stage.INPUT.value, label="输入分析", intent=intent, required_tools=required_tools),
            ],
        }

    def complexity_node(self, state: OrchestratorState) -> dict:
        score = 10
        user_input = state["user_input"]
        required_tools = state.get("required_tools", [])

        score += min(len(required_tools) * 10, 20)
        if any(keyword in user_input for keyword in ("步骤", "计划", "方案", "分解")):
            score += 15
        if any(keyword in user_input for keyword in ("结合历史", "继续上次", "基于之前")):
            score += 10
        if any(keyword in user_input for keyword in ("对比", "评估", "权衡", "trade-off")):
            score += 15
        if any(keyword in user_input for keyword in ("多个", "协作", "workflow", "multi-agent")):
            score += 20

        mode = state.get("execution_mode", ExecutionMode.REACT.value)
        if state.get("retry_count", 0) == 0 and mode == ExecutionMode.REACT.value:
            if score >= 55:
                mode = ExecutionMode.WORKFLOW.value
            elif score >= 25:
                mode = ExecutionMode.PLAN_EXECUTE.value

        return {
            "current_stage": Stage.COMPLEXITY.value,
            "complexity_score": score,
            "execution_mode": mode,
            "trace": [
                _trace("stage_start", stage=Stage.COMPLEXITY.value, label="复杂度评估"),
                _trace("stage_end", stage=Stage.COMPLEXITY.value, label="复杂度评估", score=score, mode=mode),
            ],
        }

    def route_node(self, state: OrchestratorState) -> dict:
        selected_agent = state.get("selected_agent") or "general"
        if selected_agent == "general":
            selected_agent = state.get("intent", IntentType.GENERAL.value)
            if selected_agent not in AGENT_REGISTRY:
                selected_agent = "general"

        return {
            "current_stage": Stage.ROUTING.value,
            "selected_agent": selected_agent,
            "trace": [
                _trace("stage_start", stage=Stage.ROUTING.value, label="执行路由"),
                _trace(
                    "route",
                    stage=Stage.ROUTING.value,
                    mode=state.get("execution_mode", ExecutionMode.REACT.value),
                    agent=selected_agent,
                    score=state.get("complexity_score", 0),
                ),
                _trace("stage_end", stage=Stage.ROUTING.value, label="执行路由"),
            ],
        }

    async def _run_agent(
        self,
        *,
        agent_name: str,
        task_text: str,
        history: list[dict],
        extra_context: str = "",
        streaming: bool = False,
        tags: list[str] | None = None,
    ) -> str:
        profile = get_agent_profile(agent_name)
        agent = create_agent(
            model=build_chat_llm(streaming=streaming),
            tools=get_tools_by_names(profile.get("tools")),
        )
        prompt = profile["system_prompt"]
        if extra_context:
            prompt = f"{prompt}\n\nAdditional context:\n{extra_context}"

        result = await agent.ainvoke(
            {
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "system", "content": f"Conversation history:\n{_build_history_prompt(history)}"},
                    {"role": "user", "content": task_text},
                ]
            },
            config={"tags": tags} if tags else None,
        )
        return _extract_ai_content(result)

    async def execute_react_node(self, state: OrchestratorState) -> dict:
        history = self.history_manager.get(state["thread_id"])
        agent_name = state["selected_agent"]
        answer = await self._run_agent(
            agent_name=agent_name,
            task_text=state["user_input"],
            history=history,
            streaming=True,
            tags=["output_synthesis"],
        )
        return {
            "current_stage": Stage.EXECUTION.value,
            "step_results": [
                {
                    "step_id": "react-1",
                    "title": "Direct response",
                    "agent": agent_name,
                    "status": "DONE",
                    "output": answer,
                }
            ],
            "trace": [
                _trace("stage_start", stage=Stage.EXECUTION.value, label="执行"),
                _trace("agent_start", agent=agent_name, label=get_agent_profile(agent_name)["label"]),
                _trace("agent_end", agent=agent_name, label=get_agent_profile(agent_name)["label"]),
                _trace("stage_end", stage=Stage.EXECUTION.value, label="执行"),
            ],
        }

    async def execute_plan_node(self, state: OrchestratorState) -> dict:
        try:
            plan_steps = await self._plan_steps(state, workflow=False)
        except ValueError as e:
            return await self._fallback_react(state, str(e))

        history = self.history_manager.get(state["thread_id"])
        step_results = []
        trace = [
            _trace("stage_start", stage=Stage.EXECUTION.value, label="计划执行"),
            _trace("plan", steps=plan_steps),
        ]

        for step in plan_steps:
            trace.append(_trace("step_start", step_id=step["step_id"], title=step["title"], agent=step["agent"]))
            output = await self._run_agent(
                agent_name=step["agent"],
                task_text=f"{step['title']}\n\nTask:\n{step['description']}\n\nOriginal request:\n{state['user_input']}",
                history=history,
            )
            step_results.append(
                {
                    "step_id": step["step_id"],
                    "title": step["title"],
                    "agent": step["agent"],
                    "status": "DONE",
                    "output": output,
                }
            )
            trace.append(_trace("step_end", step_id=step["step_id"], title=step["title"], agent=step["agent"]))

        trace.append(_trace("stage_end", stage=Stage.EXECUTION.value, label="计划执行"))
        return {
            "current_stage": Stage.EXECUTION.value,
            "plan_steps": plan_steps,
            "step_results": step_results,
            "trace": trace,
        }

    async def execute_workflow_node(self, state: OrchestratorState) -> dict:
        try:
            plan_steps = await self._plan_steps(state, workflow=True)
        except ValueError as e:
            return await self._fallback_react(state, str(e))

        history = self.history_manager.get(state["thread_id"])
        step_results = []
        trace = [
            _trace("stage_start", stage=Stage.EXECUTION.value, label="多 Agent 工作流"),
            _trace("plan", steps=plan_steps),
        ]

        for step in plan_steps:
            trace.append(_trace("agent_start", agent=step["agent"], label=get_agent_profile(step["agent"])["label"]))
            trace.append(_trace("step_start", step_id=step["step_id"], title=step["title"], agent=step["agent"]))
            prior_outputs = "\n\n".join(
                f"{item['title']}: {item['output']}" for item in step_results if item.get("output")
            )
            output = await self._run_agent(
                agent_name=step["agent"],
                task_text=(
                    f"{step['title']}\n\nTask:\n{step['description']}\n\n"
                    f"Original request:\n{state['user_input']}\n\n"
                    f"Previous outputs:\n{prior_outputs or 'None'}"
                ),
                history=history,
            )
            step_results.append(
                {
                    "step_id": step["step_id"],
                    "title": step["title"],
                    "agent": step["agent"],
                    "status": "DONE",
                    "output": output,
                }
            )
            trace.append(_trace("step_end", step_id=step["step_id"], title=step["title"], agent=step["agent"]))
            trace.append(_trace("agent_end", agent=step["agent"], label=get_agent_profile(step["agent"])["label"]))

        trace.append(_trace("stage_end", stage=Stage.EXECUTION.value, label="多 Agent 工作流"))
        return {
            "current_stage": Stage.EXECUTION.value,
            "plan_steps": plan_steps,
            "step_results": step_results,
            "trace": trace,
        }

    async def _plan_steps(self, state: OrchestratorState, *, workflow: bool) -> list[dict]:
        llm = build_chat_llm(streaming=False, enable_thinking=True)
        selected_agent = state["selected_agent"]
        mode_label = "workflow" if workflow else "plan_execute"
        
        agents_desc = "\n".join([f"- {k}: {v['label']}" for k, v in AGENT_REGISTRY.items()])
        
        prompt = (
            "You are a planner in a multi-agent system. "
            "Decompose the user request into a logical sequence of 2-4 steps. "
            "Return ONLY a JSON array of objects, each with: "
            "\"step_id\" (string), \"title\" (short name), \"description\" (what to do), and \"agent\" (one of the allowed agents).\n\n"
            f"Available agents:\n{agents_desc}"
        )

        # Retry logic for robust JSON extraction
        last_error = None
        for attempt in range(2):
            response = await llm.ainvoke(
                [
                    {"role": "system", "content": prompt},
                    {
                        "role": "user",
                        "content": (
                            f"Mode: {mode_label}\n"
                            f"Context: This is a {mode_label} task. "
                            f"{'In workflow mode, use different agents if appropriate.' if workflow else 'In plan_execute mode, you usually stick to the primary agent but can use others.'}\n"
                            f"User request: {state['user_input']}\n"
                            "JSON array:"
                        ),
                    },
                ]
            )
            content = str(getattr(response, "content", "") or "").strip()
            
            try:
                data = _extract_json_block(content)
                if isinstance(data, list) and len(data) > 0:
                    raw_steps = []
                    for index, item in enumerate(data, start=1):
                        if not isinstance(item, dict):
                            continue
                        agent_name = str(item.get("agent", selected_agent)).strip()
                        if agent_name not in AGENT_REGISTRY:
                            agent_name = selected_agent
                        raw_steps.append(
                            {
                                "step_id": str(item.get("step_id", f"s{index}")),
                                "title": str(item.get("title", f"Step {index}")),
                                "description": str(item.get("description", item.get("title", ""))),
                                "agent": agent_name,
                            }
                        )
                    if raw_steps:
                        return validate_plan_steps(raw_steps)
            except Exception as e:
                last_error = e
                continue
                
        raise ValueError(f"Planner failed to produce valid steps for mode={mode_label}. Last error: {last_error}")

    async def _fallback_react(self, state: OrchestratorState, reason: str) -> dict:
        history = self.history_manager.get(state["thread_id"])
        agent_name = state["selected_agent"]
        answer = await self._run_agent(
            agent_name=agent_name,
            task_text=state["user_input"],
            history=history,
            streaming=True,
            tags=["output_synthesis"],
        )
        return {
            "current_stage": Stage.EXECUTION.value,
            "step_results": [
                {
                    "step_id": "fallback-1",
                    "title": "Direct response (fallback)",
                    "agent": agent_name,
                    "status": "DONE",
                    "output": answer,
                }
            ],
            "warnings": [reason],
            "trace": [
                _trace("stage_start", stage=Stage.EXECUTION.value, label="执行(降级)"),
                _trace("warning", message=reason),
                _trace("agent_start", agent=agent_name, label=get_agent_profile(agent_name)["label"]),
                _trace("agent_end", agent=agent_name, label=get_agent_profile(agent_name)["label"]),
                _trace("stage_end", stage=Stage.EXECUTION.value, label="执行(降级)"),
            ],
        }

    async def output_node(self, state: OrchestratorState) -> dict:
        if state.get("execution_mode") == ExecutionMode.REACT.value:
            final_answer = state.get("step_results", [{}])[-1].get("output", "")
        else:
            llm = build_chat_llm(streaming=True, enable_thinking=True)
            combined = "\n\n".join(
                f"{item.get('title', 'Step')}: {item.get('output', '')}" for item in state.get("step_results", [])
            )
            response = await llm.ainvoke(
                [
                    {
                        "role": "system",
                        "content": (
                            "You are the output assembler in a multi-agent system. "
                            "Synthesize the step results into a cohesive user-facing response."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Original request:\n{state['user_input']}\n\nStep results:\n{combined}",
                    },
                ],
                config={"tags": ["output_synthesis"]},
            )
            final_answer = str(getattr(response, "content", "") or "")

        return {
            "current_stage": Stage.OUTPUT.value,
            "final_answer": final_answer,
            "trace": [
                _trace("stage_start", stage=Stage.OUTPUT.value, label="输出整理"),
                _trace("stage_end", stage=Stage.OUTPUT.value, label="输出整理"),
            ],
        }

    def quality_node(self, state: OrchestratorState) -> dict:
        score = 85 if state.get("final_answer") else 20
        if state.get("errors"):
            score -= 20
        passed = score >= 60
        return {
            "current_stage": Stage.DONE.value,
            "quality_score": score,
            "quality_passed": passed,
            "trace": [
                _trace("stage_start", stage=Stage.QUALITY.value, label="质量检查"),
                _trace("quality", score=score, passed=passed),
                _trace("stage_end", stage=Stage.QUALITY.value, label="质量检查"),
            ],
        }
