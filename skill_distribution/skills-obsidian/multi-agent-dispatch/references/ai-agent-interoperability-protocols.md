# AI 智能体互通互用协议深度分析

> 2026-06-10 整理

## A2A（Agent-to-Agent Protocol）

**Google 主导，Linux Foundation 托管，24.2k ⭐，Apache 2.0，v1.0 已发布**

**GitHub：** https://github.com/a2aproject/A2A
**文档：** https://a2a-protocol.org
**Python SDK：** `pip install a2a-sdk`
**JS SDK：** `npm install @a2a-js/sdk`

### 核心概念

| 概念 | 说明 |
|------|------|
| Agent Card | 智能体的"名片"：声明有哪些技能（Skills）、支持的格式、连接地址 |
| Skill | 一个具体能做的事（如"翻译"、"查天气"），包含描述、输入/输出 schema |
| Task | 带完整生命周期的任务：created → working → completed → terminal |
| JSON-RPC 2.0 over HTTP(S) | 通信协议标准 |

### 交互模式

- **同步请求/响应** — 发任务 → 等结果
- **SSE 流式推送** — 运行中实时返回进度
- **异步通知** — 完成后主动推回结果

### 支持的数据类型

文本、文件、结构化 JSON 数据。支持认证、OpenTelemetry 追踪、SQL 数据库后端。

### SDK 列表

- Python: `pip install a2a-sdk`
- JS: `npm install @a2a-js/sdk`
- Go: `go get github.com/a2aproject/a2a-go`
- Java: Maven
- .NET: `dotnet add package A2A`
- Rust: `cargo add a2a-lf`

### 示例代码位置

`a2a-samples/samples/python/agents/helloworld/` — 一个完整的 hello world A2A server + client 示例。

```bash
git clone https://github.com/a2aproject/a2a-samples.git
cd a2a-samples/samples/python/agents/helloworld
uv run .  # server
# 另一终端：
cd a2a-samples/samples/python/agents/helloworld
uv run test_client.py  # client
```

### 与你当前方案的映射

**multi-agent-dispatch = 手动 A2A**

当前模式：
```
Hermes(调度器) → 拆任务 → Claude Code(执行者) → 监控 → 验收 → 汇报
     ↑_______________ 人工中间路由 ________________↓
```

A2A 成熟后：
```
Hermes(A2A Server) ←→ A2A 协议 ←→ Claude Code(A2A Server)
     ↑                        ↑
  MCP 连 Obsidian         MCP 连代码库
```

Hermes 通过 A2A 发现 Claude Code 的 Agent Card，知道它能做什么，直接派任务。不再需要 supervisor.py 做中间调度。

### 成熟度评估

- **协议：** ✅ v1.0 已稳定
- **SDK：** ✅ 全语言支持
- **生态：** ⚠️ 主流 AI 工具（Claude Code、Cursor）尚未原生支持 A2A
- **可用场景：** Google ADK 已内置 A2A server 支持
- **预期：** 属于"协议已定，生态发育"阶段，预计 6-12 个月内主流工具跟进

## MCP（Model Context Protocol）

**Anthropic 创建，MIT 开源，事实标准**

**GitHub：** https://github.com/modelcontextprotocol/modelcontextprotocol
**文档：** https://modelcontextprotocol.io

### 核心概念

| 概念 | 说明 |
|------|------|
| Server | 提供工具/数据的程序（如 Obsidian MCP） |
| Client | 调用工具的 AI 智能体（如 Hermes） |
| Tools | 具体能做的事（search, read_file, write_note） |
| Resources | 可读数据（文件、配置） |
| Prompts | 预定义消息模板 |

### 通信

- JSON-RPC 2.0
- stdio（本地进程）或 HTTP/SSE（远程）

### 与你当前方案的映射

**已经在用。** 你的 Obsidian 40+ MCP 工具、CodeGraph MCP 都是基于此协议。
- Hermes = MCP Client
- `obsidian-cli-mcp` = MCP Server

## A2A vs MCP 对比

| 维度 | MCP | A2A |
|------|-----|-----|
| 解决的问题 | AI ↔ 工具 | AI ↔ AI |
| 创建方 | Anthropic | Google |
| 许可证 | MIT | Apache 2.0 |
| 协议 | JSON-RPC 2.0 | JSON-RPC 2.0 |
| 传输 | stdio, HTTP/SSE | HTTP(S) |
| 核心对象 | Tools, Resources, Prompts | Agent Card, Skill, Task |
| 成熟度 | ✅ 广泛使用 | ⚠️ 协议稳定，生态发育 |
| 典型场景 | 让 AI 读文件、操作工具 | 让 AI 跟另一个 AI 协作 |

## 参考链接

- A2A 官方文档：https://a2a-protocol.org
- A2A Spec v1.0：https://a2a-protocol.org/v1.0.0/specification/
- A2A Python SDK：https://github.com/a2aproject/a2a-python
- A2A Samples：https://github.com/a2aproject/a2a-samples
- A2A DeepLearning.AI 课程：https://goo.gle/dlai-a2a
- MCP 文档：https://modelcontextprotocol.io