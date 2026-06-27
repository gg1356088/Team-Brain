---
name: hermes-setup
description: "Hermes Agent 配置验证、模型切换与 provider 依赖关系。覆盖 config 审计、主模型切换对辅助服务的影响、TTS/STT 免费本地方案。"
version: 1.0.0
author: agent
created_by: agent
---

# Hermes Setup — 配置审计与模型切换

## 触发条件
- 用户要求验证当前配置
- 切换主模型（deepseek ↔ agnes ↔ 其他）
- 图片生成或识别突然不可用
- TTS/STT 报错
- 用户问"现在用的是什么模型"

## 核心原则：配置验证必须先看再说的

永远不要说"现在配置是 X"除非刚刚读过配置文件。凭记忆说的配置状态经常是过时的——用户可能用 Codex 或其他方式改过。

```bash
# 快速验证
cat ~/.hermes/config.yaml | head -30   # 看 model 段
hermes config get model.provider        # 当前 provider
hermes config get model.default         # 当前模型
hermes config get tools.image_gen       # 图片生成配置
hermes config get auxiliary_models      # 辅助模型配置
```

## 关键依赖关系（踩坑经验）

### 图片生成依赖 model.api_key

`image_gen/agnes` 插件从 `model.api_key` 读取 API key，不是从环境变量或 .env 读取。

```python
# 插件代码逻辑（plugins/image_gen/agnes/__init__.py）
cfg = _load_model_config()        # → 读 config.yaml 的 model 段
api_key = cfg.get("api_key")      # → 取 model.api_key
```

**含义**：如果主模型从 agnes 切换到其他 provider（如 deepseek），`model.api_key` 经常被清空或替换为其他 provider 的 key。图片生成会直接失效。

**修复**：
```bash
# 设置 Agnes API key 用于图片生成
hermes config set model.api_key <AGNES_API_KEY>
hermes config set image_gen.provider agnes
hermes config set image_gen.model flux-schnell
```

### 辅助模型 vision 需要自己的 api_key

`auxiliary_models.vision` 和 `auxiliary.vision` 使用独立的 provider 配置：
```yaml
auxiliary:
  vision:
    provider: agnes
    model: agnes-2.0-flash-vision
    api_key: sk-48H...     # ← 必须设置！空了 vision_analyze 工具不加载

auxiliary_models:
  vision:
    provider: agnes
    model: agnes-2.0-flash-vision  # ← 不要加 agentic/ 前缀
```

即使主模型是 deepseek，vision 辅助模型仍然走 Agnes。**但前提是 `auxiliary.vision.api_key` 非空**——空了 Hermes 会静默跳过 vision 工具的加载，不会报错。

踩坑：`auxiliary.vision.api_key` 和 `auxiliary_models.vision.model` 两处必须和对面的段一致（双重结构）。model 字段别加 `agentic/` 前缀——那是底部 auxiliary_models 段的历史残留。

### 图片生成配置位置

```yaml
# config.yaml 中的相关位置
tools:
  image_gen:
    provider: agnes          # ← 决定用哪个插件

plugins:
  enabled:
    - image_gen/agnes        # ← 必须启用

image_gen:
  provider: agnes
  model: flux-schnell        # ← 可用模型列表见插件代码
```

Agnes 图片生成插件支持模型：`agnes-image-2.1-flash`（默认）、`flux-schnell`。

## TTS / STT 免费本地方案

### 推荐配置
```bash
hermes config set tts.provider auto
hermes config set stt.provider auto
```

Auto 检测逻辑：
- **STT**：优先 `faster-whisper`（本地免费），pip install faster-whisper
- **TTS**：默认 `Edge TTS`（微软免费 TTS），无需 API key
- **备选 TTS**：`NeuTTS`（本地），pip install neutts[all] + espeak-ng

### 常见错误
- `provider: openai` 但没配 OpenAI base_url/api_key → 切到 auto
- 不要手动指定 edge/local，auto 会自行检测可用方案

## 模型切换检查清单

切换主模型前，逐项确认：

1. 图片生成还能用吗？（model.api_key 是否还是 Agnes 的 key）
2. 辅助模型 vision 还在吗？（检查 auxiliary.vision.api_key 非空，auxiliary_models.vision.model 不要带 agentic/ 前缀，两段一致）
3. TTS/STT 是 auto 吗？
4. 新模型需要额外的 api_key 吗？（检查 providers 段）

