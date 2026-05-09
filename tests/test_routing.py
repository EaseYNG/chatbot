from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from backend.multi_agent.enums import ExecutionMode
from backend.multi_agent.graph import MultiAgentGraph


class FakeHistoryManager:
    def get(self, chat_id: int) -> list[dict]:  # noqa: ARG002
        return []


class FakeLLMResponse:
    def __init__(self, content: str):
        self.content = content


def make_state(**overrides):
    graph = MultiAgentGraph(history_manager=FakeHistoryManager())
    state = graph.initial_state(
        thread_id=1,
        user_input="hello",
        system_message="You are helpful.",
    )
    state.update(overrides)
    return state


class TestComplexityScoring:
    def test_simple_question_low_score(self):
        state = make_state(user_input="你好")
        result = MultiAgentGraph(history_manager=FakeHistoryManager()).complexity_node(state)
        assert result["complexity_score"] == 10
        assert result["execution_mode"] == ExecutionMode.REACT.value

    def test_tool_keywords_increase_score(self):
        state = make_state(
            user_input="readme.md 里写了什么？请读取后总结",
            required_tools=["read_md"],
        )
        result = MultiAgentGraph(history_manager=FakeHistoryManager()).complexity_node(state)
        assert result["complexity_score"] >= 20

    def test_step_keywords_add_15(self):
        state = make_state(user_input="请给我一个详细的步骤和方案")
        result = MultiAgentGraph(history_manager=FakeHistoryManager()).complexity_node(state)
        assert result["complexity_score"] >= 25

    def test_cross_domain_triggers_workflow(self):
        state = make_state(user_input="请多个角度协作对比评估这个多 Agent workflow 方案")
        result = MultiAgentGraph(history_manager=FakeHistoryManager()).complexity_node(state)
        assert result["complexity_score"] >= 55
        assert result["execution_mode"] == ExecutionMode.WORKFLOW.value

    def test_plan_threshold_triggers_plan_execute(self):
        state = make_state(user_input="请按步骤分析这段代码的问题")
        result = MultiAgentGraph(history_manager=FakeHistoryManager()).complexity_node(state)
        assert result["complexity_score"] >= 25
        assert result["execution_mode"] == ExecutionMode.PLAN_EXECUTE.value

    def test_mode_hint_respected_on_first_attempt(self):
        state = make_state(
            user_input="你好",
            execution_mode=ExecutionMode.PLAN_EXECUTE.value,
            retry_count=0,
        )
        result = MultiAgentGraph(history_manager=FakeHistoryManager()).complexity_node(state)
        assert result["execution_mode"] == ExecutionMode.PLAN_EXECUTE.value

    def test_mode_hint_not_overridden_on_retry(self):
        state = make_state(
            user_input="请多个角度协作对比评估这个多 Agent workflow 方案",
            execution_mode=ExecutionMode.PLAN_EXECUTE.value,
            retry_count=1,
        )
        result = MultiAgentGraph(history_manager=FakeHistoryManager()).complexity_node(state)
        assert result["execution_mode"] == ExecutionMode.PLAN_EXECUTE.value


class TestRouting:
    def test_react_mode_routes_to_execute_react(self):
        graph = MultiAgentGraph(history_manager=FakeHistoryManager())
        state = make_state(execution_mode=ExecutionMode.REACT.value)
        assert graph.execution_router(state) == "execute_react"

    def test_plan_execute_mode_routes_correctly(self):
        graph = MultiAgentGraph(history_manager=FakeHistoryManager())
        state = make_state(execution_mode=ExecutionMode.PLAN_EXECUTE.value)
        assert graph.execution_router(state) == "execute_plan"

    def test_workflow_mode_routes_correctly(self):
        graph = MultiAgentGraph(history_manager=FakeHistoryManager())
        state = make_state(execution_mode=ExecutionMode.WORKFLOW.value)
        assert graph.execution_router(state) == "execute_workflow"


class TestInputAnalysis:
    @pytest.mark.asyncio
    @patch("backend.multi_agent.graph.build_chat_llm")
    async def test_llm_classifies_coding_intent(self, mock_llm):
        mock_instance = AsyncMock()
        mock_instance.ainvoke.return_value = FakeLLMResponse(
            '{"intent": "coding", "required_tools": ["read_md"]}'
        )
        mock_llm.return_value = mock_instance

        state = make_state(user_input="这段 Python 代码有 bug 需要 debug")
        result = await MultiAgentGraph(history_manager=FakeHistoryManager()).input_node(state)
        assert result["intent"] == "coding"

    @pytest.mark.asyncio
    @patch("backend.multi_agent.graph.build_chat_llm")
    async def test_llm_classifies_writing_intent(self, mock_llm):
        mock_instance = AsyncMock()
        mock_instance.ainvoke.return_value = FakeLLMResponse(
            '{"intent": "writing", "required_tools": []}'
        )
        mock_llm.return_value = mock_instance

        state = make_state(user_input="帮我总结这篇文章并改写")
        result = await MultiAgentGraph(history_manager=FakeHistoryManager()).input_node(state)
        assert result["intent"] == "writing"

    @pytest.mark.asyncio
    @patch("backend.multi_agent.graph.build_chat_llm")
    async def test_llm_classifies_analysis_intent(self, mock_llm):
        mock_instance = AsyncMock()
        mock_instance.ainvoke.return_value = FakeLLMResponse(
            '{"intent": "analysis", "required_tools": []}'
        )
        mock_llm.return_value = mock_instance

        state = make_state(user_input="分析对比这两个方案的优劣")
        result = await MultiAgentGraph(history_manager=FakeHistoryManager()).input_node(state)
        assert result["intent"] == "analysis"

    @pytest.mark.asyncio
    @patch("backend.multi_agent.graph.build_chat_llm")
    async def test_falls_back_to_general_on_invalid_json(self, mock_llm):
        mock_instance = AsyncMock()
        mock_instance.ainvoke.return_value = FakeLLMResponse("not json at all")
        mock_llm.return_value = mock_instance

        state = make_state(user_input="今天天气怎么样")
        result = await MultiAgentGraph(history_manager=FakeHistoryManager()).input_node(state)
        assert result["intent"] == "general"
        assert result["required_tools"] == []

    @pytest.mark.asyncio
    @patch("backend.multi_agent.graph.build_chat_llm")
    async def test_falls_back_on_unknown_agent(self, mock_llm):
        mock_instance = AsyncMock()
        mock_instance.ainvoke.return_value = FakeLLMResponse(
            '{"intent": "nonexistent", "required_tools": []}'
        )
        mock_llm.return_value = mock_instance

        state = make_state(user_input="some request")
        result = await MultiAgentGraph(history_manager=FakeHistoryManager()).input_node(state)
        assert result["intent"] == "general"

    @pytest.mark.asyncio
    @patch("backend.multi_agent.graph.build_chat_llm")
    async def test_llm_suggests_tools(self, mock_llm):
        mock_instance = AsyncMock()
        mock_instance.ainvoke.return_value = FakeLLMResponse(
            '{"intent": "general", "required_tools": ["get_weather"]}'
        )
        mock_llm.return_value = mock_instance

        state = make_state(user_input="北京天气怎么样")
        result = await MultiAgentGraph(history_manager=FakeHistoryManager()).input_node(state)
        assert "get_weather" in result["required_tools"]
