# 飞书 Gateway 接入 — 完整配置流程

## 前提

- 飞书开放平台已创建企业自建应用，开启机器人能力
- 已获取 `App ID` 和 `App Secret`
- `lark-oapi` Python 包已安装（`pip install lark-oapi`）

## .env 配置

```bash
# ~/.hermes/.env
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxx
FEISHU_CONNECTION_MODE=websocket   # 推荐 websocket，无需公网回调 URL
```

gateway 启动时会自动检测 `.env` 中的 `FEISHU_APP_ID` + `FEISHU_APP_SECRET`，两者都有就自动启用飞书平台。

## 用户白名单

网关能收到消息，但默认所有用户都是 unauthorized。必须把用户 open_id 加入白名单：

```bash
# 从网关日志找 open_id：
# WARNING gateway.run: Unauthorized user: ou_xxxxxxxxxxxx (None) on feishu
echo 'FEISHU_ALLOWED_USERS=ou_xxxxxxxxxxxx' >> ~/.hermes/.env
```

多个用户用逗号分隔。

## 主频道设置

飞书要求设置主频道（home channel），否则 cron 任务结果无处投递，发给用户的消息也无目标。

### 方式一：用户在飞书里发 `/sethome`

机器人收到 `/sethome` 后会自动记录当前 chat 为主频道，之后所有 cron 投递和主动消息都发到这里。

### 方式二：手动设置环境变量

```bash
# 从网关日志找 chat_id：
# [Feishu] Inbound dm message received: ... chat_id=oc_xxxxxxxxxxxx
echo 'FEISHU_HOME_CHANNEL=oc_xxxxxxxxxxxx' >> ~/.hermes/.env
echo 'FEISHU_HOME_CHANNEL_NAME=My Hermes' >> ~/.hermes/.env
```

## 启动 / 重启网关

修改 `.env` 后必须重启网关才能生效：

```bash
# 先杀掉旧进程
pkill -f "hermes.*gateway run"

# 重启
cd ~/.hermes/hermes-agent && . venv/bin/activate && \
  hermes gateway run --replace > ~/.hermes/logs/gateway.log 2>&1 &
```

## 验证

查看网关日志确认飞书已连接：

```bash
grep -i feishu ~/.hermes/logs/gateway.log | tail -5
```

成功标志：`✓ feishu connected` + websocket 连接成功。

## Cron 投递到飞书

主频道设好后，将 cron 任务的 `deliver` 改为 `feishu`：

```bash
cronjob action=update job_id=xxxx deliver=feishu
```

之前 `deliver=origin` 会因为 "no delivery target resolved" 静默失败——飞书主频道就解决了这个问题。

## 常见故障

| 症状 | 原因 | 修复 |
|------|------|------|
| 消息能收到但回复不了 | 用户 open_id 不在白名单 | 加 `FEISHU_ALLOWED_USERS` |
| 提示"飞书尚未设置主频道" | 未设 home channel | 用户发 `/sethome` 或设 `FEISHU_HOME_CHANNEL` |
| 网关日志没有 feishu | `.env` 缺少凭证或未重启 | 检查 `FEISHU_APP_ID` + `FEISHU_APP_SECRET`，重启网关 |
| cron 投递报 "no delivery target" | deliver=origin 但飞书主频道未设 | 改 `deliver=feishu` + 确认主频道已设 |