## 完整配置速览命令
```bash
# 一次性看全貌
echo "=== 主模型 ===" && hermes config get model
echo "=== 图片生成 ===" && hermes config get tools.image_gen && hermes config get image_gen
echo "=== 辅助模型 ===" && hermes config get auxiliary_models
echo "=== TTS/STT ===" && hermes config get tts && hermes config get stt
```

## 图片识别诚实规则

已写入 `~/.hermes/.soul.md` 的"图片识别诚实规则"段，每次对话自动加载：
- 不假装自己能看图
- 识别结果标注"这是辅助模型识别的结果"
- 识别失败直说不行
- 图片生成同理

详细规则见 `image-identification-behavior` 技能。

## 参考文件
- `references/agnes-image-gen-dependency.md` — Agnes 图片生成插件源码分析，model.api_key 依赖详解
- `references/vision-tool-debugging.md` — Vision 工具不加载的调试实录：api_key 为空 → 静默跳过
- `references/claude-code-local-proxy-debugging.md` — Claude Code 本地代理 ConnectionRefused 排查：端口 mismatch、gateway 双重启动冲突、端口换掉导致配置过期
- `references/feishu-gateway-setup.md` — 飞书 Gateway 接入全流程：.env 配置、白名单、主频道、cron 投递

## 已知平台差异

### macOS
- `hermes config` 命令直接可用
- .env 文件在 `~/.hermes/.env`
- npm 缓存权限问题可能需要 `sudo chown`（如遇权限问题，按系统提示操作）
- **Hermes Pet GUI 动画卡顿** — 已知问题，多次尝试修复无效。这是前端渲染性能限制，不是配置问题。如果用户反馈卡顿，告知这是已知问题，无法通过配置解决。

### Obsidian CLI 安装陷阱
- `npm install -g obsidian-cli` 装的是 **ObsidianQA** 测试工具，不是笔记 CLI。
- 官方 Obsidian Integrated CLI 路径：`/Applications/Obsidian.app/Contents/MacOS/obsidian-cli`
- 必须先打开 Obsidian 设置 → General → Advanced → 启用 "Integrated CLI"
- 第三方工具 `@safetnsr/cortex` 是无头 vault CLI，需 `npm run build` 编译后使用
- MCP 桥接工具 `@marwansaab/obsidian-cli-mcp` 用于 Claude Code 等 MCP 客户端连接 Obsidian

## 视频生成 API 行为

### Agnes Video V2.0
- 图生视频要求 `image_url` 必须是公网可访问 URL，不接受本地路径
- 如果传本地路径会报错 `requires publicly accessible http(s) image URLs`
- 纯文字生成（不传 image_url）可能第一次超时，重试通常能成
- API 超时重试一次是标准操作
- 涉及敏感内容（暴露衣物）大概率被安全策略拦截

## 文件输出位置惯例

生成的文件默认放在可见目录（如 `~/HermesPet_Workspace/` 或项目根目录），不要放在隐藏目录 `.hermes/cache/`。

> ⚠️ 此配置是个人偏好，分发时应移除或改为可配置项。用户可通过 `HERMES_OUTPUT_DIR` 环境变量自定义输出目录。

## Web 联网能力配置（踩坑记录）

**核心问题：** Hermes 内置了 8 个搜索后端插件（brave-free、ddgs、exa、firecrawl、parallel、searxng、tavily、xai），但 `config.yaml` 中 `web.backend` 和 `web.search_backend` 默认为空。插件已注册但**未指定使用哪个**——就像装了 8 个搜索引擎 App 但一个都没打开。

**症状：** `web_search` 工具不可用，cron 情报任务报 `⚠️ Skill(s) not found and skipped: web`。

**修复：**
```bash
# 方案1（免费无key）：使用 DuckDuckGo
hermes config set web.backend ddgs
hermes config set web.search_backend ddgs

# 方案2（更强搜索）：注册 Tavily（免费 1000次/月）或 Brave（免费 2000次/月）
# 在 ~/.hermes/.env 中添加 API key
# TAVILY_API_KEY=xxx
# BRAVE_API_KEY=xxx
hermes config set web.backend tavily
hermes config set web.search_backend tavily
```

**生效：** 配置后需要 `/reset` 重启会话才能加载 web_search 工具。

**验证：** 重启后可以用 `hermes tools list` 确认 `web` 工具集已启用，或直接让 agent 执行一次搜索验证。

