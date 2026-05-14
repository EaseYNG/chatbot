from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


class FakeLLMResponse:
    def __init__(self, content: str):
        self.content = content


@pytest.fixture
def mock_llm():
    """Fixture that patches build_chat_llm to return a controllable mock."""

    def _make_mock(response: str):
        patch_target = "backend.multi_agent.graph.build_chat_llm"
        from unittest.mock import patch

        patcher = patch(patch_target)
        mock_factory = patcher.start()
        instance = AsyncMock()
        instance.ainvoke.return_value = FakeLLMResponse(response)
        mock_factory.return_value = instance
        return patcher

    return _make_mock
