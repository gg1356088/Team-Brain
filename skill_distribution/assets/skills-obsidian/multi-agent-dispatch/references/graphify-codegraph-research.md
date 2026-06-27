# Graphify & CodeGraph 调研 (2026-06-11)

## Graphify

**项目**: `safishamsi/graphify` ⭐65,261
**描述**: AI coding assistant skill — 把任意文件夹（代码、SQL、R脚本、Shell、文档、论文、图片、视频）转成可查询的知识图谱。App代码+数据库schema+基础设施在一个图里。
**支持**: Claude Code, Codex, OpenCode, Cursor, Gemini CLI 等
**URL**: https://github.com/safishamsi/graphify

### 相关项目
- `lucasrosati/claude-code-memory-setup` ⭐760 — Obsidian + Graphify 组合方案，持久记忆+代码库知识图谱
- `bright-interaction/second-brain-for-claude` ⭐12 — Karpathy-style wiki + Graphify 知识图谱
- `rhanka/graphify` ⭐4 — 另一个 fork，也支持 OpenClaw, Factory Droid, Trae
- `sjhorn/graphify` ⭐3 — Go 语言移植版

### 安装
GitHub API 限流时无法自动安装。恢复后：
```bash
hermes skills install https://raw.githubusercontent.com/safishamsi/graphify/main/SKILL.md
```

### 与 Obsidian 结合
- Graphify 生成代码库知识图谱
- Obsidian 存结构化笔记和 wikilinks
- 两者互补：Graphify 管代码侧，Obsidian 管知识侧

## CodeGraph

**当前状态**: MCP 已安装 (`mcp_codegraph_codegraph_*` 工具可用)
**问题**: 需要指向项目路径才能工作
**修复**:
```bash
# 在项目目录初始化
cd /path/to/project && agent-primer init
```

或者手动配 MCP server args:
```json
{
  "codegraph": {
    "command": "agent-primer",
    "args": ["serve", "--mcp", "--path", "/absolute/path/to/project"]
  }
}
```

### 外部技能
- `zazuone/hermes-skills` 包含 codegraph 技能，可以直接安装
