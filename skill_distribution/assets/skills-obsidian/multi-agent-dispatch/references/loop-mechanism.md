# LOOP 机制调研与修正（2026-06-18 重大修正）

## 来源

awesome-agent-loops: https://github.com/serenakeyitan/awesome-agent-loops
Claude Code 创建者 Boris Cherny 的 X 推文：
"I don't prompt Claude anymore. I create loops — and the loops do the work."

## ⚠️ 重大修正（2026-06-18）

`/goal`、`/loop`、`/schedule` **三个命令在 Claude Code 和 Codex 中都不存在**。

2026-06-18 实际测试验证：
```
$ claude -p "/goal ..."
→ Claude Code 不认识 /goal，当作普通 prompt 文字处理
$ codex exec -p "/loop ..."  
→ Codex 也不认识 /loop，当作普通 prompt 文字处理
```

结论：Boris Cherny 的推文是关于编程理念（让循环结构编码），不是关于 CLI 命令。

## 实际替代方案

用 **结构化自然语言 Prompt** 模拟 LOOP 效果：

### 模拟 /goal（一次性大任务，AI 自循环完成）
```
你的目标：{具体任务描述}
请一步步完成，每次做完验证结果是否正确，完成后写入 {output_path}。
如果中途遇到障碍，尝试不同的方法直到完成任务。
```

### 模拟 /loop（定时重复执行）
外部调度器（loop_monitor.py）负责定时轮询，AI 每次只执行单次任务。不做自循环。

### 模拟 /schedule（云端定时任务）
用 Hermes 内置 `cronjob` 工具，不在 AI 子进程中实现。

## 与 supervisor.py 的关系

- supervisor.py 做"协调层"（分配谁干什么、验收结果）
- loop_dispatch.py 做"执行层"，将结构化 Prompt 下发给 AI 子进程
- loop_monitor.py 做"通知层"，轮询任务状态并推飞书通知
- 不存在原生的 LOOP 命令，所有循环逻辑在外部调度器实现

## 最佳实践

1. Prompt 要包含：目标、输出路径、验证标准、重试策略
2. 输出文件路径要具体（如 `results/output.json`），方便外部检测完成
3. Monitor 通过正则 `(?:保存到|写入到|生成|创建)\s+([^\s"']+\.json)` 提取文件名来自动检测完成
4. Claude Code 需要预审批权限（settings.json 中 permissions.allow）
5. Codex 必须用 `codex exec -s workspace-write` 允许文件写入

## Pitfalls

- **`/goal` `/loop` `/schedule` 都不存在** — 不要用这些指令
- Claude Code 超时要设 120s 以上（短 timeout 会导致 AI 没写完就断）
- Codex 用 `codex exec -s workspace-write -p "prompt"` 而不是 `-p`
- 不要在 Prompt 里包含 `/goal` 前缀，会当作文本处理