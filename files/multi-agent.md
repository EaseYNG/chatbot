# 多 Agent 对话系统 - 基于当前仓库的可落地实现方案

## 1. 结论

这件事 **可行**，但必须按“在现有单 Agent 项目上渐进升级”的方式实施，不能直接按全新项目重写。

当前仓库已经具备多 Agent 演进所需的 5 个基础条件：

- 已接入 `langgraph` 与 `langchain`
- 已有统一的 `ChatBot` 封装和工具注册入口
- 已有 `FastAPI + SSE` 的流式返回链路
- 已有前端对流式事件的消费能力
- 已有会话历史持久化机制

因此，多 Agent 方案不需要推翻现有结构，推荐做法是：

1. 保留现有 Web API、CLI、前端聊天界面
2. 将当前 `ChatBot` 从“单个 Agent 调用器”升级为“Orchestrator 工作流入口”
3. 在 `backend/` 内新增 Orchestrator、路由决策、专业 Agent 和执行状态模型
4. 扩展 SSE 事件类型，让前端能够展示“阶段、计划、子 Agent、工具、最终结果”

---

## 2. 与现有项目的匹配度

### 2.1 已可复用的现有能力

| 现有模块 | 当前职责 | 在多 Agent 方案中的作用 |
|------|------|------|
| `backend/api/routes.py` | 暴露 `/api/chat` 与会话接口 | 保持不变，继续作为统一入口 |
| `backend/agent/chatbot.py` | 封装 DeepSeek + LangChain Agent | 升级为多 Agent 工作流入口 |
| `backend/agent/streaming.py` | 将 LangGraph/LangChain 事件转换为 SSE | 扩展为工作流事件总线 |
| `backend/memory/history_manager.py` | JSON 持久化对话历史 | 继续保存最终消息与结构化元数据 |
| `backend/tools/__init__.py` | 统一注册工具 | 扩展为“按 Agent 分配工具” |
| `frontend/src/api/client.js` | 解析 SSE 流 | 增加对阶段/计划/Agent 事件的解析 |
| `frontend/src/stores/chat.js` | 维护消息流式状态 | 增加工作流进度状态 |
| `frontend/src/components/chat/*` | 渲染消息和工具调用 | 增加阶段条、计划面板、Agent 标签 |

### 2.2 当前不足

原文中的设计要完全落地，当前仓库还缺少以下关键能力：

- 没有 Orchestrator 状态模型
- 没有复杂度评估器和执行模式路由器
- 没有专业 Agent 注册表
- 没有计划执行器和多分支工作流
- 没有结构化的质量评估与重试机制
- 没有可持久化的 LangGraph checkpointer，当前仍是内存版 `MemorySaver`
- 前端只能理解 `token`、`tool_start`、`tool_end`、`done`、`error`，无法展示多 Agent 过程

结论：**架构方向正确，但原文需要从“抽象蓝图”收敛到“当前仓库可分阶段交付的实施方案”。**

---

## 3. 推荐范围

### 3.1 v1 必做范围

v1 只实现文本型多 Agent，不一次性引入 PDF、OCR、音频、视频。

v1 范围建议限制为：

- Orchestrator 主管流程
- 输入分析
- 复杂度评估
- 三种执行模式
  - `react`
  - `plan_execute`
  - `workflow`
- 4 个专业 Agent
  - `general`
  - `coding`
  - `writing`
  - `analysis`
- SSE 过程事件
- 前端进度展示
- 失败重试与降级
- 最终结果和过程摘要持久化

### 3.2 v1 暂不做

以下内容建议明确排除在 v1 之外：

- 真正的多模态输入
- 视频和音频处理
- 浏览器自动化工具链
- 大规模 RAG
- 人工介入后台
- 分布式任务队列
- 并行子图执行

这些能力可以在 v2、v3 再进入。

---

## 4. 目标架构

### 4.1 总体思路

保留现有访问链路：

`前端/CLI -> FastAPI /chat -> ChatService -> OrchestratorGraph -> SSE -> 前端`

升级后后端主调用链为：

`routes.py -> MultiAgentService -> OrchestratorGraph -> Specialized Agent -> OutputAssembler -> HistoryManager`

### 4.2 分层设计

