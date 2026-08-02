# touchdesigner-mcp — TouchDesigner MCP Server

Control [TouchDesigner](https://derivative.ca/) from AI assistants — Claude Code, Claude Desktop, GitHub Copilot, Cursor, or any [Model Context Protocol](https://modelcontextprotocol.io/) client.

```
MCP client (Claude, Copilot, …)  ←— stdio/MCP —→  touchdesigner-mcp  ←— HTTP :9980 —→  TouchDesigner (Web Server DAT)
```

19 tools: create/connect/inspect nodes, get/set parameters, build whole networks in one call, export networks as JSON, run Python inside TD, save the project, and more.

## Quick start

You need two things running: the **bridge inside TouchDesigner** and the **MCP server config in your AI client**. Python 3.10+ and [uv](https://docs.astral.sh/uv/getting-started/installation/) are the only prerequisites (or plain `pip` if you prefer).

### 1. TouchDesigner side — install the bridge

**Option A — paste the callbacks script:**

1. Print the bridge script and copy it:
   ```bash
   uvx touchdesigner-mcp bridge
   ```
   (or copy [`touchdesigner_mcp/bridge_script.py`](touchdesigner_mcp/bridge_script.py) from this repo / the latest [release](../../releases))
2. In TouchDesigner: right-click in the network editor → `Add Operator` → `DAT` → `Web Server`
3. In the Web Server DAT parameters: set **Port** to `9980`, toggle **Active** ON
4. Click the arrow icon on the Web Server DAT to open its **callbacks DAT**, and replace its entire contents with the copied script

**Option B — drag & drop:** download `touchdesigner-mcp-bridge.tox` from the latest [release](../../releases) and drag it into your network.

Your `.toe` file can be saved **anywhere** — the bridge is fully self-contained.

### 2. Client side — add the MCP server

**Claude Code:**
```bash
claude mcp add touchdesigner -- uvx touchdesigner-mcp
```

**Claude Desktop** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "touchdesigner": {
      "command": "uvx",
      "args": ["touchdesigner-mcp"]
    }
  }
}
```

**VS Code / GitHub Copilot** (`.vscode/mcp.json` in your workspace):
```json
{
  "servers": {
    "touchdesigner": {
      "type": "stdio",
      "command": "uvx",
      "args": ["touchdesigner-mcp"]
    }
  }
}
```

**Cursor** (`.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "touchdesigner": {
      "command": "uvx",
      "args": ["touchdesigner-mcp"]
    }
  }
}
```

That's it. Open your assistant and try: *"Create a noise TOP called myNoise in /project1"*.

## Configuration

By default touchdesigner-mcp talks to `http://127.0.0.1:9980`. Override via environment variables or CLI flags:

| Setting | Default | Description |
|---------|---------|-------------|
| `TD_URL` | — | Full endpoint URL (overrides host/port) |
| `TD_HOST` | `127.0.0.1` | TouchDesigner host |
| `TD_PORT` | `9980` | Web Server DAT port |
| `--url`, `--host`, `--port` | — | CLI equivalents (take precedence over env vars) |

Example — TD on a non-default port, via the client config:
```json
{
  "command": "uvx",
  "args": ["touchdesigner-mcp", "--port", "9981"]
}
```

**Multiple TouchDesigner instances:** add one MCP server entry per instance, each with a different name and port (each TD project needs its own Web Server DAT on a distinct port).

## Usage examples

Prompts that work well in agent mode:

- "Create a noise TOP called myNoise in /project1"
- "What nodes are in /project1?"
- "Set the seed parameter of /project1/myNoise to 42"
- "Connect myNoise to null1"
- "Find all TOP nodes in the project"
- "Show me the info and parameters of /project1/myNoise"
- "Create a network with a noiseTOP, levelTOP, and nullTOP connected in series"
- "Export the network in /project1 as JSON"
- "Are there any errors in the project?"
- "Copy noise1 and call it noise_backup"
- "Create a constant TOP called bg, then set its color to red (colorr=1, colorg=0, colorb=0)"
- "Save the project"

