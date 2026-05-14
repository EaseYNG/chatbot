"""基础类型定义 - LangChain 多Agent系统"""

from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentRole(Enum):
    """Agent角色枚举"""
    ANALYST = "analyst"
    CODER = "coder"
    RETRIEVER = "retriever"
    SUMMARIZER = "summarizer"
    PLANNER = "planner"
    VALIDATOR = "validator"


@dataclass
class SubTask:
    """子任务数据结构"""
    task_id: str
    instruction: str
    agent_type: str
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    priority: int = 0  # 优先级，数值越大优先级越高

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "instruction": self.instruction,
            "agent_type": self.agent_type,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "priority": self.priority,
        }


@dataclass
class TaskResult:
    """任务执行结果"""
    task_id: str
    agent_type: str
    output: str
    success: bool
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestratorContext:
    """共享上下文"""
    user_input: str
    session_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    intermediate_results: Dict[str, str] = field(default_factory=dict)
    global_variables: Dict[str, Any] = field(default_factory=dict)
