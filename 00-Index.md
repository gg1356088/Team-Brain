---
tags: [MOC, index, hub]
created: 2026-05-26
updated: 2026-06-12
---

# IncepVision Law Knowledge Hub

这套 Obsidian / Codex 工作区按业务上只分三块：

| 业务块 | 入口 | 覆盖范围 |
|---|---|---|
| 财务 | [MOC/财务](财务.md) | Bookkeeping、tax、财报、客户 workpaper、Staff Payment、Receipt Renamer、TimeSheet to Wave |
| 人事 | [MOC/人事](人事.md) | HR 简历、面试、笔试、HR monitor、HR Chat 状态 |
| 行政 | [MOC/行政](行政.md) | Remote office asset handoff、运营文档、Chat archive、表单/权限/交接类工作 |

## 当前任务怎么走

- 财务问题：先看 [MOC/财务](财务.md)，再进入 [docs/codex-index/finance](../docs/codex-index/finance.md)。
- 人事问题：先看 [MOC/人事](人事.md)，再进入 [docs/codex-index/hr](../docs/codex-index/hr.md)。
- 行政问题：先看 [MOC/行政](行政.md)，再进入 [docs/codex-index/admin-work](../docs/codex-index/admin-work.md)。
- 不确定归属时：看 [MOC/知识架构总图](知识架构总图.md)。

## 系统与历史

这些不是第四类业务，只是支撑三大业务块的操作层或历史层。

| 类型 | 入口 | 用途 |
|---|---|---|
| 系统支撑 | [MOC/系统支撑](系统支撑.md) | Agent 规则、Codex 索引、基础设施、Skills、工具和历史记忆 |
| Codex 顶层规则 | [AGENTS](../AGENTS.md) | 路由、安全边界、Google/Office/Obsidian 全局规则 |
| Workflow registry | [workflows/workflow-registry](../workflows/workflow-registry.md) | 当前 workflow 状态、入口、是否 self-running |
| Workspace summary | [README](../README.md) | 工作区总目录 |
| 能力快照 | [docs/codex-index/capability-snapshot](../docs/codex-index/capability-snapshot.md) | 程序/技能/插件能力口径 |
| 深层总图 | [MOC/知识架构总图](知识架构总图.md) | 解释散落文件、历史口径和跨模块关系 |
| README / 对象命名说明 | [MOC/对象命名与模块结构说明](对象命名与模块结构说明.md) | 为什么根目录保留 README、业务对象改用名称 |
| 顶层写作偏好使用规则 | [MOC/顶层写作偏好使用规则](顶层写作偏好使用规则.md) | 总结、timesheet、邮件写作、回复客户的顶层写作口径 |

## 读取原则

- 业务视角永远优先：财务 / 人事 / 行政。
- 资料调用默认 local-route-first + targeted-Obsidian：先用本地 router / workflow index / state 判断任务、客户、期间和执行入口，再从本页进入对应 MOC，定向读取 client profile / workflow note / workpaper / run log；不全量扫描 vault。只有资料缺失、过期或冲突时才问用户。
- Obsidian 与本地 workflow 不做镜像复制。只有当 Obsidian 记忆会改变可执行 state、source-document status、workpaper 状态、客户 profile 字段或自动化配置时，才同步回本地 workflow；人工判断、历史结论、已确认口径保留在 Obsidian，并链接本地证据。
- 当前税法、截止日、罚金、表格说明等规则性问题仍要结合官方现行来源；客户事实优先以 Obsidian 和 workpaper 记忆为准。
- 写入任何业务记忆或新 Markdown note 前，先从本页判断归属，再进入对应 MOC 和 workflow/client/object 索引确认规范路径；写入后补回 MOC / workflow / index / profile 链接，避免游离节点和重复对象。
- `Projects/*` 只放非 workflow 的项目构想；workflow 历史摘要放回各自 `workflows/*/docs/`。
- `Skills/*`、`Infrastructure/*`、历史记忆不是主业务入口。
- 客户和 workflow 的 Obsidian 可见笔记用对象名称；只有真正的 workspace/root 说明保留 README。
- 不为了“看起来少”合并客户事实、state、token、日志或运行说明；只在入口层收拢。