```
frontend
  -> 发起聊天请求
  -> 渲染工作流阶段和最终回复

api
  -> 接收请求、返回 SSE

service
  -> 创建运行上下文
  -> 调用 Orchestrator 图
  -> 汇总事件

orchestrator
  -> 输入处理
  -> 复杂度评估
  -> 路由选择
  -> 执行监控
  -> 质量评估
  -> 重试/降级

agents
  -> general agent
  -> coding agent
  -> writing agent
  -> analysis agent

memory
  -> 对话消息持久化
  -> 工作流摘要持久化
```

### 4.3 执行模式

#### `react`

适用于简单问答或单工具调用。

实现方式：

- Orchestrator 只做轻量输入分析
- 直接路由到 `general agent`
- 输出结果后进入质量检查

#### `plan_execute`

适用于多步骤但仍由一个专业域主导的任务。

实现方式：

- 先生成结构化计划
- 按顺序执行步骤
- 每步执行后写入状态
- 失败可在步骤级重试

#### `workflow`

适用于跨领域协作任务。

实现方式：

- Orchestrator 生成子任务图
- 将子任务分配给不同专业 Agent
- 汇总中间产物
- 最终交给合成节点生成答复

---

## 5. 基于当前仓库的目录落点

不建议新建一个平行项目目录，应该直接落在 `backend/` 下。

推荐结构如下：

```text
backend/
├── agent/
│   ├── chatbot.py
│   ├── streaming.py
│   └── llm_factory.py
├── multi_agent/
│   ├── service.py
│   ├── graph.py
│   ├── registry.py
│   ├── prompts.py
│   ├── enums.py
│   ├── state.py
│   ├── events.py
│   ├── router.py
│   ├── quality.py
│   ├── reducers.py
│   ├── nodes/
│   │   ├── init_node.py
│   │   ├── input_node.py
│   │   ├── complexity_node.py
│   │   ├── route_node.py
│   │   ├── react_node.py
│   │   ├── planner_node.py
│   │   ├── workflow_node.py
│   │   ├── output_node.py
│   │   ├── quality_node.py
│   │   ├── recovery_node.py
│   │   └── finalize_node.py
│   └── agents/
│       ├── base.py
│       ├── general.py
│       ├── coding.py
│       ├── writing.py
│       └── analysis.py
├── tools/
│   ├── __init__.py
│   ├── weather.py
│   ├── md_io.py
│   ├── registry.py
│   └── bundles.py
├── memory/
│   ├── history_manager.py
│   ├── checkpointer.py
│   └── run_store.py
└── models/
    ├── schemas.py
    └── workflow.py
```

---

## 6. 核心数据模型

### 6.1 枚举

建议新增以下枚举：

- `Stage`
  - `INIT`
  - `INPUT`
  - `COMPLEXITY`
  - `ROUTING`
  - `EXECUTION`
  - `OUTPUT`
  - `QUALITY`
  - `RECOVERY`
  - `DONE`

- `ExecutionMode`
  - `REACT`
  - `PLAN_EXECUTE`
  - `WORKFLOW`

- `IntentType`
  - `GENERAL`
  - `CODING`
  - `WRITING`
  - `ANALYSIS`

- `StepStatus`
  - `PENDING`
  - `RUNNING`
  - `DONE`
  - `FAILED`
  - `SKIPPED`

### 6.2 OrchestratorState

建议以 `TypedDict` 或 `pydantic.BaseModel` 定义统一状态：

```python
class OrchestratorState(BaseModel):
    thread_id: int
    run_id: str
    user_input: str
    system_message: str
    current_stage: str
    intent: str
    complexity_score: int = 0
    execution_mode: str = "REACT"
    selected_agent: str = "general"
    required_tools: list[str] = []
    plan_steps: list[dict] = []
    step_results: list[dict] = []
    events: list[dict] = []
    warnings: list[str] = []
    errors: list[dict] = []
    retry_count: int = 0
    max_retries: int = 2
    final_answer: str = ""
    final_payload: dict = {}
```

### 6.3 计划步骤模型

```python
class PlanStep(BaseModel):
    step_id: str
    title: str
    description: str
    agent: str
    tools: list[str] = []
    depends_on: list[str] = []
    status: str = "PENDING"
```

### 6.4 执行结果模型

