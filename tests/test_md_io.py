from __future__ import annotations

from backend.tools.io import write, read


class TestPathTraversalPrevention:
    def test_read_md_blocks_path_traversal(self):
        result = read.invoke({"file": "../../../etc/passwd"})
        assert "Error: Access denied" in result

    def test_read_md_blocks_absolute_path(self):
        result = read.invoke({"file": "/etc/passwd"})
        assert "Error: Access denied" in result

    def test_read_md_blocks_windows_path_traversal(self):
        result = read.invoke({"file": r"..\..\..\windows\system32\config"})
        assert "Error: Access denied" in result

    def test_read_md_allows_valid_path(self):
        result = read.invoke({"file": "nonexistent.md"})
        # Should try to read a file that doesn't exist, getting a different error
        assert "Access denied" not in result
        assert "Error" in result  # FileNotFound or similar

    def test_to_md_blocks_path_traversal(self):
        result = write.invoke({"msg": "test", "file": "../../../etc/passwd"})
        assert "Error: Access denied" in result

    def test_to_md_blocks_absolute_path(self):
        result = write.invoke({"msg": "test", "file": "/etc/passwd"})
        assert "Error: Access denied" in result
