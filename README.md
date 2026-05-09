# LangChain Chatbot

基于 `FastAPI + LangChain + LangGraph + DeepSeek + Vue 3` 的全栈智能对话助手，当前已从单 Agent 架构开始演进为“可观测的多 Agent 工作流”版本。

## 当前状态

当前仓库已经具备以下能力：

- 单一 `/api/chat` 入口
- 自动复杂度评估与执行模式路由
- 三种执行模式：`REACT` / `PLAN_EXECUTE` / `WORKFLOW`
- 4 类专业 Agent：`general` / `coding` / `writing` / `analysis`
- SSE 流式返回过程事件与最终回答
- 对话历史持久化，并记录多 Agent 元信息

多 Agent 实施方案文档见 `files/multi-agent.md`，阶段成果记录见 `files/multi-agent-progress.md`。

## 项目结构

```text
├── backend/
│   ├── config.py                  # 集中配置（API Key、路径、常量）
│   ├── main.py                    # uvicorn 启动入口
│   ├── cli.py                     # 旧 CLI 模式（仍可用）
│   ├── agent/
│   │   ├── chatbot.py             # 旧单 Agent 封装
│   │   ├── llm_factory.py         # 统一 DeepSeek LLM 工厂
│   │   └── streaming.py           # 旧 SSE 转换器
│   ├── api/
│   │   ├── dependencies.py        # 依赖注入工厂
│   │   ├── routes.py              # FastAPI 路由
│   │   └── server.py              # FastAPI app 工厂 + CORS
│   ├── memory/
│   │   ├── history_manager.py     # 对话与元信息持久化
│   │   └── checkpointer.py        # LangGraph MemorySaver 封装
│   ├── models/
│   │   └── schemas.py             # 请求/响应模型
│   ├── multi_agent/
│   │   ├── __init__.py
│   │   ├── enums.py               # 阶段/模式/意图枚举
│   │   ├── state.py               # OrchestratorState
│   │   ├── registry.py            # 专业 Agent 注册表
│   │   ├── graph.py               # 多 Agent Orchestrator 图
│   │   └── service.py             # 多 Agent 服务层 + SSE 输出
│   └── tools/
│       ├── __init__.py            # 工具注册与按名称筛选
│       ├── weather.py             # 天气查询工具
│       └── md_io.py               # Markdown 文件读写工具
├── frontend/
│   └── src/
│       ├── api/client.js          # SSE 流式客户端
│       ├── stores/chat.js         # 聊天状态与工作流事件展示
│       ├── stores/conversations.js
│       └── components/
├── files/                         # Markdown 文件与设计文档
├── memory/                        # 对话历史 JSON 存储
├── .env                           # 环境变量（需自行创建）
└── requirements.txt               # Python 依赖
```

## 快速开始

### 1. 配置 API Key

在项目根目录创建 `.env`：

```env
DEEPSEEK_API_KEY=sk-your-key-here
```

### 2. 安装后端依赖

```bash
pip install -r requirements.txt
```

### 3. 启动后端

```bash
python -m backend.main
```

服务默认启动在 `http://localhost:8000`，API 文档在 `http://localhost:8000/docs`。

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认地址为 `http://localhost:5173`，通过 Vite 代理自动转发 `/api` 到后端。

### 5. CLI 模式（可选）

```bash
python backend/cli.py
```

说明：CLI 当前仍走旧单 Agent 封装，Web API 已接入新的多 Agent 服务层。

## 多 Agent 执行模式

### `REACT`

- 用于简单问答和轻量工具调用
- 单次调用一个专业 Agent 直接给出结果

### `PLAN_EXECUTE`

- 用于多步骤但单领域主导的任务
- 先生成计划，再按步骤顺序执行

### `WORKFLOW`

- 用于跨领域协作任务
- 由 Orchestrator 生成多 Agent 步骤并汇总输出

## API 文档

### `POST /api/chat`

流式对话接口，返回 `text/event-stream`。

**请求体：**

```json
{
  "thread_id": null,
  "message": "请给我一个多 Agent 实现方案",
  "system_message": "You are a helpful assistant.",
  "mode_hint": null,
  "agent_hint": null,
  "return_trace": true
}
```

