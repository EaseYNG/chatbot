# 多 Agent 实施进展记录

## 本轮实施目标

在不推翻现有项目结构的前提下，完成多 Agent 架构的第一轮可运行版本，并同步更新文档。

---

## 阶段一：多 Agent 基础设施

### 目标

搭建后端骨架，抽出公共能力，准备状态模型和注册表。

### 已完成

- 新增 `backend/agent/llm_factory.py`
- 新增 `backend/multi_agent/__init__.py`
- 新增 `backend/multi_agent/enums.py`
- 新增 `backend/multi_agent/state.py`
- 新增 `backend/multi_agent/registry.py`
- `backend/tools/__init__.py` 支持按工具名筛选

### 成果

- 后端具备统一的 LLM 创建入口
- 多 Agent 所需的枚举、状态和 Agent 注册机制已经建立
- 后续图编排和执行器可以直接复用这一层

---

## 阶段二：Orchestrator 与执行模式

### 目标

让后端具备最小可运行的多 Agent 编排能力。

### 已完成

- 新增 `backend/multi_agent/graph.py`
- 新增 `backend/multi_agent/service.py`
- 接入 3 种执行模式：
  - `REACT`
  - `PLAN_EXECUTE`
  - `WORKFLOW`
- 实现输入分析、复杂度评分、执行路由、输出整理、质量评估
- 增加失败后向简单模式降级的最小逻辑

### 成果

- 多 Agent 已不再只是设计文档，后端已能依据请求复杂度自动选择执行路径
- 已可根据意图路由到 `general`、`coding`、`writing`、`analysis`
- 具备最小闭环：分析 -> 路由 -> 执行 -> 汇总 -> 质量检查

---

## 阶段三：API、SSE 与前端兼容

### 目标

让现有 Web 入口接入新后端，并尽量兼容现有前端展示逻辑。

### 已完成

- `backend/api/routes.py` 已切换到 `MultiAgentService`
- `backend/api/dependencies.py` 新增多 Agent 服务依赖
- `backend/models/schemas.py` 新增：
  - `mode_hint`
  - `agent_hint`
  - `return_trace`
- SSE 新增事件：
  - `stage_start`
  - `stage_end`
  - `route`
  - `plan`
  - `step_start`
  - `step_end`
  - `agent_start`
  - `agent_end`
  - `quality`
  - `warning`
- `frontend/src/stores/chat.js` 已支持将这些过程事件显示为基础系统提示

### 成果

- 新后端已经接入现有前端入口
- 即使没有新的可视化组件，用户也能在聊天流里看到多 Agent 过程提示
- 保留了 `token` 和 `done` 事件，旧前端不会因协议升级直接失效

---

## 阶段四：持久化与文档

### 目标

记录多 Agent 执行结果，更新项目文档，保证后续迭代可追踪。

### 已完成

- `backend/memory/history_manager.py` 新增 `meta` 持久化
- 支持保存：
  - 执行模式
  - 选中 Agent
  - 质量分
  - 计划步骤
  - 事件轨迹
- `README.md` 已更新为当前多 Agent 架构说明
- `files/multi-agent.md` 已整理为可落地实施方案
- 新增本进展记录文件

### 成果

- 会话历史不再只保存最终消息，也开始保存工作流摘要
- 文档与代码状态已经同步
- 后续阶段可以直接基于此记录继续迭代

---

## 阶段五：质量增强

### 目标

增强系统健壮性：计划器 schema 校验、前端时间线可视化、自动化测试。

### 已完成

- `backend/multi_agent/state.py` 新增 `PlanStep` Pydantic 模型与 `validate_plan_steps()` 函数
- `backend/multi_agent/graph.py` 计划器 `_plan_steps()` 接入严格 schema 校验，失败抛出 `ValueError`
- `execute_plan_node()` 与 `execute_workflow_node()` 捕获校验失败并降级为 REACT 直答（`_fallback_react()`）
- `backend/multi_agent/graph.py` `input_node()` 从硬编码关键词匹配改为 LLM 动态分类：
  - 输入分析读取 `AGENT_REGISTRY` 自动生成可用 Agent 列表
  - 新增 Agent 只需注册即可被路由识别，无需修改枚举或路由逻辑
