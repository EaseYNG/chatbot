from langchain_deepseek import ChatDeepSeek

from backend.config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    DEEPSEEK_TEMPERATURE,
)


def build_chat_llm(*, streaming: bool = True, enable_thinking: bool = False) -> ChatDeepSeek:
    """Create the shared DeepSeek chat model instance.

    enable_thinking: If False (default), disables the reasoning/thinking mode
    to avoid ``reasoning_content`` round-trip issues with agent frameworks.
    Enable for single-turn calls (planner, classifier, output assembly) where
    deeper reasoning improves quality.
    """
    extra = {}
    if not enable_thinking:
        extra = {"thinking": {"type": "disabled"}}
    return ChatDeepSeek(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        model=DEEPSEEK_MODEL,
        temperature=DEEPSEEK_TEMPERATURE,
        streaming=streaming,
        extra_body=extra if extra else None,
    )
