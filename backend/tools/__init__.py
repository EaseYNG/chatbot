from backend.tools.weather import get_weather, recommend_activity
from backend.tools.io import write, read


def get_all_tools() -> list:
    """Return the default tool list. Extend this to add RAG or skill tools."""
    return [write, read, get_weather, recommend_activity]


def get_tool_registry() -> dict[str, object]:
    registry: dict[str, object] = {}
    for tool in get_all_tools():
        name = getattr(tool, "name", None) or getattr(tool, "__name__", None)
        if name:
            registry[name] = tool
    return registry


def get_tools_by_names(names: list[str] | None) -> list:
    if not names:
        return get_all_tools()

    registry = get_tool_registry()
    return [registry[name] for name in names if name in registry]
