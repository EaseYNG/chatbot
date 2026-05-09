import os
from backend.config import FILES_DIR


class MdIO:
    @staticmethod
    def to_md(msg: str, file: str) -> None:
        """Write a string to a markdown file under files/."""
        try:
            with open(os.path.join(FILES_DIR, file), "w", encoding="utf-8") as f:
                f.write(msg)
        except FileNotFoundError:
            print(f"Error: The file {file} was not found.")
        except IOError as e:
            print(f"IOError: {e}")

    @staticmethod
    def read_md(file: str) -> str | None:
        """Read a string from a markdown file under files/."""
        try:
            with open(os.path.join(FILES_DIR, file), "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print(f"Error: The file {file} was not found.")
        except IOError as e:
            print(f"IOError: {e}")
