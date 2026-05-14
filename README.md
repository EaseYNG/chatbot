# ChatBot — 多 Agent 智能对话助手

基于 `FastAPI + LangGraph + DeepSeek + Vue 3` 的全栈多 Agent 对话系统，支持动态复杂度评估、多模式执行编排、JWT 认证与速率限制。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI (Python 3.11+) |
| 编排框架 | LangGraph (StateGraph DAG) |
| LLM | DeepSeek Chat API |
| Agent 框架 | LangChain (`create_agent`) |
| 数据库 | SQLite (aiosqlite) |
| 认证 | JWT (PyJWT, PBKDF2-HMAC-SHA256) |
| 前端 | Vue 3 + Vite 5 + Pinia |
| Markdown 渲染 | marked + highlight.js |
| 测试 | pytest |

---

## 项目概述

### 项目结构

```
├── backend/
│   ├── config.py                  # 集中配置
│   ├── main.py                    # uvicorn 启动入口
│   ├── agent/
│   │   ├── chatbot.py             # 旧 ChatBot 封装（仅 restore_state）
│   │   └── llm_factory.py         # DeepSeek LLM 工厂
│   ├── api/
│   │   ├── dependencies.py        # 依赖注入工厂
│   │   ├── routes.py              # 对话/会话路由
│   │   └── server.py              # FastAPI app 工厂
│   ├── auth/                      # JWT 认证模块
│   │   ├── middleware.py          # get_current_user / optional_user
│   │   ├── models.py              # 请求/响应模型
│   │   └── routes.py              # register / login / refresh
│   ├── memory/
│   │   ├── database.py            # SQLite 连接管理 + 建表
│   │   └── history_manager.py     # 对话持久化
│   ├── middleware/
│   │   └── rate_limit.py          # 用户级滑动窗口限流
│   ├── models/
│   │   └── schemas.py             # Pydantic 模型 + 输入校验
│   ├── multi_agent/               # 多 Agent 编排核心
│   │   ├── enums.py               # 阶段/模式/意图枚举
│   │   ├── state.py               # OrchestratorState + PlanStep
│   │   ├── registry.py            # Agent 注册表
│   │   ├── graph.py               # DAG 编排图
│   │   └── service.py             # SSE 流式服务层
│   └── tools/
│       ├── __init__.py            # 工具注册
│       ├── weather.py             # 天气查询
│       └── md_io.py               # Markdown 文件读写
├── frontend/
│   └── src/
│       ├── api/client.js          # SSE 客户端 + Auth 拦截
│       ├── stores/                # Pinia 状态管理
│       │   ├── auth.js            # JWT 管理 + 401 自动登出
│       │   ├── chat.js            # 对话流 + 工作流事件
│       │   └── conversations.js   # 会话 CRUD
│       ├── views/                 # Login / Register
│       ├── components/
│       │   ├── layout/            # ChatLayout
│       │   ├── chat/              # 消息列表 / 输入框 / 工作流时间线
│       │   └── sidebar/           # 会话列表
│       └── utils/markdown.js      # Markdown + 代码高亮渲染
├── tests/                         # 63 个测试用例
└── memory/                        # SQLite 数据库文件
```

---

### 架构总览

```
用户请求
    │
    ▼
┌─────────────────────────────────────────────────┐
│            FastAPI Server (uvicorn)              │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ Auth     │  │ Rate     │  │ Multi-Agent   │  │
│  │ (JWT)    │  │ Limiter  │  │ Orchestrator  │  │
│  └──────────┘  └──────────┘  └───────┬───────┘  │
└─────────────────────────────────────────────────┘
                                       │
                                       ▼
                          ┌─────────────────────┐
                          │  LangGraph DAG      │
                          │                     │
                          │  INIT → INPUT       │
                          │    → COMPLEXITY     │
                          │    → ROUTE          │
                          │    → EXECUTION      │
                          │    → OUTPUT         │
                          │    → QUALITY → END  │
                          └─────────────────────┘
                                       │
                          ┌────────────┼────────────┐
                          ▼            ▼            ▼
                    ┌────────┐ ┌──────────┐ ┌──────────┐
                    │ REACT  │ │PLAN_EXEC │ │ WORKFLOW │
                    └────────┘ └──────────┘ └──────────┘
                          │         │            │
                          ▼         ▼            ▼
                    ┌───────────────────────────────┐
                    │  4 个专业 Agent               │
                    │  general / coding / writing   │
                    │  / analysis + 3 个工具         │
                    └───────────────────────────────┘
```

### 核心特性

