from backend.tools.weather import get_weather
from backend.tools.md_io import MdIO


def get_all_tools() -> list:
    """Return the default tool list. Extend this to add RAG or skill tools."""
    return [MdIO.to_md, MdIO.read_md, get_weather]


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
