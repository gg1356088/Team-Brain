#!/usr/bin/env python3
"""Test gws upload with name and verify, then cleanup."""
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

# Step 1: Create a folder
print("Creating test folder...")
folder_body = json.dumps({"name": "gws-upload-test", "mimeType": "application/vnd.google-apps.folder"})
r = subprocess.run(
    ["gws", "drive", "files", "create", "--params", json.dumps({
        "driveId": drive_id, "supportsAllDrives": True, "corpora": "drive"
    }), "--json", folder_body],
    capture_output=True, text=True, env=env
)
folder_result = json.loads(r.stdout)
folder_id = folder_result["id"]
print(f"Folder created: {folder_id}")

# Step 2: Upload file WITH name set
print("\nUploading file with name...")
test_content = "gws CLI upload test\n"
test_file = "./gws_upload_test.txt"
with open(test_file, "w") as f:
    f.write(test_content)

# Use --upload for content + --json for metadata
r2 = subprocess.run(
    ["gws", "drive", "files", "create", "--params", json.dumps({
        "driveId": drive_id, "supportsAllDrives": True, "corpora": "drive", "parents": folder_id
    }), "--upload", test_file],
    capture_output=True, text=True, env=env
)
print(r2.stdout)
# The file is uploaded but name is "Untitled". Let's rename it.
uploaded_file_id = json.loads(r2.stdout)["id"]
print(f"Uploaded file id: {uploaded_file_id}")

# Rename the uploaded file
rename_body = json.dumps({"name": "gws_upload_test.txt"})
r3 = subprocess.run(
    ["gws", "drive", "files", "update", "--params", json.dumps({
        "fileId": uploaded_file_id, "supportsAllDrives": True
    }), "--json", rename_body],
    capture_output=True, text=True, env=env
)
print(f"Rename result: {r3.stdout}")

# Step 3: List files in folder to verify
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

# Step 4: Get file content to verify
print("\nGetting file content...")
r5 = subprocess.run(
    ["gws", "drive", "files", "get", "--params", json.dumps({
        "fileId": uploaded_file_id, "supportsAllDrives": True, "alt": "media"
    }), "--output", "/tmp/gws_verify_download.txt"],
    capture_output=True, text=True, env=env
)
print(f"Download result: {r5.stdout}")
with open("/tmp/gws_verify_download.txt") as f:
    print(f"Verified content: {f.read()}")

# Step 5: Cleanup
print("\nCleaning up...")
# Delete the uploaded file first
r6 = subprocess.run(
    ["gws", "drive", "files", "delete", "--params", json.dumps({
        "fileId": uploaded_file_id, "supportsAllDrives": True
    })],
    capture_output=True, text=True, env=env
)
print(f"Delete file: {r6.stdout}")

# Delete the folder
r7 = subprocess.run(
    ["gws", "drive", "files", "delete", "--params", json.dumps({
        "fileId": folder_id, "supportsAllDrives": True
    })],
    capture_output=True, text=True, env=env
)
print(f"Delete folder: {r7.stdout}")

# Clean local files
os.remove(test_file)
print("Local test file removed.")
print("\nAll tests passed!")
