#!/usr/bin/env python3
"""Test gws shared drive operations - v3 fixes."""
import json
import subprocess
import os

token_file = "/Users/xinban/IncepVision Law/Gmail API 邮件管理工具/tokens/office_at_incepvisionlaw.com.json"
with open(token_file) as f:
    data = json.load(f)

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

drive_id = "0AHkxgftb0oFyUk9PVA"

# Test 1: List files in shared drive root (fixed params)
print("=" * 60)
print("TEST 1: List files in shared drive root")
print("=" * 60)
params = {
    "driveId": drive_id,
    "pageSize": 10,
    "corpora": "drive",
    "supportsAllDrives": True,
    "includeItemsFromAllDrives": True
}
r1 = subprocess.run(
    ["gws", "drive", "files", "list", "--params", json.dumps(params)],
    capture_output=True, text=True, env=env
)
print(r1.stdout[:3000])
if r1.stderr:
    print("STDERR:", r1.stderr)
print("Exit code:", r1.returncode)

# Test 2: Create a folder in shared drive
print("\n" + "=" * 60)
print("TEST 2: Create sub-folder in shared drive")
print("=" * 60)
folder_body = json.dumps({
    "name": "gws-test-folder-2",
    "mimeType": "application/vnd.google-apps.folder"
})
r2 = subprocess.run(
    ["gws", "drive", "files", "create", "--params", json.dumps({
        "driveId": drive_id,
        "supportsAllDrives": True,
        "corpora": "drive"
    }), "--json", folder_body],
    capture_output=True, text=True, env=env
)
print(r2.stdout)
if r2.stderr:
    print("STDERR:", r2.stderr)
print("Exit code:", r2.returncode)

new_folder_id = None
if '"id"' in r2.stdout:
    new_folder = json.loads(r2.stdout)
    new_folder_id = new_folder["id"]
    print(f"Created folder with ID: {new_folder_id}")
    
    # Test 3: Create a sub-sub-folder inside it
    print("\n" + "=" * 60)
    print("TEST 3: Create sub-sub-folder")
    print("=" * 60)
    sub_folder_body = json.dumps({
        "name": "sub-folder-test",
        "mimeType": "application/vnd.google-apps.folder"
    })
    r3 = subprocess.run(
        ["gws", "drive", "files", "create", "--params", json.dumps({
            "driveId": drive_id,
            "supportsAllDrives": True,
            "corpora": "drive"
        }), "--json", sub_folder_body],
        capture_output=True, text=True, env=env
    )
    print(r3.stdout)
    if r3.stderr:
        print("STDERR:", r3.stderr)
    print("Exit code:", r3.returncode)
    
    # Test 4: Upload a file using multipart (upload in working dir)
    print("\n" + "=" * 60)
    print("TEST 4: Upload a test file")
    print("=" * 60)
    # Put the test file in the working directory
    test_file = "./gws_test_upload.txt"
    with open(test_file, "w") as f:
        f.write("This is a test file created by gws CLI.\nDate: 2026-06-16\nAccount: office@incepvisionlaw.com")
    
    r4 = subprocess.run(
        ["gws", "drive", "files", "create", "--params", json.dumps({
            "driveId": drive_id,
            "supportsAllDrives": True,
            "corpora": "drive",
            "parents": new_folder_id
        }), "--upload", test_file],
        capture_output=True, text=True, env=env
    )
    print(r4.stdout[:2000])
    if r4.stderr:
        print("STDERR:", r4.stderr)
    print("Exit code:", r4.returncode)
    
    # Test 5: List files in the created folder to verify
    print("\n" + "=" * 60)
    print("TEST 5: List files in the created folder")
    print("=" * 60)
    r5 = subprocess.run(
        ["gws", "drive", "files", "list", "--params", json.dumps({
            "driveId": drive_id,
            "q": f"'{new_folder_id}' in parents",
            "pageSize": 5,
            "corpora": "drive",
            "supportsAllDrives": True,
            "includeItemsFromAllDrives": True
        })],
        capture_output=True, text=True, env=env
    )
    print(r5.stdout[:2000])
    if r5.stderr:
        print("STDERR:", r5.stderr)
    print("Exit code:", r5.returncode)
    
    # Cleanup
    print("\n" + "=" * 60)
    print("CLEANUP: Delete test folder")
    print("=" * 60)
    # First find the folder to delete
    r_clean = subprocess.run(
        ["gws", "drive", "files", "list", "--params", json.dumps({
            "driveId": drive_id,
            "q": "name='gws-test-folder-2'",
            "pageSize": 1,
            "corpora": "drive",
            "supportsAllDrives": True,
            "includeItemsFromAllDrives": True
        })],
        capture_output=True, text=True, env=env
    )
    files = json.loads(r_clean.stdout).get("files", [])
    if files:
        fid = files[0]["id"]
        print(f"Found folder to delete: {fid}")
        r_del = subprocess.run(
            ["gws", "drive", "files", "delete", "--params", json.dumps({
                "fileId": fid,
                "supportsAllDrives": True
            })],
            capture_output=True, text=True, env=env
        )
        print(r_del.stdout[:500])
        print("Exit code:", r_del.returncode)
    
    # Remove local test file
    os.remove(test_file)
    print("Cleanup done.")
