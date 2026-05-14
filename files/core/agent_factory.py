"""Agent工厂 - 创建预置的子Agent"""

from typing import List, Optional
from langchain_core.language_models import BaseLanguageModel
from langchain.tools import Tool
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

from .base_agent import BaseAgent


def create_analyst_agent(
    llm: BaseLanguageModel,
    verbose: bool = False,
    extra_tools: Optional[List[Tool]] = None,
) -> BaseAgent:
    """
    创建分析Agent - 数据分析师
    
    擅长数据解读、趋势分析、报告生成
    """
    tools = extra_tools or []
    
    # 添加默认工具
    tools.append(
        Tool.from_function(
            func=lambda x: eval(x, {"__builtins__": {}}, {}),
            name="calculator",
            description="用于数学计算。输入数学表达式，返回计算结果。",
        )
    )
    
    system_prompt = """你是一个专业的数据分析师。你的职责包括：
1. 数据解读：分析数据背后的含义和趋势
2. 统计分析：计算平均值、增长率、占比等统计指标
3. 报告生成：生成结构化的分析报告
4. 洞察发现：从数据中提取有价值的业务洞察

请使用专业、客观的语言进行分析，并在适当的时候使用数据支持你的结论。
如果需要进行计算，请使用calculator工具。"""
    
    return BaseAgent(
        name="analyst",
        role="analyst",
        llm=llm,
        tools=tools,
        system_prompt=system_prompt,
        verbose=verbose,
    )


def create_coder_agent(
    llm: BaseLanguageModel,
    verbose: bool = False,
    extra_tools: Optional[List[Tool]] = None,
) -> BaseAgent:
    """
    创建代码Agent - 代码工程师
    
    擅长代码编写、调试、代码审查
    """
    tools = extra_tools or []
    
    system_prompt = """你是一个专业的Python代码工程师。你的职责包括：
1. 代码编写：根据需求编写清晰、高效的Python代码
2. 代码调试：分析和修复代码中的bug
3. 代码审查：检查代码质量，提出改进建议
4. 技术方案：提供技术实现方案和最佳实践

请遵循以下原则：
- 代码要有良好的注释和文档
- 遵循PEP 8编码规范
- 考虑异常处理和边界情况
- 提供代码使用示例"""
    
    return BaseAgent(
        name="coder",
        role="coder",
        llm=llm,
        tools=tools,
        system_prompt=system_prompt,
        verbose=verbose,
    )


def create_retriever_agent(
    llm: BaseLanguageModel,
    verbose: bool = False,
    extra_tools: Optional[List[Tool]] = None,
) -> BaseAgent:
    """
    创建检索Agent - 知识检索员
    
    擅长信息查找、文档问答、知识检索
    """
    tools = extra_tools or []
    
    # 添加搜索工具
    try:
        search = DuckDuckGoSearchRun()
        tools.append(
            Tool.from_function(
                func=search.run,
                name="web_search",
                description="搜索互联网信息。输入搜索关键词，返回相关结果。",
            )
        )
    except Exception:
        pass
    
    try:
        wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
        tools.append(
            Tool.from_function(
                func=wikipedia.run,
                name="wikipedia",
                description="查询维基百科。输入查询关键词，返回百科内容。",
            )
        )
    except Exception:
        pass
    
    system_prompt = """你是一个专业的知识检索员。你的职责包括：
1. 信息查找：使用搜索工具查找准确、可靠的信息
2. 文档问答：基于检索到的文档回答问题
3. 事实核查：验证信息的准确性和可靠性
4. 知识整理：将检索到的信息整理成结构化的知识

请遵循以下原则：
- 优先使用可靠的信息源
- 标注信息的来源
- 如果找不到相关信息，如实告知
- 对信息进行交叉验证"""
    
    return BaseAgent(
        name="retriever",
        role="retriever",
        llm=llm,
        tools=tools,
        system_prompt=system_prompt,
        verbose=verbose,
    )


