#!/usr/bin/env python3
"""Refresh Capacities MCP OAuth token."""

import os, sys, json, time, urllib.request, subprocess

BASE = "https://api.capacities.io"
TOKEN_FILE = os.path.expanduser("~/.hermes/capacities_mcp_oauth.json")

def load_tokens():
    with open(TOKEN_FILE) as f:
        return json.load(f)

def save_tokens(data):
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f, indent=2)

def api_post(url, data):
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
            return json.loads(body) if body.strip() else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"HTTP {e.code}: {body}")

def refresh():
    tokens = load_tokens()
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        print("No refresh token found. Re-run the OAuth setup.")
        sys.exit(1)

    print("Refreshing Capacities MCP token...")
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": tokens["client_id"],
        "scope": "mcp:read mcp:write",
    }
    result = api_post(f"{BASE}/oauth/token", data)

    tokens["access_token"] = result["access_token"]
    if "refresh_token" in result:
        tokens["refresh_token"] = result["refresh_token"]
    tokens["expires_in"] = result.get("expires_in", 3600)
    tokens["created_at"] = int(time.time())
    save_tokens(tokens)

    at = result["access_token"]
    subprocess.run([
        "hermes", "config", "set",
        "mcp_servers.capacities_native.headers.Authorization",
        f"Bearer {at}"
    ])

    print(f"Token refreshed! New access token: {at[:30]}...")
    print("Restart Hermes for the new token to take effect.")

if __name__ == "__main__":
    refresh()