## Available MCP tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `create_node` | `node_type`, `node_name`, `parent_path` | Create an operator node |
| `delete_node` | `node_path` | Delete a node |
| `rename_node` | `node_path`, `new_name` | Rename a node |
| `copy_node` | `node_path`, `destination_path`, `new_name` | Duplicate a node |
| `get_node_info` | `node_path` | Full node details (type, connections, position) |
| `list_nodes` | `parent_path` | List children of a container |
| `get_parameter` | `node_path`, `param_name` | Read a parameter value |
| `set_parameter` | `node_path`, `param_name`, `value` | Set a parameter on a node |
| `list_parameters` | `node_path`, `filter_pattern` | List all params with values/types/ranges |
| `connect_nodes` | `source_path`, `target_path`, `input_index`, `output_index` | Wire output→input |
| `disconnect_nodes` | `target_path`, `input_index` | Remove a connection |
| `create_network` | `nodes`, `connections`, `parent_path` | Batch create nodes + connections in one call |
| `export_network` | `parent_path`, `recursive` | Serialize a subnetwork to JSON |
| `search_nodes` | `pattern`, `parent_path`, `family`, `recursive` | Find nodes by name/type pattern |
| `set_node_position` | `node_path`, `x`, `y` | Position a node in the network |
| `save_project` | `file_path` (optional) | Save the .toe file |
| `get_project_info` | *(none)* | Project metadata (name, FPS, cook rate) |
| `get_errors` | `parent_path`, `recursive`, `include_warnings` | List nodes with errors/warnings |
| `execute_script` | `script`, `parent_path` | Run arbitrary Python inside TD |

## Common TouchDesigner node types

| Human Name | TD Type | Family |
|------------|---------|--------|
| Noise | `noiseTOP` | TOP |
| Constant | `constantTOP` | TOP |
| Circle | `circletopTOP` | TOP |
| Rectangle | `rectangletopTOP` | TOP |
| Text | `textTOP` | TOP |
| Composite | `compositeTOP` | TOP |
| Null | `nullTOP` | TOP |
| Wave | `waveCHOP` | CHOP |
| Constant | `constantCHOP` | CHOP |
| LFO | `lfoCHOP` | CHOP |
| Noise | `noiseCHOP` | CHOP |
| Text | `textDAT` | DAT |
| Table | `tableDAT` | DAT |
| Circle | `circleSOP` | SOP |
| Box | `boxSOP` | SOP |
| Geometry | `geoCOMP` | COMP |
| Container | `containerCOMP` | COMP |

## Security note

The bridge executes commands sent to the Web Server DAT **without authentication** — including arbitrary Python via `execute_script`. It binds to your machine's local network interface. Keep the port firewalled from untrusted networks, and don't expose it to the internet.

## Troubleshooting

### "Cannot connect to TouchDesigner at …"
- Is TouchDesigner running?
- Is the Web Server DAT **Active** (toggle it on)?
- Does the DAT's port match your configured `TD_PORT` (default `9980`)?
- Try opening `http://localhost:9980` in your browser — you should get a response.

### "Unknown action" error
- Make sure you pasted the **entire** bridge script into the callbacks DAT.
- Your bridge may be older than your touchdesigner-mcp version — re-paste the output of `uvx touchdesigner-mcp bridge`.

### "Node not found"
- Check the path with `list_nodes` first.
- Paths are case-sensitive and start with `/`.

### "Parameter not found"
- The error message lists all available parameters — check the exact name.
- Use TD's parameter dialog to find the programmatic name (hover over a parameter label).

## Development

```bash
git clone https://github.com/quentinR2/TouchDesignerMcp
cd TouchDesignerMcp
uv venv && uv pip install -e .[dev]   # or: python -m venv .venv && pip install -e .[dev]
pytest                                 # smoke tests, no TouchDesigner needed
```

Project layout:

```
touchdesigner_mcp/               # MCP server package (runs outside TD)
│   ├── __main__.py   # CLI entry point (touchdesigner-mcp / python -m touchdesigner_mcp)
│   ├── config.py     # Endpoint resolution (env vars / flags)
│   ├── client.py     # send_to_td() async HTTP helper
│   ├── bridge_script.py  # GENERATED single-file TD bridge — do not edit
│   └── tools/        # One module per tool group, registered via @mcp.tool()
├── td_bridge/        # TD-side source of truth (modular, dev only, not shipped)
│   ├── router.py     # Dispatch table + handle_request()
│   └── handlers/     # One module per tool group
├── scripts/build_bridge.py  # Merges td_bridge/ → touchdesigner_mcp/bridge_script.py
└── tests/            # MCP-layer smoke tests
```

**Editing the bridge:** change files under `td_bridge/`, then regenerate:

```bash
python scripts/build_bridge.py
```

CI fails if `touchdesigner_mcp/bridge_script.py` is stale. To test bridge changes in TD, re-paste the regenerated script into the callbacks DAT.

**Releasing:** bump `version` in `pyproject.toml`, tag `vX.Y.Z`, push the tag. GitHub Actions builds, publishes to PyPI (Trusted Publishing), and creates a GitHub release with the bridge script attached. Build the `.tox` in TouchDesigner and upload it to the release manually when the bridge changed.

## License

[MIT](LICENSE)
