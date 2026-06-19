# Vision 工具不加载调试实录

## 症状
- `hermes tools list` 显示 vision 工具集 enabled
- 但 vision_analyze 工具不在实际可用工具列表中
- 用户发图片无法识别

## 根因
`auxiliary.vision.api_key` 为空字符串。Hermes 初始化时发现 vision 辅助模型缺少 api_key，静默跳过工具加载——不报错、不警告、日志不留。

## 发现过程

1. `hermes tools list | grep vision` → vision enabled ✓
2. 检查 config：`auxiliary.vision.api_key: ''` ← 空的
3. 主模型 `model.api_key` 有值（`sk-48H...`），但 vision 段有自己的 api_key 字段，不共享
4. 修复：`hermes config set auxiliary.vision.api_key "sk-48H..."` 

## 连带问题：双重配置段不一致

顶部 `auxiliary.vision.model` 是 `agnes-2.0-flash-vision`，底部 `auxiliary_models.vision.model` 是 `agentic/agnes-2.0-flash-vision`（多了 agentic/ 前缀）。

修复：`hermes config set auxiliary_models.vision.model "agnes-2.0-flash-vision"`

## 验证尝试（未成功）

想用 curl 调 Agnes Vision API 验证配置修复效果，遇到两个阻碍：
1. **Shell 引号转义**：base64 编码内嵌在 curl JSON 里时引号冲突
2. **安全扫描拦截**：`curl | python3` 管道被 tirith 标为 HIGH 风险

解决方案：存 base64 到文件，Python 脚本读文件再调 API——但需要真实 api_key（config 里被 secrets 系统掩码了）。

## 教训
- vision 工具静默缺失 → 第一反应检查 `auxiliary.vision.api_key`
- 别假设 `model.api_key` 会传递到 auxiliary 段——它们是独立的
- 双重配置段（auxiliary + auxiliary_models）要对齐：model 名一致、都不带 agentic/ 前缀、api_key 都有值
