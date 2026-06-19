---
name: multi-agent-dispatch
description: 多AI调度：拆解任务→派 Claude Code CLI 或 Codex CLI 执行→自动监控进度→自动验收→汇报。内置 supervisor.py 监督系统（任务管理+输出监控），自动创建任务、更新状态、监控输出（2分钟卡住自动重试）、验收、飞书集成预留。支持 Obsidian 共享知识库作为多智能体上下文枢纽。
version: "2.1.0"
---

# Multi-Agent Dispatch v1.0 — 带自动监督的调度
# Multi-Agent Dispatch v2.0 — 带自动监督的多智能体调度

## 架构（v3 — 三层互补）

```
┌──────────────────────────────────────┐
│  协调层 — supervisor.py              │
│  supervisor.py loop "任务描述"       │
│  supervisor.py dispatch "任务" claude│
│  supervisor.py status/list           │
└──────────┬───────────────────────────┘
           │ 调用
┌──────────▼───────────────────────────┐
│  执行层 — loop_dispatch.py           │
│  将自然语言任务转成结构化 Prompt     │
│  下发给 Claude Code / Codex          │
└──────────┬───────────────────────────┘
           │ 下发给
     ┌─────┴─────┐
     ▼           ▼
  Claude Code   Codex
  (claude -p)   (codex exec -s ws-write)
     
┌──────────┐
│  通知层 — loop_monitor.py          │
│  loop_monitor.py check/start       │
│  完成后推飞书                       │
└──────────┘
```

### 三层职责划分

- **协调层（supervisor.py）**：分配谁干什么、验收结果、汇报状态。
- **执行层（loop_dispatch.py）**：把自然语言任务转成结构化 Prompt，下发给 AI 子代理。
- **通知层（loop_monitor.py）**：持续监控任务状态，完成后推送到飞书。

### ⚠️ LOOP 机制真相（2026-06-18 修正）

`/goal`、`/loop`、`/schedule` **在 Claude Code 和 Codex 中都不存在**。
Boris Cherny 的推文是关于编程理念，不是 CLI 命令。
实际做法：用结构化自然语言 Prompt + 外部调度器实现循环效果。
详见 `references/loop-mechanism.md`。

## 监督系统（v2 — 独立路径）

**脚本位置**: `~/supervisor/supervisor.py`

### 用法

```bash
python3 ~/supervisor/supervisor.py add "任务描述" --worker claude --timeout 600
python3 ~/supervisor/supervisor.py add "任务描述" --worker codex
python3 ~/supervisor/supervisor.py start          # 启动调度（默认并行）
python3 ~/supervisor/supervisor.py start --no-parallel  # 串行
python3 ~/supervisor/supervisor.py status
python3 ~/supervisor/supervisor.py results
python3 ~/supervisor/supervisor.py clear
```

### Worker 配置

| Worker | 路径 | 用途 |
|--------|------|------|
| claude | `claude` (全局命令) | 编码、研究、分析 |
| codex | `/Applications/Codex.app/Contents/Resources/codex` | 编码、测试、调试 |

### 调度逻辑

1. 分配任务 → 各 worker 并行执行
2. 2 分钟无输出 = 卡住，重启
3. 超时重试最多 3 次
4. 按任务类型分级验收
5. 汇总结果，通知用户

### 状态文件

- `~/supervisor/supervisor_workspace/tasks.json` — 任务状态
- `~/supervisor/supervisor_workspace/logs/` — 日志
- `~/supervisor/supervisor_workspace/results/` — 结果

### 飞书触发

`~/supervisor/feishu_trigger.py` — 解析飞书消息并转发给 supervisor。需要配合飞书 WebSocket 事件监听使用。

### Obsidian 作为共享知识库

所有智能体（Hermes、Claude Code、Codex）通过 `obsidian` 或 `knowledge-base` 技能读取 Markdown 笔记，wikilinks 关联上下文。关键笔记：
- `多AI总调度/监督系统.md` — 系统架构和配置（示例路径，实际路径按用户 vault 结构）
- `技能工具链清单.md` — 所有技能和工具索引
- `AI智能体互通协议 A2A与MCP.md` — 协议深度分析

> 💡 笔记路径按用户实际 vault 结构而定，不是固定值。分发时替换为实际路径或使用变量。

## 调度流程（标准化 v3.0 — LOOP 集成）

### LOOP 机制（2026-06-16 新增）

在 supervisor.py 基础上加装 LOOP 自循环引擎：

```bash
# 最简方式 — 自动走 /goal
cd ~/HermesPet_Workspace && python3 supervisor.py dispatch "任务描述" claude

# 完整方式
python3 supervisor.py loop "任务描述" --worker claude      # /goal
python3 supervisor.py loop "任务描述" --loop --interval 5m # /loop
python3 supervisor.py loop "任务描述" --schedule --cron "0 9 * * *"  # /schedule

# 监控 + 飞书通知
python3 loop_monitor.py start
python3 loop_monitor.py check  # 单次检查
```

