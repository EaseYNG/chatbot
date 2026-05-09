from backend.tools.weather import get_weather
from backend.tools.md_io import MdIO


def get_all_tools() -> list:
    """Return the default tool list. Extend this to add RAG or skill tools."""
    return [MdIO.to_md, MdIO.read_md, get_weather]
