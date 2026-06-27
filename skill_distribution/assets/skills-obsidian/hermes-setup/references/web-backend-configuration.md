# Web 联网能力配置排查

## 症状
- `web_search` 工具不可用
- cron 情报任务报 `⚠️ Skill(s) not found and skipped: web`

## 根因
Hermes Agent 内置了 8 个搜索后端插件（brave-free、ddgs、exa、firecrawl、parallel、searxng、tavily、xai），但 `config.yaml` 中 `web.backend` 和 `web.search_backend` 默认为空。

## 修复
```bash
hermes config set web.backend ddgs
hermes config set web.search_backend ddgs
```
然后 `/reset` 重启会话。

## 验证
用 `hermes tools list` 确认 `web` 工具集已启用。