#!/usr/bin/env python3
"""Refresh Google OAuth token and set up gws CLI."""
import json
import subprocess
import sys
import os

token_file = "/Users/xinban/IncepVision Law/Gmail API 邮件管理工具/tokens/office_at_incepvisionlaw.com.json"

with open(token_file) as f:
    data = json.load(f)

client_id = data["client_id"]
client_secret = data["client_secret"]
refresh_token = data["refresh_token"]

print(f"Client ID: {client_id}")
print(f"Refresh Token: {refresh_token[:30]}...")

# Refresh the access token
resp = subprocess.run(
    ["curl", "-s", "-X", "POST", "https://oauth2.googleapis.com/token",
     "-d", f"client_id={client_id}",
     "-d", f"client_secret={client_secret}",
     "-d", f"refresh_token={refresh_token}",
     "-d", "grant_type=refresh_token"],
    capture_output=True, text=True
)
result = json.loads(resp.stdout)
if "access_token" in result:
    access_token = result["access_token"]
    print(f"\nGot new access token: {access_token[:50]}...")
    
    # Export as env var for gws
    env = os.environ.copy()
    env["GOOGLE_WORKSPACE_CLI_TOKEN"] = access_token
    
    # Test drive files list
    print("\n--- Testing: gws drive files list ---")
    r = subprocess.run(
        ["gws", "drive", "files", "list", "--params", '{"pageSize": 5}'],
        capture_output=True, text=True, env=env
    )
    print(r.stdout)
    if r.stderr:
        print("STDERR:", r.stderr)
    print("Exit code:", r.returncode)
else:
    print("ERROR refreshing token:", result)
    sys.exit(1)
