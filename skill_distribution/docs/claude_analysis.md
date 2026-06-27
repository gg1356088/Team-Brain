# Claude Code LOOP 调度系统调用失败分析

## 1. 环境信息

- **Claude Code 版本**: 2.1.123
- **安装路径**: /usr/local/bin/claude (指向 ../lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe)
- **平台**: macOS (Darwin ARM64)
- **构建时间**: 2026-04-29T00:34:52Z
- **Git SHA**: 54903ade25087ef906df59ec6a608cc3a50a3f06

## 2. 问题描述

使用 `claude -p "/goal 任务描述"` 调用 Claude Code 时，返回：
```
Unknown command: /goal
```

同时测试了 `/loop` 和 `/schedule` 指令，均不支持（/loop 和 /schedule 指令被当作普通 prompt 发送给了 Claude API，消耗了额度后超时）。

## 3. 调查过程

### 3.1 官方帮助文档检查

运行 `claude --help` 查看可用选项，确认:
- Claude Code 的 CLI 只有 `--print/-p` 等非交互模式参数
- 没有任何 LOOP 相关的 CLI 参数或选项
- 支持的子命令包括: agents, auth, doctor, install, mcp, plugin, setup-token, update, ultrareview

### 3.2 二进制文件反编译分析

从编译后的二进制文件中提取关键信息:

**已实现的 Slash Command (Skills) 机制**:
- Claude Code 有完整的 slash-command/skills 系统
- Slash commands 通过 `<skill>` XML 标签加载技能内容
- 支持内置技能 (bundled/builtin) 和第三方插件技能 (plugin)
- 可通过 `@anthropic` 工具 `@anthropic-ai/claude-code` npm 包安装

**未找到的功能**:
- 源代码中**没有任何** `/goal`, `/loop`, `/schedule`, `/orchestrate` 等 LOOP 相关指令的实现
- 二进制文件中的 `Unknown command:` 错误是内置命令解析器的标准错误信息
- 没有发现任何 LOOP 调度相关的代码路径

### 3.3 可用的技能/命令

Claude Code 2.1.123 支持以下机制进行任务调度:

1. **内置 Slash Commands** (通过 `/` 触发):
   - 标准命令如 `/help`, `/bug`, `/resume`, `/continue` 等
   - 通过 skill 系统加载的技能 (如 `/frontend-design`, `/commit-push-pr`)
   - 这些技能本质上是预定义的系统 prompt + 权限配置

2. **Agent 工具调用** (via `@anthropic-ai/skills` tool):
   - 通过 `@anthropic-ai` 工具包中的 skill 工具调用已安装的技能
   - 支持 inline 和 forked 两种执行模式

3. **MCP (Model Context Protocol)**:
   - 通过 `--mcp-config` 加载自定义 MCP 服务器
   - MCP 命令也可作为 prompt 类型技能使用

4. **自定义 Agent** (via `--agents`):
   - 通过 `--agents` 参数定义自定义 agent (JSON 格式)
   - 每个 agent 可以有自己的 description 和 prompt

## 4. 根本原因

**LOOP 调度指令 (`/goal`, `/loop`, `/schedule`) 在 Claude Code 2.1.123 中不存在。**

LOOP 调度系统是 LOOP 项目自定义的调度机制，它假设 Claude Code 支持某些特定的 slash command 指令。然而：
- Claude Code 的 slash command 是由 Anthropic 定义的内置技能，不支持任意自定义的 slash command
- `/goal` 不是 Claude Code 的标准命令
- Claude Code 的 prompt 系统只会将 `--print` 模式的输入作为自然语言 prompt 发送给 Claude API，不会解析内部指令

## 5. API 余额问题

另一个问题是 402 Insufficient Balance：
- 这是 Anthropic API 的计费问题，与 LOOP 指令无关
- 需要充值 Anthropic API key 才能继续使用

## 6. 解决方案

### 方案 A: 使用普通 prompt 替代 LOOP 指令（推荐）

既然 Claude Code 不支持 LOOP 指令，最直接的方式是用结构化的自然语言 prompt 替代：

```bash
# 替代 "/goal 任务描述"
claude -p "请执行以下任务：任务描述。请按步骤完成，并在完成后总结结果。"

# 替代 "/loop 任务描述"
claude -p "请完成以下任务：任务描述。任务包含多个步骤，请逐步完成并在每一步后验证。"
```

### 方案 B: 使用 Claude Code 的 Agent 机制

利用 `--agents` 参数定义自定义 agent 来实现类似 LOOP 的功能：

```bash
claude --agents '{"task_executor": {"description": "执行具体任务", "prompt": "你是一个任务执行助手。请根据用户的描述完成任务。"}}' \
  -p "请帮我完成任务：任务描述"
```

### 方案 C: 使用 Claude Code Skills 系统

如果需要使用预定义的技能，可以通过 `@anthropic-ai` 工具在 Claude Code 内部调用：

```bash
claude -p "请使用 @anthropic-ai 工具执行以下技能：skill_name"
```

### 方案 D: 升级 Claude Code 版本

Loop 调度机制可能是 Anthropic 未来版本中才会引入的功能。当前版本 2.1.123 的构建时间是 2026-04-29，如果有更新的版本可能包含该功能。建议：
```bash
claude upgrade
```

但鉴于源码分析中完全没有 LOOP 相关的代码痕迹，即使升级也可能不包含此功能，因为 LOOP 指令很可能是 LOOP 项目自己的假设而非 Claude Code 的官方功能。

### 方案 E: 在 LOOP 项目中添加 fallback 机制

修改 LOOP 调度系统，使其：
1. 首先尝试发送 `/goal` 指令
2. 如果收到 "Unknown command" 错误，自动降级为普通 prompt
3. 在 prompt 中用自然语言描述任务意图

## 7. 总结

| 项目 | 状态 |
|------|------|
| Claude Code 版本 | 2.1.123 (确认) |
| `/goal` 指令 | 不支持，返回 "Unknown command" |
| `/loop` 指令 | 不支持，会被当作普通 prompt 发送给 API |
| `/schedule` 指令 | 不支持，会被当作普通 prompt 发送给 API |
| LOOP 功能存在性 | 在 Claude Code 中不存在，是 LOOP 项目的假设 |
| API 余额 | 不足 (402)，需充值 |
| 推荐方案 | 使用普通 prompt 替代，并添加 fallback 机制 |

## 8. 行动建议

1. **立即修复**: 修改 LOOP 调度代码，将 `/goal 任务描述` 替换为结构化 prompt：
   ```
   "请执行以下任务：任务描述。请按步骤完成，并在完成后总结结果。"
   ```

2. **添加 fallback**: 在 LOOP 代码中检测到 "Unknown command" 时自动降级

3. **解决 API 余额**: 充值 Anthropic API 额度

4. **长期考虑**: 如果使用 Claude Code 的 LOOP 调度是核心功能，建议联系 Anthropic 确认该功能是否在路线图中，或考虑使用其他支持类似功能的工具
