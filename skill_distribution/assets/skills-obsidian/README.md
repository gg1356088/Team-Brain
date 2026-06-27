# Obsidian 技能分发包

## 概述

这是从 Hermes Agent 实际生产环境中提炼的 Obsidian 相关技能集合，已去除所有个人硬编码路径和敏感信息，可供其他企业或个人直接使用。

## 包含的技能

| 技能 | 说明 | 适用场景 |
|------|------|---------|
| `obsidian` | 通用 Obsidian vault 操作技能 | 文件系统级别的笔记读写、搜索、创建 |
| `knowledge-base` | 通用知识库协作技能 | Karpathy LLM Wiki 方法论实践 |
| `hermes-setup` | Hermes 配置审计与模型切换 | 配置验证、环境搭建 |
| `multi-agent-dispatch` | 多AI调度系统 | 任务拆解、AI子代理调度 |
| `dispatch-with-context` | 调度与验收规范 | 确保子任务有完整背景 |

## 安装方式

```bash
# 1. 克隆或解压到 skills 目录
cp -r skills-obsidian/* ~/.hermes/skills/

# 2. 配置 vault 路径（两种方式选一）
# 方式A：设置环境变量
export OBSIDIAN_VAULT_PATH="/path/to/your/vault"

# 方式B：创建用户配置文件
mkdir -p ~/.hermes/skills/obsidian/references/
cat > ~/.hermes/skills/obsidian/references/user-vault-path.md << 'EOF'
# User's Obsidian Vault Path
## Vault
- **Path**: /path/to/your/vault
- **Name**: your-vault-name
- **Platform**: macos | linux | windows
EOF
```

## 架构说明

```
obsidian (基础操作)
  └── knowledge-base (知识库方法论，依赖 obsidian 的路径解析)
    └── xinban-kb (个人定制版，可选)

multi-agent-dispatch (调度系统)
  └── 依赖 obsidian/knowledge-base 进行知识库访问
  
dispatch-with-context (调度规范)
  └── 独立使用，配合 multi-agent-dispatch
  
hermes-setup (环境配置)
  └── 独立使用
```

## 已去除的硬编码

- ❌ `/Users/xinban/obsidian知识内容库` → ✅ `OBSIDIAN_VAULT_PATH` 环境变量
- ❌ 用户 sudo 密码 → ✅ 提示按系统操作
- ❌ 个人工作区路径 → ✅ `$HERMES_WORKSPACE` 环境变量
- ❌ 个人 Obsidian 笔记路径 → ✅ 按用户 vault 结构可变

## 注意事项

1. **Obsidian CLI 需要先安装**：`/Applications/Obsidian.app/Contents/MacOS/obsidian-cli`（macOS）
2. **Integrated CLI 需要在 Obsidian 设置中启用**
3. **MCP 工具访问 vault** 比文件系统工具更安全，推荐使用
4. `knowledge-base` 是通用的 Karpathy LLM Wiki 方法论，不依赖特定 vault 结构
