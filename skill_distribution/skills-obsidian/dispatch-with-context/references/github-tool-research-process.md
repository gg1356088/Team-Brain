# GitHub 工具调研标准流程

> 每次调研工具时的标准操作，避免遗漏步骤。

## 流程

### 1. 用 GitHub API 搜索（不是浏览器）
```bash
curl -s "https://api.github.com/search/repositories?q=关键词&sort=stars&per_page=10" | python3 -c "..."
```
- 三个关键词变体都要搜（比如 `pdf extraction`、`pdf parse`、`pdf split`）
- 按 stars 排序，取前 10
- **不要只用浏览器搜** — 看不到精确的星标数和 API 数据

### 2. 抓 README 原文
```bash
curl -sL "https://raw.githubusercontent.com/OWNER/REPO/main/README.md" | head -50
```
- 对每个领域 Top 3 都抓
- 不要只看标题和描述，README 才有安装方式和具体能力

### 3. 检查当前环境
```bash
python3 --version
python3 -c "import markitdown; print('version:', markitdown.__version__)" 2>/dev/null || echo "未安装"
pip3 list 2>/dev/null | grep -iE "关键包名"
```
- **不要假设环境状态** — 之前我说 Python 3.11，实际是 3.9.6
- 不要假设包已安装 — 要实际查

### 4. 对比报告必须包含
- 每个工具对现有技能的"补充/替代关系"
- 安装方式
- Python 兼容性
- CLI / MCP Server 支持
- 成本（免费/需 API Key）

## 验收清单
- [ ] 步骤1：三个领域各搜 10 个结果，完整输出
- [ ] 步骤2：每个领域 Top 3+ 的 README 前 50 行
- [ ] 步骤3：环境检查完整输出（包括实际 Python 版本，不要假设）
- [ ] 步骤4：每个工具都有"对现有技能的补充/替代关系"

## 常见陷阱
- **假设 Python 版本**：说 3.11 实际 3.9.6，导致很多工具装不上
- **假设包已安装**：markitdown/marker 可能没装，要先验证
- **只抓结论不抓过程**：结论再漂亮，步骤没跑完就是不合格
- **用浏览器搜 GitHub**：看不到 API 级别的数据，容易被标题误导
- **用子 agent 调度**：子 agent 拿不到终端权限，调不了 Claude Code CLI
- **文件丢根目录**：临时文件必须放 HermesPet_Workspace
