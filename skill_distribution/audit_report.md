============================================================
  Hermes Pet Skill Distribution — 功能正确性审查报告
  审查目录: ~/HermesPet_Workspace/skill_distribution/
  审查日期: 2026-06-18
============================================================

一、config.py 加载逻辑审查
------------------------------------------------------------
文件: loop-dispatch/config.py

配置优先级链:
  CLI 参数 > 环境变量 > .env 文件 > config.json > 默认值

[OK] 默认值 (L40-45): 合理。workspace 默认为 ~/HermesWorkspaces。

[OK] 环境变量 (L48-53): 使用 os.environ.get() 回退到 defaults，正确。

[WARN] .env 文件 (L56-61): .env 文件路径依赖 env["workspace"] 的值。
  如果 HERMES_SKILLS_WORKSPACE 环境变量被设置了一个不存在的目录，
  那么 .env 加载时会静默跳过（env_path.exists() 返回 False），
  这不会报错，而是静默使用环境变量值。行为合理，但文档未明确。

[WARN] config.json (L64-70): 路径同样依赖 workspace。
  读取路径: workspace/config.json。
  键路径: cfg["feishu"]["chat_id"], cfg["workers"]["claude_cmd"]。
  如果 config.json 格式不对（例如缺少 feishu 键），
  cfg.get("feishu", {}).get("chat_id", ...) 会正确回退。
  行为正确。

