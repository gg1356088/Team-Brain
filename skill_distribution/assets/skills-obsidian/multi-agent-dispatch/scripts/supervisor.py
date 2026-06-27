#!/usr/bin/env python3
"""
Hermes Agent 监督系统 - 任务管理核心
================================
派任务时：写 task.json
检查时：读 task.json，判断状态
验收时：按规则检查文件质量
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path("/Users/xinban/HermesPet_Workspace/.supervisor/tasks")
LOG_DIR = Path("/Users/xinban/HermesPet_Workspace/.supervisor/logs")
BASE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

def task_file(task_id):
    return BASE_DIR / f"{task_id}.json"

def log_file(task_id):
    return LOG_DIR / f"{task_id}.log"

def create_task(task_name, task_id, context=None):
    tf = task_file(task_id)
    if tf.exists():
        print(f"ERROR: Task {task_id} already exists")
        sys.exit(1)
    
    task = {
        "task_id": task_id,
        "task_name": task_name,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None,
        "assignee": "claude-code",
        "timeout_minutes": 30,
        "expected_files": [],
        "verification_rules": [],
        "notes": context or "",
        "actual_files": [],
        "verify_result": None,
        "fail_reason": None,
        "retry_count": 0,
        "max_retries": 2,
    }
    
    with open(tf, 'w', encoding='utf-8') as f:
        json.dump(task, f, ensure_ascii=False, indent=2)
    
    with open(log_file(task_id), 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().isoformat()}] TASK_CREATED: {task_name}\n")
    
    print(f"OK: Created task {task_id} ({task_name})")

def update_status(task_id, status, reason=None):
    tf = task_file(task_id)
    if not tf.exists():
        print(f"ERROR: Task {task_id} not found")
        sys.exit(1)
    
    with open(tf, 'r') as f:
        task = json.load(f)
    
    old_status = task["status"]
    task["status"] = status
    
    if status == "running":
        task["started_at"] = datetime.now().isoformat()
    elif status in ("completed", "failed"):
        task["completed_at"] = datetime.now().isoformat()
    
    if reason:
        task["notes"] += f"\n[{datetime.now().isoformat()}] {status}: {reason}"
    
    with open(tf, 'w', encoding='utf-8') as f:
        json.dump(task, f, ensure_ascii=False, indent=2)
    
    with open(log_file(task_id), 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().isoformat()}] STATUS_CHANGE: {old_status} → {status}\n")
    
    print(f"OK: {task_id} → {status}")

def set_verification(task_id, expected_files, rules=None):
    tf = task_file(task_id)
    if not tf.exists():
        print(f"ERROR: Task {task_id} not found")
        sys.exit(1)
    
    with open(tf, 'r') as f:
        task = json.load(f)
    
    task["expected_files"] = expected_files
    if rules:
        task["verification_rules"] = rules
    
    with open(tf, 'w', encoding='utf-8') as f:
        json.dump(task, f, ensure_ascii=False, indent=2)
    
    with open(log_file(task_id), 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().isoformat()}] VERIFICATION_SET: files={expected_files}\n")
    
    print(f"OK: Verification rules set for {task_id}")

def verify_task(task_id):
    """执行自动验收"""
    tf = task_file(task_id)
    if not tf.exists():
        print(f"ERROR: Task {task_id} not found")
        sys.exit(1)
    
    with open(tf, 'r') as f:
        task = json.load(f)
    
    if task["status"] == "pending":
        print(f"SKIP: Task {task_id} is pending, not started yet")
        return
    
    results = []
    all_pass = True
    errors = []
    
    if task.get("started_at"):
        started = datetime.fromisoformat(task["started_at"])
        timeout = timedelta(minutes=task.get("timeout_minutes", 30))
        if datetime.now() - started > timeout:
            all_pass = False
            errors.append(f"TIMEOUT: Exceeded {task['timeout_minutes']} minutes")
    
    for ef in task.get("expected_files", []):
        path = Path(ef) if not str(ef).startswith("/") else Path(ef)
        candidates = [
            path,
            Path(f"/Users/xinban/HermesPet_Workspace/{ef}"),
            Path(f"/Users/xinban/{ef}"),
        ]
        found = False
        for c in candidates:
            if c.exists():
                found = True
                if ef not in task.get("actual_files", []):
                    task.setdefault("actual_files", []).append(str(c))
                break
        
        if not found:
            all_pass = False
            errors.append(f"MISSING: {ef}")
        else:
            results.append(f"FILE_OK: {ef}")
    
    for ef in task.get("expected_files", []):
        path = None
        for candidate in [
            Path(ef) if str(ef).startswith("/") else Path(f"/Users/xinban/HermesPet_Workspace/{ef}"),
        ]:
            if candidate.exists():
                path = candidate
                break
        
        if path and path.exists():
            stat = path.stat()
            size_kb = stat.st_size / 1024
            results.append(f"SIZE: {ef} = {size_kb:.1f}KB")
            
            if size_kb < 1:
                all_pass = False
                errors.append(f"TOO_SMALL: {ef} ({size_kb:.1f}KB < 1KB)")
    
    for rule in task.get("verification_rules", []):
        if rule.get("type") == "contains":
            path = Path(rule["path"]) if str(rule["path"]).startswith("/") else Path(f"/Users/xinban/HermesPet_Workspace/{rule['path']}")
            if path.exists():
                content = path.read_text(encoding='utf-8', errors='ignore')
                if rule["keyword"] in content:
                    results.append(f"CONTENT_OK: {rule['path']} contains '{rule['keyword']}'")
                else:
                    all_pass = False
                    errors.append(f"CONTENT_MISSING: {rule['path']} missing '{rule['keyword']}'")
    
    task["verify_result"] = "PASS" if all_pass else "FAIL"
    task["fail_reason"] = "; ".join(errors) if errors else None
    
    with open(tf, 'w', encoding='utf-8') as f:
        json.dump(task, f, ensure_ascii=False, indent=2)
    
    with open(log_file(task_id), 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().isoformat()}] VERIFICATION: {'PASS' if all_pass else 'FAIL'}\n")
        for r in results:
            f.write(f"  {r}\n")
        for e in errors:
            f.write(f"  ERR: {e}\n")
    
    print(f"\n=== Task {task_id} Verification ===")
    print(f"Status: {'✅ PASS' if all_pass else '❌ FAIL'}")
    for r in results:
        print(f"  {r}")
    for e in errors:
        print(f"  ❌ {e}")
    
    if not all_pass and task["retry_count"] < task.get("max_retries", 2):
        print(f"\n⚠️  Auto-retry {task['retry_count'] + 1}/{task['max_retries']}")
        task["retry_count"] += 1
        task["status"] = "pending"
        with open(tf, 'w', encoding='utf-8') as f:
            json.dump(task, f, ensure_ascii=False, indent=2)
        print("Task reset to 'pending' for retry")
    
    return all_pass

def show_status(task_id=None):
    """显示任务状态"""
    if task_id:
        tf = task_file(task_id)
        if not tf.exists():
            print(f"ERROR: Task {task_id} not found")
            sys.exit(1)
        with open(tf, 'r') as f:
            task = json.load(f)
        
        print(f"\n{'='*50}")
        print(f"Task: {task['task_name']}")
        print(f"ID:   {task['task_id']}")
        print(f"Status: {task['status']}")
        print(f"Assignee: {task.get('assignee', 'unknown')}")
        print(f"Created: {task['created_at']}")
        if task.get('started_at'):
            print(f"Started: {task['started_at']}")
        if task.get('completed_at'):
            print(f"Completed: {task['completed_at']}")
        
        if task.get('started_at') and not task.get('completed_at'):
            started = datetime.fromisoformat(task['started_at'])
            elapsed = datetime.now() - started
            print(f"Elapsed: {elapsed}")
        
        print(f"Expected files: {task.get('expected_files', [])}")
        print(f"Actual files: {task.get('actual_files', [])}")
        
        if task.get('verify_result'):
            print(f"Verify: {'✅ PASS' if task['verify_result'] == 'PASS' else '❌ FAIL'}")
        
        if task.get('fail_reason'):
            print(f"Fail reason: {task['fail_reason']}")
        
        print(f"Retries: {task.get('retry_count', 0)}/{task.get('max_retries', 2)}")
        print(f"{'='*50}")
        
        log = log_file(task_id)
        if log.exists():
            print(f"\n--- Log ---")
            print(log.read_text(encoding='utf-8'))
    else:
        tasks = sorted(BASE_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        if not tasks:
            print("No tasks found.")
            return
        
        print(f"\n{'ID':<20} {'Name':<30} {'Status':<10} {'Time':<10}")
        print("-" * 70)
        for tf in tasks:
            with open(tf, 'r') as f:
                task = json.load(f)
            print(f"{task['task_id']:<20} {task['task_name']:<30} {task['status']:<10} {task.get('created_at', '')[:10]}")
        print(f"\nTotal: {len(tasks)} tasks")

def mark_complete(task_id):
    update_status(task_id, "completed", "Manually marked complete")

def mark_fail(task_id, reason):
    update_status(task_id, "failed", reason)

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "create":
        if len(sys.argv) < 4:
            print("Usage: supervisor.py create <task_name> <task_id>")
            sys.exit(1)
        context = sys.argv[3] if len(sys.argv) > 3 else None
        create_task(sys.argv[2], sys.argv[3], context)
    
    elif cmd == "update":
        if len(sys.argv) < 4:
            print("Usage: supervisor.py update <task_id> <status> [reason]")
            sys.exit(1)
        update_status(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
    
    elif cmd == "verify":
        if len(sys.argv) < 3:
            print("Usage: supervisor.py verify <task_id>")
            sys.exit(1)
        verify_task(sys.argv[2])
    
    elif cmd == "status":
        show_status(sys.argv[2] if len(sys.argv) > 2 else None)
    
    elif cmd == "verify_set":
        if len(sys.argv) < 4:
            print("Usage: supervisor.py verify_set <task_id> <file1,file2,...> [keyword1,keyword2]")
            sys.exit(1)
        files = sys.argv[3].split(",")
        rules = []
        if len(sys.argv) > 4:
            keywords = sys.argv[4].split(",")
            for f in files:
                rules.append({"type": "contains", "path": f.strip(), "keyword": keywords[0].strip()})
        set_verification(sys.argv[2], [f.strip() for f in files], rules)
    
    elif cmd == "complete":
        if len(sys.argv) < 3:
            print("Usage: supervisor.py complete <task_id>")
            sys.exit(1)
        mark_complete(sys.argv[2])
    
    elif cmd == "fail":
        if len(sys.argv) < 4:
            print("Usage: supervisor.py fail <task_id> <reason>")
            sys.exit(1)
        mark_fail(sys.argv[2], sys.argv[3])
    
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
