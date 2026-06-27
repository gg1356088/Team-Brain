#!/usr/bin/env python3
"""
LOOP 调度器 — 把任务自动转成结构化 prompt，下发给 Claude Code 或 Codex
让它们干活，不需要主 AI 盯着。

用法：
  python3 loop_dispatch.py goal "任务描述" --worker claude|codex
  python3 loop_dispatch.py loop "任务描述" --interval 15m --worker claude
  python3 loop_dispatch.py schedule "任务描述" --cron "0 9 * * *" --worker claude
  python3 loop_dispatch.py status
  python3 loop_dispatch.py list

配置：
  通过环境变量、.env 文件或 config.json 配置。
  详见 templates/config.template.json
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import argparse

# 添加本目录到 path，方便 import config（从同目录加载）
_script_dir = Path(__file__).parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

try:
    from config import load_config
except ImportError:
    # 降级：如果 config.py 不在 path 上，内联加载
    import os as _os
    from pathlib import Path as _Path

    def _load_env_file(env_path):
        env_vars = {}
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        env_vars[k.strip()] = v.strip()
        return env_vars

    def load_config(cli_overrides=None):
        cli_overrides = cli_overrides or {}
        defaults = {
            "workspace": str(_Path.home() / "HermesWorkspaces"),
            "feishu_chat_id": "",
            "claude_cmd": "claude",
            "codex_cmd": "/Applications/Codex.app/Contents/Resources/codex",
        }
        workspace = _os.environ.get("HERMES_SKILLS_WORKSPACE", defaults["workspace"])
        env_file = _load_env_file(_Path(workspace) / ".env")
        cfg_path = _Path(workspace) / "config.json"
        cfg = {}
        if cfg_path.exists():
            with open(cfg_path) as f:
                cfg = json.load(f)
        env = {
            "workspace": workspace,
            "feishu_chat_id": _os.environ.get("FEISHU_CHAT_ID",
                      env_file.get("FEISHU_CHAT_ID",
                      cfg.get("feishu", {}).get("chat_id", ""))),
            "claude_cmd": _os.environ.get("CLAUDE_CMD",
                      env_file.get("CLAUDE_CMD",
                      cfg.get("workers", {}).get("claude_cmd", defaults["claude_cmd"]))),
            "codex_cmd": _os.environ.get("CODEX_CMD",
                      env_file.get("CODEX_CMD",
                      cfg.get("workers", {}).get("codex_cmd", defaults["codex_cmd"]))),
        }
        for key in defaults:
            if key in cli_overrides and cli_overrides[key]:
                env[key] = cli_overrides[key]
        return env


# ==================== 配置 ====================

CONFIG = load_config()

BASE_DIR = Path(CONFIG["workspace"]) / "loop_dispatch"
TASK_DIR = BASE_DIR / "tasks"

WORKERS = {
    "claude": {
        "name": "Claude Code",
        "cmd": CONFIG["claude_cmd"],
    },
    "codex": {
        "name": "Codex",
        "cmd": CONFIG["codex_cmd"],
    },
}

FEISHU_CHAT_ID = CONFIG["feishu_chat_id"]


# ==================== 工具函数 ====================

def generate_goal_prompt(task_desc, max_turns=20):
    """把自然语言任务描述转成结构化 prompt（Claude Code 和 Codex 都能理解）。"""
    workspace = CONFIG["workspace"]
    goal = f"""请执行以下任务：{task_desc}

完成标准：
- 所有文件/代码/数据已处理完毕
- 输出文件已保存到 {workspace}/ 或任务指定目录
- 过程中如有报错，自行修复后继续
- 完成后在任务报告文件中记录做了什么、处理了多少、遇到什么问题

请在 {max_turns} 轮内完成以上任务。"""
    return goal


def generate_loop_prompt(task_desc, interval="15m", max_runs=10):
    """把任务描述转成结构化 loop prompt。"""
    return f"""请定期执行以下任务：{task_desc}
执行间隔：{interval}
最多执行 {max_runs} 次，完成后报告每次结果"""


def generate_schedule_prompt(task_desc, cron_expr):
    """把任务描述转成结构化 schedule prompt。"""
    return f"""请按照以下 cron 表达式定时执行任务：{cron_expr}