[BUG #1] 优先级逻辑 — .env 和 config.json 的覆盖顺序可能误导。
  代码顺序是: 环境变量 -> .env -> config.json -> CLI
  注释说 .env > config.json，但实际代码中 config.json 在 .env 之后加载，
  会覆盖 .env 的值。所以实际优先级是:
    config.json > .env 文件
  
  但 config.json 中也有 workspace 相关的默认回退吗？没有。
  config.json 只覆盖 feishu_chat_id, claude_cmd, codex_cmd，不覆盖 workspace。
  这不算 bug，但值得注意: config.json 可以覆盖 .env 的值。
  
  优先级链实际生效顺序（从高到低）:
    1. CLI 参数
    2. config.json (如果存在)
    3. .env 文件 (如果存在)
    4. 环境变量
    5. 默认值

  这与 docstring 中写的 "CLI > 环境变量 > .env > config.json > 默认值" 不符！
  实际上 config.json 排在 .env 之后，会覆盖 .env。
  DOCSTRING 声称的优先级与实际代码执行顺序不一致。
  --> LOW SEVERITY (行为可预期，但文档误导)

[INFO] .env 解析器 (_load_env_file, L13-25):
  - 支持 # 注释
  - 使用 split("=", 1)，正确支持值中包含 = 符号
  - strip() 清理键值两边的空白
  - 没有处理引号（如 "value" 会保留引号）— 但这对本工具影响不大，
    因为 .env 中通常不需要引号
  --> 可接受

[INFO] 默认值中的 codex_cmd 硬编码了 macOS 路径:
  /Applications/Codex.app/Contents/Resources/codex
  这在非 macOS 上会不可用。但这是默认值，用户可以覆盖。
  --> LOW SEVERITY (平台特定默认值)


二、loop_dispatch.py 的 argparse 审查
------------------------------------------------------------
文件: loop-dispatch/loop_dispatch.py

[OK] _build_parser() (L225-262):
  - prog="loop_dispatch.py" — 帮助输出会显示正确的程序名
  - 子命令: goal, loop, schedule, status, list, help — 共 6 个
  - goal/loop/schedule 都有 --worker 参数

[WARN] --worker 参数在子命令中的可见性:
  --worker 出现在 goal、loop、schedule 三个子命令的 help 文本中。
  对于 "help" 子命令，它没有 --worker，这正确（help 就是显示帮助）。
  
  但注意: "help" 作为子命令和 argparse 内置的 --help 功能会冲突吗？
  argparse 的 --help 是由主 parser 的 -h 触发的，与子命令 "help" 不冲突。
  python3 loop_dispatch.py help 会调用 commands["help"] -> parser.print_help()
  --> 行为正确

[OK] description 字段 (L229):
  "LOOP 调度器 — 把任务转成结构化 prompt 下发给 AI"
  不包含 --worker 等参数的描述文本。
  --> 正确，不会"混进"参数描述

[OK] 参数定义:
  - goal.description: nargs="+"  (至少一个词)
  - loop.description: nargs="+" 
  - schedule.description: nargs="+"
  - status.task_id: nargs="?" (可选)
  - 所有 --worker 都有 choices=["claude", "codex"], default="claude"
  --> 定义完整且正确

[INFO] main() 函数 (L394-415):
  - args.command 为 None 时打印帮助 — 正确
  - "help" 子命令映射到 lambda: parser.print_help() — 正确
  - 未知命令也打印帮助 — 合理


三、loop_monitor.py 的 import config 审查
------------------------------------------------------------
文件: loop-dispatch/loop_monitor.py

[OK] sys.path 注入 (L17-20):
  _script_dir = Path(__file__).parent
  if str(_script_dir) not in sys.path:
      sys.path.insert(0, str(_script_dir))
  --> 如果从 loop-dispatch/ 目录下运行，config.py 在同一个目录，
     sys.path[0] 会被设置为该目录，from config import load_config 可正常工作。

[OK] 降级内联 (L22-53):
  try:
      from config import load_config
  except ImportError:
      # 降级内联 — 完整复制了 load_config 逻辑
      ...
  --> 降级路径正确。

[BUG #2] 降级逻辑缺少 .env 文件加载。
  对比 config.py 的完整版本（L56-61），config.py 会加载 .env 文件。
  但降级内联版本 (loop_monitor.py L43-50) 直接跳过了 .env 加载，
  只加载了 config.json。
  
  loop_dispatch.py 的降级逻辑 (L52-58) 同样缺少 .env 加载。
  
  影响: 如果用户通过 PYTHONPATH 或其他方式运行脚本，
  config.py 不在 sys.path 上时，降级版本会缺少 .env 配置。
  这意味着 .env 文件的优先级高于 config.json，但在降级路径下，
  .env 被完全跳过。
  --> MEDIUM SEVERITY (降级路径丢失配置层级)

[BUG #3] 两个 Python 文件的降级内联代码几乎完全相同，
  与 config.py 的完整实现相比，降级版本缺少 .env 文件加载逻辑。
  如果用户从 loop-dispatch/ 外部运行脚本（例如通过 PYTHONPATH 或
  符号链接后的位置），降级路径会丢失 .env 配置。
  --> MEDIUM SEVERITY (重复代码 + 配置遗漏)

[WARN] loop_monitor.py 没有 argparse，而是用 sys.argv[1] 解析命令。
  这在 L378-405 的 main() 中直接实现。
  - 缺少 --help 功能
  - 缺少参数验证
  - 未知命令只打印 "未知命令: {cmd}" 然后退出
  --> LOW SEVERITY (不如 argparse 健壮，但功能上够用)


四、install.sh 路径正确性审查
------------------------------------------------------------
文件: install.sh

[OK] SCRIPT_DIR 计算 (L23):
  SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
  --> 正确获取 install.sh 所在目录的绝对路径

[OK] 文件复制路径 (L25-27):
  cp "$SCRIPT_DIR/loop-dispatch/loop_dispatch.py" "$SKILL_DIR/"
  cp "$SCRIPT_DIR/loop-dispatch/loop_monitor.py" "$SKILL_DIR/"
  cp "$SCRIPT_DIR/loop-dispatch/SKILL.md" "$SKILL_DIR/.hermes/skills/loop-dispatch/"
  --> $SCRIPT_DIR/loop-dispatch/ 正确指向 skill_distribution/loop-dispatch/
  如果从 skill_distribution/ 目录运行 ./install.sh，完全正确。

[WARN] 复制的 2>/dev/null || echo 静默容错:
  如果 loop-dispatch/ 目录不存在，三个 cp 都会静默失败，
  只打印警告行。脚本继续执行（set -e 不会阻止，因为 || 捕获了退出码）。
  --> 合理行为

[WARN] install.sh 没有复制 config.py！
  步骤 3 只复制了 loop_dispatch.py, loop_monitor.py, SKILL.md。
  但没有复制 config.py。
  
  这意味着安装后，$SKILL_DIR/ 下没有 config.py。
  但 loop_dispatch.py 和 loop_monitor.py 都依赖 config.py（通过 sys.path 注入
  或降级内联）。
  
  降级内联可以工作，但如果用户安装了 config.py 到 sys.path 上，
  它会优先使用安装版本的 config.py。
  然而 install.sh 没有安装 config.py，所以只会使用降级内联版本。
  降级版本缺少 .env 文件加载（见 BUG #2, #3）。
  --> MEDIUM SEVERITY (install.sh 遗漏 config.py)

[OK] 配置文件创建 (L31-37):
  ENV_FILE="$INSTALL_DIR/.env"
  如果不存在则从 .env.example 复制。
  --> 正确

[OK] 符号链接 (L65-97):
  三种情况处理: 已有正确链接 -> 目录迁移 -> 全新创建
  --> 逻辑完善

[WARN] README.md 中的文件结构图 (L47-58):
  显示 env.example 在 loop-dispatch/templates/ 下，
  但实际文件在 loop-dispatch/.env.example（根目录，非 templates 子目录）。
  --> LOW SEVERITY (文档与文件系统不一致)


五、配置加载降级逻辑对比
------------------------------------------------------------

  功能                config.py 完整版    降级内联版本
  --------            ----------------    --------------
  默认值                YES                 YES
  环境变量              YES                 YES
  .env 文件加载          YES                NO <--- 遗漏
  config.json           YES                 YES
  CLI 覆盖              YES                 YES

  两个 Python 文件的降级内联版本完全相同，且都遗漏了 .env 文件加载。


六、其他问题
------------------------------------------------------------

[WARN] .gitignore (L4):
  包含 "*.json" — 这会排除所有 JSON 文件，包括项目自己的
  config.template.json。
  templates/config.template.json 应该被 git 跟踪，但 *.json 会忽略它。
  --> LOW SEVERITY (模板文件被意外忽略)

[INFO] .gitignore (L3):
  "*.pid" — 正确排除 PID 锁文件

[INFO] .gitignore (L6):
  "tasks/" — 正确排除任务数据目录

[WARN] loop_monitor.py L303:
  sys.stdout.write(f"\r[{datetime.now().strftime('%H:%M:%S')}] 检查中... ({state['checked_count']}次)")
  这个状态行在每次循环时刷新，但 state['checked_count'] 在循环内部
  更新前读取，所以会显示旧计数。需要再检查一次。
  
  实际上 state 在 run_status_check() 中已更新（L255 save_monitor_state），
  所以 L303 读取的是新保存的 state。但 run_status_check() 返回 changes 后，
  changes 非空时不执行此 printf，changes 为空时才执行。
  逻辑正确。

[INFO] loop_monitor.py L310:
  LOCK_FILE.unlink(missing_ok=True)
  missing_ok 参数需要 Python 3.8+。如果目标环境是 Python 3.7 或更低版本，
  这会报错。
  --> LOW SEVERITY (Python 版本兼容性)


七、总结
------------------------------------------------------------

严重级别统计:
  MEDIUM: 3 处
  LOW:    5 处

关键问题:

  [MEDIUM] BUG #1 — config.py docstring 中声明的优先级与实际代码不符。
    文档说 "CLI > 环境变量 > .env > config.json > 默认值"，
    但实际代码执行顺序是: CLI > config.json > .env > 环境变量 > 默认值。
    修复: 更新 docstring 或调整代码顺序以匹配文档。

  [MEDIUM] BUG #2,#3 — 降级内联版本缺少 .env 文件加载。
    loop_dispatch.py 和 loop_monitor.py 的降级 load_config 都省略了
    .env 文件读取逻辑。如果 config.py 不可用，用户将无法通过 .env 文件
    配置 FEISHU_CHAT_ID 等关键参数。
    修复: 在两个降级内联版本中补充 .env 加载逻辑。

  [MEDIUM] BUG #4 — install.sh 没有复制 config.py。
    安装后 loop_dispatch.py 和 loop_monitor.py 的 from config import
    会失败，只能使用降级内联版本（缺少 .env 支持）。
    修复: 在 install.sh 步骤 3 中增加 config.py 的复制。

低严重问题:

  [LOW] README 文件结构图与实际路径不符（env.example 位置）。
  [LOW] .gitignore 中的 *.json 会排除 config.template.json。
  [LOW] macOS 硬编码默认路径影响跨平台可用性。
  [LOW] loop_monitor.py 使用 missing_ok=True（Python 3.8+）。
  [LOW] loop_monitor.py 使用 sys.argv 而非 argparse。
