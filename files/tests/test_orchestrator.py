"""Orchestrator单元测试"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from langchain_core.language_models import BaseLanguageModel

from core.types import SubTask, TaskResult, TaskStatus
from core.base_agent import BaseAgent
from core.orchestrator import Orchestrator, SchedulingStrategy


@pytest.fixture
def mock_llm():
    """Mock LLM"""
    llm = Mock(spec=BaseLanguageModel)
    
    # Mock invoke方法
    async def mock_invoke(messages):
        mock_response = Mock()
        mock_response.content = '{"tasks": [{"task_id": "task_001", "instruction": "测试任务", "agent_type": "test_agent", "dependencies": [], "priority": 5}]}'
        return mock_response
    
    llm.ainvoke = AsyncMock(side_effect=mock_invoke)
    return llm


@pytest.fixture
def mock_agent():
    """Mock Agent"""
    agent = Mock(spec=BaseAgent)
    agent.name = "test_agent"
    agent.role = "test"
    
    async def mock_execute(task, context=None):
        return TaskResult(
            task_id=task.task_id,
            agent_type="test",
            output=f"执行结果: {task.instruction}",
            success=True,
            execution_time=0.1,
        )
    
    agent.execute = AsyncMock(side_effect=mock_execute)
    agent.get_capabilities = Mock(return_value=["测试能力"])
    
    return agent


@pytest.mark.asyncio
async def test_orchestrator_initialization(mock_llm):
    """测试Orchestrator初始化"""
    orchestrator = Orchestrator(llm=mock_llm, verbose=False)
    
    assert orchestrator.llm == mock_llm
    assert orchestrator.strategy == SchedulingStrategy.HYBRID
    assert len(orchestrator.agents) == 0
    assert orchestrator.context is None


@pytest.mark.asyncio
async def test_register_agent(mock_llm, mock_agent):
    """测试注册Agent"""
    orchestrator = Orchestrator(llm=mock_llm)
    orchestrator.register_agent(mock_agent)
    
    assert "test_agent" in orchestrator.agents
    assert orchestrator.agents["test_agent"] == mock_agent


@pytest.mark.asyncio
async def test_register_agents(mock_llm, mock_agent):
    """测试批量注册Agent"""
    orchestrator = Orchestrator(llm=mock_llm)
    
    agent2 = Mock(spec=BaseAgent)
    agent2.name = "test_agent_2"
    agent2.role = "test2"
    
    orchestrator.register_agents([mock_agent, agent2])
    
    assert len(orchestrator.agents) == 2
    assert "test_agent" in orchestrator.agents
    assert "test_agent_2" in orchestrator.agents


@pytest.mark.asyncio
async def test_decompose_task(mock_llm, mock_agent):
    """测试任务分解"""
    orchestrator = Orchestrator(llm=mock_llm)
    orchestrator.register_agent(mock_agent)
    
    tasks = await orchestrator._decompose_task("测试用户输入")
    
    assert len(tasks) > 0
    assert all(isinstance(t, SubTask) for t in tasks)
    assert tasks[0].task_id == "task_001"


@pytest.mark.asyncio
async def test_decompose_task_fallback(mock_llm, mock_agent):
    """测试任务分解失败时的降级处理"""
    # 模拟LLM返回无效JSON
    async def mock_invoke_error(messages):
        mock_response = Mock()
        mock_response.content = "无效的JSON响应"
        return mock_response
    
    mock_llm.ainvoke = AsyncMock(side_effect=mock_invoke_error)
    
    orchestrator = Orchestrator(llm=mock_llm)
    orchestrator.register_agent(mock_agent)
    
    tasks = await orchestrator._decompose_task("测试输入")
    
    # 应该降级为单个任务
    assert len(tasks) == 1
    assert tasks[0].task_id == "task_001"


@pytest.mark.asyncio
async def test_analyze_dependencies(mock_llm):
    """测试依赖分析"""
    orchestrator = Orchestrator(llm=mock_llm)
    
    tasks = [
        SubTask(task_id="task_001", instruction="任务1", agent_type="agent1"),
        SubTask(
            task_id="task_002", 
            instruction="任务2", 
            agent_type="agent2",
            dependencies=["task_001", "task_999"],  # task_999不存在
        ),
    ]
    
    result = orchestrator._analyze_dependencies(tasks)
    
    # 应该移除不存在的依赖
    assert result[1].dependencies == ["task_001"]


@pytest.mark.asyncio
async def test_execute_sequential(mock_llm, mock_agent):
    """测试串行执行"""
    orchestrator = Orchestrator(llm=mock_llm, strategy=SchedulingStrategy.SEQUENTIAL)
    orchestrator.register_agent(mock_agent)
    
    tasks = [
        SubTask(task_id="task_001", instruction="任务1", agent_type="test_agent"),
        SubTask(task_id="task_002", instruction="任务2", agent_type="test_agent"),
    ]
    
    await orchestrator._execute_tasks(tasks)
    
    assert tasks[0].status == TaskStatus.COMPLETED
    assert tasks[1].status == TaskStatus.COMPLETED
    assert mock_agent.execute.call_count == 2


@pytest.mark.asyncio
async def test_execute_parallel(mock_llm, mock_agent):
    """测试并行执行"""
    orchestrator = Orchestrator(llm=mock_llm, strategy=SchedulingStrategy.PARALLEL)
    orchestrator.register_agent(mock_agent)
    
    tasks = [
        SubTask(task_id="task_001", instruction="任务1", agent_type="test_agent"),
        SubTask(task_id="task_002", instruction="任务2", agent_type="test_agent"),
    ]
    
    await orchestrator._execute_tasks(tasks)
    
    assert tasks[0].status == TaskStatus.COMPLETED
    assert tasks[1].status == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_execute_dag(mock_llm, mock_agent):
    """测试DAG执行"""
    orchestrator = Orchestrator(llm=mock_llm, strategy=SchedulingStrategy.DAG)
    orchestrator.register_agent(mock_agent)
    
    tasks = [
        SubTask(task_id="task_001", instruction="任务1", agent_type="test_agent"),
        SubTask(
            task_id="task_002", 
            instruction="任务2", 
            agent_type="test_agent",
            dependencies=["task_001"],
        ),
        SubTask(
            task_id="task_003", 
            instruction="任务3", 
            agent_type="test_agent",
            dependencies=["task_001"],
        ),
    ]
    
    await orchestrator._execute_tasks(tasks)
    
    assert tasks[0].status == TaskStatus.COMPLETED
    assert tasks[1].status == TaskStatus.COMPLETED
    assert tasks[2].status == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_execute_single_task_success(mock_llm, mock_agent):
    """测试单个任务执行成功"""
    orchestrator = Orchestrator(llm=mock_llm)
    orchestrator.register_agent(mock_agent)
    
    task = SubTask(task_id="task_001", instruction="测试任务", agent_type="test_agent")
    
    await orchestrator._execute_single_task(task)
    
    assert task.status == TaskStatus.COMPLETED
    assert task.result == "执行结果: 测试任务"
    assert "task_001" in orchestrator.task_results


@pytest.mark.asyncio
async def test_execute_single_task_agent_not_found(mock_llm):
    """测试Agent不存在的情况"""
    orchestrator = Orchestrator(llm=mock_llm)
    
    task = SubTask(task_id="task_001", instruction="测试任务", agent_type="nonexistent")
    
    await orchestrator._execute_single_task(task)
    
    assert task.status == TaskStatus.FAILED
    assert "未找到Agent" in task.error


@pytest.mark.asyncio
async def test_aggregate_results(mock_llm, mock_agent):
    """测试结果聚合"""
    orchestrator = Orchestrator(llm=mock_llm)
    orchestrator.register_agent(mock_agent)
    
    # 模拟一些任务结果
    tasks = [
        SubTask(task_id="task_001", instruction="任务1", agent_type="test_agent"),
    ]
    
    # 先执行任务以产生结果
    await orchestrator._execute_single_task(tasks[0])
    
    # Mock聚合响应
    async def mock_aggregate(messages):
        mock_response = Mock()
        mock_response.content = "这是聚合后的最终回答"
        return mock_response
    
    mock_llm.ainvoke = AsyncMock(side_effect=mock_aggregate)
    
    result = await orchestrator._aggregate_results("用户问题", tasks)
    
    assert result == "这是聚合后的最终回答"


@pytest.mark.asyncio
async def test_full_process(mock_llm, mock_agent):
    """测试完整处理流程"""
    orchestrator = Orchestrator(llm=mock_llm, verbose=False)
    orchestrator.register_agent(mock_agent)
    
    # Mock聚合响应
    async def mock_aggregate(messages):
        mock_response = Mock()
        mock_response.content = "最终回答"
        return mock_response
    
    mock_llm.ainvoke = AsyncMock(side_effect=[
        # 第一次调用：任务分解
        Mock(content='{"tasks": [{"task_id": "task_001", "instruction": "分析趋势", "agent_type": "test_agent", "dependencies": [], "priority": 5}]}'),
        # 第二次调用：结果聚合
        Mock(content="最终回答"),
    ])
    
    result = await orchestrator.process("分析AI趋势")
    
    assert result == "最终回答"
    assert len(orchestrator.task_results) > 0


@pytest.mark.asyncio
async def test_get_execution_summary(mock_llm, mock_agent):
    """测试获取执行摘要"""
    orchestrator = Orchestrator(llm=mock_llm)
    orchestrator.register_agent(mock_agent)
    
    # 执行一些任务
    task = SubTask(task_id="task_001", instruction="测试", agent_type="test_agent")
    await orchestrator._execute_single_task(task)
    
    summary = orchestrator.get_execution_summary()
    
    assert summary["total_tasks"] == 1
    assert summary["successful"] == 1
    assert summary["failed"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
