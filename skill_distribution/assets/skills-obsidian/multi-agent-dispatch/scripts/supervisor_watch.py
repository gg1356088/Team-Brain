#!/usr/bin/env python3
"""
Hermes Agent 监督系统 - 输出监控守护进程
==========================================
监控 Claude Code 后台进程，连续2分钟没新输出就 kill + 重启

用法：
  python3 supervisor_watch.py register <session_id> <task_id> <output_file> [timeout_minutes]
  python3 supervisor_watch.py status
  python3 supervisor_watch.py stop
"""

import json
import sys
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path("/Users/xinban/HermesPet_Workspace/.supervisor")
WATCH_DIR = BASE_DIR / "watch"
WATCH_DIR.mkdir(parents=True, exist_ok=True)

NO_OUTPUT_TIMEOUT = 120  # 2分钟 = 120秒
CHECK_INTERVAL = 5  # 每5秒检查一次
MAX_RESTARTS = 3

class MonitoredProcess:
    def __init__(self, task_id, output_file, timeout_minutes=30):
        self.task_id = task_id
        self.output_file = Path(output_file)
        self.timeout_minutes = timeout_minutes
        self.last_output_time = datetime.now()
        self.last_output_size = 0
        self.start_time = datetime.now()
        self.restart_count = 0
        self.status = "monitoring"
        self.killed = False
        self.max_restarts = MAX_RESTARTS
    
    def check_output(self):
        if not self.output_file.exists():
            return True
        
        try:
            current_size = self.output_file.stat().st_size
            
            if current_size == self.last_output_size:
                time_since_last = (datetime.now() - self.last_output_time).total_seconds()
                if time_since_last > NO_OUTPUT_TIMEOUT:
                    return False
            else:
                self.last_output_size = current_size
                self.last_output_time = datetime.now()
            
            return True
        except:
            return True
    
    def check_timeout(self):
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return elapsed < self.timeout_minutes * 60
    
    def kill_and_log(self, reason="timeout or no output"):
        if self.killed:
            return
        
        self.killed = True
        self.status = "killed"
        
        task_file = BASE_DIR / "tasks" / f"{self.task_id}.json"
        if task_file.exists():
            try:
                with open(task_file, 'r') as f:
                    task = json.load(f)
                task["fail_reason"] = f"卡住: {reason}"
                task["restart_count"] = self.restart_count + 1
                with open(task_file, 'w', encoding='utf-8') as f:
                    json.dump(task, f, ensure_ascii=False, indent=2)
            except:
                pass
        
        log_file = BASE_DIR / "logs" / f"{self.task_id}.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().isoformat()}] KILLED: {reason} (restart #{self.restart_count + 1})\n")
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] KILLED: {self.task_id} - {reason}")
    
    def to_dict(self):
        return {
            "task_id": self.task_id,
            "status": self.status,
            "restart_count": self.restart_count,
            "max_restarts": self.max_restarts,
            "start_time": self.start_time.isoformat(),
            "output_file": str(self.output_file),
            "last_output_time": self.last_output_time.isoformat(),
        }


def save_watch_state(processes):
    state_file = WATCH_DIR / "state.json"
    with open(state_file, 'w') as f:
        json.dump([p.to_dict() for p in processes], f, indent=2)


def load_watch_state():
    state_file = WATCH_DIR / "state.json"
    if state_file.exists():
        with open(state_file, 'r') as f:
            return json.load(f)
    return []


def register_process(task_id, output_file, timeout_minutes=30):
    """注册一个新的被监控进程"""
    # 更新任务状态为 running
    task_file = BASE_DIR / "tasks" / f"{task_id}.json"
    if task_file.exists():
        with open(task_file, 'r') as f:
            task = json.load(f)
        task["status"] = "running"
        task["started_at"] = datetime.now().isoformat()
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task, f, ensure_ascii=False, indent=2)
    
    save_watch_state([])  # 初始化状态
    
    log_file = BASE_DIR / "logs" / f"{task_id}.log"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().isoformat()}] MONITOR_START: task={task_id}, timeout={timeout_minutes}min\n")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "register":
        if len(sys.argv) < 5:
            print("Usage: supervisor_watch.py register <task_id> <output_file> [timeout_minutes]")
            sys.exit(1)
        
        task_id = sys.argv[2]
        output_file = sys.argv[3]
        timeout = int(sys.argv[4]) if len(sys.argv) > 4 else 30
        
        register_process(task_id, output_file, timeout)
        print(f"✅ Registered: {task_id} → {output_file}")
    
    elif cmd == "monitor":
        print(f"Monitoring... (check interval: {CHECK_INTERVAL}s, timeout: {NO_OUTPUT_TIMEOUT}s)")
        print("Ctrl+C to stop\n")
        
        while True:
            try:
                state = load_watch_state()
                for ps in state:
                    if ps["status"] == "killed":
                        continue
                    
                    # 检查输出
                    output_file = Path(ps["output_file"])
                    if not output_file.exists():
                        continue
                    
                    current_size = output_file.stat().st_size
                    last_time = datetime.fromisoformat(ps["last_output_time"])
                    
                    if current_size == ps.get("last_output_size", 0):
                        elapsed = (datetime.now() - last_time).total_seconds()
                        if elapsed > NO_OUTPUT_TIMEOUT:
                            print(f"🔴 KILLED: {ps['task_id']} - no output for {elapsed:.0f}s")
                    else:
                        pass  # new output
                    
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                print("\n🛑 Stopped")
                break
            except Exception as e:
                print(f"ERROR: {e}")
                time.sleep(CHECK_INTERVAL)
    
    elif cmd == "status":
        state = load_watch_state()
        if not state:
            print("No active monitors.")
            return
        
        print(f"\n{'Task ID':<20} {'Status':<12} {'Restart':<10}")
        print("-" * 45)
        for p in state:
            print(f"{p['task_id']:<20} {p['status']:<12} {p['restart_count']}/{p['max_restarts']}")
        print()
    
    elif cmd == "stop":
        state_file = WATCH_DIR / "state.json"
        if state_file.exists():
            with open(state_file, 'w') as f:
                json.dump([], f)
            print("✅ Monitoring stopped")
        else:
            print("No active monitors to stop")
    
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