## Cron 情报扫描

已配置 hourly cron job（`deliver=origin`）扫描 AI Agent、MCP、CLI工具、自动化、开源项目。规则：有料推一条，没料闭嘴。不要发"今日无重大变化"之类的内容。

## Cron 关键踩坑记录

### `repeat` 参数陷阱
`cronjob` 工具的 `repeat` 参数：`repeat=1` 表示只执行一次就消失，`repeat=0` 表示无限循环。创建 cron job 时如果希望循环执行，必须传 `repeat=0`（或省略让它默认）。传 `repeat=1` 会创建一次性任务然后自动删除。

### `deliver=origin` 投递失败
新创建的 cron job 可能因为 `deliver=origin` 解析不到投递目标而静默失败（`last_delivery_error: "no delivery target resolved"`）。确认投递目标（如 Telegram/Discord channel）已连接后再创建，或改用显式目标。

### 删除旧 cron 再创建新 cron
如果有旧 cron 处于 `enabled: false` 且投递失败的状态，不要试图 `update` 它（可能残留配置问题），直接 `remove` 旧的再 `create` 新的更干净。

### `enabled_toolsets` 限制缩小 token 消耗
创建 cron job 时指定 `enabled_toolsets: ["web", "search"]` 或 `["terminal", "web"]` 可以显著减少 token 消耗，比让 agent 加载所有默认工具更经济。情报扫描用 `["web", "search"]`，活动快照用 `["terminal", "web"]`。

## Claude Code API 余额不足
当调用 Claude Code 子进程时出现 `402 Insufficient Balance`，表示 API 账户余额不足。这不是 Hermes bug。
**处理方案：** 充值 API key 或切换 provider。不要花时间在 CLI 参数上排查。

## Scrapling 安装 — macOS pyobjc 编译失败
macOS 上 `pip install scrapling[all]` 会在 pyobjc-core 构建步骤失败，报错 `clang -Werror` 和 simd 初始化错误。这是 Apple clang 的 bug。
**处理方案：** 放弃 scrapling，改用 `pip3 install httpx beautifulsoup4 lxml`。轻量、零编译依赖，覆盖同样核心能力。

## 浏览器自动化 — Google 登录检测
Google Pages（Forms, Docs, Login）检测 CDP 自动化，会弹出"此浏览器或应用可能不安全"警告。CDP/Playwright 工具均受影响。
**处理方案：** 让用户手动登录其真实浏览器，之后 agent 接管后续步骤。

## Skill 安装来源与清理策略

从上游仓库（GitHub）抓取 Skill 时，常见的正确做法：

1. **先确认现有 umbrella**——`skill_view(name='multi-agent-dispatch')` 等现有 umbrella 是否已经覆盖了新 skill 的领域。如果覆盖了，优先 `patch` umbrella 而非新建独立 skill。
2. **独立 skill 的命名必须类级别**——不能是具体 PR 号、具体错误名、具体功能代号。gstack、caveman 这种具体方法论应归入 `software-development` umbrella 下的子路径（如 `software-development/gstack/`）。
3. **抓取后立即注册**——`write_file` 写入 SKILL.md 和 references/ 后，立刻 `skill_manage(action='create')` 注册，避免忘记。
4. **旧 Skill 的清理**——如果发现了更好或更合适的 Skill 覆盖了旧 Skill 的功能，`skill_manage(action='delete', absorbed_into='')` 删除旧 Skill。如果旧 Skill 内容合并到了 umbrella，用 `absorbed_into='umbrella-name'`。

### 常见安装流程模板

```bash
# 1. 从上游仓库抓取文件
curl -sL "https://raw.githubusercontent.com/USER/REPO/BRANCH/SKILL.md" -o /tmp/SKILL.md

# 2. 查看内容确认适用性
cat /tmp/SKILL.md

# 3. 写入本地 skill 目录
mkdir -p ~/.hermes/skills/<category>/<name>/references/

# 4. 注册
skill_manage(action='create', name='<name>', content='...')
```

### 不要做的事

- 不要为每个安装都创建独立 skill——考虑是否应归入 umbrella
- 不要安装后忘记注册——`write_file` 之后必须 `skill_manage`
- 不要假设上游 SKILL.md 直接兼容——Hermes 需要 YAML frontmatter（name, description, version），上游可能没有
- 不要安装已存在于 umbrella 下的 skill——先 `skill_view` 检查 umbrella 是否已有相关内容