字段说明：

- `thread_id`：`null` 表示创建新会话
- `message`：用户输入
- `system_message`：系统提示词
- `mode_hint`：可选，支持 `REACT` / `PLAN_EXECUTE` / `WORKFLOW`
- `agent_hint`：可选，支持 `general` / `coding` / `writing` / `analysis`
- `return_trace`：是否返回阶段事件

**SSE 事件类型：**

| 事件 | 数据结构示例 | 说明 |
|------|--------------|------|
| `stage_start` | `{"stage":"INPUT","label":"输入分析"}` | 某阶段开始 |
| `stage_end` | `{"stage":"INPUT","label":"输入分析"}` | 某阶段结束 |
| `route` | `{"mode":"PLAN_EXECUTE","agent":"coding","score":35}` | 路由结果 |
| `plan` | `{"steps":[...]}` | 计划或工作流步骤 |
| `step_start` | `{"step_id":"s1","title":"Analyze","agent":"coding"}` | 步骤开始 |
| `step_end` | `{"step_id":"s1","title":"Analyze","agent":"coding"}` | 步骤结束 |
| `agent_start` | `{"agent":"coding","label":"Coding Agent"}` | 专业 Agent 开始 |
| `agent_end` | `{"agent":"coding","label":"Coding Agent"}` | 专业 Agent 结束 |
| `quality` | `{"score":85,"passed":true}` | 质量评估 |
| `warning` | `{"message":"..."}` | 降级或重试提示 |
| `token` | `{"content":"..."}` | 最终回答的流式片段 |
| `done` | `{"thread_id":1,"mode":"PLAN_EXECUTE"}` | 本次执行结束 |
| `error` | `{"message":"..."}` | 错误信息 |

### `GET /api/conversations`

获取会话列表。

### `GET /api/conversations/{id}`

获取单条会话详情，当前返回：

- `messages`
- `meta`

其中 `meta` 会记录：

- `run_id`
- `execution_mode`
- `selected_agent`
- `quality_score`
- `intent`
- `plan_steps`
- `trace`

### `DELETE /api/conversations/{id}`

删除指定会话。

## 当前实现进度

### 阶段一：多 Agent 基础设施

已完成：

- 抽出统一 LLM 工厂 `backend/agent/llm_factory.py`
- 新增 `backend/multi_agent/` 目录
- 新增状态模型、枚举、Agent 注册表
- 工具层支持按名称筛选

### 阶段二：Orchestrator 路由与执行

已完成：

- 多 Agent 图 `backend/multi_agent/graph.py`
- 输入分析、复杂度评估、执行模式路由
- `REACT` / `PLAN_EXECUTE` / `WORKFLOW` 三种模式
- 最小质量评估与降级重试

### 阶段三：SSE 与前端兼容

已完成：

- `/api/chat` 已切换到 `MultiAgentService`
- SSE 新增阶段、计划、Agent、质量事件
- 前端 `chat store` 已能展示基本过程提示

### 阶段四：持久化与文档

已完成：

- 对话历史增加 `meta`
- 记录执行模式、质量分、计划步骤、事件轨迹
- 更新 `README.md`
- 新增阶段成果记录文档

## 扩展指南

### 添加新工具

在 `backend/tools/` 下新增工具后，注册到 `get_all_tools()` 中；如果要限制给特定 Agent，再在 `backend/multi_agent/registry.py` 中配置工具白名单。

### 添加新专业 Agent

在 `backend/multi_agent/registry.py` 中新增条目，至少配置：

- `label`
- `intent`
- `tools`
- `system_prompt`

### 下一步建议

建议优先继续以下工作：

- 将 `workflow` 计划器改为严格 schema 校验
- 为前端增加专门的工作流时间线组件
- 引入可持久化的 checkpointer
- 为多 Agent 路由与降级增加自动化测试

## 技术栈

- 后端：Python 3.11+ / FastAPI / LangChain / LangGraph / DeepSeek
- 前端：Vue 3 / Vite 5 / Pinia
- 持久化：JSON 文件 + LangGraph MemorySaver
