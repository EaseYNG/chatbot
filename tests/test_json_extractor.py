from __future__ import annotations

import pytest
from backend.multi_agent.graph import _extract_json_block


class TestExtractJsonBlock:
    def test_pure_json_object(self):
        result = _extract_json_block('{"key": "value"}')
        assert result == {"key": "value"}

    def test_pure_json_array(self):
        result = _extract_json_block('[{"a": 1}, {"b": 2}]')
        assert result == [{"a": 1}, {"b": 2}]

    def test_json_in_code_fence(self):
        text = "```json\n{\"score\": 85, \"mode\": \"REACT\"}\n```"
        result = _extract_json_block(text)
        assert result == {"score": 85, "mode": "REACT"}

    def test_json_in_code_fence_no_lang(self):
        text = "```\n[1, 2, 3]\n```"
        result = _extract_json_block(text)
        assert result == [1, 2, 3]

    def test_embedded_array(self):
        text = "Here is the result:\n[{\"step\": \"s1\", \"title\": \"Analyze\"}]\nEnd."
        result = _extract_json_block(text)
        assert result == [{"step": "s1", "title": "Analyze"}]

    def test_embedded_object(self):
        text = "Output: {\"a\": 1, \"b\": 2} Done."
        result = _extract_json_block(text)
        assert result == {"a": 1, "b": 2}

    def test_nested_structure(self):
        text = '{"outer": {"inner": [1, 2, 3]}, "arr": [{"x": 1}]}'
        result = _extract_json_block(text)
        assert result == {"outer": {"inner": [1, 2, 3]}, "arr": [{"x": 1}]}

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="empty response"):
            _extract_json_block("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="empty response"):
            _extract_json_block("   \n\n  ")

    def test_no_json_raises(self):
        with pytest.raises(ValueError, match="no json found"):
            _extract_json_block("This is just plain text with no JSON at all")

    def test_broken_json_raises(self):
        """Unclosed brace inside code fence should fail."""
        with pytest.raises(ValueError):
            _extract_json_block("```json\n{\"key\": \"value\"\n```")

    def test_partial_json_still_extracted(self):
        """Even partial JSON in braces should be extracted."""
        text = "Some text before { \"key\": \"value\" } and after"
        result = _extract_json_block(text)
        assert result == {"key": "value"}

    def test_multiple_json_blocks_picks_first_valid(self):
        text = '```json\n{"first": "valid"}\n```\n```json\n{"second": "also_valid"}\n```'
        result = _extract_json_block(text)
        assert result == {"first": "valid"}
