# TouchDesigner MCP Server

Control TouchDesigner from AI assistants (GitHub Copilot) using the [Model Context Protocol](https://modelcontextprotocol.io/).

## Architecture

```
Copilot (VS Code)  ←— stdio/MCP —→  mcp_server/ (FastMCP)  ←— HTTP —→  TouchDesigner (Web Server DAT)
```

## Prerequisites

- **Python 3.10+** installed and on PATH
- **TouchDesigner** (latest free version)
- **VS Code** with GitHub Copilot extension

## Setup

### 1. Install Python dependencies

```bash
cd C:\Users\UF434QRO\Documents\TouchDesigner
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

> `pip install -e .` reads `pyproject.toml` and installs the package in editable mode, so code changes are picked up immediately without reinstalling.

### 2. Set up TouchDesigner

> ⚠️ **Important**: Your `.toe` project file must be saved **inside this repository folder** (next to `td_bridge/`).  
> The bridge script uses `project.folder` to locate `td_bridge/` — if the `.toe` is elsewhere, the import will fail.

1. Save (or create) your TouchDesigner project inside `C:\Users\UF434QRO\Documents\TouchDesigner\`
2. **Create a Web Server DAT**:
   - Right-click in the network editor → `Add Operator` → `DAT` → `Web Server`
3. **Configure it**:
   - In the parameters panel, set **Port** to `9980`
   - Make sure **Active** is toggled **ON**
4. **Paste the bridge script**:
   - Click the small arrow/icon on the Web Server DAT to open its **callbacks DAT**
   - Select all existing content and **replace it entirely** with the contents of `td_webserver_callbacks.py`
   - The stub auto-loads `td_bridge/` handlers from your project folder — re-paste whenever you update handler code
5. Done — TouchDesigner is now listening for commands on `http://localhost:9980`

### 3. Configure VS Code (GitHub Copilot)

The `.vscode/mcp.json` file is already included. Just open this folder in VS Code:

```bash
code C:\Users\UF434QRO\Documents\TouchDesigner
```

Copilot will automatically detect the MCP server. You can verify in the Copilot chat by checking available tools.

## Usage

Open Copilot Chat in VS Code (agent mode) and try these prompts:

### Create a node
> "Create a noise TOP called myNoise in /project1"

### List nodes
> "What nodes are in /project1?"

### Set a parameter
> "Set the seed parameter of /project1/myNoise to 42"

### Connect two nodes
> "Connect myNoise to null1"

### Search for nodes
> "Find all TOP nodes in the project"

### Get node details
> "Show me the info and parameters of /project1/myNoise"

### Run a script
> "Execute a script that prints all node types in /project1"

### Build a node chain in one call
> "Create a network with a noiseTOP, levelTOP, and nullTOP connected in series"

### Export a network
> "Export the network in /project1 as JSON"

### Check for errors
> "Are there any errors in the project?"

### Duplicate a node
> "Copy noise1 and call it noise_backup"

### Save the project
> "Save the project"

### Combine operations
> "Create a constant TOP called bg, then set its color to red (colorr=1, colorg=0, colorb=0)"

## Available MCP Tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `create_node` | `node_type`, `node_name`, `parent_path` | Create an operator node |
| `delete_node` | `node_path` | Delete a node |
| `connect_nodes` | `source_path`, `target_path`, `input_index`, `output_index` | Wire output→input |
| `disconnect_nodes` | `target_path`, `input_index` | Remove a connection |
| `get_node_info` | `node_path` | Full node details (type, connections, position) |
| `list_nodes` | `parent_path` | List children of a container |
| `get_parameter` | `node_path`, `param_name` | Read a parameter value |
| `set_parameter` | `node_path`, `param_name`, `value` | Set a parameter on a node |
| `list_parameters` | `node_path`, `filter_pattern` | List all params with values/types/ranges |
| `rename_node` | `node_path`, `new_name` | Rename a node |
| `search_nodes` | `pattern`, `parent_path`, `family`, `recursive` | Find nodes by name/type pattern |
| `set_node_position` | `node_path`, `x`, `y` | Position a node in the network |
| `execute_script` | `script`, `parent_path` | Run arbitrary Python inside TD |
| `get_project_info` | *(none)* | Project metadata (name, FPS, cook rate) |
| `create_network` | `nodes`, `connections`, `parent_path` | Batch create nodes + connections in one call |
| `export_network` | `parent_path`, `recursive` | Serialize a subnetwork to JSON |
| `save_project` | `file_path` (optional) | Save the .toe file |
| `get_errors` | `parent_path`, `recursive`, `include_warnings` | List nodes with errors/warnings |
| `copy_node` | `node_path`, `destination_path`, `new_name` | Duplicate a node |

## Common TouchDesigner Node Types

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

## Troubleshooting

### "Cannot connect to TouchDesigner"
- Is TouchDesigner running?
- Is the Web Server DAT **Active** (toggle it on)?
- Is the port set to **9980**?
- Try opening `http://localhost:9980` in your browser — you should see a response.

### "Unknown action" error
- Make sure you pasted the full `td_webserver_callbacks.py` into the callbacks DAT.
- If you edited files in `td_bridge/`, re-paste `td_webserver_callbacks.py` to reload them (it calls `importlib.reload` on all handlers).

### "Node not found"
- Check the path with `list_nodes` first.
- Paths are case-sensitive and start with `/`.

### "Parameter not found"
- The error message lists all available parameters — check the exact name.
- Use TD's parameter dialog to find the programmatic name (hover over a parameter label).

## Project Structure

```
TouchDesigner/
├── your_project.toe               # ← .toe file MUST live here (next to td_bridge/)
├── mcp_server/                    # MCP server Python package (runs outside TD)
│   ├── __init__.py                # Shared FastMCP instance
│   ├── __main__.py                # Entry point: python -m mcp_server
│   ├── config.py                  # TD_URL and port constants
│   ├── client.py                  # send_to_td() async HTTP helper
│   └── tools/
│       ├── __init__.py            # Auto-registers all tools on import
│       ├── nodes.py               # create_node, delete_node, rename_node, copy_node, get_node_info, list_nodes
│       ├── parameters.py          # get_parameter, set_parameter, list_parameters
│       ├── connections.py         # connect_nodes, disconnect_nodes
│       ├── network.py             # create_network, export_network, search_nodes, set_node_position
│       └── project.py             # save_project, get_project_info, get_errors, execute_script
├── td_bridge/                     # TD bridge package (imported from inside TD)
│   ├── __init__.py
│   ├── router.py                  # Dispatch table + handle_request() entry point
│   └── handlers/
│       ├── __init__.py
│       ├── nodes.py               # Node operation handlers
│       ├── parameters.py          # Parameter operation handlers
│       ├── connections.py         # Connection operation handlers
│       ├── network.py             # Network-level operation handlers
│       └── project.py             # Project-level operation handlers
├── td_webserver_callbacks.py      # Thin stub: uses project.folder to import td_bridge, then delegates
├── pyproject.toml                 # Python packaging (replaces requirements.txt)
├── README.md                      # This file
└── .vscode/
    └── mcp.json                   # VS Code MCP config for Copilot
```
