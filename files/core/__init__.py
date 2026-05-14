"""
LangChain 多Agent系统核心模块

基于Orchestrator模式的多Agent协作系统。
"""

from .types import SubTask, TaskResult, TaskStatus, AgentRole, OrchestratorContext
from .base_agent import BaseAgent
from .orchestrator import Orchestrator, SchedulingStrategy
from .agent_factory import (
    create_analyst_agent,
    create_coder_agent,
    create_retriever_agent,
    create_summarizer_agent,
    create_planner_agent,
    create_validator_agent,
    get_default_agents,
)

__all__ = [
    # 类型定义
    "SubTask",
    "TaskResult",
    "TaskStatus",
    "AgentRole",
    "OrchestratorContext",
    
    # 核心类
    "BaseAgent",
    "Orchestrator",
    "SchedulingStrategy",
    
    # Agent工厂
    "create_analyst_agent",
    "create_coder_agent",
    "create_retriever_agent",
    "create_summarizer_agent",
    "create_planner_agent",
    "create_validator_agent",
    "get_default_agents",
]

__version__ = "1.0.0"
