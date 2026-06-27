# 监督系统设计指南

## 为什么需要监督机制

没有监督的多AI调度是盲目的：派完任务就忘，结果不对也得收。监督的核心目标是三个：

1. **进度可见** — 谁在做、做了多久、卡没卡
2. **质量可控** — 文件存在≠内容正确，必须验收
3. **异常可恢复** — 超时/失败要重试或告警

## 核心设计原则

### 1. 任务创建时必须声明验收规则

不能只做"派出去"，必须同时声明：
- 产出什么文件（`expected_files`）
- 内容必须包含什么关键字（`verification_rules`）

这是最小必要契约。没有验收标准的任务不需要跟踪。

### 2. 自动验收优于人工检查

内置验收规则覆盖：
- **文件存在性** — 支持相对路径、HermesPet_Workspace、用户根目录三种路径
- **文件大小** — 默认 <1KB 判定为异常
- **内容关键字** — 检查关键字段是否生成
- **超时检测** — 默认 30 分钟，超时无脑 FAIL

### 3. 失败自动重试

单次失败不标记 final fail，自动重试最多 2 次。这解决了 Claude Code 偶尔超时或写入不完整的问题。

### 4. 完整审计日志

每个任务有独立日志文件，记录所有状态变更和验收结果。出问题时可以回溯。

## 使用场景

### 场景 A：研究类任务（最常见）
```bash
supervisor.py create "研究X方案" research-001 "在HermesPet_Workspace生成对比报告"
supervisor.py verify_set research-001 "研究报告.md" "结论,建议,方案"
supervisor.py update research-001 running
supervisor.py verify research-001
```

### 场景 B：开发类任务
```bash
supervisor.py create "修复X功能" fix-001 "修改Y模块"
supervisor.py verify_set fix-001 "fix.py,test.py" "def test_"
supervisor.py update fix-001 running
```

### 场景 C：文档/整理类任务
```bash
supervisor.py create "整理发票PDF" invoice-001 "分类命名并重命名"
supervisor.py verify_set invoice-001 "output.xlsx" "序号,日期,分类"
```

## 路径解析规则

`supervisor.py` 自动尝试三种路径：
1. 绝对路径（以 `/` 开头）
2. `/Users/xinban/HermesPet_Workspace/` + 相对路径
3. `/Users/xinban/` + 相对路径

写验收规则时不需要写完整路径，写文件名或相对路径即可。

## 超时配置

默认 30 分钟，对于复杂任务可以调整 `timeout_minutes` 参数。

## 与 Cron 集成（进阶）

可以设置 Cron job 定时巡检所有 running 任务，超时的自动告警。当前版本只做了核心工具，Cron 集成按需添加。
