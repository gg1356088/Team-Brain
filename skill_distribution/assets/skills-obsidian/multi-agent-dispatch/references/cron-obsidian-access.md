# Cron 任务 + Obsidian MCP 访问问题

## 问题
Cron 任务（后台定时任务）在执行时，Obsidian MCP 工具可能无法找到 vault，返回 `CLI_REPORTED_ERROR: "Vault not found."`。

## 原因
Cron 任务在独立 session 中运行，不继承当前对话的上下文。Obsidian CLI 需要通过 `obsidian vaults` 或 `vaults` 命令枚举 vault，如果 Obsidian 应用正在运行但 CLI 找不到注册的 vault，就会失败。

常见情况：
1. **Obsidian 应用未启动** — CLI 无法连接
2. **Vault 名称不匹配** — CLI 注册的 vault 名与实际文件夹名不同
3. **CLI 版本过旧** — 某些版本的 obsidian-cli 有 vault 枚举 bug

## 诊断方法
```bash
# 检查 CLI 是否能找到 vault
/Applications/Obsidian.app/Contents/MacOS/obsidian-cli vaults 2>&1

# 检查 vault 文件夹是否存在（从 CONFIG 读取路径）
CONFIG_VAULT_PATH=$(get_vault_path)
ls "$CONFIG_VAULT_PATH" 2>/dev/null | head -5
```

## 解决方案

### 方案 A：先存本地，Obsidian 开了再导入
Cron 任务先写到本地文件系统（如 `$HERMES_SKILLS_WORKSPACE/`），等用户打开 Obsidian 后，手动或用 MCP 工具迁移进去。

### 方案 B：双重写入
Cron 任务同时写入本地文件 + Obsidian（Obsidian 失败不影响本地）。

### 方案 C：修复 vault 注册
确认 Obsidian 应用中 vault 的名称与 CLI 注册的一致。如果不一致，在 Obsidian 中重命名 vault 或更新 CLI 配置。

## 通用故障排查

| 症状 | 可能原因 | 排查步骤 |
|------|---------|---------|
| `Vault not found` | Obsidian 未启动 | `ps aux | grep -i obsidian` |
| `Vault not found` | Vault 名不匹配 | `obsidian-cli vaults` 对比 Obsidian 设置 |
| `CLI_TIMEOUT` | CLI 路径不对 | 检查 `/Applications/Obsidian.app/Contents/MacOS/obsidian-cli` 是否存在 |
| `CLI_TIMEOUT` | Integrated CLI 未启用 | 在 Obsidian 设置中确认已开启 |