- **三级执行模式**：REACT（单步直接回答）、PLAN_EXECUTE（计划分解顺序执行）、WORKFLOW（跨 Agent 协作）
- **LLM 质量评估**：完整性/准确性/清晰度三维评分，< 60 分触发自动降级重试
- **流式输出**：基于 SSE 的 15 种事件类型实时推送（token、阶段、路由、Agent、工具等）
- **JWT 认证**：Access + Refresh Token 双令牌机制，Refresh Token 轮换
- **用户隔离**：对话数据按 user_id 隔离，请求级速率限制
- **前端工作流可视化**：实时展示阶段进度条、Agent 状态、质量评分

---

## 关键业务逻辑实现

### 1. 多 Agent 编排引擎

核心在 `backend/multi_agent/graph.py` 的 `MultiAgentGraph`，基于 LangGraph 的 `StateGraph` 构建。

**7 个节点 + 条件边**：

```
INIT ─→ INPUT ─→ COMPLEXITY ─→ ROUTE ─→ REACT ┬─→ OUTPUT ─→ QUALITY ─→ END
                                           ├─→ PLAN_EXECUTE ┘
                                           └─→ WORKFLOW ┘
```

每个节点接收 `OrchestratorState`（TypedDict），返回 state diff，由 LangGraph 自动合并。

**执行模式选择逻辑**：

```
                    REACT          PLAN_EXECUTE      WORKFLOW
                    (10-24)         (25-54)          (55-100)
                    ┌──────┐       ┌──────────┐     ┌──────────┐
复杂性评分 ──────── │ 单步 │ ────→ │ 分解步骤 │ ──→ │ 多Agent  │
                    │ 直接回答 │    │ 顺序执行 │    │ 协作执行  │
                    └──────┘       └──────────┘     └──────────┘
```

### 2. 上下文管理

- 对话历史以 JSON 数组存储在 SQLite `conversations.messages` 列
- 每次请求从 DB 读取全量历史，取最近 10 条拼成文本注入 System Prompt
- 多步骤模式下，WORKFLOW 模式通过 `prior_outputs` 在步骤间传递上下文
- 执行完成后将新消息（human + ai）追加回 SQLite

**注意**：当前历史以纯文本而非结构化消息数组传递给 LLM，属于已知可优化项。

### 3. 质量评估与降级重试

```python
quality_node → LLM 评分（completeness/accuracy/clarity）
    ↓
score < 60 → service 层 _downgrade_mode()
    ↓
WORKFLOW → PLAN_EXECUTE → REACT → 仍失败则返回最终结果
    ↓
score >= 60 → 保存历史，返回 done 事件
```

### 4. JWT 认证

| 端点 | 功能 | Token 类型 |
|------|------|-----------|
| `POST /api/auth/register` | 注册 | 返回 access + refresh |
| `POST /api/auth/login` | 登录 | 返回 access + refresh |
| `POST /api/auth/refresh` | 刷新令牌 | 旧 refresh 被轮换 |
| `GET /api/auth/me` | 当前用户信息 | 需 access token |

- Access Token 有效期 30 分钟，Refresh Token 7 天
- 密码使用 PBKDF2-HMAC-SHA256（10 万次迭代）加盐哈希
- Refresh Token 使用哈希值存储，支持轮换和撤销
- Token 过期自动触发前端登出

### 5. 专业 Agent 注册表

`backend/multi_agent/registry.py` 定义了 4 个 Agent：

| Agent | 领域 | 可用工具 |
|-------|------|---------|
| general | 通用问答 | get_weather, read_md |
| coding | 编程与架构 | read_md, to_md |
| writing | 内容写作 | read_md, to_md |
| analysis | 分析与评估 | read_md |

Agent 实例使用 `_agent_cache`（module-level dict）按 `(name, streaming, tools)` 缓存，避免重复编译。

---

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- DeepSeek API Key

### 配置

在项目根目录创建 `.env`：

```env
DEEPSEEK_API_KEY=sk-your-key-here
JWT_SECRET=your-jwt-secret-change-me
```

### 启动后端

```bash
pip install -r requirements.txt
python -m backend.main
```

服务启动在 `http://localhost:8000`，API 文档在 `http://localhost:8000/docs`。

### 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端地址 `http://localhost:5173`，通过 Vite 代理转发 `/api` 到后端。

### 测试

```bash
pytest tests/ -v    # 63 个测试用例
```

---

## API 文档

### 认证

```
POST /api/auth/register   { username, password } → { access_token, refresh_token }
POST /api/auth/login      { username, password } → { access_token, refresh_token }
POST /api/auth/refresh    { refresh_token }      → { access_token, refresh_token }
GET  /api/auth/me         [Auth]                 → { id, username, created_at }
```

### 对话（需 Bearer Token）

```
POST   /api/chat              → SSE stream (15 种事件类型)
GET    /api/conversations     → 会话列表
GET    /api/conversations/{id} → 会话详情（含消息）
DELETE /api/conversations/{id} → 删除会话
```

### 速率限制

基于用户的滑动窗口算法，默认每分钟 30 次，超限返回 `429 Too Many Requests`。

---

## License

MIT
