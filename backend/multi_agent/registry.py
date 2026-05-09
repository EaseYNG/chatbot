from backend.multi_agent.enums import IntentType


AGENT_REGISTRY: dict[str, dict] = {
    "general": {
        "label": "General Agent",
        "intent": IntentType.GENERAL.value,
        "tools": ["get_weather", "read_md"],
        "system_prompt": (
            "You are the general-purpose agent in a multi-agent system. "
            "Answer clearly, stay concise, and use tools only when needed."
        ),
    },
    "coding": {
        "label": "Coding Agent",
        "intent": IntentType.CODING.value,
        "tools": ["read_md", "to_md"],
        "system_prompt": (
            "You are the coding specialist in a multi-agent system. "
            "Focus on architecture, implementation details, debugging, and code quality."
        ),
    },
    "writing": {
        "label": "Writing Agent",
        "intent": IntentType.WRITING.value,
        "tools": ["read_md", "to_md"],
        "system_prompt": (
            "You are the writing specialist in a multi-agent system. "
            "Produce clear, well-structured, reader-friendly content."
        ),
    },
    "analysis": {
        "label": "Analysis Agent",
        "intent": IntentType.ANALYSIS.value,
        "tools": ["read_md"],
        "system_prompt": (
            "You are the analysis specialist in a multi-agent system. "
            "Break down problems, compare options, and explain trade-offs."
        ),
    },
}


def get_agent_profile(name: str) -> dict:
    return AGENT_REGISTRY.get(name, AGENT_REGISTRY["general"])
