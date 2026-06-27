# 技能分发模式（2026-06-18 更新）

## 背景

自建技能直接给别人用不了——路径硬编码、API Key 暴露、工具版本不匹配。需要一套标准流程让技能可分发。

## 分发目录结构

```
skill_distribution/
├── README.md                    # 使用说明
├── install.sh                   # 一键安装脚本
├── .gitignore                   # 防止敏感文件泄露
└── loop-dispatch/
    ├── loop_dispatch.py         # 去硬编码版
    ├── loop_monitor.py          # 去硬编码版
    ├── SKILL.md                 # 技能说明
    ├── .env.example             # 环境变量模板
    └── templates/
        └── config.template.json # 配置模板
```

## 核心原则

1. **配置模板化** — 所有路径、API Key、Chat ID 移到 `.env` + `config.json`
2. **一键安装** — `install.sh` 自动检测路径、创建 `.env`、设置权限
3. **版本解耦** — README 写明所需最低版本
4. **文档先行** — README 写清楚"是什么、怎么用、出了问题怎么办"

## install.sh 编写要点

1. 用 `$(dirname "$0")` 定位脚本目录（不是假设相对路径）
2. 检测依赖（claude、codex、lark-cli）
3. 创建 `.env` 模板（不自动写入密钥）
4. 处理旧版本目录迁移：
   - 已有符号链接 → 检查目标是否一致
   - 是目录 → 备份为 `.bak.TIMESTAMP` + 重链为符号链接
   - 不存在 → 创建新链接
5. 验证 Python 语法（`python3 -m py_compile`）

## 配置模板

### .env.example — 只留实际生效的字段

```bash
FEISHU_CHAT_ID=填写你的飞书群ID
# CLAUDE_CMD=claude  （可选，默认值在代码里）
# CODEX_CMD=...      （可选，默认值在代码里）
```

**关键：不要留代码不读取的字段！** 比如 `feishu.bot_token`（通知走 lark-cli 不需要 token），`workspace.base_dir`（代码用 `$HERMES_SKILLS_WORKSPACE` 环境变量）。

### config.template.json — 同上

```json
{
    "feishu": { "chat_id": "oc_xxxxx" },
    "workers": {
        "claude_cmd": "claude",
        "codex_cmd": "/Applications/Codex.app/Contents/Resources/codex"
    }
}
```

## 去硬编码检查清单

- [ ] 所有路径通过 `CONFIG["workspace"]` 或环境变量读取
- [ ] 飞书 Chat ID 不硬编码
- [ ] Claude/Codex 路径不硬编码（用环境变量或 config.json）
- [ ] prompt 中的输出目录用 `{workspace}` 变量而非固定路径
- [ ] 不引用不存在的文件（如 supervisor.py）

## 修复流程（双Agent审查模式）

1. **第一轮**：派 Claude Code 全面审查（代码结构、逻辑、边界、安全性）
2. **第二轮**：派 Codex 从不同侧重点审查（用户体验、安装脚本、配置一致性）
3. **分级修复**：P0（阻断）→ P1（重要）→ P2（体验）
4. **验证**：`python3 -m py_compile` + `bash install.sh` 实测
5. **同步**：修复后的文件同步回本地版本

## Pitfalls

- 不要直接发源代码给别人——硬编码的路径和密钥会泄露
- install.sh 不要自动写入密钥——让用户手动填 `.env`
- 配置模板字段必须和代码实际读取的一致，多余的字段会让用户困惑
- install.sh 中 `rm -rf` 不能写成 `rm -f`，后者无法删除目录
- 技能目录迁移：旧版本可能是普通目录而非符号链接，需要先备份再创建链接
- `.gitignore` 必须包含 `.env`、`*.pid`、`*.log`、`tasks/`，防止运行时文件被提交
- `SKILL.md` 不要引用不存在的文件（如 supervisor.py），会误导用户

## 分发载体选择

| 方式 | 适用场景 |
|------|---------|
| GitHub 私有仓库 | 企业内部团队，需要版本控制和 PR 评审 |
| zip 打包 | 外部客户/非技术用户，零门槛 |
| 直接发文件 | 临时共享，极易遗漏更新 |

**推荐：GitHub 私有仓库 + install.sh + README**
