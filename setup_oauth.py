#!/usr/bin/env python3
"""
Capacities MCP OAuth 2.1 PKCE Setup.

Registers a Dynamic Client and runs the authorization code flow
to obtain tokens for the Capacities native MCP server.

For headless/server environments:
1. Shows you the auth URL to open in YOUR browser
2. After authorizing, Capacities redirects to 127.0.0.1 (which fails on server)
3. You copy the FAILED redirect URL from your browser's address bar
4. Paste it here, we extract the code and exchange for tokens

Usage:
  python3 /root/.hermes/mcp-servers/capacities/setup_oauth.py
"""

import os
import sys
import json
import base64
import hashlib
import secrets
import urllib.request
import urllib.parse
import urllib.error
import time
import subprocess

# ── Configuration ──────────────────────────────────────────────────────

BASE = "https://api.capacities.io"
MCP_URL = "https://api.capacities.io/mcp"
CALLBACK_PORT = 8765
REDIRECT_URI = f"http://127.0.0.1:{CALLBACK_PORT}/callback"
TOKEN_FILE = os.path.expanduser("~/.hermes/capacities_mcp_oauth.json")
SCOPE = "mcp:read mcp:write"

# ── PKCE ───────────────────────────────────────────────────────────────

def generate_pkce():
    code_verifier = secrets.token_urlsafe(64)[:128]
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")
    state = secrets.token_urlsafe(32)
    return code_verifier, code_challenge, state


# ── HTTP Helpers ──────────────────────────────────────────────────────

def api_post(url, data, auth=None):
    headers = {"Content-Type": "application/json"}
    if auth:
        if isinstance(auth, tuple):
            creds = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
            headers["Authorization"] = f"Basic {creds}"
        else:
            headers["Authorization"] = f"Bearer {auth}"
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
            return json.loads(body) if body.strip() else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"HTTP {e.code}: {body}")


def api_get(url):
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"HTTP {e.code}: {body}")


# ── Register Client ───────────────────────────────────────────────────

def register_client():
    print("Step 1: Registering Dynamic Client with Capacities...")
    client_data = {
        "client_name": "hermes-agent-capacities-mcp",
        "redirect_uris": [REDIRECT_URI],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
        "scope": SCOPE,
    }
    result = api_post(f"{BASE}/oauth/reg", client_data)
    client_id = result["client_id"]
    reg_token = result.get("registration_access_token", "")
    print(f"  ✅ Client registered!")
    print(f"     Client ID: {client_id}")
    return client_id, reg_token


# ── Exchange Code for Tokens ─────────────────────────────────────────

def exchange_code(client_id, code_verifier, code):
    print("\nStep 4: Exchanging authorization code for tokens...")
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": client_id,
        "code_verifier": code_verifier,
    }
    result = api_post(f"{BASE}/oauth/token", data)
    print(f"  ✅ Tokens received!")
    return result


