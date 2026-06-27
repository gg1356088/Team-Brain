# Hermes 技能跨企业分发方案

> 2026-06-17 制定

## 一、问题本质

技能做出来了，但别人装不上。根因不是技能本身不行，是**环境绑定太紧**：

| 硬编码项 | 例子 | 别人的环境 |
|---------|------|-----------|
| 用户路径 | `/Users/xinban/HermesPet_Workspace/` | `/home/user/workspace/` 或 `D:\workspace\` |
| API Key | 你的飞书 bot、Anthropic key | 他们的 key |
| 工具路径 | Claude Code 在 PATH 中 | 可能在别处 |
| 操作系统 | macOS | Windows/Linux |

## 二、推荐方案：GitHub 仓库 + 模板化 + 一键安装

### 2.1 仓库结构

```
hermes-skills/                    ← GitHub 仓库根目录
├── README.md                     ← 仓库说明 + 快速开始
├── install.sh                    ← 一键安装脚本（Linux/macOS）
├── install.ps1                   ← Windows 安装脚本
├── .env.example                  ← 环境变量模板
├── skills/                       ← 技能包
│   ├── loop-dispatch/
│   │   ├── SKILL.md              ← 技能定义（Hermes 格式）
│   │   ├── loop_dispatch.py      ← 调度器
│   │   ├── loop_monitor.py       ← 监控器
│   │   └── templates/
│   │       └── config.template.json  ← 配置模板
│   ├── invoice-automation/
│   │   ├── SKILL.md
│   │   ├── invoice_processor.py
│   │   └── templates/
│   │       └── config.template.json
│   └── supervisor/
│       ├── SKILL.md
│       ├── supervisor.py
│       └── templates/
│           └── config.template.json
└── docs/
    ├── quick-start.md            ← 5 分钟上手指南
    ├── config-guide.md           ← 配置详解
    └── troubleshooting.md        ← 常见问题
```

### 2.2 核心设计原则

**原则 1：零硬编码**
- 所有路径用环境变量或配置文件
- 不写死 `/Users/xinban/` 这类路径
- 用 `$HOME` 或 `~` 代替

**原则 2：配置模板化**
- 每个技能带一个 `config.template.json`
- 安装时复制成 `config.json`，用户填自己的值
- 敏感信息（API Key）不进代码仓库

**原则 3：安装脚本自动检测**
- 检测 Claude Code / Codex / lark-cli 是否安装
- 自动创建目录结构
- 自动复制配置文件模板

## 三、具体实施方案

### 3.1 改造现有技能（以 loop-dispatch 为例）

#### 第一步：移除硬编码路径

**修改前（loop_dispatch.py）：**
```python
BASE_DIR = Path("/Users/xinban/HermesPet_Workspace/loop_dispatch")
FEISHU_CHAT_ID = "oc_2f807f2775060ad77f6875f278be44d4"
```

**修改后：**
```python
import os
from pathlib import Path

# 从环境变量读取，有默认值
BASE_DIR = Path(os.environ.get("HERMES_SKILLS_WORKSPACE", str(Path.home() / "HermesWorkspaces")))
TASK_DIR = BASE_DIR / "loop_dispatch" / "tasks"
FEISHU_CHAT_ID = os.environ.get("FEISHU_CHAT_ID", "")
```

#### 第二步：创建配置模板

```json
{
    "feishu": {
        "chat_id": "填写你的飞书群ID",
        "bot_token": "${FEISHU_BOT_TOKEN}"
    },
    "workers": {
        "claude_cmd": "claude",
        "codex_cmd": "/Applications/Codex.app/Contents/Resources/codex"
    },
    "workspace": {
        "base_dir": "~/.hermes-skills/workspace"
    }
}
```

#### 第三步：创建安装脚本

```bash
#!/bin/bash
# install.sh — 一键安装 Hermes Skills

set -e

echo "🔧 正在安装 Hermes Skills..."

# 1. 确定安装目录
INSTALL_DIR="${HOME}/.hermes-skills"
mkdir -p "$INSTALL_DIR"

