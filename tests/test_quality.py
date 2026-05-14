from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from backend.multi_agent.enums import ExecutionMode
from backend.multi_agent.graph import MultiAgentGraph


class FakeHistoryManager:
    async def get(self, chat_id: int) -> list[dict]:  # noqa: ARG002
        return []


class FakeLLMResponse:
    def __init__(self, content: str):
        self.content = content


def make_state(**overrides):
    graph = MultiAgentGraph(history_manager=FakeHistoryManager())
    state = graph.initial_state(
        thread_id=1,
        user_input="test",
        system_message="You are helpful.",
    )
    state.update(overrides)
    return state


class TestQualityNode:
    @pytest.mark.asyncio
    @patch("backend.multi_agent.graph.build_chat_llm")
    async def test_quality_node_empty_answer_fails(self, mock_llm):
        """Empty final_answer should immediately fail with score 20."""
        state = make_state(final_answer="", quality_score=0)
        result = await MultiAgentGraph(history_manager=FakeHistoryManager()).quality_node(state)
        assert result["quality_score"] == 20
        assert result["quality_passed"] is False

    @pytest.mark.asyncio
    @patch("backend.multi_agent.graph.build_chat_llm")
    async def test_quality_node_llm_assessment(self, mock_llm):
        """LLM returns high scores, quality should pass."""
        mock_instance = AsyncMock()
        mock_instance.ainvoke.return_value = FakeLLMResponse(
            '{"completeness": 35, "accuracy": 25, "clarity": 25}'
        )
        mock_llm.return_value = mock_instance

        state = make_state(
            final_answer="This is a detailed and accurate response that fully addresses the question.",
        )
        result = await MultiAgentGraph(history_manager=FakeHistoryManager()).quality_node(state)
        assert result["quality_score"] == 85  # 35 + 25 + 25
        assert result["quality_passed"] is True

    @pytest.mark.asyncio
    @patch("backend.multi_agent.graph.build_chat_llm")
    async def test_quality_node_llm_low_score_fails(self, mock_llm):
        """LLM returns low scores, quality should fail."""
        mock_instance = AsyncMock()
        mock_instance.ainvoke.return_value = FakeLLMResponse(
            '{"completeness": 10, "accuracy": 15, "clarity": 10}'
        )
        mock_llm.return_value = mock_instance

        state = make_state(final_answer="Brief answer.")
        result = await MultiAgentGraph(history_manager=FakeHistoryManager()).quality_node(state)
        assert result["quality_score"] == 35  # 10 + 15 + 10
        assert result["quality_passed"] is False

    @pytest.mark.asyncio
    @patch("backend.multi_agent.graph.build_chat_llm")
    async def test_quality_node_llm_failure_falls_back(self, mock_llm):
        """When LLM fails, fall back to heuristic score of 80."""
        mock_instance = AsyncMock()
        mock_instance.ainvoke.return_value = FakeLLMResponse("invalid json")
        mock_llm.return_value = mock_instance

        state = make_state(
            final_answer="Some response here.",
            errors=[],
        )
        result = await MultiAgentGraph(history_manager=FakeHistoryManager()).quality_node(state)
        # Fallback gives 80, no errors, so passed
        assert result["quality_score"] == 80
        assert result["quality_passed"] is True

    @pytest.mark.asyncio
    @patch("backend.multi_agent.graph.build_chat_llm")
    async def test_quality_node_errors_reduce_score(self, mock_llm):
        """Presence of errors reduces final score by 20."""
        mock_instance = AsyncMock()
        mock_instance.ainvoke.return_value = FakeLLMResponse(
            '{"completeness": 35, "accuracy": 25, "clarity": 25}'
        )
        mock_llm.return_value = mock_instance

        state = make_state(
            final_answer="Good response but had errors.",
            errors=[{"message": "Something went wrong"}],
        )
        result = await MultiAgentGraph(history_manager=FakeHistoryManager()).quality_node(state)
        # 85 (LLM) - 20 (errors) = 65
        assert result["quality_score"] == 65
        assert result["quality_passed"] is True

    @pytest.mark.asyncio
    @patch("backend.multi_agent.graph.build_chat_llm")
    async def test_quality_node_errors_dont_go_below_zero(self, mock_llm):
        """Score floor at 0 when errors would take it negative."""
        mock_instance = AsyncMock()
        mock_instance.ainvoke.return_value = FakeLLMResponse(
            '{"completeness": 5, "accuracy": 5, "clarity": 5}'
        )
        mock_llm.return_value = mock_instance

        state = make_state(
            final_answer="Poor response with errors.",
            errors=[{"message": "Error 1"}, {"message": "Error 2"}],
        )
        result = await MultiAgentGraph(history_manager=FakeHistoryManager()).quality_node(state)
        # 15 (LLM) - 20 (errors) = 0 (clamped)
        assert result["quality_score"] == 0
        assert result["quality_passed"] is False
