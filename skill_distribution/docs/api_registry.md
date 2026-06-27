# IncepVision Law API Registry

> 集中式 API 目录。新工作流从注册表取 API，不再重复实现认证逻辑。
>
> 使用：`from api_registry import get_google_creds; creds = get_google_creds("admin_all")`
>
> CLI：`python3 api_registry.py list` / `python3 api_registry.py authorize <key>`

## Google OAuth APIs

| Key | Account | Scopes | Token 位置 | 管理方 |
|---|---|---|---|---|
| `admin_all` | admin@incepvisionlaw.com | Gmail(全) + Drive + Calendar + Docs + Sheets + Slides + Forms + Apps Script + Cloud + Chat(全) — 共 21 项 | `tools/admin-google-auth/google_admin_all_services_token.json` | 注册表 |
| `hr_gmail_oauth` 🔒 | team@incepvisionlaw.com | drive + sheets + docs + gmail.send + gmail.compose + gmail.settings.basic + userinfo.profile + chat.messages.readonly | `workflows/hr-resume-automation/google_drive_token.json` | HR Workflow |
| `office_gmail` | office@incepvisionlaw.com | `gmail.modify` + `drive` | `workflows/receipt-renamer/google_office_gmail_token.json` | Receipt Renamer |

## IMAP / SMTP

| Key | Type | Host:Port | Account | 凭据文件 |
|---|---|---|---|---|
| `hr_gmail_imap` 🔒 | IMAP | imap.gmail.com:993 | team@incepvisionlaw.com | `workflows/hr-resume-automation/gmail_credentials.json` |
| `hr_sina_imap` 🔒 | IMAP | imap.sina.com:993 | hr@incepvisionlaw.com | `workflows/hr-resume-automation/sina_credentials.json` |
| `hr_sina_smtp` 🔒 | SMTP (SSL) | smtp.sina.com:465 | hr@incepvisionlaw.com | `workflows/hr-resume-automation/sina_credentials.json` |

## API Key

| Key | 用途 | 环境变量 / 文件 |
|---|---|---|
| `gemini` | Gemini LLM（姓名提取、视频识别等） | `GEMINI_API_KEY` 或 `workflows/hr-resume-automation/gemini_credentials.json` |

## Webhook

| Key | 用途 | 配置文件 |
|---|---|---|
| `google_chat_webhook` | Google Chat 消息推送 | `workflows/hr-resume-automation/google_chat_config.json` |

> 🔒 = 由现有工作流管理，注册表只做文档记录，不通过注册表修改。

## 新工作流怎么用

```python
from api_registry import get_google_creds

# 一行拿 Admin 全权限凭据，自动处理 token 过期刷新 / 首次 OAuth 授权
creds = get_google_creds("admin_all")

# 然后正常使用 Google API
from googleapiclient.discovery import build
gmail = build("gmail", "v1", credentials=creds)
```

**如果当前账号 scope 不够**：先检查 `admin_all` 是否过期、是否需要重授权、Google Cloud API 是否启用、以及文件/账号权限。不要新建 Admin 窄权限 token。

**首次授权**：`python3 api_registry.py authorize admin_all`

## 可移植性

把工作流搬到另一台电脑：

1. 拷贝工作流目录 + `api_registry.py`
2. 拷贝 `google_credentials.json`（OAuth client secret，所有 Google API 共用）
3. 在新电脑上运行 `python3 api_registry.py authorize <api_key>` 生成新 token
4. 或者在目标电脑设置环境变量指定路径（见下节）

## 路径覆盖

默认路径从 `api_registry.py` 所在目录推导。如需覆盖：

1. **环境变量**：`IPCV_API_BASE=/path/to/project`、`GOOGLE_CLIENT_SECRET_PATH=/path/to/client_secret.json`、`{API_KEY}_TOKEN_PATH=/path/to/token.json`
2. **`api_paths.json`**（不提交 git）：在项目根创建，按 `api_paths.example.json` 模板填写
