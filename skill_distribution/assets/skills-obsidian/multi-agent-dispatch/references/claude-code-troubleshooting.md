# Claude Code 子进程调度常见问题与修复

## ConnectionRefused —— BASE_URL 端口漂移

**症状：** Claude Code 报错 `API Error: Unable to connect to API (ConnectionRefused)`，发生在改脚本/跑任务时。

**根因：** Claude Code 的 `ANTHROPIC_BASE_URL` 指向的本地端口（代理/gateway）挂了或换了端口。

**诊断步骤：**
1. 查看 Claude Code 配置里的 BASE_URL：`~/.claude/settings.json` → `env.ANTHROPIC_BASE_URL`
2. 检查端口是否在监听：`lsof -i :<PORT>`
3. 如果端口没监听，说明代理/gateway 进程挂了

**修复方案（二选一）：**

**A. 本地代理方案（推荐，解决 400 thinking/reasoning 冲突）：**
1. 部署 proxy 脚本（见 `deepseek-fix-proxy.py` 模板）
2. 改 `ANTHROPIC_BASE_URL` 为 `http://127.0.0.1:<PORT>/anthropic`
3. 加 SessionStart hook 自动启动 proxy：`"command": "python3 /path/to/deepseek-fix-proxy.py --port <PORT> &"`
4. 注意 `&` 不能丢，否则阻塞启动

**B. 直连上游 API：**
- 改回 `ANTHROPIC_BASE_URL` 指向直连地址（如 `https://api.deepseek.com/anthropic`）

**预防措施：**
- 启动 Claude Code 前先确认端口监听：`lsof -i :15722`
- proxy 脚本放在 `.claude/` 目录下，随项目一起管理

## Gateway 端口变化

**症状：** Hermes gateway 进程在但端口不监听，Claude Code 报 ConnectionRefused。

**诊断：** `lsof -iTCP -sTCP:LISTEN -P -n | grep python` 查看所有 Python 监听的端口。

**注意：** Hermes gateway 端口可能随版本或配置变化，不要硬编码在 Claude Code 配置里。

## Patch 工具不能修改 Hermes config.yaml

**症状：** `patch` 工具报错 `Refusing to write to Hermes config file`。

**原因：** `~/.hermes/config.yaml` 是安全文件，`patch` 工具拒绝写入。

**正确做法：**
- 用 `hermes config show/edit/set` 命令
- 或手动编辑 `~/.hermes/config.yaml`
- 不要尝试用 patch/execute_code/write_file 直接改

## 常见权限/联网问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `Insufficient Balance` (402) | API 余额不足 | 充值 key 或切换 provider |
| `web_search` 工具不可用 | 子进程无 Hermes 工具 | 用 `curl` 或 `browser_navigate` 代替 |
| Claude Code 不能联网 | `web_fetch`/`web_search` 权限未批准 | 在 `~/.claude/settings.json` 的 `permissions.allow` 添加 |
| Security scan 拦截 | prompt 混用 URL 和中文字符 | prompt 中 URL 和中文字符分开 |

## 参考文件

- Claude Code 代理脚本模板见 skill 目录（`deepseek-fix-proxy.py` 的变体可用于任何需要参数过滤的场景）
