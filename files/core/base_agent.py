"""基础Agent类 - 所有子Agent的基类"""

import logging
import time
from typing import List, Dict, Any, Optional
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import SystemMessage, HumanMessage
from .types import SubTask, TaskResult, TaskStatus

logger = logging.getLogger(__name__)


class BaseAgent:
    """Agent基类，封装了LangChain Agent的通用逻辑"""

    def __init__(
        self,
        name: str,
        role: str,
        llm: BaseLanguageModel,
        tools: List[Tool],
        system_prompt: str,
        verbose: bool = False,
    ):
        self.name = name
        self.role = role
        self.llm = llm
        self.tools = tools
        self.system_prompt = system_prompt
        self.verbose = verbose

        # 构建Agent的Prompt模板
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # 创建Agent
        self.agent = create_openai_functions_agent(llm, tools, self.prompt)
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=tools,
            verbose=verbose,
            handle_parsing_errors=True,
            max_iterations=5,
            early_stopping_method="generate",
        )

    async def execute(
        self,
        task: SubTask,
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskResult:
        """
        执行任务
        
        Args:
            task: 要执行的任务
            context: 共享上下文信息
            
        Returns:
            TaskResult: 任务执行结果
        """
        start_time = time.time()
        
        try:
            # 构建输入
            input_text = self._build_input(task, context)
            
            logger.info(f"Agent [{self.name}] 开始执行任务: {task.task_id}")
            logger.debug(f"任务指令: {task.instruction[:100]}...")
            
            # 执行Agent
            result = await self.executor.ainvoke({"input": input_text})
            
            output = result["output"]
            execution_time = time.time() - start_time
            
            logger.info(
                f"Agent [{self.name}] 完成任务: {task.task_id} "
                f"(耗时: {execution_time:.2f}s)"
            )
            
            return TaskResult(
                task_id=task.task_id,
                agent_type=self.role,
                output=output,
                success=True,
                execution_time=execution_time,
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Agent [{self.name}] 执行任务失败: {str(e)}"
            logger.error(error_msg)
            
            return TaskResult(
                task_id=task.task_id,
                agent_type=self.role,
                output="",
                success=False,
                error=str(e),
                execution_time=execution_time,
            )

    def _build_input(
        self,
        task: SubTask,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """构建Agent输入文本"""
        parts = [f"任务ID: {task.task_id}"]
        
        if context:
            context_str = self._format_context(context)
            if context_str:
                parts.append(f"\n上下文信息:\n{context_str}")
        
        parts.append(f"\n任务指令:\n{task.instruction}")
        
        return "\n".join(parts)

    def _format_context(self, context: Dict[str, Any]) -> str:
        """格式化上下文信息"""
        lines = []
        for key, value in context.items():
            if isinstance(value, str) and len(value) > 500:
                value = value[:500] + "..."
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    def get_capabilities(self) -> List[str]:
        """获取Agent能力描述"""
        return [tool.description for tool in self.tools]

    def __repr__(self) -> str:
        return f"BaseAgent(name={self.name}, role={self.role}, tools={len(self.tools)})"
