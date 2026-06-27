# ⚽ FIFA World Cup 2026 — MCP Server & Dashboard

An MCP server built with **FastMCP** to query FIFA World Cup 2026 data directly from any AI compatible with the MCP protocol (Claude, Cursor, etc.), plus a **Streamlit dashboard** for standalone use.

Data is sourced from [openfootball/worldcup.json](https://github.com/openfootball/worldcup.json) — open source, no API key required.

## 🚀 Available Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `recent_matches` | Scores from the most recent matches | `count` (default: 5) |
| `upcoming_matches` | Upcoming scheduled matches | `count` (default: 5) |
| `group_standings` | Standings for a specific group | `group` (A–L) |
| `search_team` | Full info for a team: group, stats, and all matches | `team_name` (in English) |
| `all_groups` | Summary of all 12 groups | — |
| `cup_statistics` | Goals, averages, top scorers, and highlights | — |

## 📦 Installation

```bash
git clone https://github.com/Eduardo-Lucas/worldcup-2026-mcp
cd worldcup-mcp

pip install fastmcp httpx streamlit
```

## 🖥️ Streamlit Dashboard

A visual dashboard with English/Portuguese language switching (🇺🇸 / 🇧🇷):

```bash
streamlit run src/app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

**Pages:**
- 🏆 Recent Matches — scores and goal scorers
- 📅 Upcoming Matches — schedule with venues
- 📊 Standings — all 12 groups with W/D/L/GF/GA/GD
- 🔍 Team Search — full team history and upcoming fixtures
- 📈 Statistics — top scorers, biggest win, goals per game

## ⚙️ MCP Server — Claude Code

```bash
claude mcp add worldcup-2026 python -- -m src.server
```

## ⚙️ MCP Server — Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "worldcup-2026": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/absolute/path/to/worldcup-mcp"
    }
  }
}
```

Restart Claude Desktop. The tools will be available automatically.

## 💬 Usage Examples

Once connected, ask Claude:

- *"What were yesterday's World Cup results?"*
- *"How is Brazil doing in the standings?"*
- *"Show me Group C table"*
- *"Who are the top scorers so far?"*
- *"What are Brazil's upcoming matches?"*

## 🧪 Tests

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

## 🏗️ Project Structure

```
worldcup-mcp/
├── src/
│   ├── server.py          # MCP server (FastMCP tools)
│   └── app.py             # Streamlit dashboard
├── tests/
│   └── test_server.py     # Tool unit tests
├── pyproject.toml
├── claude_desktop_config.json
└── README.md
```

## 📝 How It Works

- **`@mcp.tool()`** — exposes Python functions as AI tools
- **Docstrings** — become the tool description the AI reads
- **Type hints** — define the parameter schema
- **`mcp.run()`** — starts the server over stdio
- **Standings** — calculated dynamically from match results (no separate endpoint needed)
- **Placeholder resolver** — knockout stage codes like `W73`, `1G`, `3A/B/C/D/F` are automatically resolved to real team names as results come in

---

Built with [FastMCP](https://github.com/jlowin/fastmcp) · Data: [openfootball/worldcup.json](https://github.com/openfootball/worldcup.json)
