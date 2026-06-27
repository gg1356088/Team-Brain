---
name: obsidian
description: Read, search, create, and edit notes in the Obsidian vault.
platforms: [linux, macos, windows]
---

# Obsidian Vault

Use this skill for filesystem-first Obsidian vault work: reading notes, listing notes, searching note files, creating notes, appending content, and adding wikilinks.

## Vault path configuration

**Resolve vault path in this order:**

1. **Environment variable** `OBSIDIAN_VAULT_PATH` — if set, use it directly
2. **User-specific config** `references/user-vault-path.md` — if this skill copy has one, read it
3. **Default fallback** `~/Documents/Obsidian Vault` — try this common macOS path
4. **Probe** — if none of the above work, search `~/` for folders named `*obsidian*` or `*知识库*` using `os.walk`

```bash
# Quick check
echo $OBSIDIAN_VAULT_PATH
ls -d ~/Documents/Obsidian\ Vault 2>/dev/null || echo "fallback not found"
```

> ⚠️ If the user references a vault by a different name (e.g. "Obsidian知识库"), DO NOT assume a different path. The actual vault folder name is what matters. Use `os.walk` to search for it if unsure. The name in Obsidian's UI settings may differ from the folder name on disk.

### For distribution / other users

When distributing this skill to another user or organization:

1. Ship `references/user-vault-path-template.md` (generic, no hardcoded path)
2. Instruct the recipient to create `references/user-vault-path.md` with their actual vault path
3. Or set `OBSIDIAN_VAULT_PATH` in their `.env` / environment
4. **Never ship** `references/user-vault-path.md` with someone else's personal path

See `references/user-vault-path-template.md` for the template.

## Read a note

Use `read_file` with the resolved absolute path to the note. Prefer this over `cat` because it provides line numbers and pagination.

## List notes

Use `search_files` with `target: "files"` and the resolved vault path. Prefer this over `find` or `ls`.

- To list all markdown notes, use `pattern: "*.md"` under the vault path.
- To list a subfolder, search under that subfolder's absolute path.

## Search

Use `search_files` for both filename and content searches. Prefer this over `grep`, `find`, or `ls`.

- For filenames, use `search_files` with `target: "files"` and a filename `pattern`.
- For note contents, use `search_files` with `target: "content"`, the content regex as `pattern`, and `file_glob: "*.md"` when you want to restrict matches to markdown notes.

## Create a note

Use `write_file` with the resolved absolute path and the full markdown content. Prefer this over shell heredocs or `echo` because it avoids shell quoting issues and returns structured results.

## Append to a note

Prefer a native file-tool workflow when it is not awkward:

- Read the target note with `read_file`.
- Use `patch` for an anchored append when there is stable context, such as adding a section after an existing heading or appending before a known trailing block.
- Use `write_file` when rewriting the whole note is clearer than constructing a fragile patch.

For an anchored append with `patch`, replace the anchor with the anchor plus the new content.

For a simple append with no stable context, `terminal` is acceptable if it is the clearest safe option.

## Targeted edits

Use `patch` for focused note changes when the current content gives you stable context. Prefer this over shell text rewriting.

## Wikilinks

Obsidian links notes with `[[Note Name]]` syntax. When creating notes, use these to link related content.

## MCP CLI 连通性检查

当使用 `mcp_marwansaab_obsidian_cli_mcp_*` 工具时，如果调用超时（`CLI_TIMEOUT`），依次检查：
1. **Obsidian 应用是否已打开** — CLI 需要 Obsidian 运行
2. **Integrated CLI 开关是否启用** — Settings 里找
3. **`obsidian-cli` 二进制路径是否正确** — 不一定是 `/usr/local/bin/obsidian`，可能在 `/Applications/Obsidian.app/Contents/MacOS/obsidian-cli`
4. **Vault 名称是否匹配** — 用 `obsidian_exec(command="vaults")` 确认实际 vault 名称

## 会话开始必须查 Obsidian
每次新会话开始时，**第一件事是搜索 Obsidian**，看看之前是否整理过相关笔记。不要等用户提醒。

搜索流程：
1. 用户提到任何话题 → 先用 `context_search` 或 `search` 搜 Obsidian
2. 有笔记 → 读笔记，基于笔记回答
3. 没笔记 → 搜索后再回答，不确定就说不知道
4. 整理完新知识 → 同时写 Obsidian + 持久记忆（关键词索引）

