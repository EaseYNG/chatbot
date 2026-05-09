# LangChain Chatbot

基于 LangChain + LangGraph + DeepSeek 的全栈智能对话助手，支持流式输出与对话记忆持久化。

## 项目结构

```
├── backend/                    # Python 后端
│   ├── config.py               # 集中配置（API Key、路径、常量）
│   ├── models/schemas.py       # Pydantic 请求/响应模型
│   ├── tools/                  # 工具注册中心（可扩展 RAG、Skill）
│   │   ├── weather.py          # 天气查询工具
│   │   └── md_io.py            # Markdown 文件读写工具
│   ├── memory/                 # 对话记忆模块
│   │   ├── history_manager.py  # JSON 文件持久化管理器
│   │   └── checkpointer.py     # LangGraph MemorySaver 封装
│   ├── agent/                  # Agent 核心
│   │   ├── chatbot.py          # ChatBot 类（同步/异步双模式）
│   │   └── streaming.py        # SSE 流式事件转换器
│   ├── api/                    # FastAPI 接口层
│   │   ├── dependencies.py     # 依赖注入工厂
│   │   ├── routes.py           # 路由处理函数
│   │   └── server.py           # FastAPI app 工厂 + CORS
│   ├── cli.py                  # CLI 终端模式
│   └── main.py                 # uvicorn 启动入口
├── memory/                     # 对话历史 JSON 存储
├── files/                      # MdIO 文件缓冲区
├── frontend/                   # Vue3 前端 SPA
│   └── src/
│       ├── api/client.js       # SSE 流式客户端
│       ├── stores/             # Pinia 状态管理
│       └── components/         # Vue 组件
├── .env                        # 环境变量（需自行配置 API Key）
└── requirements.txt            # Python 依赖
```

## 快速开始

### 1. 配置 API Key

编辑 `.env` 文件，填入你的 DeepSeek API Key：

```
DEEPSEEK_API_KEY=sk-your-key-here
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动后端

```bash
python -m backend.main
```

FastAPI 服务将在 `http://localhost:8000` 启动，自动生成 API 文档见 `http://localhost:8000/docs`。

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端将在 `http://localhost:5173` 启动，通过 Vite 代理自动转发 `/api` 请求到后端。

### 5. CLI 模式（可选）

```bash
python backend/cli.py
```

## API 文档

### POST /api/chat

流式对话接口（Server-Sent Events）。

**请求体：**
```json
{
  "thread_id": null,
  "message": "你好",
  "system_message": "You are a helpful assistant."
}
```

- `thread_id`：`null` 表示创建新对话；传入已有 ID 则继续对话
- `message`：用户消息内容
- `system_message`：系统提示词（可选，有默认值）

**SSE 事件类型：**

| 事件 | 数据结构 | 说明 |
|------|----------|------|
| `token` | `{"content": "Hello"}` | LLM 逐 token 输出 |
| `tool_start` | `{"tool_name": "get_weather", "tool_input": {"city": "北京"}}` | 工具调用开始 |
| `tool_end` | `{"tool_name": "get_weather", "tool_output": "sunny"}` | 工具调用完成 |
| `done` | `{"thread_id": 1}` | 对话结束，返回 thread_id |
| `error` | `{"message": "..."}` | 错误信息 |

### GET /api/conversations

获取所有对话列表。

**响应：**
```json
[
  {
    "thread_id": 1,
    "title": "你好",
    "created_at": "2026-05-08T...",
    "updated_at": "2026-05-08T...",
    "message_count": 4
  }
]
```

### GET /api/conversations/{id}

获取单条对话完整消息（同时恢复 Agent 检查点状态）。

### DELETE /api/conversations/{id}

删除指定对话。

## 扩展指南

### 添加新工具

在 `backend/tools/` 下创建新文件，然后在 `__init__.py` 的 `get_all_tools()` 中注册：

```python
from backend.tools.my_tool import my_function

def get_all_tools():
    return [MdIO.to_md, MdIO.read_md, get_weather, my_function]
```

### 添加 RAG 功能

在 `backend/tools/` 下新增 RAG 检索工具，注入向量数据库查询能力即可。

## 技术栈

- **后端**：Python 3.11+ / FastAPI / LangChain / LangGraph / DeepSeek
- **前端**：Vue 3 / Vite 5 / Pinia
- **持久化**：JSON 文件 + LangGraph MemorySaver（可切换 SqliteSaver）
