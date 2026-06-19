---
name: dispatch-with-context
description: 调度 AI 子任务时必须先交代完整背景，并逐条验收结果是否达标
version: 2.0
tags: [dispatch, context, quality, supervision]
---

# 调度与验收规范

## 一、派任务前：必须交代完整背景
- 告诉对方：我们现有技能、当前痛点、约束条件、目标
- 不要只给通用 prompt
- 错误示范："调研 PDF 识别工具" → 通用列表
- 正确示范：先说明 markitdown/pymupdf/vision_analyze 现状 + 发票流程痛点

## 二、派任务时：明确验收清单（Checklist）
每个任务必须附带验收清单，例如：
- [ ] 步骤1：三个领域各搜 10 个结果
- [ ] 步骤2：Top 3 工具的 README 前 50 行
- [ ] 步骤3：环境检查输出
- [ ] 步骤4：结论是否包含"对现有技能的补充/替代关系"

## 三、收到结果后：逐条核对（必须执行）
1. **检查每个步骤是否执行** — 对照 Checklist，逐项确认
2. **任何一项未达标 → 让他重跑该步骤** — 不是跳过，是补做
3. **不要只看结论** — 结论再漂亮，步骤没跑完就是不合格
4. **中间也要 check** — 不要等全部完成才看，定期 poll 进度，发现跑偏立即纠正

## 四、错误案例
- ❌ 收到 Claude Code 结果，只看结论说"还行"就结束
- ❌ 发现步骤1有搜索但没抓 README，直接放过
- ❌ 没有逐条核对 Checklist，放任子 agent 跑偏
- ❌ 用 `delegate_task` 派发但子 agent 拿不到终端权限 → 导致 Claude Code 无法执行
|- ❌ **文件丢在家目录根上** — 临时产物必须放工作区（`$HERMES_WORKSPACE` 或 `HermesPet_Workspace`），用完清理

## 五、正确流程
```
派任务（带 Checklist + 完整背景）
  ↓
Claude Code 跑完
  ↓
我逐条核对 Checklist（1→2→3→4）
  ↓
全部通过 → 验收通过，写入报告
有缺失 → 告诉他缺什么，让他补跑
  ↓
最终输出
```

## 六、文件存放纪律
- **临时产物**（`.py`、`.txt` 草稿、`-prompt.txt`）→ 放 `$HERMES_WORKSPACE/`，用完要么删要么整理
- **正式配置/说明**（协作规则 `.md`、配置 `.json`）→ 放在该在的位置不动
- **最终报告** → 写 Obsidian
- **绝对禁止**：把临时文件扔在家目录根上（`~/*.py`、`~/*.md`）

## 七、调度方式选择
- **首选 `claude -p "prompt"`** — Claude Code 直接跑，有完整终端权限
- **避免 `delegate_task`** — 子 agent 拿不到终端权限，所有命令执行都被拒绝
- 不要绕道子 agent 再去调终端，直接调 Claude Code CLI
