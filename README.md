# Capacities MCP Server

** Capacities are working on OAUTH for the V2 API and this will not work. You should not be requesting access to the local URL from Capacities . Once this is available it will be updated here. The REST V1 API will still work **

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-2024--11--05-purple.svg)](https://modelcontextprotocol.io)

An **MCP (Model Context Protocol) server** for [Capacities](https://capacities.io) — the AI-powered knowledge management app. Provides AI agents with tools to create, read, and manage content in Capacities spaces.

Works with any MCP-compatible host: **Claude Desktop**, **Cursor**, **VS Code Copilot**, **Continue.dev**, **Hermes Agent**, and others.

## Features

- 🔍 **Look up content** — search notes by title across your spaces
- 🔗 **Save weblinks** — save URLs as objects with auto-fetched metadata
- 📝 **Daily notes** — append markdown to today's daily note
- 📋 **List spaces** — discover all your spaces and their structures
- 🏗️ **Zero dependencies** — pure Python stdlib, no pip install needed
- 🔐 **Bearer token auth** — secure API key from Capacities settings
- 🆕 **Native MCP server support** — setup scripts for Capacities' official OAuth 2.1 MCP server (10 tools, search + CRUD)

## Quick Start

### 1. Get your API token

Open **Capacities desktop app → Settings → Capacities API → Generate Token**

### 2. Run the server

```bash
# Clone
git clone https://github.com/andypduk/Hermes-Capacities
cd Hermes-Capacities

# Set your token
export CAPACITIES_API_TOKEN="your...n
# Start the MCP server
python3 server.py
```

The server reads JSON-RPC messages from stdin and writes responses to stdout — standard MCP stdio transport.

### 3. Configure your MCP host

**Claude Desktop** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "capacities": {
      "command": "python3",
      "args": ["/path/to/Hermes-Capacities/server.py"],
      "env": { "CAPACITIES_API_TOKEN": "your_token_here" }
    }
  }
}
```

**Hermes Agent:**
```bash
hermes mcp add capacities \
  --command python3 \
  --args /path/to/Hermes-Capacities/server.py \
  --env CAPACITIES_API_TOKEN=<your_token>
```

**Any other MCP host:** point it at `python3 /path/to/server.py` with the `CAPACITIES_API_TOKEN` env var.

## Native MCP Server (OAuth 2.1)

Capacities also hosts an [official MCP server](https://docs.capacities.io/developer/model-context-protocol) at `https://api.capacities.io/mcp` with 10 tools including search, getObjectContent, createPage, createTask, createObjectViaMd, updateObjectViaMD, and more.

This server uses **OAuth 2.1 with PKCE** (separate from the REST API Bearer token). This repo includes helper scripts:

- **[`setup_oauth.py`](setup_oauth.py)** — interactive OAuth 2.1 PKCE setup. Registers a Dynamic Client, generates auth URL for browser authorization, exchanges code for tokens.
- **[`refresh_oauth.py`](refresh_oauth.py)** — refreshes an expiring OAuth token. Run manually or schedule as a cron job.

Usage:
```bash
# Complete one-time OAuth setup
python3 setup_oauth.py

# Periodic token refresh (tokens expire in 1 hour)
python3 refresh_oauth.py
```

## Tools

### `get_spaces`
List all your Capacities personal spaces. Returns IDs, titles, and icons.
```json
// No input required
// Response:
{ "spaces": [{ "id": "uuid", "title": "Notes", "icon": { "val": "ph:lightbulb", "type": "iconify" } }] }
```

### `get_space_info`
Get structures (object types), property definitions, and collections for a space.
```json
{ "spaceId": "6c052359-e6b6-40f7-9851-9eb004b54f0d" }
```

### `lookup_content`
Search for content by title in a space.
```json
{ "searchTerm": "Q3 planning", "spaceId": "6c052359-..." }
```

### `save_weblink`
Save a URL as a new object in a space. Auto-fetches title and description.
```json
{
  "spaceId": "6c052359-...",
  "url": "https://example.com/article",
  "tags": ["tech", "todo"]
}
```

### `save_to_daily_note`
Append markdown text to today's daily note in a space.
```json
{
  "spaceId": "6c052359-...",
  "mdText": "## Notes\n- Had a great meeting today",
  "noTimeStamp": true,
  "origin": "mcp"
}
```

## Example: Daily Automation

This server can be used to build a morning briefing that fetches weather, calendar events, tasks, and health data into your Capacities daily note. See [examples/daily-note-cron.md](examples/daily-note-cron.md).

## API Reference

The Capacities REST API (beta v0.1.0):

| Endpoint | Method | Description | Rate Limit |
|----------|--------|-------------|------------|
| `/spaces` | GET | List all spaces | 5 req/60s |
| `/space-info` | GET | Get structures & collections | 5 req/60s |
| `/lookup` | POST | Search content by title | 120 req/60s |
| `/save-weblink` | POST | Save a URL as an object | 10 req/60s |
| `/save-to-daily-note` | POST | Append to daily note | 5 req/60s |

**Docs:** https://docs.capacities.io/developer/api
**OpenAPI:** https://api.capacities.io/docs
**Auth:** Bearer token via `CAPACITIES_API_TOKEN` env var

## Requirements

- Python 3.10+
- Capacities Pro account (required for API access)
- No external Python packages (stdlib only)

## License

MIT
