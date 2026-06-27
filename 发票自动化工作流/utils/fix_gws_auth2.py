#!/usr/bin/env python3
"""Properly format gws credentials files."""
import json, subprocess, os

token_file = "/Users/xinban/IncepVision Law/Gmail API 邮件管理工具/tokens/office_at_incepvisionlaw.com.json"
with open(token_file) as f:
    data = json.load(f)

client_id = data["client_id"]
client_secret = data["client_secret"]
refresh_token = data["refresh_token"]

config_dir = os.path.expanduser("~/.config/gws")

# Format client_secret.json exactly as gws expects
client_secret_path = os.path.join(config_dir, "client_secret.json")
client_data = {
    "installed": {
        "client_id": client_id,
        "client_secret": client_secret,
        "project_id": "",
        "project_name": ""
    }
}
with open(client_secret_path, "w") as f:
    json.dump(client_data, f, indent=2)

# Refresh token
resp = subprocess.run(
    ["curl", "-s", "-X", "POST", "https://oauth2.googleapis.com/token",
     "-d", f"client_id={client_id}",
     "-d", f"client_secret={client_secret}",
     "-d", f"refresh_token={refresh_token}",
     "-d", "grant_type=refresh_token"],
    capture_output=True, text=True
)
result = json.loads(resp.stdout)
access_token = result["access_token"]

# Write credentials.json with proper structure
# gws expects: {"installed": {...}, "token": {"access_token":..., "refresh_token":..., ...}}
creds_path = os.path.join(config_dir, "credentials.json")
creds_data = {
    "installed": {
        "client_id": client_id,
        "client_secret": client_secret
    },
    "token": {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": client_id,
        "client_secret": client_secret,
        "scopes": data.get("scopes", []),
        "type": "Authorized"
    }
}
with open(creds_path, "w") as f:
    json.dump(creds_data, f, indent=2)

print("=== client_secret.json ===")
with open(client_secret_path) as f:
    print(f.read())

print("\n=== credentials.json ===")
with open(creds_path) as f:
    print(f.read())

# Check auth status
r = subprocess.run(["gws", "auth", "status"], capture_output=True, text=True)
print(f"\nAuth status:\n{r.stdout}")
