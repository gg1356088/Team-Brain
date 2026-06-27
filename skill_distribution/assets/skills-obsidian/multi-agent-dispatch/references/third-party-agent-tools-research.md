# 第三方 Agent 监督/调度工具调研

调研时间：2026-06-08

## 调研结果

### 1. obra/superpowers ⭐221k
- **定位：** 编码流程框架（写计划→写代码→TDD→review）
- **适合：** Claude Code / Codex / Cursor 的插件
- **不适合我们：** 管"怎么写代码"，不管"任务派出去后谁盯着"
- **结论：** 不装

### 2. Ibrahim-3d/orchestrator-supaconductor ⭐357
- **定位：** Claude Code 的"董事会"插件，自动拆任务并行执行
- **不适合我们：** 给 Claude Code 命令行内部用，不是给 Hermes 调度的
- **结论：** 不装

### 3. 23blocks/ai-maestro ⭐701
- **定位：** Agent 编排系统 + Skills 注册表 + Web Dashboard
- **优点：** 多 Agent 编排、Agent 间通信、Web UI 看板
- **结论：** 未来如果需要 Web Dashboard 可考虑（分阶段：先用自研 supervisor.py）

### 4. larksuite/cli ⭐13673（飞书官方 CLI）
- **定位：** 飞书官方 CLI，200+ 命令，26 个 AI Agent Skills
- **覆盖：** 消息、文档、日历、邮件、任务等 18 个业务域
- **安装：** `npx @larksuite/cli@latest install` 或 `npm install -g @larksuite/cli`
- **npm install -g 权限问题 workaround：**
  ```bash
  mkdir -p ~/.npm-global
  npm config set prefix ~/.npm-global
  npm install -g @larksuite/cli
  export PATH="$HOME/.npm-global/bin:$PATH"
  ```
- **AI Skill 包括：** lark-im（消息）、lark-doc（文档）、lark-task（任务）
- **适合场景：** 飞书推送通知、文档自动化、任务管理
- **结论：** 后续可集成到监督系统做飞书推送

### 搜索能力教训
- **教训：** `curl GitHub API search` 只能搜 repo 名和 description
- **关键案例：** 搜索 `feishu cli` 找不到 `larksuite/cli`，因为 repo 名是 `lark` 不是 `feishu`
- **正确做法：** 优先使用 `web_search` 或 MCP 搜索工具，不要自己 curl GitHub API
- **原因：** 搜索引擎能处理中文别名、变体名；GitHub API 只能精确匹配 repo name + description