```python
class StepResult(BaseModel):
    step_id: str
    agent: str
    status: str
    output: str = ""
    tool_calls: list[dict] = []
    error: str = ""
    elapsed_ms: int = 0
```

---

## 7. Agent 设计

### 7.1 基本原则

专业 Agent 不建议一开始做成完全独立模型实例；v1 推荐：

- 共享同一个 LLM 工厂
- 使用不同系统提示词
- 使用不同工具白名单
- 使用统一执行接口

这样能先把编排跑通，后续再扩展真正的异构 Agent。

### 7.2 Agent 注册表

建议以注册表管理 Agent 能力：

```python
AGENT_REGISTRY = {
    "general": {
        "system_prompt": "...",
        "tools": ["get_weather", "read_md"],
        "intents": ["general"],
    },
    "coding": {
        "system_prompt": "...",
        "tools": ["read_md", "to_md"],
        "intents": ["coding"],
    },
    "writing": {
        "system_prompt": "...",
        "tools": ["read_md", "to_md"],
        "intents": ["writing"],
    },
    "analysis": {
        "system_prompt": "...",
        "tools": ["read_md"],
        "intents": ["analysis"],
    },
}
```

### 7.3 v1 四类 Agent 职责

#### General Agent

- 处理简单问答
- 处理兜底任务
- 适配 `react` 模式

#### Coding Agent

- 处理代码解释、重构建议、方案设计类任务
- v1 先不直接执行本地命令
- 后续可接入更强工具

#### Writing Agent

- 处理摘要、重写、扩写、翻译、结构化写作
- 可写入 `files/` 中的 Markdown

#### Analysis Agent

- 处理结构化分析、结论归纳、对比评估
- v1 不做 pandas 图表链路，先做文本分析版

---

## 8. 输入处理与复杂度评估

### 8.1 输入处理器

输入处理建议先采用“规则 + LLM 兜底”混合模式：

1. 先用规则识别关键词
2. 再让一个轻量 LLM 结构化补全
3. 输出统一的 `InputAnalysis`

推荐输出字段：

- `intent`
- `entities`
- `required_tools`
- `needs_context`
- `output_format`
- `risk_flags`

### 8.2 复杂度评分

建议保留原文思路，但将评分规则写死在代码中，便于调试：

| 因素 | 分值 |
|------|------|
| 单轮简单问答 | 10 |
| 涉及工具调用 | +10/个，上限 20 |
| 明确要求“步骤/方案/比较” | +15 |
| 依赖历史上下文 | +10 |
| 需要跨领域协作 | +25 |
| 指定复杂结构化输出 | +10 |

路由阈值建议：

- `0-24` -> `REACT`
- `25-54` -> `PLAN_EXECUTE`
- `55+` -> `WORKFLOW`

### 8.3 为什么这样更适合当前项目

原文的评分维度包含多模态、图表、OCR、视频等，但当前仓库没有这些能力。
如果直接照搬，评分会失真，导致路由不稳定。

---

## 9. Orchestrator 图设计

### 9.1 节点图

建议采用如下 LangGraph 节点：

```text
init
  -> input
  -> complexity
  -> route
  -> react_exec / planner / workflow_exec
  -> output
  -> quality
  -> recovery_or_finalize
```

### 9.2 节点职责

#### `init_node`

- 初始化 `run_id`
- 记录开始时间
- 写入第一条阶段事件

#### `input_node`

- 解析输入意图
- 提取工具需求
- 识别是否依赖上下文

#### `complexity_node`

- 计算复杂度分值
- 选出执行模式

#### `route_node`

- 决定使用哪个专业 Agent
- 决定是否进入 planner/workflow

#### `react_node`

- 单次调用某个 Agent
- 产生 token/tool 事件

#### `planner_node`

- 生成 `plan_steps`
- 顺序执行每个 step
- 为每步指定 agent 和 tools

#### `workflow_node`

- 生成多个子任务
- 子任务顺序执行
- 汇总中间结果

#### `output_node`

- 汇总 `step_results`
- 生成最终答案
- 生成可展示的结构化摘要

#### `quality_node`

- 检查结果是否为空
- 检查是否有关键错误
- 打出质量分

#### `recovery_node`

- 决定重试、降级还是结束

#### `finalize_node`

