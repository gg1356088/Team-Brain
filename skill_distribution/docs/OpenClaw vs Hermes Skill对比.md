# OpenClaw vs Hermes Skill 体系对比

> 评估日期：2026-06-08 | 目的：对比两套 AI Agent 的 Skill 体系，标注融合优先级

---

## 一、双方概况

### OpenClaw
| 指标 | 详情 |
|------|------|
| 仓库 | [openclaw/openclaw](https://github.com/openclaw/openclaw) |
| ⭐ Stars | 377,581 |
| Forks | 78,942 |
| 语言 | TypeScript |
| 许可证 | MIT |
| 创建时间 | 2025-11-24 |
| 定位 | 个人 AI 助手，本地运行，多渠道接入 |

### Hermes Agent
| 指标 | 详情 |
|------|------|
| 仓库 | [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) |
| ⭐ Stars | 186,987 |
| 语言 | Python |
| 创建方 | NousResearch |
| 定位 | "与你一起成长的 Agent"，研究导向 |

---

## 二、Skill 体系架构对比

| 维度 | OpenClaw | Hermes |
|------|----------|--------|
| **Skill 注册中心** | ClawHub（公共注册中心） | 无中心化注册中心 |
| **Skill 总量** | 5,400+（经筛选 5,198） | 当前环境 30+ |
| **安装方式** | `openclaw skills install <slug>` 或 `npx clawhub install <slug>` | 本地文件管理 |
| **Skill 优先级** | Workspace > Local > Bundled | 无明确分层 |
| **安全审计** | VirusTotal 合作扫描 + Snyk 安全扫描器 | 无系统化审计 |
| **版本管理** | GitOps 自动化部署/回滚（arc-skill-gitops） | 手动管理 |
| **包管理** | npm/pnpm 生态集成 | 独立文件系统 |
| **多语言支持** | 英文为主，部分中文 | 中英文混合 |
| **社区贡献** | 开放 PR 机制 + 精选列表 | 相对封闭 |

---

## 三、Skill 分类对比

### OpenClaw Skill 分类（5,198 curated）

| 分类 | 数量 | 代表 Skills |
|------|------|-------------|
| **Coding Agents & IDEs** | 1,184 | agent-team-orchestration, auto-pr-merger, arc-skill-gitops |
| **Web & Frontend Development** | 920 | 前端开发、UI 生成、网页抓取 |
| **DevOps & Cloud** | 393 | 部署、容器管理、云服务集成 |
| **Search & Research** | 345 | arxiv-search-collector, 网页研究、数据采集 |
| **Browser & Automation** | 323 | 浏览器自动化、网页交互 |
| **Productivity & Tasks** | 206 | 日程、任务管理、笔记 |
| **CLI Utilities** | 180 | 命令行工具、脚本执行 |
| **AI & LLMs** | 176 | 模型调用、Prompt 工程、Agent 管理 |
| **Image & Video Generation** | 170 | AI 图片/视频生成 |
| **Git & GitHub** | 167 | PR 管理、代码审查、Git 操作 |
| **Communication** | 146 | Slack、Discord、邮件等通讯集成 |
| **Transportation** | 110 | 出行、导航 |
| **Marketing & Sales** | 103 | 营销自动化、销售工具 |
| **PDF & Documents** | 105 | PDF 处理、文档生成 |
| **Health & Fitness** | 87 | 健康追踪、健身后勤 |
| **Media & Streaming** | 86 | 媒体处理、流媒体 |
| **Notes & PKM** | 69 | Obsidian、笔记系统 |
| **Calendar & Scheduling** | 66 | 日历管理、预约 |
| **Security & Passwords** | 54 | 安全审计、密码管理 |
| **Shopping & E-commerce** | 51 | 购物比价、电商工具 |
| **Speech & Transcription** | 46 | 语音识别、播客转录 |
| **Apple Apps & Services** | 44 | Apple 生态集成 |
| **Smart Home & IoT** | 41 | 智能家居控制 |
| **Data & Analytics** | 28 | 数据分析 |
| **iOS & macOS Development** | 29 | Apple 平台开发 |
| **Self-Hosted & Automation** | 33 | 自托管服务 |

### Hermes 当前 Skill 分类（30+）

| 分类 | Skills |
|------|--------|
| **文档处理** | document-processing, document-processing-workflows, invoice-pdf-workflow, invoice-reconciliation, defuddle |
| **AI/自动化** | autonomous-ai-agents, multi-agent-dispatch, red-teaming |
| **开发工具** | devops, mlops, software-development |
| **笔记/知识** | obsidian-bases, obsidian-markdown, note-taking, json-canvas |
| **媒体/创意** | creative, media, video-gen, agnes-image-gen, image-identification-behavior |
| **社媒/通讯** | social-media, email |
| **平台集成** | github, apple, yuanbao, scrapling-official |
| **运维** | hermes-cron-troubleshooting, hermes-setup, dogfood |
| **数据/研究** | data-science, research, productivity |
| **智能家居** | smart-home |

---

## 四、Skill 能力覆盖差异分析

### OpenClaw 有、Hermes 缺失的能力

| 能力域 | OpenClaw Skills | 对 Hermes 的价值 |
|--------|----------------|-------------------|
| **Skill 安全审计** | VirusTotal 扫描 + Snyk + Agent Trust Hub | 高——当前 Hermes 无安全审计机制 |
| **Skill 注册中心** | ClawHub（公开可发现） | 高——Hermes 缺少统一的 Skill 发现机制 |
| **多 Agent 编排** | agent-team-orchestration, agentdo | 高——Hermes 有 multi-agent-dispatch 但功能较弱 |
| **GitOps 部署** | arc-skill-gitops（自动部署/回滚） | 中——Hermes 缺少自动化部署 |
| **Skill 版本管理** | 版本化安装 + 回滚 | 中——Hermes 手动管理 |
| **浏览器自动化** | 323 个 browser & automation skills | 中——Hermes 缺少浏览器能力 |
| **日程/日历** | 66 个 calendar & scheduling skills | 中——律所场景需要预约管理 |
| **语音/转录** | 46 个 speech & transcription skills | 中——直播场景可用的转录能力 |
| **营销/销售** | 103 个 marketing & sales skills | 低——律所偏专业服务，营销工具相关性有限 |
| **购物/电商** | 51 个 shopping skills | 低——非律所核心需求 |

### Hermes 有、OpenClaw 可能较弱的能力

| 能力域 | Hermes Skills | 说明 |
|--------|--------------|------|
| **法律文档处理** | invoice-pdf-workflow, invoice-reconciliation | 律所场景专用，OpenClaw 无对应 |
| **中文内容生态** | yuanbao, social-media（国内平台） | OpenClaw 偏英文生态 |
| **红队测试** | red-teaming | OpenClaw 安全类 skill 可覆盖但未专门化 |
| **智能家居** | smart-home | OpenClaw 也有 41 个 smart-home skills |

---

## 五、核心差异总结

### OpenClaw 的核心优势
1. **规模效应** — 5,400+ skills vs 30+，10 倍以上的分类覆盖
2. **中心化生态** — ClawHub 注册中心 + CLI 一键安装 + VirusTotal 安全扫描
3. **社区驱动** — 开放贡献 + 严格筛选（剔除 7,215 个低质量/恶意 skill）
4. **企业级安全** — 沙箱模式、RBAC、安全扫描、信任评分体系
5. **多渠道分发** — 20+ 通讯渠道，Skill 可在不同渠道激活
6. **GitOps 部署** — Skill 的自动化部署、回滚、版本管理

### Hermes 的核心优势
1. **研究深度** — NousResearch 学术背景，模型训练 + Agent 一体的深度整合
2. **中文本地化** — 国内平台（微信、抖音、小红书）相关 skills
3. **法律场景** — 发票处理、合同对账等律所专用能力
4. **轻量简洁** — 30+ skills 易于管理，没有选择负担
5. **定时任务系统** — Cron + deliver 机制已成熟运行

### 关键差异
| 维度 | OpenClaw | Hermes |
|------|----------|--------|
| 生态规模 | 庞大（5K+） | 精简（30+） |
| 安全机制 | 多层（扫描+沙箱+RBAC） | 基本 |
| 分发方式 | 统一注册中心 | 分散管理 |
| 目标用户 | 个人用户/开发者 | 研究者 + 专业用户 |
| 中文支持 | 有限 | 较强 |
| 社区治理 | 开放 + 筛选 | 中心化 |

---

## 六、融合优先级建议

### 🔴 P0 — 立即融合（高价值、低难度）

| 序号 | 融合项 | 来源 | 理由 |
|------|--------|------|------|
| 1 | **Skill 安全扫描机制** | OpenClaw → Hermes | Hermes 目前无任何 skill 安全审计，30+ skills 直接访问文件系统和网络，存在安全隐患。引入 VirusTotal 集成或 Snyk agent-scan |
| 2 | **Sandbox 模式** | OpenClaw → Hermes | OpenClaw 的 `sandbox.mode: "non-main"` 设计（Docker/SSH/OpenShell 后端）可限制非主 session 的工具权限，对律所场景的客户数据保护至关重要 |
| 3 | **多 Agent 编排** | OpenClaw → Hermes | agent-team-orchestration 的角色定义、任务生命周期、handoff 协议可增强 Hermes 的 multi-agent-dispatch |

### 🟡 P1 — 短期融合（高价值、中难度）

| 序号 | 融合项 | 来源 | 理由 |
|------|--------|------|------|
| 4 | **Skill 注册/发现机制** | OpenClaw → Hermes | 建立类似 ClawHub 的 Hermes Skill 目录，便于发现和安装。可先做轻量版（GitHub Awesome List） |
| 5 | **浏览器自动化 Skill** | OpenClaw → Hermes | OpenClaw 323 个 browser skills 可大幅增强 Hermes 的网页操作能力（如自动填表、信息采集、网页监控） |
| 6 | **日历/预约 Skill** | OpenClaw → Hermes | 律所场景需要客户预约管理、开庭提醒、截止日期追踪，OpenClaw 的 calendar 类 skills 可直接适配 |
| 7 | **GitOps Skill 部署** | OpenClaw → Hermes | arc-skill-gitops 的自动化部署/回滚/版本管理，减少手动维护负担 |

### 🟢 P2 — 中期融合（中价值、中难度）

| 序号 | 融合项 | 来源 | 理由 |
|------|--------|------|------|
| 8 | **语音转录 Skill** | OpenClaw → Hermes | 直播场景的语音转文字、会议记录等需求 |
| 9 | **文档处理增强** | OpenClaw → Hermes | OpenClaw 有 105 个 PDF/Documents skills，可与 Hermes 现有的 invoice-pdf-workflow 互补 |
| 10 | **多渠道分发** | OpenClaw → Hermes | OpenClaw 的 20+ 渠道支持（WhatsApp/Telegram/Slack 等），如律所需要多渠道客户接入 |

### ⚪ P3 — 长期关注（低优先级）

| 序号 | 融合项 | 方向 | 理由 |
|------|--------|------|------|
| 11 | 中文内容 Skill 贡献 | Hermes → OpenClaw | Hermes 的国内平台（抖音、小红书、微信）skills 可反向贡献到 ClawHub |
| 12 | 法律专业 Skill 包 | Hermes → OpenClaw | 律所场景的发票处理、合同对账、合规检查等 skills 可打包发布 |
| 13 | 红队测试标准化 | 双向融合 | Hermes 的 red-teaming 经验 + OpenClaw 的安全扫描基础设施 |

---

## 七、融合路线图

```
Week 1-2 (P0):
  ┌─ Skill 安全扫描 ─────────────────────────────┐
  │  · 集成 Snyk agent-scan 到 Hermes skill 加载流程  │
  │  · 建立 skill 安装前的安全 checklist            │
  └──────────────────────────────────────────────┘
  ┌─ Sandbox 隔离 ───────────────────────────────┐
  │  · 为非主 session 启用 Docker sandbox         │
  │  · 定义律所场景的最小权限集                    │
  └──────────────────────────────────────────────┘

Week 3-4 (P1):
  ┌─ Skill 目录 + 浏览器 + 日历 ──────────────────┐
  │  · 搭建 Hermes Skill Awesome List（GitHub）   │
  │  · 引入 browser 自动化能力                    │
  │  · 适配 calendar 预约 skills                  │
  └──────────────────────────────────────────────┘

Month 2-3 (P2):
  ┌─ 语音 + 文档 + 多渠道 ────────────────────────┐
  │  · 直播转录 + 会议记录自动化                   │
  │  · PDF 处理能力增强                           │
  │  · 客户多渠道接入（WhatsApp/微信等）           │
  └──────────────────────────────────────────────┘

Ongoing (P3):
  · 双向贡献：中文生态 skills 贡献到 ClawHub
  · 法律专业 skill 包沉淀
```

---

## 八、关键结论

1. **OpenClaw 在 Skill 生态规模上领先 100 倍以上**（5,400 vs 30），但其 skill 偏向英文开发者场景，对律所中文场景的非开发类需求覆盖不足。

2. **Hermes 当前 Skill 体系的短板不在数量，在基础设施**：缺少安全审计、沙箱隔离、自动部署——这些恰恰是 OpenClaw 的强项。P0 融合应聚焦"引入基础设施"而非"堆砌更多 skill"。

3. **双向融合才有意义**：Hermes 可贡献中文生态和法律专业 skills 到 OpenClaw 社区，OpenClaw 可贡献安全/部署基础设施到 Hermes。

4. **不建议直接迁移到 OpenClaw**：Hermes 的中文本地化（微信、抖音、小红书集成）和法律场景定制（发票、合规）是 OpenClaw 不具备的差异化能力。融合策略应是"各取所长"，而非"二选一"。

---

*以上对比基于 2026-06-08 GitHub 公开数据。具体 Skills 功能以实际安装测试为准。*
