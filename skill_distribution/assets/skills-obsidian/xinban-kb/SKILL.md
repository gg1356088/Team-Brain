---
name: xinban-kb
description: "xinban 的个人知识库协作 — 基于通用 knowledge-base 技能，叠加个人偏好和情报领域。"
platforms: [macos]
version: "1.0.0"
---

# xinban 知识库协作

This is a **personal customization** of the `knowledge-base` skill. The general methodology, zone architecture, and reading/writing protocols are defined in the `knowledge-base` skill — read that first.

This file adds **personal preferences** on top of the generic rules.

## Vault Location

```
/Users/xinban/obsidian知识内容库/
```

> ⚠️ This is user-specific. For the generic vault path resolution, see the `knowledge-base` skill.

## Personal Intelligence Domains

The user expects active intelligence pushing in these domains:
- AI Agent
- MCP
- CLI tools
- Automation
- Open source projects

When pushing:
- Explain WHAT + WHY + HOW + WHO + STAGE
- Connect to the user's work explicitly
- Offer to dig deeper: "要不要我帮你看看具体怎么接入?"
- No report-style formatting (no "判断:", "结论:", "建议:")
- If nothing worth pushing, stay silent

The cron job `情报扫描-AI Agent/MCP/CLI/自动化/开源` runs hourly for this purpose.

## Key Collaboration Rules (personal additions)

1. **Fact-first**: Always check primary sources before answering. Never guess.
2. **Certainty levels**: Distinguish 已本地验证 / 官方文档 / 推断 / 社区说法 / 尚未确认.
3. **Install/access debugging**: Follow the dependency chain layer by layer.
4. **User observation priority**: If the user's screen contradicts your analysis, trust what they see.
5. **File iteration**: Modify existing files, don't create version explosion. Clean up temp files before delivery.
6. **Conciseness**: Fact question → check source. Uncertain → keep checking. Don't guess. Non-official → must label.

## References

- `references/distilled-principles.md` — Operational rules distilled from the knowledge base
- `knowledge-base` — Generic methodology (parent skill)