Obsidian 是我的知识库大脑。持久记忆（MEMORY.md）只存关键词索引触发 Obsidian 搜索，Obsidian 里存详细内容。

> ⚠️ **忘记搜 Obsidian 是最常见的失误**——整理完知识只写文件不写记忆，下次会话完全不知道。每次重要知识整理后，务必在持久记忆中存关键词索引。

## Pitfalls
- 每次新会话必须查 Obsidian，不要等用户提醒。忘了搜 Obsidian 就是忘了我的知识库在哪。
- CLI 路径可能不是默认的 `/usr/local/bin/obsidian`，需要用 `terminal` 检查实际路径——正确路径通常是 `/Applications/Obsidian.app/Contents/MacOS/obsidian-cli`
- 用户说的 vault 名称（如"知识库 内容库"）可能跟文件夹名一致，也可能不一致
- 所有 MCP 调用都超时 = 基本是 Integrated CLI 没启用或者 Obsidian 没打开
- MCP 连不上时的验证顺序：先用轻量级工具（如 `files`、`paths`）确认 vault 连通性，不要直接上 `obsidian_exec`——重命令更容易超时且错误信息不明确
- `obsidian_exec` 需要设置 `timeoutMs`，默认 30s 可能不够，建议设 10000-15000ms
- MCP 连续失败后标记 unreachable（~48s auto-retry），不要立即重试
- 知识库按 10 zone 架构组织，00-08 目录。读取笔记时优先按图谱化链路：来源摘要 → 概念/实体 → 主题综述 → 开放问题
- 知识库文件结构通过 `paths` 工具确认，`files` 只返回直接子目录的文件（非递归）
- Obsidian 回收站（.trash）不在 vault 路径下可见，MCP 工具看不到 `.obsidian/.trash` 里的内容——如果需要清理回收站，用户需在 Obsidian UI 里操作
- `paths` 工具返回目录条目（以 `/` 结尾）和文件条目（不以 `/` 结尾），区分注意

## 知识库健康审计与修复

当知识库出现断链、孤儿页、frontmatter 缺失等问题时，用这个流程：

1. **扫描断链**：用 Python 脚本 `os.walk` 遍历 vault，正则提取 `[[...]]` wikilink，逐一尝试候选路径（原始、加.md、取basename、strip trailing /、split heading `#`）匹配。输出 `broken_links` 列表。
2. **扫描孤儿页**：维护 `inbound` 字典（被哪些文件引用），然后对比所有 `.md` 文件路径，找出不在 `inbound` 中的非系统文件（排除 index.md, log.md, README.md, 首页, 工作台）。
3. **扫描 frontmatter 缺失**：对非系统文件检查 `---...---` 头部是否存在，以及 `title:`, `type:`, `tags:` 是否齐全。
4. **修复断链**：优先将 bare wikilink `[[EntityName]]` 替换为带路径的 `[[03-实体/EntityName]]`。对于 log.md 这类单层 heading 结构，`patch_heading` 无法处理（需 `::` 分隔的 heading_path），直接 `write_note` 覆盖整个文件。
5. **修复 frontmatter**：用 `write_note` 覆盖添加标准 frontmatter（title, type, status, tags, created, updated, related_* 字段）。
6. **修复孤儿页**：在对应地图页（实体地图、概念地图等）添加指向孤儿页的链接。
7. **清理空文件**：删除内容为空或只有 frontmatter 的孤立文件。
8. **最终验证**：重新运行步骤 1 的断链扫描，确认清零。

### Pitfalls
- `patch_heading` 要求 `heading_path` 至少两段 `::` 分隔（如 `"H1::H2"`），单层 heading（如 `## [date] title`）会报 VALIDATION_ERROR。遇到这种情况直接 `write_note` 覆盖。
- log.md 经常有重复条目（同一事件写了两次，一次带路径一次不带），修复时要去重，只保留带完整路径的版本。
- 引用不存在的"概念名"（如 `[[双链]]` 但知识库中没有 `双链.md`）不算真正断链——这是引用了一个概念而非文件。这类应在概念页补全，但短期内可以容忍。
- `write_note` overwrite 会完全替换文件内容，务必先 `read` 完整内容再写入，避免丢失历史段落。
