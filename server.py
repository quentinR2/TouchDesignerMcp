"""
TouchDesigner MCP Server — PoC
Exposes 3 tools: create_node, list_nodes, set_parameter
Communicates with TouchDesigner via HTTP (Web Server DAT on port 9980)
"""

import json
import httpx
from mcp.server.fastmcp import FastMCP

TD_URL = "http://localhost:9980"

mcp = FastMCP("TouchDesigner MCP")


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


if __name__ == "__main__":
    mcp.run(transport="stdio")
