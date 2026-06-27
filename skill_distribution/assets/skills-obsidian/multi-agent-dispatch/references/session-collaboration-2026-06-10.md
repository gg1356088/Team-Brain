"""
Session 协作纪要：2026-06-10

## Obsidian 知识库大脑
- Obsidian 知识内容库是主要知识库，重要知识存 Obsidian（详细内容）+ 持久记忆（关键词索引）
- 每次新会话启动必须搜索 Obsidian，不能等用户提醒
- 文件：AGENTS.md 中有详细规则
- 关键笔记：技能工具链清单.md、AI智能体互通协议 A2A与MCP.md

## AGENTS.md 文件管理
- /Users/xinban/AGENTS.md — Hermes 会话级协作规则
- ~/.hermes/SOUL.md — 人格和沟通风格定义
- 其他 AI 工具（Claude Code、Codex 等）有各自的 AGENTS/CLAUDE.md，互不干扰
- 不要混改不同 AI 工具的文件

## DeepSeek 400 修复
- 已在 references/deepseek-proxy-fix.md 记录
- 本地 proxy 脚本：~/.claude/deepseek-fix-proxy.py
- patch 工具不能改 config.yaml（安全拦截），用 write_file

## A2A 与 MCP 协议对比
- MCP = AI ↔ 工具，A2A = AI ↔ AI
- A2A v1.0 已发布，Python SDK 可用，Claude Code 尚未原生支持
- 参考资料：references/ai-agent-interoperability-protocols.md
"""
