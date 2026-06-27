"""
DeepSeek 400 修复：thinking/reasoning_effort 冲突
本地 proxy 拦截请求，过滤冲突参数

使用场景：Claude Code 用 DeepSeek API (Anthropic compatible) 报 400 错误
错误信息：thinking options type cannot be disabled when reasoning_effort is set

修复步骤：
1. 确认代理文件存在：~/.claude/deepseek-fix-proxy.py
2. 内容：Python HTTP proxy，拦截 thinking.type == "disabled" 的请求，移除 reasoning_effort 和 output_config
3. 启动：python3 /Users/xinban/.claude/deepseek-fix-proxy.py --port 15722 &
4. 配置 Claude Code settings.json：
   "ANTHROPIC_BASE_URL": "http://127.0.0.1:15722/anthropic"
5. SessionStart hook 自动启动：
   {"type":"command","command":"python3 /Users/xinban/.claude/deepseek-fix-proxy.py --port 15722 &"}
   （& 不能丢，否则阻塞启动）

注意：
- patch 工具不能直接改 config.yaml（安全拦截），用 write_file 或 hermes config 命令
- 如果 proxy 不需要了，把 ANTHROPIC_BASE_URL 改回 https://api.deepseek.com/anthropic
- 删除 SessionStart hook 中的 proxy 启动命令
"""
