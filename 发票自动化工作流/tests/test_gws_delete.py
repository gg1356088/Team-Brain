#!/usr/bin/env python3
"""Debug gws delete behavior."""
import json, subprocess, os

token_file = "/Users/xinban/IncepVision Law/Gmail API 邮件管理工具/tokens/office_at_incepvisionlaw.com.json"
with open(token_file) as f:
    data = json.load(f)
client_id = data["client_id"]
client_secret = data["client_secret"]
refresh_token = data["refresh_token"]
resp = subprocess.run(["curl", "-s", "-X", "POST", "https://oauth2.googleapis.com/token",
    "-d", f"client_id={client_id}", "-d", f"client_secret={client_secret}",
    "-d", f"refresh_token={refresh_token}", "-d", "grant_type=refresh_token"],
    capture_output=True, text=True)
access_token = json.loads(resp.stdout)["access_token"]
env = os.environ.copy()
env["GOOGLE_WORKSPACE_CLI_TOKEN"] = access_token
drive_id = "0AHkxgftb0oFyUk9PVA"

# Create test folder
r = subprocess.run(["gws", "drive", "files", "create", "--params", json.dumps({"driveId": drive_id, "supportsAllDrives": True, "corpora": "drive"}), "--json", json.dumps({"name": "gws-delete-test", "mimeType": "application/vnd.google-apps.folder"})], capture_output=True, text=True, env=env)
fid = json.loads(r.stdout)["id"]
print(f"Created folder: {fid}")

# Try delete
r2 = subprocess.run(["gws", "drive", "files", "delete", "--params", json.dumps({"fileId": fid, "supportsAllDrives": True})], capture_output=True, text=True, env=env)
print(f"Delete stdout: {r2.stdout[:200]}")
print(f"Delete stderr: {r2.stderr[:200] if r2.stderr else 'none'}")
print(f"Delete returncode: {r2.returncode}")

# Check if file still exists
r3 = subprocess.run(["gws", "drive", "files", "list", "--params", json.dumps({"driveId": drive_id, "q": "name='gws-delete-test'", "pageSize": 1, "corpora": "drive", "supportsAllDrives": True, "includeItemsFromAllDrives": True})], capture_output=True, text=True, env=env)
result = json.loads(r3.stdout)
print(f"After delete, files found: {len(result.get('files', []))}")
print(f"List returncode: {r3.returncode}")
