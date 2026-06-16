# Capacities MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-2024--11--05-purple.svg)](https://modelcontextprotocol.io)

An **MCP (Model Context Protocol) server** for [Capacities](https://capacities.io) — the AI-powered knowledge management app. Provides AI agents with tools to create, read, and manage content in Capacities spaces.

Works with any MCP-compatible host: **Hermes Agent**, **Claude Desktop**, **Cursor**, **VS Code Copilot**, and others.

## Features

- 🔍 **Look up content** — search notes by title across your spaces
- 🔗 **Save weblinks** — save URLs as objects with auto-fetched metadata
- 📝 **Daily notes** — append markdown to today's daily note
- 📋 **List spaces** — discover all your spaces and their structures
- 🏗️ **Zero dependencies** — pure Python stdlib, no pip install needed
- 🔐 **Bearier token auth** — secure API key from Capacities settings

## Quick Start

### 1. Get your API token

Open **Capacities desktop app → Settings → Capacities API → Generate Token**

### 2. Run the server

```bash
# Clone
git clone https://github.com/andydennis/hermes-capacities
cd hermes-capacities

# Set your token
export CAPACITIES_API_TOKEN="your...n
# Start the MCP server
python3 server.py
```

The server reads JSON-RPC messages from stdin and writes responses to stdout — standard MCP stdio transport.

### 3. Configure your MCP host

**Hermes Agent:**
```bash
hermes mcp add capacities \
  --command python3 \
  --args /path/to/capacities-mcp/server.py \
  --env CAPACITIES_API_TOKEN=<your_...n```

**Claude Desktop** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "capacities": {
      "command": "python3",
      "args": ["/path/to/capacities-mcp/server.py"],
      "env": { "CAPACITIES_API_TOKEN": "your_token_here" }
    }
  }
}
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

This server powers an 8am cron job that fetches weather, calendar events, tasks, and health data into your Capacities daily note. See [examples/daily-note-cron.md](examples/daily-note-cron.md) for the full setup.

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

## Setup with Hermes Agent

Full integration requires:
- **MCP server** — this repo (5 tools for Capacities operations)
- **Composio** — for Google Calendar and Google Tasks
- **Whoop MCP** — for health data
- **Open-Meteo** — for weather (free, no key)

See the [SKILL.md](SKILL.md) for the complete Hermes skill definition.

## Requirements

- Python 3.10+
- Capacities Pro account (required for API access)
- No external Python packages (stdlib only)

## License

MIT
