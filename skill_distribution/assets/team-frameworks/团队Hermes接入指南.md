# 团队 Hermes 接入指南

> 给团队里还没用 Hermes 的人。先装 Hermes，再加载技能，然后用团队框架理解方法论。

## 一、安装 Hermes

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

装完验证：
```bash
hermes doctor
hermes --version
```

## 二、加载团队技能

所有团队技能在 `skill_distribution/skills-obsidian/` 里，复制到 Hermes 技能目录：

```bash
cp -r skill_distribution/skills-obsidian/* ~/.hermes/skills/
```

然后在 Hermes 会话中加载：
```
/skill obsidian
/skill knowledge-base
/skill multi-agent-dispatch
```

## 三、配置环境变量

在 `~/.hermes/.env` 中设置：

```bash
# Obsidian vault 路径（必需）
OBSIDIAN_VAULT_PATH="/你的vault路径"

# 工作区（可选）
HERMES_WORKSPACE="~/你的工作目录"
```

## 四、加载后能做什么

| 加载技能后 | 效果 |
|-----------|------|
| `obsidian` | AI 能直接读写你的 Obsidian vault，按图谱化链路搜索 |
| `knowledge-base` | AI 按 LLM Wiki 方法论帮你整理知识，不再瞎建文件 |
| `multi-agent-dispatch` | AI 能拆任务、派 Claude Code/Codex 并行干活、自动验收 |
| `dispatch-with-context` | 派任务时 AI 会带上完整背景和验收清单，不会瞎跑 |

## 五、和团队框架的关系

| 先读 | 再加载 | 理解了什么 |
|------|--------|-----------|
| 知识库建设框架 | `obsidian` + `knowledge-base` | 为什么 AI 这样组织知识、zone 架构的设计思路 |
| AI 协作框架 | `dispatch-with-context` | 为什么 AI 派任务时要带验收清单、CaveMan 精简规则 |
| 发票处理框架 | 实际操作时 | 为什么要按 7 步流程走、10 个坑点别踩 |
| PDF 踩坑框架 | 实际操作时 | 14 条前人踩过的坑——别重蹈覆辙 |
| 视觉复核框架 | 实际操作时 | 工具链怎么选、高风险类别怎么判断 |

框架是"为什么"，技能是"怎么做"。两个一起读才能既知道方法又知道操作方法。
