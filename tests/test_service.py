from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.multi_agent.service import MultiAgentService
from backend.multi_agent.enums import ExecutionMode

class FakeHistoryManager:
    def __init__(self):
        self.conversations = {}
    def get(self, chat_id):
        return self.conversations.get(chat_id, [])
    def save_conversation(self, chat_id, messages, meta=None):
        self.conversations[chat_id] = messages

@pytest.mark.asyncio
async def test_service_retry_logic():
    history = FakeHistoryManager()
    service = MultiAgentService(history_manager=history)
    
    # Mock the graph to fail first time (quality_passed=False) and pass second time
    mock_graph = MagicMock()
    
    state_fail = {
        "quality_passed": False,
        "execution_mode": ExecutionMode.WORKFLOW.value,
        "max_retries": 2,
        "trace": [{"type": "stage_start", "stage": "init"}],
        "final_answer": "bad answer"
    }
    state_pass = {
        "quality_passed": True,
        "execution_mode": ExecutionMode.PLAN_EXECUTE.value,
        "max_retries": 2,
        "trace": [{"type": "stage_start", "stage": "init"}],
        "final_answer": "good answer"
    }
    
    # Use side_effect to return different states
    mock_graph.run = AsyncMock(side_effect=[state_fail, state_pass])
    mock_graph.initial_state = service.graph.initial_state # use real initial_state logic
    
    service.graph = mock_graph
    
    events = []
    async for sse in service.stream_chat(chat_id=1, user_msg="test"):
        events.append(sse)
    
    # Check if we got a warning event (retry)
    assert any("warning" in e for e in events)
    assert any("good answer" in e for e in events)
    assert any("event: done" in e for e in events)
    
    # Verify graph was called twice
    assert mock_graph.run.call_count == 2
