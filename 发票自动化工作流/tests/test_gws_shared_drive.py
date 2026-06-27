#!/usr/bin/env python3
"""Test gws shared drive operations."""
import json
import subprocess
import os

token_file = "/Users/xinban/IncepVision Law/Gmail API 邮件管理工具/tokens/office_at_incepvisionlaw.com.json"
with open(token_file) as f:
    data = json.load(f)

# Refresh token
client_id = data["client_id"]
client_secret = data["client_secret"]
refresh_token = data["refresh_token"]

resp = subprocess.run(
    ["curl", "-s", "-X", "POST", "https://oauth2.googleapis.com/token",
     "-d", f"client_id={client_id}",
     "-d", f"client_secret={client_secret}",
     "-d", f"refresh_token={refresh_token}",
     "-d", "grant_type=refresh_token"],
    capture_output=True, text=True
)
access_token = json.loads(resp.stdout)["access_token"]

env = os.environ.copy()
env["GOOGLE_WORKSPACE_CLI_TOKEN"] = access_token

# Test 1: List shared drives
print("=" * 60)
print("TEST 1: List shared drives")
print("=" * 60)
r = subprocess.run(
    ["gws", "drive", "drives", "list"],
    capture_output=True, text=True, env=env
)
print(r.stdout[:2000])
if r.stderr:
    print("STDERR:", r.stderr)
print("Exit code:", r.returncode)

# Parse shared drives to get IDs
drives = json.loads(r.stdout).get("drives", [])
if drives:
    for d in drives:
        print(f"  Drive: {d['name']} (id={d['id']})")
    drive_id = drives[0]["id"]
    print(f"\nUsing first shared drive: {drive_id}")
    
    # Test 2: List files in shared drive root
    print("\n" + "=" * 60)
    print("TEST 2: List files in shared drive root")
    print("=" * 60)
    r2 = subprocess.run(
        ["gws", "drive", "files", "list", "--params",
         json.dumps({"driveId": drive_id, "pageSize": 10, "corpora": "drive", "includeItemsFromAllDrives": True})],
        capture_output=True, text=True, env=env
    )
    print(r2.stdout[:2000])
    if r2.stderr:
        print("STDERR:", r2.stderr)
    print("Exit code:", r2.returncode)
    
    # Test 3: Create a folder in shared drive
    print("\n" + "=" * 60)
    print("TEST 3: Create sub-folder in shared drive")
    print("=" * 60)
    folder_body = json.dumps({
        "name": "gws-test-folder",
        "mimeType": "application/vnd.google-apps.folder",
        "parents": ["root"],
        "driveId": drive_id,
        "supportsAllDrives": True
    })
    r3 = subprocess.run(
        ["gws", "drive", "files", "create", "--params", json.dumps({
            "driveId": drive_id,
            "supportsAllDrives": True,
            "corpora": "drive"
        }), "--json", folder_body],
        capture_output=True, text=True, env=env
    )
    print(r3.stdout[:2000])
    if r3.stderr:
        print("STDERR:", r3.stderr)
    print("Exit code:", r3.returncode)
    
    # Extract new folder ID
    if '"id"' in r3.stdout:
        new_folder = json.loads(r3.stdout)
        folder_id = new_folder["id"]
        print(f"Created folder with ID: {folder_id}")
        
        # Test 4: Upload a small text file to the shared drive folder
        print("\n" + "=" * 60)
        print("TEST 4: Upload a test file to the created folder")
        print("=" * 60)
        # Create a test file
        test_content = "This is a test file created by gws CLI.\nDate: 2026-06-16"
        test_file = "/tmp/gws_test_upload.txt"
        with open(test_file, "w") as f:
            f.write(test_content)
        
        r4 = subprocess.run(
            ["gws", "drive", "files", "create", "--params", json.dumps({
                "driveId": drive_id,
                "supportsAllDrives": True,
                "corpora": "drive",
                "parents": folder_id
            }), "--upload", test_file],
            capture_output=True, text=True, env=env
        )
        print(r4.stdout[:2000])
        if r4.stderr:
            print("STDERR:", r4.stderr)
        print("Exit code:", r4.returncode)
    
    # Cleanup: delete the test folder
    print("\n" + "=" * 60)
    print("TEST 5: Cleanup - delete test folder")
    print("=" * 60)
    if drives:
        # Need to find the folder we just created
        r5 = subprocess.run(
            ["gws", "drive", "files", "list", "--params",
             json.dumps({"driveId": drive_id, "q": "name='gws-test-folder'", "pageSize": 1})],
            capture_output=True, text=True, env=env
        )
        files = json.loads(r5.stdout).get("files", [])
        if files:
            fid = files[0]["id"]
            r5b = subprocess.run(
                ["gws", "drive", "files", "delete", "--params", json.dumps({
                    "supportsAllDrives": True
                })],
                capture_output=True, text=True, env=env,
                input=f'--params \'{{"fileId": "{fid}"}}\''
            )
            # gws delete takes fileId as param, not body
            # Let's try the right way
            r5c = subprocess.run(
                ["gws", "drive", "files", "delete", "--params",
                 json.dumps({"fileId": fid, "supportsAllDrives": True})],
                capture_output=True, text=True, env=env
            )
            print(r5c.stdout[:1000])
            print("Exit code:", r5c.returncode)
        else:
            print("Test folder not found (may have been deleted already)")
    print("Cleanup done.")
