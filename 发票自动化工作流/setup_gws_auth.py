#!/usr/bin/env python3
"""Set up gws with existing credentials so auth persists."""
import json, subprocess, os

token_file = "/Users/xinban/IncepVision Law/Gmail API 邮件管理工具/tokens/office_at_incepvisionlaw.com.json"
with open(token_file) as f:
    data = json.load(f)

client_id = data["client_id"]
client_secret = data["client_secret"]

# Write client_secret.json to gws config dir
config_dir = os.path.expanduser("~/.config/gws")
os.makedirs(config_dir, exist_ok=True)

client_secret_path = os.path.join(config_dir, "client_secret.json")
client_data = {
    "installed": {
        "client_id": client_id,
        "client_secret": client_secret,
        "project_id": None,
        "project_name": None
    }
}
with open(client_secret_path, "w") as f:
    json.dump(client_data, f, indent=2)
print(f"Wrote client_secret.json to {client_secret_path}")

# Now try to set up gws auth
# The refresh_token can be used to get a new access token
refresh_token = data["refresh_token"]
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
    # Write credentials.json manually so gws auth status picks it up
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
    print(f"Wrote credentials.json to {creds_path}")
    
    # Check auth status
    r = subprocess.run(["gws", "auth", "status"], capture_output=True, text=True)
    print(f"\nAuth status:\n{r.stdout}")
    print(f"Exit code: {r.returncode}")
else:
    print("Failed to refresh token:", resp.stdout)