# 2. 复制技能文件
echo "📦 复制技能文件..."
cp -r skills/* "$INSTALL_DIR/"

# 3. 创建配置文件
echo "⚙️  创建配置文件..."
cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
echo "   请编辑 $INSTALL_DIR/.env 填入你的 API Key 和配置"

# 4. 检测依赖
echo "🔍 检测依赖..."
if command -v claude &> /dev/null; then
    echo "   ✅ Claude Code 已安装"
else
    echo "   ⚠️  Claude Code 未安装（可选）"
fi

if command -v codex &> /dev/null; then
    echo "   ✅ Codex 已安装"
else
    echo "   ⚠️  Codex 未安装（可选）"
fi

if command -v lark-cli &> /dev/null; then
    echo "   ✅ lark-cli 已安装"
else
    echo "   ⚠️  lark-cli 未安装（飞书通知不可用）"
fi

# 5. 提示用户
echo ""
echo "✅ 安装完成！"
echo "📝 下一步："
echo "   1. 编辑 $INSTALL_DIR/.env 填入配置"
echo "   2. 将技能链接到 Hermes："
echo "      ln -s $INSTALL_DIR/skills ~/.hermes/skills/"
echo ""
echo "📖 详细文档：docs/quick-start.md"
```

### 3.2 用户安装流程（5 分钟上手）

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/hermes-skills.git
cd hermes-skills

# 2. 运行安装脚本
chmod +x install.sh
./install.sh

# 3. 编辑配置
nano ~/.hermes-skills/.env
# 填入：FEISHU_CHAT_ID, FEISHU_BOT_TOKEN 等

# 4. 链接到 Hermes
ln -sf ~/.hermes-skills/skills ~/.hermes/skills/

# 5. 测试
python3 ~/.hermes-skills/loop_dispatch.py help
```

## 四、分发渠道对比

| 方式 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **GitHub 仓库** | 版本管理、issue 反馈、fork 定制 | 需要懂 git | ⭐⭐⭐⭐⭐ |
| zip 包下载 | 不需要 git | 没法更新、没法提 PR | ⭐⭐⭐ |
| pip 包 | 自动安装、版本管理 | Python 技能不适合打包成 pip | ⭐⭐ |
| Docker 镜像 | 环境隔离 | 太重，不适合 Hermes 技能 | ⭐ |

**推荐：GitHub 仓库为主 + release 附 zip 包。**

## 五、技能打包成可分发的格式

每个技能目录应该包含：

```
skill-name/
├── SKILL.md              ← Hermes 技能定义（必填）
├── *.py                  ← Python 脚本（可选）
├── templates/
│   └── config.template.json  ← 配置模板（必填）
├── .env.example          ← 环境变量模板（必填）
└── README.md             ← 技能使用说明（推荐）
```

## 六、配置适配策略

### 6.1 环境变量优先

```python
# 所有配置项通过环境变量注入
FEISHU_CHAT_ID = os.environ.get("FEISHU_CHAT_ID", "")
FEISHU_BOT_TOKEN = os.environ.get("FEISHU_BOT_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
```

### 6.2 配置文件兜底

```python
import json
from pathlib import Path

config_file = Path(os.environ.get("HERMES_CONFIG", str(Path.home() / ".hermes-skills" / "config.json")))
if config_file.exists():
    with open(config_file) as f:
        config = json.load(f)
    # 环境变量优先级高于配置文件
    FEISHU_CHAT_ID = os.environ.get("FEISHU_CHAT_ID", config.get("feishu", {}).get("chat_id", ""))
```

### 6.3 敏感信息不进仓库

`.env` 文件加入 `.gitignore`，只提交 `.env.example`：

```gitignore
# .gitignore
.env
config.json
*.pid
*.log
```

## 七、推荐的完整技能包

把目前所有技能打包成一个可分发的仓库：

| 技能 | 说明 | 依赖 |
|------|------|------|
| loop-dispatch | LOOP 调度系统 | claude, codex, lark-cli |
| invoice-automation | 发票自动化处理 | pdfplumber, openpyxl |
| supervisor | 监督系统 | lark-cli |

打包后用户只需要：
1. 安装 Python 3.9+
2. 安装需要的 CLI 工具（claude/codex/lark-cli）
3. 跑安装脚本
4. 填配置

## 八、实施计划

1. **本周**：改造 loop-dispatch，移除硬编码，加配置模板
2. **下周**：打包成 GitHub 仓库，写安装脚本和文档
3. **后续**：陆续改造其他技能（invoice-automation 等）
