---
name: search-best-practices
description: 正确的搜索方法论——遇到要找的东西时，用多维度关键词组合搜索，不要只靠一个关键词。覆盖 GitHub、npm、Google 三源搜索。
---

# 搜索最佳实践

## 核心问题
搜索失败的根本原因：只用单一关键词，不知道目标可能有多个别名。

## 搜索策略（每次搜索都走这三步）

### 第一步：多关键词组合搜索 GitHub

**不要只搜 `feishu cli`**，要同时搜：
- `feishu cli`
- `lark cli`
- `larksuite cli`
- `飞书 cli`

因为同一个东西可能叫 `lark-cli`（npm名）但 repo 叫 `larksuite/cli`。

### 第二步：搜 npm 包管理器

很多 CLI 工具通过 npm 分发，不在 GitHub 上叫 `cli`：
- `npm search lark cli`
- `npm search feishu cli`
- `npm search lark-openapi`

### 第三步：搜 Google

用 `web_search` 或浏览器搜索：
- `"lark" "cli" site:github.com`
- `"feishu" CLI tool`

## 常见别名表

| 中文名 | 英文名 | 别名 |
|--------|--------|------|
| 飞书 | Lark | larksuite |
| 钉钉 | DingTalk | dingding |
| 企业微信 | WeCom | weixin |
| 微信 | WeChat | wx |

## 搜索失败时
1. 换关键词——搜功能而不是名字
2. 搜 npm 而不是 GitHub——很多 CLI 是 npm 包
3. 搜 Google——看 Stack Overflow、博客推荐
