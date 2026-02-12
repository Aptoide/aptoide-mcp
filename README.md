# Aptoide MCP Server

An MCP (Model Context Protocol) server that exposes Aptoide app store data as tools. Works with any MCP-compatible AI client (Claude, Cursor, Windsurf, etc.) to look up Android app details and search the Aptoide catalog.

## Tools

### `get_app`
Get detailed information about an app by package name.

```
get_app(package_name="com.whatsapp")
```

Returns: name, version, developer, description, downloads, rating, size, malware rank, Aptoide URL, and more.

### `search_apps`
Search for apps by keyword.

```
search_apps(query="file manager", limit=5)
```

Returns: list of matching apps with name, package name, version, developer, downloads, rating, size, malware rank, and Aptoide URL.

## Local Setup

```bash
pip install -r requirements.txt
python server.py
```

The server starts on port 8000 by default. Set the `PORT` environment variable to change it.

## Docker

```bash
docker build -t aptoide-mcp .
docker run -p 8000:8000 aptoide-mcp
```

## Add to Claude Code

Production:
```bash
claude mcp add aptoide --transport http https://mcp.aptoide.com/mcp
```

Local development:
```bash
claude mcp add aptoide --transport http http://localhost:8000/mcp
```

## Example Queries

Once added to Claude Code, you can ask Claude things like:

- "Look up the WhatsApp app on Aptoide"
- "Search for VPN apps on Aptoide"
- "Get details about com.android.chrome from Aptoide"
- "Find file manager apps and compare their ratings"
