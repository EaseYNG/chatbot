from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.multi_agent.service import MultiAgentService
from backend.multi_agent.enums import ExecutionMode


class FakeHistoryManager:
    def __init__(self):
        self.conversations = {}

    async def get(self, chat_id):
        return self.conversations.get(chat_id, [])

    async def save_conversation(self, chat_id, messages, meta=None, user_id=None):
        self.conversations[chat_id] = messages


def _make_astream_events(final_state: dict):
    """Create an async generator that simulates astream_events output."""
    async def _gen(_state, _config, **_kwargs):
        # Yield a LangGraph end event so the service captures final_state
        yield {
            "event": "on_chain_end",
            "name": "LangGraph",
            "data": {"output": final_state},
        }
    return _gen


@pytest.mark.asyncio
async def test_service_retry_logic():
    history = FakeHistoryManager()
    service = MultiAgentService(history_manager=history)

    mock_graph = MagicMock()

    state_fail = {
        "quality_passed": False,
        "execution_mode": ExecutionMode.WORKFLOW.value,
        "max_retries": 2,
        "trace": [],
        "final_answer": "bad answer",
    }
    state_pass = {
        "quality_passed": True,
        "execution_mode": ExecutionMode.PLAN_EXECUTE.value,
        "max_retries": 2,
        "trace": [],
        "final_answer": "good answer",
    }

    # Mock graph.graph.astream_events to return different states
    graph_attr = MagicMock()
    graph_attr.astream_events = _make_astream_events(state_fail)
    mock_graph.graph = graph_attr
    mock_graph.initial_state = service.graph.initial_state
    mock_graph.run = AsyncMock(return_value=state_fail)

    service.graph = mock_graph

    events = []
    async for sse in service.stream_chat(chat_id=1, user_msg="test"):
        events.append(sse)

    # On first call with no streaming events, quality_passed=False falls through,
    # then quality_passed stays False (since we don't have more events),
    # then attempt > max_retries or downgraded is None -> break.
    # The test verifies the service doesn't crash on this path.
    # At minimum, we should see a done event.
    assert any("event: done" in e for e in events), "Expected done event"

    # Verify save was attempted (conversation appears in history)
    assert 1 in history.conversations