def create_summarizer_agent(
    llm: BaseLanguageModel,
    verbose: bool = False,
    extra_tools: Optional[List[Tool]] = None,
) -> BaseAgent:
    """
    创建总结Agent - 总结专家
    
    擅长文本摘要、信息提炼、格式化输出
    """
    tools = extra_tools or []
    
    system_prompt = """你是一个专业的总结专家。你的职责包括：
1. 文本摘要：将长文本提炼为简洁的摘要
2. 信息提炼：从大量信息中提取关键要点
3. 格式化输出：将信息整理为清晰的结构化格式
4. 多语言总结：支持中英文等多种语言的总结

请遵循以下原则：
- 保留核心信息，删除冗余内容
- 保持原文的主要观点和逻辑
- 使用清晰的结构（如列表、分段）
- 控制总结的长度，根据需求调整详略程度"""
    
    return BaseAgent(
        name="summarizer",
        role="summarizer",
        llm=llm,
        tools=tools,
        system_prompt=system_prompt,
        verbose=verbose,
    )


def create_planner_agent(
    llm: BaseLanguageModel,
    verbose: bool = False,
    extra_tools: Optional[List[Tool]] = None,
) -> BaseAgent:
    """
    创建规划Agent - 规划专员
    
    擅长任务规划、步骤拆解、风险评估
    """
    tools = extra_tools or []
    
    system_prompt = """你是一个专业的任务规划专家。你的职责包括：
1. 任务规划：将复杂目标分解为可执行的步骤
2. 时间估算：预估每个步骤所需的时间
3. 资源分配：合理分配人力、物力资源
4. 风险评估：识别潜在风险并制定应对策略

请遵循以下原则：
- 使用SMART原则制定目标
- 考虑任务之间的依赖关系
- 提供多个备选方案
- 明确每个步骤的交付物"""
    
    return BaseAgent(
        name="planner",
        role="planner",
        llm=llm,
        tools=tools,
        system_prompt=system_prompt,
        verbose=verbose,
    )


def create_validator_agent(
    llm: BaseLanguageModel,
    verbose: bool = False,
    extra_tools: Optional[List[Tool]] = None,
) -> BaseAgent:
    """
    创建验证Agent - 验证员
    
    擅长结果校验、质量检查、错误修正
    """
    tools = extra_tools or []
    
    system_prompt = """你是一个专业的质量验证员。你的职责包括：
1. 结果校验：检查输出结果的准确性和完整性
2. 质量检查：评估内容质量和格式规范性
3. 错误修正：发现并修正逻辑错误和事实错误
4. 一致性检查：确保输出与输入要求一致

请遵循以下原则：
- 严格检查事实准确性
- 检查逻辑一致性
- 验证格式规范性
- 提供具体的改进建议"""
    
    return BaseAgent(
        name="validator",
        role="validator",
        llm=llm,
        tools=tools,
        system_prompt=system_prompt,
        verbose=verbose,
    )


def get_default_agents(
    llm: BaseLanguageModel,
    verbose: bool = False,
    include: Optional[List[str]] = None,
) -> List[BaseAgent]:
    """
    获取默认的Agent列表
    
    Args:
        llm: 语言模型
        verbose: 是否输出详细日志
        include: 需要包含的Agent名称列表，默认全部包含
        
    Returns:
        List[BaseAgent]: Agent列表
    """
    all_agents = {
        "analyst": create_analyst_agent,
        "coder": create_coder_agent,
        "retriever": create_retriever_agent,
        "summarizer": create_summarizer_agent,
        "planner": create_planner_agent,
        "validator": create_validator_agent,
    }
    
    if include:
        creators = {name: all_agents[name] for name in include if name in all_agents}
    else:
        creators = all_agents
    
    agents = []
    for name, creator in creators.items():
        try:
            agent = creator(llm=llm, verbose=verbose)
            agents.append(agent)
        except Exception as e:
            print(f"创建Agent [{name}] 失败: {e}")
    
    return agents
