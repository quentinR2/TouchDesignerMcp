# TouchDesigner MCP Server — PoC

Control TouchDesigner from AI assistants (GitHub Copilot) using the [Model Context Protocol](https://modelcontextprotocol.io/).

## Architecture

```
Copilot (VS Code)  ←— stdio/MCP —→  server.py (FastMCP)  ←— HTTP —→  TouchDesigner (Web Server DAT)
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
pip install -r requirements.txt
```

### 2. Set up TouchDesigner

1. Open your TouchDesigner project (or create a new one)
2. **Create a Web Server DAT**:
   - Right-click in the network editor → `Add Operator` → `DAT` → `Web Server`
3. **Configure it**:
   - In the parameters panel, set **Port** to `9980`
   - Make sure **Active** is toggled **ON**
4. **Paste the bridge script**:
   - Click the small arrow/icon on the Web Server DAT to open its **callbacks DAT**
   - Select all existing content and **replace it entirely** with the contents of `td_webserver_callbacks.py`
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

### "Node not found"
- Check the path with `list_nodes` first.
- Paths are case-sensitive and start with `/`.

### "Parameter not found"
- The error message lists all available parameters — check the exact name.
- Use TD's parameter dialog to find the programmatic name (hover over a parameter label).

## Project Structure

```
TouchDesigner/
├── server.py                     # MCP server (runs outside TD)
├── td_webserver_callbacks.py     # Bridge script (paste into TD)
├── requirements.txt              # Python dependencies
├── README.md                     # This file
└── .vscode/
    └── mcp.json                  # VS Code MCP config for Copilot
```
