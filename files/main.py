"""
LangChain 多Agent系统 - 主程序入口

基于Orchestrator模式的多Agent系统，支持任务分解、并行执行和结果聚合。
"""

import asyncio
import logging
import sys
from typing import Optional

from langchain_openai import ChatOpenAI

from core.orchestrator import Orchestrator, SchedulingStrategy
from core.agent_factory import get_default_agents

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class MultiAgentSystem:
    """
    多Agent系统主类
    
    封装了Orchestrator和Agent的创建、配置和执行
    """
    
    def __init__(
        self,
        model_name: str = "gpt-4",
        temperature: float = 0,
        verbose: bool = False,
        strategy: SchedulingStrategy = SchedulingStrategy.HYBRID,
        api_key: Optional[str] = None,
    ):
        """
        初始化多Agent系统
        
        Args:
            model_name: LLM模型名称
            temperature: 温度参数
            verbose: 是否输出详细日志
            strategy: 调度策略
            api_key: OpenAI API密钥
        """
        # 初始化LLM
        llm_kwargs = {
            "model": model_name,
            "temperature": temperature,
        }
        if api_key:
            llm_kwargs["api_key"] = api_key
            
        self.llm = ChatOpenAI(**llm_kwargs)
        
        # 创建默认Agent
        self.agents = get_default_agents(llm=self.llm, verbose=verbose)
        
        # 创建Orchestrator
        self.orchestrator = Orchestrator(
            llm=self.llm,
            strategy=strategy,
            verbose=verbose,
        )
        
        # 注册Agent
        self.orchestrator.register_agents(self.agents)
        
        # 注册回调
        if verbose:
            self.orchestrator.on_task_start = self._on_task_start
            self.orchestrator.on_task_complete = self._on_task_complete
            self.orchestrator.on_error = self._on_error
        
        self.verbose = verbose
        logger.info(
            f"多Agent系统初始化完成: "
            f"模型={model_name}, "
            f"Agent数量={len(self.agents)}, "
            f"调度策略={strategy.value}"
        )
    
    async def ask(self, query: str, **kwargs) -> str:
        """
        向系统提问
        
        Args:
            query: 用户问题
            **kwargs: 额外参数（如session_id, metadata等）
            
        Returns:
            str: 系统回答
        """
        logger.info(f"收到用户问题: {query[:100]}...")
        return await self.orchestrator.process(query, **kwargs)
    
    def ask_sync(self, query: str, **kwargs) -> str:
        """
        同步版本的提问方法
        
        Args:
            query: 用户问题
            **kwargs: 额外参数
            
        Returns:
            str: 系统回答
        """
        return asyncio.run(self.ask(query, **kwargs))
    
    def get_stats(self) -> dict:
        """获取系统统计信息"""
        return self.orchestrator.get_execution_summary()
    
    def _on_task_start(self, task):
        """任务开始回调"""
        logger.info(f"▶️ 开始执行任务: [{task.task_id}] {task.agent_type}")
    
    def _on_task_complete(self, task, result):
        """任务完成回调"""
        status = "✅" if result.success else "❌"
        logger.info(
            f"{status} 任务完成: [{task.task_id}] "
            f"耗时={result.execution_time:.2f}s"
        )
    
    def _on_error(self, error):
        """错误回调"""
        logger.error(f"⚠️ 系统错误: {error}")


def main():
    """命令行交互入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="LangChain 多Agent系统 (Orchestrator模式)"
    )
    parser.add_argument(
        "--model", 
        default="gpt-4",
        help="LLM模型名称 (默认: gpt-4)"
    )
    parser.add_argument(
        "--temperature", 
        type=float, 
        default=0,
        help="温度参数 (默认: 0)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="输出详细日志"
    )
    parser.add_argument(
        "--strategy",
        choices=["sequential", "parallel", "dag", "hybrid"],
        default="hybrid",
        help="调度策略 (默认: hybrid)"
    )
    parser.add_argument(
        "--query",
        help="直接执行查询并退出"
    )
    
    args = parser.parse_args()
    
    # 映射策略名称
    strategy_map = {
        "sequential": SchedulingStrategy.SEQUENTIAL,
        "parallel": SchedulingStrategy.PARALLEL,
        "dag": SchedulingStrategy.DAG,
        "hybrid": SchedulingStrategy.HYBRID,
    }
    
    # 初始化系统
    system = MultiAgentSystem(
        model_name=args.model,
        temperature=args.temperature,
        verbose=args.verbose,
        strategy=strategy_map[args.strategy],
    )
    
    if args.query:
        # 直接执行查询
        print(f"\n🔍 查询: {args.query}")
        print("⏳ 正在处理...\n")
        
        result = system.ask_sync(args.query)
        
        print(f"📋 回答:\n{result}\n")
        print(f"📊 统计: {system.get_stats()}")
    else:
        # 交互模式
        print("\n" + "="*60)
        print("🤖 LangChain 多Agent系统 (Orchestrator模式)")
        print("="*60)
        print(f"模型: {args.model}")
        print(f"调度策略: {args.strategy}")
        print(f"Agent数量: {len(system.agents)}")
        print("-"*60)
        print("输入 'exit' 或 'quit' 退出")
        print("输入 'stats' 查看统计信息")
        print("输入 'agents' 查看Agent列表")
        print("-"*60)
        
        while True:
            try:
                query = input("\n💬 请输入您的问题: ").strip()
                
                if query.lower() in ("exit", "quit"):
                    print("👋 再见！")
                    break
                
                if query.lower() == "stats":
                    print(f"📊 统计: {system.get_stats()}")
                    continue
                
                if query.lower() == "agents":
                    print("🤖 Agent列表:")
                    for agent in system.agents:
                        print(f"  - {agent.name} ({agent.role})")
                    continue
                
                if not query:
                    continue
                
                print("⏳ 正在处理...\n")
                result = system.ask_sync(query)
                print(f"📋 回答:\n{result}\n")
                
            except KeyboardInterrupt:
                print("\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 错误: {e}")


if __name__ == "__main__":
    main()