文件位置: `~/HermesPet_Workspace/loop_dispatch.py`, `loop_monitor.py`
详情: [[LOOP调度系统]] (Obsidian)

### 第零步：载入精简规则

调度 Claude Code / Codex 时，**必须启用 `caveman` 技能**，将所有 AI→AI 通信精简到极致：
- 去掉客套、解释、过渡词
- 指令放最前，引用放最后
- 预期节省 70-85% token

详见 [[多AI总调度/多智能体通信精简规则]]

### LOOP 机制真相（2026-06-18 修正）

`/goal`、`/loop`、`/schedule` 不存在于 Claude Code 或 Codex。
实际做法：用结构化自然语言 Prompt 替代。

```bash
# 最简方式 — 自动走结构化 Prompt
cd ~/HermesPet_Workspace && python3 supervisor.py dispatch "任务描述" claude

# 完整方式
python3 supervisor.py loop "任务描述" --worker claude      # 结构化 Prompt
python3 supervisor.py loop "任务描述" --loop --interval 5m # 外部定时
python3 supervisor.py loop "任务描述" --schedule --cron "0 9 * * *"  # 用 cronjob

# 监控 + 飞书通知
python3 loop_monitor.py start
python3 loop_monitor.py check  # 单次检查
```

## 任务类型与验收规则模板

| 类型 | timeout | 验收方式 |
|------|---------|---------|
| 研究报告 | 30min | 文件存在 + 含"结论"/"总结"/"分析" |
| 代码/脚本 | 20min | 文件存在 + 大小 > 1KB |
| 数据分析 | 30min | 文件存在 + 含"结果"/"统计" |
| 简单查询 | 10min | 文件存在或输出非空 |
| 文件整理 | 15min | 文件数 > 0 |
| 发票处理 | 20min | 每笔需人工复核（AI 分类错误率高） |

## Pitfalls

### 调度类
- **你是监督者，不是工人** — 当用户让你"检查"、"审核"、"审查"某个东西时，你的角色是监督者（supervisor）：派 Claude Code 和 Codex 去检查，拿到报告后汇总汇报给用户。**不要自己去读文件、自己去修代码、自己去干活**。你的工作是：拆解任务 → 派 agent → 拿到结果 → 验收 → 汇报。这个纪律从 2026-06-18 开始严格执行。
- **每次会话先查 Obsidian** — Obsidian 是知识库大脑。重要知识（多AI调度、A2A协议、工具链等）都存 Obsidian，持久记忆只存关键词索引。会话启动时必须搜索 Obsidian 回忆，不能等用户提醒。
- **搜索技能不存在的处理** — `hermes skills search` 超时时，先 `find ~/.hermes/skills/ -iname "*keyword*"` 搜本地文件系统，再搜 GitHub (`curl api.github.com/search/repositories`)。三层搜索都找不到才说"没有"。用户说"装过"的东西大概率在，只是名字/路径变了。
- **Claude Code + Codex 并行执行** — 两个 worker 同时跑，不是串行。长任务互相干扰时改用 `--no-parallel` 串行。
- **Cron 任务写入 Obsidian 可能失败** — cron 在独立 session 运行，Obsidian MCP 的 vault 可能枚举不到。Cron 任务应先存本地（如 `~/HermesPet_Workspace/`），再尝试 Obsidian MCP。Obsidian 失败不应阻塞任务完成。详见 `references/cron-obsidian-access.md`。
- **汇报必须用中文** — 用户是中文版飞书，所有回复必须纯中文。工具/CLI 的英文输出要在飞书推送前翻译成中文，用户不应看到中英混杂。
- **不要问用户"你要不要我执行？"** — 列出"可立即执行的操作"后直接执行，只在有破坏性风险或真正需要用户确认时才停下来问。

### LOOP/Prompt 关键坑点（2026-06-18 新增）
- **`/goal` `/loop` `/schedule` 不存在** — 这三个命令在 Claude Code 和 Codex 中都没有。不要在任何 Prompt 中使用它们。用结构化自然语言 Prompt 替代。详见 `references/loop-mechanism.md`。
- **Claude Code timeout 至少 120s** — 之前设 10s 导致 AI 没写完就断。短 timeout 是最大隐形杀手。
- **Codex 必须用 `codex exec -s workspace-write`** — 不加 `-s workspace-write` 无法写入文件。
- **不要在 Prompt 里加 `/goal` 前缀** — 会被当作普通文本处理，浪费 token 还可能误导 AI。

### Claude Code 子进程常见问题

