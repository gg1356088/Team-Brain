#!/usr/bin/env python3
"""Debug shared drive parent issue and test with proper approach."""
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

# Step 1: Create folder
print("Creating test folder...")
folder_body = json.dumps({"name": "gws-parent-test", "mimeType": "application/vnd.google-apps.folder"})
r = subprocess.run(
    ["gws", "drive", "files", "create", "--params", json.dumps({
        "driveId": drive_id, "supportsAllDrives": True, "corpora": "drive"
    }), "--json", folder_body],
    capture_output=True, text=True, env=env
)
folder_result = json.loads(r.stdout)
folder_id = folder_result["id"]
print(f"Folder created: {folder_id}")

# Step 2: Upload file WITH parents in the JSON body
print("\nUploading file with parents in body...")
test_content = "gws CLI upload test\n"
test_file = "./gws_parent_test.txt"
with open(test_file, "w") as f:
    f.write(test_content)

# Combine: --upload for file content, --json for body with parents
body_with_parents = json.dumps({
    "name": "gws_parent_test.txt",
    "parents": [folder_id]
})
r2 = subprocess.run(
    ["gws", "drive", "files", "create", "--params", json.dumps({
        "driveId": drive_id, "supportsAllDrives": True, "corpora": "drive"
    }), "--upload", test_file, "--json", body_with_parents],
    capture_output=True, text=True, env=env
)
print(r2.stdout)
file_id = json.loads(r2.stdout)["id"]
print(f"File created: {file_id}")

# Step 3: Verify parent relationship
print("\nChecking file details...")
r3 = subprocess.run(
    ["gws", "drive", "files", "get", "--params", json.dumps({
        "fileId": file_id, "supportsAllDrives": True
    })],
    capture_output=True, text=True, env=env
)
print(r3.stdout)

# Step 4: List files in folder
print("\nListing files in folder...")
r4 = subprocess.run(
    ["gws", "drive", "files", "list", "--params", json.dumps({
        "driveId": drive_id,
        "q": f"'{folder_id}' in parents",
        "pageSize": 5,
        "corpora": "drive",
        "supportsAllDrives": True,
        "includeItemsFromAllDrives": True
    })],
    capture_output=True, text=True, env=env
)
print(r4.stdout)

# Step 5: Download to current directory
print("\nDownloading file to verify content...")
r5 = subprocess.run(
    ["gws", "drive", "files", "get", "--params", json.dumps({
        "fileId": file_id, "supportsAllDrives": True
    }), "--output", "gws_verify_output.txt"],
    capture_output=True, text=True, env=env
)
print(r5.stdout)
if os.path.exists("gws_verify_output.txt"):
    with open("gws_verify_output.txt") as f:
        print(f"Verified content: {f.read().strip()}")

# Cleanup
print("\nCleaning up...")
os.remove(test_file)
if os.path.exists("gws_verify_output.txt"):
    os.remove("gws_verify_output.txt")

r6 = subprocess.run(
    ["gws", "drive", "files", "delete", "--params", json.dumps({
        "fileId": file_id, "supportsAllDrives": True
    })],
    capture_output=True, text=True, env=env
)
print(f"Delete file: {r6.stdout}")

r7 = subprocess.run(
    ["gws", "drive", "files", "delete", "--params", json.dumps({
        "fileId": folder_id, "supportsAllDrives": True
    })],
    capture_output=True, text=True, env=env
)
print(f"Delete folder: {r7.stdout}")
print("Done!")
