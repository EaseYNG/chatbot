# 🏗️ LangChain 多 Agent 系统（Orchestrator 模式）

> 基于 **Orchestrator 模式** 的 LangChain 多 Agent 协作系统，支持任务分解、DAG 调度、并行执行和结果聚合。

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3%2B-green)](https://www.langchain.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 目录

- [项目概述](#-项目概述)
- [系统架构](#-系统架构)
- [核心特性](#-核心特性)
- [快速开始](#-快速开始)
- [配置说明](#-配置说明)
- [代码结构](#-代码结构)
- [运行说明](#-运行说明)
- [使用示例](#-使用示例)
- [API 参考](#-api-参考)
- [测试](#-测试)
- [常见问题](#-常见问题)
- [扩展指南](#-扩展指南)
- [许可证](#-许可证)

---

## 🎯 项目概述

本项目实现了一个基于 **Orchestrator 模式** 的 LangChain 多 Agent 协作系统。核心思想是：

1. **一个 Orchestrator（协调者）** 作为中央调度器
2. **多个子 Agent** 各司其职（分析、编码、检索、总结等）
3. **任务分解与 DAG 调度** 实现复杂任务的自动拆解和高效执行
4. **结果聚合** 将多个 Agent 的输出合并为连贯的最终回答

### 适用场景

| 场景 | 说明 |
|------|------|
| 📊 **数据分析报告** | 数据检索 → 分析 → 图表生成 → 报告撰写 |
| 💻 **代码开发** | 需求分析 → 代码编写 → 代码审查 → 测试 |
| 🔍 **深度研究** | 多源信息检索 → 交叉验证 → 综合报告 |
| 📝 **文档生成** | 信息收集 → 结构化 → 格式化输出 |
| ✅ **质量检查** | 多角度验证 → 冲突检测 → 最终审核 |

---

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户输入                                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Orchestrator Agent                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   任务处理流水线                           │  │
│  │                                                          │  │
│  │  ① 意图识别 ──→ ② 任务分解 ──→ ③ 依赖分析 ──→ ④ 调度执行 │  │
│  │                           │                              │  │
│  │                           ▼                              │  │
│  │                    ⑤ 结果聚合 ──→ ⑥ 最终回复              │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   Analyst Agent  │ │   Coder Agent   │ │ Retriever Agent │
│   (数据分析师)    │ │   (代码工程师)   │ │   (知识检索员)   │
├─────────────────┤ ├─────────────────┤ ├─────────────────┤
│ 工具:           │ │ 工具:           │ │ 工具:           │
│ • 计算器        │ │ • Python REPL   │ │ • 网络搜索      │
│ • 图表生成      │ │ • 文件读写      │ │ • 向量数据库    │
│ • 统计分析      │ │ • 代码审查      │ │ • 文档检索      │
└─────────────────┘ └─────────────────┘ └─────────────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Summarizer Agent│ │  Planner Agent  │ │ Validator Agent │
│   (总结专家)    │ │   (规划专员)     │ │   (验证员)      │
├─────────────────┤ ├─────────────────┤ ├─────────────────┤
│ 工具:           │ │ 工具:           │ │ 工具:           │
│ • 文本处理      │ │ • 思维链        │ │ • 对比检查      │
│ • 模板引擎      │ │ • 时间规划      │ │ • 质量检测      │
│ • 格式化输出    │ │ • 风险评估      │ │ • 错误修正      │
└─────────────────┘ └─────────────────┘ └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      共享工具层 / 工具库                         │
│  [搜索工具] [计算器] [文件读写] [API调用] [数据库] [代码执行]   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      记忆 / 状态管理层                           │
│  [短期记忆] [长期记忆] [共享上下文] [会话历史] [任务状态]       │
└─────────────────────────────────────────────────────────────────┘
```

### 调度流程图

```
用户输入
    │
    ▼
┌──────────────┐
│ 意图识别      │ ← 判断任务类型、复杂度、领域
└──────┬──────┘
       │
       ▼
┌──────────────┐
│ 任务分解      │ ← 拆分为原子子任务（LLM驱动）
└──────┬──────┘
       │
       ▼
┌──────────────┐
│ 依赖分析      │ ← 构建 DAG 依赖图
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────────┐
│          调度执行（按 DAG 拓扑序）          │
│                                          │
│  阶段一（并行）：                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Agent A  │  │ Agent B  │  │ Agent C  │ │
│  └──────────┘  └──────────┘  └──────────┘ │
│                                          │
│  阶段二（串行 - 依赖A+B结果）：              │
│  ┌──────────────────────────────────┐     │
│  │         Agent D                  │     │
│  └──────────────────────────────────┘     │
│                                          │
│  阶段三（并行 - 依赖D结果）：               │
│  ┌──────────┐  ┌──────────┐              │
│  │ Agent E  │  │ Agent F  │              │
│  └──────────┘  └──────────┘              │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────┐
│ 结果聚合      │ ← 去重、排序、冲突解决
└──────┬──────┘
       │
       ▼
┌──────────────┐
│ 生成最终回复   │ ← LLM 综合所有结果
└──────────────┘
```

### 通信机制

采用 **消息队列 + 共享上下文** 的混合模式：

```
┌─────────────────────────────────────────┐
│           共享上下文 (Shared Context)      │
│  ┌───────┬───────┬───────┬───────┐      │
│  │ 任务池 │ 结果池 │ 状态表 │ 全局变量 │      │
│  └───────┴───────┴───────┴───────┘      │
└─────────────────────────────────────────┘
         ▲              ▲
         │ 读写          │ 读写
    ┌────┴────┐    ┌────┴────┐
    │Orchestrator│◄───│ Agent A  │
    └─────────┘    └─────────┘
```

---

## ✨ 核心特性

### 🎯 4 种调度策略

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| **串行模式** | Agent 依次执行，前一个输出作为后一个输入 | 流水线式处理 |
| **并行模式** | 所有 Agent 同时执行，结果合并 | 多角度分析 |
| **DAG 模式** | 基于依赖图自动调度，支持并行+串行混合 | 复杂任务（默认） |
| **混合模式** | 根据任务特性动态选择最优策略 | 通用场景 |

### 🤖 6 种预置 Agent

| Agent | 角色 | 核心能力 | 工具 |
|-------|------|----------|------|
| **Analyst** | 数据分析师 | 数据解读、趋势分析、报告生成 | 计算器、统计分析 |
| **Coder** | 代码工程师 | 代码编写、调试、代码审查 | Python REPL、文件读写 |
| **Retriever** | 知识检索员 | 信息查找、文档问答、RAG | 网络搜索、向量数据库 |
| **Summarizer** | 总结专家 | 文本摘要、信息提炼、格式化输出 | LLM、模板引擎 |
| **Planner** | 规划专员 | 任务规划、步骤拆解、风险评估 | 思维链、工具链 |
| **Validator** | 验证员 | 结果校验、质量检查、错误修正 | 对比检查、测试工具 |

### 🔧 其他特性

- ✅ **自动任务分解** — LLM 驱动，智能拆分复杂任务
- ✅ **DAG 依赖管理** — 自动识别任务依赖，最大化并行度
- ✅ **错误处理与重试** — 内置容错机制，提高系统鲁棒性
- ✅ **结构化日志** — 每个 Agent 输出可追踪的日志信息
- ✅ **可扩展架构** — 轻松添加自定义 Agent 和工具
- ✅ **交互式 CLI** — 支持命令行和交互模式

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- OpenAI API 密钥（或其他兼容的 LLM API）

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/yourusername/multi-agent-system.git
cd multi-agent-system
```

#### 2. 创建虚拟环境（推荐）

```bash
# 使用 venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 使用 conda
conda create -n multi-agent python=3.10
conda activate multi-agent
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API 密钥：

```ini
# OpenAI API 配置
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL_NAME=gpt-4

# 可选：其他 LLM 提供商
# ANTHROPIC_API_KEY=sk-ant-...
# AZURE_OPENAI_API_KEY=...
```

---

## ⚙️ 配置说明

### 环境变量

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `OPENAI_API_KEY` | ✅ | — | OpenAI API 密钥 |
| `OPENAI_MODEL_NAME` | ❌ | `gpt-4` | 使用的模型名称 |
| `OPENAI_TEMPERATURE` | ❌ | `0` | LLM 温度参数 |
| `MAX_RETRIES` | ❌ | `3` | 任务重试次数 |
| `LOG_LEVEL` | ❌ | `INFO` | 日志级别 |

### 依赖清单（requirements.txt）

```
langchain>=0.3.0
langchain-openai>=0.1.0
langchain-community>=0.3.0
python-dotenv>=1.0.0
pydantic>=2.0.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

---

## 📁 代码结构

```
multi-agent-system/
│
├── core/                          # 核心模块
│   ├── __init__.py                # 模块导出
│   ├── types.py                   # 基础类型定义
│   ├── base_agent.py              # Agent 基类
│   ├── orchestrator.py            # Orchestrator 调度器（核心）
│   └── agent_factory.py           # Agent 工厂（预置 6 种 Agent）
│
├── tests/                         # 测试模块
│   ├── __init__.py
│   └── test_orchestrator.py       # 单元测试（12 个测试用例）
│
├── examples/                      # 使用示例
│   └── basic_usage.py             # 基本使用示例
│
├── main.py                        # 主程序入口
├── .env.example                   # 环境变量模板
├── requirements.txt               # 依赖列表
├── README.md                      # 项目文档（本文件）
└── LICENSE                        # 许可证
```

### 核心模块说明

#### `core/types.py` — 基础类型定义

```python
class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 待执行
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 已失败

class SubTask:
    """子任务定义"""
    task_id: str             # 任务 ID
    instruction: str         # 任务指令
    agent_type: str          # 目标 Agent 类型
    dependencies: List[str]  # 依赖任务 ID 列表
    status: TaskStatus       # 任务状态
    result: Optional[str]    # 执行结果

class TaskResult:
    """任务执行结果"""
    task_id: str
    agent_type: str
    output: str
    success: bool
    error: Optional[str]
```

#### `core/base_agent.py` — Agent 基类

封装 LangChain 的 `AgentExecutor`，提供统一接口：

```python
class BaseAgent:
    def __init__(self, name, llm, tools, system_prompt):
        """初始化 Agent"""
        
    async def execute(self, task: SubTask, context: dict = None) -> str:
        """执行任务（统一接口）"""
```

#### `core/orchestrator.py` — Orchestrator 调度器（核心）

```python
class Orchestrator:
    def __init__(self, llm):
        """初始化调度器"""
        
    def register_agent(self, name: str, agent: BaseAgent):
        """注册子 Agent"""
        
    async def process(self, user_input: str) -> str:
        """主处理流程"""
        # 1. 任务分解
        # 2. DAG 调度执行
        # 3. 结果聚合
```

#### `core/agent_factory.py` — Agent 工厂

```python
class AgentFactory:
    @staticmethod
    def create_default_agents(llm) -> Dict[str, BaseAgent]:
        """创建 6 种预置 Agent"""
```

---

## ▶️ 运行说明

### 交互模式（推荐）

```bash
python main.py
```

启动后进入交互式命令行：

```
╔══════════════════════════════════════════════════════════════╗
║       🤖 LangChain 多 Agent 系统 (Orchestrator 模式)        ║
╚══════════════════════════════════════════════════════════════╝

已注册 Agent: analyst, coder, retriever, summarizer, planner, validator
调度策略: DAG 模式（自动依赖调度）

请输入你的问题（输入 'exit' 退出，输入 'help' 查看帮助）:

> 
```

### 命令行模式

```bash
# 单次查询
python main.py --query "分析2024年AI行业趋势"

# 指定输出文件
python main.py --query "写一个Python快速排序函数" --output result.md

# 指定调度策略
python main.py --query "..." --strategy parallel

# 详细日志
python main.py --query "..." --verbose
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--query`, `-q` | 直接执行查询（不进入交互模式） | — |
| `--output`, `-o` | 输出结果到文件 | — |
| `--strategy`, `-s` | 调度策略：`dag`/`parallel`/`serial`/`auto` | `dag` |
| `--verbose`, `-v` | 显示详细执行日志 | `False` |

### 作为模块导入

```python
import asyncio
from core.orchestrator import Orchestrator
from core.agent_factory import AgentFactory
from langchain_openai import ChatOpenAI

async def main():
    # 1. 初始化 LLM
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    
    # 2. 创建 Agent
    agents = AgentFactory.create_default_agents(llm)
    
    # 3. 创建 Orchestrator 并注册 Agent
    orchestrator = Orchestrator(llm)
    for name, agent in agents.items():
        orchestrator.register_agent(name, agent)
    
    # 4. 处理请求
    result = await orchestrator.process("分析2024年AI行业趋势")
    print(result)

asyncio.run(main())
```

---

## 💡 使用示例

### 示例 1：数据分析与报告生成

```bash
python main.py --query "分析2023年全球新能源汽车市场趋势，包括主要厂商市场份额、增长率预测，并生成一份简要报告"
```

**执行流程：**
1. **Planner** — 规划分析框架和步骤
2. **Retriever** — 搜索市场数据和行业报告
3. **Analyst** — 分析数据、计算增长率
4. **Summarizer** — 整合信息生成报告
5. **Validator** — 检查数据准确性和逻辑一致性

### 示例 2：代码开发任务

```bash
python main.py --query "写一个Python函数，实现LRU缓存，包含详细注释和单元测试"
```

**执行流程：**
1. **Planner** — 拆解任务：设计 → 编码 → 测试
2. **Coder** — 编写 LRU 缓存实现代码
3. **Validator** — 代码审查，检查边界情况
4. **Coder** — 根据审查意见优化代码
5. **Summarizer** — 整理最终代码和说明

### 示例 3：深度研究任务

```bash
python main.py --query "对比分析Transformer和Mamba架构的异同，包括理论基础、性能表现和适用场景"
```

**执行流程：**
1. **Retriever** × 3 — 同时从多个来源检索信息
2. **Analyst** — 对比分析两种架构
3. **Validator** — 交叉验证信息准确性
4. **Summarizer** — 生成结构化对比报告

### 示例 4：Python 代码中使用

```python
# examples/basic_usage.py
import asyncio
from core.orchestrator import Orchestrator
from core.agent_factory import AgentFactory
from langchain_openai import ChatOpenAI

async def main():
    # 初始化
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    agents = AgentFactory.create_default_agents(llm)
    
    orchestrator = Orchestrator(llm)
    for name, agent in agents.items():
        orchestrator.register_agent(name, agent)
    
    # 执行任务
    queries = [
        "用Python写一个二分查找算法",
        "解释量子计算的基本原理",
        "分析2024年云计算市场趋势",
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"📝 问题: {query}")
        print(f"{'='*60}")
        
        result = await orchestrator.process(query)
        print(f"\n✅ 回答:\n{result}")

asyncio.run(main())
```

---

## 📚 API 参考

### `Orchestrator` 类

```python
class Orchestrator:
    def __init__(
        self,
        llm: BaseLanguageModel,
        max_retries: int = 3,
        verbose: bool = False
    )
```

**方法：**

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `register_agent()` | 注册子 Agent | `name: str, agent: BaseAgent` | `None` |
| `process()` | 处理用户请求 | `user_input: str` | `str` |
| `decompose_task()` | 任务分解 | `user_input: str` | `List[SubTask]` |
| `execute_dag()` | DAG 调度执行 | `tasks: List[SubTask]` | `None` |
| `aggregate_results()` | 结果聚合 | `user_input, tasks` | `str` |

### `BaseAgent` 类

```python
class BaseAgent:
    def __init__(
        self,
        name: str,
        llm: BaseLanguageModel,
        tools: List[Tool],
        system_prompt: str
    )
```

**方法：**

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `execute()` | 执行任务 | `task: SubTask, context: dict` | `str` |

### `AgentFactory` 类

```python
class AgentFactory:
    @staticmethod
    def create_default_agents(llm) -> Dict[str, BaseAgent]
    @staticmethod
    def create_agent(name, llm, tools, system_prompt) -> BaseAgent
```

---

## 🧪 测试

```bash
# 运行全部测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_orchestrator.py::test_basic_query -v

# 查看测试覆盖率
pytest tests/ --cov=core -v

# 运行测试并生成报告
pytest tests/ -v --html=report.html
```

### 测试覆盖

| 测试类别 | 测试用例数 | 说明 |
|----------|-----------|------|
| 基础功能 | 4 | 单 Agent 执行、简单查询 |
| DAG 调度 | 3 | 依赖图构建、并行执行 |
| 错误处理 | 2 | 重试机制、降级策略 |
| 边界情况 | 3 | 空输入、超长输入、无效 Agent |

---

## ❓ 常见问题

### Q1: 为什么需要 API 密钥？

系统使用 LLM（如 GPT-4）进行任务分解、Agent 调度和结果聚合，因此需要有效的 API 密钥。

### Q2: 如何添加自定义 Agent？

```python
from core.base_agent import BaseAgent
from langchain.tools import Tool

# 1. 定义自定义工具
my_tool = Tool.from_function(
    func=my_function,
    name="my_tool",
    description="我的自定义工具"
)

# 2. 创建自定义 Agent
my_agent = BaseAgent(
    name="my_agent",
    llm=llm,
    tools=[my_tool],
    system_prompt="你是一个自定义专家..."
)

# 3. 注册到 Orchestrator
orchestrator.register_agent("my_agent", my_agent)
```

### Q3: 支持哪些 LLM 提供商？

支持所有 LangChain 兼容的 LLM 提供商：
- OpenAI（GPT-4, GPT-3.5）
- Anthropic（Claude）
- Azure OpenAI
- 本地模型（通过 Ollama 等）

### Q4: 如何处理执行错误？

系统内置了自动重试机制（默认 3 次）。如果所有重试都失败，Orchestrator 会：
1. 记录错误日志
2. 跳过失败任务
3. 使用已有结果生成回答
4. 在最终回复中注明部分失败

### Q5: 如何优化性能？

- 使用 `gpt-3.5-turbo` 替代 `gpt-4`（速度更快）
- 减少并行 Agent 数量
- 启用结果缓存
- 使用更小的模型进行简单任务

---

## 🔧 扩展指南

### 添加新的调度策略

```python
# 在 orchestrator.py 中添加
class Orchestrator:
    async def execute_custom_strategy(self, tasks: List[SubTask]):
        """自定义调度策略"""
        # 实现你的调度逻辑
        pass
```

### 添加新的 Agent 角色

```python
# 在 agent_factory.py 中添加
@staticmethod
def create_custom_agent(llm) -> BaseAgent:
    tools = [
        Tool.from_function(...),
        # 自定义工具
    ]
    system_prompt = "你是一个[角色]专家..."
    return BaseAgent("custom", llm, tools, system_prompt)
```

### 集成外部工具

```python
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

wikipedia = WikipediaQueryRun(
    api_wrapper=WikipediaAPIWrapper()
)

# 添加到 Agent 的工具列表
tools.append(wikipedia)
```

---

## 📄 许可证

本项目基于 MIT 许可证开源。详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

- [LangChain](https://www.langchain.com/) — 强大的 LLM 应用框架
- [OpenAI](https://openai.com/) — 提供强大的语言模型

---

<p align="center">
  <b>如果这个项目对你有帮助，请给一个 ⭐️！</b>
</p>