# ── Main ──────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Capacities MCP - OAuth 2.1 PKCE Setup")
    print("=" * 60)
    print()

    # Step 1: Register client
    client_id, reg_token = register_client()

    # Generate PKCE
    code_verifier, code_challenge, state = generate_pkce()

    # Build authorization URL
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "resource": MCP_URL,
    }
    auth_url = f"{BASE}/oauth/authorize?{urllib.parse.urlencode(params)}"

    print(f"\nStep 2: Authorize in your browser")
    print("-" * 60)
    print(f"Open this URL in YOUR browser (on any device):")
    print()
    print(f"  {auth_url}")
    print()
    print("📋  Tip: You can copy this using:")
    print(f'     echo "{auth_url}" | xclip -selection clipboard')
    print()
    print("Step 3: After authorizing, Capacities will try to redirect")
    print(f"to http://127.0.0.1:{CALLBACK_PORT}/callback?code=...&state=...")
    print()
    print("Since this is a headless server, that redirect will fail.")
    print("That's expected! Copy the FULL failed URL from your browser's")
    print("address bar and paste it below.")
    print()

    # Read the callback URL from stdin
    try:
        callback_url = input("Paste the full redirect URL here: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        sys.exit(1)

    if not callback_url:
        print("No URL provided. Exiting.")
        sys.exit(1)

    # Parse the callback URL
    parsed = urllib.parse.urlparse(callback_url)
    qs = urllib.parse.parse_qs(parsed.query)

    if "error" in qs:
        print(f"\n  ❌ Authorization error: {qs['error'][0]}")
        sys.exit(1)

    if "code" not in qs:
        print("\n  ❌ No authorization code found in URL. The URL should contain ?code=...")
        print(f"     Full query: {parsed.query}")
        sys.exit(1)

    received_code = qs["code"][0]
    received_state = qs.get("state", [""])[0]

    if received_state != state:
        print("\n  ❌ State mismatch! Possible CSRF attack.")
        sys.exit(1)

    print(f"\n  ✅ Authorization code received and validated!")

    # Exchange code for tokens
    tokens = exchange_code(client_id, code_verifier, received_code)

    print(f"     Access token:  {tokens.get('access_token', '?')[:30]}...")
    print(f"     Refresh token: {tokens.get('refresh_token', '?')[:30]}...")
    print(f"     Expires in:    {tokens.get('expires_in', '?')} seconds")
    print(f"     Scope:         {tokens.get('scope', '?')}")

    # Save tokens
    token_data = {
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token", ""),
        "expires_in": tokens.get("expires_in", 3600),
        "token_type": tokens.get("token_type", "Bearer"),
        "scope": tokens.get("scope", SCOPE),
        "client_id": client_id,
        "registration_token": reg_token,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier,
        "created_at": int(time.time()),
    }

    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)
    print(f"\n  ✅ Tokens saved to {TOKEN_FILE}")

    # ── Print Hermes config ──────────────────────────────────────────
    print()
    print("=" * 60)
    print("Hermes MCP Configuration")
    print("=" * 60)
    print()
    print("Run this to update Hermes config:")
    print()
    print(f"  hermes config set mcp_servers.capacities_native.url {MCP_URL}")
    print(f'  hermes config set mcp_servers.capacities_native.headers.Authorization "Bearer {tokens["access_token"]}"')
    print(f"  hermes config set mcp_servers.capacities_native.timeout 180")
    print()
    print("Then restart Hermes Agent.")
    print()
    print("To refresh the token later, run:")
    print(f"  python3 /root/.hermes/mcp-servers/capacities/refresh_oauth.py")
    print()

    # Also create the refresh script
    create_refresh_script(client_id, code_verifier)
    print("  ✅ Refresh script created at /root/.hermes/mcp-servers/capacities/refresh_oauth.py")


def create_refresh_script(client_id, code_verifier):
    content = '''#!/usr/bin/env python3
"""Refresh Capacities MCP OAuth token."""

import os, sys, json, time, urllib.request, urllib.parse, urllib.error, subprocess

BASE = "https://api.capacities.io"
TOKEN_FILE = os.path.expanduser("~/.hermes/capacities_mcp_oauth.json")
CONFIG_FILE = os.path.expanduser("~/.hermes/config.yaml")

def load_tokens():
    with open(TOKEN_FILE) as f:
        return json.load(f)

def save_tokens(data):
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
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

    # Update stored tokens
    tokens["access_token"] = result["access_token"]
    if "refresh_token" in result:
        tokens["refresh_token"] = result["refresh_token"]
    tokens["expires_in"] = result.get("expires_in", 3600)
    tokens["created_at"] = int(time.time())
    save_tokens(tokens)

    # Update Hermes config
    at = result["access_token"]
    subprocess.run([
        "hermes", "config", "set",
        "mcp_servers.capacities_native.headers.Authorization",
        f"Bearer {at}"
    ])

    print(f"  Token refreshed! New access token: {at[:30]}...")
    print("  Restart Hermes for the new token to take effect.")

if __name__ == "__main__":
    refresh()
'''
    path = os.path.expanduser("~/.hermes/mcp-servers/capacities/refresh_oauth.py")
    with open(path, "w") as f:
        f.write(content)
    os.chmod(path, 0o755)


if __name__ == "__main__":
    main()
