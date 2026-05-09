from enum import StrEnum


class Stage(StrEnum):
    INIT = "INIT"
    INPUT = "INPUT"
    COMPLEXITY = "COMPLEXITY"
    ROUTING = "ROUTING"
    EXECUTION = "EXECUTION"
    OUTPUT = "OUTPUT"
    QUALITY = "QUALITY"
    DONE = "DONE"


class ExecutionMode(StrEnum):
    REACT = "REACT"
    PLAN_EXECUTE = "PLAN_EXECUTE"
    WORKFLOW = "WORKFLOW"


class IntentType(StrEnum):
    GENERAL = "general"
    CODING = "coding"
    WRITING = "writing"
    ANALYSIS = "analysis"
