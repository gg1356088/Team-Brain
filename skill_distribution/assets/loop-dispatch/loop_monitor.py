#!/usr/bin/env python3
"""
LOOP 监控器 — 定期检查 LOOP 任务状态，完成后推送到飞书

配置通过 config.py 统一管理。
"""

import json
import os
import subprocess
import sys
import time
import re
from pathlib import Path
from datetime import datetime

# 添加本目录到 path
_script_dir = Path(__file__).parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

try:
    from config import load_config
except ImportError:
    # 降级内联
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

LOOP_TASK_DIR = Path(CONFIG["workspace"]) / "loop_dispatch" / "tasks"
MONITOR_STATE_FILE = Path(CONFIG["workspace"]) / "loop_dispatch" / ".monitor_state.json"
LOCK_FILE = Path(CONFIG["workspace"]) / "loop_dispatch" / ".monitor.pid"
CHECK_INTERVAL = 30  # 秒

FEISHU_CHAT_ID = CONFIG["feishu_chat_id"]


# ==================== 飞书通知 ====================

def send_feishu_via_lark(title, content, max_retries=3):
    """通过 lark-cli 发送飞书消息到指定群，带重试机制。"""
    if not FEISHU_CHAT_ID:
        print("  ⚠️  FEISHU_CHAT_ID 未配置，跳过通知")
        return False

    full_msg = f"{title}\n\n{content}"
    cmd = [
        "lark-cli", "im", "+messages-send",
        "--chat-id", FEISHU_CHAT_ID,
        "--text", full_msg,
    ]

    for attempt in range(max_retries):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"  📤 飞书通知已发送")
                return True
            else:
                err = result.stderr[:200]
                print(f"  ⚠️ 飞书发送失败 (尝试 {attempt+1}/{max_retries}): {err}")
                if attempt < max_retries - 1:
                    time.sleep(2 * (attempt + 1))
        except subprocess.TimeoutExpired:
            print(f"  ⚠️ 飞书发送超时 (尝试 {attempt+1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))
        except Exception as e:
            print(f"  ⚠️ 飞书通知异常: {e}")
            return False

    print(f"  ❌ 飞书通知最终失败（{max_retries} 次重试后）")
    log_file = Path(CONFIG["workspace"]) / "loop_dispatch" / ".notification_errors.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().isoformat()} | {title} | {content}\n")
    return False


def notify_task_complete(task_id, task_name, worker, details=""):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    content = f"**任务ID:** {task_id}\n**Worker:** {worker}\n**时间:** {ts}\n**详情:** {details}"
    send_feishu_via_lark(f"✅ 任务完成: {task_name}", content)


def notify_task_failed(task_id, task_name, worker, reason=""):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    content = f"**任务ID:** {task_id}\n**Worker:** {worker}\n**时间:** {ts}\n**失败原因:** {reason}"
    send_feishu_via_lark(f"❌ 任务失败: {task_name}", content)


def notify_task_dispatched(task_id, task_name, worker):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    content = f"**任务ID:** {task_id}\n**Worker:** {worker}\n**时间:** {ts}"
    send_feishu_via_lark(f"🚀 任务已下发: {task_name}", content)


# ==================== 任务状态检查 ====================

def _is_process_alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (ProcessLookupError, ValueError, OSError):
        return False