**1. `Insufficient Balance`（402 错误）**
- 原因：Anthropic API 账户余额不足
- 解决：充值 API key 余额，或切换到其他 provider/model

**2. `web_search` 工具不可用**
- 原因：`web_search` 是 Hermes 工具，Claude Code 子进程没有
- 解决：用 `curl` 或 `browser_navigate` 代替

**3. Claude Code 没有联网能力**
- 原因：`WebSearch`/`WebFetch` 权限需要用户手动批准
- 解决：在 `~/.claude/settings.json` 中添加 `web_fetch` 和 `web_search` 到 `permissions.allow`

**4. `Insufficient Balance`（402 错误）**
- 现象：`claude -p` 返回 `{"error":{"message":"Insufficient Balance","code":"invalid_request_error"}}`
- 原因：Anthropic API 账户余额不足，**不是 Hermes bug**
- 解决：充值 API key 余额，或切换到其他 provider/model

**5. Claude Code 输出被安全扫描拦截**
- 现象：`claude -p` 调用被阻断，报错 `Security scan — Non-ASCII characters in hostname`
- 原因：Hermes 安全扫描检测到 prompt 中包含非 ASCII 字符（如中文）在 URL/hostname 附近
- 解决：prompt 中不要混用英文 URL 和中文字符

### 搜索能力警告

**不要用 `curl GitHub API` 搜索 repo！** 它只能匹配 repo name 和 description，搜索不到 README 内容、tags、中文别名。

- **错误做法：** `curl "https://api.github.com/search/repositories?q=feishu+cli"` → 搜不到 `larksuite/cli`（因为 repo 名是 `lark` 不是 `feishu`）
- **正确做法：** 使用 `web_search` 或 MCP 搜索工具
- **关键教训：** 同一个东西可能叫不同名字（飞书 → Lark，中文 → 英文），搜索引擎能处理变体，GitHub API 不能
- 详见 `references/third-party-agent-tools-research.md`

### 发票自动化工作流交付模式

处理发票自动化类项目时的标准交付流程：

1. **脚本 + 业务规则一体化** — 所有脚本（`invoice_workflow.py`, `invoice_recognize.py` 等）必须在顶部包含完整业务规则文档：分类规则、别名映射表、Pitfalls 字典、版本号。不是"脚本逻辑里隐含"，而是"文档化在脚本头部"。
2. **Obsidian 导出** — 把 Obsidian 里的工作流笔记导出为标准 `.md` 文件放到项目根目录，不只留在 Obsidian 里。
3. **双 Agent 审计** — 脚本完成后，必须同时派 Claude Code + Codex 审查，对照 Obsidian 源文档验证业务规则是否完整、是否有 bug。
4. **修复后二次验证** — 审计发现的 bug（如重复 key、MIME 类型硬编码、版本号不一致、日期硬编码）修完后，跑一遍 `python3 -c "import py_compile; py_compile.compile(...)"` 确认语法正确，再跑 `report` 命令确认功能正常。

### 发票处理特殊坑点（详见 references/invoice-pitfalls.md）

发票识别 AI 自动分类准确率极低，必须人工复核：
- Wave Team = Wave Financial Inc.（Stripe 商家名）
- LSCO 分类需人工判断（Shipping-Fee vs Software）
- Filing ID 反查的公司名不放入文件名
- 政府收据收款方为政府机构，付款方为实际付款人
- 律所自开发票不参与客户发票流程
- 详见 `references/invoice-pitfalls.md`

## 脚本位置

> ⚠️ 以下为默认位置，可通过环境变量或 config.json 覆盖：
> - `HERMES_WORKSPACE` → supervisor.py 和 loop_dispatch.py 所在目录
> - `SUPERVISOR_WORKSPACE` → supervisor_workspace 目录

主监督系统: `~/HermesPet_Workspace/supervisor.py`（v3，含 LOOP 集成）
飞书触发器: `~/HermesPet_Workspace/supervisor/feishu_command_handler.py`
LOOP 调度器: `~/HermesPet_Workspace/loop_dispatch.py`
LOOP 监控器: `~/HermesPet_Workspace/loop_monitor.py`
LOOP 任务目录: `~/HermesPet_Workspace/loop_dispatch/tasks/`

## 浏览器自动化要点

（保持不变）

## 浏览器自动化要点

浏览器工具（`browser_navigate` + `browser_type`/`browser_click`/`browser_snapshot`）适合简单表单和页面操作，但有明确局限：