- 返回最终状态
- 写入会话历史和运行摘要

---

## 10. SSE 事件协议扩展

### 10.1 现状

当前前端只支持：

- `token`
- `tool_start`
- `tool_end`
- `done`
- `error`

这不足以表达多 Agent 编排过程。

### 10.2 建议新增事件

v1 推荐增加以下事件类型：

| 事件 | 用途 |
|------|------|
| `stage_start` | 某阶段开始 |
| `stage_end` | 某阶段结束 |
| `route` | 路由结果 |
| `plan` | 生成执行计划 |
| `step_start` | 计划步骤开始 |
| `step_end` | 计划步骤结束 |
| `agent_start` | 某专业 Agent 开始处理 |
| `agent_end` | 某专业 Agent 完成处理 |
| `quality` | 质量评估结果 |
| `warning` | 非致命风险提示 |

### 10.3 事件示例

```text
event: stage_start
data: {"stage":"INPUT","label":"输入分析"}

event: route
data: {"mode":"PLAN_EXECUTE","agent":"coding","score":38}

event: plan
data: {"steps":[{"step_id":"s1","title":"分析需求"},{"step_id":"s2","title":"给出方案"}]}

event: step_start
data: {"step_id":"s1","agent":"coding","title":"分析需求"}

event: quality
data: {"score":82,"passed":true}
```

### 10.4 前端改造要求

前端至少要新增两类状态：

- `workflowEvents`
- `currentPlan`

界面上建议增加：

- 聊天区顶部显示当前阶段
- AI 消息上方显示“由哪个 Agent 回答”
- 可折叠的执行计划面板
- 错误和降级提示条

---

## 11. 历史与记忆设计

### 11.1 当前问题

当前 `HistoryManager` 只保存简化后的消息列表，不保存：

- 执行模式
- 计划步骤
- 阶段事件
- 质量评分
- 错误与重试信息

### 11.2 建议扩展

历史结构建议增加 `meta`：

```json
{
  "thread_id": 1,
  "title": "xxx",
  "messages": [],
  "meta": {
    "execution_mode": "PLAN_EXECUTE",
    "selected_agent": "coding",
    "quality_score": 82,
    "plan_steps": [],
    "warnings": [],
    "run_id": "..."
  }
}
```

### 11.3 checkpointer 方案

v1 可以继续使用 `MemorySaver`，但要明确限制：

- 服务重启后，LangGraph 内部状态丢失
- 可通过 `HistoryManager` 重放关键上下文
- 真正的图状态持久化留到 v2

v2 再切换到：

- `SqliteSaver`
- 或自定义 DB checkpointer

---

## 12. API 与 Schema 变更

### 12.1 `ChatRequest`

建议在现有字段基础上增加可选参数：

- `mode_hint`: 用户指定模式，如 `auto/react/plan/workflow`
- `agent_hint`: 用户指定偏好 Agent
- `return_trace`: 是否返回完整过程事件

### 12.2 对话详情

`GET /conversations/{id}` 建议在后续返回：

- `messages`
- `meta`
- `last_run_summary`

这样前端切换历史会话时，能恢复“这次对话是如何完成的”。

---

## 13. 具体实施步骤

## 阶段一：后端基础设施

目标：搭出可运行的工作流骨架，但先不改前端。

任务：

- 新增 `backend/multi_agent/state.py`
- 新增枚举、计划步骤、运行结果模型
- 新增 `llm_factory.py`
- 抽出统一的 Agent 执行接口
- 新增 Agent 注册表和工具白名单逻辑

交付标准：

- 可在单元测试中构造 `OrchestratorState`
- 不影响现有单 Agent 路径

## 阶段二：Orchestrator 图落地

目标：让 `/api/chat` 可切换到多 Agent 工作流。

任务：

- 实现 `graph.py`
- 实现输入分析、复杂度评估、路由节点
- 实现 `react_node`
- 实现 `planner_node`
- 实现 `workflow_node`
- 实现 `quality_node` 和 `recovery_node`

交付标准：

- 同一接口可完成三种模式路由
- 能输出结构化状态和阶段事件

## 阶段三：SSE 协议升级

目标：把工作流事件推给前端。

任务：