def check_ai_completion(task_id, task_data):
    """检查 AI 是否已完成任务。返回 (new_status, reason) 或 (None, msg)。"""
    # 策略1：检查 output_file 字段
    output_file = task_data.get("output_file")
    if output_file and Path(output_file).exists():
        return "completed", "输出文件存在"

    # 策略2：从 prompt 中提取文件名
    prompt = task_data.get("prompt", "")
    file_matches = re.findall(r'(?:保存到|写入到|生成|创建)\s+(?:一个\s*)?(?:JSON\s*)?(?:文件\s*)?([^\s"\']+\.json)', prompt)
    if not file_matches:
        file_matches = re.findall(r'([a-zA-Z0-9_-]+\.json)', prompt)

    workspace = Path(CONFIG["workspace"])
    for fname in file_matches:
        fpath = workspace / fname
        if fpath.exists():
            task_file = LOOP_TASK_DIR / f"{task_id}.json"
            if task_file.exists():
                with open(task_file) as f:
                    task = json.load(f)
                task["status"] = "completed"
                task["output_file"] = str(fpath)
                task["completed_at"] = datetime.now().isoformat()
                task["last_check"] = datetime.now().isoformat()
                with open(task_file, 'w') as f:
                    json.dump(task, f, ensure_ascii=False, indent=2)
            return "completed", f"检测到输出文件 {fname}"

    # 策略3：检查 dispatched 时间
    created_at = task_data.get("created_at", "")
    if created_at:
        try:
            created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            elapsed = (datetime.now() - created).total_seconds()
            if elapsed > 1800:
                return "running", f"已运行 {int(elapsed/60)} 分钟"
            elif elapsed > 600:
                return "running", f"已等待 {int(elapsed/60)} 分钟"
        except Exception:
            pass

    return None, "仍在 dispatched 状态"


def load_monitor_state():
    if MONITOR_STATE_FILE.exists():
        with open(MONITOR_STATE_FILE) as f:
            return json.load(f)
    return {"notified": [], "checked_count": 0, "cleanup_version": 1}


def save_monitor_state(state):
    MONITOR_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MONITOR_STATE_FILE, 'w') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def cleanup_notified_list(state, max_entries=50):
    if len(state.get("notified", [])) <= max_entries:
        return state
    state["notified"] = state["notified"][-max_entries:]
    state["checked_count"] = state.get("checked_count", 0) + 1
    return state


def check_task_status(task_file):
    try:
        with open(task_file) as f:
            data = json.load(f)
        return data.get('task_id'), data, data.get('status')
    except (json.JSONDecodeError, FileNotFoundError):
        return None, None, None


def run_status_check():
    """执行一次状态检查，返回变更的任务列表。"""
    if not LOOP_TASK_DIR.exists():
        return []

    tasks = sorted(LOOP_TASK_DIR.glob("*.json"))
    if not tasks:
        return []

    state = load_monitor_state()
    changes = []

    for tf in tasks:
        task_id, task_data, status = check_task_status(tf)
        if task_id is None:
            continue

        is_new = task_id not in state.get("notified", [])

        if status == "dispatched":
            new_status, reason = check_ai_completion(task_id, task_data)
            if new_status and new_status != "dispatched":
                status = new_status
                is_new = True

        if status in ("completed", "failed", "dispatched", "running"):
            if is_new or status == "dispatched":
                changes.append({
                    "task_id": task_id,
                    "task_name": task_data.get("task_name", ""),
                    "worker": task_data.get("worker", ""),
                    "status": status,
                    "details": json.dumps(task_data, ensure_ascii=False),
                    "is_new": is_new,
                })

    for c in changes:
        if c["task_id"] not in state["notified"]:
            state["notified"].append(c["task_id"])

    state = cleanup_notified_list(state)
    state["checked_count"] = state.get("checked_count", 0) + 1
    save_monitor_state(state)
    return changes


# ==================== 监控循环 ====================

