from __future__ import annotations

import pytest

from backend.multi_agent.state import PlanStep, validate_plan_steps


class TestPlanStepModel:
    def test_valid_step_passes(self):
        step = PlanStep(step_id="s1", title="Test", description="Desc", agent="general")
        assert step.step_id == "s1"
        assert step.title == "Test"

    def test_default_description(self):
        step = PlanStep(step_id="s1", title="Test")
        assert step.description == ""

    def test_default_agent(self):
        step = PlanStep(step_id="s1", title="Test")
        assert step.agent == "general"

    def test_missing_step_id_raises(self):
        with pytest.raises(Exception):
            PlanStep(title="Test")

    def test_missing_title_raises(self):
        with pytest.raises(Exception):
            PlanStep(step_id="s1")


class TestValidatePlanSteps:
    def test_valid_list_passes(self):
        raw = [
            {"step_id": "s1", "title": "Analyze", "description": "Analyze the problem", "agent": "analysis"},
            {"step_id": "s2", "title": "Solve", "description": "Solve the problem", "agent": "coding"},
        ]
        result = validate_plan_steps(raw)
        assert len(result) == 2
        assert result[0]["step_id"] == "s1"
        assert result[1]["agent"] == "coding"

    def test_missing_optional_fields_filled(self):
        raw = [{"step_id": "s1", "title": "Test"}]
        result = validate_plan_steps(raw)
        assert result[0]["description"] == ""
        assert result[0]["agent"] == "general"

    def test_invalid_step_filtered_out(self):
        raw = [
            {"step_id": "s1", "title": "Valid"},
            {"title": "Missing step_id"},
            {"step_id": "s2", "title": "Also valid"},
        ]
        result = validate_plan_steps(raw)
        assert len(result) == 2
        assert result[0]["step_id"] == "s1"
        assert result[1]["step_id"] == "s2"

    def test_empty_list_raises(self):
        with pytest.raises(ValueError, match="No valid plan steps"):
            validate_plan_steps([])

    def test_all_invalid_raises(self):
        raw = [
            {"title": "Missing ID 1"},
            {"title": "Missing ID 2"},
        ]
        with pytest.raises(ValueError, match="No valid plan steps"):
            validate_plan_steps(raw)

    def test_non_dict_items_skipped(self):
        raw = [
            {"step_id": "s1", "title": "Valid"},
            "not a dict",
            {"step_id": "s2", "title": "Also valid"},
        ]
        result = validate_plan_steps(raw)
        assert len(result) == 2

    def test_extra_fields_preserved(self):
        raw = [{"step_id": "s1", "title": "Test", "description": "Desc", "agent": "coding", "extra": "ignored"}]
        result = validate_plan_steps(raw)
        assert "extra" not in result[0]
