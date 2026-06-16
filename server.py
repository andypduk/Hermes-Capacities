#!/usr/bin/env python3
"""Capacities MCP Server — Hermes Agent Integration.

Wraps the Capacities REST API (beta v0.1.0) as MCP tools for AI agents.
Supports any MCP-compatible host (Claude Desktop, Hermes Agent, Cursor, etc.).

API docs: https://docs.capacities.io/developer/api
OpenAPI: https://api.capacities.io/docs

Auth: Bearer token from Capacities desktop app (Settings > Capacities API).
"""

import os
import json
import sys
import urllib.request
import urllib.error
import urllib.parse

BASE_URL = "https://api.capacities.io"

# ── Token Handling ─────────────────────────────────────────────────────

def get_token():
    """Retrieve Capacities API token from env or ~/.hermes/.env."""
    token = os.environ.get("CAPACITIES_API_TOKEN")
    if not token:
        config_path = os.path.expanduser("~/.hermes/.env")
        if os.path.exists(config_path):
            with open(config_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("CAPACITIES_API_TOKEN="):
                        token = line.split("=", 1)[1].strip().strip("'\"")
                        break
    return token


def set_token_env_var():
    """Ensure CAPACITIES_API_TOKEN is set in the environment.
    
    Called during initialization so that child processes and tool calls
    can rely on os.environ.get("CAPACITIES_API_TOKEN") being populated.
    """
    if not os.environ.get("CAPACITIES_API_TOKEN"):
        token = get_token()
        if token:
            os.environ["CAPACITIES_API_TOKEN"] = token


# ── API Client ─────────────────────────────────────────────────────────

def api_request(method, path, body=None):
    """Make an authenticated request to the Capacities REST API."""
    token = os.environ.get("CAPACITIES_API_TOKEN") or get_token()
    if not token:
        return {"error": "CAPACITIES_API_TOKEN not set. Add it to ~/.hermes/.env or set the environment variable."}

    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body else None

    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json" if body else "text/plain",
            "User-Agent": "capacities-mcp/1.0",
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = resp.read().decode("utf-8")
            if result.strip():
                return json.loads(result)
            return {"status": resp.status, "message": "OK"}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"error": f"HTTP {e.code}: {body}"}
    except urllib.error.URLError as e:
        return {"error": f"Connection error: {e.reason}"}


# ── MCP Tool Handlers ─────────────────────────────────────────────────

def handle_list_tools():
    return {
        "tools": [
            {
                "name": "get_spaces",
                "description": "List all your Capacities personal spaces (IDs + titles + icons). Rate limit: 5 req/60s.",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "get_space_info",
                "description": "Get structures (object types), property definitions, and collections for a space.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "spaceId": {
                            "type": "string",
                            "description": "UUID of the space (found in Settings > Space settings)"
                        }
                    },
                    "required": ["spaceId"]
                }
            },
            {
                "name": "lookup_content",
                "description": "Search for content by title in a space. Returns IDs and structure types.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "searchTerm": {
                            "type": "string",
                            "description": "Title (or partial title) to search for"
                        },
                        "spaceId": {
                            "type": "string",
                            "description": "UUID of the space to search in"
                        }
                    },
                    "required": ["searchTerm", "spaceId"]
                }
            },
            {
                "name": "save_weblink",
                "description": "Save a URL as a new object in a Capacities space. Auto-fetches title and description.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "spaceId": {"type": "string", "description": "UUID of the space"},
                        "url": {"type": "string", "description": "The URL to save (format: uri)"},
                        "titleOverwrite": {"type": "string", "description": "Custom title (optional, max 500 chars)"},
                        "descriptionOverwrite": {"type": "string", "description": "Custom description (optional, max 1000 chars)"},
                        "tags": {
                            "type": "array", "items": {"type": "string"},
                            "description": "Tags (max 30). Must match existing names or will be created."
                        },
                        "mdText": {
                            "type": "string",
                            "description": "Markdown notes (max 200000 chars)"
                        }
                    },
                    "required": ["spaceId", "url"]
                }
            },
            {
                "name": "save_to_daily_note",
                "description": "Append markdown text to today's daily note in a space. Rate limit: 5 req/60s.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "spaceId": {"type": "string", "description": "UUID of the space"},
                        "mdText": {"type": "string", "description": "Markdown text (max 200000 chars)"},
                        "noTimeStamp": {
                            "type": "boolean",
                            "description": "Skip prepending a timestamp to the note"
                        },
                        "origin": {
                            "type": "string",
                            "enum": ["commandPalette", "mcp"],
                            "description": "Origin icon. Use 'mcp' for AI integrations."
                        }
                    },
                    "required": ["spaceId", "mdText"]
                }
            }
        ]
    }