def start_monitor():
    if LOCK_FILE.exists():
        with open(LOCK_FILE) as f:
            pid = f.read().strip()

        if _is_process_alive(pid):
            print(f"⚠️  监控已在运行（PID: {pid}）")
            print(f"   先用 `python3 loop_monitor.py stop` 停止后再启动")
            return
        else:
            print(f"⚠️  发现僵尸 PID 文件（进程 {pid} 不存在），清理后重启")
            LOCK_FILE.unlink()

    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))

    print(f"🔍 LOOP 监控器已启动（PID: {os.getpid()}）")
    print(f"   检查间隔: {CHECK_INTERVAL}秒")
    print(f"   按 Ctrl+C 停止")
    print()

    state = load_monitor_state()
    print(f"📊 已检查 {state.get('checked_count', 0)} 次，通知过 {len(state.get('notified', []))} 个任务")
    print()

    try:
        while True:
            changes = run_status_check()

            if changes:
                for c in changes:
                    if c["status"] == "dispatched" and c["is_new"]:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 新任务: {c['task_id']} ({c['task_name']})")
                        notify_task_dispatched(c["task_id"], c["task_name"], c["worker"])
                    elif c["status"] in ("completed", "failed"):
                        icon = "✅" if c["status"] == "completed" else "❌"
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] {icon} 任务完成: {c['task_id']} ({c['task_name']})")
                        if c["status"] == "completed":
                            notify_task_complete(c["task_id"], c["task_name"], c["worker"])
                        else:
                            notify_task_failed(c["task_id"], c["task_name"], c["worker"])
            else:
                sys.stdout.write(f"\r[{datetime.now().strftime('%H:%M:%S')}] 检查中... ({state['checked_count']}次)")
                sys.stdout.flush()

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print(f"\n\n🛑 监控已停止")
        LOCK_FILE.unlink(missing_ok=True)
        state = load_monitor_state()
        state["checked_count"] = state.get("checked_count", 0) + 1
        save_monitor_state(state)
        print(f"📊 共检查 {state['checked_count']} 次，通知 {len(state.get('notified', []))} 个任务")


def stop_monitor():
    if not LOCK_FILE.exists():
        print("⚠️  监控未运行")
        return

    with open(LOCK_FILE) as f:
        pid = f.read().strip()

    try:
        os.kill(int(pid), 15)
        print(f"✅ 监控已停止（PID: {pid}）")
    except (ProcessLookupError, ValueError):
        print(f"⚠️  进程 {pid} 不存在，清理 PID 文件")
    finally:
        LOCK_FILE.unlink()


def show_status():
    state = load_monitor_state()
    print(f"📊 监控状态:")
    print(f"   检查次数: {state.get('checked_count', 0)}")
    print(f"   通知任务: {len(state.get('notified', []))}")

    if LOCK_FILE.exists():
        with open(LOCK_FILE) as f:
            pid = f.read().strip()
        print(f"   监控进程: {pid} (运行中)")
    else:
        print(f"   监控进程: 未运行")

    if LOOP_TASK_DIR.exists():
        tasks = list(LOOP_TASK_DIR.glob("*.json"))
        print(f"\n   任务总计: {len(tasks)}")
        for tf in tasks[-5:]:
            try:
                with open(tf) as f:
                    data = json.load(f)
                print(f"     [{data['status']}] {data['task_id']} — {data['task_name']}")
            except Exception:
                pass


def manual_check():
    changes = run_status_check()
    if not changes:
        print("✅ 所有任务状态正常，无变更")
        return

    for c in changes:
        icon = "🚀" if c["status"] == "dispatched" else ("✅" if c["status"] == "completed" else "❌")
        print(f"{icon} {c['status']}: {c['task_id']} — {c['task_name']} ({c['worker']})")
        if c["status"] == "dispatched":
            notify_task_dispatched(c["task_id"], c["task_name"], c["worker"])
        elif c["status"] == "completed":
            notify_task_complete(c["task_id"], c["task_name"], c["worker"])
        elif c["status"] == "failed":
            notify_task_failed(c["task_id"], c["task_name"], c["worker"])


# ==================== 主入口 ====================

def main():
    if len(sys.argv) < 2:
        print("""
LOOP 监控器 — 自动检查 LOOP 任务状态并推送飞书通知

用法：
  python3 loop_monitor.py start    # 启动监控
  python3 loop_monitor.py stop     # 停止监控
  python3 loop_monitor.py status   # 查看状态
  python3 loop_monitor.py check    # 手动检查一次

配置：
  通过环境变量、.env 文件或 config.json 配置。
  详见 config.py 模块。
""")
        return

    cmd = sys.argv[1]
    if cmd == "start":
        start_monitor()
    elif cmd == "stop":
        stop_monitor()
    elif cmd == "status":
        show_status()
    elif cmd == "check":
        manual_check()
    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()