- 扩展 `backend/agent/streaming.py`
- 兼容原有 `token/tool_*` 事件
- 新增 `stage_*`、`route`、`plan`、`step_*`、`quality`

交付标准：

- 前端不升级时仍至少能收到最终回复
- 新前端能消费全部过程事件

## 阶段四：前端可视化

目标：让多 Agent 过程可见。

任务：

- 扩展 `frontend/src/api/client.js`
- 扩展 `frontend/src/stores/chat.js`
- 新增工作流进度组件，如 `WorkflowTimeline.vue`
- 扩展 `MessageItem.vue` 支持 Agent 标签
- 在 `ChatPanel.vue` 显示当前模式和阶段

交付标准：

- 用户能看到“当前阶段、路由结果、计划步骤、最终回复”

## 阶段五：持久化与回放

目标：保存结果和过程摘要。

任务：

- 扩展 `HistoryManager`
- 保存 `meta`
- 历史会话切换时恢复过程摘要

交付标准：

- 打开旧会话时能看到主要执行信息

## 阶段六：优化与增强

目标：提高稳定性和扩展性。

任务：

- 降级策略
- 重试策略
- 更细粒度的工具分配
- 更强的质量评估
- checkpointer 持久化

---

## 14. 测试方案

### 14.1 单元测试

覆盖以下模块：

- 输入分类
- 复杂度评分
- 路由决策
- 计划生成结果校验
- 质量评估与降级逻辑

### 14.2 集成测试

至少覆盖 3 条主路径：

1. 简单问答 -> `REACT`
2. 多步骤写作/总结 -> `PLAN_EXECUTE`
3. 跨领域综合任务 -> `WORKFLOW`

### 14.3 前端联调

验证：

- 阶段事件是否按顺序显示
- 工具事件与 Agent 事件是否共存
- 历史会话恢复是否正常

### 14.4 手工验收清单

- 新对话可以正常创建
- 简单问题不会被错误升级为复杂工作流
- 复杂任务能展示清晰的计划和步骤
- 某一步失败后可以看到重试或降级提示
- 最终答复仍兼容现有消息渲染

---

## 15. 风险与规避

### 15.1 最大风险

最大风险不是“能不能写出来”，而是“多 Agent 带来的复杂度是否超过当前项目承载能力”。

### 15.2 主要风险点

#### 事件流过于复杂

风险：

- SSE 事件种类太多，前端状态容易错乱

规避：

- 所有事件统一成 `{type, payload}` 语义
- 先做最小事件集，不一次性上全部

#### 规划质量不稳定

风险：

- planner 输出步骤不稳定，执行链路会抖动

规避：

- 先要求 planner 输出严格 JSON
- 用 schema 校验，不合法则回退 `REACT`

#### 状态持久化不足

风险：

- 服务重启后无法完整回放工作流

规避：

- v1 只承诺保存最终结果和过程摘要
- 不承诺图级别断点续跑

#### Agent 职责边界模糊

风险：

- coding / analysis / writing 路由经常打架

规避：

- 路由规则先简单明确
- 设置 `general` 兜底
- 为每类任务准备 20 到 30 条样例回归测试

---

## 16. 里程碑建议

### M1：可运行骨架

- 有 OrchestratorState
- 有三种模式路由
- 后端能产出阶段事件
- 不改前端

### M2：前端可见

- 聊天界面显示阶段和计划
- 兼容现有 token 流

### M3：稳定化

- 有重试、降级、质量评估
- 历史会话保存摘要

### M4：增强版

- 引入持久化 checkpointer
- 引入更多专业工具

---

## 17. 最终建议

这份设计 **值得做**，但必须遵守以下实施原则：

1. 不重写现有项目，只在现有骨架上扩展
2. 先实现文本型多 Agent，再扩展多模态
3. 先做“可观测工作流”，再做“复杂工具生态”
4. 先保证 SSE 和前端状态稳定，再增加并发和高级能力
5. 先保存“结果和摘要”，再追求“完整图状态恢复”

如果按这个方案推进，当前仓库完全可以演进为一个可维护的多 Agent 系统，而不是停留在概念图层面。

---

> 文档版本: v2.0  
> 适用项目: 当前 `e:\dev\chatbot` 仓库  
> 实施策略: 单 Agent 平滑升级为可观测的多 Agent Orchestrator 系统
