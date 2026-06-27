# Hermes 技能分发包

两套分发体系：外部企业用技能包，内部团队用框架文档。

## 目录结构

```
skill_distribution/
├── README.md              # 本文件
├── skills-obsidian/       # 外部企业版：可安装的 Hermes 技能
│   ├── README.md
│   ├── obsidian/          # Obsidian vault 基础操作（去硬编码）
│   ├── knowledge-base/    # 通用知识库方法论
│   ├── hermes-setup/      # Hermes 配置审计
│   ├── multi-agent-dispatch/  # 多AI调度系统
│   └── dispatch-with-context/ # 调度规范
├── loop-dispatch/         # 外部企业版：LOOP 调度器分发包
│   ├── loop_dispatch.py
│   ├── loop_monitor.py
│   ├── config.py
│   ├── install.sh
│   ├── SKILL.md
│   └── ...
└── team-frameworks/       # 内部团队版：方法论 + 踩坑
    ├── README.md
    ├── 发票处理框架.md
    ├── AI协作与精简通信框架.md
    ├── 视觉复核与OCR框架.md
    ├── PDF自动化踩坑框架.md
    ├── 知识库建设框架.md
    ├── 知识库模板库/
    └── 框架与Vault对照.md
```

## 外部 vs 内部

| | 外部企业版 | 内部团队版 |
|---|---|---|
| 谁用 | 其他公司、开源社区 | 内部团队成员 |
| 是什么 | 可安装的 Hermes 技能 + Python 脚本 | 方法论文档 + 踩坑经验 |
| 给什么 | 去硬编码的技能文件 | 剥离所有敏感数据的框架 |
| 怎么接 | 复制到 ~/.hermes/skills/ 直接用 | 先读完建立认知，再看 vault 原文 |
| 更新频率 | 每次功能变更 | 每次踩新坑或流程变更 |