- `backend/agent/llm_factory.py` 移除 `thinking: disabled`，允许 DeepSeek 推理链
- 新增 `tests/` 目录，37 项测试覆盖：
  - `test_routing.py`：复杂度评分、执行路由、LLM 意图分类（含 mock）、工具检测
  - `test_planner.py`：PlanStep 模型校验、`validate_plan_steps()` 边界情况
  - `test_downgrade.py`：降级链、重试状态、模式保护
- 新增 `frontend/src/components/chat/WorkflowTimeline.vue`：
  - 紧凑进度条，位于聊天区顶部，不污染消息列表
  - 显示：模式标签 + 步骤进度点 + 活跃 Agent + 质量分
  - 有执行计划时可展开/收起查看步骤详情
  - 流式完成后 4 秒自动收起
- `frontend/src/stores/chat.js` 移除 `addSystemNote` 调用，工作流信息不再插入聊天消息
- `ChatPanel.vue` 已集成 `WorkflowTimeline` 组件

### 成果

- 计划器输出不再静默退化，无法生成有效步骤时显式降级为 REACT
- 意图分类从硬编码改为 LLM 驱动，新增 Agent 只需在 registry 注册
- 路由、评分、降级等核心逻辑具备可回归测试基础
- 前端用户可直观看到多 Agent 执行过程，且不会污染聊天内容

---

## 阶段六：稳定性与持久化增强

### 目标

提升计划器的稳定性，并实现跨重启的状态持久化。

### 已完成

- **Planner 稳定性增强**：
  - `backend/multi_agent/graph.py` 中的 `_plan_steps` 引入了重试逻辑（2 次尝试）。
  - 改进了 Planner Prompt，要求严格的 JSON 数组格式，并自动从 `AGENT_REGISTRY` 注入可用 Agent 描述。
  - 增强了 JSON 提取逻辑，支持更复杂的 LLM 响应格式。
- **状态持久化实现**：
  - 引入 `langgraph-checkpoint-sqlite` 依赖。
  - `backend/config.py` 新增 `CHECKPOINT_DB` 配置，指定 sqlite 数据库路径。
  - `backend/memory/checkpointer.py` 将 `MemorySaver` 替换为 `SqliteSaver`。
  - 现在 Agent 的运行状态（线程、检查点）可以在服务重启后恢复。
- **自动化测试补充**：
  - 新增 `tests/test_service.py`，模拟并验证了 `MultiAgentService` 的重试、降级和 SSE 事件流逻辑。
- **前端优化**：
  - `WorkflowTimeline.vue` 的可见性逻辑调整为始终保留当前会话的执行轨迹，不再在 `done` 事件后立即隐藏。

### 成果

- 计划生成失败率进一步降低，且具备基本的重放尝试能力。
- 解决了服务重启后多 Agent 运行现场丢失的问题，为后续的断点续传和多轮深度协作打下基础。
- 核心服务链路（Service -> Graph -> SSE）具备了单元测试覆盖。

---

## 当前限制

- 质量评估逻辑（`quality_node`）目前仍较为简单，仅基于结果是否存在。
- 前端 `WorkflowTimeline` 仅展示当前最新的执行轨迹，尚未实现查看历史消息对应轨迹的功能。
- 尚未引入并行执行节点，目前多 Agent 协作仍是顺序执行。

---

## 下一阶段建议

1. 增强质量评估节点，引入更细粒度的检查（长度、格式、事实一致性）
2. 为前端增加历史会话回放时间线
3. 引入更丰富的 Agent 工具生态（RAG、代码执行等）
4. 增加多轮对话上下文压缩
