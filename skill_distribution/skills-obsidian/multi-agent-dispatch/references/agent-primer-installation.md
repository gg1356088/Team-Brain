# Agent-Primer 全局安装指南

## 什么是 Agent-Primer

Agent-Primer 是一个全局工具，为多个 AI coding agent（Claude Code, Codex, Cursor, Gemini, OpenCode 等）在会话启动时自动注入编码规范、项目规则和 CodeGraph 索引检查。

## 安装流程

```bash
# 全局安装 agent-primer
curl -fsSL https://raw.githubusercontent.com/nicepkg/agent-primer/main/install.sh | bash -s -- --global --with primer

# 安装过程中可以选择加载的模块：
# - primer: 本地记忆引擎（记住用户编码风格）
# - karpathy: Karpathy 编码规范
# - superpowers: Superpowers 方法论
# - codegraph: CodeGraph 索引自动检查 Hook
```

## 全局配置结构

安装后会在多个 agent 的目录下注册 SessionStart Hook：

- `~/.claude/CLAUDE.md` — Claude Code 加载的编码规范
- `~/.claude/settings.json` — Hook 注册（SessionStart 触发 CodeGraph 检查）
- `~/.codex/AGENTS.md` — Codex 加载的规范
- `~/.codex/hooks.json` — Codex Hook 注册
- `~/.cursor/hooks.json` — Cursor Hook 注册
- `~/.gemini/settings.json` + `~/.gemini/GEMINI.md` — Gemini
- `~/.config/opencode/` — OpenCode
- `~/.kimi-code/` — Kimi

## CodeGraph Hook 逻辑

SessionStart Hook 会在 agent 会话启动时自动运行：

1. 检查当前目录是否有 `.codegraph/` 目录
2. 如果有 → 直接使用，跳过检查
3. 如果无 → 提示用户运行 `codegraph init -i` 并终止本次会话
4. 用户运行 init 后，下次会话自动通过

## 注意事项

- agent-primer 的安装脚本可能输出重复拷贝的小错误（`kit` 重复），但不影响核心功能
- Hook 配置是全局的，影响所有支持的 agent
- 如果需要移除，手动删除对应的 hooks.json 和 AGENTS.md/CLAUDE.md 中的 primer 段
- CodeGraph CLI 必须已安装（`which codegraph` 确认），否则 Hook 检查会失败

## 安装后验证

```bash
# 确认 CLI 已安装
codegraph --version

# 确认 Hook 已注册
cat ~/.claude/settings.json | grep -A5 hooks

# 确认 CLAUDE.md 有 primer 内容
grep -c "codegraph" ~/.claude/CLAUDE.md
```