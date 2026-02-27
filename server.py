"""
TouchDesigner MCP Server
Exposes 14 tools to control a running TouchDesigner instance.
Communicates with TouchDesigner via HTTP (Web Server DAT on port 9980)
"""

import json
import httpx
from mcp.server.fastmcp import FastMCP

TD_URL = "http://localhost:9980"

mcp = FastMCP(
    "TouchDesigner MCP")


async def send_to_td(action: str, params: dict) -> dict:
    """Send a command to TouchDesigner's Web Server DAT and return the response."""
    payload = {"action": action, "params": params}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(TD_URL, json=payload)
            resp.raise_for_status()
            return resp.json()
    except httpx.ConnectError:
        return {"error": "Cannot connect to TouchDesigner. Is it running with the Web Server DAT active on port 9980?"}
    except httpx.HTTPStatusError as e:
        return {"error": f"TouchDesigner returned HTTP {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def create_node(
    node_type: str,
    node_name: str,
    parent_path: str = "/project1",
) -> str:
    """Create a new operator node in TouchDesigner.

    Args:
        node_type: The operator type, e.g. 'noiseTOP', 'constantCHOP', 'textDAT',
                   'waveCHOP', 'circletopTOP', etc.
        node_name: Name for the new node.
        parent_path: Path to the parent container (default: /project1).
    """
    result = await send_to_td("create_node", {
        "node_type": node_type,
        "node_name": node_name,
        "parent_path": parent_path,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def list_nodes(parent_path: str = "/project1") -> str:
    """List all operator nodes inside a TouchDesigner container.

    Args:
        parent_path: Path to the container to list (default: /project1).
    """
    result = await send_to_td("list_nodes", {
        "parent_path": parent_path,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def set_parameter(
    node_path: str,
    param_name: str,
    value: str,
) -> str:
    """Set a parameter value on an existing TouchDesigner node.

    Args:
        node_path: Full path to the node, e.g. '/project1/noise1'.
        param_name: Parameter name, e.g. 'seed', 'roughness', 'text'.
        value: New value for the parameter (will be converted to the appropriate type).
    """
    result = await send_to_td("set_parameter", {
        "node_path": node_path,
        "param_name": param_name,
        "value": value,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def delete_node(node_path: str) -> str:
    """Delete an operator node from TouchDesigner.

    Args:
        node_path: Full path to the node to delete, e.g. '/project1/noise1'.
    """
    result = await send_to_td("delete_node", {
        "node_path": node_path,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def connect_nodes(
    source_path: str,
    target_path: str,
    input_index: int = 0,
    output_index: int = 0,
) -> str:
    """Connect the output of one node to the input of another node.

    Args:
        source_path: Full path to the source node (output side).
        target_path: Full path to the target node (input side).
        input_index: Input connector index on the target node (default: 0).
        output_index: Output connector index on the source node (default: 0).
    """
    result = await send_to_td("connect_nodes", {
        "source_path": source_path,
        "target_path": target_path,
        "input_index": input_index,
        "output_index": output_index,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def disconnect_nodes(
    target_path: str,
    input_index: int = 0,
) -> str:
    """Disconnect a specific input on a node.

    Args:
        target_path: Full path to the node whose input to disconnect.
        input_index: Input connector index to disconnect (default: 0).
    """
    result = await send_to_td("disconnect_nodes", {
        "target_path": target_path,
        "input_index": input_index,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_node_info(node_path: str) -> str:
    """Get detailed information about a TouchDesigner node, including type,
    family, inputs, outputs, and position.

    Args:
        node_path: Full path to the node, e.g. '/project1/noise1'.
    """
    result = await send_to_td("get_node_info", {
        "node_path": node_path,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_parameter(
    node_path: str,
    param_name: str,
) -> str:
    """Read the current value of a parameter on a TouchDesigner node.

    Args:
        node_path: Full path to the node, e.g. '/project1/noise1'.
        param_name: Parameter name, e.g. 'seed', 'roughness', 'text'.
    """
    result = await send_to_td("get_parameter", {
        "node_path": node_path,
        "param_name": param_name,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def rename_node(
    node_path: str,
    new_name: str,
) -> str:
    """Rename a TouchDesigner node.

    Args:
        node_path: Full path to the node to rename, e.g. '/project1/noise1'.
        new_name: New name for the node.
    """
    result = await send_to_td("rename_node", {
        "node_path": node_path,
        "new_name": new_name,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def execute_script(
    script: str,
    parent_path: str = "/project1",
) -> str:
    """Execute arbitrary Python code inside TouchDesigner. The script runs in
    TD's Python environment with access to all TD APIs (op(), me, etc.).
    Use print() to return output.

    Args:
        script: Python code to execute inside TouchDesigner.
        parent_path: Context path for the script execution (default: /project1).
    """
    result = await send_to_td("execute_script", {
        "script": script,
        "parent_path": parent_path,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def list_parameters(
    node_path: str,
    filter_pattern: str = "*",
) -> str:
    """List all parameters of a TouchDesigner node with their current values,
    types, defaults, and ranges.

    Args:
        node_path: Full path to the node, e.g. '/project1/noise1'.
        filter_pattern: Optional glob pattern to filter parameter names (default: '*').
    """
    result = await send_to_td("list_parameters", {
        "node_path": node_path,
        "filter_pattern": filter_pattern,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def search_nodes(
    pattern: str,
    parent_path: str = "/project1",
    family: str = "",
    recursive: bool = True,
) -> str:
    """Search for nodes by name or type pattern in the TouchDesigner project.

    Args:
        pattern: Glob pattern to match node names, e.g. 'noise*', '*TOP', '*'.
        parent_path: Container to search in (default: /project1).
        family: Optional filter by family: 'TOP', 'CHOP', 'SOP', 'DAT', 'COMP', or '' for all.
        recursive: Whether to search recursively into sub-containers (default: True).
    """
    result = await send_to_td("search_nodes", {
        "pattern": pattern,
        "parent_path": parent_path,
        "family": family,
        "recursive": recursive,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def set_node_position(
    node_path: str,
    x: float,
    y: float,
) -> str:
    """Set the visual position of a node in the TouchDesigner network editor.

    Args:
        node_path: Full path to the node, e.g. '/project1/noise1'.
        x: Horizontal position in network units.
        y: Vertical position in network units.
    """
    result = await send_to_td("set_node_position", {
        "node_path": node_path,
        "x": x,
        "y": y,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_project_info() -> str:
    """Get information about the current TouchDesigner project including
    name, file path, resolution, FPS, and cook rate."""
    result = await send_to_td("get_project_info", {})
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
