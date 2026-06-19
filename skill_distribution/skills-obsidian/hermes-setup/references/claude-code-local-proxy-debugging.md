# Claude Code 本地代理调试

## 问题：ConnectionRefused

**症状：** Claude Code 报 `API Error: Unable to connect to API (ConnectionRefused)`

**根因：** Claude Code settings.json 的 `ANTHROPIC_BASE_URL` 指向本地代理端口（如 `127.0.0.1:15722`），但该端口未监听。

## 排查步骤

### 1. 看 Claude Code 配置

```bash
cat ~/.claude/settings.json | grep ANTHROPIC_BASE_URL
```

记录 Base URL 指向的端口。

### 2. 检查端口是否在监听

```bash
lsof -i :<PORT>
# 如果无输出 → 端口未监听，这就是原因
```

### 3. 检查实际监听端口

```bash
lsof -iTCP -sTCP:LISTEN -P -n | grep python
# 看 python 进程监听了哪个端口
```

**常见情况：** Hermes gateway 可能从 15722 换到了 8642（或反之），导致 Claude Code 配置过期。

### 4. 查日志

```bash
# Gateway 日志
tail -30 ~/.hermes/logs/gateway.error.log
# 常见错误：
# - "Another gateway instance started during our startup" → 双重启动冲突
# - "Shutdown context: signal=SIGTERM" → 进程被终止
```

### 5. 修复

- **改 Claude Code 配置**：更新 `ANTHROPIC_BASE_URL` 到正确端口
- **或重启 gateway**：`pkill -f "hermes_cli.main gateway"` 然后重新拉起来
- **或直接绕过代理**：改回直连 API（如 `https://api.deepseek.com/anthropic`）

## 常见坑

- Gateway 双重启动会导致两个实例互相杀死对方 → 端口全挂
- Claude Code 的 settings.json 改完后**必须重启**才生效
- Claude Code 用 `ANTHROPIC_BASE_URL` 覆盖默认 API endpoint，不是 `OPENAI_BASE_URL`
- DeepSeek 有 400 错误（thinking disabled + reasoning_effort 冲突），需要本地 proxy 过滤