def handle_call_tool(name, arguments):
    if name == "get_spaces":
        result = api_request("GET", "/spaces")
        if "error" in result:
            return {"content": [{"type": "text", "text": f"Error: {result['error']}"}], "isError": True}
        spaces = result.get("spaces", [])
        if not spaces:
            return {"content": [{"type": "text", "text": "No spaces found. Create one in Capacities first."}]}
        lines = ["Your Capacities Spaces:\n"]
        for s in spaces:
            icon = s.get("icon", {})
            icon_str = icon.get("val", "📁") if icon else "📁"
            lines.append(f"  {icon_str}  {s['title']}")
            lines.append(f"      ID: {s['id']}")
        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    elif name == "get_space_info":
        space_id = arguments.get("spaceId")
        if not space_id:
            return {"content": [{"type": "text", "text": "Error: spaceId is required"}], "isError": True}
        result = api_request("GET", f"/space-info?spaceid={urllib.parse.quote(space_id)}")
        if "error" in result:
            return {"content": [{"type": "text", "text": f"Error: {result['error']}"}], "isError": True}
        structures = result.get("structures", [])
        lines = [f"Space Info ({space_id[:8]}...):\n"]
        for st in structures:
            lines.append(f"  📋 {st.get('title', '?')} (plural: {st.get('pluralName', '?')})")
            lines.append(f"      ID: {st.get('id', '?')}")
            cols = st.get("collections", [])
            if cols:
                lines.append(f"      Collections: {', '.join(c['title'] for c in cols)}")
        return {"content": [{"type": "text", "text": "\n".join(lines) if len(lines) > 1 else "No structures found."}]}

    elif name == "lookup_content":
        search_term = arguments.get("searchTerm")
        space_id = arguments.get("spaceId")
        if not search_term or not space_id:
            return {"content": [{"type": "text", "text": "Error: searchTerm and spaceId are required"}], "isError": True}
        result = api_request("POST", "/lookup", {"searchTerm": search_term, "spaceId": space_id})
        if "error" in result:
            return {"content": [{"type": "text", "text": f"Error: {result['error']}"}], "isError": True}
        results = result.get("results", [])
        if not results:
            return {"content": [{"type": "text", "text": f"No content found matching '{search_term}'."}]}
        lines = [f"Results for '{search_term}':\n"]
        for r in results:
            lines.append(f"  📄 {r.get('title', '?')}  (ID: {r.get('id', '?')[:8]}...)")
        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    elif name == "save_weblink":
        space_id = arguments.get("spaceId")
        url = arguments.get("url")
        if not space_id or not url:
            return {"content": [{"type": "text", "text": "Error: spaceId and url are required"}], "isError": True}
        body = {"spaceId": space_id, "url": url}
        for key in ("titleOverwrite", "descriptionOverwrite", "mdText"):
            if key in arguments:
                body[key] = arguments[key]
        if "tags" in arguments:
            body["tags"] = arguments["tags"]
        result = api_request("POST", "/save-weblink", body)
        if "error" in result:
            return {"content": [{"type": "text", "text": f"Error: {result['error']}"}], "isError": True}
        title = result.get("title", url)
        return {
            "content": [{"type": "text", "text": f"✅ Weblink saved!\n\nTitle: {title}\nID: {result.get('id', '?')}\nSpace: {result.get('spaceId', '?')}"}]
        }

    elif name == "save_to_daily_note":
        space_id = arguments.get("spaceId")
        md_text = arguments.get("mdText")
        if not space_id or not md_text:
            return {"content": [{"type": "text", "text": "Error: spaceId and mdText are required"}], "isError": True}
        body = {
            "spaceId": space_id,
            "mdText": md_text,
            "origin": arguments.get("origin", "mcp"),
        }
        if arguments.get("noTimeStamp"):
            body["noTimeStamp"] = True
        result = api_request("POST", "/save-to-daily-note", body)
        if "error" in result:
            return {"content": [{"type": "text", "text": f"Error: {result['error']}"}], "isError": True}
        preview = md_text[:80] + ("..." if len(md_text) > 80 else "")
        return {
            "content": [{"type": "text", "text": f"✅ Saved to today's daily note!\n\n{preview}"}]
        }

    else:
        return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}], "isError": True}


# ── MCP STDIO Transport Loop ──────────────────────────────────────────

def main():
    """MCP stdio transport: read JSON-RPC messages from stdin, write to stdout."""
    # Ensure token is available for the session
    set_token_env_var()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg_id = msg.get("id")
        method = msg.get("method")
        params = msg.get("params", {})

        if method == "tools/list":
            response = {"jsonrpc": "2.0", "id": msg_id, "result": handle_list_tools()}
        elif method == "tools/call":
            result = handle_call_tool(params.get("name"), params.get("arguments", {}))
            response = {"jsonrpc": "2.0", "id": msg_id, "result": result}
        elif method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "capacities-mcp", "version": "1.0.0"},
                    "capabilities": {"tools": {}}
                }
            }
        elif method == "notifications/initialized":
            continue
        else:
            response = {
                "jsonrpc": "2.0", "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }

        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
