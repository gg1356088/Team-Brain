---
name: knowledge-base
description: "通用知识库协作技能 — Karpathy LLM Wiki 方法论在 Obsidian 中的实践。覆盖图谱化读取、zone 架构、读写协议、命名规范。"
platforms: [macos, linux, windows]
version: "1.0.0"
---

# 知识库协作 — 通用版

This skill covers how to work with a structured Obsidian knowledge base following Karpathy's LLM Wiki methodology.

## Vault Location

**Resolve vault path in this order:**

1. **Environment variable** `OBSIDIAN_VAULT_PATH` — if set, use it directly
2. **User-specific config** `references/user-vault-path.md` — if this skill copy has one
3. **Default fallback** `~/Documents/Obsidian Vault` — try this common macOS path
4. **Probe** — search for `.obsidian` folders if none of the above work

```bash
# Quick check
echo $OBSIDIAN_VAULT_PATH
find ~ -maxdepth 3 -name ".obsidian" -type d 2>/dev/null | head -5
```

> ⚠️ If the user references the vault by a different name, the actual folder name on disk may differ. Use `os.walk` to search the home directory if the hardcoded path doesn't match the user's intent.

## Directory Structure (Zone Architecture)

| Zone | Purpose |
|------|---------|
| `00-系统/` | Rules, templates, collaboration guidelines, field specs |
| `01-原始资料/` | Raw source materials — read-only, never modify |
| `02-来源摘要/` | Source summaries — one page per article/PDF/podcast |
| `03-实体/` | Entities — people, companies, products, tools, projects |
| `04-概念/` | Concepts — methods, terminology, frameworks, models |
| `05-主题综述/` | Theme reviews — long-term research directions |
| `06-对比分析/` | Comparisons — tools, methods, models, viewpoints |
| `07-问题与待研究/` | Open questions — unresolved problems, hypotheses to verify |
| `08-会话沉淀/` | Session summaries — high-value conclusions from conversations |

### System Files

- `index.md` — Master index. Update after significant writes.
- `log.md` — Operation log. Append after every write.
- `00-首页.md` — Knowledge base home page.
- `00-工作台.md` — Daily workbench entry point.
- `00-系统/知识库规则.md` — Maintenance rules, page types, update principles.
- `00-系统/AI协作准则.md` — Long-term AI collaboration behavioral rules.
- `00-系统/字段规范.md` — Unified frontmatter and relationship fields.
- `00-系统/图谱化读取说明.md` — How to read the knowledge base by relationship graph.

### Maps (graph entry points)

- `03-实体/实体地图.md` — Entity page index
- `04-概念/概念地图.md` — Concept page index
- `05-主题综述/主题地图.md` — Theme review index
- `07-问题与待研究/开放问题地图.md` — Open questions index

> 💡 Zone names are customizable. The numbering (00-08) is a convention, not a requirement. Adapt to your own structure.

## Reading Protocol

Never full-scan the vault unless the user explicitly asks. Follow the graph chain:

```
index.md → map page → relevant pages → source summaries → raw materials
```

This minimizes token waste and respects the LLM Wiki principle: knowledge is organized, not scattered.

## Writing Protocol

When the user triggers writing (says "沉淀一下", "记录到 Obsidian", "写进知识库", "这个要记下来", or asks for session summaries):

1. Determine the content category
2. Choose the right directory (see table above)
3. Use the appropriate template from `00-系统/模板库/`
4. Write the note with proper frontmatter (see 字段规范.md)
5. Add wikilinks to connect related pages
6. Update `index.md` with a one-line entry
7. Append to `log.md`

### Naming Convention

Format: `YYYY-MM-DD 项目或主题 类型.md`

Session summaries always carry a date prefix. Stable concepts and entities can omit dates.

### Active Ingestion Rules

- Raw materials go to `01-原始资料` — read-only
- Knowledge pages are continuously updatable
- Each page must link at least 2 other pages — no orphans
- Conflicts are recorded with sources, not flattened
- Uncertain content is marked "待验证"
- Cross-workspace rules: Obsidian is the knowledge hub; each workspace AGENTS.md is a lightweight entry

### When to Write Proactively

Write to the knowledge base when encountering:
- High-quality viewpoints
- Reusable methodologies
- Worth-learning cases
- Tool, skill, or workflow experiences
- Content creation / video / web production experience
- User's explicitly stated long-term preferences and collaboration rules
- Judgment criteria that may be reused

## Vault Access via MCP

The vault is accessed through the Obsidian MCP server. Use MCP tools for all vault operations:
- `read` — read note content
- `write_note` — create/replace notes
- `search` / `context_search` / `pattern_search` — search vault
- `links` / `backlinks` — navigate graph
- `paths` / `files` — list directory contents
- `set_property` / `read_property` — frontmatter management
- `patch_block` / `patch_heading` — surgical edits

Never use `file` tools (read_file, write_file, etc.) directly on vault files — the vault may be on a different filesystem or have sync considerations. Always route through MCP.

## Pitfalls

- Do NOT edit raw materials in `01-原始资料/` — they are read-only by design.
- Do NOT create pages as "总结.md" or "记录.md" — use proper dated, typed names.
- Do NOT merge unrelated topics into one page.
- Do NOT full-scan the vault for simple queries — use the graph chain.
- The MCP server may time out if Obsidian's Integrated CLI is not enabled — verify the toggle in Obsidian Settings first.
- Never use file tools on vault files — always use MCP tools for vault access.
