"""Orchestrator Agent - 多Agent系统的调度中枢"""

import json
import logging
import asyncio
import time
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage, SystemMessage

from .types import (
    SubTask, TaskResult, TaskStatus, AgentRole, OrchestratorContext
)
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class SchedulingStrategy(Enum):
    """调度策略枚举"""
    SEQUENTIAL = "sequential"      # 串行执行
    PARALLEL = "parallel"          # 并行执行
    DAG = "dag"                    # DAG依赖图执行
    HYBRID = "hybrid"              # 混合策略（默认）


class Orchestrator:
    """
    Orchestrator Agent - 协调者/调度者
    
    职责：
    1. 接收用户输入，分析意图
    2. 将复杂任务分解为子任务（Task Decomposition）
    3. 选择合适的子Agent并分配任务
    4. 监控各Agent执行状态
    5. 收集所有结果并进行合并/排序/冲突解决
    6. 生成最终回复
    """

    def __init__(
        self,
        llm: BaseLanguageModel,
        strategy: SchedulingStrategy = SchedulingStrategy.HYBRID,
        verbose: bool = False,
    ):
        self.llm = llm
        self.strategy = strategy
        self.verbose = verbose
        
        # Agent注册表
        self.agents: Dict[str, BaseAgent] = {}
        
        # 上下文管理器
        self.context: Optional[OrchestratorContext] = None
        
        # 任务执行记录
        self.task_results: Dict[str, TaskResult] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        # 钩子函数
        self.on_task_start: Optional[Callable] = None
        self.on_task_complete: Optional[Callable] = None
        self.on_error: Optional[Callable] = None

    def register_agent(self, agent: BaseAgent) -> None:
        """注册子Agent"""
        if agent.name in self.agents:
            logger.warning(f"Agent [{agent.name}] 已存在，将被覆盖")
        
        self.agents[agent.name] = agent
        logger.info(f"注册Agent: {agent.name} (角色: {agent.role})")

    def register_agents(self, agents: List[BaseAgent]) -> None:
        """批量注册Agent"""
        for agent in agents:
            self.register_agent(agent)

    async def process(self, user_input: str, **kwargs) -> str:
        """
        主处理流程
        
        Args:
            user_input: 用户输入
            **kwargs: 额外参数
            
        Returns:
            str: 最终回答
        """
        start_time = time.time()
        
        # 初始化上下文
        self.context = OrchestratorContext(
            user_input=user_input,
            session_id=kwargs.get("session_id", datetime.now().isoformat()),
            metadata=kwargs.get("metadata", {}),
        )
        
        # 重置任务结果
        self.task_results = {}
        
        logger.info(f"开始处理用户输入: {user_input[:100]}...")
        
        try:
            # Step 1: 意图识别与任务分解
            tasks = await self._decompose_task(user_input)
            
            if self.verbose:
                logger.info(f"任务分解完成: {len(tasks)} 个子任务")
                for t in tasks:
                    logger.debug(f"  - [{t.task_id}] {t.agent_type}: {t.instruction[:50]}...")
            
            # Step 2: 依赖分析
            tasks = self._analyze_dependencies(tasks)
            
            # Step 3: 执行任务
            await self._execute_tasks(tasks)
            
            # Step 4: 结果聚合
            final_answer = await self._aggregate_results(user_input, tasks)
            
            elapsed = time.time() - start_time
            logger.info(f"处理完成，总耗时: {elapsed:.2f}s")
            
            # 记录执行历史
            self.execution_history.append({
                "user_input": user_input,
                "tasks": [t.to_dict() for t in tasks],
                "final_answer": final_answer,
                "elapsed": elapsed,
                "timestamp": datetime.now().isoformat(),
            })
            
            return final_answer
            
        except Exception as e:
            error_msg = f"处理过程中发生错误: {str(e)}"
            logger.error(error_msg)
            
            if self.on_error:
                self.on_error(e)
            
            return f"抱歉，处理您的请求时出现了问题。错误信息: {str(e)}"

    async def _decompose_task(self, user_input: str) -> List[SubTask]:
        """
        使用LLM进行任务分解
        
        将用户输入分解为多个子任务，每个子任务指定由哪个Agent执行
        """
        available_agents = {
            name: {
                "role": agent.role,
                "capabilities": agent.get_capabilities(),
            }
            for name, agent in self.agents.items()
        }
        
        decomposition_prompt = f"""你是一个任务分解专家。请将用户请求分解为多个可执行的子任务。

可用Agent列表:
{json.dumps(available_agents, ensure_ascii=False, indent=2)}

用户请求: {user_input}

请分析用户请求，将其分解为1-5个子任务。对于每个子任务，请提供：
1. task_id: 唯一的任务ID（如 "task_001"）
2. instruction: 清晰具体的执行指令
3. agent_type: 由哪个Agent执行（必须是上面列表中的名称）
4. dependencies: 依赖的任务ID列表（如果该任务需要等待其他任务完成）
5. priority: 优先级（0-10，数值越大越优先）

请以JSON格式返回，格式如下：
{{
    "tasks": [
        {{
            "task_id": "task_001",
            "instruction": "具体指令",
            "agent_type": "agent_name",
            "dependencies": [],
            "priority": 5
        }}
    ]
}}

注意：
- 如果任务简单，可以只分解为1个子任务
- 任务之间如果有依赖关系，请在dependencies中指定
- 确保每个agent_type都在可用Agent列表中
- 返回纯JSON，不要包含其他文字
"""

        response = await self.llm.ainvoke(
            [HumanMessage(content=decomposition_prompt)]
        )
        
        # 解析JSON响应
        try:
            # 尝试提取JSON部分
            content = response.content if hasattr(response, 'content') else str(response)
            
            # 清理可能的markdown代码块标记
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            data = json.loads(content)
            tasks_data = data.get("tasks", [])
            
            tasks = []
            for t in tasks_data:
                task = SubTask(
                    task_id=t["task_id"],
                    instruction=t["instruction"],
                    agent_type=t["agent_type"],
                    dependencies=t.get("dependencies", []),
                    priority=t.get("priority", 0),
                )
                tasks.append(task)
            
            return tasks
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"任务分解JSON解析失败: {e}，使用默认单任务模式")
            
            # 降级：创建单个任务
            return [
                SubTask(
                    task_id="task_001",
                    instruction=user_input,
                    agent_type=list(self.agents.keys())[0] if self.agents else "unknown",
                    dependencies=[],
                    priority=5,
                )
            ]

    def _analyze_dependencies(self, tasks: List[SubTask]) -> List[SubTask]:
        """
        分析任务依赖关系
        
        确保依赖的任务ID都存在，移除无效依赖
        """
        task_ids = {t.task_id for t in tasks}
        
        for task in tasks:
            # 移除不存在的依赖
            valid_deps = [
                dep for dep in task.dependencies 
                if dep in task_ids and dep != task.task_id
            ]
            task.dependencies = valid_deps
        
        return tasks

    async def _execute_tasks(self, tasks: List[SubTask]) -> None:
        """执行所有任务，支持DAG依赖调度"""
        
        if self.strategy == SchedulingStrategy.SEQUENTIAL:
            await self._execute_sequential(tasks)
        elif self.strategy == SchedulingStrategy.PARALLEL:
            await self._execute_parallel(tasks)
        else:  # DAG 或 HYBRID
            await self._execute_dag(tasks)

    async def _execute_sequential(self, tasks: List[SubTask]) -> None:
        """串行执行任务"""
        for task in tasks:
            await self._execute_single_task(task)

    async def _execute_parallel(self, tasks: List[SubTask]) -> None:
        """并行执行任务"""
        coros = [self._execute_single_task(task) for task in tasks]
        await asyncio.gather(*coros)

    async def _execute_dag(self, tasks: List[SubTask]) -> None:
        """按DAG依赖图执行任务"""
        completed = set()
        total = len(tasks)
        
        while len(completed) < total:
            # 找出可执行的任务（所有依赖已完成）
            ready_tasks = []
            for task in tasks:
                if task.task_id in completed:
                    continue
                if task.status == TaskStatus.RUNNING:
                    continue
                if task.status == TaskStatus.FAILED:
                    continue
                    
                # 检查依赖是否全部完成
                deps_met = all(dep in completed for dep in task.dependencies)
                if deps_met:
                    ready_tasks.append(task)
            
            if not ready_tasks:
                # 检查是否有任务卡住
                pending = [t for t in tasks if t.task_id not in completed]
                if pending:
                    logger.warning(f"存在无法执行的任务: {[t.task_id for t in pending]}")
                    # 将无依赖的pending任务标记为可执行
                    for task in pending:
                        if not task.dependencies or all(
                            d in completed for d in task.dependencies
                        ):
                            ready_tasks.append(task)
                        else:
                            # 强制移除无法满足的依赖
                            task.dependencies = []
                            ready_tasks.append(task)
                else:
                    break
            
            # 按优先级排序
            ready_tasks.sort(key=lambda t: t.priority, reverse=True)
            
            # 并行执行
            coros = []
            for task in ready_tasks:
                task.status = TaskStatus.RUNNING
                coro = self._execute_single_task(task)
                coros.append(coro)
            
            if coros:
                await asyncio.gather(*coros)
                
                # 更新完成状态
                for task in ready_tasks:
                    if task.status == TaskStatus.COMPLETED:
                        completed.add(task.task_id)

    async def _execute_single_task(self, task: SubTask) -> None:
        """执行单个任务"""
        
        # 触发开始回调
        if self.on_task_start:
            self.on_task_start(task)
        
        # 查找对应的Agent
        agent = self.agents.get(task.agent_type)
        if not agent:
            error_msg = f"未找到Agent: {task.agent_type}"
            logger.error(error_msg)
            task.status = TaskStatus.FAILED
            task.error = error_msg
            return
        
        # 构建上下文（依赖任务的结果）
        context = {}
        for dep_id in task.dependencies:
            if dep_id in self.task_results:
                dep_result = self.task_results[dep_id]
                context[dep_id] = dep_result.output
        
        # 执行
        result = await agent.execute(task, context)
        
        # 更新任务状态
        if result.success:
            task.status = TaskStatus.COMPLETED
            task.result = result.output
            task.completed_at = datetime.now()
        else:
            task.status = TaskStatus.FAILED
            task.error = result.error
        
        # 保存结果
        self.task_results[task.task_id] = result
        
        # 更新共享上下文
        if self.context:
            self.context.intermediate_results[task.task_id] = result.output
        
        # 触发完成回调
        if self.on_task_complete:
            self.on_task_complete(task, result)

    async def _aggregate_results(
        self, 
        user_input: str, 
        tasks: List[SubTask]
    ) -> str:
        """聚合所有子任务结果，生成最终回答"""
        
        # 构建结果摘要
        results_lines = []
        for task in tasks:
            result = self.task_results.get(task.task_id)
            if result and result.success:
                results_lines.append(
                    f"## 任务 {task.task_id} ({task.agent_type})\n"
                    f"指令: {task.instruction}\n"
                    f"结果: {result.output}\n"
                )
            elif result:
                results_lines.append(
                    f"## 任务 {task.task_id} ({task.agent_type}) - 失败\n"
                    f"指令: {task.instruction}\n"
                    f"错误: {result.error}\n"
                )
        
        results_summary = "\n".join(results_lines)
        
        # 统计执行情况
        success_count = sum(
            1 for t in tasks 
            if self.task_results.get(t.task_id) 
            and self.task_results[t.task_id].success
        )
        total_count = len(tasks)
        
        aggregation_prompt = f"""你是一个结果汇总专家。请综合所有子任务的执行结果，生成一个完整、连贯、准确的最终回答。

用户原始请求: {user_input}

任务执行概况: {success_count}/{total_count} 个任务成功

各子任务执行结果:
{results_summary}

请综合以上结果，生成最终回答。要求：
1. 回答要完整覆盖用户的所有需求
2. 保持逻辑连贯，语言自然
3. 如果某个任务失败，请如实说明
4. 对于重要信息，可以适当强调
5. 最终回答应该像是一个专家直接给出的答案，而不是简单罗列各任务结果
"""
        
        response = await self.llm.ainvoke(
            [HumanMessage(content=aggregation_prompt)]
        )
        
        return response.content if hasattr(response, 'content') else str(response)

    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        return {
            "total_tasks": len(self.task_results),
            "successful": sum(1 for r in self.task_results.values() if r.success),
            "failed": sum(1 for r in self.task_results.values() if not r.success),
            "total_execution_time": sum(
                r.execution_time for r in self.task_results.values()
            ),
            "history_count": len(self.execution_history),
        }

    def clear_history(self) -> None:
        """清除执行历史"""
        self.execution_history.clear()
        self.task_results.clear()
        logger.info("执行历史已清除")
