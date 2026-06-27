---
name: loop-dispatch
description: LOOP 调度 — 通过结构化 prompt 让 Claude Code 或 Codex 自循环执行任务。当用户说"调度"、"让AI自己干"、"LOOP"、"goal"、"loop"时自动加载。
tags: [loop, dispatch, supervisor, multi-agent]
version: "2.0.0"
---

# LOOP 调度系统

## 核心概念

LOOP 调度系统让 Claude Code 或 Codex 自主执行任务，无需主 AI 盯着。

- **loop_dispatch.py** — 调度器：下发任务给 AI
- **loop_monitor.py** — 监控器：检查状态 + 飞书通知
- **config.py** — 统一配置模块

## 文件位置

安装后在 `$HERMES_SKILLS_WORKSPACE/loop_dispatch/`：
- `loop_dispatch.py` — LOOP 调度器
- `loop_monitor.py` — 监控器 + 飞书通知
- `config.py` — 统一配置模块

## 使用方式

### 下发任务

```bash
# Claude Code
cd ~/HermesWorkspaces/loop_dispatch
python3 loop_dispatch.py goal "处理 ~/待复核/*.pdf 发票，提取内容写入 invoice_results.json" --worker claude

# Codex
python3 loop_dispatch.py goal "处理 ~/待复核/*.pdf 发票，提取内容写入 invoice_results.json" --worker codex
```

### 查看状态

```bash
python3 loop_dispatch.py list
python3 loop_dispatch.py status <task_id>
```

### 启动监控

```bash
python3 loop_monitor.py start    # 后台监控
python3 loop_monitor.py check    # 手动检查一次
python3 loop_monitor.py status   # 查看监控状态
python3 loop_monitor.py stop     # 停止监控
```

## 配置

通过环境变量或 `config.json` 配置：

```bash
export HERMES_SKILLS_WORKSPACE=~/HermesWorkspaces
export FEISHU_CHAT_ID=oc_你的群ID
export CLAUDE_CMD=claude
export CODEX_CMD=/Applications/Codex.app/Contents/Resources/codex
```

或创建 `~/HermesWorkspaces/config.json`：

```json
{
    "feishu": { "chat_id": "oc_xxxxx" },
    "workers": {
        "claude_cmd": "claude",
        "codex_cmd": "/Applications/Codex.app/Contents/Resources/codex"
    }
}
```

## 协作思维框架——监督者模式

这是本系统的核心方法论：**你（主 AI）是监督者，子 AI 是执行者。**

### 基本原则

1. **监督者不下场干活** — 你的工作是拆分任务、派发、验收、汇总，不是自己去写代码
2. **子 AI 各司其职** — 不要让一个 AI 做所有事，按角色分工
3. **验收必须交叉验证** — 至少两个 AI 从不同角度审查，互相印证
4. **汇报要干净** — 把两份报告交叉比对后，提炼成一份结论给最终用户

### 角色分工模板

#### Agent A — 代码质量审查员

**适用场景：** 代码审查、逻辑验证、语法检查、边界条件

**派任务时的提示词模板：**
```
请审查 [文件路径] 目录下的代码，重点检查：
1. 语法是否正确
2. 边界条件是否处理
3. 错误处理是否完备
4. 有没有明显的逻辑 bug

请给出详细的审查报告，按严重程度排列问题。
```

#### Agent B — 安全与配置审查员

**适用场景：** 敏感信息扫描、配置检查、文档准确性

**派任务时的提示词模板：**
```
请审查 [文件路径] 目录，重点检查：
1. 有没有硬编码的个人路径、API Key、Token
2. .gitignore 是否覆盖了 .env、*.pid、*.log 等运行时文件
3. 文档中的路径和命令是否与代码一致
4. 有没有泄露真实密钥或群ID

请给出详细的安全审查报告。
```

#### Agent C — 用户体验审查员（可选）

**适用场景：** 安装脚本、README、配置模板

**派任务时的提示词模板：**
```
假设你是一个完全不懂这个项目的新人，从 [文件路径] 开始安装：
1. README 是否足够清晰？
2. 安装脚本会不会踩坑？
3. 配置模板是否覆盖了所有必要项？
4. 有没有遗漏的步骤？

请从用户角度给出改进建议。
```

### 工作流程

```
1. 拆分任务 → 确定需要审查哪些方面
2. 并行派发 → 不同角色同时工作，不互相等待
3. 收集报告 → 两份或多份报告分别阅读
4. 交叉验证 → 对比两份报告的结论，看是否有矛盾
5. 汇总决策 → 综合所有信息，决定是否需要修复
6. 指派修复 → 有针对性的指派对应的 Agent 修复
7. 复查验收 → 修复后再派对应的 Agent 验证
8. 最终汇报 → 提炼成一份干净的报告给最终用户
```

### 常见错误

- ❌ 让一个 AI 做所有事 → 信息重叠，浪费 token
- ❌ 两份报告结论矛盾却不深究 → 可能有隐藏 bug
- ❌ 收到报告就交给用户 → 监督者必须提炼，不是转发
- ❌ 修复后不复查 → 修了等于没修

## Pitfalls

- Claude Code 需要在 PATH 中或配置 `CLAUDE_CMD`
- Codex 路径通常是 `/Applications/Codex.app/Contents/Resources/codex`
- 飞书通知依赖 lark-cli 已配置认证
- 任务描述尽量明确，AI 通过结构化 prompt 理解意图
- monitor.py 通过 prompt 中的文件名模式检测任务完成
- 飞书通知失败会记录到 `.notification_errors.log`
- config.py 配置优先级：CLI > 环境变量 > .env > config.json > 默认值
- 两个 Python 文件都有降级机制，config.py 不在 path 上时自动内联加载

## 审查记录

> 2026-06-18 v2.0 重大更新：
> 1. 新增 config.py 统一配置模块
> 2. loop_dispatch.py 改用 argparse，参数解析不再混入描述
> 3. 降级代码补齐 .env 加载逻辑
> 4. install.sh 补齐 config.py 复制
> 5. .gitignore 修正，模板文件不被忽略
> 6. 新增协作思维框架章节

> 2026-06-17 两轮审查（Claude Code + Codex）后修复 4 个问题：
> 1. P0 状态流转断裂 — 自动检测 dispatched 任务完成状态
> 2. P0 飞书通知无重试 — 3 次重试 + 指数退避 + 失败日志
> 3. P1 notified 无限增长 — 超过 50 条自动裁剪
> 4. P1 PID 锁文件无验证 — 僵尸进程自动清理

## 参考

- [loop_reference.md](references/loop-reference.md) — 经典用例速查
- [awesome-agent-loops](https://github.com/serenakeyitan/awesome-agent-loops) — LOOP 指令大全
