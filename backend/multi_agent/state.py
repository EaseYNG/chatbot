from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from pydantic import BaseModel, ValidationError


class PlanStep(BaseModel):
    """Validated plan step model for planner output schema enforcement."""

    step_id: str
    title: str
    description: str = ""
    agent: str = "general"


def validate_plan_steps(raw: list[dict]) -> list[dict]:
    """Validate and clean a list of raw step dicts against PlanStep schema.

    Returns only valid steps. Raises ValueError if zero steps survive validation.
    """
    cleaned: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            step = PlanStep(**item)
            cleaned.append(step.model_dump())
        except ValidationError:
            continue
    if not cleaned:
        raise ValueError("No valid plan steps after schema validation")
    return cleaned


TraceList = Annotated[list[dict], operator.add]
StringList = Annotated[list[str], operator.add]
DictList = Annotated[list[dict], operator.add]


class OrchestratorState(TypedDict, total=False):
    thread_id: int
    run_id: str
    user_input: str
    system_message: str
    current_stage: str
    intent: str
    complexity_score: int
    execution_mode: str
    selected_agent: str
    required_tools: list[str]
    plan_steps: list[dict]
    step_results: DictList
    warnings: StringList
    errors: DictList
    trace: TraceList
    retry_count: int
    max_retries: int
    final_answer: str
    quality_score: int
    quality_passed: bool
