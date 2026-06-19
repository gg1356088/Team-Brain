#!/bin/bash
# install.sh — 一键安装 Hermes Skills（loop-dispatch）
#
# 用法：chmod +x install.sh && ./install.sh

set -e

echo "🔧 正在安装 Hermes Skills (loop-dispatch)..."
echo ""

# 1. 确定安装目录
INSTALL_DIR="${HERMES_SKILLS_WORKSPACE:-$HOME/HermesWorkspaces}"
SKILL_DIR="$INSTALL_DIR/loop_dispatch"

echo "📦 安装目录: $INSTALL_DIR"

# 2. 创建目录结构
mkdir -p "$SKILL_DIR/tasks"
mkdir -p "$SKILL_DIR/.hermes/skills/loop-dispatch"

# 3. 复制技能文件（从脚本所在目录复制）
echo "📋 复制技能文件..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cp "$SCRIPT_DIR/loop-dispatch/config.py" "$SKILL_DIR/" 2>/dev/null || echo "   ⚠️  config.py 未找到"
cp "$SCRIPT_DIR/loop-dispatch/loop_dispatch.py" "$SKILL_DIR/" 2>/dev/null || echo "   ⚠️  loop_dispatch.py 未找到"
cp "$SCRIPT_DIR/loop-dispatch/loop_monitor.py" "$SKILL_DIR/" 2>/dev/null || echo "   ⚠️  loop_monitor.py 未找到"
cp "$SCRIPT_DIR/loop-dispatch/SKILL.md" "$SKILL_DIR/.hermes/skills/loop-dispatch/" 2>/dev/null || echo "   ⚠️  SKILL.md 未找到"

# 4. 创建配置文件
echo "⚙️  创建配置文件..."
ENV_FILE="$INSTALL_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    cp "$SCRIPT_DIR/loop-dispatch/.env.example" "$ENV_FILE"
    echo "   已创建 $ENV_FILE，请编辑填入你的 API Key"
else
    echo "   配置文件 $ENV_FILE 已存在，跳过"
fi

# 5. 检测依赖
echo ""
echo "🔍 检测依赖..."
if command -v claude &> /dev/null; then
    echo "   ✅ Claude Code: $(claude --version 2>&1 | head -1)"
else
    echo "   ⚠️  Claude Code 未安装（可选）"
fi

if [ -f "/Applications/Codex.app/Contents/Resources/codex" ]; then
    echo "   ✅ Codex 已安装"
elif command -v codex &> /dev/null; then
    echo "   ✅ Codex: $(codex --version 2>&1 | head -1)"
else
    echo "   ⚠️  Codex 未安装（可选）"
fi

if command -v lark-cli &> /dev/null; then
    echo "   ✅ lark-cli 已安装"
else
    echo "   ⚠️  lark-cli 未安装（飞书通知不可用）"
fi

# 6. 链接到 Hermes
echo ""
echo "🔗 链接到 Hermes..."
HERMES_SKILLS_DIR="$HOME/.hermes/skills"
mkdir -p "$HERMES_SKILLS_DIR"

LINK_TARGET="$SKILL_DIR/.hermes/skills/loop-dispatch"
LINK_DEST="$HERMES_SKILLS_DIR/loop-dispatch"

if [ -L "$LINK_DEST" ]; then
    # 已有符号链接
    CURRENT_TARGET=$(readlink "$LINK_DEST")
    if [ "$CURRENT_TARGET" = "$LINK_TARGET" ]; then
        echo "   ℹ️  链接已存在且正确，跳过"
    else
        echo "   🔗 更新链接: $LINK_DEST -> $LINK_TARGET"
        rm -rf "$LINK_DEST"
        ln -sf "$LINK_TARGET" "$LINK_DEST"
        echo "   ✅ 链接已更新"
    fi
elif [ -d "$LINK_DEST" ]; then
    echo "   ⚠️  $LINK_DEST 是一个目录（可能是旧版本）"
    echo "   ℹ️  正在迁移为符号链接..."
    BACKUP="$LINK_DEST.bak.$(date +%Y%m%d%H%M%S)"
    echo "   备份到: $BACKUP"
    mv "$LINK_DEST" "$BACKUP"
    ln -sf "$LINK_TARGET" "$LINK_DEST"
    echo "   ✅ 已迁移为符号链接"
    echo "   💡 旧版本已备份，可安全删除: rm -rf $BACKUP"
elif [ -e "$LINK_DEST" ]; then
    echo "   ⚠️  $LINK_DEST 存在但不是目录或链接，请先清理"
    echo "      运行: rm -rf $LINK_DEST"
else
    ln -sf "$LINK_TARGET" "$LINK_DEST"
    echo "   ✅ 已链接到 $LINK_DEST"
fi

# 7. 完成
echo ""
echo "✅ 安装完成！"
echo ""
echo "📝 下一步："
echo "   1. 编辑 $ENV_FILE 填入配置（FEISHU_CHAT_ID 等）"
echo "   2. 测试调度器："
echo "      cd $SKILL_DIR && python3 loop_dispatch.py help"
echo ""
echo "📖 详细文档：见 loop-dispatch/SKILL.md"