任务描述：{task_desc}"""


def send_to_claude(prompt):
    """把 prompt 通过 Claude Code CLI 发送。"""
    print(f"🚀 发送给 Claude Code...")
    result = subprocess.run(
        [CONFIG["claude_cmd"], "-p", prompt],
        capture_output=True,
        text=True,
        timeout=300,  # 复杂任务可能需要较长时间
    )
    if result.returncode == 0:
        print("✅ 指令已下发")
        return True
    else:
        print(f"❌ 发送失败: {result.stderr[:500]}")
        return False


def send_to_codex(prompt):
    """把 prompt 通过 Codex CLI 发送。"""
    print(f"🚀 发送给 Codex...")
    result = subprocess.run(
        [
            CONFIG["codex_cmd"],
            "exec", "--skip-git-repo-check", "-s", "workspace-write",
            prompt
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode == 0:
        print("✅ 指令已下发")
        return True
    else:
        print(f"❌ 发送失败: {result.stderr[:500]}")
        return False


# ==================== 任务管理 ====================

def _ensure_task_dir():
    """确保任务目录存在（懒创建，help/status 等只读操作不调用）。"""
    TASK_DIR.mkdir(parents=True, exist_ok=True)


def create_task(task_name, task_type, worker, prompt, task_id=None):
    """创建 LOOP 任务，写入 JSON 文件。"""
    _ensure_task_dir()
    if task_id is None:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        task_id = f"loop_{ts}"

    task = {
        "task_id": task_id,
        "task_name": task_name,
        "task_type": task_type,
        "worker": worker,
        "prompt": prompt,
        "status": "dispatched",
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None,
        "output_file": None,
        "retry_count": 0,
        "max_retries": 2,
        "last_check": None,
    }

    task_file = TASK_DIR / f"{task_id}.json"
    with open(task_file, 'w', encoding='utf-8') as f:
        json.dump(task, f, ensure_ascii=False, indent=2)

    return task_id


def update_status(task_id, status, completed_at=None, output_file=None, error=None):
    """更新任务状态。"""
    task_file = TASK_DIR / f"{task_id}.json"
    if not task_file.exists():
        return False

    with open(task_file) as f:
        task = json.load(f)

    old_status = task.get("status")
    task["status"] = status
    task["last_check"] = datetime.now().isoformat()

    if status == "running" and task.get("started_at") is None:
        task["started_at"] = datetime.now().isoformat()

    if status in ("completed", "failed"):
        task["completed_at"] = completed_at or datetime.now().isoformat()

    if output_file:
        task["output_file"] = output_file

    if error:
        task["error"] = error

    with open(task_file, 'w', encoding='utf-8') as f:
        json.dump(task, f, ensure_ascii=False, indent=2)

    print(f"  📝 状态变更: {task_id} {old_status} → {status}")
    return True


# ==================== 命令实现 ====================

def _build_parser():
    """构建 argparse 解析器。"""
    parser = argparse.ArgumentParser(
        prog="loop_dispatch.py",
        description="LOOP 调度器 — 把任务转成结构化 prompt 下发给 AI",
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # goal
    p_goal = subparsers.add_parser("goal", help="下发任务 — AI 执行直到完成")
    p_goal.add_argument("description", nargs="+", help="任务描述")
    p_goal.add_argument("--worker", choices=["claude", "codex"], default="claude", help="Worker（默认 claude）")
    p_goal.add_argument("--max-turns", type=int, default=20, help="最大轮次（默认 20）")

    # loop
    p_loop = subparsers.add_parser("loop", help="下发定时任务 — AI 定时重复执行")
    p_loop.add_argument("description", nargs="+", help="任务描述")
    p_loop.add_argument("--interval", default="15m", help="执行间隔（默认 15m）")
    p_loop.add_argument("--max-runs", type=int, default=10, help="最大执行次数（默认 10）")
    p_loop.add_argument("--worker", choices=["claude", "codex"], default="claude", help="Worker（默认 claude）")

    # schedule
    p_sched = subparsers.add_parser("schedule", help="下发定时任务 — 按 cron 表达式执行")
    p_sched.add_argument("description", nargs="+", help="任务描述")
    p_sched.add_argument("--cron", default="0 9 * * *", help="Cron 表达式（默认 '0 9 * * *'）")
    p_sched.add_argument("--worker", choices=["claude", "codex"], default="claude", help="Worker（默认 claude）")

    # status
    p_status = subparsers.add_parser("status", help="查看任务状态")
    p_status.add_argument("task_id", nargs="?", help="任务 ID（可选，不填则列出所有）")

    # list
    subparsers.add_parser("list", help="列出所有任务")

    # help
    subparsers.add_parser("help", help="显示此帮助")

    return parser


def cmd_goal(args):
    """下发 goal 任务。"""
    task_desc = " ".join(args.description)
    prompt = generate_goal_prompt(task_desc, args.max_turns)
    task_id = create_task(task_desc, "goal", args.worker, prompt)

    if args.worker == "claude":
        success = send_to_claude(prompt)
    else:
        success = send_to_codex(prompt)

    if success:
        print(f"📋 任务 ID: {task_id}")
        print(f"🤖 Worker: {WORKERS[args.worker]['name']}")
        print(f"⏱  最多轮次: {args.max_turns}")
    else:
        print(f"⚠️  任务已创建（{task_id}）但下发失败")


def cmd_loop(args):
    """下发 loop 任务。"""
    task_desc = " ".join(args.description)
    prompt = generate_loop_prompt(task_desc, args.interval, args.max_runs)
    task_id = create_task(task_desc, "loop", args.worker, prompt)

    if args.worker == "claude":
        success = send_to_claude(prompt)
    else:
        success = send_to_codex(prompt)

    if success:
        print(f"📋 任务 ID: {task_id}")
        print(f"🤖 Worker: {WORKERS[args.worker]['name']}")
        print(f"🔄 间隔: {args.interval}")
    else:
        print(f"⚠️  任务已创建（{task_id}）但下发失败")


def cmd_schedule(args):
    """下发 schedule 任务。"""
    task_desc = " ".join(args.description)
    prompt = generate_schedule_prompt(task_desc, args.cron)
    task_id = create_task(task_desc, "schedule", args.worker, prompt)

    if args.worker == "claude":
        success = send_to_claude(prompt)
    else:
        success = send_to_codex(prompt)

    if success:
        print(f"📋 任务 ID: {task_id}")
        print(f"🤖 Worker: {WORKERS[args.worker]['name']}")
        print(f"📅 Cron: {args.cron}")
    else:
        print(f"⚠️  任务已创建（{task_id}）但下发失败")


def cmd_status(args):
    """查看任务状态。"""
    if not TASK_DIR.exists():
        print("没有任务")
        return

    if args.task_id:
        tf = TASK_DIR / f"{args.task_id}.json"
        if not tf.exists():
            print(f"任务 {args.task_id} 不存在")
            return
        with open(tf) as f:
            task = json.load(f)
        print(f"任务: {task['task_id']}")
        print(f"名称: {task['task_name']}")
        print(f"类型: {task['task_type']}")
        print(f"Worker: {task['worker']}")
        print(f"状态: {task['status']}")
        print(f"创建: {task['created_at']}")
        print(f"重试: {task['retry_count']}/{task['max_retries']}")
    else:
        tasks = sorted(TASK_DIR.glob("*.json"), key=lambda x: x.name, reverse=True)
        if not tasks:
            print("没有任务")
            return

        print(f"{'ID':<25} {'名称':<30} {'类型':<8} {'Worker':<10} {'状态':<12} {'创建时间'}")
        print("-" * 110)
        for tf in tasks:
            with open(tf) as f:
                task = json.load(f)
            name = task['task_name'][:28]
            print(f"{task['task_id']:<25} {name:<30} {task['task_type']:<8} {task['worker']:<10} {task['status']:<12} {task['created_at']}")


def cmd_list(args):
    """列出所有任务。"""
    if not TASK_DIR.exists():
        print("没有任务")
        return

    tasks = sorted(TASK_DIR.glob("*.json"), key=lambda x: x.name, reverse=True)
    if not tasks:
        print("没有任务")
        return

    running = []
    done = []
    for tf in tasks:
        with open(tf) as f:
            task = json.load(f)
        if task['status'] in ('dispatched', 'running'):
            running.append((tf, task))
        else:
            done.append((tf, task))

    print(f"📊 总任务: {len(tasks)} | 运行中: {len(running)} | 已完成: {len(done)}")
    print()

    if running:
        print("🔄 运行中:")
        for tf, task in running:
            print(f"  [{task['status']}] {task['task_id']} — {task['task_name']} ({WORKERS[task['worker']]['name']})")
        print()

    if done:
        print("✅ 已完成:")
        for tf, task in done:
            icon = "✅" if task['status'] == 'completed' else "❌"
            print(f"  [{icon}] {task['task_id']} — {task['task_name']} ({task['task_type']}/{task['worker']})")


def main():
    parser = _build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    commands = {
        "goal": cmd_goal,
        "loop": cmd_loop,
        "schedule": cmd_schedule,
        "status": cmd_status,
        "list": cmd_list,
        "help": lambda args: parser.print_help(),
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
