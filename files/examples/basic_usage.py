"""
基本使用示例 - LangChain 多Agent系统
"""

import asyncio
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from main import MultiAgentSystem
from core.orchestrator import SchedulingStrategy


async def basic_example():
    """基础使用示例"""
    
    # 创建系统（使用环境变量中的API密钥）
    system = MultiAgentSystem(
        model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-4"),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0")),
        verbose=os.getenv("VERBOSE", "false").lower() == "true",
        strategy=SchedulingStrategy.HYBRID,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    
    print("="*60)
    print("示例1: 简单查询")
    print("="*60)
    result = await system.ask("2024年AI行业有哪些主要趋势？")
    print(f"回答: {result}\n")
    
    print("="*60)
    print("示例2: 复杂任务（需要多Agent协作）")
    print("="*60)
    result = await system.ask(
        "请分析Python和JavaScript的优缺点对比，并给出学习建议"
    )
    print(f"回答: {result}\n")
    
    print("="*60)
    print("示例3: 需要检索的任务")
    print("="*60)
    result = await system.ask("最近有哪些重要的科技新闻？")
    print(f"回答: {result}\n")
    
    # 打印统计信息
    print("="*60)
    print("系统统计")
    print("="*60)
    print(system.get_stats())


async def custom_agents_example():
    """自定义Agent示例"""
    
    from langchain.tools import Tool
    from core.agent_factory import create_analyst_agent, create_coder_agent
    from core.orchestrator import Orchestrator
    from langchain_openai import ChatOpenAI
    
    # 初始化LLM
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0,
    )
    
    # 创建自定义工具
    custom_tool = Tool.from_function(
        func=lambda x: f"处理: {x}",
        name="custom_processor",
        description="自定义处理工具",
    )
    
    # 创建自定义Agent
    analyst = create_analyst_agent(
        llm=llm,
        verbose=True,
        extra_tools=[custom_tool],
    )
    
    coder = create_coder_agent(
        llm=llm,
        verbose=True,
    )
    
    # 创建Orchestrator并注册Agent
    orchestrator = Orchestrator(llm=llm, verbose=True)
    orchestrator.register_agent(analyst)
    orchestrator.register_agent(coder)
    
    # 执行任务
    result = await orchestrator.process("计算 15 * 37 的结果")
    print(f"结果: {result}")


if __name__ == "__main__":
    # 运行基础示例
    asyncio.run(basic_example())
    
    # 取消注释运行自定义示例
    # asyncio.run(custom_agents_example())