- **Google/Gmail/Outlook 等大厂页面**：通常有 bot 检测（reCAPTCHA、行为分析），自动化会被拦截（"此浏览器或应用可能不安全"）。不要用浏览器工具填 Google 表单或登录 Google 账号，大概率被拦。
- **简单表单**（非大厂）：`browser_snapshot` 通常够用，直接用 ref ID 定位元素。
- **动态页面/复杂 UI**：`browser_snapshot` 可能漏掉动态渲染的元素或无法获取语义。**解决方案：先 `browser_snapshot` 拿元素，再 `browser_vision` 截图确认页面结构和元素位置**。视觉辅助能解决 snapshot 拿不到的问题。
- **截图路径**：`browser_vision` 返回 `screenshot_path`，可直接用于视觉分析或存档。
- **不要假设页面稳定**：大厂页面经常改版，定位策略需要验证。

## AI 智能体互通互用协议

**多AI调度的演进路径：当前 → A2A 成熟**

**当前状态（本 skill 实现的模式）：** Hermes 作为中间调度器，通过 delegate_task 或 claude CLI 派任务给 Claude Code，自行监控、验收、汇报。本质上是"人工 A2A"——人（或 Hermes）在中间当路由器。

**A2A 协议（Agent-to-Agent）：** Google 主导，Linux Foundation 托管，24.2k ⭐，v1.0 已发布。
- Agent Card = 智能体名片（声明技能、连接地址）
- Skill = 具体能做的事
- Task = 带完整生命周期的任务对象（created → working → completed → terminal）
- 通信：JSON-RPC 2.0 over HTTP(S)
- SDK：Python/JS/Go/Java/.NET/Rust
- 安装：`pip install a2a-sdk`
- 成熟后：Hermes 和 Claude Code 各做 A2A server，直接对话，不需要中间调度层

**MCP 协议（Model Context Protocol）：** Anthropic 创建，MIT 开源，事实标准。
- Server = 提供工具/数据的程序（如 Obsidian MCP）
- Client = 调用工具的 AI 智能体（如 Hermes）
- 通信：JSON-RPC 2.0，支持 stdio 和 HTTP/SSE
- 你已经在用：Obsidian 40+ MCP 工具、CodeGraph MCP

**A2A vs MCP 的关系：** MCP = AI ↔ 工具，A2A = AI ↔ AI。互补不冲突。
- 未来理想：Hermes 通过 MCP 连 Obsidian/文件系统等工具，通过 A2A 跟其他 AI 智能体互相派任务

**参考资料：** `references/ai-agent-interoperability-protocols.md`

## 参考资料

- `references/cron-obsidian-access.md` — Cron 任务执行时 Obsidian MCP 无法找到 vault 的问题和解决方案
- `references/deepseek-proxy-fix.md` — DeepSeek 400 错误修复：本地代理脚本方案，解决 thinking/reasoning_effort 冲突
- `references/third-party-agent-tools-research.md`
- `references/browser-automation-cautions.md` — 浏览器自动化测试的陷阱和正确做法（Google 表单、bot 检测、snapshot vs vision）
- `references/claude-code-troubleshooting.md` — Claude Code 子进程调度常见问题：ConnectionRefused、Gateway端口漂移、patch工具限制、权限/联网问题
- `references/agent-primer-installation.md` — Agent-Primer 全局安装与 CodeGraph Hook 配置流程
- `references/pdf-ocr-invoice-gap-analysis.md` — PDF/图片/发票识别技能差距分析
- `references/graphify-codegraph-research.md` — Graphify (⭐65k) 和 CodeGraph 调研：安装方式、MCP 配置、与 Obsidian 结合方案
- `references/ai-agent-interoperability-protocols.md` — A2A/MCP 协议深度分析：协议对比、核心概念、SDK 安装、与你当前方案的映射关系
- `references/skill-distribution-pattern.md` — 技能跨企业分发模式：配置模板化、install.sh 一键安装、GitHub 私有仓库载体选择

## 工作区约定

> ⚠️ 以下路径是用户个人的工作区约定，分发时应替换为变量或可配置项。

- 工作文件：`~/HermesPet_Workspace/`（可配置为 `$HERMES_WORKSPACE`）
- 临时数据：`/tmp/research_data/`
- 监督系统: `~/supervisor/supervisor_workspace/`
- 监督日志: `~/supervisor/supervisor_workspace/logs/`
- 任务状态: `~/supervisor/supervisor_workspace/tasks.json`

## 设计决策记录

- 用户要求自研监督系统，拒绝了第三方方案（Superpowers 22万星），因为 Superpowers 是给 Claude Code/Codex 用的编码流程插件，不管任务监控
- 2分钟无输出 = 卡住：用户明确指"连续2分钟没反应"才重启，不是任务总超时
- 超时设置：研究报告30min、代码20min、简单查询10min、文件整理15min
- 验收精度：按任务类型分级（报告类要求"结论"关键字，代码类要求可运行，数据类要求"结果"关键字）
- 自动重试3次：第1次重派，第2次缩短context，第3次失败通知用户
