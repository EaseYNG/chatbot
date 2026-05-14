import logging
import os

from langchain.tools import tool

from backend.config import FILES_DIR

logger = logging.getLogger(__name__)


@tool
def write(msg: str, file: str) -> str:
    """Write a string to a file under files/."""
    resolved = os.path.normpath(os.path.join(FILES_DIR, file))
    if not resolved.startswith(os.path.normpath(FILES_DIR)):
        logger.warning("Path traversal blocked for file=%s", file)
        return "Error: Access denied."
    try:
        os.makedirs(os.path.dirname(resolved), exist_ok=True)
        with open(resolved, "w", encoding="utf-8") as f:
            f.write(msg)
        return f"Written to {file}"
    except OSError as e:
        logger.error("IOError writing %s: %s", file, e)
        return f"Error: {e}"


@tool
def read(file: str) -> str:
    """Read a string from a file under files/."""
    resolved = os.path.normpath(os.path.join(FILES_DIR, file))
    if not resolved.startswith(os.path.normpath(FILES_DIR)):
        logger.warning("Path traversal blocked for file=%s", file)
        return "Error: Access denied."
    try:
        with open(resolved, "r", encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        logger.error("IOError reading %s: %s", file, e)
        return f"Error: {e}"
